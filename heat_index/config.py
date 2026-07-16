from __future__ import annotations


MAP_BOUNDS = (-92.45, -87.95, 28.60, 31.65)

# Labels are intentionally limited to useful anchors, not every incorporated
# place. Offsets are in display points and reduce collisions on the final map.
CITIES = (
    {"name": "Baton Rouge", "lat": 30.4515, "lon": -91.1871, "offset": (-7, 8), "ha": "right", "tier": "key"},
    {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715, "offset": (8, -14), "ha": "left", "tier": "key"},
    {"name": "Slidell", "lat": 30.2752, "lon": -89.7812, "offset": (9, 9), "ha": "left", "tier": "key"},
    {"name": "Hammond", "lat": 30.5044, "lon": -90.4612, "offset": (-8, 9), "ha": "right", "tier": "key"},
    {"name": "McComb", "lat": 31.2438, "lon": -90.4532, "offset": (0, 10), "ha": "center", "tier": "key"},
    {"name": "Bogalusa", "lat": 30.7910, "lon": -89.8487, "offset": (8, 8), "ha": "left", "tier": "key"},
    {"name": "Houma", "lat": 29.5958, "lon": -90.7195, "offset": (-8, -14), "ha": "right", "tier": "key"},
    {"name": "Bay St. Louis", "lat": 30.3088, "lon": -89.3300, "offset": (9, 8), "ha": "left", "tier": "key"},
    {"name": "Grand Isle", "lat": 29.2366, "lon": -89.9873, "offset": (0, -15), "ha": "center", "tier": "key"},
    {"name": "Thibodaux", "lat": 29.7958, "lon": -90.8229, "offset": (-8, 8), "ha": "right", "tier": "detail"},
    {"name": "Gonzales", "lat": 30.2385, "lon": -90.9201, "offset": (-8, -15), "ha": "right", "tier": "detail"},
    {"name": "Mandeville", "lat": 30.3583, "lon": -90.0656, "offset": (7, -16), "ha": "left", "tier": "detail"},
)

NDFD_URLS = (
    "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
    "AR.smissvly/VP.001-003/ds.apt.bin",
    "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
    "AR.smissvly/VP.004-007/ds.apt.bin",
)

TIMEZONE = "America/Chicago"
