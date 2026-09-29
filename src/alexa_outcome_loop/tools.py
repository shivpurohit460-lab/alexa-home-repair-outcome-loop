from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import isfinite

from .domain import (
    DEFAULT_VERIFICATION_TOLERANCE_C,
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
            "verification_tolerance_c": case.verification_tolerance_c,
            "acceptable_temperature_c": (
                case.target_temperature_c + case.verification_tolerance_c
            ),
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

    Freshness <=15min and future-clock <=30sec are prototype policy values.
    Tolerance is fixed per case at creation, never adjusted at verification.
    No authenticated real-device provenance is claimed; missing evidence is inconclusive.
    """
    case = STORE.get_case(case_id)
    if (
        isinstance(tolerance_c, bool)
        or not isinstance(tolerance_c, (int, float))
        or not isfinite(tolerance_c)
        or tolerance_c != case.verification_tolerance_c
        or case.verification_tolerance_c != DEFAULT_VERIFICATION_TOLERANCE_C
    ):
        raise ValueError("tolerance_c is fixed at case creation and cannot be overridden")
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
    threshold = case.target_temperature_c + case.verification_tolerance_c

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

    # Bound the untrusted user narrative before any state mutation. A length
    # cap limits resource abuse; it does NOT make note text trusted instructions.
    if reason is None:
        note = None
    elif not isinstance(reason, str):
        raise TypeError("recovery reason must be text or None")
    elif len(reason) > 500:
        raise ValueError("recovery note is limited to 500 characters")
    else:
        note = reason.strip() or None

    case.escalation_count += 1
    case.service_status = ServiceStatus.REOPENED
    case.provider_completed_at = None
    case.failed_evidence_snapshot = None
    case.status = CaseStatus.ESCALATED if case.escalation_count > 1 else CaseStatus.REOPENED
    # User-supplied note is not evidence; preserve verified failure reason.
    case.last_recovery_note = note
    case.touch()
    return {
        "case_id": case.case_id,
        "action": "escalated" if case.escalation_count > 1 else "reopened",
        "escalation_count": case.escalation_count,
        "reason": case.last_failure_reason,
        "recovery_note": case.last_recovery_note,
        "recovery_note_trust": (
            "untrusted_user_input" if case.last_recovery_note else "none"
        ),
        "provider_reference": case.provider_reference,
        "service_status": case.service_status.value,
        "case_status": case.status.value,
    }
