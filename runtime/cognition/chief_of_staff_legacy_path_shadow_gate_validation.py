from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.chief_of_staff_legacy_path_shadow_gate import build_shadow_gate_report


class ChiefOfStaffLegacyPathShadowGateValidation(unittest.TestCase):
    def test_reports_ready_when_employee_workspace_is_parallel_and_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            support_root = workspace_root / "TriMetaverse" / "TriCompany-copilot-host-assets"
            self._seed_workspace(workspace_root, support_root, compatibility_status="deprecated-legacy-path")

            report = build_shadow_gate_report(workspace_root=workspace_root, support_root=support_root)

            self.assertEqual(report["status"], "shadow-gate-ready-for-formal-takeover")
            self.assertEqual(report["blockerCount"], 0)

    def test_blocks_when_employee_workbench_still_points_to_legacy_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            support_root = workspace_root / "TriMetaverse" / "TriCompany-copilot-host-assets"
            self._seed_workspace(workspace_root, support_root, compatibility_status="deprecated-legacy-path")
            workbench = support_root / "knowledge" / "employees" / "ceo-chief-of-staff" / "workbench" / "index.html"
            workbench.write_text("active path: knowledge/chief-of-staff/wiki\n", encoding="utf-8")

            report = build_shadow_gate_report(workspace_root=workspace_root, support_root=support_root)

            self.assertEqual(report["status"], "blocked-before-formal-takeover")
            self.assertIn("employee-workbench-legacy-reference", {item["category"] for item in report["blockers"]})

    def test_blocks_when_manifest_keeps_preserved_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            support_root = workspace_root / "TriMetaverse" / "TriCompany-copilot-host-assets"
            self._seed_workspace(workspace_root, support_root, compatibility_status="preserved-legacy-path")

            report = build_shadow_gate_report(workspace_root=workspace_root, support_root=support_root)

            self.assertEqual(report["status"], "blocked-before-formal-takeover")
            self.assertIn("manifest-status-not-deprecated", {item["category"] for item in report["blockers"]})

    def _seed_workspace(self, workspace_root: Path, support_root: Path, *, compatibility_status: str) -> None:
        legacy_root = support_root / "knowledge" / "chief-of-staff"
        employee_root = support_root / "knowledge" / "employees" / "ceo-chief-of-staff"
        for root in (legacy_root, employee_root):
            for area in ("wiki", "workbench", "audit"):
                (root / area).mkdir(parents=True, exist_ok=True)
            (root / "wiki" / "current.md").write_text("current wiki\n", encoding="utf-8")
            (root / "audit" / "record.json").write_text("{}\n", encoding="utf-8")

        for root in (legacy_root / "workbench", employee_root / "workbench"):
            (root / "approval-report").mkdir(parents=True, exist_ok=True)
            (root / "index.html").write_text("knowledge/employees/ceo-chief-of-staff/wiki\n", encoding="utf-8")
            (root / "snapshot.json").write_text("{}\n", encoding="utf-8")
            (root / "approval-report" / "snapshot.json").write_text("{}\n", encoding="utf-8")
            (root / "approval-report" / "summary.md").write_text("summary\n", encoding="utf-8")

        self._write_manifest(
            workspace_root / "TriCompany" / ".github" / "manifests" / "tricompany-host-object-generation-manifest.json",
            compatibility_status=compatibility_status,
        )
        self._write_manifest(support_root / "host-object-manifest.json", compatibility_status=compatibility_status)
        anchor_index = workspace_root / "TriMetaverse" / "docs" / "workflow" / "tricompany-copilot-host-assets-anchor-index.json"
        anchor_index.parent.mkdir(parents=True, exist_ok=True)
        anchor_index.write_text(
            json.dumps(
                {
                    "anchors": [
                        {
                            "path": "TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/index.html"
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def _write_manifest(self, path: Path, *, compatibility_status: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "objectSets": [
                        {
                            "supportObjects": [
                                {
                                    "path": "TriCompany-copilot-host-assets/knowledge/chief-of-staff",
                                    "compatibilityStatus": compatibility_status,
                                }
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()