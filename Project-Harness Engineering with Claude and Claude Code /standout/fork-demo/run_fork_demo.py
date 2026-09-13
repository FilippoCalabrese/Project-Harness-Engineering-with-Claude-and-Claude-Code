"""Stand-out 3 — exercise System 4's fork path end-to-end.

Forks the base hot state into two competing hypotheses for the capacitor-bank-C-7
defect cluster, gives each fork its own isolated scratchpad, proves the two
scratchpads never cross-contaminate, then merges both findings into the main stream.

Run from the System 4 solution venv:
    python run_fork_demo.py <base_hot_state.json> <work_dir>
Outputs (under <work_dir>):
    forks/hypA-lot-defect/scratchpad.jsonl
    forks/hypB-equipment-wear/scratchpad.jsonl
    main_scratchpad.jsonl
and prints an isolation report to stdout.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from shift_monitor.fork import fork_for_hypothesis, merge_findings
from shift_monitor.scratchpad import Scratchpad, ScratchpadEntry


def _now() -> datetime:
    return datetime.now(timezone.utc)


def main() -> int:
    base_hot_state = Path(sys.argv[1])
    work = Path(sys.argv[2])
    forks_root = work / "forks"
    main_scratchpad_path = work / "main_scratchpad.jsonl"

    # Two competing hypotheses for the capacitor-bank-C-7 cluster.
    hyps = {
        "hypA-lot-defect": ScratchpadEntry(
            hypothesis_id="hypA-lot-defect",
            evidence="5 defects on capacitor-bank-C-7 all trace to lot 2026-0430-B; DAR 0.39, ESR ~19 mOhm cluster within a single lot.",
            conclusion="Most consistent with a dielectric/impregnation defect in lot 2026-0430-B. Recommend lot quarantine + sample retest.",
            ts=_now(),
        ),
        "hypB-equipment-wear": ScratchpadEntry(
            hypothesis_id="hypB-equipment-wear",
            evidence="capacitor-bank-C-7 shows 15/17 defects on night shift over 60 days, spanning multiple lots — points to an equipment/environment factor, not one lot.",
            conclusion="Most consistent with night-shift equipment wear or thermal cycling on bank C-7. Recommend PM inspection + thermal logging.",
            ts=_now(),
        ),
    }

    fork_dirs: dict[str, Path] = {}
    fork_scratchpads: list[Path] = []
    for hyp_id, entry in hyps.items():
        fork_dir = fork_for_hypothesis(base_hot_state, hyp_id, forks_root)
        fork_dirs[hyp_id] = fork_dir
        sp_path = fork_dir / "scratchpad.jsonl"
        Scratchpad(sp_path).append(entry)  # each fork writes ONLY its own entry
        fork_scratchpads.append(sp_path)

    # --- Isolation proof: each fork scratchpad holds exactly its own hypothesis ---
    print("=== Fork isolation report ===")
    ok = True
    for hyp_id, fork_dir in fork_dirs.items():
        entries = Scratchpad(fork_dir / "scratchpad.jsonl").read()
        ids = [e.hypothesis_id for e in entries]
        isolated = ids == [hyp_id]
        ok = ok and isolated
        # confirm the shared baseline was actually copied into the fork
        has_baseline = (fork_dir / "hot_state.json").exists()
        print(
            f"  {hyp_id}: entries={ids} isolated={isolated} baseline_copied={has_baseline}"
        )

    # --- Merge both isolated findings into the main stream ---
    merge_findings(fork_scratchpads, main_scratchpad_path)
    merged = Scratchpad(main_scratchpad_path).read()
    merged_ids = sorted(e.hypothesis_id for e in merged)
    print(f"  main after merge: {merged_ids} (count={len(merged)})")

    all_merged = merged_ids == ["hypA-lot-defect", "hypB-equipment-wear"]
    print(f"=== RESULT: isolation_ok={ok} merge_ok={all_merged} ===")
    return 0 if (ok and all_merged) else 1


if __name__ == "__main__":
    raise SystemExit(main())
