from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.tasks.operating_review_closeout_task import (
    run_operating_review_closeout_task,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dispatch a central registry closeout from an operating review object."
    )
    parser.add_argument(
        "--operating-review",
        required=True,
        help="Path to the OPERATING_REVIEW JSON object.",
    )
    parser.add_argument(
        "--closeout",
        required=True,
        help="Path to the CENTRAL_REGISTRY_CLOSEOUT JSON object.",
    )
    parser.add_argument("--workspace-root", help="Override workspace root.")
    parser.add_argument("--delivery-channel", help="Override delivery channel.")
    parser.add_argument("--delivery-target", help="Override delivery target.")
    args = parser.parse_args()

    result = run_operating_review_closeout_task(
        operating_review_path=args.operating_review,
        closeout_path=args.closeout,
        workspace_root=args.workspace_root,
        trigger_mode="manual",
        delivery_channel=args.delivery_channel,
        delivery_target=args.delivery_target,
    )
    print(f"status={result['status']}")
    print(f"deliveryStatus={result['deliveryStatus']}")
    artifact_paths = result.get("artifactPaths")
    for artifact_path in artifact_paths if isinstance(artifact_paths, (list, tuple)) else ():
        print(artifact_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())