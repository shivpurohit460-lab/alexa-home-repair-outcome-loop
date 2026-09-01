from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4

from .domain import HomeState, RepairCase


@dataclass
class InMemoryStore:
    """Prototype state store.

    Intentionally in-memory for the hackathon's deterministic simulator phase.
    AgentCore-backed state can replace this adapter later without changing the MCP tool contract.
    """

    cases: dict[str, RepairCase] = field(default_factory=dict)
    home_states: dict[str, HomeState] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False)

    def create_case(
        self,
        *,
        issue: str,
        room: str,
        target_temperature_c: float,
    ) -> RepairCase:
        case_id = f"repair-{uuid4().hex[:10]}"
        case = RepairCase(
            case_id=case_id,
            issue=issue,
            room=room,
            target_temperature_c=target_temperature_c,
        )
        with self._lock:
            self.cases[case_id] = case
            self.home_states[case_id] = HomeState()
        return case

    def get_case(self, case_id: str) -> RepairCase:
        try:
            return self.cases[case_id]
        except KeyError as exc:
            raise ValueError(f"Unknown repair case: {case_id}") from exc

    def get_home_state(self, case_id: str) -> HomeState:
        self.get_case(case_id)
        return self.home_states[case_id]

    def reset(self) -> None:
        with self._lock:
            self.cases.clear()
            self.home_states.clear()


STORE = InMemoryStore()
