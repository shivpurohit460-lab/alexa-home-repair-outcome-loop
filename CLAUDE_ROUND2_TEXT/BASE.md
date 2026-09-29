# BASE · Exact Git source snapshot for Claude review

Source commit: `3d396517485d8096da91397e3adf142ac7e7d7ca`.
This file is a verbatim concatenation of source files fetched through the connected GitHub app. Each included file has its original Git blob SHA below. Missing new test files in BASE are expected. This copy is for source review, not a runnable directory. Original branch contents remain unchanged.

## pyproject.toml

Blob SHA-1: `435c569b6f435c144daead32e6b9fbd3ba2c57ef`

~~~~toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "alexa-home-repair-outcome-loop"
version = "0.1.0"
description = "Outcome-verifying home repair agent for the Amazon Developer Hackathon 2026"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [
  { name = "PUROHIT SHIVKUMAR VIJAY" }
]
dependencies = [
  "mcp==1.30.0",
  "strands-agents==1.56.0",
  "bedrock-agentcore==1.23.1",
  "starlette==1.6.0",
  "uvicorn==0.53.0",
]

[project.optional-dependencies]
dev = [
  "pytest==8.4.2",
  "ruff==0.16.8",
]

[project.scripts]
outcome-loop-agent = "alexa_outcome_loop.agent:main"
outcome-loop-mcp = "alexa_outcome_loop.mcp_server:main"
outcome-loop-demo = "alexa_outcome_loop.demo_web:main"

[tool.hatch.build.targets.wheel]
packages = ["src/alexa_outcome_loop"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

~~~~

## .github/workflows/ci.yml

Blob SHA-1: `f9201a0132a51ed4b9f44dc61932ee42c7736e08`

~~~~yaml
name: ci

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.13']
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
        with:
          persist-credentials: false
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: pip install -e '.[dev]'
      - name: Ruff
        run: ruff check .
      - name: Tests
        run: pytest -q

~~~~

## src/alexa_outcome_loop/domain.py

Blob SHA-1: `ba9de7407e653084ecc7652ddbab199118fe067b`

~~~~python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class CaseStatus(StrEnum):
    OPEN = "open"
    SERVICE_BOOKED = "service_booked"
    AWAITING_VERIFICATION = "awaiting_verification"
    REOPENED = "reopened"
    ESCALATED = "escalated"
    VERIFIED_RESOLVED = "verified_resolved"


class ServiceStatus(StrEnum):
    NOT_BOOKED = "not_booked"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PROVIDER_COMPLETE = "provider_complete"
    REOPENED = "reopened"


@dataclass(slots=True)
class HomeState:
    temperature_c: float = 30.0
    hvac_running: bool = False
    observed_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RepairCase:
    case_id: str
    issue: str
    room: str
    target_temperature_c: float
    status: CaseStatus = CaseStatus.OPEN
    service_status: ServiceStatus = ServiceStatus.NOT_BOOKED
    provider_name: str | None = None
    provider_reference: str | None = None
    escalation_count: int = 0
    last_failure_reason: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["service_status"] = self.service_status.value
        return payload

~~~~

## src/alexa_outcome_loop/store.py

Blob SHA-1: `d66ed56972ed783834bcfe632a1a8a53643a18fe`

~~~~python
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4

from .domain import HomeState, RepairCase


@dataclass
class InMemoryStore:
    """Prototype state store.

    Intentionally in-memory for the hackathon's deterministic simulator phase.
    AgentCore-backed state can replace this adapter later without changing the MCP tool contract.
    """

    cases: dict[str, RepairCase] = field(default_factory=dict)
    home_states: dict[str, HomeState] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False)

    def create_case(
        self,
        *,
        issue: str,
        room: str,
        target_temperature_c: float,
    ) -> RepairCase:
        case_id = f"repair-{uuid4().hex[:10]}"
        case = RepairCase(
            case_id=case_id,
            issue=issue,
            room=room,
            target_temperature_c=target_temperature_c,
        )
        with self._lock:
            self.cases[case_id] = case
            self.home_states[case_id] = HomeState()
        return case

    def get_case(self, case_id: str) -> RepairCase:
        try:
            return self.cases[case_id]
        except KeyError as exc:
            raise ValueError(f"Unknown repair case: {case_id}") from exc

    def get_home_state(self, case_id: str) -> HomeState:
        self.get_case(case_id)
        return self.home_states[case_id]

    def reset(self) -> None:
        with self._lock:
            self.cases.clear()
            self.home_states.clear()


STORE = InMemoryStore()

~~~~

## src/alexa_outcome_loop/simulators.py

