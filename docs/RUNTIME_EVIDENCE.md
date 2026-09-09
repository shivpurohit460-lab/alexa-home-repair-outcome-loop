# Gate 8 — Public Judge Simulator Runtime Evidence

Date: 09 Sep 2026

## Scope

This gate records a manual runtime check of the public GitHub Pages judge simulator for the **Alexa+ Home-Repair Outcome Loop**.

Public simulator:

`https://shivpurohit460-lab.github.io/alexa-home-repair-outcome-loop/`

The simulator is intentionally deterministic and synthetic. It demonstrates the repository's real outcome-verification and recovery-loop logic without claiming that the provider, thermostat, Alexa+, Amazon Bedrock, or AgentCore paths are live production integrations.

## Manual runtime result

**Status: PASS**

The public simulator was opened on an Android mobile device and the full outcome loop completed visibly end-to-end.

Observed sequence:

1. User asks for an outcome: the AC must be handled and actually fixed.
2. Repair is booked.
3. Provider reports the job complete.
4. Outcome verification still fails because the thermostat remains at **29.2°C** while the acceptable threshold is **≤ 25.0°C**.
5. The system refuses false closure and keeps responsibility open by reopening/escalating the case.
6. After the technician revisit, the thermostat is shown at **24.4°C**.
7. Outcome verification passes only when provider completion and home-state evidence agree.
8. Final state displays **Verified resolved**.

## What this proves

This manual gate proves that:

- the public judge URL loads successfully on a real mobile browser,
- the GitHub Pages export functions without the local `/api/demo/run` backend,
- the deterministic seven-step judge story renders correctly,
- the critical truth boundary is visible: **provider complete ≠ home recovered**,
- false closure is rejected,
- closure happens only after outcome evidence passes.

## What this does NOT prove

This gate does **not** prove:

- a live Alexa+ invocation,
- a live Amazon Bedrock model response,
- a deployed AgentCore Runtime,
- a real home-service provider integration,
- a real thermostat/device integration.

Those claims remain separate gates. In particular, live AgentCore + Bedrock evidence remains blocked until AWS clears the account-verification state and Gate 5B passes.

## Evidence retention

A mobile screen recording of the runtime pass was captured by the project owner and retained outside the public repository for final demo/submission preparation.

## Gate verdict

**PASS — Public judge simulator is manually runtime-verified and judgeable on mobile.**
