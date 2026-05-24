from __future__ import annotations

import pandas as pd
import shapely.wkt
import shapely.geometry as sg

from pipeline.config import DOMINIO_CSV, PSR_XLSX


_dominio_cache: pd.DataFrame | None = None
_psr_cache: pd.DataFrame | None = None


def _load_dominio() -> pd.DataFrame:
    global _dominio_cache
    if _dominio_cache is None:
        df = pd.read_csv(DOMINIO_CSV, encoding="utf-8", low_memory=False)
        # Columns: nome_territorio, dominio_orcrim, geometria (WKT, EPSG:4326)
        df["geom"] = df["geometria"].apply(lambda wkt: shapely.wkt.loads(wkt) if pd.notna(wkt) else None)
        _dominio_cache = df.dropna(subset=["geom"])
    return _dominio_cache


def _load_psr() -> pd.DataFrame:
    global _psr_cache
    if _psr_cache is None:
        # Columns include: Latitude, Longitude, Ano (2020, 2022, 2024)
        df = pd.read_excel(PSR_XLSX, engine="openpyxl", usecols=["Latitude", "Longitude", "Ano"])
        _psr_cache = df.dropna(subset=["Latitude", "Longitude"])
    return _psr_cache


def build_contexto_territorial(polygon: sg.Polygon) -> dict:
    # --- Domínio territorial: ORCRIM area proportions ---
    # FM polygons are small street-level areas. ORCRIM territories (favelas) are
    # nearby but rarely fully overlapping. Strategy:
    # 1. Try direct intersection first.
    # 2. If no intersections found, expand with a ~500m buffer (~0.0045 degrees)
    #    and compute intersected area within the buffer to rank ORCRIM presence.
    df_dom = _load_dominio()

    def _compute_orcrim_areas(search_polygon: sg.Polygon) -> dict[str, float]:
        areas: dict[str, float] = {}
        for _, row in df_dom.iterrows():
            geom = row["geom"]
            if not geom.is_valid:
                geom = geom.buffer(0)
            try:
                intersection = search_polygon.intersection(geom)
            except Exception:
                continue
            if intersection.is_empty:
                continue
            area = intersection.area
            if area <= 0:
                continue
            orcrim = str(row["dominio_orcrim"]).strip()
            areas[orcrim] = areas.get(orcrim, 0.0) + area
        return areas

    orcrim_areas = _compute_orcrim_areas(polygon)

    # Fall back to 500m buffer (~0.0045 degrees) if no direct intersections
    if not orcrim_areas:
        buffer_deg = 0.0045  # roughly 500m
        buffered = polygon.buffer(buffer_deg)
        orcrim_areas = _compute_orcrim_areas(buffered)

    total_intersected_area = sum(orcrim_areas.values())

    if total_intersected_area > 0:
        orcrim_por_tipo = {
            orcrim: round(area / total_intersected_area, 4)
            for orcrim, area in sorted(orcrim_areas.items(), key=lambda x: -x[1])
        }
        orcrim_dominante = max(orcrim_areas, key=orcrim_areas.get)
    else:
        orcrim_por_tipo = {}
        orcrim_dominante = "Sem dados"

    # --- PSR: Population in Street Situation spatial join ---
    df_psr = _load_psr()

    # Vectorized point-in-polygon using shapely.vectorized
    from shapely.vectorized import contains as sv_contains
    lons = df_psr["Longitude"].to_numpy(dtype=float)
    lats = df_psr["Latitude"].to_numpy(dtype=float)
    mask = sv_contains(polygon, lons, lats)
    df_in = df_psr[mask].copy()

    psr_by_year: dict[int, int] = {}
    for ano in [2020, 2022, 2024]:
        psr_by_year[ano] = int((df_in["Ano"] == ano).sum())

    # Determine trend based on 2020→2024 trajectory
    t2020, t2022, t2024 = psr_by_year[2020], psr_by_year[2022], psr_by_year[2024]
    if t2024 > t2020 * 1.05:
        tendencia = "crescente"
    elif t2024 < t2020 * 0.95:
        tendencia = "decrescente"
    else:
        tendencia = "estável"

    # Build list of PSR points (lat, lon) for heatmap
    pontos_psr = [
        [row["Latitude"], row["Longitude"]]
        for _, row in df_in.iterrows()
    ]

    return {
        "orcrim_dominante": orcrim_dominante,
        "orcrim_por_tipo": orcrim_por_tipo,
        "comunidades_proximas": [],
        "psr": {
            "total_2020": t2020,
            "total_2022": t2022,
            "total_2024": t2024,
            "tendencia": tendencia,
            "pontos": pontos_psr,
        },
    }
