# Gate 7 — Demo Video Script & Shot Plan

Target: **2:40–2:50 total**. Hard ceiling: **under 3:00**.

Primary track: **Alexa+**

Project: **Alexa+ Home-Repair Outcome Loop**

## Recording rules

- English narration.
- Lead with the problem and product behavior, not setup screens.
- Show the judge simulator early.
- Show technical proof only after the core behavior is obvious.
- Do not claim live AgentCore/Bedrock execution unless Gate 5B has actually passed.
- No copyrighted music or third-party footage.
- Keep synthetic-data disclosure visible when the simulator is shown.

---

## 0:00–0:18 — Hook

### Visual

Open directly on the simulated Alexa+ experience. Keep the headline visible:

**Don't stop at “done.” Verify the outcome.**

### Narration

> Most assistants stop when an action reports success. But in the real world, “the technician completed the job” does not mean your home is actually fixed. Alexa+ Home-Repair Outcome Loop keeps responsibility open until the real-world outcome is verified.

---

## 0:18–0:38 — User request

### Visual

Show the conversation panel with:

> “Alexa, my AC is broken. Handle it and make sure it is actually fixed.”

Then click **Run outcome loop**.

### Narration

> The user asks Alexa to handle a broken AC — with one important condition: make sure it is actually fixed. The system does not treat a successful booking or a provider status as the final outcome.

---

## 0:38–1:12 — Action and false closure

### Visual

Let the timeline reveal:

- case created,
- service booked,
- provider status changes,
- home-state evidence is checked.

Pause visually when the provider says complete but the room remains too warm.

### Narration

> The agent creates the repair case, books service, and tracks the provider. Then the provider reports completion. A normal automation could close the task here. This one checks observable home-state evidence too. The room is still too warm, so the outcome is not verified.

---

## 1:12–1:38 — Recovery loop

### Visual

Show the failure/warning state and the reopen or escalation event.

### Narration

> Instead of producing a false success message, the agent refuses closure, reopens or escalates the case, and keeps responsibility active. Only when provider status and home-state evidence agree does the case become verified resolved.

---

## 1:38–1:55 — Principle / impact

### Visual

Show final state: **Verified resolved** and the principle:

**Provider complete ≠ home recovered.**

### Narration

> The idea is simple: agents should optimize for verified outcomes, not successful API calls. The same pattern can apply to deliveries, refunds, appointments, maintenance, and many other real-world workflows.

---

## 1:55–2:25 — Technical proof

### Visual sequence

1. GitHub repository root.
2. MCP server / six frozen tools.
3. Streamable HTTP test or CI success.
4. Public Pages simulator workflow success.

### Narration

> Under the hood, the project exposes six bounded operations through a Model Context Protocol server using Streamable HTTP and protocol revision 2025-11-25. The MCP path is exercised through a real HTTP-level round trip. The deterministic domain logic is tested in CI, and the judge simulator is generated from that same application logic and deployed publicly through GitHub Pages.

---

## 2:25–2:42 — AWS proof slot

Use **exactly one** of the two variants below.

### Variant A — only if Gate 5B PASSES

#### Visual

Show sanitized evidence of:

- AgentCore Runtime deployed/ready,
- remote invocation,
- returned tool trace.

#### Narration

> We also deployed the Strands agent to Amazon Bedrock AgentCore Runtime. A live remote invocation returns an auditable tool trace through the same outcome-loop operations, while the MCP server remains the Alexa+-compatible transport surface.

### Variant B — if Gate 5B is still blocked

#### Visual

Show the architecture diagram or AgentCore code/config, **not** a fake deployment screen.

#### Narration

> The repository also includes the Strands and Amazon Bedrock AgentCore runtime path, but live AWS deployment is intentionally not claimed here because account-level verification is still blocking that evidence gate. The Alexa+ primary demo and Streamable HTTP MCP implementation remain independently working and testable.

---

## 2:42–2:52 — Close

### Visual

Return to **Verified resolved**.

### Narration

> Alexa+ Home-Repair Outcome Loop: don't stop when the tool says done. Stop when the outcome is verified.

---

# Recording checklist

- [ ] Total final cut is below 3:00.
- [ ] Simulator disclosure is readable.
- [ ] User request is visible.
- [ ] False-closure moment is obvious.
- [ ] Reopen/escalation is visible.
- [ ] Verified-resolved state is visible.
- [ ] MCP / Streamable HTTP proof is visible.
- [ ] CI proof is visible.
- [ ] No secrets, account IDs, case IDs, emails, or credentials appear.
- [ ] AWS Variant A is used only after Gate 5B passes.
- [ ] Video is public on YouTube or Vimeo.
- [ ] Video language is English.

# Suggested title

**Alexa+ Home-Repair Outcome Loop — Amazon Developer Hackathon 2026**

# Suggested video description

A simulated Alexa+ experience backed by a real Streamable HTTP MCP implementation. The agent coordinates a home-repair workflow but refuses to declare success until observable outcome evidence confirms the problem is actually resolved.

Source code and reproducible instructions are available in the public project repository.
