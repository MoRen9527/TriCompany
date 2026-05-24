from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_host_publish import publish_declared_employee_host_assets


class EmployeeHostPublishValidation(unittest.TestCase):
    def test_publishes_single_employee_support_payload_and_binding_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            source_root = workspace_root / "TriCompany"
            support_root = workspace_root / "TriCompany-copilot-host-assets"

            published = publish_declared_employee_host_assets(
                source_root=source_root,
                support_root=support_root,
                employee_ids=("rd-trainer",),
            )

            self.assertEqual(published.employee_ids, ("rd-trainer",))
            self.assertEqual(len(published.generated_host_object_sets), 1)
            self.assertEqual(len(published.binding_profile_paths), 1)
            self.assertTrue((support_root / "knowledge" / "roles" / "rd-trainer" / "README.md").is_file())
            self.assertTrue((source_root / ".github" / "binding-profiles" / "rd-trainer.json").is_file())

            manifest = json.loads((support_root / "host-object-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["objectSets"][0]["bindingProfile"], "TriCompany/.github/binding-profiles/rd-trainer.json")

    def test_publishes_all_declared_employees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            source_root = workspace_root / "TriCompany"
            support_root = workspace_root / "TriCompany-copilot-host-assets"

            published = publish_declared_employee_host_assets(source_root=source_root, support_root=support_root)

            self.assertEqual(
                published.employee_ids,
                (
                    "rd-trainer",
                    "ceo-chief-of-staff",
                    "chief-product-officer",
                    "chief-technology-officer",
                    "chief-human-resources-officer",
                    "chief-administrative-officer",
                ),
            )
            self.assertEqual(len(published.generated_host_object_sets), 6)
            self.assertEqual(len(published.binding_profile_paths), 6)
            self.assertTrue((source_root / ".github" / "binding-profiles" / "ceo-chief-of-staff.json").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-technology-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-human-resources-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-administrative-officer" / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()