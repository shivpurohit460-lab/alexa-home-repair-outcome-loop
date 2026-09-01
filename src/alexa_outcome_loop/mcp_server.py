from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools

mcp = FastMCP(
    "Alexa Home Repair Outcome Loop",
    instructions=(
        "Coordinate home-repair cases. Never treat provider-side completion as final closure. "
        "Use read_home_state and verify_outcome before declaring the user's goal achieved; "
        "if verification fails, use reopen_or_escalate_case."
    ),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def create_repair_case(
    issue: str,
    room: str = "living room",
    target_temperature_c: float = 24.0,
) -> dict:
    """Create a repair case and an explicit outcome criterion."""
    return tools.create_repair_case(issue, room, target_temperature_c)


@mcp.tool()
def book_home_service(
    case_id: str,
    provider_name: str = "CoolCare HVAC",
    eta_minutes: int = 45,
) -> dict:
    """Book the deterministic home-service simulator for a repair case."""
    return tools.book_home_service(case_id, provider_name, eta_minutes)


@mcp.tool()
def get_service_status(case_id: str) -> dict:
    """Read provider-side workflow status."""
    return tools.get_service_status(case_id)


@mcp.tool()
def read_home_state(case_id: str) -> dict:
    """Read outcome-side thermostat/home-state evidence."""
    return tools.read_home_state(case_id)


@mcp.tool()
def verify_outcome(case_id: str, tolerance_c: float = 1.0) -> dict:
    """Verify provider completion against real-world outcome evidence."""
    return tools.verify_outcome(case_id, tolerance_c)


@mcp.tool()
def reopen_or_escalate_case(case_id: str, reason: str | None = None) -> dict:
    """Reopen or escalate a case when the intended outcome is not verified."""
    return tools.reopen_or_escalate_case(case_id, reason)


app = mcp.streamable_http_app()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
