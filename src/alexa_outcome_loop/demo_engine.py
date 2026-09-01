from __future__ import annotations

from .simulators import HOME_SIMULATOR, SERVICE_SIMULATOR
from .store import STORE
from .tools import (
    book_home_service,
    create_repair_case,
    reopen_or_escalate_case,
    verify_outcome,
)


def build_demo_timeline() -> dict:
    """Run the deterministic seven-step judge demo using production domain logic."""
    STORE.reset()

    created = create_repair_case(
        "AC is running but the living room is not cooling",
        room="living room",
        target_temperature_c=24.0,
    )
    case_id = created["case"]["case_id"]
    events: list[dict] = [
        {
            "step": 1,
            "state": "request_received",
            "title": "User asks for an outcome",
            "detail": "My AC is broken. Handle it and make sure it is actually fixed.",
            "tone": "neutral",
        }
    ]

    booking = book_home_service(case_id, eta_minutes=30)
    events.append(
        {
            "step": 2,
            "state": "service_booked",
            "title": "Repair booked",
            "detail": f"{booking['provider']} · ETA {booking['eta_minutes']} min",
            "tone": "progress",
        }
    )

    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    events.append(
        {
            "step": 3,
            "state": "provider_complete",
            "title": "Provider reports complete",
            "detail": "Workflow says done. Outcome is still unverified.",
            "tone": "warning",
        }
    )

    HOME_SIMULATOR.set_state(case_id, temperature_c=29.2, hvac_running=True)
    failed = verify_outcome(case_id)
    events.append(
        {
            "step": 4,
            "state": "verification_failed",
            "title": "Outcome check fails",
            "detail": (
                f"Thermostat: {failed['observed_temperature_c']:.1f}°C · "
                f"acceptable ≤ {failed['acceptable_temperature_c']:.1f}°C"
            ),
            "tone": "failure",
        }
    )

    reopened = reopen_or_escalate_case(
        case_id,
        reason="Temperature did not recover after provider completion",
    )
    events.append(
        {
            "step": 5,
            "state": "case_reopened",
            "title": "False closure refused",
            "detail": f"Case {reopened['action']}; responsibility stays open.",
            "tone": "action",
        }
    )

    SERVICE_SIMULATOR.mark_provider_complete(case_id)
    HOME_SIMULATOR.set_state(case_id, temperature_c=24.4, hvac_running=True)
    events.append(
        {
            "step": 6,
            "state": "recovery_observed",
            "title": "Recovery observed",
            "detail": "Technician revisit complete · thermostat now 24.4°C",
            "tone": "progress",
        }
    )

    passed = verify_outcome(case_id)
    events.append(
        {
            "step": 7,
            "state": "verified_resolved",
            "title": "Outcome verified",
            "detail": "Provider status and home-state evidence agree. Case can close.",
            "tone": "success",
        }
    )

    return {
        "demo_mode": "synthetic_deterministic",
        "disclosure": (
            "Hackathon simulated Alexa+ experience. Provider and thermostat state are synthetic; "
            "the outcome-verification logic is the repository's real domain logic."
        ),
        "case_id": case_id,
        "verified": passed["verified"],
        "events": events,
    }
