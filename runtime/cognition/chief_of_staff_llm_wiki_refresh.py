from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.runners.wiki_refresh_runner import run_chief_of_staff_wiki_refresh


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a chief-of-staff LLM wiki refresh.")
    parser.add_argument("--page-id", required=True, help="Target wiki page id.")
    parser.add_argument("--title", required=True, help="Target wiki page title.")
    parser.add_argument("--workspace-root", help="Override workspace root.")
    args = parser.parse_args()

    result = run_chief_of_staff_wiki_refresh(
        page_id=args.page_id,
        title=args.title,
        workspace_root=args.workspace_root,
    )
    print(f"run_id={result.run_id}")
    print(f"page={result.output_page_path.as_posix()}")
    print(f"audit={result.audit_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())