#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
MODEL_ID="${BEDROCK_MODEL_ID:-global.anthropic.claude-sonnet-4-6}"
RUNTIME_NAME="OutcomeLoopAgent"
TARGET_NAME="default"
DO_DEPLOY="false"

if [[ "${1:-}" == "--deploy" ]]; then
  DO_DEPLOY="true"
fi

echo "== Gate 5B: AWS preflight =="
echo "Region: ${REGION}"
echo "Runtime: ${RUNTIME_NAME}"
echo "Model: ${MODEL_ID}"

command -v aws >/dev/null || { echo "ERROR: AWS CLI is required."; exit 10; }
command -v node >/dev/null || { echo "ERROR: Node.js 20+ is required."; exit 11; }
command -v npm >/dev/null || { echo "ERROR: npm is required."; exit 12; }

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if (( NODE_MAJOR < 20 )); then
  echo "ERROR: Node.js 20+ is required; found $(node --version)."
  exit 13
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
if [[ ! "${ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
  echo "ERROR: Could not resolve a valid AWS account from the active CloudShell identity."
  exit 14
fi

aws configure set region "${REGION}"

if ! command -v uv >/dev/null; then
  echo "Installing uv for Python packaging..."
  python3 -m pip install --user --quiet uv
  export PATH="${HOME}/.local/bin:${PATH}"
fi

uv python install 3.13 >/dev/null

echo "Installing/updating AgentCore CLI and AWS CDK..."
npm install -g @aws/agentcore aws-cdk >/dev/null

cat > agentcore/aws-targets.json <<EOF
[
  {
    "name": "${TARGET_NAME}",
    "description": "Hackathon deployment target (Mumbai)",
    "account": "${ACCOUNT_ID}",
    "region": "${REGION}"
  }
]
EOF

echo "Checking Bedrock model access with a minimal live call..."
MODEL_REPLY="$(aws bedrock-runtime converse \
  --region "${REGION}" \
  --model-id "${MODEL_ID}" \
  --messages '[{"role":"user","content":[{"text":"Reply with READY only."}]}]' \
  --inference-config '{"maxTokens":8,"temperature":0}' \
  --query 'output.message.content[0].text' \
  --output text)"

echo "Bedrock replied: ${MODEL_REPLY}"

if [[ "${MODEL_REPLY}" != *"READY"* ]]; then
  echo "ERROR: Bedrock responded, but the expected READY marker was not returned."
  exit 15
fi

echo "Validating AgentCore project..."
agentcore validate

echo "Running deployment dry-run..."
agentcore deploy --target "${TARGET_NAME}" --dry-run

echo "Gate 5B preflight: PASS"

if [[ "${DO_DEPLOY}" != "true" ]]; then
  echo "No AWS resources were deployed. Re-run with --deploy to create the runtime."
  exit 0
fi

echo "Deploying AgentCore Runtime. AWS resources may incur charges until removed."
agentcore deploy --target "${TARGET_NAME}" --yes --verbose

agentcore status \
  --runtime "${RUNTIME_NAME}" \
  --target "${TARGET_NAME}" \
  --json > gate5b-status.json

echo "Invoking deployed runtime..."
agentcore invoke \
  --runtime "${RUNTIME_NAME}" \
  --target "${TARGET_NAME}" \
  --prompt "My AC is broken. Handle it and make sure it is actually fixed. Do not claim success without outcome evidence." \
  --json | tee gate5b-invoke.json

echo
echo "Gate 5B live deployment command completed."
echo "Saved: gate5b-status.json and gate5b-invoke.json"
echo "To inspect recent runtime errors: agentcore logs --runtime ${RUNTIME_NAME} --since 30m --level error"
