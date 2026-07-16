from __future__ import annotations

import io
import json
from datetime import date, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patheffects as path_effects
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.collections import LineCollection
from matplotlib.path import Path as MplPath
from matplotlib.patches import FancyBboxPatch

from .config import CITIES, MAP_BOUNDS
from .data import nearest_grid_value


ROOT = Path(__file__).resolve().parents[1]
LEVELS = np.arange(75, 126, 5)
COLORS = (
    "#d9f0f0",
    "#fff7bc",
    "#fee391",
    "#fec44f",
    "#fe9929",
    "#f16913",
    "#d94801",
    "#d73027",
    "#b2182b",
    "#8e0f70",
)


def _load_geojson(name: str):
    return json.loads((ROOT / "assets" / name).read_text())


def _polygons(collection):
    for feature in collection["features"]:
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            yield geometry["coordinates"]
        elif geometry["type"] == "MultiPolygon":
            yield from geometry["coordinates"]


def _rings(collection):
    for polygon in _polygons(collection):
        yield from polygon


def cwa_mask(longitude: np.ndarray, latitude: np.ndarray) -> np.ndarray:
    points = np.column_stack((longitude.ravel(), latitude.ravel()))
    inside = np.zeros(points.shape[0], dtype=bool)
    for polygon in _polygons(_load_geojson("lix_cwa.geojson")):
        polygon_inside = MplPath(np.asarray(polygon[0])).contains_points(points)
        for hole in polygon[1:]:
            polygon_inside &= ~MplPath(np.asarray(hole)).contains_points(points)
        inside |= polygon_inside
    return inside.reshape(longitude.shape)


def smooth_field(values: np.ndarray, passes: int = 2) -> np.ndarray:
    """Lightly smooth grid-scale noise without changing sampled city values."""
    output = np.asarray(values, dtype=float).copy()
    kernel = np.array(((1, 2, 1), (2, 4, 2), (1, 2, 1)), dtype=float)
    for _ in range(passes):
        padded = np.pad(output, 1, mode="edge")
        total = np.zeros_like(output)
        weights = np.zeros_like(output)
        for row in range(3):
            for column in range(3):
                sample = padded[row : row + output.shape[0], column : column + output.shape[1]]
                valid = np.isfinite(sample)
                total += np.where(valid, sample, 0) * kernel[row, column]
                weights += valid * kernel[row, column]
        output = np.divide(total, weights, out=np.full_like(output, np.nan), where=weights > 0)
    return output


def _draw_boundaries(ax, collection, color, linewidth, alpha=1.0, zorder=5):
    segments = [np.asarray(ring) for ring in _rings(collection)]
    ax.add_collection(
        LineCollection(segments, colors=color, linewidths=linewidth, alpha=alpha, zorder=zorder)
    )


def _date_label(day: date) -> str:
    return f"{day.strftime('%A, %B')} {day.day}, {day.year}"


