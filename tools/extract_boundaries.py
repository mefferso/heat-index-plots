"""Extract the LIX features from the supplied national shapefiles.

This intentionally uses only the Python standard library so the source
shapefiles can be reduced before the application dependencies are installed.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT.parents[0] / "upload"


def read_dbf(path: Path) -> list[dict[str, str]]:
    data = path.read_bytes()
    record_count = struct.unpack("<I", data[4:8])[0]
    header_length = struct.unpack("<H", data[8:10])[0]
    record_length = struct.unpack("<H", data[10:12])[0]
    fields: list[tuple[str, int]] = []
    offset = 32
    while data[offset] != 0x0D:
        raw = data[offset : offset + 32]
        name = raw[:11].split(b"\0", 1)[0].decode("latin-1")
        fields.append((name, raw[16]))
        offset += 32

    records = []
    for index in range(record_count):
        raw = data[
            header_length + index * record_length : header_length + (index + 1) * record_length
        ]
        position = 1
        record = {}
        for name, length in fields:
            record[name] = raw[position : position + length].decode("latin-1").strip()
            position += length
        records.append(record)
    return records


def read_shapes(path: Path) -> list[list[list[tuple[float, float]]]]:
    data = path.read_bytes()
    position = 100
    shapes = []
    while position < len(data):
        content_words = struct.unpack(">I", data[position + 4 : position + 8])[0]
        content = data[position + 8 : position + 8 + content_words * 2]
        shape_type = struct.unpack("<I", content[:4])[0]
        if shape_type == 0:
            shapes.append([])
        elif shape_type in (5, 15, 25):
            part_count, point_count = struct.unpack("<II", content[36:44])
            starts = list(struct.unpack(f"<{part_count}I", content[44 : 44 + part_count * 4]))
            starts.append(point_count)
            point_start = 44 + part_count * 4
            points = [
                struct.unpack("<dd", content[point_start + i * 16 : point_start + (i + 1) * 16])
                for i in range(point_count)
            ]
            shapes.append([points[starts[i] : starts[i + 1]] for i in range(part_count)])
        else:
            raise ValueError(f"Unsupported shape type {shape_type}")
        position += 8 + content_words * 2
    return shapes


def perpendicular_distance(point, start, end):
    if start == end:
        return math.dist(point, start)
    x, y = point
    x1, y1 = start
    x2, y2 = end
    return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / math.hypot(y2 - y1, x2 - x1)


def simplify(points, tolerance=0.002):
    if len(points) < 4:
        return points
    closed = points[0] == points[-1]
    working = points[:-1] if closed else points

    def rdp(segment):
        if len(segment) < 3:
            return segment
        distances = [perpendicular_distance(p, segment[0], segment[-1]) for p in segment[1:-1]]
        maximum = max(distances, default=0)
        if maximum <= tolerance:
            return [segment[0], segment[-1]]
        index = distances.index(maximum) + 1
        return rdp(segment[: index + 1])[:-1] + rdp(segment[index:])

    result = rdp(working)
    if closed and result[0] != result[-1]:
        result.append(result[0])
    return [[round(x, 5), round(y, 5)] for x, y in result]


def signed_area(ring):
    return sum((x2 - x1) * (y2 + y1) for (x1, y1), (x2, y2) in zip(ring, ring[1:]))


def point_in_ring(point, ring):
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def polygon_geometry(parts):
    rings = [simplify(part) for part in parts if len(part) >= 4]
    # Shapefile exteriors are clockwise. The fallback treats every ring as an
    # exterior, which is safer for masking coastal islands than dropping one.
    exteriors = [ring for ring in rings if signed_area(ring) > 0]
    holes = [ring for ring in rings if signed_area(ring) <= 0]
    if not exteriors:
        exteriors, holes = rings, []
    polygons = [[outer] for outer in exteriors]
    for hole in holes:
        for polygon in polygons:
            if point_in_ring(hole[0], polygon[0]):
                polygon.append(hole)
                break
        else:
            polygons.append([hole])
    return {"type": "MultiPolygon", "coordinates": polygons}


def feature_collection(shp: Path, dbf: Path, predicate, properties):
    shapes = read_shapes(shp)
    records = read_dbf(dbf)
    features = []
    for parts, record in zip(shapes, records):
        if predicate(record):
            features.append(
                {
                    "type": "Feature",
                    "properties": {name: record[name] for name in properties},
                    "geometry": polygon_geometry(parts),
                }
            )
    return {"type": "FeatureCollection", "features": features}


def main():
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    counties = feature_collection(
        UPLOAD / "c_16ap26(1).shp",
        UPLOAD / "c_16ap26(1).dbf",
        lambda row: row["CWA"] == "LIX",
        ("STATE", "COUNTYNAME", "FIPS"),
    )
    cwa = feature_collection(
        UPLOAD / "w_16ap26(1).shp",
        UPLOAD / "w_16ap26(1).dbf",
        lambda row: row["CWA"] == "LIX",
        ("CWA", "CITYSTATE"),
    )
    states = feature_collection(
        UPLOAD / "s_16ap26(1).shp",
        UPLOAD / "s_16ap26(1).dbf",
        lambda row: row["STATE"] in {"LA", "MS"},
        ("STATE", "NAME"),
    )
    for name, content in (("lix_counties", counties), ("lix_cwa", cwa), ("states", states)):
        (assets / f"{name}.geojson").write_text(json.dumps(content, separators=(",", ":")))
        print(name, len(content["features"]), (assets / f"{name}.geojson").stat().st_size)


if __name__ == "__main__":
    main()
