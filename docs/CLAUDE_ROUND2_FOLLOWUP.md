# Claude Round 2 follow-up — isolated audit gate, 29 Sep 2026

## Change boundary

This review branch starts at the **exact** independently reviewed PR #11 GREEN commit
`04e2724b00f4ecde46677ba8533e6035572bcbce`.
It must **NOT** be merged directly to `main`; it is a separate, proposed follow-up
to [Draft PR #11](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/pull/11).
The latter's audited head and the existing public judge simulator stay unchanged.

External Claude Round 2 ran with Python 3.12.3 and offline wheels. Its own report:
BASE 14 pass, RED six fail/37 pass, GREEN 48 pass, Ruff pass; demo seven steps and
Streamable HTTP/AgentCore tests passed. It found F7 tolerance override, F7b unbounded
untrusted recovery notes, F8 stalled cases and mutation-test gaps. The original
repository did **not** independently attest to real-world sensor evidence.

## Scope: F7 and F7b repaired, mutation-test gaps targeted

- **Acceptance contract fixed at creation:** every synthetic repair case now stores
  `verification_tolerance_c=1.0`. The creation response explicitly returns the
  tolerance and threshold as part of the initial success criterion. The existing
  `verify_outcome(case_id, tolerance_c=1.0)` MCP/Strands signature remains callable,
  but **any other tolerance is rejected** (including booleans, NaN, 0, 5 and 50),
  without changing prior evidence or case state. An operator cannot change the
  outcome threshold after service completion. Only an in-process developer with
  direct state access can tamper with the stored policy; such access is outside the
  prototype's trust boundary and is NOT a real-world attestation guarantee.
- **Recovery note:** `reason` is raw caller-supplied narrative, **not evidence or
  instructions**. Strings longer than 500 raw characters are rejected BEFORE state
  mutation and `recovery_note_trust="untrusted_user_input"` is included in the
  response when a note exists. The additive trust label is not sanitization or
  prompt-injection immunity. Downstream clients must treat the text as data.
- **Tri-state client alignment:** Strands system prompt and MCP tool instructions
  now permit automatic recovery only after explicit `not_recovered` with fresh
  evidence, not on `inconclusive`. They explicitly disclose simulator-only evidence.
- **Mutation-targeted negative tests:** test a cross-thread attempt to acquire the
  store lock during the recovery critical section, exact 15:00 expiration boundary,
  30-second future timestamp boundary, status guard, strict tolerance matching,
  note-limit edge and agent prompt consistency. These augment—not replace—the
  existing six original negative reproductions and MCP/demo contract tests.
- All changes remain **synthetic hackathon prototype only**. The six MCP tool names
  and tool call signatures remain unchanged, although attempts to override
  `tolerance_c` now raise a documented error and the creation response gains
  acceptance criteria fields. External clients must honor `verification_state`.

## Reproducibility and prior CI

| Gate | Exact commit / job | Outcome |
|---|---|---|
| External Claude Round 2 | original GREEN `04e2724b...` | Claude reported 48 pass on Python 3.12; six red failures replicated. |
| New F7/F7b RED repro | `98214af31fc5f0c55118d5ff87c15f616e3ebe0b`, [run 36538592698](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/actions/runs/36538592698) | **11 intentionally failing / 58 passing, Ruff pass**, EACH on Python 3.11 and 3.13. |
| Isolated fixed code + expanded prompt checks | `d0ac10a6534ec2f40e77880fa57d34d2e27a3184`, [run 36538974065](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/actions/runs/36538974065) | **70 passing, 4 dependency warnings, Ruff pass**, EACH on Python 3.11 and 3.13. |
| One deliberate lock removal mutation | isolated branch `audit/2026-09-29-mutation-lock`, separate CI | Pending results at initial authoring. Must fail the new cross-thread lock-ownership test to substantiate the coverage improvement. |

Passing CI is NOT independent security certification; a separate reviewer must challenge
the revised exact head before any change is promoted.

## Explicitly unresolved (not silently waived)

- [F8 — stalled evidence, human handoff and escalation ceiling](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/issues/12):
  no user-facing MCP way to obtain fresh evidence once an observation is permanently
  unavailable; six or more genuine failures may escalate indefinitely. This requires
  a specified safe timeout/human policy, not invented automatic closure. Outside
  this narrow F7/F7b repair; BLOCK for production.
- [Security gate — unauthenticated MCP and multi-worker isolation](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/issues/13):
  current FastMCP bind `0.0.0.0` and no tenant authorization means do not publicly
  expose it. `STORE` lock is in-process only; a combined demo/MCP process could
  be harmed by `build_demo_timeline` calling `STORE.reset()` (conditional
  hosting hypothesis). Authenticate and isolate before external deployment.
- Direct state+snapshot tampering by an in-process actor can defeat the synthetic
  verifier; unverified device provenance and untrusted clock source remain outside
  the hackathon implementation. The ±30-second tolerance and 15-minute freshness
  rule are provisional and unvalidated for real appliances.
- No public Alexa+, real thermostat, AWS production or durable multi-tenant
  reliability claim. The public demo and Devpost status remain unchanged.
- [Branch protection before submission](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/issues/10) remains open.

## Promotion gate

1. Confirm precise final follow-up diff, zero unexpected dependencies and both raw
   GREEN CI job logs.
2. Independently challenge F7 and note-size failure cases, tri-state agent
   instructions, exact boundary behavior and the *actual* lock-removal mutation
   result.
3. Retain F8/security issues as explicit blockers for any real-world or public
   service claims; separate synthetic-only judge-demo scope from production.
4. Obtain owner approval before any update/merge of audited PR #11 or its follow-up.
