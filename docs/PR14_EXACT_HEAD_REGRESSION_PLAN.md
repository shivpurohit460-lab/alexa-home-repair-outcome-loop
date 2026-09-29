# PR #14 exact-head regression follow-up (test-only proposal)

## Provenance and scope

- Target original PR #14 head: `86a5a0e60195daacfd6e5a655729ddf19ed616de`.
- Base the follow-up directly on this exact original PR head, not on a reconstructed patch or on `main`.
- This follow-up **adds tests and this note only**. Do not edit PR #14, PR #11, the six-tool MCP surface, simulator/production code, existing acceptance criteria, or any deployment.
- PR #14 remains draft. Shiv retains merge approval; this follow-up also remains draft until its tests and an independent challenge pass.

## Reviewer findings specifically addressed

The supplied independent incremental review found F7 fixed-tolerance and F7b recovery-note boundaries passing for a locally reconstructed PR #14, but reported surviving mutants B1, B2, B3, B13 and D2–D6. These are **test-detection gaps**, not proof that the current implementation fails. The new `tests/test_pr14_exact_head_regressions.py` includes:

1. Exactly 25.0 °C at target 24.0 °C accepted, 25.000001 °C rejected, catching a `<=` to `<` threshold mutant (B1).
2. Reopen future-observation check at +30 seconds accepted and +30 seconds + 1 microsecond rejected, asserting preservation of state on rejection (B2).
3. Reopen pre-completion check at exactly the provider timestamp accepted and one microsecond earlier rejected, asserting preservation of state on rejection (B3).
4. Independent off-thread RLock ownership probes at the entry of all seven public state mutators: create, book, verify, reopen, mark in progress, provider complete, and synthetic-state update. These target D2–D6 in addition to existing reopen coverage. An entry-lock probe does **not** prove uninterrupted lock ownership during every later mutation, or across processes.
5. Functional fail-closed tests: invalid, stale and pre-completion evidence produce `inconclusive` and cannot cause recovery. A separate normalized instruction-contract assertion detects the reported contradictory B13 prompt mutant, comparing agent and MCP guidance. **Live model behavior is not tested**, and the prompt wording check alone does not prove the agent's behavior.

## Explicitly out of scope

- F8 timeout, retry, escalation ceiling and human handoff remain [issue #12](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/issues/12).
- External MCP authentication, tenant authorization and multi-worker atomicity remain [issue #13](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/issues/13). Do not expose the current unauthenticated `0.0.0.0` listener outside an isolated sandbox.
- The fixed `tolerance_c` parameter remains in MCP schema; raw, not trimmed, 500-character note validation remains unchanged. Those low-severity consistency choices need separate decisions.
- No real-device provenance, trusted sensor clocks, live Alexa integration, AWS production or production-ready claims.

## Promotion gate

- Fetch original PR #14's exact head and compare this branch: exactly one new test module and one new review note.
- Run Ruff, pytest and the synthetic demo against this actual checked-out branch. GitHub CI must pass on Python 3.11 and 3.13; independent reviewer may also use Python 3.12.
- Independently inject B1/B2/B3/B13 and D2–D6 mutants into **disposable** worktrees. Show the intended new test failing for each mutant, and show all tests passing without mutations. Preserve raw commands, outputs and commit references.
- Record the limitations of model-prompt behavior tests, one-process RLock, unauthenticated MCP and the absence of real-world evidence.
- Independent reviewer returns PASS, FAIL or INCONCLUSIVE. No merge or deployment without Shiv's explicit approval.
