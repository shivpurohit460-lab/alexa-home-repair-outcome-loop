"""Exact-PR14 follow-up: independently test previously surviving safety mutants.

These tests exercise the existing synthetic-demo contract. They deliberately
make no claims about real sensor provenance, inter-process locking, or LLM
prompt obedience. In-process lock probes cover an entry read, not all later
mutation points; the older concurrent-recovery test remains complementary.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from re import sub
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


def _booked_case() -> str:
    case_id = create_repair_case("AC not cooling", target_temperature_c=24.0)["case"]["case_id"]
    book_home_service(case_id)
    return case_id


def _completed_case(temperature_c: float = 29.0) -> str:
    case_id = _booked_case()
    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=temperature_c, hvac_running=True)
    return case_id


def _verified_failure() -> str:
    case_id = _completed_case()
    assert verify_outcome(case_id)["verification_state"] == "not_recovered"
    return case_id


def _set_matching_failed_snapshot(
    case_id: str, provider_at: datetime, observed_at: datetime
) -> None:
    """Preserve the earlier failure proof to reach the *second* recovery gate."""
    case = STORE.get_case(case_id)
    state = STORE.get_home_state(case_id)
    case.provider_completed_at = provider_at.isoformat()
    state.observed_at = observed_at.isoformat()
    case.failed_evidence_snapshot = (
        case.provider_completed_at,
        state.observed_at,
        state.temperature_c,
        state.source,
    )


def test_exact_25c_threshold_is_inclusive_and_a_fraction_above_fails() -> None:
    at_threshold = _completed_case(25.0)
    exact = verify_outcome(at_threshold)
    assert exact["verification_state"] == "verified"
    assert exact["acceptable_temperature_c"] == 25.0
    assert STORE.get_case(at_threshold).status == CaseStatus.VERIFIED_RESOLVED

    above_threshold = _completed_case(25.000001)
    above = verify_outcome(above_threshold)
    assert above["verification_state"] == "not_recovered"
    assert above["acceptable_temperature_c"] == 25.0
    assert STORE.get_case(above_threshold).status == CaseStatus.AWAITING_VERIFICATION


@pytest.mark.parametrize(
    ("future_delta", "permitted"),
    [
        (timedelta(seconds=30), True),
        (timedelta(seconds=30, microseconds=1), False),
    ],
)
def test_recovery_rechecks_future_observation_before_mutation(
    future_delta: timedelta, permitted: bool,
) -> None:
    case_id = _verified_failure()
    origin = datetime.now(UTC)
    _set_matching_failed_snapshot(
        case_id, origin - timedelta(minutes=1), origin + future_delta
    )
    snapshot = STORE.get_case(case_id).failed_evidence_snapshot
    with patch("alexa_outcome_loop.tools.datetime", wraps=datetime) as clock:
        clock.now.return_value = origin
        if permitted:
            assert reopen_or_escalate_case(case_id)["action"] == "reopened"
            assert STORE.get_case(case_id).escalation_count == 1
        else:
            with pytest.raises(ValueError, match="expired"):
                reopen_or_escalate_case(case_id)
            case = STORE.get_case(case_id)
            assert case.status == CaseStatus.AWAITING_VERIFICATION
            assert case.escalation_count == 0
            assert case.failed_evidence_snapshot == snapshot


@pytest.mark.parametrize(
    ("before_provider", "permitted"),
    [
        (timedelta(0), True),
        (timedelta(microseconds=1), False),
    ],
)
def test_recovery_rechecks_precompletion_observation_before_mutation(
    before_provider: timedelta, permitted: bool,
) -> None:
    case_id = _verified_failure()
    origin = datetime.now(UTC)
    provider_at = origin - timedelta(minutes=1)
    _set_matching_failed_snapshot(case_id, provider_at, provider_at - before_provider)
    snapshot = STORE.get_case(case_id).failed_evidence_snapshot
    with patch("alexa_outcome_loop.tools.datetime", wraps=datetime) as clock:
        clock.now.return_value = origin
        if permitted:
            assert reopen_or_escalate_case(case_id)["action"] == "reopened"
        else:
            with pytest.raises(ValueError, match="expired"):
                reopen_or_escalate_case(case_id)
            case = STORE.get_case(case_id)
            assert case.status == CaseStatus.AWAITING_VERIFICATION
            assert case.escalation_count == 0
            assert case.failed_evidence_snapshot == snapshot


@pytest.mark.parametrize(
    "operation",
    [
        "create_repair_case",
        "book_home_service",
        "verify_outcome",
        "reopen_or_escalate_case",
        "mark_in_progress",
        "mark_provider_complete",
        "set_state",
    ],
)
def test_every_public_mutator_holds_store_lock_at_entry(
    monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    """Detect removal of any seven individual in-process lock decorators."""
    case_id: str | None = None
    if operation in {"book_home_service", "set_state"}:
        case_id = create_repair_case("AC not cooling")["case"]["case_id"]
    elif operation in {"mark_in_progress", "mark_provider_complete"}:
        case_id = _booked_case()
    elif operation == "verify_outcome":
        case_id = _completed_case(29.0)
    elif operation == "reopen_or_escalate_case":
        case_id = _verified_failure()

    original = STORE.create_case if operation == "create_repair_case" else STORE.get_case
    observed_lock_state: list[bool] = []

    def other_thread_can_acquire() -> bool:
        acquired = STORE._lock.acquire(blocking=False)
        if acquired:
            STORE._lock.release()
        return acquired

    def checked_entry(*args, **kwargs):
        # An RLock is re-entrant only on its *owning* thread, so we probe from
        # another thread while the public operation is inside its entry read.
        with ThreadPoolExecutor(max_workers=1) as pool:
            observed_lock_state.append(not pool.submit(other_thread_can_acquire).result(timeout=5))
        return original(*args, **kwargs)

    target = "create_case" if operation == "create_repair_case" else "get_case"
    monkeypatch.setattr(STORE, target, checked_entry)
    if operation == "create_repair_case":
        create_repair_case("AC not cooling")
    elif operation == "book_home_service":
        book_home_service(case_id)
    elif operation == "verify_outcome":
        verify_outcome(case_id)
    elif operation == "reopen_or_escalate_case":
        reopen_or_escalate_case(case_id)
    elif operation == "mark_in_progress":
        SERVICE_SIMULATOR.mark_in_progress(case_id)
    elif operation == "mark_provider_complete":
        SERVICE_SIMULATOR.mark_provider_complete(case_id)
    elif operation == "set_state":
        HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)
    assert observed_lock_state, f"No store entry was observed for {operation}"
    assert all(observed_lock_state), f"Store entry unlocked in {operation}"


@pytest.mark.parametrize(
    "invalid_evidence",
    ["invalid_timestamp", "stale_observation", "pre_completion_observation"],
)
def test_inconclusive_never_triggers_recovery(invalid_evidence: str) -> None:
    case_id = _completed_case(29.0)
    state = STORE.get_home_state(case_id)
    if invalid_evidence == "invalid_timestamp":
        state.observed_at = "invalid"
    elif invalid_evidence == "stale_observation":
        state.observed_at = (datetime.now(UTC) - timedelta(minutes=16)).isoformat()
    else:
        state.observed_at = (datetime.now(UTC) - timedelta(minutes=2)).isoformat()
        STORE.get_case(case_id).provider_completed_at = (
            datetime.now(UTC) - timedelta(minutes=1)
        ).isoformat()
    result = verify_outcome(case_id)
    assert result["verification_state"] == "inconclusive"
    assert result["home_recovered"] is None
    with pytest.raises(ValueError, match="failed post-completion"):
        reopen_or_escalate_case(case_id)
    case = STORE.get_case(case_id)
    assert case.escalation_count == 0
    assert case.status == CaseStatus.AWAITING_VERIFICATION


def test_agent_and_mcp_instructions_have_unambiguous_tristate_contract() -> None:
    """Catch B13's contradictory prompt text; tool behavior is tested above.

    This checks a deterministic instruction contract, not live LLM obedience.
    """
    from alexa_outcome_loop.agent import SYSTEM_PROMPT
    from alexa_outcome_loop.mcp_server import mcp

    prompt = sub(r"\s+", " ", SYSTEM_PROMPT).lower()
    instruction = sub(r"\s+", " ", mcp.instructions).lower()
    assert (
        "if verification_state is not_recovered, call reopen_or_escalate_case with fresh "
        "matching failure evidence. if inconclusive, await valid fresh evidence; do "
        "not treat unknown as proven failure or trigger recovery on inconclusive data."
    ) in prompt
    assert (
        "only verification_state=not_recovered permits reopen_or_escalate_case; "
        "if verification_state=inconclusive, await fresh evidence and never invent success."
    ) in instruction
    assert "treat unknown as failure and trigger recovery" not in prompt
