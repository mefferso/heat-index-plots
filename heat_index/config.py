from __future__ import annotations


MAP_BOUNDS = (-91.95, -88.25, 28.72, 31.58)

# Labels are intentionally limited to useful anchors, not every incorporated
# place. Offsets are in display points and reduce collisions on the final map.
CITIES = (
    {"name": "Baton Rouge", "lat": 30.4515, "lon": -91.1871, "offset": (7, 7)},
    {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715, "offset": (7, -15)},
    {"name": "Slidell", "lat": 30.2752, "lon": -89.7812, "offset": (7, 7)},
    {"name": "Hammond", "lat": 30.5044, "lon": -90.4612, "offset": (7, 7)},
    {"name": "McComb", "lat": 31.2438, "lon": -90.4532, "offset": (7, 7)},
    {"name": "Bogalusa", "lat": 30.7910, "lon": -89.8487, "offset": (7, 7)},
    {"name": "Houma", "lat": 29.5958, "lon": -90.7195, "offset": (7, -15)},
    {"name": "Thibodaux", "lat": 29.7958, "lon": -90.8229, "offset": (7, 7)},
    {"name": "Bay St. Louis", "lat": 30.3088, "lon": -89.3300, "offset": (7, 7)},
    {"name": "Gonzales", "lat": 30.2385, "lon": -90.9201, "offset": (7, 7)},
    {"name": "Mandeville", "lat": 30.3583, "lon": -90.0656, "offset": (7, -15)},
    {"name": "Grand Isle", "lat": 29.2366, "lon": -89.9873, "offset": (7, 7)},
)

NDFD_URLS = (
    "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
    "AR.smissvly/VP.001-003/ds.apt.bin",
    "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
    "AR.smissvly/VP.004-007/ds.apt.bin",
)

TIMEZONE = "America/Chicago"

