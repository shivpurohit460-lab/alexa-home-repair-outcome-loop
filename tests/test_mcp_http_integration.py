from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

EXPECTED_TOOLS = {
    "create_repair_case",
    "book_home_service",
    "get_service_status",
    "read_home_state",
    "verify_outcome",
    "reopen_or_escalate_case",
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise TimeoutError(f"MCP server did not start on port {port}")


async def _round_trip(port: int) -> None:
    url = f"http://127.0.0.1:{port}/mcp"
    async with (
        streamablehttp_client(url) as (read_stream, write_stream, _),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS

        result = await session.call_tool(
            "create_repair_case",
            arguments={"issue": "AC not cooling", "target_temperature_c": 24.0},
        )
        assert result.content
        assert "repair-" in str(result.content)


def test_real_streamable_http_round_trip() -> None:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "alexa_outcome_loop.mcp_server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_port(port)
        asyncio.run(_round_trip(port))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
