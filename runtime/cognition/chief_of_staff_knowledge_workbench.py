from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.tasks.wiki_workbench_task import build_chief_of_staff_knowledge_workbench


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the chief-of-staff knowledge workbench.")
    parser.add_argument("--workspace-root", help="Override workspace root.")
    args = parser.parse_args()

    result = build_chief_of_staff_knowledge_workbench(workspace_root=args.workspace_root)
    for artifact_path in result["artifactPaths"]:
        print(artifact_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())