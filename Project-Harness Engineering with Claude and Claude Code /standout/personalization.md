# Stand-out 5 — Personalizing a system for a vertical

**Vertical: medical / professional-liability (malpractice) claims intake.** I re-frame System 1
(`../../Build a Claims Intake Agent with a stop_reason-Driven Loop/exercises/03-dynamic-decomposition/solution`)
for a medical-liability insurer. The `stop_reason`-driven loop (`claims_intake/loop.py`) stays
untouched — it is domain-agnostic — but the tool set, context strategy, and state design change.

## Tool set

Starting from the seven tools in `claims_intake/tools.py`:

- **`lookup_policy` -> `lookup_provider_coverage`.** Returns the clinician's malpractice policy,
  covered procedures, retroactive date, and tail coverage — not homeowner coverage.
- **`classify_claim` enum changes.** The four property types (`property_damage / theft / liability /
  auto`) become clinical incident types: `diagnostic_error / surgical_complication /
  medication_error / consent_documentation`. Because the anti-pattern suite forbids branching on
  the type in Python (`test_no_claim_type_equality_branching_in_package`,
  `../evidence/system-1-claims/pytest.log`), swapping the enum in the schema + prompt is the *only*
  change needed — the harness never hard-codes the categories.
- **New tool `check_statute_of_limitations`.** Med-mal is dominated by filing deadlines; a
  deterministic date-math tool (like System 4's `python-dateutil` usage) gates whether a claim is
  even actionable before classification.
- **`assess_severity` reworked** around injury severity (NAIC-style) and reserve estimate rather
  than dollar-damage buckets.
- **Terminal tools gain a compliance branch.** Alongside `route_to_adjuster` /
  `escalate_to_human`, add `flag_for_peer_review` — some incidents must go to a clinical peer
  panel, not a claims adjuster.

## Context strategy

Med-mal records are far larger than a homeowner claim (full medical charts, imaging reports). I'd
adopt **System 2's deterministic pruning** (`retail_context/pruner.py`, "keep exactly the
contracted set") to trim a chart to the decision-relevant fields, and **System 2's summarize-vs-
preserve rule** (`../evidence/system-2-retail/budget.json`: resolved segments compressed to
358/522 tokens, active kept verbatim at 15789) so that closed prior encounters are summarized while
the *index incident* narrative stays byte-exact — clinical wording is legally load-bearing and
cannot be paraphrased.

## State design

- **PHI-aware state.** The case-facts block (System 2's 12-field durable block) becomes a
  structured, access-logged record; unlike the current in-memory `ClaimSession`, med-mal state must
  be encrypted at rest and carry an audit trail of every read.
- **Tiered store with legal-hold semantics.** Reuse System 4's warm SQLite tier
  (`shift_monitor/warm.py`) but records are immutable and subject to legal hold — no
  `INSERT OR REPLACE` overwrite; corrections are append-only versions, preserving the full history
  a deposition may require.
- **The byte budget still applies.** The current `hot_state.json` is 661 B
  (`../evidence/system-4-shift/hot_state.json`); the med-mal hot state stays small (open-incident
  pointers + deadlines), with the heavy chart data pushed to the audited warm/cold tiers and pulled
  only via indexed, logged queries.

## What stays exactly the same

The three invariants that make the harness trustworthy carry over unchanged: the loop terminates
only on `end_turn` and raises on unexpected `stop_reason`; terminal tools are guarded so a claim
can't be double-routed (`session.terminal_called` in `tools.py`); and the Budget (token +
wall-clock) is the kill switch. Those are vertical-independent safety properties.
