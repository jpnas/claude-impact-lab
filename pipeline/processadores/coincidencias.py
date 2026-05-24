from __future__ import annotations
import json
import logging
import anthropic
import shapely.geometry as sg

from pipeline.config import ANTHROPIC_API_KEY, RAIO_METROS
from pipeline.utils.geo import geodesic_distance_m

logger = logging.getLogger(__name__)


def _score(crimes: int, max_crimes: int, n_fatores: int, max_fatores: int, ponto_cego: bool) -> float:
    crime_norm = crimes / max_crimes if max_crimes > 0 else 0
    fator_norm = n_fatores / max_fatores if max_fatores > 0 else 0
    return round(crime_norm * 0.5 + fator_norm * 0.3 + (0.2 if ponto_cego else 0), 3)


def _centroid_from_heatmap(heatmap_points: list) -> tuple[float, float] | None:
    """Compute overall area centroid from heatmap points (used as fallback for logradouro location)."""
    if not heatmap_points:
        return None
    lats = [p[0] for p in heatmap_points]
    lons = [p[1] for p in heatmap_points]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def build_coincidencias(
    ocorrencias: dict,
    fatores_urbanos: dict,
    cobertura_operacional: dict,
    dinamica_criminal: dict,
    contexto_territorial: dict,
) -> dict:
    top_locf = ocorrencias.get("top_logradouros", [])
    fatores = fatores_urbanos.get("fatores", [])
    pontos_cegos_set = {p["logradouro"] for p in cobertura_operacional.get("pontos_cegos", [])}
    heatmap = ocorrencias.get("heatmap_points", [])

    # Stage 1: Deterministic spatial crosscheck
    area_centroid = _centroid_from_heatmap(heatmap)
    trechos = []
    for locf_obj in top_locf:
        locf = locf_obj["nome"]
        crimes = locf_obj["contagem"]

        # Use area centroid as proxy for logradouro location (heatmap doesn't have per-logradouro coords)
        fatores_proximos = []
        if area_centroid:
            for fator in fatores:
                for ponto in fator.get("pontos", []):
                    if (len(ponto) >= 2 and
                        geodesic_distance_m(area_centroid[0], area_centroid[1], ponto[0], ponto[1]) <= RAIO_METROS):
                        fatores_proximos.append(fator["tipo"])
                        break
        fatores_proximos = list(set(fatores_proximos))
        ponto_cego = locf in pontos_cegos_set
        trechos.append({
            "logradouro": locf,
            "crimes_no_periodo": crimes,
            "ponto_cego": ponto_cego,
            "fatores_proximos": fatores_proximos,
        })

    if not trechos:
        return {"trechos_criticos": [], "recomendacoes": {}}

    max_crimes = max(t["crimes_no_periodo"] for t in trechos)
    max_fatores = max(len(t["fatores_proximos"]) for t in trechos) or 1

    # Stage 2: LLM causal relevance evaluation
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Você é um analista de segurança pública. Avalie a relevância causal dos fatores urbanos nos trechos críticos da área.

**Perfil criminal:**
- Modalidade: {dinamica_criminal.get('modalidade_predominante', '')}
- Horário predominante: {ocorrencias.get('hora_critica', '')}
- Dia crítico: {ocorrencias.get('dia_critico', '')}
- ORCRIM: {contexto_territorial.get('orcrim_dominante', '')}

**Trechos para avaliar:**
{json.dumps(trechos, ensure_ascii=False, indent=2)}

Para cada trecho, avalie quais fatores urbanos listados em fatores_proximos são causalmente relevantes para o padrão de crime identificado (ex: iluminação só é relevante se pico for noturno).

Retorne JSON:
{{
  "trechos_avaliados": [
    {{
      "logradouro": "string (mesmo nome do trecho)",
      "fatores_relevantes": [{{"tipo": "string", "orgao": "string ou N/A", "relevancia": "string"}}],
      "justificativa": "1-2 frases"
    }}
  ],
  "recomendacoes": {{
    "rota_fm": "string",
    "horario_patrulhamento": "string",
    "modelo_emprego": "string",
    "acoes_municipais": [{{"orgao": "string", "acao": "string"}}]
  }}
}}

Retorne APENAS o JSON."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        import re
        text = message.content[0].text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
        llm_result = json.loads(text)
    except Exception as e:
        logger.warning(f"coincidencias LLM failed: {e}")
        llm_result = {"trechos_avaliados": [], "recomendacoes": {}}

    # Merge LLM evaluation with deterministic scores
    avaliados = {t["logradouro"]: t for t in llm_result.get("trechos_avaliados", [])}
    trechos_criticos = []
    for trecho in trechos:
        avaliado = avaliados.get(trecho["logradouro"], {})
        fatores_relevantes = avaliado.get("fatores_relevantes", [])
        score = _score(
            trecho["crimes_no_periodo"], max_crimes,
            len(fatores_relevantes), max_fatores,
            trecho["ponto_cego"],
        )
        trechos_criticos.append({
            "logradouro": trecho["logradouro"],
            "score_prioridade": score,
            "crimes_no_periodo": trecho["crimes_no_periodo"],
            "ponto_cego": trecho["ponto_cego"],
            "fatores_relevantes": fatores_relevantes,
            "justificativa": avaliado.get("justificativa", ""),
        })

    trechos_criticos.sort(key=lambda x: x["score_prioridade"], reverse=True)

    return {
        "trechos_criticos": trechos_criticos,
        "recomendacoes": llm_result.get("recomendacoes", {}),
    }
