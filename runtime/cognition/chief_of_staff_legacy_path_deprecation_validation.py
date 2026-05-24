from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.cognition.chief_of_staff_legacy_path_deprecation_readiness import (
    LegacyPathScanRoot,
    build_readiness_report,
)


class ChiefOfStaffLegacyPathDeprecationValidation(unittest.TestCase):
    def test_reports_blocked_when_active_dependencies_reference_legacy_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            runtime_file = workspace_root / "TriCompany" / "runtime" / "cognition" / "dispatch" / "host_dispatcher.py"
            anchor_file = workspace_root / "TriMetaverse" / "docs" / "workflow" / "anchor-index.json"
            runtime_file.parent.mkdir(parents=True)
            anchor_file.parent.mkdir(parents=True)
            runtime_file.write_text('target = "knowledge/chief-of-staff/audit"\n', encoding="utf-8")
            anchor_file.write_text('{"path":"TriCompany-copilot-host-assets/knowledge/chief-of-staff/workbench/index.html"}\n', encoding="utf-8")

            report = build_readiness_report(
                workspace_root=workspace_root,
                scan_roots=(
                    LegacyPathScanRoot(
                        root=runtime_file.parent,
                        category="runtime-source",
                        blocking=True,
                        reason="runtime dependency",
                    ),
                    LegacyPathScanRoot(
                        root=anchor_file,
                        category="governance-anchor-index",
                        blocking=True,
                        reason="governance anchor",
                    ),
                ),
            )

            self.assertEqual(report["status"], "blocked-by-active-legacy-path-dependencies")
            self.assertEqual(report["blockingDependencyCount"], 2)
            self.assertEqual(
                {item["category"] for item in report["blockingDependencies"]},
                {"runtime-source", "governance-anchor-index"},
            )

    def test_reports_ready_when_no_blocking_dependencies_remain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            runtime_file = workspace_root / "TriCompany" / "runtime" / "cognition" / "dispatch" / "host_dispatcher.py"
            manifest_file = workspace_root / "TriMetaverse" / "TriCompany-copilot-host-assets" / "host-object-manifest.json"
            runtime_file.parent.mkdir(parents=True)
            manifest_file.parent.mkdir(parents=True)
            runtime_file.write_text('target = "knowledge/employees/ceo-chief-of-staff/audit"\n', encoding="utf-8")
            manifest_file.write_text('{"path":"TriCompany-copilot-host-assets/knowledge/chief-of-staff"}\n', encoding="utf-8")

            report = build_readiness_report(
                workspace_root=workspace_root,
                scan_roots=(
                    LegacyPathScanRoot(
                        root=runtime_file.parent,
                        category="runtime-source",
                        blocking=True,
                        reason="runtime dependency",
                    ),
                    LegacyPathScanRoot(
                        root=manifest_file,
                        category="support-host-object-manifest",
                        blocking=False,
                        reason="manifest compatibility reference",
                    ),
                ),
            )

            self.assertEqual(report["status"], "ready-for-deprecation-label")
            self.assertEqual(report["blockingDependencyCount"], 0)
            self.assertEqual(report["nonBlockingReferenceCount"], 1)

    def test_runtime_compatibility_records_are_non_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            generator_file = workspace_root / "TriCompany" / "runtime" / "cognition" / "host_object_generation.py"
            generator_file.parent.mkdir(parents=True)
            generator_file.write_text('{"path":"TriCompany-copilot-host-assets/knowledge/chief-of-staff"}\n', encoding="utf-8")

            report = build_readiness_report(
                workspace_root=workspace_root,
                scan_roots=(
                    LegacyPathScanRoot(
                        root=generator_file.parent,
                        category="runtime-source",
                        blocking=True,
                        reason="runtime dependency",
                    ),
                ),
            )

            self.assertEqual(report["status"], "ready-for-deprecation-label")
            self.assertEqual(report["blockingDependencyCount"], 0)
            self.assertEqual(report["nonBlockingReferenceCount"], 1)
            self.assertEqual(report["nonBlockingReferences"][0]["category"], "runtime-compatibility-record")


if __name__ == "__main__":
    unittest.main()