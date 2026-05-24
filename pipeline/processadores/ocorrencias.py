from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import date
import shapely.geometry as sg

from pipeline.config import OCORRENCIAS_CSV, JANELA_MESES
from pipeline.utils.geo import point_in_polygon


def _load_ocorrencias() -> pd.DataFrame:
    df = pd.read_csv(OCORRENCIAS_CSV, encoding="utf-8", low_memory=False)
    # 'data' column contains crime date in DD/MM/YYYY format
    df["data_fato"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    return df.dropna(subset=["data_fato"])


def _spatial_filter(df: pd.DataFrame, polygon: sg.Polygon) -> pd.DataFrame:
    mask = df.apply(
        lambda r: point_in_polygon(r["latitude"], r["longitude"], polygon)
        if pd.notna(r.get("latitude")) and pd.notna(r.get("longitude"))
        else False,
        axis=1,
    )
    return df[mask]


def build_ocorrencias_base(polygon: sg.Polygon, ref_date: date | None = None) -> dict:
    df = _load_ocorrencias()
    if ref_date is None:
        # Default to the latest date in the dataset so the window always captures data.
        # date.today() would exceed the dataset range after the data cut-off date.
        ref_date = df["data_fato"].max().date()
    df_area = _spatial_filter(df, polygon)

    cutoff_end = pd.Timestamp(ref_date)
    cutoff_start = cutoff_end - pd.DateOffset(months=JANELA_MESES)
    cutoff_prev_start = cutoff_start - pd.DateOffset(months=JANELA_MESES)

    periodo = df_area[
        (df_area["data_fato"] >= cutoff_start) & (df_area["data_fato"] < cutoff_end)
    ]
    prev = df_area[
        (df_area["data_fato"] >= cutoff_prev_start) & (df_area["data_fato"] < cutoff_start)
    ]

    total = len(periodo)
    total_prev = len(prev)
    if total_prev > 0:
        variacao = f"{round((total - total_prev) / total_prev * 100):+d}%"
    else:
        variacao = "N/A"

    # desc_delito is the crime type description column
    por_tipo = periodo["desc_delito"].value_counts().head(10).to_dict()

    # hora is stored as time string "HH:MM:SS" — extract the hour portion
    hora_series = periodo["hora"].dropna().str.split(":").str[0]
    por_hora = hora_series.value_counts().to_dict()

    # dia_semana is a string with Portuguese day names (e.g. "Segunda", "Terca", ...)
    # ~22 nulls across the full dataset — safe to drop
    por_dia = periodo["dia_semana"].dropna().value_counts().to_dict()

    top_locf = periodo["locf"].dropna().value_counts().head(10)

    heatmap_points = []
    for _, row in periodo.dropna(subset=["latitude", "longitude"]).iterrows():
        heatmap_points.append([round(row["latitude"], 4), round(row["longitude"], 4), 1.0])

    hora_critica = max(por_hora, key=por_hora.get) + "h" if por_hora else None
    dia_critico = max(por_dia, key=por_dia.get) if por_dia else None

    return {
        "total_periodo": total,
        "variacao_yoy": variacao,
        "periodo_referencia": f"{cutoff_start.strftime('%Y-%m')} a {cutoff_end.strftime('%Y-%m')}",
        "por_tipo": por_tipo,
        "por_hora": por_hora,
        "por_dia_semana": por_dia,
        "hora_critica": hora_critica,
        "dia_critico": dia_critico,
        "top_logradouros": [
            {"nome": nome, "contagem": int(cnt)} for nome, cnt in top_locf.items()
        ],
        "heatmap_points": heatmap_points[:500],  # cap for Supabase JSON size
    }
