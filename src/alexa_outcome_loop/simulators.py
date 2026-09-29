from __future__ import annotations

from math import isfinite

from .domain import (
    MAX_SIMULATED_TEMPERATURE_C,
    MIN_SIMULATED_TEMPERATURE_C,
    CaseStatus,
    HomeState,
    ServiceStatus,
    utc_now,
)
from .store import STORE, synchronized_store


class ServiceSimulator:
    @synchronized_store
    def mark_in_progress(self, case_id: str) -> dict:
        case = STORE.get_case(case_id)
        booked = (
            case.status == CaseStatus.SERVICE_BOOKED
            and case.service_status in {ServiceStatus.SCHEDULED, ServiceStatus.IN_PROGRESS}
        )
        revisiting = (
            case.status in {CaseStatus.REOPENED, CaseStatus.ESCALATED}
            and case.service_status == ServiceStatus.REOPENED
        )
        if not (booked or revisiting):
            raise ValueError("Provider progress requires booked or reopened service")
        case.service_status = ServiceStatus.IN_PROGRESS
        case.touch()
        return case.to_dict()

    @synchronized_store
    def mark_provider_complete(self, case_id: str) -> dict:
        """Timestamp completed scheduled/reopened synthetic repair work."""
        case = STORE.get_case(case_id)
        if case.status == CaseStatus.VERIFIED_RESOLVED:
            raise ValueError("Cannot complete an already verified-closed case")
        if case.service_status not in {
            ServiceStatus.SCHEDULED,
            ServiceStatus.IN_PROGRESS,
            ServiceStatus.REOPENED,
        }:
            raise ValueError("Provider completion requires scheduled or reopened service")
        case.service_status = ServiceStatus.PROVIDER_COMPLETE
        case.provider_completed_at = utc_now()
        case.failed_evidence_snapshot = None
        case.verified_evidence_snapshot = None
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.touch()
        return case.to_dict()

class HomeSimulator:
    @synchronized_store
    def set_state(self, case_id: str, *, temperature_c: float, hvac_running: bool) -> dict:
        STORE.get_case(case_id)
        if isinstance(temperature_c, bool):
            raise ValueError("temperature_c must be a numeric reading")
        try:
            observed = float(temperature_c)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("temperature_c must be numeric") from exc
        if not isfinite(observed):
            raise ValueError("temperature_c must be finite")
        if not MIN_SIMULATED_TEMPERATURE_C <= observed <= MAX_SIMULATED_TEMPERATURE_C:
            raise ValueError("temperature_c outside simulated plausibility range")
        state = HomeState(
            temperature_c=observed,
            hvac_running=bool(hvac_running),
            observed_at=utc_now(),
            source="synthetic_thermostat",
        )
        STORE.home_states[case_id] = state
        return state.to_dict()


SERVICE_SIMULATOR = ServiceSimulator()
HOME_SIMULATOR = HomeSimulator()
