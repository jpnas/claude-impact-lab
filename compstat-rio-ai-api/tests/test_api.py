from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_summary_endpoint_returns_executive_context():
    response = client.get("/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["priority_area"] == "Rua Lauro Müller"
    assert payload["bingo_identified"] is True


def test_action_plan_endpoint_returns_actions():
    response = client.get("/action-plan")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["actions"]) == 5


def test_chat_endpoint_returns_structured_answer():
    response = client.post(
        "/chat",
        json={"message": "Onde a FM deve atuar hoje à noite?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Diagnóstico" in payload["answer"]
    assert "Rua Lauro Müller" in payload["answer"]
