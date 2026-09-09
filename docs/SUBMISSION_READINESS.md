# Submission Readiness — Build, Ship, Shape: Amazon Developer Hackathon 2026

Primary track target: **Alexa+**

Project: **Alexa+ Home-Repair Outcome Loop**

Core idea: Most assistants stop when an action reports success. This project keeps responsibility open until the **real-world outcome is verified**, and reopens/escalates the case when evidence shows the problem is not actually fixed.

## Current gate status

| Gate | Status | Evidence / next action |
| --- | --- | --- |
| Core deterministic outcome loop | PASS | Domain, simulator, recovery logic and tests are in the repository. |
| MCP tool surface | PASS | Six frozen tools exposed through MCP. |
| Streamable HTTP MCP round trip | PASS | HTTP-level integration test completed in prior build gate. |
| Simulated Alexa+ judge experience | PASS | Source is in the repository. |
| Public GitHub Pages simulator | PASS | Pages build/deploy succeeded and the public URL completed the full seven-step flow on a real Android mobile browser. See `RUNTIME_EVIDENCE.md`. |
| CI / lint / tests | PASS | Current `main` CI completed successfully on Python 3.13. |
| Open-source license | PASS | MIT `LICENSE` present in public repository. |
| AgentCore integration code | PASS (code/CI) | Runtime entry point, traced adapters and deployment config are present. |
| Live AgentCore + Bedrock deployment | BLOCKED EXTERNALLY | AWS account verification is blocking CloudShell/Bedrock. Internal AWS service-team escalation raised. No live deployment claimed yet. |
| Product feedback | DRAFTED | See `PRODUCT_FEEDBACK_DRAFT.md`; update after live AWS gate if it becomes available. |
| Friction log | DRAFTED | See `FRICTION_LOG.md`. |
| Demo video (<3 min, English) | SCRIPT PASS / RECORDING TODO | Judge narration and shot plan are frozen in `DEMO_VIDEO_SCRIPT.md`; record/edit/upload next. |
| Devpost project/draft | DRAFT CREATED | Devpost draft project exists for the Amazon Developer Hackathon; project copy and links can now be hardened without submitting. |
| Final submission answers | TODO | Complete required custom fields, track/mini-challenge choices and evidence URLs only after final compliance audit. |

## Alexa+ primary-track compliance

The hackathon accepts either:

1. a self-hosted MCP server using the required Streamable HTTP / MCP revision path, or
2. a simulated Alexa+ experience in a web app.

This repository deliberately supports both judgeability paths:

- a real MCP server at `/mcp`, independently tested through Streamable HTTP,
- a deterministic simulated Alexa+ experience for no-credential judging.

The repo must continue to show the required technology **in code**, not only in the README.

## AWS Builder mini-challenge decision

**Current state: conditional / not yet earned.**

Do not enter the AWS Builder mini-challenge merely because AgentCore/Bedrock code exists. Enter only if we can provide convincing documented evidence that AWS services were actually incorporated and exercised for the project during the hackathon window.

Preferred proof gate:

- live Bedrock model-access check passes,
- AgentCore deploy/ready succeeds,
- remote invocation succeeds,
- returned response includes the runtime path and a real `tool_trace`,
- screenshots/log evidence is preserved before cleanup.

If AWS account access is not restored in time, submit the Alexa+ primary track without overstating AWS Builder eligibility.

## Open Source mini-challenge decision

**Strong candidate.**

The project is a new public repository created during the hackathon window and contains an MIT license. Before final submission, verify the Open Source mini-challenge fields against the live Devpost form and provide:

- contribution/project URL,
- repository URL,
- GitHub username,
- concise explanation of what was built, how it works, and why it matters.

## Required Devpost deliverables

### Project page

- Project name
- One-line tagline
- Full text description
- Built-with technologies
- Public GitHub repository URL
- Public judge simulator URL

### Demo video

- YouTube or Vimeo
- public
- English
- under 3 minutes
- strongest material first
- no unlicensed music/footage/trademarks

### Product feedback

For every Amazon/AWS tool, API or SDK actually used, answer:

1. what it was used for,
2. what worked well,
3. what needs work,
4. how onboarding felt,
5. whether we would build with it again and why.

Do not describe planned/live-unverified AWS behavior as completed.

### Friction log

Submission-ready entry must include:

- task attempted,
- steps taken,
- expected vs. actual result,
- severity,
- workaround,
- actionable suggestion.

The AWS verification incident now has a structured draft in `FRICTION_LOG.md`.

## 3-minute judge story — frozen structure

### 0:00–0:20 — Problem

"An assistant saying 'the technician completed the job' is not the same as the home actually being fixed."

Show the user reporting an AC problem.

### 0:20–0:55 — Action

The agent opens the repair case and books service through bounded tools.

### 0:55–1:30 — False closure exposed

Provider status says complete, but home-state evidence still shows the room is too warm.

The agent refuses to claim success.

### 1:30–2:00 — Recovery loop

The agent verifies the outcome, reopens/escalates, and keeps responsibility active.

### 2:00–2:25 — Verified closure

Only after the home returns to the target state does the case close as verified.

### 2:25–2:45 — Technical proof

Show:

- Streamable HTTP MCP endpoint/tool surface,
- automated test/CI proof,
- public simulator,
- AgentCore/Bedrock proof only if Gate 5B has actually passed.

### 2:45–3:00 — Impact

Close on the principle:

**Agents should optimize for verified outcomes, not successful API calls.**

## Next execution order

1. Merge Gate 8 runtime-evidence documentation after CI passes.
2. Harden the existing Devpost draft with reviewed tagline, description, technologies, repository URL and public simulator URL.
3. Fetch the live submission requirements and map every required field before any submission attempt.
4. Record/edit the frozen under-3-minute demo video and upload publicly to YouTube or Vimeo.
5. Keep AWS Gate 5B isolated; rerun it immediately if AWS restores account access.
6. Perform the final compliance/truth-boundary audit, then submit only when all mandatory gates are complete.
