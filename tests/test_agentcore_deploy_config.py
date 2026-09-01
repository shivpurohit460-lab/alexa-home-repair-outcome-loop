from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_agentcore_deployment_config_is_safe_and_deployable() -> None:
    config = json.loads((ROOT / "agentcore" / "agentcore.json").read_text())
    runtime = config["runtimes"][0]

    assert config["name"] == "AlexaOutcomeLoop"
    assert runtime["name"] == "OutcomeLoopAgent"
    assert runtime["build"] == "CodeZip"
    assert runtime["runtimeVersion"] == "PYTHON_3_13"
    assert runtime["protocol"] == "HTTP"
    assert runtime["entrypoint"] == "agentcore_entrypoint.py"
    assert (ROOT / runtime["entrypoint"]).is_file()

    env = {item["name"]: item["value"] for item in runtime["envVars"]}
    assert env["AWS_REGION"] == "ap-south-1"
    assert env["BEDROCK_MODEL_ID"] == "global.anthropic.claude-sonnet-4-6"


def test_private_aws_target_and_runtime_outputs_are_gitignored() -> None:
    ignored = (ROOT / ".gitignore").read_text().splitlines()

    assert "agentcore/aws-targets.json" in ignored
    assert "agentcore/.cli/" in ignored
    assert "gate5b-status.json" in ignored
    assert "gate5b-invoke.json" in ignored


def test_cloudshell_runner_has_fail_closed_ordering() -> None:
    script = (ROOT / "scripts" / "gate5b_cloudshell.sh").read_text()

    model_check = script.index("aws bedrock-runtime converse")
    validation = script.index("agentcore validate")
    dry_run = script.index('agentcore deploy --target "${TARGET_NAME}" --dry-run')
    live_deploy = script.index('agentcore deploy --target "${TARGET_NAME}" --yes --verbose')
    remote_invoke = script.index("agentcore invoke")

    assert model_check < validation < dry_run < live_deploy < remote_invoke
