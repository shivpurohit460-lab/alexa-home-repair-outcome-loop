from __future__ import annotations

from alexa_outcome_loop.agentcore_app import invoke_payload
from alexa_outcome_loop.agentcore_tools import book_home_service, create_repair_case
from alexa_outcome_loop.store import STORE


class FakeAgent:
    def __call__(self, prompt: str) -> str:
        assert "AC" in prompt
        created = create_repair_case(
            "AC is running but the living room is not cooling",
            room="living room",
            target_temperature_c=24.0,
        )
        case_id = created["case"]["case_id"]
        book_home_service(case_id, eta_minutes=30)
        return f"Repair case {case_id} opened and service booked."


def test_agentcore_payload_requires_prompt() -> None:
    assert invoke_payload({}) == {"error": "payload.prompt is required"}


def test_agentcore_payload_returns_auditable_tool_trace() -> None:
    STORE.reset()

    response = invoke_payload(
        {"prompt": "My AC is broken. Handle it and make sure it is actually fixed."},
        agent=FakeAgent(),
    )

    assert response["runtime"] == "amazon-bedrock-agentcore"
    assert response["framework"] == "strands-agents"
    assert response["model_id"] == "global.anthropic.claude-sonnet-4-6"
    assert [event["tool"] for event in response["tool_trace"]] == [
        "create_repair_case",
        "book_home_service",
    ]
    assert response["tool_trace"][0]["result"]["case"]["status"] == "open"
    assert response["tool_trace"][1]["result"]["service_status"] == "scheduled"


def test_tool_trace_is_reset_for_each_invocation() -> None:
    STORE.reset()

    first = invoke_payload(
        {"prompt": "My AC is broken. Handle it and make sure it is actually fixed."},
        agent=FakeAgent(),
    )
    second = invoke_payload(
        {"prompt": "My AC is broken. Handle it and make sure it is actually fixed."},
        agent=FakeAgent(),
    )

    assert len(first["tool_trace"]) == 2
    assert len(second["tool_trace"]) == 2