Blob SHA-1: `bc291c828c93d7493a64394e59513f677ff07b08`

~~~~python
from __future__ import annotations

from .domain import CaseStatus, HomeState, ServiceStatus, utc_now
from .store import STORE


class ServiceSimulator:
    def mark_in_progress(self, case_id: str) -> dict:
        case = STORE.get_case(case_id)
        case.service_status = ServiceStatus.IN_PROGRESS
        case.touch()
        return case.to_dict()

    def mark_provider_complete(self, case_id: str) -> dict:
        """Simulate a provider saying the job is complete.

        This does not change the home state. That separation is the core of the demo:
        workflow completion is not equivalent to outcome completion.
        """
        case = STORE.get_case(case_id)
        case.service_status = ServiceStatus.PROVIDER_COMPLETE
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.touch()
        return case.to_dict()


class HomeSimulator:
    def set_state(self, case_id: str, *, temperature_c: float, hvac_running: bool) -> dict:
        STORE.get_case(case_id)
        state = HomeState(
            temperature_c=float(temperature_c),
            hvac_running=bool(hvac_running),
            observed_at=utc_now(),
        )
        STORE.home_states[case_id] = state
        return state.to_dict()


SERVICE_SIMULATOR = ServiceSimulator()
HOME_SIMULATOR = HomeSimulator()

~~~~

## src/alexa_outcome_loop/tools.py

Blob SHA-1: `2be54b5d509991c2869381bb16889f6778efe41a`

~~~~python
from __future__ import annotations

from .domain import CaseStatus, ServiceStatus
from .store import STORE


def create_repair_case(
    issue: str,
    room: str = "living room",
    target_temperature_c: float = 24.0,
) -> dict:
    """Create a repair case and define the observable success condition.

    For the hackathon AC demo, success means the room temperature is at or below
    target_temperature_c plus the verification tolerance.
    """
    if not issue.strip():
        raise ValueError("issue must not be empty")
    if not 16.0 <= target_temperature_c <= 30.0:
        raise ValueError("target_temperature_c must be between 16 and 30")

    case = STORE.create_case(
        issue=issue.strip(),
        room=room.strip() or "living room",
        target_temperature_c=float(target_temperature_c),
    )
    return {
        "case": case.to_dict(),
        "success_criterion": {
            "type": "temperature_threshold",
            "target_temperature_c": case.target_temperature_c,
            "meaning": "The workflow remains open until home-state evidence supports recovery.",
        },
    }


def book_home_service(
    case_id: str,
    provider_name: str = "CoolCare HVAC",
    eta_minutes: int = 45,
) -> dict:
    """Book a deterministic home-service provider for an existing repair case."""
    if eta_minutes < 1:
        raise ValueError("eta_minutes must be positive")
    case = STORE.get_case(case_id)
    case.provider_name = provider_name.strip() or "CoolCare HVAC"
    case.provider_reference = f"svc-{case_id.split('-', 1)[-1]}"
    case.service_status = ServiceStatus.SCHEDULED
    case.status = CaseStatus.SERVICE_BOOKED
    case.touch()
    return {
        "case_id": case.case_id,
        "provider": case.provider_name,
        "provider_reference": case.provider_reference,
        "service_status": case.service_status.value,
        "eta_minutes": int(eta_minutes),
        "closure_policy": "Provider completion is evidence, not final outcome proof.",
    }


def get_service_status(case_id: str) -> dict:
    """Return the provider-side workflow status for a repair case."""
    case = STORE.get_case(case_id)
    return {
        "case_id": case.case_id,
        "provider": case.provider_name,
        "provider_reference": case.provider_reference,
        "service_status": case.service_status.value,
        "case_status": case.status.value,
        "updated_at": case.updated_at,
    }


def read_home_state(case_id: str) -> dict:
    """Read outcome-side evidence from the deterministic thermostat simulator."""
    case = STORE.get_case(case_id)
    state = STORE.get_home_state(case_id)
    return {
        "case_id": case.case_id,
        "room": case.room,
        "target_temperature_c": case.target_temperature_c,
        "home_state": state.to_dict(),
    }


