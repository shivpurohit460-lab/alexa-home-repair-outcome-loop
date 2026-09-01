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
