from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.host_object_generation import (
    DECLARED_HOST_OBJECT_SETS,
    generate_all_declared_employee_host_objects,
    generate_ceo_chief_of_staff_host_objects,
    generate_chief_product_officer_host_objects,
    generate_chief_technology_officer_host_objects,
    generate_rd_trainer_host_objects,
)


class RAndDTrainerHostObjectGenerationValidation(unittest.TestCase):
    def test_generates_role_employee_workspace_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            support_root = Path(temp_dir) / "TriCompany-copilot-host-assets"
            result = generate_rd_trainer_host_objects(support_root)

            self.assertEqual(result.object_set_id, "rd-trainer-knowledge-workspace-v0.1")
            self.assertTrue((support_root / "knowledge" / "roles" / "rd-trainer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "rd-trainer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "org" / "shared" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "audit" / "README.md").is_file())
            self.assertTrue(result.role_workspace.inbox_root.is_dir())
            self.assertTrue(result.employee_workspace.workbench_root.is_dir())

            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["manifestId"], "tricompany-host-object-manifest-v0.1")
            self.assertEqual(manifest["objectSets"][0]["objectSetId"], "rd-trainer-knowledge-workspace-v0.1")
            self.assertEqual(manifest["objectSets"][0]["liveEntryStatus"], "current-copilot-host-live")
            self.assertEqual(manifest["objectSets"][0]["bindingProfile"], "TriCompany/.github/binding-profiles/rd-trainer.json")
            self.assertEqual(manifest["objectSets"][0]["employeeDisplayName"], "小吴")
            self.assertIn("layer contracts only", " ".join(manifest["objectSets"][0]["notes"]))
            self.assertIn("TriCompany/docs/training/ipd-usage-guide.md", manifest["objectSets"][0]["sourceRefs"])
            self.assertEqual(
                [item["kind"] for item in manifest["objectSets"][0]["supportObjects"]],
                [
                    "role-knowledge-workspace",
                    "employee-knowledge-workspace",
                    "org-shared-knowledge-workspace",
                    "audit-knowledge-workspace",
                ],
            )
            self.assertEqual(
                [item["tracking"] for item in manifest["objectSets"][0]["runtimeNamespaces"]],
                ["runtime-state", "runtime-state", "runtime-state"],
            )
            employee_readme = support_root / "knowledge" / "employees" / "rd-trainer" / "README.md"
            employee_readme_text = employee_readme.read_text(encoding="utf-8")
            self.assertIn("employeeDisplayName: 小吴", employee_readme_text)
            self.assertIn("employee-consumption-records.md", employee_readme_text)

    def test_generates_chief_of_staff_employee_workspace_without_legacy_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            support_root = Path(temp_dir) / "TriCompany-copilot-host-assets"

            result = generate_ceo_chief_of_staff_host_objects(support_root)

            self.assertEqual(result.object_set_id, "ceo-chief-of-staff-knowledge-workspace-v0.1")
            self.assertTrue((support_root / "knowledge" / "roles" / "ceo-chief-of-staff" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "ceo-chief-of-staff" / "README.md").is_file())

            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            object_set = manifest["objectSets"][0]
            self.assertEqual(object_set["liveEntryStatus"], "live-entry-existing-not-changed")
            self.assertNotIn("legacy-chief-of-staff-knowledge-object-set", [item["kind"] for item in object_set["supportObjects"]])
            self.assertIn("employee/ceo-chief-of-staff", [item["namespace"] for item in object_set["runtimeNamespaces"]])

    def test_generates_all_declared_employee_object_sets(self) -> None:
        """全量生成 = 声明列表驱动 + 反快照守卫。

        期望从 DECLARED_HOST_OBJECT_SETS 派生而非硬编码员工清单——onboard
        新员工只更新声明表，本测试不再过期（FADE-LEFTOVER-20260821-001 批 1
        终审观察项 1 修复，CTO 2026-08-21 裁决：原期望是 9 员工时代快照，
        生成器现返回 13，持续红污染回归基线）。
        反快照守卫：当前在役 13 员工全数在位（增量 onboard 不红、声明表
        意外删减即红）。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            support_root = Path(temp_dir) / "TriCompany-copilot-host-assets"
            results = generate_all_declared_employee_host_objects(support_root)

            declared_ids = [definition.object_set_id for definition in DECLARED_HOST_OBJECT_SETS]
            generated_ids = [result.object_set_id for result in results]
            self.assertEqual(generated_ids, declared_ids)
            self.assertGreaterEqual(len(results), 13)
            for expected in (
                "test-engineer-knowledge-workspace-v0.1",
                "full-stack-developer-knowledge-workspace-v0.1",
                "deployment-engineer-knowledge-workspace-v0.1",
                "customer-success-officer-knowledge-workspace-v0.1",
            ):
                self.assertIn(expected, generated_ids)
            manifest = json.loads(results[-1].manifest_path.read_text(encoding="utf-8"))
            self.assertEqual([item["objectSetId"] for item in manifest["objectSets"]], generated_ids)

    def test_generates_cpo_and_cto_live_entry_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            support_root = Path(temp_dir) / "TriCompany-copilot-host-assets"
            cpo_result = generate_chief_product_officer_host_objects(support_root)
            cto_result = generate_chief_technology_officer_host_objects(support_root)

            self.assertEqual(cpo_result.object_set_id, "chief-product-officer-knowledge-workspace-v0.1")
            self.assertEqual(cto_result.object_set_id, "chief-technology-officer-knowledge-workspace-v0.1")
            self.assertTrue((support_root / "knowledge" / "roles" / "chief-product-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-technology-officer" / "README.md").is_file())

            manifest = json.loads(cto_result.manifest_path.read_text(encoding="utf-8"))
            object_sets = {item["objectSetId"]: item for item in manifest["objectSets"]}
            self.assertEqual(object_sets["chief-product-officer-knowledge-workspace-v0.1"]["liveEntryStatus"], "live-entry-existing-not-changed")
            self.assertEqual(object_sets["chief-technology-officer-knowledge-workspace-v0.1"]["liveEntryStatus"], "live-entry-existing-not-changed")
            self.assertEqual(object_sets["chief-product-officer-knowledge-workspace-v0.1"]["employeeDisplayName"], "小乔")
            self.assertEqual(object_sets["chief-technology-officer-knowledge-workspace-v0.1"]["employeeDisplayName"], "小狄")
            self.assertIn("employee/chief-product-officer", [item["namespace"] for item in object_sets["chief-product-officer-knowledge-workspace-v0.1"]["runtimeNamespaces"]])
            self.assertIn("employee/chief-technology-officer", [item["namespace"] for item in object_sets["chief-technology-officer-knowledge-workspace-v0.1"]["runtimeNamespaces"]])
            cpo_readme = support_root / "knowledge" / "employees" / "chief-product-officer" / "README.md"
            cto_readme = support_root / "knowledge" / "employees" / "chief-technology-officer" / "README.md"
            self.assertIn("employeeDisplayName: 小乔", cpo_readme.read_text(encoding="utf-8"))
            self.assertIn("employeeDisplayName: 小狄", cto_readme.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
