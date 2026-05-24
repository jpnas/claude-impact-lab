from typing import Any

from app.services.action_plan import build_action_plan
from app.services.data_loader import load_area_data
from app.services.risk import enrich_segments, find_priority_segment


def build_executive_summary() -> dict[str, Any]:
    area_data = load_area_data()
    enriched_segments = enrich_segments(area_data["segments"])
    priority_segment = find_priority_segment(enriched_segments)
    bingo_segments = [
        segment for segment in enriched_segments if bool(segment["bingo"])
    ]
    action_plan = build_action_plan()
    readable_peak_time = str(area_data["peak_time"]).replace("-", " e ")

    return {
        "executive_summary": (
            "O território analisado apresenta convergência entre ocorrências criminais, "
            "baixa qualidade urbana, inteligência de rotas de fuga e concentração temporal "
            "noturna. A Rua Lauro Müller deve ser tratada como prioridade operacional imediata."
        ),
        "executiveSummary": (
            "O território analisado apresenta convergência entre ocorrências criminais, "
            "baixa qualidade urbana, inteligência de rotas de fuga e concentração temporal "
            "noturna. A Rua Lauro Müller deve ser tratada como prioridade operacional imediata."
        ),
        "priority_area": priority_segment["name"],
        "priorityArea": priority_segment["name"],
        "critical_time": area_data["peak_time"],
        "criticalTime": area_data["peak_time"],
        "bingo_identified": len(bingo_segments) > 0,
        "bingoIdentified": len(bingo_segments) > 0,
        "main_recommendations": [
            f"Reforçar patrulhamento noturno nos trechos críticos entre {readable_peak_time}.",
            "Acionar RioLuz e Comlurb para reduzir fatores urbanos que favorecem oportunidade criminal.",
            "Integrar SEOP, SMAS/SMS e Força Municipal em operação territorial coordenada.",
            (
                f"Executar primeiro: {action_plan[0]['action']}, "
                f"sob responsabilidade da {action_plan[0]['responsible']}."
            ),
        ],
        "mainRecommendations": [
            f"Reforçar patrulhamento noturno nos trechos críticos entre {readable_peak_time}.",
            "Acionar RioLuz e Comlurb para reduzir fatores urbanos que favorecem oportunidade criminal.",
            "Integrar SEOP, SMAS/SMS e Força Municipal em operação territorial coordenada.",
            (
                f"Executar primeiro: {action_plan[0]['action']}, "
                f"sob responsabilidade da {action_plan[0]['responsible']}."
            ),
        ],
    }
