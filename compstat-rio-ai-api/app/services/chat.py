import json
import os

from anthropic import Anthropic

from app.services.action_plan import build_action_plan
from app.services.summary import build_executive_summary


def build_prompt(message: str) -> str:
    summary = build_executive_summary()
    action_plan = build_action_plan()

    return f"""
You are CompStat Rio AI, an operational intelligence assistant for municipal public safety in Rio de Janeiro.
Always answer in Portuguese using exactly these sections:
- Diagnóstico
- Evidências
- Recomendação operacional
- Órgãos responsáveis

Executive context:
{json.dumps(summary, ensure_ascii=False, indent=2)}

Action plan:
{json.dumps(action_plan, ensure_ascii=False, indent=2)}

User question:
{message}
"""


def build_mock_chat_response(message: str) -> str:
    normalized_message = message.lower()
    summary = build_executive_summary()

    if "horário" in normalized_message or "horario" in normalized_message:
        return f"""Diagnóstico
O maior risco está concentrado no período {summary["critical_time"]}, com maior exposição em sexta-feira e sábado.

Evidências
Há convergência entre padrão temporal noturno, roubos oportunistas, baixa iluminação e rotas de fuga em áreas de baixa visibilidade.

Recomendação operacional
Antecipar a presença da Força Municipal a partir de 20h30 e manter rondas orientadas por pontos críticos até 23h30.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb e SEOP."""

    if "órgãos" in normalized_message or "orgaos" in normalized_message:
        return """Diagnóstico
A resposta precisa combinar presença operacional, correção urbana e assistência social.

Evidências
Os fatores identificados envolvem iluminação, vegetação, comércio irregular, obstrução de calçada e vulnerabilidade social.

Recomendação operacional
Abrir uma operação integrada com responsáveis e prazo por frente de atuação.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS."""

    if (
        "plano" in normalized_message
        or "ação" in normalized_message
        or "acao" in normalized_message
        or "atuar" in normalized_message
    ):
        return f"""Diagnóstico
A prioridade operacional de hoje é a {summary["priority_area"]}, pois apresenta bingo territorial e score crítico.

Evidências
O trecho combina crime, fatores urbanos, inteligência territorial e concentração no horário {summary["critical_time"]}.

Recomendação operacional
Reforçar patrulhamento noturno, corrigir iluminação, podar vegetação e ordenar calçadas em ação coordenada.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS."""

    return f"""Diagnóstico
O território analisado exige resposta integrada porque há convergência de risco criminal, urbano, temporal e territorial.

Evidências
Foram registradas 208 ocorrências no período 2023-2024, com pico entre {summary["critical_time"]} e bingo identificado em área prioritária.

Recomendação operacional
Executar operação noturna na {summary["priority_area"]}, combinando presença ostensiva e correções urbanas rápidas.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS."""


def build_chat_response(message: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return build_mock_chat_response(message)

    anthropic_client = Anthropic(api_key=api_key)
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=700,
        messages=[{"role": "user", "content": build_prompt(message)}],
    )
    text_blocks = [
        content_block.text
        for content_block in response.content
        if content_block.type == "text"
    ]

    return "\n\n".join(text_blocks)