def verify_outcome(case_id: str, tolerance_c: float = 1.0) -> dict:
    """Verify whether the user's intended outcome is actually supported by evidence.

    A provider's completion signal is necessary but not sufficient. For the AC demo,
    the room must also be within the user's target-temperature tolerance.
    """
    if not 0.0 <= tolerance_c <= 5.0:
        raise ValueError("tolerance_c must be between 0 and 5")

    case = STORE.get_case(case_id)
    state = STORE.get_home_state(case_id)
    provider_complete = case.service_status == ServiceStatus.PROVIDER_COMPLETE
    threshold = case.target_temperature_c + float(tolerance_c)
    home_recovered = state.temperature_c <= threshold
    verified = provider_complete and home_recovered

    if verified:
        case.status = CaseStatus.VERIFIED_RESOLVED
        case.last_failure_reason = None
        case.touch()
        recommendation = "close_case"
        explanation = "Provider completion and home-state evidence agree."
    else:
        case.status = CaseStatus.AWAITING_VERIFICATION
        reasons: list[str] = []
        if not provider_complete:
            reasons.append("provider_has_not_reported_completion")
        if not home_recovered:
            reasons.append(
                f"temperature_{state.temperature_c:.1f}C_above_threshold_{threshold:.1f}C"
            )
        case.last_failure_reason = ";".join(reasons)
        case.touch()
        recommendation = "reopen_or_escalate"
        explanation = "Workflow completion is not yet supported by outcome evidence."

    return {
        "case_id": case.case_id,
        "verified": verified,
        "provider_complete": provider_complete,
        "home_recovered": home_recovered,
        "observed_temperature_c": state.temperature_c,
        "acceptable_temperature_c": threshold,
        "recommendation": recommendation,
        "explanation": explanation,
        "case_status": case.status.value,
    }


def reopen_or_escalate_case(case_id: str, reason: str | None = None) -> dict:
    """Keep responsibility open after failed verification and request recovery."""
    case = STORE.get_case(case_id)
    if case.status == CaseStatus.VERIFIED_RESOLVED:
        return {
            "case_id": case.case_id,
            "action": "no_op",
            "case_status": case.status.value,
            "message": "Case is already outcome-verified and closed.",
        }

    case.escalation_count += 1
    case.service_status = ServiceStatus.REOPENED
    case.status = CaseStatus.ESCALATED if case.escalation_count > 1 else CaseStatus.REOPENED
    case.last_failure_reason = reason or case.last_failure_reason or "outcome_not_verified"
    case.touch()

    return {
        "case_id": case.case_id,
        "action": "escalated" if case.escalation_count > 1 else "reopened",
        "escalation_count": case.escalation_count,
        "reason": case.last_failure_reason,
        "provider_reference": case.provider_reference,
        "service_status": case.service_status.value,
        "case_status": case.status.value,
    }

~~~~

## src/alexa_outcome_loop/demo_engine.py

Blob SHA-1: `027dad4e7b91d075004ef7b342f6717f13ef1614`

~~~~python
from __future__ import annotations

from .simulators import HOME_SIMULATOR, SERVICE_SIMULATOR
from .store import STORE
from .tools import (
    book_home_service,
    create_repair_case,
    reopen_or_escalate_case,
    verify_outcome,
)


def build_demo_timeline() -> dict:
    """Run the deterministic seven-step judge demo using production domain logic."""
    STORE.reset()

    created = create_repair_case(
        "AC is running but the living room is not cooling",
        room="living room",
        target_temperature_c=24.0,
    )
    case_id = created["case"]["case_id"]
    events: list[dict] = [
        {
            "step": 1,
            "state": "request_received",
            "title": "User asks for an outcome",
            "detail": "My AC is broken. Handle it and make sure it is actually fixed.",
            "tone": "neutral",
        }
    ]

    booking = book_home_service(case_id, eta_minutes=30)
    events.append(
        {
            "step": 2,
            "state": "service_booked",
            "title": "Repair booked",
            "detail": f"{booking['provider']} · ETA {booking['eta_minutes']} min",
            "tone": "progress",
        }
    )

    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    events.append(
        {
            "step": 3,
            "state": "provider_complete",
            "title": "Provider reports complete",
            "detail": "Workflow says done. Outcome is still unverified.",
            "tone": "warning",
        }
    )

    HOME_SIMULATOR.set_state(case_id, temperature_c=29.2, hvac_running=True)
    failed = verify_outcome(case_id)
    events.append(
        {
            "step": 4,
            "state": "verification_failed",
            "title": "Outcome check fails",
            "detail": (
                f"Thermostat: {failed['observed_temperature_c']:.1f}°C · "
                f"acceptable ≤ {failed['acceptable_temperature_c']:.1f}°C"
            ),
            "tone": "failure",
        }
    )

    reopened = reopen_or_escalate_case(
        case_id,
        reason="Temperature did not recover after provider completion",
    )
    events.append(
        {
            "step": 5,
            "state": "case_reopened",
            "title": "False closure refused",
            "detail": f"Case {reopened['action']}; responsibility stays open.",
            "tone": "action",
        }
    )

    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)
    events.append(
        {
            "step": 6,
            "state": "recovery_observed",
            "title": "Recovery observed",
            "detail": "Technician revisit complete · thermostat now 24.4°C",
            "tone": "progress",
        }
    )

    passed = verify_outcome(case_id)
    events.append(
        {
            "step": 7,
            "state": "verified_resolved",
            "title": "Outcome verified",
            "detail": "Provider status and home-state evidence agree. Case can close.",
            "tone": "success",
        }
    )

    return {
        "demo_mode": "synthetic_deterministic",
        "disclosure": (
            "Hackathon simulated Alexa+ experience. Provider and thermostat state are synthetic; "
            "the outcome-verification logic is the repository's real domain logic."
        ),
        "case_id": case_id,
        "verified": passed["verified"],
        "events": events,
    }

