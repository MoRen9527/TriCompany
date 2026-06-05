from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.cognition.knowledge_workspace import (
    audit_workspace,
    employee_recall_workspace_order,
    employee_workspace,
    normalize_workspace_id,
    org_shared_workspace,
    role_workspace,
    support_root,
)


class RoleEmployeeWorkspaceValidation(unittest.TestCase):
    def test_normalizes_role_and_employee_identifiers(self) -> None:
        self.assertEqual(normalize_workspace_id("ChiefProductOfficer"), "chief-product-officer")
        self.assertEqual(normalize_workspace_id("rd_trainer"), "rd-trainer")
        self.assertEqual(normalize_workspace_id("CEO Chief Of Staff"), "c-e-o-chief-of-staff")

    def test_rejects_path_like_identifiers(self) -> None:
        with self.assertRaises(ValueError):
            normalize_workspace_id("../chief-product-officer")
        with self.assertRaises(ValueError):
            normalize_workspace_id("chief/product/officer")

    def test_builds_role_employee_org_and_audit_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            role = role_workspace("ChiefProductOfficer", workspace_root)
            employee = employee_workspace("cpo", workspace_root)
            org = org_shared_workspace(workspace_root)
            audit = audit_workspace(workspace_root)

            self.assertEqual(role.root, workspace_root / "knowledge" / "roles" / "chief-product-officer")
            self.assertEqual(employee.root, workspace_root / "knowledge" / "employees" / "cpo")
            self.assertEqual(org.root, workspace_root / "knowledge" / "org" / "shared")
            self.assertEqual(audit.root, workspace_root / "knowledge" / "audit")

    def test_resolves_support_root_from_source_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            source_root = workspace_root / "TriCompany"
            support = workspace_root / "TriMetaverse" / "TriCompany-copilot-host-assets"
            (source_root / ".github").mkdir(parents=True)
            (source_root / "runtime").mkdir(parents=True)
            support.mkdir(parents=True)

            self.assertEqual(support_root(source_root), support.resolve())

    def test_ensures_workspace_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = employee_workspace("rd-trainer", temp_dir)
            workspace.ensure_directories()

            self.assertTrue(workspace.inbox_root.is_dir())
            self.assertTrue(workspace.wiki_root.is_dir())
            self.assertTrue(workspace.audit_root.is_dir())
            self.assertTrue(workspace.workbench_root.is_dir())

    def test_employee_recall_order_is_private_role_shared_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_order = employee_recall_workspace_order(
                employee_id="rd-trainer",
                role_id="rd-trainer",
                workspace_root=temp_dir,
            )

            self.assertEqual([workspace.kind for workspace in workspace_order], ["employee", "role", "org", "audit"])
            self.assertEqual(workspace_order[0].identifier, "rd-trainer")
            self.assertEqual(workspace_order[1].identifier, "rd-trainer")


if __name__ == "__main__":
    unittest.main()
