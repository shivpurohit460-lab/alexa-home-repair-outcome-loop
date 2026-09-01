from __future__ import annotations

from copy import deepcopy
from typing import Any

from strands import tool

from . import tools as domain_tools

_TOOL_TRACE: list[dict[str, Any]] = []


def reset_tool_trace() -> None:
    """Clear the per-invocation tool trace used for demo evidence and tests."""
    _TOOL_TRACE.clear()


def get_tool_trace() -> list[dict[str, Any]]:
    """Return a defensive copy so callers cannot mutate runtime trace state."""
    return deepcopy(_TOOL_TRACE)


def _record(name: str, arguments: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    _TOOL_TRACE.append(
        {
            "tool": name,
            "arguments": deepcopy(arguments),
            "result": deepcopy(result),
        }
    )
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
