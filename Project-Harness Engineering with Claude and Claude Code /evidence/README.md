# Capstone Evidence — Harness Engineering

Built, run, and verified on macOS (darwin 25.6.0), Python 3.12.3, one `.venv` per system.
API traffic routed through the Vocareum gateway (`ANTHROPIC_BASE_URL=https://claude.vocareum.com`).

## Test totals — 127 passing (29 + 30 + 35 + 33)

| System | Tests | Run artifact(s) | Key result |
|--------|-------|-----------------|------------|
| 1 Claims Intake | 29 passed (`system-1-claims/pytest.log`) | `summary.md`, `traces/`, `queues/` | 4 routed / 4 incomplete on `claude-sonnet-4-6`, $0.4321 |
| 2 Retail Context | 30 passed (`system-2-retail/pytest.log`) | `budget.json`, `eval.jsonl`, `eval_control.jsonl`, `context.md` | 56.46% reduction, eval 6/6, control Q6 regressed |
| 3 Claude Code Config | 35 passed (`system-3-claude-code/pytest.log`) | `validator_stdout.log`, `claude_tree.txt`, `config_snippets.txt` | validator `OK`, exit 0 |
| 4 Multi-Shift Orchestration | 33 passed (`system-4-shift/pytest.log`) | `shift_stdout.log`, `hot_state.json`, `shift_scratchpad.jsonl`, `metrics.txt` | 1 defect returned vs 40 warm total, hot_state 661 B |

## Environment fixes applied (see brief Q19)

- System 1 (`anthropic==0.39.0`): pinned `httpx<0.28` (installed 0.27.2) to resolve
  `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`.
- All API systems: set `ANTHROPIC_BASE_URL=https://claude.vocareum.com` so the `voc-` key
  does not 401 against `api.anthropic.com`.

The completed reflection brief is at `../reflection-brief.md`.
