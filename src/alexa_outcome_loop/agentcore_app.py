from __future__ import annotations

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

from .agent import SYSTEM_PROMPT

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """AgentCore Runtime entry point.

    The MCP server URL is intentionally supplied through configuration so the same
    agent can target local development or a deployed self-hosted MCP endpoint.
    """
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {"error": "payload.prompt is required"}

    mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    client = MCPClient(
        lambda: streamablehttp_client(mcp_url),
        application_name="alexa-home-repair-outcome-loop-agentcore",
    )

    with client:
        agent = Agent(model=model_id, tools=[client], system_prompt=SYSTEM_PROMPT)
        result = agent(prompt)
        return {"result": str(result)}


if __name__ == "__main__":
    app.run()
