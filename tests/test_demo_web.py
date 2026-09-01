from starlette.testclient import TestClient

from alexa_outcome_loop.demo_engine import build_demo_timeline
from alexa_outcome_loop.demo_web import app


def test_demo_engine_returns_seven_step_verified_story() -> None:
    payload = build_demo_timeline()

    assert payload["demo_mode"] == "synthetic_deterministic"
    assert payload["verified"] is True
    assert [event["step"] for event in payload["events"]] == list(range(1, 8))
    assert payload["events"][2]["state"] == "provider_complete"
    assert payload["events"][3]["state"] == "verification_failed"
    assert payload["events"][4]["state"] == "case_reopened"
    assert payload["events"][-1]["state"] == "verified_resolved"


def test_demo_web_surface_and_api() -> None:
    client = TestClient(app)

    home = client.get("/")
    assert home.status_code == 200
    assert "SIMULATED EXPERIENCE" in home.text
    assert "Provider complete ≠ home recovered" in home.text

    response = client.post("/api/demo/run")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified"] is True
    assert len(payload["events"]) == 7
