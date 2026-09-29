# GREEN · Exact Git source snapshot for Claude review

Source commit: `04e2724b00f4ecde46677ba8533e6035572bcbce`.
Verbatim file contents and blob SHA-1 retrieved via GitHub app. This copy is for source review, not a runnable directory. See README for how to review without downloads.

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

Blob SHA-1: `7ced434e5d688f8c556b9adc810c5663c01070ec`

~~~~python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

# Deliberately broad synthetic demonstration range, not sensor calibration.
MIN_SIMULATED_TEMPERATURE_C = -20.0
MAX_SIMULATED_TEMPERATURE_C = 60.0


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
    source: str = "synthetic_thermostat"

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
    provider_completed_at: str | None = None
    escalation_count: int = 0
    last_failure_reason: str | None = None
    last_recovery_note: str | None = None
    failed_evidence_snapshot: tuple[str | None, str, float, str] | None = None
    verified_evidence_snapshot: tuple[str, str, float, str, float] | None = None
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

Blob SHA-1: `d52479eb8ae8547e351a23d9f9a15c9bd3076117`

~~~~python
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
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


def synchronized_store(operation):
    """Serialize one-process demo operations over the existing reentrant lock.

    This protects in-process state transitions, not tenant authorization or
    independent worker processes. All public case operations must use it.
    """
    @wraps(operation)
    def wrapper(*args, **kwargs):
        with STORE._lock:
            return operation(*args, **kwargs)

    return wrapper

~~~~

## src/alexa_outcome_loop/simulators.py

Blob SHA-1: `0217c4ea49a2540f5a05ee511d40b8d28bedbb57`

~~~~python
from __future__ import annotations

from math import isfinite

from .domain import (
    MAX_SIMULATED_TEMPERATURE_C,
    MIN_SIMULATED_TEMPERATURE_C,
    CaseStatus,
    HomeState,
    ServiceStatus,
    utc_now,
)
from .store import STORE, synchronized_store


class ServiceSimulator:
    @synchronized_store
    def mark_in_progress(self, case_id: str) -> dict:
        case = STORE.get_case(case_id)
        booked = (
            case.status == CaseStatus.SERVICE_BOOKED
            and case.service_status in {ServiceStatus.SCHEDULED, ServiceStatus.IN_PROGRESS}
        )
        revisiting = (
            case.status in {CaseStatus.REOPENED, CaseStatus.ESCALATED}
            and case.service_status == ServiceStatus.REOPENED
        )
        if not (booked or revisiting):
            raise ValueError("Provider progress requires booked or reopened service")
        case.service_status = ServiceStatus.IN_PROGRESS
        case.touch()
        return case.to_dict()

    @synchronized_store
    def mark_provider_complete(self, case_id: str) -> dict:
        """Timestamp completed scheduled/reopened synthetic repair work."""
        case = STORE.get_case(case_id)
        if case.status == CaseStatus.VERIFIED_RESOLVED:
            raise ValueError("Cannot complete an already verified-closed case")
        if case.service_status not in {
            ServiceStatus.SCHEDULED,
            ServiceStatus.IN_PROGRESS,
            ServiceStatus.REOPENED,
        }:
            raise ValueError("Provider completion requires scheduled or reopened service")
        case.service_status = ServiceStatus.PROVIDER_COMPLETE
        case.provider_completed_at = utc_now()
        case.failed_evidence_snapshot = None
        case.verified_evidence_snapshot = None
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.touch()
        return case.to_dict()

