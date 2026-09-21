# Gate 5B — Live AWS AgentCore Deployment

This gate proves that the hackathon agent actually runs on **Amazon Bedrock AgentCore Runtime** and invokes **Claude Sonnet 4.6 through Amazon Bedrock**.

## Why CloudShell

AWS CloudShell keeps AWS authentication inside the AWS account session. No access keys, account IDs, or secrets need to be copied into GitHub or chat.

The deployment target is **Asia Pacific (Mumbai) — `ap-south-1`**. The model is `global.anthropic.claude-sonnet-4-6`.

## Run from AWS CloudShell

```bash
git clone https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop.git
cd alexa-home-repair-outcome-loop
bash scripts/gate5b_cloudshell.sh --deploy
```

The script deliberately performs these gates in order:

1. Verify the active AWS identity without printing the account ID.
2. Refuse deployment when the caller is the AWS root identity; use a scoped IAM deployment role/user instead.
3. Use Mumbai as the AWS region.
4. Ensure `uv`, AgentCore CLI, and AWS CDK are available.
5. Generate a local, gitignored `agentcore/aws-targets.json`.
6. Make a minimal live Bedrock call and require a `READY` response.
7. Run `agentcore validate`.
8. Run `agentcore deploy --dry-run`.
9. Deploy the runtime only after the preceding checks pass.
10. Invoke the deployed runtime with the AC-repair prompt.
11. Save `gate5b-status.json` and `gate5b-invoke.json` locally for verification.

## What counts as PASS

Gate 5B is not complete merely because CloudFormation deploys.

PASS requires:

- AgentCore Runtime reaches a deployed/ready state.
- Remote invocation returns successfully.
- Response identifies the AgentCore/Strands runtime path.
- Returned `tool_trace` contains at least one of the frozen outcome-loop tools.
- No fabricated successful repair claim is made without outcome evidence.

## Current provider evidence — 21 Sep 2026

A read-only ARRA recheck confirmed that AWS identity lookup, Bedrock model/profile listing, and AgentCore control-plane listing are reachable. The configured `global.anthropic.claude-sonnet-4-6` profile is ACTIVE, but a minimal `Converse` call still returns an account-verification `AccessDeniedException`. No AgentCore runtime is currently deployed.

This means Gate 5B remains blocked before deployment. Do not reinterpret catalog visibility as live model access.

## If Bedrock model access fails

Open the Amazon Bedrock console in the same account and region and resolve model/Marketplace access for Claude Sonnet 4.6, then rerun the script. Do not weaken the code to hide an access failure.

## Cost boundary

`--deploy` creates AWS resources and makes a small live model call. AWS charges may apply until resources are removed. Keep the runtime only while it is useful for the hackathon.

Before cleanup, save screenshots/log evidence required for the submission.
