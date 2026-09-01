from __future__ import annotations

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

from .agent import SYSTEM_PROMPT
from .agentcore_tools import CLOUD_TOOLS, get_tool_trace, reset_tool_trace

app = BedrockAgentCoreApp()


def build_cloud_agent() -> Agent:
    """Build the Strands agent used inside Amazon Bedrock AgentCore Runtime.

    The cloud runtime uses the same six domain operations as the MCP server through
    direct Strands adapters. This keeps the AgentCore deployment self-contained while
    preserving the independently tested MCP transport for the Alexa+ track.
    """
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    return Agent(model=model_id, tools=CLOUD_TOOLS, system_prompt=SYSTEM_PROMPT)


def invoke_payload(payload: dict, agent: Agent | None = None) -> dict:
    """Execute one AgentCore invocation and return an auditable tool trace."""
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {"error": "payload.prompt is required"}

    reset_tool_trace()
    runtime_agent = agent or build_cloud_agent()
    result = runtime_agent(prompt)

    return {
        "result": str(result),
        "runtime": "amazon-bedrock-agentcore",
        "framework": "strands-agents",
        "model_id": os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
        "tool_trace": get_tool_trace(),
    }


@app.entrypoint
def invoke(payload: dict) -> dict:
    """Amazon Bedrock AgentCore Runtime entry point."""
    return invoke_payload(payload)


if __name__ == "__main__":
    app.run()
