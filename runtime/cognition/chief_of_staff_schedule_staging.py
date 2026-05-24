from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.runners.cron_runner import run_due_chief_of_staff_schedules


def main() -> int:
    parser = argparse.ArgumentParser(description="Run chief-of-staff schedule/cron staging tasks.")
    parser.add_argument("--workspace-root", help="Override workspace root.")
    args = parser.parse_args()

    result = run_due_chief_of_staff_schedules(workspace_root=args.workspace_root)
    print(f"schedule_count={result.schedule_count}")
    for path in result.run_record_paths:
        print(f"run_record={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())