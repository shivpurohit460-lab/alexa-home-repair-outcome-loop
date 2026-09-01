from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CaseStatus(StrEnum):
    OPEN = "open"
    SERVICE_BOOKED = "service_booked"
    AWAITING_VERIFICATION = "awaiting_verification"
    REOPENED = "reopened"
    ESCALATED = "escalated"
    VERIFIED_RESOLVED = "verified_resolved"


class ServiceStatus(StrEnum):
    NOT_BOOKED = "not_booked"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PROVIDER_COMPLETE = "provider_complete"
    REOPENED = "reopened"


@dataclass(slots=True)
class HomeState:
    temperature_c: float = 30.0
    hvac_running: bool = False
    observed_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RepairCase:
    case_id: str
    issue: str
    room: str
    target_temperature_c: float
    status: CaseStatus = CaseStatus.OPEN
    service_status: ServiceStatus = ServiceStatus.NOT_BOOKED
    provider_name: str | None = None
    provider_reference: str | None = None
    escalation_count: int = 0
    last_failure_reason: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["service_status"] = self.service_status.value
        return payload
