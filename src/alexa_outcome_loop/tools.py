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
