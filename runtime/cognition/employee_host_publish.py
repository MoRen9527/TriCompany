from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.host_object_generation import (
    DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE,
    DECLARED_HOST_OBJECT_SETS,
    GeneratedHostObjectSet,
    generate_host_object_set,
    write_host_binding_profiles,
)


EMPLOYEE_CHOICES = {
    "all": None,
    **{employee_id: (employee_id,) for employee_id in sorted(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE)},
}


@dataclass(frozen=True)
class PublishedEmployeeHostAssets:
    employee_ids: tuple[str, ...]
    generated_host_object_sets: tuple[GeneratedHostObjectSet, ...]
    binding_profile_paths: tuple[Path, ...]


def publish_declared_employee_host_assets(
    *,
    source_root: str | Path,
    support_root: str | Path,
    employee_ids: tuple[str, ...] | None = None,
) -> PublishedEmployeeHostAssets:
    definitions = _selected_definitions(employee_ids)
    generated_host_object_sets = tuple(
        generate_host_object_set(support_root=support_root, definition=definition) for definition in definitions
    )
    normalized_employee_ids = tuple(definition.employee_id for definition in definitions)
    binding_profile_paths = write_host_binding_profiles(source_root, employee_ids=normalized_employee_ids)
    return PublishedEmployeeHostAssets(
        employee_ids=normalized_employee_ids,
        generated_host_object_sets=generated_host_object_sets,
        binding_profile_paths=binding_profile_paths,
    )


def _selected_definitions(employee_ids: tuple[str, ...] | None):
    if employee_ids is None:
        return DECLARED_HOST_OBJECT_SETS
    return tuple(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE[employee_id] for employee_id in employee_ids)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish declared TriCompany employee support payloads and source-side binding profiles together."
    )
    parser.add_argument("--source-root", default=".", help="Path to the TriCompany source root.")
    parser.add_argument("--support-root", required=True, help="Path to TriCompany-copilot-host-assets.")
    parser.add_argument(
        "--employee",
        default="all",
        choices=sorted(EMPLOYEE_CHOICES),
        help="Employee publish target. Defaults to all declared employees.",
    )
    args = parser.parse_args()

    published = publish_declared_employee_host_assets(
        source_root=args.source_root,
        support_root=args.support_root,
        employee_ids=EMPLOYEE_CHOICES[args.employee],
    )
    for generated_host_object_set in published.generated_host_object_sets:
        print(f"object_set={generated_host_object_set.object_set_id}")
        print(f"role_workspace={generated_host_object_set.role_workspace.root.as_posix()}")
        print(f"employee_workspace={generated_host_object_set.employee_workspace.root.as_posix()}")
    for binding_profile_path in published.binding_profile_paths:
        print(f"binding_profile={binding_profile_path.as_posix()}")
    if published.generated_host_object_sets:
        print(f"manifest={published.generated_host_object_sets[-1].manifest_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())