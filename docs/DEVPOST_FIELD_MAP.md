# Devpost Submission Field Map — Amazon Developer Hackathon 2026

Fetched from the live Devpost submission form on 09 Sep 2026.

This document is a preparation map only. **Do not submit from this file without the project owner's explicit review of personal attestations and the final video/AWS state.**

## Project-level deliverables

- Project: `Alexa+ Home-Repair Outcome Loop`
- Public repository: `https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop`
- Public testing link: `https://shivpurohit460-lab.github.io/alexa-home-repair-outcome-loop/`
- License: MIT
- Demo video: **TODO — required, public YouTube/Vimeo, English, <3 min**

## Custom field map

| Field ID | Field | Planned answer / state |
| --- | --- | --- |
| 28285 | Submitter Type | **OWNER CONFIRMATION REQUIRED:** Individual / Team / Organization |
| 28286 | Organization Name | If submitting as SHANX: `SHANX SYSTEMS`; otherwise `N/A`. Must match owner decision above. |
| 28287 | Country of Residence | `India` |
| 28288 | Canada province | `N/A` |
| 28289 | Primary Track(s) | `Alexa+` |
| 28290 | Public GitHub repository | `https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop` |
| 28291 | New or existing before Aug 31, 2026? | `New` |
| 28292 | Existing-project updates | Leave blank because project is new. |
| 28293 | AWS Builder Mini Challenge? | **PENDING GATE 5B.** `Yes` only if live AWS incorporation/evidence is strong enough before submission; otherwise `No`. |
| 28294 | AWS services incorporated and how | Required form field. If AWS Builder = No, answer truthfully that the repository contains Strands/AgentCore/Bedrock integration code but live AWS deployment remained unverified and AWS Builder is not being claimed. If Gate 5B passes, replace with verified services + invocation evidence. |
| 28295 | Open Source Mini Challenge? | Planned `Yes`, subject to final audit. |
| 28296 | Open Source contribution URL | Public repo or a qualifying hackathon-window contribution URL; verify best exact URL before submission. |
| 28297 | Open Source project repository URL | `https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop` |
| 28298 | GitHub username | `shivpurohit460-lab` |
| 28299 | Open Source description | New MIT-licensed public project built during the hackathon. Explain the bounded MCP tool surface, deterministic outcome-verification loop, tests, public simulator and why verified outcomes matter. |
| 28300 | Optional Feature Requests | Draft after final tool experience review. |
| 28301 | Optional Friction Log URL | `https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/blob/main/docs/FRICTION_LOG.md` |
| 28302 | Optional Project Testing Link | `https://shivpurohit460-lab.github.io/alexa-home-repair-outcome-loop/` |
| 28303 | Feedback Q1 — tools used / purpose | Source from `PRODUCT_FEEDBACK_DRAFT.md`; preserve distinction between verified use and live-unverified AWS runtime. |
| 28304 | Feedback Q2 — what worked well | Source from `PRODUCT_FEEDBACK_DRAFT.md`. |
| 28305 | Feedback Q3 — what needs work | Source from `PRODUCT_FEEDBACK_DRAFT.md` + `FRICTION_LOG.md`. |
| 28306 | Feedback Q4 — onboarding | Source from `PRODUCT_FEEDBACK_DRAFT.md`; do not claim successful live AgentCore onboarding before Gate 5B. |
| 28307 | Feedback Q5 — build with again? | Source from `PRODUCT_FEEDBACK_DRAFT.md`. |
| 28308 | Age attestation | **OWNER MUST PERSONALLY CONFIRM** before submission. |
| 28309 | Eligible-jurisdiction attestation | **OWNER MUST PERSONALLY CONFIRM** before submission. |
| 28310 | Promotion-entity employee attestation | **OWNER MUST PERSONALLY CONFIRM** before submission. |

## Track compliance note

The live form confirms Alexa+ accepts either:

- a self-hosted MCP server using specification `2025-11-25+` and Streamable HTTP, or
- a simulated Alexa+ experience whose source code is in the repository and whose demo clearly shows it working.

This project has both a Streamable HTTP MCP implementation and a public deterministic simulation. The final video should show the simulation working and briefly show the MCP code/transport evidence.

## AWS Builder decision rule

Do **not** choose `Yes` merely because AWS SDK/runtime code exists.

Choose `Yes` only if final evidence supports the statement that AWS services were actually incorporated into the hackathon project strongly enough to satisfy the live form requirement. Preferred evidence remains:

1. Bedrock model-access check passes.
2. AgentCore runtime deploys and reaches ready state.
3. Remote invocation succeeds.
4. Returned response includes the runtime path and actual tool trace.
5. Evidence is preserved for judges.

If AWS verification stays blocked, submit Alexa+ without overstating the AWS Builder mini-challenge.

## Personal-attestation boundary

The following are not technical fields and must never be inferred by automation:

- submitter type / organization representation,
- age-of-majority checkbox,
- eligible-jurisdiction checkbox,
- employee/representative/agent checkbox.

Collect explicit owner confirmation immediately before final submission.
