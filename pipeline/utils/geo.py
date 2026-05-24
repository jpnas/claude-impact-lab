import math
import shapely.geometry as sg


def point_in_polygon(lat: float, lon: float, polygon: sg.Polygon) -> bool:
    return polygon.contains(sg.Point(lon, lat))


def geodesic_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in metres."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def points_within_radius(
    center_lat: float,
    center_lon: float,
    points: list[tuple[float, float]],
    radius_m: float,
) -> list[tuple[float, float]]:
    """Return subset of (lat, lon) points within radius_m of center."""
    return [
        p for p in points
        if geodesic_distance_m(center_lat, center_lon, p[0], p[1]) <= radius_m
    ]
