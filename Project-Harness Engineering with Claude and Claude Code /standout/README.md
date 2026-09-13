# Stand-out extras — Harness Engineering Capstone

Five enrichment activities on top of the graded capstone, each grounded in real artifacts from my
own runs. The graded deliverable is `../reflection-brief.md`; these are extra credit.

| # | Activity | Write-up | Key artifacts | API spend |
|---|----------|----------|---------------|-----------|
| 1 | Same system, two models (System 1: haiku vs sonnet-4-6) | `model-comparison.md` | `model-comparison/summary_haiku.md`, `summary_sonnet.md` | $0 (reused runs) |
| 2 | Break a system on purpose (System 1: unresolvable ambiguous claim) | `break-on-purpose.md` | `break-on-purpose/{fixture,trace,summary,escalations}.*` | ~$0.07 |
| 3 | Fork path end-to-end (System 4: 2 competing hypotheses) | `fork-demo.md` | `fork-demo/run_fork_demo.py`, `fork-demo/stdout.log`, `fork-demo/work/` | $0 (offline) |
| 4 | Map a system to a new use case (IT support triage) | `reuse-note.md` | written analysis | $0 |
| 5 | Personalize for a vertical (medical-liability claims) | `personalization.md` | written analysis | $0 |

## Headline results

- **ST1** — Only `claim_02_stolen_bike` flipped outcome (incomplete -> routed) going haiku ->
  sonnet-4-6; sonnet cost ~3.9x ($0.4321 vs $0.1103) for one extra routed claim.
- **ST2** — The deliberately ambiguous shared-wall water claim escalated at `confidence: 0.45`
  after one `request_clarification` returned `NO_RESPONSE` — graceful degradation, no hallucinated
  source (`break-on-purpose/trace.jsonl`).
- **ST3** — Two forks stayed fully isolated (`isolation_ok=True`), each got its own baseline copy,
  and `merge_findings` reconciled both into the main stream (`merge_ok=True`).

Total additional API spend: ~$0.07, all on ST2.
