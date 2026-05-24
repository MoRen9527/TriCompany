from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.host_object_generation import DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE, write_host_binding_profiles


EMPLOYEE_CHOICES = {
    "all": None,
    **{employee_id: (employee_id,) for employee_id in sorted(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE)},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Write declared TriCompany employee host binding profiles.")
    parser.add_argument("--source-root", default=".", help="Path to the TriCompany source root.")
    parser.add_argument(
        "--employee",
        default="all",
        choices=sorted(EMPLOYEE_CHOICES),
        help="Employee binding profile to write. Defaults to all declared employees.",
    )
    args = parser.parse_args()

    profile_paths = write_host_binding_profiles(args.source_root, employee_ids=EMPLOYEE_CHOICES[args.employee])
    for profile_path in profile_paths:
        print(f"binding_profile={profile_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())