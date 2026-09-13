# Stand-out 1 — Same system, two models (System 1)

System 1 (Insurance Claims Intake) run against the same 8 fixtures on two models via the
Vocareum gateway. Raw artifacts: `model-comparison/summary_haiku.md` (run `20260913_112904`)
and `model-comparison/summary_sonnet.md` (run `20260913_113120`, also in
`../evidence/system-1-claims/summary.md`).

## Per-claim comparison

| claim_id | haiku outcome | haiku turns | haiku $ | sonnet-4-6 outcome | sonnet turns | sonnet $ |
|----------|---------------|-------------|---------|--------------------|--------------|----------|
| claim_01_kitchen_fire | incomplete | 2 | 0.0089 | incomplete | 2 | 0.0245 |
| claim_02_stolen_bike | incomplete | 2 | 0.0084 | **routed** (theft/low) | 6 | 0.0787 |
| claim_03_water_damage | incomplete | 3 | 0.0112 | incomplete | 3 | 0.0354 |
| claim_04_neighbor_injury | routed (liability/high) | 5 | 0.0219 | routed (liability/high) | 5 | 0.0738 |
| claim_05_auto_collision | routed (auto/high) | 4 | 0.0203 | routed (auto/high) | 6 | 0.0827 |
| claim_06_low_confidence_escalation | incomplete | 3 | 0.0124 | incomplete | 3 | 0.0416 |
| claim_07_tree_falls_on_car | incomplete | 2 | 0.0084 | incomplete | 2 | 0.0255 |
| claim_08_minor_porch_damage | routed (property_damage/low) | 4 | 0.0187 | routed (property_damage/low) | 5 | 0.0698 |

## Aggregates

| Metric | claude-haiku-4-5-20251001 | claude-sonnet-4-6 |
|--------|---------------------------|-------------------|
| Routed | 3 / 8 | 4 / 8 |
| Escalated | 0 / 8 | 0 / 8 |
| Incomplete | 5 / 8 | 4 / 8 |
| Total est. cost | $0.1103 | $0.4321 |
| Cost multiple | 1x | ~3.9x |
| Avg turns (routed claims) | 4.3 | 5.5 |

## Where the stronger model changes routing behavior

- **The decisive difference is `claim_02_stolen_bike`.** Haiku ended the turn early (`incomplete`, 2 turns); sonnet-4-6 worked the full tool sequence over 6 turns and routed it to the `theft` queue at `low` severity. This is the only claim whose *outcome* flipped between models — the stronger model followed the multi-step `record_claim_fact -> classify_claim -> assess_severity -> route_to_adjuster` contract to completion where haiku stopped short.
- **Where both routed, sonnet spent more turns and tokens.** `claim_05_auto_collision` went 4 turns (haiku) vs 6 (sonnet); `claim_08` 4 vs 5. Sonnet batches fewer `record_claim_fact` calls per turn and reasons more per step, which raises both turn count and cost.
- **Neither model escalated `claim_06_low_confidence_escalation`.** Both left it `incomplete` rather than calling `escalate_to_human` — the expected-escalation path is the shared weak spot, addressed in stand-out 2 and in reflection-brief Q20 (a harness-level completion guard).
- **Cost vs. yield.** Sonnet cost ~3.9x more ($0.4321 vs $0.1103) to convert exactly one extra claim from incomplete to routed. For this fixture set the harness is model-agnostic and correct on both (the 29 tests pass regardless); the model choice is a cost/completion-rate tradeoff, not a correctness one.
