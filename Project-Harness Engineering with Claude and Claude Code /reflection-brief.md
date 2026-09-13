# Reflection Brief — Harness Engineering Capstone

**Name:** Filippo Calabrese
**Date:** 2026-09-13

Replace each `→` with your answer. **Every answer cites at least one artifact from your own runs** — a run ID, file path, token count, claim outcome, or test count. Uncited answers do not pass. 3–6 sentences each unless noted. Paste short artifact snippets where they help.

**Environment**

- Model(s): `claude-sonnet-4-6` (System 1 primary run) and `claude-haiku-4-5-20251001` (System 1 first run + System 2 default); System 3 needs no API; System 4 ran offline against a recorded response. All API traffic routed through the Vocareum gateway (`ANTHROPIC_BASE_URL=https://claude.vocareum.com`).
- OS / Python: macOS (darwin 25.6.0); Python 3.12.3 in a separate `.venv` per system (`anthropic==0.39.0` for System 1 vs `0.69.0` for System 2, so they cannot share an env).
- Approx. API spend: ~$0.75 total (System 1: $0.1103 haiku + $0.4321 sonnet per `evidence/system-1-claims/summary.md`; System 2: ~$0.20; smoke tests negligible).

---

## Part 1 — Per-system

### System 1 — Agentic loop

1. **Loop control.** Quote the `stop_reason` sequence from one trace. Name the file and function that decides continue-vs-stop, and how.
   → From `evidence/system-1-claims/traces/claim_04_neighbor_injury.routed.jsonl` the per-turn `stop_reason` sequence is `tool_use → tool_use → tool_use → tool_use → end_turn` (turns 1–5). The decision lives in `run()` in `claims_intake/loop.py`: it runs a `while True:` and branches purely on `response.stop_reason` — it appends the assistant turn and `continue`s on `"tool_use"`, returns a `FinalState` on `"end_turn"`, and raises `UnexpectedStopReason` on anything else. No assistant text or turn counter is consulted; `stop_reason` is the only control signal crossing the model/harness boundary.

2. **Anti-pattern.** Name one anti-pattern `test_antipatterns.py` checks for. What would break in your run if the loop used it?
   → `test_no_integer_literal_iteration_cap_in_loop` forbids a `while turn < N` / `for _ in range(N)` cap as the stopping mechanism (only a config-sourced `Budget` is allowed). In my sonnet run `claim_05_auto_collision` took 6 turns and `claim_02_stolen_bike` took 6 (`evidence/system-1-claims/summary.md`); a hardcoded cap of, say, 5 would have truncated those two mid-claim *before* `route_to_adjuster` fired, silently converting successful routes into incompletes. The companion `test_no_string_membership_against_text_in_loop` would likewise break control flow if the loop keyed off prose like `"done" in text`.

3. **Tool design.** Pick two tools with overlapping inputs. How do the descriptions prevent misrouting? What did a structured tool error let the agent do that a generic string would not?
   → `route_to_adjuster` and `escalate_to_human` (in `claims_intake/tools.py`) both terminate the claim and both take a summary field, so they overlap. Their descriptions both start `TERMINAL TOOL.` but give mutually exclusive triggers — route when "classification confidence is at least 0.6", escalate when "confidence is below 0.6 even after clarification" — which keeps the model from firing both. Structured errors follow `{"is_error": true, "error_category": ..., "is_retryable": ..., "message": ...}`; e.g. `route_to_adjuster` returns a `permanent`, non-retryable error `"classify_claim must be called before routing"` if prerequisites are missing, so the agent can self-correct by calling the missing tool rather than blindly retrying an opaque string.

4. **Your numbers.** Quote the turn count and cost for one claim. How does it differ from the README sample, and why?
   → `claim_04_neighbor_injury` routed to the `liability` queue at `high` severity in `turns=5`, `input_tokens=19057 / output_tokens=1109`, `est_cost_usd=$0.0738` (`evidence/system-1-claims/summary.md`, run `20260913_113120`). My per-claim cost is much higher than the README's haiku sample because I ran the primary pass on `claude-sonnet-4-6` ($3/$15 per Mtok in `pricing.py`) vs haiku ($1/$5); my earlier haiku run of the same fixture cost only ~$0.02. Turn counts also differ run-to-run because the model chooses how many `record_claim_fact` calls to batch per turn — the README explicitly notes outcomes vary by model and input.

