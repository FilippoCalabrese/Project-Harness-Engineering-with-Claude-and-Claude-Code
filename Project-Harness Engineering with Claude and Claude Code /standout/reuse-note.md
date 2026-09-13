# Stand-out 4 — Mapping a system to a new use case

**Scenario: an IT support-desk triage agent.** Engineers file free-text incidents ("VPN drops
every ~10 min after the latest client update"). The agent must gather facts, classify the
incident (network / auth / hardware / software), assess severity against SLA, and either route to
the right on-call queue or escalate to a human when it can't decide.

## Which system I'd reuse: System 1 (Claims Intake), almost verbatim

The claims-intake shape is a near-exact structural match, so I'd reuse **System 1** as the base:

- The `stop_reason`-driven loop in `../../Build a Claims Intake Agent with a stop_reason-Driven Loop/exercises/03-dynamic-decomposition/solution/claims_intake/loop.py`
  is domain-agnostic — it dispatches on `tool_use` / `end_turn` / else with no claims-specific
  logic, proven by `test_no_claim_type_equality_branching_in_package` in the anti-pattern suite
  (`../evidence/system-1-claims/pytest.log`, 29 passed). Nothing in the loop needs to change.
- The tool contract maps 1:1: `lookup_policy` -> `lookup_asset/service`, `record_claim_fact` ->
  `record_incident_fact`, `classify_claim` -> `classify_incident`, `assess_severity` ->
  `assess_severity` (SLA buckets), `request_clarification` stays, and the two terminal tools
  `route_to_adjuster` / `escalate_to_human` become `route_to_oncall` / `escalate_to_human`.
- The **confidence >= 0.6 else escalate** contract in `claims_intake/system_prompt.py` is exactly
  the behavior I want, and stand-out 2 (`break-on-purpose.md`) already proved it degrades
  gracefully on genuine ambiguity (escalated at confidence 0.45) — critical for a support desk
  where a wrong route wastes an on-call engineer's night.

## What I'd borrow from the other three

- **System 4's tiered state** (`shift_monitor/warm.py` `defects_since()` + the 661-byte
  `hot_state.json`) for the *cross-incident* layer: a warm SQLite store of historical incidents,
  queried by an indexed `incidents_since()` so the agent sees only the relevant recent slice, never
  the whole history — the same "push work down to SQL" pattern I cited in reflection-brief Q11.
- **System 2's pruning** (`retail_context/pruner.py`, "keep exactly the contracted set") for the
  verbose monitoring/log payloads a support incident drags in — trim a 57-field telemetry blob to
  the handful of fields the routing decision needs before it ever hits the prompt.
- **System 3's forked, read-only skill** (`context: fork` + read-only `allowed-tools` in
  `../evidence/system-3-claude-code/config_snippets.txt`) for a "diagnose" sub-agent that can grep
  logs and run `kubectl get`-style read commands without any power to restart services.

## What I would *not* reuse

System 2's LLM segment summarization is overkill here — support incidents are short-lived, so
cross-session compression matters more than intra-conversation compression. I'd keep System 4's
external tiered store and skip System 2's in-prompt summarizer for this use case.
