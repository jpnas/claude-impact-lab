from typing import Any, Literal


RiskLevel = Literal["baixo", "médio", "alto", "crítico"]
PriorityLevel = Literal["Baixa", "Média", "Alta", "Emergencial"]


def calculate_risk_score(segment: dict[str, Any]) -> int:
    return int(
        segment["crime_score"]
        + segment["urban_factor_score"]
        + segment["intelligence_score"]
        + segment["temporal_score"]
    )


def classify_risk(total_score: int) -> RiskLevel:
    if total_score > 100:
        return "crítico"

    if total_score >= 70:
        return "alto"

    if total_score >= 40:
        return "médio"

    return "baixo"


def calculate_bingo(segment: dict[str, Any]) -> bool:
    layer_scores = [
        segment["crime_score"],
        segment["urban_factor_score"],
        segment["intelligence_score"],
        segment["temporal_score"],
    ]
    elevated_layers = [
        layer_score for layer_score in layer_scores if int(layer_score) > 20
    ]

    return len(elevated_layers) >= 3


def priority_from_risk(risk_level: RiskLevel) -> PriorityLevel:
    priority_by_risk: dict[RiskLevel, PriorityLevel] = {
        "baixo": "Baixa",
        "médio": "Média",
        "alto": "Alta",
        "crítico": "Emergencial",
    }

    return priority_by_risk[risk_level]


def enrich_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched_segments: list[dict[str, Any]] = []

    for segment in segments:
        total_score = calculate_risk_score(segment)
        risk_level = classify_risk(total_score)
        enriched_segments.append(
            {
                **segment,
                "total_score": total_score,
                "totalScore": total_score,
                "risk_level": risk_level,
                "riskLevel": risk_level,
                "priority": priority_from_risk(risk_level),
                "bingo": calculate_bingo(segment),
            }
        )

    return enriched_segments


def find_priority_segment(segments: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        segments,
        key=lambda segment: int(segment["total_score"]),
        reverse=True,
    )[0]
