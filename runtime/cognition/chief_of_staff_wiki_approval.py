from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.tasks.wiki_approval_task import record_wiki_approval


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a chief-of-staff wiki approval decision.")
    parser.add_argument("--page-id", required=True, help="Target wiki page id.")
    parser.add_argument("--decision", required=True, choices=["approved", "rejected", "pending"], help="Approval decision.")
    parser.add_argument("--reviewer", required=True, help="Reviewer name or role.")
    parser.add_argument("--note", default="", help="Approval note.")
    parser.add_argument("--workspace-root", help="Override workspace root.")
    args = parser.parse_args()

    result = record_wiki_approval(
        page_id=args.page_id,
        decision=args.decision,
        reviewer=args.reviewer,
        note=args.note,
        workspace_root=args.workspace_root,
    )
    for artifact_path in result["artifactPaths"]:
        print(artifact_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())