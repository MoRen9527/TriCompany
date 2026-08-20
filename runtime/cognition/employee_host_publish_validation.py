from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_host_publish import publish_declared_employee_host_assets

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
                    "chief-marketing-officer",
                    "chief-operating-officer",
                    "chief-financial-officer",
                    "chief-human-resources-officer",
                    "chief-administrative-officer",
                    "test-engineer",
                    "full-stack-developer",
                    "deployment-engineer",
                    "customer-success-officer",
                ),
            )
            self.assertEqual(len(published.generated_host_object_sets), 13)
            self.assertEqual(len(published.binding_profile_paths), 13)
            self.assertTrue((source_root / ".github" / "binding-profiles" / "ceo-chief-of-staff.json").is_file())
            self.assertTrue((source_root / ".github" / "binding-profiles" / "test-engineer.json").is_file())
            self.assertTrue((source_root / ".github" / "binding-profiles" / "full-stack-developer.json").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-technology-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-marketing-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-operating-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-financial-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-human-resources-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "chief-administrative-officer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "test-engineer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "full-stack-developer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "deployment-engineer" / "README.md").is_file())
            self.assertTrue((support_root / "knowledge" / "employees" / "customer-success-officer" / "README.md").is_file())


class EmployeeHostPublishCLIValidation(unittest.TestCase):
    """CLI safety-gate tests (ADE phase-0 fix 1: default is dry-run, no writes)."""

    def _run_cli(self, source_root: Path, support_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            "-m",
            "runtime.cognition.employee_host_publish",
            "--source-root",
            str(source_root),
            "--support-root",
            str(support_root),
            "--employee",
            "rd-trainer",
            "--format",
            "json",
        ]
        args.extend(extra_args)
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(_REPO_ROOT),
            timeout=60,
        )

    def test_default_is_dry_run_and_writes_nothing(self) -> None:
        """ADE fix 1: no --dry-run/--execute → dry-run, no files written."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            source_root = workspace_root / "TriCompany"
            support_root = workspace_root / "TriCompany-copilot-host-assets"

            proc = self._run_cli(source_root, support_root)
            self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
            data = json.loads(proc.stdout)
            self.assertEqual(data["status"], "pass")

            self.assertFalse(
                (source_root / ".github" / "binding-profiles" / "rd-trainer.json").exists(),
                "default invocation must not write binding profiles",
            )
            self.assertFalse(
                (support_root / "knowledge" / "roles" / "rd-trainer" / "README.md").exists(),
                "default invocation must not write support payloads",
            )
            self.assertFalse(
                (support_root / "knowledge" / "employees" / "rd-trainer" / "README.md").exists(),
                "default invocation must not write employee workspace payloads",
            )

    def test_execute_is_explicit_and_writes(self) -> None:
        """ADE fix 1: --execute explicitly writes generated assets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            source_root = workspace_root / "TriCompany"
            support_root = workspace_root / "TriCompany-copilot-host-assets"

            proc = self._run_cli(source_root, support_root, "--execute")
            self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
            data = json.loads(proc.stdout)
            self.assertEqual(data["status"], "pass")

            self.assertTrue(
                (source_root / ".github" / "binding-profiles" / "rd-trainer.json").is_file(),
                "--execute must write binding profiles",
            )
            self.assertTrue(
                (support_root / "knowledge" / "roles" / "rd-trainer" / "README.md").is_file(),
                "--execute must write support payloads",
            )

    def test_dry_run_and_execute_are_mutually_exclusive(self) -> None:
        """ADE fix 1: passing both --dry-run and --execute exits with code 2."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            proc = self._run_cli(
                workspace_root / "TriCompany",
                workspace_root / "TriCompany-copilot-host-assets",
                "--dry-run",
                "--execute",
            )
            self.assertEqual(proc.returncode, 2, f"stderr: {proc.stderr}")
            self.assertIn("mutually exclusive", proc.stderr)


if __name__ == "__main__":
    unittest.main()