class HomeSimulator:
    @synchronized_store
    def set_state(self, case_id: str, *, temperature_c: float, hvac_running: bool) -> dict:
        STORE.get_case(case_id)
        if isinstance(temperature_c, bool):
            raise TypeError("temperature_c must be a numeric reading")
        try:
            observed = float(temperature_c)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("temperature_c must be numeric") from exc
        if not isfinite(observed):
            raise ValueError("temperature_c must be finite")
        if not MIN_SIMULATED_TEMPERATURE_C <= observed <= MAX_SIMULATED_TEMPERATURE_C:
            raise ValueError("temperature_c outside simulated plausibility range")
        state = HomeState(
            temperature_c=observed,
            hvac_running=bool(hvac_running),
            observed_at=utc_now(),
            source="synthetic_thermostat",
        )
        STORE.home_states[case_id] = state
        return state.to_dict()


SERVICE_SIMULATOR = ServiceSimulator()
HOME_SIMULATOR = HomeSimulator()

~~~~

## src/alexa_outcome_loop/tools.py

Blob SHA-1: `751abbc12c6f0d404271e76e5f26782561daeb3b`

~~~~python
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import isfinite

from .domain import (
    MAX_SIMULATED_TEMPERATURE_C,
    MIN_SIMULATED_TEMPERATURE_C,
    CaseStatus,
    ServiceStatus,
)
from .store import STORE, synchronized_store


@synchronized_store
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


@synchronized_store
def book_home_service(
    case_id: str,
    provider_name: str = "CoolCare HVAC",
    eta_minutes: int = 45,
) -> dict:
    """Book a deterministic home-service provider for an existing repair case."""
    if eta_minutes < 1:
        raise ValueError("eta_minutes must be positive")
    case = STORE.get_case(case_id)
    if case.status not in {CaseStatus.OPEN, CaseStatus.REOPENED, CaseStatus.ESCALATED}:
        raise ValueError("Service booking requires an open, reopened or escalated case")
    case.provider_completed_at = None
    case.failed_evidence_snapshot = None
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


@synchronized_store
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


@synchronized_store
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


