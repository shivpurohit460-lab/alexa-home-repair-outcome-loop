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
