# Product Feedback Draft — Amazon Developer Hackathon 2026

> Draft for Devpost submission. Keep facts separated from planned/live-unverified integrations. Update after Gate 5B if AWS account access is restored.

## MCP / Streamable HTTP

### What we used it for

The project exposes the six frozen home-repair outcome-loop operations through an MCP server using Streamable HTTP. The server is the Alexa+-compatible integration surface and is tested through a real HTTP-level MCP round trip.

### What worked well

- The tool-oriented boundary maps cleanly onto the project's domain operations.
- Streamable HTTP gives the integration a clear, testable transport surface instead of hiding the agent behind an opaque application layer.
- Keeping the MCP transport and AgentCore adapters on top of the same domain implementation reduced duplication and made behavioral testing more deterministic.
- The Python MCP SDK version used by the project supports protocol revision `2025-11-25`, which aligns with the Alexa+ hackathon requirement.

### What needs work

- Developer tooling could make protocol/transport conformance more visible through a single diagnostic command that reports negotiated protocol revision, transport health, and tool-schema validation.
- End-to-end examples that pair a Streamable HTTP MCP server with a simulated Alexa+ experience would reduce onboarding ambiguity for developers new to Alexa+.

### Onboarding

The protocol concepts were understandable once the server/tool boundary was frozen, but a stronger official "zero to Alexa+ simulation" path would make the first successful integration faster.

### Would we build with it again?

Yes. The transport and tool model fit the project's goal of auditable, bounded capabilities well.

---

## Amazon Bedrock AgentCore

### What we used it for

The repository contains an AgentCore Runtime entry point, deployment configuration, traced tool adapters, and a fail-closed CloudShell deployment runner intended to prove the agent remotely on AgentCore Runtime.

### What worked well

- The Runtime model provides a natural boundary for packaging the agent as a deployable service.
- Keeping a per-invocation tool trace in the project makes the runtime path auditable for judges.
- The CodeZip/Python 3.13 deployment target can be validated in CI before touching a live account.

### What needs work

Live deployment has **not yet been verified** because the AWS account remained stuck in an account-verification state that blocked CloudShell and Bedrock access. This is recorded separately in `FRICTION_LOG.md`.

The deployment experience would benefit from clearer separation between:

- application/configuration validation failures,
- model-access failures,
- account-level verification/service-access failures.

That distinction would help developers know whether to debug code or stop and escalate the account state.

### Onboarding

Local configuration and CI validation were straightforward enough to prepare safely. The live onboarding path was interrupted before deployment by account-level verification, so no claim is made about successful remote AgentCore onboarding yet.

### Would we build with it again?

Conditionally yes. The runtime model fits the project, but final feedback should be updated only after the blocked live deployment gate is completed.

---

## Amazon Bedrock

### What we intended to use it for

Claude Sonnet 4.6 through Amazon Bedrock is configured as the model for the Strands/AgentCore path.

### Current evidence boundary

- model configuration exists in code,
- integration paths are CI-tested without claiming a live model response,
- a minimal live `READY` model-access check is part of Gate 5B,
- that live check has not yet run successfully because AWS service access is account-verification blocked.

Do not convert this section into a positive live-performance claim until Gate 5B passes.

---

## Strands Agents SDK

### What we used it for

The project uses Strands to construct the agent path and expose the six outcome-loop operations as traced agent tools.

### What worked well

- The tool-first agent design maps directly to the project's deterministic domain operations.
- The agent and the MCP server can share one domain implementation while using different integration surfaces.
- The traced adapters make it easier to show judges which operations actually ran.

### What needs work

Final feedback on runtime behavior should wait for the live Bedrock/AgentCore invocation. Local and CI behavior should not be presented as remote AWS-runtime proof.

### Would we build with it again?

Yes for bounded tool-driven agents, subject to the final live-runtime validation.

---

## AWS CloudShell

### What we used it for

CloudShell was selected as the safe deployment environment so AWS authentication stays inside the AWS account session and no long-lived access keys or account identifiers need to be copied into source control or chat.

### What worked well

The security model is appropriate for a hackathon deployment workflow because it avoids moving credentials into development artifacts.

### What needs work

The environment remained unavailable for at least seven days because account verification was reported as still in progress, despite the console initially stating a window of up to two days. AWS Support later raised an internal service-team escalation and confirmed no further documentation or verification was required from the account holder at that time.

See `FRICTION_LOG.md` for the structured friction entry and proposed improvements.

### Would we build with it again?

Yes, once account activation is functioning, because the credential-isolation property is valuable. The verification-state UX needs improvement.

---

## GitHub Pages judge simulator

GitHub Pages is not an Amazon API/SDK, but it is part of the submission experience. The project exports a deterministic simulated Alexa+ experience and deploys it through a dedicated GitHub Actions workflow. This gives judges a stable, no-credential way to understand the outcome-verification loop while the real MCP and AWS paths remain separately testable.
