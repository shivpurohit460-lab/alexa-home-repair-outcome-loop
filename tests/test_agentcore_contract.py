from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

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


class InterleavingAgent:
    """Force two invocations to overlap between their first and second tool calls."""

    def __init__(self, label: str, barrier: Barrier) -> None:
        self.label = label
        self.barrier = barrier

    def __call__(self, prompt: str) -> str:
        assert self.label in prompt
        created = create_repair_case(
            f"AC issue for {self.label}",
            room="living room",
            target_temperature_c=24.0,
        )
        case_id = created["case"]["case_id"]
        self.barrier.wait(timeout=5)
        book_home_service(case_id, provider_name=f"{self.label} HVAC", eta_minutes=30)
        return f"{self.label}:{case_id}"


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


def test_concurrent_invocations_do_not_mix_tool_traces() -> None:
    STORE.reset()
    barrier = Barrier(2)

    def run(label: str) -> dict:
        return invoke_payload(
            {"prompt": f"My AC is broken for {label}."},
            agent=InterleavingAgent(label, barrier),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(run, "alpha")
        second_future = executor.submit(run, "beta")
        first = first_future.result(timeout=10)
        second = second_future.result(timeout=10)

    traces = {first["result"].split(":", 1)[0]: first["tool_trace"],
              second["result"].split(":", 1)[0]: second["tool_trace"]}

    for label in ("alpha", "beta"):
        trace = traces[label]
        assert [event["tool"] for event in trace] == [
            "create_repair_case",
            "book_home_service",
        ]
        assert trace[0]["arguments"]["issue"] == f"AC issue for {label}"
        assert trace[1]["arguments"]["provider_name"] == f"{label} HVAC"
