from __future__ import annotations

from pprint import pprint

from alexa_outcome_loop.simulators import HOME_SIMULATOR, SERVICE_SIMULATOR
from alexa_outcome_loop.store import STORE
from alexa_outcome_loop.tools import (
    book_home_service,
    create_repair_case,
    reopen_or_escalate_case,
    verify_outcome,
)


def main() -> None:
    STORE.reset()

    created = create_repair_case(
        "AC is running but the living room is not cooling",
        room="living room",
        target_temperature_c=24.0,
    )
    case_id = created["case"]["case_id"]
    print("\n1) CASE CREATED")
    pprint(created)

    print("\n2) SERVICE BOOKED")
    pprint(book_home_service(case_id, eta_minutes=30))

    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=29.2, hvac_running=True)

    print("\n3) PROVIDER SAYS COMPLETE, HOME STILL HOT")
    failed = verify_outcome(case_id)
    pprint(failed)
    assert failed["verified"] is False

    print("\n4) AGENT REFUSES FALSE CLOSURE AND REOPENS")
    pprint(reopen_or_escalate_case(case_id, reason="Temperature did not recover after service"))

    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)

    print("\n5) REPAIR RECOVERS; OUTCOME VERIFIED")
    passed = verify_outcome(case_id)
    pprint(passed)
    assert passed["verified"] is True


if __name__ == "__main__":
    main()
