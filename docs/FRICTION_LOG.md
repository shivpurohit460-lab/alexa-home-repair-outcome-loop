# Friction Log — AWS Account Verification Blocking Live AgentCore Deployment

## Summary

**Task attempted:** Deploy the Alexa+ Home-Repair Outcome Loop to Amazon Bedrock AgentCore Runtime and verify a live Amazon Bedrock invocation from AWS CloudShell.

**Severity:** High — blocks the live AWS deployment path and AWS Builder mini-challenge validation, but does not block local MCP development, CI, the public simulator, or the Alexa+ primary-track simulated-experience path.

**Observed duration:** At least 7 days before escalation to the AWS internal service team.

## Steps taken

1. Completed AWS account setup and customer/account verification steps, including payment method, phone verification, and MFA.
2. Opened AWS CloudShell in `ap-south-1` (Mumbai) to run the repository's fail-closed Gate 5B deployment script.
3. CloudShell refused to create/open an environment and displayed an account-verification-in-progress message stating that verification may take up to two days for new accounts.
4. Rechecked the account-side setup and verification state rather than weakening the deployment code or bypassing account controls.
5. Kept the existing AWS support case open after the issue remained unresolved beyond the stated window.
6. After seven days, opened a live AWS Support chat on the existing case.
7. AWS Support confirmed that an internal service-team escalation was raised and that no further documentation or verification was required from the account holder at that time.

## Expected result

After completing account verification, CloudShell should become available within the window communicated by the console so the authenticated deployment sequence can:

- verify the active AWS identity,
- make a minimal Bedrock model-access check,
- validate and dry-run the AgentCore configuration,
- deploy the AgentCore Runtime,
- invoke the remote runtime,
- capture the returned tool trace as submission evidence.

## Actual result

CloudShell remained blocked after seven days with the same verification-in-progress state. Because the repository deliberately keeps AWS credentials and account identifiers out of GitHub and chat, the safe live-deployment gate could not proceed through CloudShell.

The project therefore does **not** claim a successful live AgentCore or Bedrock deployment yet.

## Workaround used

Development continued without weakening the truth boundary:

- the MCP server remains independently tested through a real Streamable HTTP round trip,
- deterministic domain and recovery-loop tests continue in CI,
- the simulated Alexa+ judge experience is built and deployed through GitHub Pages,
- AgentCore/Bedrock integration code and deployment configuration remain code-ready and CI-tested,
- live AWS deployment stays a separate blocked gate until AWS clears the account state.

## Actionable suggestion

For new accounts that remain verification-blocked beyond the stated window, the AWS console should expose:

1. the exact verification state or pending category without exposing sensitive review logic,
2. a clear "no action required" vs. "customer action required" status,
3. an automatic escalation path once the advertised verification window is exceeded,
4. a notification when CloudShell/Bedrock service access is unlocked,
5. a support-visible correlation between account verification and service-level access so customers do not spend days retrying the same environment creation flow.

## Submission-use note

This log intentionally omits account IDs, support case IDs, personal information, and credentials. Screenshots or support correspondence can be retained privately as corroborating evidence if judges request it.
