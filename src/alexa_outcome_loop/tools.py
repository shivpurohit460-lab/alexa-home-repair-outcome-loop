from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import isfinite

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
    if case.status not in {CaseStatus.OPEN, CaseStatus.REOPENED}:
        raise ValueError("Service booking requires an open or reopened case")
    case.provider_completed_at = None
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


def verify_outcome(case_id: str, tolerance_c: float = 1.0) -> dict:
    """Simulator-only postcondition check: provider + fresh post-work reading.

    Freshness <=15min and future-clock <=30sec are prototype policy values,
    not guarantees of real-device provenance. Unusable evidence is inconclusive.
    """
    if not 0.0 <= tolerance_c <= 5.0:
        raise ValueError("tolerance_c must be between 0 and 5")

    case = STORE.get_case(case_id)
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
    elif not isfinite(state.temperature_c):
        evidence_status = "invalid_temperature"
    else:
        evidence_status = "fresh_post_completion"

    home_recovered = evidence_status == "fresh_post_completion" and (
        state.temperature_c <= threshold
    )
    verified = provider_complete and home_recovered

    if verified:
        case.status = CaseStatus.VERIFIED_RESOLVED
        case.last_failure_reason = None
        verification_state = "verified"
        recommendation = "close_case"
        explanation = "Synthetic provider completion and fresh thermostat data agree."
    elif evidence_status != "fresh_post_completion":
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.last_failure_reason = None
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

    case.escalation_count += 1
    case.service_status = ServiceStatus.REOPENED
    case.provider_completed_at = None
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
