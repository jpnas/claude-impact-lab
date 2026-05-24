from __future__ import annotations

import pandas as pd
import numpy as np
import shapely.geometry as sg
import shapely.wkt
from shapely.vectorized import contains

from pipeline.config import CAMERAS_CSV, RAIO_METROS
from pipeline.utils.geo import geodesic_distance_m


_cameras_cache: dict[str, list[dict]] | None = None


def _load_all_cameras() -> dict[str, list[dict]]:
    """Load all cameras grouped by area name. Returns {area_nome: [{id, lat, lon}]}"""
    global _cameras_cache
    if _cameras_cache is not None:
        return _cameras_cache
    df = pd.read_csv(CAMERAS_CSV, encoding="utf-8")
    result: dict[str, list[dict]] = {}
    for _, row in df.iterrows():
        try:
            geom = shapely.wkt.loads(str(row["geometry"]))
            # WKT POINT(lon lat) — geom.x = lon, geom.y = lat
            lat, lon = geom.y, geom.x
        except Exception:
            continue
        area = str(row["nome_area_fm"])
        if area not in result:
            result[area] = []
        result[area].append({"id": str(row["id_ponto"]), "lat": lat, "lon": lon})
    _cameras_cache = result
    return result


def _top_logradouros_brutos(polygon: sg.Polygon) -> pd.Series:
    """From raw ocorrencias, get logradouros above P80 crime count within polygon."""
    from pipeline.processadores.ocorrencias import _load_ocorrencias
    df = _load_ocorrencias()
    # Spatial filter via vectorized shapely
    valid = df["latitude"].notna() & df["longitude"].notna()
    df_v = df[valid]
    lons = df_v["longitude"].to_numpy(dtype=float)
    lats = df_v["latitude"].to_numpy(dtype=float)
    mask = contains(polygon, lons, lats)
    df_area = df_v[mask]
    counts = df_area["locf"].dropna().value_counts()
    if counts.empty:
        return pd.Series(dtype=int)
    p80 = np.percentile(counts.values, 80)
    return counts[counts >= p80]


def build_cobertura_operacional(area_nome: str, polygon: sg.Polygon) -> dict:
    all_cameras = _load_all_cameras()
    cameras = all_cameras.get(area_nome, [])
    cam_coords = [(c["lat"], c["lon"]) for c in cameras]

    top_locf = _top_logradouros_brutos(polygon)

    # Get centroid per logradouro from ocorrencias
    from pipeline.processadores.ocorrencias import _load_ocorrencias
    df = _load_ocorrencias()

    pontos_cegos = []
    for locf, cnt in top_locf.items():
        group = df[df["locf"] == locf].dropna(subset=["latitude", "longitude"])
        if group.empty:
            continue
        clat = group["latitude"].mean()
        clon = group["longitude"].mean()
        nearby = [
            c for c in cam_coords
            if geodesic_distance_m(clat, clon, c[0], c[1]) <= RAIO_METROS
        ]
        if len(nearby) == 0:
            pontos_cegos.append({
                "logradouro": locf,
                "contagem_crimes": int(cnt),
                "cameras_proximas": 0,
            })

    poly_geom = sg.mapping(polygon)

    return {
        "poligono": poly_geom,
        "cameras": cameras,
        "total_cameras": len(cameras),
        "pontos_cegos": sorted(pontos_cegos, key=lambda x: x["contagem_crimes"], reverse=True),
    }
