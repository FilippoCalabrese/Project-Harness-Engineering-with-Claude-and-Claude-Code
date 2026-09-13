# Capstone Evidence — Harness Engineering

Built, run, and verified on macOS (darwin 25.6.0), Python 3.12.3, one `.venv` per system.
API traffic routed through the Vocareum gateway (`ANTHROPIC_BASE_URL=https://claude.vocareum.com`).

## Test totals — 127 passing (29 + 30 + 35 + 33)

| System | Tests | Run artifact(s) | Key result |
|--------|-------|-----------------|------------|
| 1 Claims Intake | 29 passed (`system-1-claims/pytest.log`) | `summary.md`, `traces/`, `queues/` | 8/8 terminal (all routed) on `claude-sonnet-4-6`, 0 incomplete, $0.7256 (post-fix; see brief Q20) |
| 2 Retail Context | 30 passed (`system-2-retail/pytest.log`) | `budget.json`, `eval.jsonl`, `eval_control.jsonl`, `context.md` | 56.46% reduction, eval 6/6, control Q6 regressed |
| 3 Claude Code Config | 35 passed (`system-3-claude-code/pytest.log`) | `validator_stdout.log`, `claude_tree.txt`, `config_snippets.txt` | validator `OK`, exit 0 |
| 4 Multi-Shift Orchestration | 33 passed (`system-4-shift/pytest.log`) | `shift_stdout.log`, `hot_state.json`, `shift_scratchpad.jsonl`, `metrics.txt` | 1 defect returned vs 40 warm total, hot_state 661 B |

## Reading the System 1 traces (post-fix run of record `20260913_131144`)

The orchestrator completion guard (brief Q20, `claims_intake/run.py`) can run a claim
in **two `run_loop` sessions**: if the model reaches `end_turn` without a terminal tool
call, the guard injects a one-line reminder and re-prompts once. Because the turn counter
is **per-session**, an affected trace shows the turn number **restart**.

- `traces/claim_01_kitchen_fire.jsonl` is the clearest example: session 1 is
  `turn 1 tool_use (lookup_policy, record_claim_fact) → turn 2 tool_use (record_claim_fact ×5) → turn 3 end_turn`
  with **no** terminal call; the guard fires, and session 2 restarts at
  `turn 1 classify_claim → turn 2 assess_severity → turn 3 route_to_adjuster → turn 4 end_turn`.
  So the turn-number restart is **intended behaviour**, not a logging bug; `summary.md`
  reports `turns=4` (the final, terminal session). The reminder alone recovered this claim,
  so the deterministic fallback escalation was not needed.
- `claim_06_low_confidence_escalation` is a single session here: its fixture is *designed*
  to escalate, but in this run of record sonnet classified with confidence ≥ 0.6 and
  **routed** it (`property_damage`/high) rather than escalating. That is genuine model
  judgment on a borderline claim (an individual `--fixture` re-run of the same case did
  escalate). The `expected=` field printed by `run.py` is informational and **not asserted
  by any test**; the guard guarantees a terminal outcome either way. See brief Q20.

## Environment fixes applied (see brief Q19)

- System 1 (`anthropic==0.39.0`): pinned `httpx<0.28` (installed 0.27.2) to resolve
  `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`.
- All API systems: set `ANTHROPIC_BASE_URL=https://claude.vocareum.com` so the `voc-` key
  does not 401 against `api.anthropic.com`.

The completed reflection brief is at `../reflection-brief.md`.
