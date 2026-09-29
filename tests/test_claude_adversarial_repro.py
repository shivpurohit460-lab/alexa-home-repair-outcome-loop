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
