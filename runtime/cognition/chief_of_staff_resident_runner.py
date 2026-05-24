from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.runners.resident_runner import run_resident_chief_of_staff_schedules


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the chief-of-staff resident schedule runner."
    )
    parser.add_argument("--workspace-root", help="Override workspace root.")
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=60.0,
        help="Seconds between cycles.",
    )
    parser.add_argument("--cycles", type=int, default=1, help="Maximum cycle count.")
    args = parser.parse_args()

    result = run_resident_chief_of_staff_schedules(
        workspace_root=args.workspace_root,
        interval_seconds=args.interval_seconds,
        max_cycles=args.cycles,
    )
    print(f"cycles={result.cycle_count}")
    print(f"schedule_runs={result.total_schedule_runs}")
    for artifact_path in result.run_record_paths:
        print(artifact_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())