from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.host_object_generation import generate_project_trainer_host_objects


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deprecated compatibility wrapper; generates RAndDTrainer host object payloads for the rd-trainer canonical id."
    )
    parser.add_argument("--support-root", required=True, help="Path to TriCompany-copilot-host-assets.")
    args = parser.parse_args()

    result = generate_project_trainer_host_objects(args.support_root)
    print("deprecated_alias=project-trainer")
    print("canonical_employee=rd-trainer")
    print(f"object_set={result.object_set_id}")
    print(f"role_workspace={result.role_workspace.root.as_posix()}")
    print(f"employee_workspace={result.employee_workspace.root.as_posix()}")
    print(f"org_shared_workspace={result.org_shared_workspace.root.as_posix()}")
    print(f"audit_workspace={result.audit_workspace.root.as_posix()}")
    print(f"manifest={result.manifest_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
