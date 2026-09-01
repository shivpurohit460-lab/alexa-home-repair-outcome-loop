# Architecture v0.1

## Product invariant

**A workflow is not closed merely because an external actor or API reports success.**

The system distinguishes two state planes:

1. **Workflow state** — booked, in progress, provider complete.
2. **Outcome state** — observable evidence of whether the user's goal has been achieved.

Closure requires the relevant evidence from both planes.

## MVP sequence

```text
create_repair_case
        |
        v
book_home_service
        |
        v
get_service_status -----------+
                              |
read_home_state --------------+--> verify_outcome
                                      |
                   +------------------+------------------+
                   |                                     |
                verified                            not verified
                   |                                     |
             close case                     reopen_or_escalate_case
```

## Why deterministic simulators first

The hackathon allows a simulated Alexa+ experience. The simulator boundary lets us prove the agentic lifecycle without pretending to have partner-only Home Services access. It also makes the judging demo reproducible.

## Planned AWS layer

- Strands Agents SDK
- Amazon Bedrock model provider
- Bedrock AgentCore Runtime
- AgentCore state/session adapter after local workflow validation

## Security principles

- no hard-coded credentials
- no secret values in repository
- least-privilege AWS role during deployment
- simulator data clearly labeled as synthetic
- explicit postcondition verification before closure
- no agent action outside the six-tool contract in MVP v0.1
