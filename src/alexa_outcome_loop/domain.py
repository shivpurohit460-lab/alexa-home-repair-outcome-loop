from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

# Deliberately broad synthetic demonstration range, not sensor calibration.
MIN_SIMULATED_TEMPERATURE_C = -20.0
MAX_SIMULATED_TEMPERATURE_C = 60.0

# A case's acceptance tolerance is fixed at creation, not chosen at verification.
DEFAULT_VERIFICATION_TOLERANCE_C = 1.0


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


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
    source: str = "synthetic_thermostat"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RepairCase:
    case_id: str
    issue: str
    room: str
    target_temperature_c: float
    verification_tolerance_c: float = DEFAULT_VERIFICATION_TOLERANCE_C
    status: CaseStatus = CaseStatus.OPEN
    service_status: ServiceStatus = ServiceStatus.NOT_BOOKED
    provider_name: str | None = None
    provider_reference: str | None = None
    provider_completed_at: str | None = None
    escalation_count: int = 0
    last_failure_reason: str | None = None
    last_recovery_note: str | None = None
    failed_evidence_snapshot: tuple[str | None, str, float, str] | None = None
    verified_evidence_snapshot: tuple[str, str, float, str, float] | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["service_status"] = self.service_status.value
        return payload
