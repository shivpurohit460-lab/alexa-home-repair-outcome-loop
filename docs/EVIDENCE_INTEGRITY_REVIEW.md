# Evidence-integrity review gate — 29 Sep 2026

**Scope:** Proposed patch for the simulated Alexa+ repair outcome loop; not a release.

## Failure conditions addressed

- A reading taken before provider completion must not close a case.
- Readings older than 15 minutes, invalid/future-dated timestamps, unrecognized source labels and non-finite temperatures are **inconclusive**; none can establish verified recovery or authorize escalation.
- A fresh synthetic reading taken after reported provider completion above the threshold produces **not_recovered** and permits one recovery transition.
- Premature, repeated or evidence-free recovery; rebooking verified-closed cases; duplicate provider completion are rejected.
- A user-supplied recovery note cannot overwrite the verified failure reason.

## Contract and assumptions

`verify_outcome` preserves existing keys and adds `verification_state` (`verified`, `not_recovered`, `inconclusive`), `evidence_status`, `evidence_source` and timestamps.

The 15-minute freshness limit and 30-second future-clock tolerance are provisional demo assumptions, not validated hardware behavior. `HomeState.source` is a plain synthetic label, **not authenticated device attestation**. No actual provider/thermostat system is integrated.

All six MCP operation names, the seven-step judge story, public page and existing AWS Gate 5B remain untouched.

## Review and promotion requirements

1. Review exact-branch Python 3.11/3.13 CI, Ruff and all existing MCP/demo regressions.
2. Verify negative tests reject false closure and invalid state transitions; demonstrate a deliberate mutant is caught.
3. Have a separate reviewer attack clock boundaries, spoofed timestamps and provenance, cross-case/state isolation and time-of-check/time-of-use. This narrow patch does not solve all production risks.
4. Preserve `main`, public GitHub Pages, Devpost, and owner-controlled submission. No merge or release before review.

The recovery gate additionally compares the exact in-memory observation snapshot
(provider timestamp, reading timestamp, temperature and source) against the one
that established the last failed verification. Any intervening observation must
be reverified. This is a bounded sequential check, not transactional concurrent
integrity or cryptographic source authentication.

## Independent Claude source-review response and exact-SHA reproduction

Claude examined PR #11 at `a3c986445d79d1f7cdd30bfaab0957f0a9b16fa5` but explicitly **did not** run any code or inspect all source files. Its report is a valuable separate-model source review, not a completed independent runtime audit. It identified F1–F9 and requested negative reproductions. The full `demo_engine.py` confirms that the synthetic hot reading occurs **after** provider completion; the speculative demo-break path does not apply to the checked revision. F9's feared old comparison is absent from final `tools.py`.

**Red evidence:** Test-only branch `audit/2026-09-29-claude-repro` starts at that exact PR head and adds only `tests/test_claude_adversarial_repro.py`. [GitHub run 36534037166](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/actions/runs/36534037166) independently executed those checks on Python 3.11 and 3.13. Each job reported **6 expected failures, 37 baseline passes and 4 dependency deprecation warnings**, with Ruff PASS. The six failures reproducibly confirm both F1 variants, F2, F3, F6 and F8 rebooking. The test-only branch deliberately remains red; do not merge it.

**Revised PR #11 changes:**

- **F1:** Verified closure becomes monotonic. Repeat verification returns the saved historical evidence/tolerance explicitly labeled `historically_verified`; it must not imply a live current reading. Provider progress after verified closure is prohibited.
- **F2:** `mark_in_progress` requires booked service or a valid reopened/escalated revisit; it cannot turn an unbooked case into a completed provider job.
- **F3:** `home_recovered` is now `null` in inconclusive JSON (Python `None`); consumers **must branch on `verification_state`**, not `not verified` as if it meant proven failure. This is a deliberate response-contract change; review external clients before release.
- **F4:** The pre-existing one-process reentrant store lock now serializes all six public tool operations and three simulator mutations, covering same-process read/check/write windows. It does **not** authenticate `case_id`, protect against direct state mutation or synchronize independent worker processes.
- **F5:** Recovery rechecks the original observation's freshness and provider-time ordering at the recovery call. Expired verification requires a fresh check.
- **F6:** Coarse *synthetic-only* temperature plausibility bounds (-20°C to +60°C) apply on input and verification. This is not sensor calibration or certified environmental safety.
- **F8:** An escalated case can be explicitly rebooked for another provider visit; missing-evidence timeouts, human handoff and escalation ceilings remain a separate unimplemented policy.
- **Additional F10 found during review:** Verifying a newly open case before any provider booking no longer changes its status into an unbookable `AWAITING_VERIFICATION` state.

**Pending:** The exact revised-head CI, independent clean-environment replay, deliberate mutation of timestamp ordering, cross-process/tenant authorization review, and owner decision. F7 caller-controlled tolerance and unbounded recovery notes still require separate policy, including whether any trust level beyond a synthetic prototype is intended. No claim of live Alexa+, device attestation, deployment or production readiness.

**Non-regression:** Keep `main`, six MCP operation names, seven-step public judge simulator, live AWS Gate 5B, and current Devpost entry unchanged. Reviewer approval and owner merge authorization remain separate gates.
