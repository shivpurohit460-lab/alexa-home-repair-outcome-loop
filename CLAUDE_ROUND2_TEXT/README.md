# CLAUDE ROUND 2 — NO-DOWNLOAD CODE REVIEW

**This folder exists specifically because direct ZIP/sandbox transfers to Claude repeatedly failed.** It is a read-only audit transport on a SEPARATE GitHub branch. Its three `.md` source snapshots contain verbatim source and original blob hashes fetched by the GitHub connector from the exact commits; they are not altered runnable source trees.

## Exact scope
- `BASE.md`: main/base commit `3d396517485d8096da91397e3adf142ac7e7d7ca` (12 critical files; no newer tests)
- `RED.md`: original PR head plus independent intentionally failing tests `746638fd97c067ccb1726cd774e8783284f93c66` (14 critical files)
- `GREEN.md`: revised PR head `04e2724b00f4ecde46677ba8533e6035572bcbce` (15 critical files, including updated review document)
- `CI_EVIDENCE.md`: curated, labeled raw excerpts from the earlier GitHub Actions jobs, if present. Historical CI is NOT your own execution.

The full GREEN source tree remains at this branch's root; the three files above preserve critical file contents from the earlier BASE and RED commits. The exported file set covers domain, store, simulators, six-tool implementation, demo engine, MCP HTTP server, AgentCore tool adapter, test files and package/test configuration. It does **not** claim to contain every file in all three historical commits. Verify coverage before a full-repository scope verdict.

## Access in Claude WITHOUT DOWNLOADING
1. In Claude, connect GitHub under Customize → Connectors if not already connected.
2. In a chat press `+` → **Add from GitHub**. Select `shivpurohit460-lab/alexa-home-repair-outcome-loop` and, if the picker offers it, select branch `audit/claude-round2-text-review`.
3. Select this folder `CLAUDE_ROUND2_TEXT` (README, BASE, RED, GREEN and CI_EVIDENCE) and add it to the chat. If the folder is too large, select README, GREEN, RED and BASE separately.
4. Before reviewing, Claude must quote the FIRST 40 characters of each selected file's `Source commit` field as proof that the connector delivered CONTENT and did not merely insert a URL. If content didn't arrive, STOP and say so—do not claim to have examined the files.

GitHub's Claude integration reads selected file contents, NOT pull-request discussions, CI history or arbitrary repo URLs. No connection here grants extra GitHub permissions automatically. If Claude cannot choose this branch, do not change `main` just to force it: use ordinary GitHub browser's **copy file contents** into Claude as fallback.

## Audit task to send Claude
Inspect full BASE, RED and GREEN snapshots. Challenge the reported F1–F10 failure/repair claims:
- F1 monotonic verified closure and historical-vs-current evidence distinction
- F2 progress without booking and invalid simulator status changes
- F3 `home_recovered=None` and backward client compatibility
- F4 check/read/write concurrency, case isolation and lock coverage; no claim of cross-worker synchronization
- F5 recovery with expired evidence
- F6 physically implausible temperature limits
- F7 caller-controlled tolerance and unbounded recovery-note injection
- F8 ESCALATED lifecycle, repeated service booking, missing-evidence timeouts/handoff
- F9 stale-diff false alarm vs final tools.py
- F10 verification before booking must not make an OPEN case unbookable.

Review the MCP adapter, seven-step demo, original tests and adversarial tests in the source snapshots. Verify blob SHA declarations where possible. Challenge all assumptions and identify new defects. Each finding: PASS, FAIL or INCONCLUSIVE, line/file evidence, exploit or counterexample, severity, exact correction, what you actually ran, and limitations.

If you have your own executable environment, run the appropriate Python tests and deliberately mutate one evidence check in a temporary copy, then report raw results. If you only receive file CONTENT, report a **source review, not independent runtime verification**. Existing CI:
- [RED 36534037166](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/actions/runs/36534037166): Python 3.11 and 3.13 each six adversarial failures, 37 existing passes; Ruff passed.
- [GREEN 36534508472](https://github.com/shivpurohit460-lab/alexa-home-repair-outcome-loop/actions/runs/36534508472): Python 3.11 and 3.13 each 48 tests passed; Ruff passed. These are GitHub executions, NOT Claude's.

Strictly read-only. Do not edit/push/merge, deploy AWS, alter public Pages or submit Devpost. Stop after returning the complete audit with promotion blockers. PR #11 remains draft and owner approval is required before any merge.
