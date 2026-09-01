from __future__ import annotations

import os
import sys

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

SYSTEM_PROMPT = """You are the Alexa+ Home-Repair Outcome Loop agent.
Your job is to keep responsibility open until the user's real-world outcome is verified.

Rules:
1. Create a repair case before booking service.
2. Provider-side completion is evidence, never sufficient proof of success.
3. Before declaring the repair resolved, read home state and call verify_outcome.
4. If verification fails, reopen_or_escalate_case rather than telling the user it is fixed.
5. State uncertainty explicitly. Do not invent sensor readings, provider status, or confirmations.
"""


def build_agent(server_url: str | None = None) -> tuple[Agent, MCPClient]:
    mcp_url = server_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    client = MCPClient(
        lambda: streamablehttp_client(mcp_url),
        application_name="alexa-home-repair-outcome-loop",
    )
    agent = Agent(model=model_id, tools=[client], system_prompt=SYSTEM_PROMPT)
    return agent, client


def run(prompt: str, server_url: str | None = None) -> str:
    agent, client = build_agent(server_url)
    with client:
        result = agent(prompt)
        return str(result)


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        raise SystemExit("Usage: outcome-loop-agent <prompt>")
    print(run(prompt))


if __name__ == "__main__":
    main()
