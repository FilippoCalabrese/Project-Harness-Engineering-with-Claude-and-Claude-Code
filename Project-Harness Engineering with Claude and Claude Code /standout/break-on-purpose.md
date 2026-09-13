# Stand-out 2 — Break a system on purpose (System 1, deliberately ambiguous claim)

I fed System 1 a claim engineered to be unresolvable and watched how it degrades.
Artifacts in `break-on-purpose/`: `fixture.json`, `trace.jsonl`, `summary.md`, `escalations.jsonl`,
`run_stdout.log`. Run `20260913_114932`, model `claude-sonnet-4-6`.

## The trap

`fixture.json` (`claim_99_ambiguous_standout`) describes water damage along a **shared wall**
whose origin is genuinely unknowable — it could be the policyholder's own pipes (`property_damage`)
or the neighbor's leak (`liability`). Critically, `clarification_responses` is `{}`, so any
`request_clarification` call comes back as `NO_RESPONSE`: the claimant cannot break the tie.

## What happened (graceful degradation, not a crash)

From `trace.jsonl` the `stop_reason` sequence is `tool_use x4 -> end_turn`, and the tool path is:

1. **turn 1** — `lookup_policy` + `record_claim_fact` (location, description noting "source unknown").
2. **turn 2** — `request_clarification` with `ambiguity_between: ["property_damage", "liability"]`.
   The tool returns `NO_RESPONSE` (empty `clarification_responses`).
3. **turn 3** — records `leak_source: "Unknown ..."` instead of inventing a source.
4. **turn 4** — `escalate_to_human` with `reason: "unresolved_ambiguity"`, `confidence: 0.45`,
   `candidate_claim_types: ["property_damage", "liability"]`, and a `recommended_action` to get a
   plumber/adjuster inspection before routing.
5. **turn 5** — `end_turn`.

Outcome (`summary.md`): `escalated`, `turns=5`, `clarifications_asked=1`, `est $0.0704`.

## Why this is the *right* failure mode

The system prompt's contract (`claims_intake/system_prompt.py`) says route only when
classification `confidence >= 0.6`, otherwise escalate. Here confidence landed at **0.45**, below
the bar, so the agent escalated rather than guessing a queue. Three design properties held under stress:

- **It did not hallucinate a source.** It recorded `leak_source: "Unknown"` and carried the
  ambiguity forward instead of fabricating facts (the prompt's "Do not invent facts" rule).
- **It asked exactly once, then stopped asking.** The `NO_RESPONSE` handling prevented a
  re-ask loop; the agent committed to escalation instead.
- **The escalation is structured, not a shrug.** `escalations.jsonl` carries `root_cause`,
  both `candidate_claim_types`, the full `case_facts`, and a concrete `recommended_action` — a
  human reviewer gets everything needed to resolve it. A generic text refusal would not.

## Contrast with System 2's control break

The System 2 control (`../evidence/system-2-retail/eval_control.jsonl`) is the complementary
break: stripping the case-facts block regresses Q6 (exact `payment_update_status` token). Together
they show both failure surfaces — missing *input certainty* (System 1) degrades to escalation;
missing *context* (System 2) degrades to a wrong/absent answer.

## Note

`fixture.json` was also added to the solution at
`fixtures/claims/claim_99_ambiguous_standout.json` (data only, clearly named, reversible). Because
the runner loads `claim_*.json`, this file *will* be included in future `--all` runs (9 fixtures
instead of 8) — delete it to reproduce the original 8-fixture graded run
(`../evidence/system-1-claims/summary.md`, run `20260913_113120`) exactly.
