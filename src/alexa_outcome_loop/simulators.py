from __future__ import annotations

from math import isfinite

from .domain import CaseStatus, HomeState, ServiceStatus, utc_now
from .store import STORE


class ServiceSimulator:
    def mark_in_progress(self, case_id: str) -> dict:
        case = STORE.get_case(case_id)
        case.service_status = ServiceStatus.IN_PROGRESS
        case.touch()
        return case.to_dict()

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
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.touch()
        return case.to_dict()

class HomeSimulator:
    def set_state(self, case_id: str, *, temperature_c: float, hvac_running: bool) -> dict:
        STORE.get_case(case_id)
        if not isfinite(float(temperature_c)):
            raise ValueError("temperature_c must be finite")
        state = HomeState(
            temperature_c=float(temperature_c),
            hvac_running=bool(hvac_running),
            observed_at=utc_now(),
            source="synthetic_thermostat",
        )
        STORE.home_states[case_id] = state
        return state.to_dict()


SERVICE_SIMULATOR = ServiceSimulator()
HOME_SIMULATOR = HomeSimulator()
