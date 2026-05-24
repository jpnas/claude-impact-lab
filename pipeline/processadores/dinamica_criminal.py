from __future__ import annotations

import json
from pathlib import Path

import anthropic
import pandas as pd
import shapely.geometry as sg
from shapely.vectorized import contains

from pipeline.config import (
    ANTHROPIC_API_KEY,
    DD_CLASSES_CRIMINAIS,
    DD_TOP_N,
    DISK_DENUNCIA_CSV,
    RELINTS,
)
from pipeline.utils.docx import read_docx_text

_AREA_TO_RELINT = {
    "Rodoviária - Terminal Gentileza - Estação Leopoldina": "Rodoviaria",
    "Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria": "Metro_Botafogo",
    "Jardim de Alah": "Jardim_de_Alah",
    "Campo Grande: Estação de Trem - Calçadão": "Campo_Grande",
    "Rio Sul": "Rio_Sul",
    "Praia de Botafogo - Rua Marquês de Abrantes": "Praia_Botafogo",
    "Estações São Francisco Xavier - Afonso Pena": "Estacoes_SFX",
    "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia": "Presidente_Vargas",
}

_dd_cache: pd.DataFrame | None = None


def _load_dd() -> pd.DataFrame:
    """Load and clean Disque Denúncia, deduplicating by id_denuncia."""
    global _dd_cache
    if _dd_cache is not None:
        return _dd_cache
    df = pd.read_csv(DISK_DENUNCIA_CSV, encoding="latin1", sep=";", low_memory=False)
    df = df.drop_duplicates(subset=["id_denuncia"])
    # Fix lat/lon: string with comma as decimal separator (e.g. "-22,899555")
    for col in ["latitude", "longitude"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )
    df = df.dropna(subset=["latitude", "longitude"])
    _dd_cache = df
    return _dd_cache


def _top_dd_for_area(polygon: sg.Polygon) -> list[str]:
    """Return top DD_TOP_N relatos for the area, filtered by criminal classes."""
    df = _load_dd()
    # Filter by criminal classes
    df_filtered = df[df["assuntos.classe"].isin(DD_CLASSES_CRIMINAIS)]
    # Vectorised spatial filter (lon, lat order for shapely)
    lons = df_filtered["longitude"].to_numpy(dtype=float)
    lats = df_filtered["latitude"].to_numpy(dtype=float)
    mask = contains(polygon, lons, lats)
    df_area = df_filtered.loc[df_filtered.index[mask]]
    # Sort by date DESC, top DD_TOP_N
    df_area = df_area.sort_values("data_denuncia", ascending=False).head(DD_TOP_N)
    return df_area["relato_redacted"].fillna("").tolist()


def _find_relint(area_nome: str) -> Path | None:
    """Locate the DOCX RELINT file matching the area name."""
    keyword = _AREA_TO_RELINT.get(area_nome, "")
    if not keyword:
        return None
    for f in RELINTS.glob("*.docx"):
        if keyword.lower() in f.name.lower():
            return f
    return None


def _parse_llm_json(text: str) -> dict:
    """Strip markdown fences and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def build_dinamica_criminal(
    area_nome: str,
    polygon: sg.Polygon,
    orcrim_dominante: str,
) -> dict:
    """LLM synthesises RELINT + top 40 Disque Denúncia into criminal dynamics summary."""
    relint_path = _find_relint(area_nome)
    relint_text = (
        read_docx_text(relint_path) if relint_path else "(RELINT não disponível)"
    )
    relatos = _top_dd_for_area(polygon)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Você é um analista de inteligência criminal. Analise o Relatório de Inteligência (RELINT) e os relatos do Disque Denúncia para a área FM "{area_nome}".

**Contexto:** A organização criminosa dominante na área é {orcrim_dominante}.

**RELINT:**
{relint_text[:8000]}

**Top {len(relatos)} relatos Disque Denúncia (mais recentes):**
{chr(10).join(f'- {r}' for r in relatos)}

Retorne um JSON com exatamente estas chaves:
{{
  "modalidade_predominante": "string",
  "modus_operandi": "string",
  "rotas_de_fuga": ["string"],
  "pontos_de_receptacao": ["string"],
  "perfil_suspeitos": "string",
  "orcrim_influencia": "string",
  "narrativa_completa": "parágrafo de 3-5 frases"
}}

Retorne APENAS o JSON, sem markdown."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_llm_json(message.content[0].text)


def enrich_ocorrencias_dd(base: dict, polygon: sg.Polygon) -> dict:
    """Enrich ocorrencias dict with Disque Denúncia signals via LLM."""
    relatos = _top_dd_for_area(polygon)
    if not relatos:
        return base

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Analise estes {len(relatos)} relatos do Disque Denúncia e extraia padrões criminais não capturados pelas ocorrências registradas. Retorne JSON:
{{
  "sinais_dd": ["padrão 1", "padrão 2"],
  "locais_suspeitos_mencionados": ["local 1", "local 2"]
}}

Relatos:
{chr(10).join(f'- {r}' for r in relatos)}

Retorne APENAS o JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    extra = _parse_llm_json(message.content[0].text)
    return {**base, **extra}


def enrich_fatores_relint(base: dict, area_nome: str) -> dict:
    """Enrich fatores dict with urban factors extracted from RELINT via LLM."""
    relint_path = _find_relint(area_nome)
    if not relint_path:
        return base

    relint_text = read_docx_text(relint_path)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Do seguinte RELINT, extraia fatores urbanos que facilitam crimes mas não estão nos dados estruturados de campo.

RELINT:
{relint_text[:6000]}

Retorne JSON:
{{"fatores_adicionais_relint": ["fator 1", "fator 2"]}}

Retorne APENAS o JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    extra = _parse_llm_json(message.content[0].text)
    return {**base, **extra}
