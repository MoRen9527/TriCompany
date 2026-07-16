from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.host_object_generation import (
    CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET,
    CHIEF_ADMINISTRATIVE_OFFICER_HOST_OBJECT_SET,
    CHIEF_FINANCIAL_OFFICER_HOST_OBJECT_SET,
    CHIEF_HUMAN_RESOURCES_OFFICER_HOST_OBJECT_SET,
    CHIEF_MARKETING_OFFICER_HOST_OBJECT_SET,
    CHIEF_OPERATING_OFFICER_HOST_OBJECT_SET,
    CHIEF_PRODUCT_OFFICER_HOST_OBJECT_SET,
    CHIEF_TECHNOLOGY_OFFICER_HOST_OBJECT_SET,
    FULL_STACK_DEVELOPER_HOST_OBJECT_SET,
    RD_TRAINER_HOST_OBJECT_SET,
    TEST_ENGINEER_HOST_OBJECT_SET,
    generate_all_declared_employee_host_objects,
    generate_ceo_chief_of_staff_host_objects,
    generate_chief_administrative_officer_host_objects,
    generate_chief_financial_officer_host_objects,
    generate_chief_human_resources_officer_host_objects,
    generate_chief_marketing_officer_host_objects,
    generate_chief_operating_officer_host_objects,
    generate_chief_product_officer_host_objects,
    generate_chief_technology_officer_host_objects,
    generate_full_stack_developer_host_objects,
    generate_rd_trainer_host_objects,
    generate_test_engineer_host_objects,
)


EMPLOYEE_GENERATORS = {
    "all": generate_all_declared_employee_host_objects,
    RD_TRAINER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_rd_trainer_host_objects(support_root),),
    "project-trainer": lambda support_root: (generate_rd_trainer_host_objects(support_root),),
    CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_ceo_chief_of_staff_host_objects(support_root),),
    CHIEF_PRODUCT_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_product_officer_host_objects(support_root),),
    CHIEF_TECHNOLOGY_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_technology_officer_host_objects(support_root),),
    CHIEF_MARKETING_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_marketing_officer_host_objects(support_root),),
    CHIEF_OPERATING_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_operating_officer_host_objects(support_root),),
    CHIEF_FINANCIAL_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_financial_officer_host_objects(support_root),),
    CHIEF_HUMAN_RESOURCES_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_human_resources_officer_host_objects(support_root),),
    CHIEF_ADMINISTRATIVE_OFFICER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_chief_administrative_officer_host_objects(support_root),),
    TEST_ENGINEER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_test_engineer_host_objects(support_root),),
    FULL_STACK_DEVELOPER_HOST_OBJECT_SET.employee_id: lambda support_root: (generate_full_stack_developer_host_objects(support_root),),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate declared TriCompany employee host object payloads.")
    parser.add_argument("--support-root", required=True, help="Path to TriCompany-copilot-host-assets.")
    parser.add_argument(
        "--employee",
        default="all",
        choices=sorted(EMPLOYEE_GENERATORS),
        help="Employee object set to generate. Defaults to all declared employee object sets.",
    )
    args = parser.parse_args()

    results = EMPLOYEE_GENERATORS[args.employee](args.support_root)
    for result in results:
        print(f"object_set={result.object_set_id}")
        print(f"role_workspace={result.role_workspace.root.as_posix()}")
        print(f"employee_workspace={result.employee_workspace.root.as_posix()}")
        print(f"org_shared_workspace={result.org_shared_workspace.root.as_posix()}")
        print(f"audit_workspace={result.audit_workspace.root.as_posix()}")
    if results:
        print(f"manifest={results[-1].manifest_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())