from __future__ import annotations
import pandas as pd
import shapely.geometry as sg

from pipeline.config import FATORES_CSV
from pipeline.utils.geo import point_in_polygon


_fatores_cache: pd.DataFrame | None = None


def _load_fatores() -> pd.DataFrame:
    global _fatores_cache
    if _fatores_cache is None:
        df = pd.read_csv(FATORES_CSV, encoding="utf-8", low_memory=False)
        # coordenada_x = lat, coordenada_y = lon (invertido na fonte)
        df = df.rename(columns={"coordenada_x": "latitude", "coordenada_y": "longitude"})
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        _fatores_cache = df.dropna(subset=["latitude", "longitude"])
    return _fatores_cache


def _spatial_filter(df: pd.DataFrame, polygon: sg.Polygon) -> pd.DataFrame:
    """Vectorized spatial filter using shapely.vectorized.contains."""
    valid = df["latitude"].notna() & df["longitude"].notna()
    df_valid = df[valid].copy()
    if df_valid.empty:
        return df_valid
    from shapely.vectorized import contains
    lons = df_valid["longitude"].to_numpy(dtype=float)
    lats = df_valid["latitude"].to_numpy(dtype=float)
    mask = contains(polygon, lons, lats)
    return df_valid[mask]


def build_fatores_urbanos_base(area_nome: str, polygon: sg.Polygon) -> dict:
    df = _load_fatores()

    # Try subarea_nome filter first (fast); fallback to spatial join
    df_area = df[df["subarea_nome"] == area_nome]
    if df_area.empty:
        df_area = _spatial_filter(df, polygon)

    tipo_col = "tipo_ocorrencia_descricao"
    orgao_col = "orgao_responsavel"

    fatores: list[dict] = []
    por_orgao: dict[str, int] = {}

    for (tipo, orgao), grp in df_area.groupby([tipo_col, orgao_col], dropna=False):
        pontos = [
            [round(float(r.latitude), 4), round(float(r.longitude), 4)]
            for r in grp[["latitude", "longitude"]].itertuples()
        ]
        cnt = len(grp)
        fatores.append({
            "tipo": str(tipo),
            "orgao_responsavel": str(orgao),
            "contagem": cnt,
            "pontos": pontos,
        })
        por_orgao[str(orgao)] = por_orgao.get(str(orgao), 0) + cnt

    fatores.sort(key=lambda x: x["contagem"], reverse=True)

    return {
        "fatores": fatores,
        "por_orgao": por_orgao,
        "fatores_adicionais_relint": [],  # filled in Phase 2
    }
