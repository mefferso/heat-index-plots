from __future__ import annotations

import io
import json
from datetime import date, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.collections import LineCollection
from matplotlib.path import Path as MplPath

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

    ax = fig.add_axes([0.025, 0.12, 0.95, 0.735])
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

    mask = cwa_mask(longitude, latitude)
    field = np.ma.masked_where(~mask | ~np.isfinite(values_f), values_f)
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
    counties = _load_geojson("lix_counties.geojson")
    cwa = _load_geojson("lix_cwa.geojson")
    _draw_boundaries(ax, states, "#263238", 1.3, 0.75, 4)
    if show_counties:
        _draw_boundaries(ax, counties, "#1f2529", 0.65, 0.58, 5)
    _draw_boundaries(ax, cwa, "#050505", 2.2, 1.0, 6)

    if show_cities:
        for city in CITIES:
            ax.scatter(
                city["lon"], city["lat"], s=18, c="#111111", edgecolors="white", linewidths=0.65, zorder=8
            )
            label = city["name"]
            if show_city_values:
                value = nearest_grid_value(longitude, latitude, values_f, city["lon"], city["lat"])
                label = f"{label}  {value:.0f}°"
            ax.annotate(
                label,
                (city["lon"], city["lat"]),
                xytext=city["offset"],
                textcoords="offset points",
                fontsize=10.5,
                fontweight="semibold" if show_city_values else "normal",
                color="#111111",
                zorder=9,
                path_effects=[],
                bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
            )

    colorbar_ax = fig.add_axes([0.17, 0.068, 0.66, 0.028])
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

