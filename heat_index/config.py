from __future__ import annotations


MAP_BOUNDS = (-92.45, -87.95, 28.60, 31.65)

# Airport-supported sites use the airport/station reference coordinates from
# the NWS Aviation Weather Center. Grand Isle uses the FAA GNI seaplane-base
# reference point. Woodville has no airport site, so it is explicitly sampled
# at the town center. Offsets are in display points and reduce label collisions.
CITIES = (
    {"name": "Baton Rouge", "station": "KBTR", "lat": 30.53783, "lon": -91.14679, "offset": (-8, 9), "ha": "right", "tier": "key"},
    {"name": "New Orleans", "station": "KMSY", "lat": 29.99739, "lon": -90.27773, "offset": (9, -14), "ha": "left", "tier": "key"},
    {"name": "Slidell", "station": "KASD", "lat": 30.34356, "lon": -89.82237, "offset": (9, -13), "ha": "left", "tier": "key"},
    {"name": "Hammond", "station": "KHDC", "lat": 30.52368, "lon": -90.41765, "offset": (-8, 9), "ha": "right", "tier": "key"},
    {"name": "McComb", "station": "KMCB", "lat": 31.18227, "lon": -90.47207, "offset": (0, 10), "ha": "center", "tier": "key"},
    {"name": "Bogalusa", "station": "KBXA", "lat": 30.81043, "lon": -89.86275, "offset": (8, 8), "ha": "left", "tier": "key"},
    {"name": "Houma", "station": "KHUM", "lat": 29.56338, "lon": -90.66286, "offset": (-8, -14), "ha": "right", "tier": "key"},
    {"name": "Gulfport", "station": "KGPT", "lat": 30.41209, "lon": -89.08093, "offset": (9, 9), "ha": "left", "tier": "key"},
    {"name": "Grand Isle", "station": "GNI", "lat": 29.26273, "lon": -89.96118, "offset": (0, -15), "ha": "center", "tier": "key"},
    {"name": "Gonzales", "station": "KREG", "lat": 30.17559, "lon": -90.93974, "offset": (-8, -15), "ha": "right", "tier": "detail"},
    {"name": "Woodville", "station": None, "lat": 31.104619, "lon": -91.299555, "offset": (-8, 9), "ha": "right", "tier": "detail"},
)

NDFD_URLS = (
    "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
    "AR.smissvly/VP.001-003/ds.apt.bin",
    "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
    "AR.smissvly/VP.004-007/ds.apt.bin",
)

TIMEZONE = "America/Chicago"