~~~~

## src/alexa_outcome_loop/mcp_server.py

Blob SHA-1: `44e019d1c37807281b697743f87b8ef4d605a372`

~~~~python
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools

mcp = FastMCP(
    "Alexa Home Repair Outcome Loop",
    host="0.0.0.0",
    port=8000,
    instructions=(
        "Coordinate home-repair cases. Never treat provider-side completion as final closure. "
        "Use read_home_state and verify_outcome before declaring the user's goal achieved; "
        "if verification fails, use reopen_or_escalate_case."
    ),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def create_repair_case(
    issue: str,
    room: str = "living room",
    target_temperature_c: float = 24.0,
) -> dict:
    """Create a repair case and an explicit outcome criterion."""
    return tools.create_repair_case(issue, room, target_temperature_c)


@mcp.tool()
def book_home_service(
    case_id: str,
    provider_name: str = "CoolCare HVAC",
    eta_minutes: int = 45,
) -> dict:
    """Book the deterministic home-service simulator for a repair case."""
    return tools.book_home_service(case_id, provider_name, eta_minutes)


@mcp.tool()
def get_service_status(case_id: str) -> dict:
    """Read provider-side workflow status."""
    return tools.get_service_status(case_id)


@mcp.tool()
def read_home_state(case_id: str) -> dict:
    """Read outcome-side thermostat/home-state evidence."""
    return tools.read_home_state(case_id)


@mcp.tool()
def verify_outcome(case_id: str, tolerance_c: float = 1.0) -> dict:
    """Verify provider completion against real-world outcome evidence."""
    return tools.verify_outcome(case_id, tolerance_c)


@mcp.tool()
def reopen_or_escalate_case(case_id: str, reason: str | None = None) -> dict:
    """Reopen or escalate a case when the intended outcome is not verified."""
    return tools.reopen_or_escalate_case(case_id, reason)


app = mcp.streamable_http_app()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

~~~~

## src/alexa_outcome_loop/agentcore_tools.py

Blob SHA-1: `dba4a1766ea561438966f35df0311aa470af7681`

~~~~python
from __future__ import annotations

from contextvars import ContextVar
from copy import deepcopy
from typing import Any

from strands import tool

from . import tools as domain_tools

# AgentCore can process more than one invocation in the same runtime process.
# ContextVar keeps audit traces invocation-local instead of sharing one mutable
# module-level list across concurrent requests.
_TOOL_TRACE: ContextVar[tuple[dict[str, Any], ...]] = ContextVar(
    "alexa_outcome_loop_tool_trace",
    default=(),
)


def reset_tool_trace() -> None:
    """Clear the current invocation's tool trace."""
    _TOOL_TRACE.set(())


def get_tool_trace() -> list[dict[str, Any]]:
    """Return a defensive copy of the current invocation's trace."""
    return deepcopy(list(_TOOL_TRACE.get()))


def _record(name: str, arguments: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    event = {
        "tool": name,
        "arguments": deepcopy(arguments),
        "result": deepcopy(result),
    }
    _TOOL_TRACE.set((*_TOOL_TRACE.get(), event))
    return result


@tool
def create_repair_case(
    issue: str,
    room: str = "living room",
    target_temperature_c: float = 24.0,
) -> dict:
    """Create a repair case and explicit observable success criterion."""
    result = domain_tools.create_repair_case(issue, room, target_temperature_c)
    return _record(
        "create_repair_case",
        {
            "issue": issue,
            "room": room,
            "target_temperature_c": target_temperature_c,
        },
        result,
    )


@tool
def book_home_service(
    case_id: str,
    provider_name: str = "CoolCare HVAC",
    eta_minutes: int = 45,
) -> dict:
    """Book the deterministic home-service simulator for an existing repair case."""
    result = domain_tools.book_home_service(case_id, provider_name, eta_minutes)
    return _record(
        "book_home_service",
        {
            "case_id": case_id,
            "provider_name": provider_name,
            "eta_minutes": eta_minutes,
        },
        result,
    )


@tool
def get_service_status(case_id: str) -> dict:
    """Read provider-side workflow status without treating it as outcome proof."""
    result = domain_tools.get_service_status(case_id)
    return _record("get_service_status", {"case_id": case_id}, result)


@tool
def read_home_state(case_id: str) -> dict:
    """Read outcome-side thermostat/home-state evidence."""
    result = domain_tools.read_home_state(case_id)
    return _record("read_home_state", {"case_id": case_id}, result)


@tool
def verify_outcome(case_id: str, tolerance_c: float = 1.0) -> dict:
    """Verify provider completion against observable home-state evidence."""
    result = domain_tools.verify_outcome(case_id, tolerance_c)
    return _record(
        "verify_outcome",
        {"case_id": case_id, "tolerance_c": tolerance_c},
        result,
    )


@tool
def reopen_or_escalate_case(case_id: str, reason: str | None = None) -> dict:
    """Keep responsibility open when the user's intended outcome is not verified."""
    result = domain_tools.reopen_or_escalate_case(case_id, reason)
    return _record(
        "reopen_or_escalate_case",
        {"case_id": case_id, "reason": reason},
        result,
    )


CLOUD_TOOLS = [
    create_repair_case,
    book_home_service,
    get_service_status,
    read_home_state,
    verify_outcome,
    reopen_or_escalate_case,
]

~~~~

## tests/test_outcome_loop.py

Blob SHA-1: `45c24fa7fd5c2e894eaa62b714eea7b30205d54b`

~~~~python
from alexa_outcome_loop.domain import CaseStatus
from alexa_outcome_loop.simulators import HOME_SIMULATOR, SERVICE_SIMULATOR
from alexa_outcome_loop.store import STORE
from alexa_outcome_loop.tools import (
    book_home_service,
    create_repair_case,
    reopen_or_escalate_case,
    verify_outcome,
)


def setup_function() -> None:
    STORE.reset()


def _new_case() -> str:
    created = create_repair_case("AC not cooling", target_temperature_c=24.0)
    return created["case"]["case_id"]


def test_provider_complete_is_not_enough() -> None:
    case_id = _new_case()
    book_home_service(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=29.0, hvac_running=True)

    result = verify_outcome(case_id)

    assert result["provider_complete"] is True
    assert result["home_recovered"] is False
    assert result["verified"] is False
    assert result["recommendation"] == "reopen_or_escalate"


def test_failed_verification_reopens_case() -> None:
    case_id = _new_case()
    book_home_service(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=28.5, hvac_running=True)
    verify_outcome(case_id)

    result = reopen_or_escalate_case(case_id)

    assert result["action"] == "reopened"
    assert STORE.get_case(case_id).status == CaseStatus.REOPENED


def test_case_closes_only_after_outcome_recovery() -> None:
    case_id = _new_case()
    book_home_service(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.5, hvac_running=True)

    result = verify_outcome(case_id, tolerance_c=1.0)

    assert result["verified"] is True
    assert STORE.get_case(case_id).status == CaseStatus.VERIFIED_RESOLVED

~~~~

## tests/test_demo_web.py

Blob SHA-1: `172fe3346cfa87d84b8916bc1e4786b57f53439b`

~~~~python
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

~~~~

## tests/test_mcp_http_integration.py

Blob SHA-1: `ddb2f91c438a16a56d910e6beab6fc16d3f27ffb`

~~~~python
from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

EXPECTED_TOOLS = {
    "create_repair_case",
    "book_home_service",
    "get_service_status",
    "read_home_state",
    "verify_outcome",
    "reopen_or_escalate_case",
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise TimeoutError(f"MCP server did not start on port {port}")


async def _round_trip(port: int) -> None:
    url = f"http://127.0.0.1:{port}/mcp"
    async with (
        streamablehttp_client(url) as (read_stream, write_stream, _),
        ClientSession(read_stream, write_stream) as session,
    ):
        initialize_result = await session.initialize()
        assert initialize_result.protocolVersion >= "2025-11-25"

        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS

        result = await session.call_tool(
            "create_repair_case",
            arguments={"issue": "AC not cooling", "target_temperature_c": 24.0},
        )
        assert result.content
        assert "repair-" in str(result.content)


def test_real_streamable_http_round_trip() -> None:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "alexa_outcome_loop.mcp_server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_port(port)
        asyncio.run(_round_trip(port))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

~~~~

