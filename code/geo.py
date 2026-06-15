"""
geo.py
INTERide — Geographic helpers: IP location, geocoding, and road routing.
"""

from typing import List, Optional, Tuple
import math


# ══════════════════════════════════════════════════════════════════════════
#  IP-based location (fallback: Manila)
# ══════════════════════════════════════════════════════════════════════════
def ip_location() -> Tuple[float, float, str]:
    """Return (lat, lon, city) from the device's public IP. Falls back to Manila."""
    from config import HAS_REQUESTS
    if not HAS_REQUESTS:
        return 14.5995, 120.9842, "Manila"
    try:
        import requests
        r = requests.get("http://ip-api.com/json/", timeout=5).json()
        if r.get("status") == "success":
            return r["lat"], r["lon"], r.get("city", "Your Area")
    except Exception:
        pass
    return 14.5995, 120.9842, "Manila"


# ══════════════════════════════════════════════════════════════════════════
#  Forward geocoding
# ══════════════════════════════════════════════════════════════════════════
def geocode(addr: str) -> Optional[Tuple[float, float] ]:
    """Convert an address string to (lat, lon). Returns None on failure."""
    from config import HAS_GEO, _gc
    if not HAS_GEO or not _gc:
        return None
    try:
        loc = _gc.geocode(addr + ", Philippines", timeout=8)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════
#  Distance helpers
# ══════════════════════════════════════════════════════════════════════════
def haversine(
    c1: Tuple[float, float],
    c2: Tuple[float, float],
) -> float:
    """Straight-line distance in kilometres between two (lat, lon) points."""
    R: float = 6371
    la1, lo1 = math.radians(c1[0]), math.radians(c1[1])
    la2, lo2 = math.radians(c2[0]), math.radians(c2[1])
    a = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def get_road_route(
    c1: Tuple[float, float],
    c2: Tuple[float, float],
) -> Optional[Tuple[List[Tuple[float, float]], float, float ]]:
    """
    Fetch a real road route from OSRM (free, no API key).

    Returns:
        (list_of_(lat,lon)_waypoints, distance_km, duration_min)
        Falls back to a straight-line estimate on any error.
    """
    from config import HAS_REQUESTS
    if not HAS_REQUESTS:
        return [c1, c2], round(haversine(c1, c2) * 1.35, 2), None

    try:
        import requests
        url: str = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{c1[1]},{c1[0]};{c2[1]},{c2[0]}"
            f"?overview=full&geometries=geojson&steps=false"
        )
        r = requests.get(url, timeout=10).json()
        if r.get("code") == "Ok":
            route:    dict  = r["routes"][0]
            dist_km:  float = round(route["distance"] / 1000, 2)
            dur_min:  float = round(route["duration"] / 60,   1)
            # GeoJSON coords are [lon, lat] — flip to (lat, lon)
            coords: List[Tuple[float, float]] = [
                (pt[1], pt[0]) for pt in route["geometry"]["coordinates"]
            ]
            return coords, dist_km, dur_min
    except Exception:
        pass

    return [c1, c2], round(haversine(c1, c2) * 1.35, 2), None
