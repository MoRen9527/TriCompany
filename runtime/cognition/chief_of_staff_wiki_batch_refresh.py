from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.runners.wiki_batch_refresh_runner import (
    run_chief_of_staff_wiki_batch_refresh,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run chief-of-staff wiki multi-topic batch refresh."
    )
    parser.add_argument("--workspace-root", help="Override workspace root.")
    parser.add_argument(
        "--spec-id",
        action="append",
        dest="spec_ids",
        help="Only refresh the given page spec. Repeatable.",
    )
    args = parser.parse_args()

    result = run_chief_of_staff_wiki_batch_refresh(
        spec_ids=tuple(args.spec_ids) if args.spec_ids else None,
        workspace_root=args.workspace_root,
    )
    print(f"spec_count={len(result.spec_ids)}")
    print(f"page_count={len(result.output_pages)}")
    print(f"audit={result.audit_path.as_posix()}")
    for page_id in result.output_pages:
        print(f"page={page_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())