def _aware_timestamp(value: str | None) -> datetime | None:
    """Reject missing, invalid and timezone-naive evidence timestamps."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None:
            return None
        return parsed.astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        return None


@synchronized_store
def verify_outcome(case_id: str, tolerance_c: float = 1.0) -> dict:
    """Simulator-only postcondition check: provider + fresh post-work reading.

    Freshness <=15min and future-clock <=30sec are prototype policy values,
    not guarantees of real-device provenance. Unusable evidence is inconclusive.
    """
    if not 0.0 <= tolerance_c <= 5.0:
        raise ValueError("tolerance_c must be between 0 and 5")

    case = STORE.get_case(case_id)
    if case.status == CaseStatus.VERIFIED_RESOLVED:
        # A closed case retains its original evidence; a subsequent check does
        # not claim that the room is STILL cool at the time of the new request.
        snapshot = case.verified_evidence_snapshot
        if snapshot is None:
            raise ValueError("Verified case lacks its original evidence snapshot")
        provider_at_str, observed_at_str, measured_c, source, stored_threshold = snapshot
        return {
            "case_id": case.case_id,
            "verified": True,
            "verification_state": "verified",
            "provider_complete": True,
            "home_recovered": True,
            "evidence_status": "historically_verified",
            "evidence_source": source,
            "provider_completed_at": provider_at_str,
            "reading_observed_at": observed_at_str,
            "observed_temperature_c": measured_c,
            "acceptable_temperature_c": stored_threshold,
            "recommendation": "already_closed",
            "explanation": (
                "Historical verified closure; no new sensor observation has been validated."
            ),
            "case_status": case.status.value,
        }

    state = STORE.get_home_state(case_id)
    now = datetime.now(UTC)
    provider_complete = case.service_status == ServiceStatus.PROVIDER_COMPLETE
    provider_at = _aware_timestamp(case.provider_completed_at)
    observed_at = _aware_timestamp(state.observed_at)
    threshold = case.target_temperature_c + float(tolerance_c)

    if not provider_complete:
        evidence_status = "provider_pending"
    elif provider_at is None:
        evidence_status = "invalid_provider_timestamp"
    elif provider_at > now + timedelta(seconds=30):
        evidence_status = "future_provider_timestamp"
    elif state.source != "synthetic_thermostat":
        evidence_status = "unrecognized_evidence_source"
    elif observed_at is None:
        evidence_status = "invalid_observation_timestamp"
    elif observed_at > now + timedelta(seconds=30):
        evidence_status = "future_observation"
    elif observed_at < provider_at:
        evidence_status = "pre_completion_observation"
    elif now - observed_at > timedelta(minutes=15):
        evidence_status = "stale_observation"
    elif (
        isinstance(state.temperature_c, bool)
        or not isinstance(state.temperature_c, (int, float))
        or not isfinite(state.temperature_c)
    ):
        evidence_status = "invalid_temperature"
    elif not (
        MIN_SIMULATED_TEMPERATURE_C <= state.temperature_c <= MAX_SIMULATED_TEMPERATURE_C
    ):
        evidence_status = "implausible_temperature"
    else:
        evidence_status = "fresh_post_completion"

    home_recovered = (
        state.temperature_c <= threshold
        if evidence_status == "fresh_post_completion"
        else None
    )
    verified = provider_complete and home_recovered is True

    if verified:
        case.status = CaseStatus.VERIFIED_RESOLVED
        case.last_failure_reason = None
        case.failed_evidence_snapshot = None
        case.verified_evidence_snapshot = (
            case.provider_completed_at,
            state.observed_at,
            state.temperature_c,
            state.source,
            threshold,
        )
        verification_state = "verified"
        recommendation = "close_case"
        explanation = "Synthetic provider completion and fresh thermostat data agree."
    elif evidence_status != "fresh_post_completion":
        # Missing provider evidence must not strand an otherwise bookable case.
        if provider_complete:
            case.status = CaseStatus.AWAITING_VERIFICATION
        case.last_failure_reason = None
        case.failed_evidence_snapshot = None
        verification_state = "inconclusive"
        recommendation = (
            "await_provider_completion" if not provider_complete else "await_fresh_evidence"
        )
        explanation = "No valid fresh post-completion evidence; do not claim success or failure."
    else:
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.last_failure_reason = (
            f"temperature_{state.temperature_c:.1f}C_above_threshold_{threshold:.1f}C"
        )
        case.failed_evidence_snapshot = (
            case.provider_completed_at, state.observed_at, state.temperature_c, state.source
        )
        verification_state = "not_recovered"
        recommendation = "reopen_or_escalate"
        explanation = "Fresh synthetic evidence shows the room remains above the threshold."
    case.touch()

    return {
        "case_id": case.case_id,
        "verified": verified,
        "verification_state": verification_state,
        "provider_complete": provider_complete,
        "home_recovered": home_recovered,
        "evidence_status": evidence_status,
        "evidence_source": state.source,
        "provider_completed_at": case.provider_completed_at,
        "reading_observed_at": state.observed_at,
        "observed_temperature_c": state.temperature_c,
        "acceptable_temperature_c": threshold,
        "recommendation": recommendation,
        "explanation": explanation,
        "case_status": case.status.value,
    }


@synchronized_store
def reopen_or_escalate_case(case_id: str, reason: str | None = None) -> dict:
    """Recover only after fresh evidence proves completed work failed."""
    case = STORE.get_case(case_id)
    if case.status == CaseStatus.VERIFIED_RESOLVED:
        return {
            "case_id": case.case_id,
            "action": "no_op",
            "case_status": case.status.value,
            "message": "Case is already outcome-verified and closed.",
        }
    if (
        case.status != CaseStatus.AWAITING_VERIFICATION
        or case.service_status != ServiceStatus.PROVIDER_COMPLETE
        or not case.last_failure_reason
    ):
        raise ValueError("Recovery requires a failed post-completion outcome verification")
    state = STORE.get_home_state(case_id)
    current_evidence = (
        case.provider_completed_at, state.observed_at, state.temperature_c, state.source
    )
    if case.failed_evidence_snapshot != current_evidence:
        raise ValueError("Evidence changed; reverification required before recovery")
    now = datetime.now(UTC)
    provider_at = _aware_timestamp(case.provider_completed_at)
    observed_at = _aware_timestamp(state.observed_at)
    if (
        provider_at is None
        or observed_at is None
        or observed_at < provider_at
        or observed_at > now + timedelta(seconds=30)
        or now - observed_at > timedelta(minutes=15)
    ):
        raise ValueError("Verification expired; fresh evidence required before recovery")

    case.escalation_count += 1
    case.service_status = ServiceStatus.REOPENED
    case.provider_completed_at = None
    case.failed_evidence_snapshot = None
    case.status = CaseStatus.ESCALATED if case.escalation_count > 1 else CaseStatus.REOPENED
    # User-supplied note is not evidence; preserve verified failure reason.
    case.last_recovery_note = reason.strip() if reason and reason.strip() else None
    case.touch()
    return {
        "case_id": case.case_id,
        "action": "escalated" if case.escalation_count > 1 else "reopened",
        "escalation_count": case.escalation_count,
        "reason": case.last_failure_reason,
        "recovery_note": case.last_recovery_note,
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

## tests/test_evidence_integrity.py

Blob SHA-1: `604a613060b4ff13aaee64c57df80500a9766998`

~~~~python
"""Negative tests for truthful closure and permitted recovery transitions.

