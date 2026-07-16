from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from .config import MAP_BOUNDS, NDFD_URLS, TIMEZONE


@dataclass(frozen=True)
class ForecastGrid:
    longitude: np.ndarray
    latitude: np.ndarray
    values_f: np.ndarray
    valid_times: np.ndarray
    generated_at: datetime
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class DailyMaximum:
    day: date
    values_f: np.ndarray
    sample_count: int


def _download(url: str, target: Path, timeout: int = 90) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "wfo-lix-heat-index-plots/1.0 (weather.gov operational tool)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    if len(payload) < 1_000 or not payload.startswith(b"GRIB"):
        raise RuntimeError(f"NDFD returned an invalid GRIB file from {url}")
    target.write_bytes(payload)


def _as_fahrenheit(values: np.ndarray, units: str) -> np.ndarray:
    units = units.lower()
    if units in {"k", "kelvin"} or np.nanmedian(values) > 150:
        return (values - 273.15) * 9 / 5 + 32
    if units in {"c", "degc", "celsius", "°c"}:
        return values * 9 / 5 + 32
    return values


def _read_grib(path: Path):
    import cfgrib

    datasets = cfgrib.open_datasets(path, backend_kwargs={"indexpath": ""})
    candidates = []
    for dataset in datasets:
        if "latitude" not in dataset.coords or "longitude" not in dataset.coords:
            continue
        for name, variable in dataset.data_vars.items():
            if variable.ndim < 2:
                continue
            candidates.append((dataset, name, variable.size))
    if not candidates:
        raise RuntimeError(f"No apparent-temperature grid was found in {path.name}")

    dataset, name, _ = max(candidates, key=lambda item: item[2])
    variable = dataset[name]
    latitude = np.asarray(dataset.latitude.values, dtype=float)
    longitude = np.asarray(dataset.longitude.values, dtype=float)
    longitude = np.where(longitude > 180, longitude - 360, longitude)
    spatial_dims = dataset.latitude.dims
    non_spatial_dims = tuple(dim for dim in variable.dims if dim not in spatial_dims)

    if non_spatial_dims:
        stacked = variable.stack(sample=non_spatial_dims).transpose("sample", *spatial_dims)
    else:
        stacked = variable.expand_dims(sample=[0]).transpose("sample", *spatial_dims)
    values = _as_fahrenheit(np.asarray(stacked.values, dtype=float), variable.attrs.get("units", ""))

    if "valid_time" in dataset.coords:
        valid = dataset.valid_time
    elif "time" in dataset.coords:
        valid = dataset.time
    else:
        raise RuntimeError(f"No valid times were found in {path.name}")
    if non_spatial_dims:
        template = variable.isel({dim: 0 for dim in spatial_dims}, drop=True)
        valid = valid.broadcast_like(template).stack(sample=non_spatial_dims)
    valid_times = np.asarray(valid.values).reshape(-1).astype("datetime64[ns]")
    if valid_times.size == 1 and values.shape[0] > 1:
        raise RuntimeError(f"Could not match forecast times to grids in {path.name}")
    return longitude, latitude, values, valid_times


def _subset(longitude, latitude, values, padding=0.25):
    west, east, south, north = MAP_BOUNDS
    inside = (
        (longitude >= west - padding)
        & (longitude <= east + padding)
        & (latitude >= south - padding)
        & (latitude <= north + padding)
    )
    rows, columns = np.where(inside)
    if not rows.size:
        raise RuntimeError("The NDFD grid does not overlap the LIX forecast area")
    row_slice = slice(rows.min(), rows.max() + 1)
    column_slice = slice(columns.min(), columns.max() + 1)
    return (
        longitude[row_slice, column_slice],
        latitude[row_slice, column_slice],
        values[:, row_slice, column_slice],
    )


def load_forecast(cache_directory: str | os.PathLike | None = None) -> ForecastGrid:
    cache = Path(cache_directory or Path(tempfile.gettempdir()) / "lix-heat-index")
    cache.mkdir(parents=True, exist_ok=True)
    chunks = []
    generated_at = datetime.now(ZoneInfo(TIMEZONE))
    for url in NDFD_URLS:
        digest = hashlib.sha1(url.encode()).hexdigest()[:10]
        path = cache / f"ndfd-{digest}.grib2"
        _download(url, path)
        chunks.append(_read_grib(path))

    longitude, latitude = chunks[0][:2]
    values = np.concatenate([chunk[2] for chunk in chunks], axis=0)
    times = np.concatenate([chunk[3] for chunk in chunks])
    order = np.argsort(times)
    times, values = times[order], values[order]
    _, unique_indices = np.unique(times, return_index=True)
    times, values = times[unique_indices], values[unique_indices]
    longitude, latitude, values = _subset(longitude, latitude, values)
    return ForecastGrid(longitude, latitude, values, times, generated_at, NDFD_URLS)


def daily_maxima(forecast: ForecastGrid, timezone: str = TIMEZONE) -> list[DailyMaximum]:
    zone = ZoneInfo(timezone)
    local_days = [
        datetime.fromtimestamp(int(value.astype("datetime64[s]").astype(int)), tz=ZoneInfo("UTC"))
        .astimezone(zone)
        .date()
        for value in forecast.valid_times
    ]
    output = []
    for day in sorted(set(local_days)):
        indices = [index for index, item in enumerate(local_days) if item == day]
        output.append(DailyMaximum(day, np.nanmax(forecast.values_f[indices], axis=0), len(indices)))
    return output


def nearest_grid_value(longitude, latitude, field, lon: float, lat: float) -> float:
    distance = (longitude - lon) ** 2 + (latitude - lat) ** 2
    row, column = np.unravel_index(np.nanargmin(distance), distance.shape)
    return float(field[row, column])

