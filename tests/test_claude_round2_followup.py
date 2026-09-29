"""Claude Round 2 follow-up: adversarial policy, boundaries and lock tests.

RED phase runs against the immutable GREEN head from Claude's completed audit.
The F7/F7b tests MUST initially fail while existing safety regressions pass.
Only a separate follow-up branch receives any repair; PR #11 remains unchanged.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from math import nan
from unittest.mock import patch

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
def clean_store() -> None:
    STORE.reset()


def completed_case(temperature_c: float = 29.0) -> str:
    case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    book_home_service(case_id)
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=temperature_c, hvac_running=True)
    return case_id


def test_f7_tolerance_is_stored_as_fixed_case_success_policy() -> None:
    created = create_repair_case("AC not cooling", target_temperature_c=24.0)
    case = STORE.get_case(created["case"]["case_id"])
    assert case.verification_tolerance_c == 1.0
    assert created["success_criterion"]["verification_tolerance_c"] == 1.0
    assert created["success_criterion"]["acceptable_temperature_c"] == 25.0


def test_f7_caller_cannot_convert_proven_failure_into_success() -> None:
    case_id = completed_case(29.0)
    failed = verify_outcome(case_id)
    assert failed["verification_state"] == "not_recovered"
    original_failure = STORE.get_case(case_id).last_failure_reason
    with pytest.raises(ValueError, match="fixed"):
        verify_outcome(case_id, tolerance_c=5.0)
    assert STORE.get_case(case_id).status == CaseStatus.AWAITING_VERIFICATION
    assert STORE.get_case(case_id).last_failure_reason == original_failure
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"


@pytest.mark.parametrize("bad", [0.0, 0.5, 2.0, 5.0, 50.0, nan, True])
def test_f7_rejects_all_nonfixed_or_invalid_tolerance(bad: object) -> None:
    case_id = completed_case(29.0)
    with pytest.raises(ValueError, match="fixed"):
        verify_outcome(case_id, tolerance_c=bad)


def test_f7_default_tolerance_remains_supported_for_verified_case() -> None:
    case_id = completed_case(24.4)
    result = verify_outcome(case_id)
    assert result["verified"] is True
    assert result["acceptable_temperature_c"] == 25.0


def test_f7b_overlong_note_is_rejected_before_state_mutation() -> None:
    case_id = completed_case(29.0)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    previous_status = STORE.get_case(case_id).status
    previous_snapshot = STORE.get_case(case_id).failed_evidence_snapshot
    with pytest.raises(ValueError, match="500"):
        reopen_or_escalate_case(case_id, reason="X" * 501)
    case = STORE.get_case(case_id)
    assert case.status == previous_status
    assert case.escalation_count == 0
    assert case.failed_evidence_snapshot == previous_snapshot


def test_f7b_note_boundary_and_untrusted_label() -> None:
    case_id = completed_case(29.0)
    verify_outcome(case_id)
    response = reopen_or_escalate_case(case_id, reason="x" * 500)
    assert len(response["recovery_note"]) == 500
    assert response["recovery_note_trust"] == "untrusted_user_input"
    assert STORE.get_case(case_id).escalation_count == 1


def test_f4_recovery_holds_store_lock_through_read_and_mutation(monkeypatch) -> None:
    case_id = completed_case(29.0)
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    original = STORE.get_case
    lock_results = []

    def attempt_lock() -> bool:
        acquired = STORE._lock.acquire(blocking=False)
        if acquired:
            STORE._lock.release()
        return acquired

    def spy_get_case(requested_id: str):
        with ThreadPoolExecutor(max_workers=1) as pool:
            lock_results.append(pool.submit(attempt_lock).result(timeout=2) is False)
        return original(requested_id)

    monkeypatch.setattr(STORE, "get_case", spy_get_case)
    assert reopen_or_escalate_case(case_id)["action"] == "reopened"
    assert lock_results and all(lock_results)


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (timedelta(minutes=15), "not_recovered"),
        (timedelta(minutes=15, microseconds=1), "inconclusive"),
    ],
)
def test_f5_exact_staleness_boundary(delta: timedelta, expected: str) -> None:
    case_id = completed_case(29.0)
    origin = datetime.now(UTC)
    STORE.get_case(case_id).provider_completed_at = (
        origin - timedelta(minutes=1)
    ).isoformat()
    STORE.get_home_state(case_id).observed_at = origin.isoformat()

    with patch("alexa_outcome_loop.tools.datetime", wraps=datetime) as clock:
        clock.now.return_value = origin + delta
        result = verify_outcome(case_id)

    assert result["verification_state"] == expected


@pytest.mark.parametrize(
    ("delta", "should_reopen"),
    [
        (timedelta(minutes=15), True),
        (timedelta(minutes=15, microseconds=1), False),
    ],
)
def test_f5_exact_recovery_expiry_boundary(delta: timedelta, should_reopen: bool) -> None:
    case_id = completed_case(29.0)
    origin = datetime.now(UTC)
    STORE.get_case(case_id).provider_completed_at = (
        origin - timedelta(minutes=1)
    ).isoformat()
    STORE.get_home_state(case_id).observed_at = origin.isoformat()
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"

    with patch("alexa_outcome_loop.tools.datetime", wraps=datetime) as clock:
        clock.now.return_value = origin + delta
        if should_reopen:
            assert reopen_or_escalate_case(case_id)["action"] == "reopened"
        else:
            with pytest.raises(ValueError, match="expired"):
                reopen_or_escalate_case(case_id)


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (timedelta(seconds=30), "fresh_post_completion"),
        (timedelta(seconds=30, microseconds=1), "future_observation"),
        (timedelta(seconds=31), "future_observation"),
    ],
)
def test_future_observation_clock_skew_boundary(
    delta: timedelta, expected: str
) -> None:
    case_id = completed_case(24.4)
    origin = datetime.now(UTC)
    STORE.get_case(case_id).provider_completed_at = (
        origin - timedelta(seconds=1)
    ).isoformat()
    STORE.get_home_state(case_id).observed_at = (origin + delta).isoformat()

    with patch("alexa_outcome_loop.tools.datetime", wraps=datetime) as clock:
        clock.now.return_value = origin
        result = verify_outcome(case_id)

    assert result["evidence_status"] == expected


def test_status_guard_is_not_redundant_in_recovery() -> None:
    case_id = completed_case(29.0)
    verify_outcome(case_id)
    STORE.get_case(case_id).status = CaseStatus.OPEN
    with pytest.raises(ValueError, match="failed post-completion"):
        reopen_or_escalate_case(case_id)