All observations are synthetic. This does not certify real sensor provenance,
home-repair efficacy, concurrency safety, or production authorization.
"""
from datetime import UTC, datetime, timedelta
from math import inf, nan

import pytest

from alexa_outcome_loop.domain import CaseStatus, ServiceStatus
from alexa_outcome_loop.simulators import HOME_SIMULATOR, SERVICE_SIMULATOR
from alexa_outcome_loop.store import STORE
from alexa_outcome_loop.tools import (
    book_home_service,
    create_repair_case,
    reopen_or_escalate_case,
    verify_outcome,
)


@pytest.fixture(autouse=True)
def clear_store() -> None:
    STORE.reset()


def completed_case(temperature_c: float = 24.4) -> str:
    case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    book_home_service(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=temperature_c, hvac_running=True)
    return case_id


def test_old_pre_completion_reading_cannot_close_case() -> None:
    case_id = completed_case()
    case = STORE.get_case(case_id)
    state = STORE.get_home_state(case_id)
    completed_at = datetime.fromisoformat(case.provider_completed_at)
    state.observed_at = (completed_at - timedelta(seconds=2)).isoformat()

    result = verify_outcome(case_id)

    assert result["verified"] is False
    assert result["evidence_status"] == "pre_completion_observation"
    assert result["verification_state"] == "inconclusive"
    assert result["recommendation"] == "await_fresh_evidence"
    with pytest.raises(ValueError, match="failed post-completion"):
        reopen_or_escalate_case(case_id)


def test_stale_but_post_completion_good_reading_is_inconclusive() -> None:
    case_id = completed_case()
    now = datetime.now(UTC)
    STORE.get_case(case_id).provider_completed_at = (
        now - timedelta(minutes=20)
    ).isoformat()
    STORE.get_home_state(case_id).observed_at = (
        now - timedelta(minutes=17)
    ).isoformat()

    result = verify_outcome(case_id)

    assert result["evidence_status"] == "stale_observation"
    assert result["verified"] is False
    assert result["home_recovered"] is None
    assert result["verification_state"] == "inconclusive"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("observed_at", "not-a-date", "invalid_observation_timestamp"),
        ("observed_at", "2026-09-29T12:00:00", "invalid_observation_timestamp"),
        ("observed_at", "future", "future_observation"),
        ("provider_completed_at", None, "invalid_provider_timestamp"),
        ("provider_completed_at", "future", "future_provider_timestamp"),
    ],
)
def test_invalid_timestamps_fail_closed(field: str, value: str | None, expected: str) -> None:
    case_id = completed_case()
    if value == "future":
        value = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    target = (
        STORE.get_home_state(case_id) if field == "observed_at" else STORE.get_case(case_id)
    )
    setattr(target, field, value)

    result = verify_outcome(case_id)

    assert result["evidence_status"] == expected
    assert result["verified"] is False


@pytest.mark.parametrize("bad_value", [float("-inf"), inf, nan])
def test_corrupted_temperature_cannot_verify_success(bad_value: float) -> None:
    case_id = completed_case()
    STORE.get_home_state(case_id).temperature_c = bad_value

    result = verify_outcome(case_id)

    assert result["evidence_status"] == "invalid_temperature"
    assert result["verified"] is False


def test_simulator_rejects_nonfinite_temperature_at_ingress() -> None:
    case_id = completed_case()
    with pytest.raises(ValueError, match="finite"):
        HOME_SIMULATOR.set_state(case_id, temperature_c=float("-inf"), hvac_running=True)


def test_unrecognized_source_cannot_verify_success() -> None:
    case_id = completed_case()
    STORE.get_home_state(case_id).source = "external_unverified"

    result = verify_outcome(case_id)

    assert result["evidence_status"] == "unrecognized_evidence_source"
    assert result["verified"] is False


def test_recovery_before_verification_is_rejected() -> None:
    case_id = completed_case(temperature_c=29.2)
    with pytest.raises(ValueError, match="failed post-completion"):
        reopen_or_escalate_case(case_id)
    assert STORE.get_case(case_id).escalation_count == 0


def test_inconclusive_evidence_cannot_trigger_recovery() -> None:
    case_id = completed_case()
    STORE.get_home_state(case_id).observed_at = "invalid"

    assert verify_outcome(case_id)["verification_state"] == "inconclusive"
    with pytest.raises(ValueError, match="failed post-completion"):
        reopen_or_escalate_case(case_id)


def test_verified_failure_allows_one_recovery_but_not_duplicate() -> None:
    case_id = completed_case(temperature_c=29.2)
    result = verify_outcome(case_id)

    assert result["verification_state"] == "not_recovered"
    assert result["recommendation"] == "reopen_or_escalate"
    failure_reason = STORE.get_case(case_id).last_failure_reason
    recovered = reopen_or_escalate_case(case_id, reason="user-provided narrative")
    assert recovered["reason"] == failure_reason
    assert recovered["recovery_note"] == "user-provided narrative"
    assert STORE.get_case(case_id).service_status == ServiceStatus.REOPENED
    assert STORE.get_case(case_id).provider_completed_at is None

    with pytest.raises(ValueError, match="failed post-completion"):
        reopen_or_escalate_case(case_id)
    assert STORE.get_case(case_id).escalation_count == 1


def test_success_after_revisit_remains_supported() -> None:
    case_id = completed_case(temperature_c=29.2)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    reopen_or_escalate_case(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)

    result = verify_outcome(case_id)

    assert result["verified"] is True
    assert result["verification_state"] == "verified"
    assert STORE.get_case(case_id).status == CaseStatus.VERIFIED_RESOLVED
    assert reopen_or_escalate_case(case_id)["action"] == "no_op"


def test_provider_cannot_report_same_work_complete_twice() -> None:
    case_id = completed_case()
    with pytest.raises(ValueError, match="requires scheduled"):
        SERVICE_SIMULATOR.mark_provider_complete(case_id)


def test_verified_closed_case_cannot_be_booked_or_recompleted() -> None:
    case_id = completed_case()
    assert verify_outcome(case_id)["verified"] is True
    with pytest.raises(ValueError, match="Service booking requires"):
        book_home_service(case_id)
    with pytest.raises(ValueError, match="already verified"):
        SERVICE_SIMULATOR.mark_provider_complete(case_id)


def test_provider_incomplete_state_is_inconclusive() -> None:
    case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    book_home_service(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)

    result = verify_outcome(case_id)

    assert result["verification_state"] == "inconclusive"
    assert result["evidence_status"] == "provider_pending"
    assert result["recommendation"] == "await_provider_completion"


@pytest.mark.parametrize("bad_value", [None, "24.4", True])
def test_non_numeric_corrupted_observation_cannot_close_case(bad_value: object) -> None:
    case_id = completed_case()
    STORE.get_home_state(case_id).temperature_c = bad_value

    result = verify_outcome(case_id)

    assert result["evidence_status"] == "invalid_temperature"
    assert result["verification_state"] == "inconclusive"


def test_changed_observation_requires_reverification_before_recovery() -> None:
    case_id = completed_case(temperature_c=29.2)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)

    with pytest.raises(ValueError, match="reverification required"):
        reopen_or_escalate_case(case_id)
    assert STORE.get_case(case_id).escalation_count == 0
    assert verify_outcome(case_id)["verified"] is True

~~~~

## tests/test_claude_adversarial_repro.py

Blob SHA-1: `33d095028d5fcd73acdb555592a83ba105be8e3e`

~~~~python
"""Expected-failing, isolated reproduction of Claude's source-review findings.