### System 2 — Context strategy

5. **The reduction.** From `budget.json`: baseline tokens, assembled tokens, reduction %. Which section dominates the assembled context, and why keep it verbatim?
   → `evidence/system-2-retail/budget.json` (run `20260913-113537`): `baseline_tokens: 38708`, `assembled_tokens: 16855`, `reduction_pct: 56.46`. The `active` section dominates at `15789` of `16855` assembled tokens (~94%). It is the still-open payment-method-update issue, so it is kept byte-exact — the copilot needs the customer's exact wording, the `AVS_MISMATCH` failure code, and card last-4 (`7782`) to continue the live thread without losing detail.

6. **Summarize vs preserve.** State the rule for what gets summarized vs kept byte-exact, citing your per-section token numbers.
   → Rule: resolved/closed segments are LLM-summarized; the active/in-flight segment is preserved verbatim. In `budget.json`, `resolved_refund` was compressed to `358` tokens and `resolved_subscription` to `522` tokens — from `compression_api` inputs of `12334` and `11475` tokens respectively, i.e. ~30–34x shrink each. Meanwhile `active` stays at `15789` tokens uncompressed, and the durable `case_facts` block is a tiny `204`-token structured header that survives regardless of which segments get summarized.

7. **Facts block.** Compare `eval.jsonl` to `eval_control.jsonl`. Which question regressed, and what does that prove?
   → `evidence/system-2-retail/eval.jsonl` shows 6/6 passed with the case-facts block present. In `evidence/system-2-retail/eval_control.jsonl` (case-facts stripped), **Q6** regressed to FAIL as expected — it asks for "the exact status token from the case record", and only the structured facts block carries `payment_update_status: in_progress`. Q1 (the `$22.14` refund amount) unexpectedly still passed in the control because that number also appears in the retained active/resolved prose. This proves the facts block is load-bearing specifically for exact structured tokens that don't survive summarization, even though some free-text facts leak through other sections.

### System 3 — Claude Code config

8. **Path-scoped rules.** Quote the glob frontmatter from one rule file. Why is it better than a directory-level CLAUDE.md for cross-cutting conventions?
   → From `evidence/system-3-claude-code/config_snippets.txt`, `.claude/rules/tests.md` declares:

   ```yaml
   paths:
     - "**/*.test.tsx"
     - "**/*.test.ts"
   ```

   A single glob rule activates for co-located test files *anywhere* in the monorepo — under both `src/components/**` and `src/api/**` — whereas a directory-level `CLAUDE.md` would force you to duplicate the same testing conventions into every directory that happens to hold tests, and they'd drift out of sync. `.claude/rules/api.md` scopes narrowly with `paths: ["src/api/**/*"]`, so API conventions never leak into React edits.

9. **Forked skill.** Quote the `context: fork` and `allowed-tools` lines. What does running forked + read-only buy you? What breaks without it?
   → From `evidence/system-3-claude-code/config_snippets.txt`, `.claude/skills/deploy-check/SKILL.md` sets `context: fork` and an `allowed-tools:` list of read-only entries (`Read`, `Grep`, `Glob`, `Bash(git status:*)`, `Bash(git diff:*)`, `Bash(git log:*)`, `Bash(git rev-parse:*)`, `Bash(git ls-files:*)`, `Bash(gh pr view:*)`). Forked + read-only buys isolation and safety: the pre-deploy validation runs in a sub-agent whose verbose output never pollutes the main session's context, and the allowlist makes it structurally incapable of writing files or triggering a deploy. Without `context: fork` the check's output balloons the main context; without the read-only allowlist a "check" could mutate the repo or actually push.

10. **Scope.** From the validator output: project-level vs user-level scope. Give one example of each from this config.
    → The validator prints `OK` / exit 0 (`evidence/system-3-claude-code/validator_stdout.log`) after checking the project-level `.claude/` hierarchy committed to the repo — `claude_tree.txt` shows `.claude/rules/`, `.claude/commands/review.md`, and `.claude/skills/deploy-check/SKILL.md`, all project-scoped (shared with the whole team via version control). A user-level example is a personal `~/.claude/CLAUDE.md` — the same instruction location but scoped to one engineer's machine and not validated by `python -m ecommerce_team_config .`, which only walks the project tree.

### System 4 — Orchestration

