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
    assert result["home_recovered"] is False
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
    with pytest.raises(ValueError, match="open or reopened"):
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
