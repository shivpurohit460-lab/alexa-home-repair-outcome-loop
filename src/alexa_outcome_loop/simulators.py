from __future__ import annotations

from .domain import CaseStatus, HomeState, ServiceStatus, utc_now
from .store import STORE


class ServiceSimulator:
    def mark_in_progress(self, case_id: str) -> dict:
        case = STORE.get_case(case_id)
        case.service_status = ServiceStatus.IN_PROGRESS
        case.touch()
        return case.to_dict()

    def mark_provider_complete(self, case_id: str) -> dict:
        """Simulate a provider saying the job is complete.

        This does not change the home state. That separation is the core of the demo:
        workflow completion is not equivalent to outcome completion.
        """
        case = STORE.get_case(case_id)
        case.service_status = ServiceStatus.PROVIDER_COMPLETE
        case.status = CaseStatus.AWAITING_VERIFICATION
        case.touch()
        return case.to_dict()


class HomeSimulator:
    def set_state(self, case_id: str, *, temperature_c: float, hvac_running: bool) -> dict:
        STORE.get_case(case_id)
        state = HomeState(
            temperature_c=float(temperature_c),
            hvac_running=bool(hvac_running),
            observed_at=utc_now(),
        )
        STORE.home_states[case_id] = state
        return state.to_dict()


SERVICE_SIMULATOR = ServiceSimulator()
HOME_SIMULATOR = HomeSimulator()
