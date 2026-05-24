from app.services.action_plan import build_action_plan
from app.services.chat import build_mock_chat_response
from app.services.risk import calculate_bingo, calculate_risk_score, classify_risk
from app.services.summary import build_executive_summary


def test_risk_engine_calculates_score_and_bingo():
    segment = {
        "crime_score": 35,
        "urban_factor_score": 30,
        "intelligence_score": 25,
        "temporal_score": 20,
    }

    assert calculate_risk_score(segment) == 110
    assert classify_risk(110) == "crítico"
    assert calculate_bingo(segment) is True


def test_summary_contains_priority_area_and_bingo():
    summary = build_executive_summary()

    assert summary["priority_area"] == "Rua Lauro Müller"
    assert summary["critical_time"] == "21h-23h"
    assert summary["bingo_identified"] is True
    assert "Reforçar patrulhamento noturno" in summary["main_recommendations"][0]


def test_action_plan_contains_municipal_responsibles():
    action_plan = build_action_plan()

    assert len(action_plan) == 5
    assert action_plan[0]["action"] == "Reforço de patrulhamento noturno"
    assert action_plan[0]["responsible"] == "Força Municipal"
    assert action_plan[2]["responsible"] == "RioLuz"


def test_mock_chat_returns_required_sections():
    answer = build_mock_chat_response("Qual o plano de ação?")

    assert "Diagnóstico" in answer
    assert "Evidências" in answer
    assert "Recomendação operacional" in answer
    assert "Órgãos responsáveis" in answer