def render_map(
    longitude: np.ndarray,
    latitude: np.ndarray,
    values_f: np.ndarray,
    forecast_day: date,
    generated_at: datetime,
    *,
    title: str = "Maximum Heat Index",
    subtitle: str = "",
    show_cities: bool = True,
    show_city_values: bool = True,
    show_counties: bool = True,
    city_detail: str = "Key cities",
    format_name: str = "Social media (16:9)",
    dpi: int = 150,
) -> bytes:
    figsize = (16, 9) if "16:9" in format_name else (12, 9)
    fig = plt.figure(figsize=figsize, dpi=dpi, facecolor="white")
    header_height = 0.135
    header = fig.add_axes([0, 1 - header_height, 1, header_height])
    header.set_facecolor("#16324f")
    header.set_xticks([])
    header.set_yticks([])
    for spine in header.spines.values():
        spine.set_visible(False)
    header.text(0.035, 0.63, title, color="white", fontsize=29, fontweight="bold", va="center")
    header.text(
        0.035,
        0.22,
        subtitle or _date_label(forecast_day),
        color="#dce8f2",
        fontsize=15,
        va="center",
    )
    header.text(
        0.965,
        0.50,
        "NWS NEW ORLEANS / BATON ROUGE",
        color="white",
        fontsize=13,
        fontweight="bold",
        ha="right",
        va="center",
    )

    ax = fig.add_axes([0.025, 0.14, 0.615, 0.705])
    ax.set_facecolor("#dcecf2")
    west, east, south, north = MAP_BOUNDS
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_aspect(1 / np.cos(np.deg2rad((south + north) / 2)))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#263238")
        spine.set_linewidth(1.1)

    # NDFD is a seamless national mosaic. Keep the shading continuous across
    # office boundaries and use the LIX outline only as a geographic reference.
    plotted_values = smooth_field(values_f)
    field = np.ma.masked_where(~np.isfinite(plotted_values), plotted_values)
    cmap = ListedColormap(COLORS)
    cmap.set_under("#eef6f6")
    cmap.set_over("#5b167d")
    norm = BoundaryNorm(LEVELS, cmap.N)
    filled = ax.contourf(
        longitude,
        latitude,
        field,
        levels=LEVELS,
        cmap=cmap,
        norm=norm,
        extend="both",
        antialiased=True,
        zorder=2,
    )

    states = _load_geojson("states.geojson")
    counties = _load_geojson("regional_counties.geojson")
    cwa = _load_geojson("lix_cwa.geojson")
    _draw_boundaries(ax, states, "#263238", 1.3, 0.75, 4)
    if show_counties:
        _draw_boundaries(ax, counties, "#1f2529", 0.65, 0.58, 5)
    _draw_boundaries(ax, cwa, "#050505", 2.2, 1.0, 6)

    displayed_cities = [city for city in CITIES if city_detail == "All reference cities" or city["tier"] == "key"]
    if show_cities:
        for city in displayed_cities:
            ax.scatter(
                city["lon"], city["lat"], s=22, c="white", edgecolors="#111111", linewidths=1.1, zorder=8
            )
            annotation = ax.annotate(
                city["name"],
                (city["lon"], city["lat"]),
                xytext=city["offset"],
                textcoords="offset points",
                fontsize=9.3,
                fontweight="semibold",
                color="#111111",
                ha=city["ha"],
                va="center",
                zorder=9,
            )
            annotation.set_path_effects([path_effects.withStroke(linewidth=2.8, foreground="white")])

    panel = fig.add_axes([0.665, 0.14, 0.31, 0.705])
    panel.set_xlim(0, 1)
    panel.set_ylim(0, 1)
    panel.axis("off")
    panel.add_patch(
        FancyBboxPatch(
            (0.01, 0.01), 0.98, 0.98,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            facecolor="#f3f6f8", edgecolor="#b8c4cc", linewidth=1.0,
        )
    )
    panel.text(0.07, 0.935, "FORECAST VALUES", color="#16324f", fontsize=16, fontweight="bold", va="top")
    panel.text(0.07, 0.885, _date_label(forecast_day), color="#52616b", fontsize=10.5, va="top")
    panel.plot([0.07, 0.93], [0.845, 0.845], color="#c4cdd3", linewidth=0.9)
    if show_cities and show_city_values:
        row_y = np.linspace(0.79, 0.18, len(displayed_cities))
        for city, y in zip(displayed_cities, row_y):
            value = nearest_grid_value(longitude, latitude, values_f, city["lon"], city["lat"])
            panel.text(0.09, y, city["name"], fontsize=11.5, color="#263238", va="center")
            panel.text(0.91, y, f"{value:.0f}°", fontsize=14, color="#b83b14", fontweight="bold", ha="right", va="center")
    else:
        panel.text(0.09, 0.76, "Official NDFD apparent-temperature\nforecast for southeast Louisiana and\nsouthern Mississippi.", fontsize=11.5, color="#37474f", va="top", linespacing=1.55)
    panel.plot([0.07, 0.93], [0.125, 0.125], color="#c4cdd3", linewidth=0.9)
    panel.text(0.07, 0.09, "Values in °F • Nearest NDFD grid point", fontsize=9.3, color="#60717d", va="center")

    colorbar_ax = fig.add_axes([0.14, 0.072, 0.72, 0.027])
    colorbar = fig.colorbar(filled, cax=colorbar_ax, orientation="horizontal", ticks=LEVELS)
    colorbar.ax.tick_params(labelsize=10, length=3, pad=3)
    colorbar.outline.set_linewidth(0.8)
    colorbar.set_label("Maximum apparent temperature (°F)", fontsize=11, labelpad=5, fontweight="semibold")

    fig.text(
        0.025,
        0.018,
        f"Official NDFD forecast • Generated {generated_at.strftime('%b %d, %Y %I:%M %p %Z')}",
        fontsize=9.5,
        color="#455a64",
        va="bottom",
    )
    fig.text(
        0.975,
        0.018,
        "weather.gov/lix",
        fontsize=9.5,
        color="#455a64",
        ha="right",
        va="bottom",
        fontweight="semibold",
    )
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, facecolor="white")
    plt.close(fig)
    return buffer.getvalue()