11. **Push work down.** Defects the SQL query returned vs warm-tier total. Name the indexed query. Why does the model never see the full history?
    → The indexed query is `WarmStore.defects_since()` in `shift_monitor/warm.py` — `SELECT * FROM defects WHERE ts > ? ORDER BY ts DESC LIMIT ?`, backed by `CREATE INDEX idx_defects_ts ON defects(ts)`. My run (`evidence/system-4-shift/`) returned `new=1` defect for the `--since 2026-04-29T00:00:00Z` window (`shift_stdout.log`) out of `40` total rows in the warm tier (`metrics.txt`). The model never sees the full history because filtering is done SQL-side ("no Python-side filtering of severity, component, or time"); only the tiny since-window slice is lifted into the session prompt.

12. **Crash recovery.** The resume-vs-fresh decision and its staleness threshold (`recovery.py`). Why is a fresh start with an injected summary sometimes more reliable than resuming?
    → `recovery.decide()` uses `STALE_RESUME_THRESHOLD_MINUTES = 30`: with no steps or a completed manifest it returns `"fresh"`; if the last step's timestamp is within 30 minutes of `now` it returns `"resume"`, otherwise `"fresh"` (`shift_monitor/recovery.py`, confirmed by `test_threshold_constant_is_30_minutes` in `evidence/system-4-shift/pytest.log`). A stale partial (older than 30 min, ~1/16 of the 8-hour cycle) may reference tool state or a defect set that has since changed, so replaying it risks acting on inconsistent mid-flight assumptions; restarting fresh but injecting the manifest's captured findings as a summary preserves the useful conclusions while dropping the brittle in-progress state.

13. **Small state.** Byte size of your `hot_state.json`. Why does the budget matter for a system run once per shift, indefinitely?
    → `evidence/system-4-shift/hot_state.json` is `661` bytes (`metrics.txt`), well under the ~5 KB budget. It carries only `recent_defect_hashes`, a one-paragraph `current_shift_summary`, a short `active_alerts` list, and `threshold_statuses`. The budget matters because the orchestrator runs once per shift forever: if hot state accreted a little each shift, after months every session would load a bloated, ever-growing prompt, driving up cost and latency and eventually blowing the context window — capping it keeps each of the indefinite future invocations equally cheap and tractable.

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.
    → Model: `claims_intake/system_prompt.py` + the `classify_claim` tool calls visible in `evidence/system-1-claims/traces/claim_04_neighbor_injury.routed.jsonl` — the LLM owns the domain judgment (claim type, severity, confidence).
    → Harness: `run()` in `claims_intake/loop.py` — the deterministic `stop_reason`-driven loop that turns model decisions into tool executions, proven by the 29 passing tests in `evidence/system-1-claims/pytest.log`.
    → Orchestration: `shift_monitor` `run-shift` pipeline with tiered hot/warm state — `evidence/system-4-shift/shift_stdout.log` (`run_shift start/done`) plus the 661-byte `hot_state.json` — coordinating one bounded invocation per 8-hour shift.

15. **Deterministic vs prompt.** Cite one behavior guaranteed in code (terminal tool, read-only allowlist, atomic write, byte budget) and one guided by prompt. When is each right?
    → Guaranteed in code: `route_to_adjuster` in `claims_intake/tools.py` returns a `permanent` error unless `classify_claim` *and* `assess_severity` ran first, and a `terminal_called` guard blocks a second terminal call — invariants that must never depend on model whim. Guided by prompt: *which* severity bucket to pick is left to the model via the dollar-range rules in `system_prompt.py`, reflected in the `high` severity chosen for `claim_04` in `evidence/system-1-claims/summary.md`. Code enforcement is right for safety/ordering invariants; prompt guidance is right for open-ended judgment that can't be exhaustively enumerated.

16. **Context, two faces.** Compare context management in System 2 (intra-session) and System 4 (cross-session) with cited numbers from both. Same principle, different mechanism — how?
    → System 2 manages context *within one 48-turn conversation*: it compresses `38708 → 16855` tokens (56.46%, `evidence/system-2-retail/budget.json`) by summarizing resolved segments while keeping the active one verbatim. System 4 manages context *across shifts*: `hot_state.json` holds just `661` bytes (`evidence/system-4-shift/metrics.txt`) while `40` defects sit in the warm SQLite tier, fetched on demand via `defects_since()`. Same principle — keep the live working set tiny and push everything else to retrievable storage — realized by two mechanisms: in-prompt LLM summarization (System 2) vs an external tiered store with an indexed query (System 4).

