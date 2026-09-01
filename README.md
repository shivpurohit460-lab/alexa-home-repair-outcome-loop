# Alexa+ Home-Repair Outcome Loop

Hackathon prototype for **Build, Ship, Shape: Amazon Developer Hackathon 2026**.

Most assistants stop when an action reports success. This prototype keeps responsibility open until the **real-world outcome** is verified.

## Demo story

1. A user reports an AC problem.
2. The agent opens a repair case and books a service provider.
3. The provider later marks the job complete.
4. Home-state evidence still shows the room is too warm.
5. The agent refuses false closure and reopens/escalates the case.
6. Only after the home returns to the target state does the case close as verified.

## Frozen MCP tool surface

- `create_repair_case`
- `book_home_service`
- `get_service_status`
- `read_home_state`
- `verify_outcome`
- `reopen_or_escalate_case`

## Architecture

```text
Simulated Alexa+ experience
        |
        v
Strands agent + Amazon Bedrock
        |
        v
Self-hosted MCP server (Streamable HTTP)
        |
        +--> deterministic service simulator
        +--> deterministic thermostat/home-state simulator
        |
        v
Outcome verification + recovery loop
```

The MCP server is built against the current stable MCP Python SDK v2 line and exposes Streamable HTTP at `/mcp`.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
uvicorn alexa_outcome_loop.mcp_server:app --host 0.0.0.0 --port 8000
```

MCP endpoint:

```text
http://localhost:8000/mcp
```

Run deterministic tests:

```bash
pytest
```

Run the no-LLM demo flow:

```bash
python scripts/demo_flow.py
```

## Strands + Bedrock

Set AWS credentials using your normal AWS credential chain. Optionally set:

```bash
export AWS_REGION=us-west-2
export BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6
export MCP_SERVER_URL=http://127.0.0.1:8000/mcp
```

Then:

```bash
python -m alexa_outcome_loop.agent "My AC is broken. Handle it and make sure it is actually fixed."
```

## AgentCore

`src/alexa_outcome_loop/agentcore_app.py` contains a minimal `BedrockAgentCoreApp` entry point. Deployment comes after local validation.

## Safety / scope

This prototype coordinates household repair outcomes. It does **not** diagnose medical conditions, control safety-critical equipment, or claim that a provider's business system is real. Simulator state is clearly separated from real integrations.

## License

MIT — see [LICENSE](LICENSE).