The repro branch starts EXACTLY at PR #11 head
a3c986445d79d1f7cdd30bfaab0957f0a9b16fa5.
No source code is changed on this branch. Intentional red CI is evidence.
"""
from datetime import UTC, datetime, timedelta

import pytest

from alexa_outcome_loop.domain import CaseStatus
from alexa_outcome_loop.simulators import HOME_SIMULATOR, SERVICE_SIMULATOR
from alexa_outcome_loop.store import STORE
from alexa_outcome_loop.tools import (
    book_home_service,
    create_repair_case,
    reopen_or_escalate_case,
    verify_outcome,
)


@pytest.fixture(autouse=True)
def reset() -> None:
    STORE.reset()


def completed_case(temperature_c: float = 24.4) -> str:
    case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    book_home_service(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=temperature_c, hvac_running=True)
    return case_id


def test_f1_closed_case_remains_closed_after_reading_ages() -> None:
    case_id = completed_case()
    assert verify_outcome(case_id)["verified"]
    STORE.get_home_state(case_id).observed_at = (
        datetime.now(UTC) - timedelta(minutes=20)
    ).isoformat()
    result = verify_outcome(case_id)
    assert result["verification_state"] == "verified"
    assert STORE.get_case(case_id).status == CaseStatus.VERIFIED_RESOLVED


def test_f1_closed_case_rejects_provider_progress_transition() -> None:
    case_id = completed_case()
    assert verify_outcome(case_id)["verified"]
    with pytest.raises(ValueError):
        SERVICE_SIMULATOR.mark_in_progress(case_id)


def test_f2_unbooked_provider_cannot_mark_work_in_progress() -> None:
    case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    with pytest.raises(ValueError):
        SERVICE_SIMULATOR.mark_in_progress(case_id)


def test_f3_unknown_recovery_is_null_not_false() -> None:
    case_id = completed_case()
    STORE.get_home_state(case_id).observed_at = "invalid"
    result = verify_outcome(case_id)
    assert result["verification_state"] == "inconclusive"
    assert result["home_recovered"] is None


def test_f6_physically_absurd_cooling_does_not_verify_success() -> None:
    case_id = completed_case()
    # Tamper with stored synthetic observation to test verification after
    # the simulator correctly rejects impossible incoming readings.
    STORE.get_home_state(case_id).temperature_c = -500.0
    result = verify_outcome(case_id)
    assert result["verification_state"] == "inconclusive"


def test_f8_escalated_case_can_be_rebooked_for_next_revisit() -> None:
    case_id = completed_case(29.2)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    assert reopen_or_escalate_case(case_id)["action"] == "reopened"
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=29.2, hvac_running=True)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    assert reopen_or_escalate_case(case_id)["action"] == "escalated"
    booking = book_home_service(case_id)
    assert booking["service_status"] == "scheduled"


def test_f6_simulator_refuses_physically_absurd_ingress() -> None:
    case_id = completed_case()
    with pytest.raises(ValueError, match="plausibility range"):
        HOME_SIMULATOR.set_state(case_id, temperature_c=-500.0, hvac_running=True)


def test_f1_historical_closure_does_not_claim_current_sensor_evidence() -> None:
    case_id = completed_case()
    first = verify_outcome(case_id)
    assert first["verified"] is True
    HOME_SIMULATOR.set_state(case_id, temperature_c=29.2, hvac_running=True)
    again = verify_outcome(case_id)
    assert again["verification_state"] == "verified"
    assert again["evidence_status"] == "historically_verified"
    assert again["reading_observed_at"] == first["reading_observed_at"]
    assert again["observed_temperature_c"] == first["observed_temperature_c"]


def test_f5_expired_failed_verification_requires_new_evidence() -> None:
    from unittest.mock import patch

    case_id = completed_case(29.2)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    with patch("alexa_outcome_loop.tools.datetime", wraps=datetime) as fake_clock:
        fake_clock.now.return_value = datetime.now(UTC) + timedelta(minutes=16)
        with pytest.raises(ValueError, match="expired"):
            reopen_or_escalate_case(case_id)
    assert STORE.get_case(case_id).escalation_count == 0


def test_f10_verification_before_booking_preserves_bookable_open_case() -> None:
    case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    result = verify_outcome(case_id)
    assert result["verification_state"] == "inconclusive"
    assert result["home_recovered"] is None
    assert STORE.get_case(case_id).status == CaseStatus.OPEN
    assert book_home_service(case_id)["service_status"] == "scheduled"


def test_f4_recovery_of_one_failed_event_serializes_in_one_process() -> None:
    from concurrent.futures import ThreadPoolExecutor

    case_id = completed_case(29.2)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"

    def concurrent_recover(_: int) -> str:
        try:
            return reopen_or_escalate_case(case_id)["action"]
        except ValueError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(concurrent_recover, range(16)))
    assert outcomes.count("reopened") == 1
    assert outcomes.count("rejected") == 15
    assert STORE.get_case(case_id).escalation_count == 1

~~~~

## docs/EVIDENCE_INTEGRITY_REVIEW.md

Blob SHA-1: `e242e564dc9f6f9a7e0c419ffca3eefe307139d7`

~~~~
# Evidence-integrity review gate — 29 Sep 2026

**Scope:** Proposed patch for the simulated Alexa+ repair outcome loop; not a release.

## Failure conditions addressed

- A reading taken before provider completion must not close a case.
- Readings older than 15 minutes, invalid/future-dated timestamps, unrecognized source labels and non-finite temperatures are **inconclusive**; none can establish verified recovery or authorize escalation.
- A fresh synthetic reading taken after reported provider completion above the threshold produces **not_recovered** and permits one recovery transition.
- Premature, repeated or evidence-free recovery; rebooking verified-closed cases; duplicate provider completion are rejected.
- A user-supplied recovery note cannot overwrite the verified failure reason.

## Contract and assumptions

`verify_outcome` preserves existing keys and adds `verification_state` (`verified`, `not_recovered`, `inconclusive`), `evidence_status`, `evidence_source` and timestamps.

The 15-minute freshness limit and 30-second future-clock tolerance are provisional demo assumptions, not validated hardware behavior. `HomeState.source` is a plain synthetic label, **not authenticated device attestation**. No actual provider/thermostat system is integrated.

All six MCP operation names, the seven-step judge story, public page and existing AWS Gate 5B remain untouched.

## Review and promotion requirements

1. Review exact-branch Python 3.11/3.13 CI, Ruff and all existing MCP/demo regressions.
2. Verify negative tests reject false closure and invalid state transitions; demonstrate a deliberate mutant is caught.
3. Have a separate reviewer attack clock boundaries, spoofed timestamps and provenance, cross-case/state isolation and time-of-check/time-of-use. This narrow patch does not solve all production risks.
4. Preserve `main`, public GitHub Pages, Devpost, and owner-controlled submission. No merge or release before review.

The recovery gate additionally compares the exact in-memory observation snapshot
(provider timestamp, reading timestamp, temperature and source) against the one
that established the last failed verification. Any intervening observation must
be reverified. This is a bounded sequential check, not transactional concurrent
integrity or cryptographic source authentication.

## Independent Claude source-review response and exact-SHA reproduction

Claude examined PR #11 at `a3c986445d79d1f7cdd30bfaab0957f0a9b16fa5` but explicitly **did not** run any code or inspect all source files. Its report is a valuable separate-model source review, not a completed independent runtime audit. It identified F1–F9 and requested negative reproductions. The full `demo_engine.py` confirms that the synthetic hot reading occurs **after** provider completion; the speculative demo-break path does not apply to the checked revision. F9's feared old comparison is absent from final `tools.py`.

**Red evidence:** Test-only branch `audit/2026-09-29-claude-repro` starts at that exact PR head and adds only `tests/test_claude_adversarial_repro.py`. [GitHub run 36534037166](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/actions/runs/36534037166) independently executed those checks on Python 3.11 and 3.13. Each job reported **6 expected failures, 37 baseline passes and 4 dependency deprecation warnings**, with Ruff PASS. The six failures reproducibly confirm both F1 variants, F2, F3, F6 and F8 rebooking. The test-only branch deliberately remains red; do not merge it.

**Revised PR #11 changes:**

- **F1:** Verified closure becomes monotonic. Repeat verification returns the saved historical evidence/tolerance explicitly labeled `historically_verified`; it must not imply a live current reading. Provider progress after verified closure is prohibited.
- **F2:** `mark_in_progress` requires booked service or a valid reopened/escalated revisit; it cannot turn an unbooked case into a completed provider job.
- **F3:** `home_recovered` is now `null` in inconclusive JSON (Python `None`); consumers **must branch on `verification_state`**, not `not verified` as if it meant proven failure. This is a deliberate response-contract change; review external clients before release.
- **F4:** The pre-existing one-process reentrant store lock now serializes all six public tool operations and three simulator mutations, covering same-process read/check/write windows. It does **not** authenticate `case_id`, protect against direct state mutation or synchronize independent worker processes.
- **F5:** Recovery rechecks the original observation's freshness and provider-time ordering at the recovery call. Expired verification requires a fresh check.
- **F6:** Coarse *synthetic-only* temperature plausibility bounds (-20°C to +60°C) apply on input and verification. This is not sensor calibration or certified environmental safety.
- **F8:** An escalated case can be explicitly rebooked for another provider visit; missing-evidence timeouts, human handoff and escalation ceilings remain a separate unimplemented policy.
- **Additional F10 found during review:** Verifying a newly open case before any provider booking no longer changes its status into an unbookable `AWAITING_VERIFICATION` state.

**Pending:** The exact revised-head CI, independent clean-environment replay, deliberate mutation of timestamp ordering, cross-process/tenant authorization review, and owner decision. F7 caller-controlled tolerance and unbounded recovery notes still require separate policy, including whether any trust level beyond a synthetic prototype is intended. No claim of live Alexa+, device attestation, deployment or production readiness.

**Non-regression:** Keep `main`, six MCP operation names, seven-step public judge simulator, live AWS Gate 5B, and current Devpost entry unchanged. Reviewer approval and owner merge authorization remain separate gates.

~~~~