17. **Reliability you can't see in one run.** Name one behavior a test guarantees that a single successful run would not reveal. Why does it matter before shipping?
    → `test_antipatterns.py` (part of the 29 in `evidence/system-1-claims/pytest.log`) statically guarantees the loop never drives control flow via string-membership on assistant text or an integer iteration cap. A single green run — even my clean `claim_04` route — can't reveal this: the loop could "work" by accident on these fixtures while being one prose change away from breaking. Before shipping this matters because production inputs vary far more than eight fixtures, and a text-keyed loop would fail silently on the first unexpected phrasing. (System 4's `test_two_forks_produce_independent_scratchpads` similarly guarantees fork isolation that a single non-forked run never exercises.)

18. **Blast radius.** Pick one system. What's the blast radius if it misbehaves, and what's the kill switch? Ground it in that system's tools, enforcement points, and state.
    → System 1. The blast radius is bounded by its seven tools (`claims_intake/tools.py`): the only side effects are appending to `queues/*.jsonl` and `escalations.jsonl` inside the per-run `run_dir` — no tool deletes data or calls an external system, and the `terminal_called` guard prevents double-routing a claim. The kill switch is the `Budget` (token + wall-clock, `max_wall_clock_s=180`) which raises `BudgetExceeded` instead of looping forever, plus `UnexpectedStopReason` which halts loudly on any unplanned `stop_reason`. State is a per-claim `ClaimSession`, so a misbehaving claim can't corrupt its neighbors — and the orchestrator's completion guard (see Q20) now guarantees each claim independently reaches a terminal state (`evidence/system-1-claims/summary.md`: 8/8 terminal).

---

## Part 3 — Honest assessment

19. **What broke.** One thing that failed first try in your environment, and how you fixed it. (If nothing, what you checked to be sure.)
    → System 1's first live run crashed instantly with `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`. Root cause: `anthropic==0.39.0` passes a `proxies` kwarg that the freshly-installed `httpx 0.28.1` removed. I fixed it by pinning `httpx<0.28` (resolved to `0.27.2`) in that venv, after which the run completed. I also had to `export ANTHROPIC_BASE_URL=https://claude.vocareum.com` — without it the `voc-` key is sent to `api.anthropic.com` and 401s. Separately, haiku left 4/8 claims `incomplete` (`summary.md`); switching to `claude-sonnet-4-6` raised it to 4 routed but still left 4 incomplete, confirming that is genuine model behavior (the model ends its turn in prose instead of calling a terminal tool), not a harness bug — the 29 tests including the anti-pattern suite still pass. I subsequently addressed this at the harness level (see Q20): after strengthening the terminal-action mandate and adding an orchestrator completion guard in `run.py`, the full `--all` sonnet run now terminates 8/8 with 0 incomplete.

20. **What you'd change.** One architectural decision you'd make differently, grounded in what you observed — and what I then implemented.
    → Originally the harness let the model reach `end_turn` without ever calling a terminal tool, which showed up as `incomplete` outcomes for `claim_01`, `claim_03`, `claim_06`, and `claim_07` (`claim_06` was even *expected to escalate*). I made two changes. (1) I strengthened the terminal-action mandate so it is an explicit precondition for ending the turn — in `claims_intake/system_prompt.py` (step 6/7 plus a hard "never end your turn without a terminal tool call" constraint) and in both terminal tool descriptions in `claims_intake/tools.py`. (2) Because prompt tightening alone only recovered `claim_03` (the other three still stalled), I added the harness-level completion guard sketched here, in the orchestrator `claims_intake/run.py` — leaving the generic `loop.py` purely `stop_reason`-driven. On `end_turn` when `session.terminal_called` is False, it injects a one-line reminder and re-prompts once; if the model still declines, it deterministically synthesizes an `escalate_to_human` call so no claim is ever left incomplete. After the fix, individual re-runs give `claim_01`→routed, `claim_03`→routed, `claim_06`→escalated, `claim_07`→routed, and a full `--all` run on `claude-sonnet-4-6` terminates 8/8 with 0 incomplete (`evidence/system-1-claims/summary.md`, `run_stdout.log`); the 29 tests including the anti-pattern suite still pass (`pytest.log`).
