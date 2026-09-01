from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_host_binding_profile_generation import (
    HOST_ENTRY_STATUS_TO_MANIFEST_STATUSES,
    LIVE_STATUS_TO_MANIFEST_STATUSES,
    validate_binding_profile_consistency,
    validate_employee_binding,
)
from runtime.cognition.host_object_generation import (
    DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE,
    HOST_ENTRY_LIVE_MANIFEST_STATUSES,
    derive_host_entries,
    derive_host_entry_status,
    render_host_binding_profile,
    write_host_binding_profiles,
)


class EmployeeHostBindingProfileGenerationValidation(unittest.TestCase):
    def test_writes_rd_trainer_live_binding_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("rd-trainer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "rd-trainer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/rd-trainer.agent.md")
            self.assertEqual(profile["supportManifest"], "TriCompany-copilot-host-assets/host-object-manifest.json")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/rd-trainer")
            self.assertEqual(profile["runtimeNamespaces"][0]["namespace"], "employee/rd-trainer")

    def test_project_trainer_alias_writes_rd_trainer_binding_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("project-trainer",))

            self.assertEqual(len(profile_paths), 1)
            self.assertEqual(profile_paths[0].name, "rd-trainer.json")
            self.assertFalse((source_root / ".github" / "binding-profiles" / "project-trainer.json").exists())
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["employeeId"], "rd-trainer")
            self.assertEqual(profile["objectSetId"], "rd-trainer-knowledge-workspace-v0.1")

    def test_writes_cho_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-human-resources-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-human-resources-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-human-resources-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-human-resources-officer")
            notes = " ".join(profile["notes"])
            self.assertIn("enabled as an independent live host agent", notes)
            self.assertIn("handoff completion tracking", notes)

    def test_writes_cao_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-administrative-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-administrative-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-administrative-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-administrative-officer")

    def test_writes_cmo_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-marketing-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-marketing-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-marketing-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-marketing-officer")
            notes = " ".join(profile["notes"])
            self.assertIn("market research", notes)
            self.assertIn("does not imply TriMC formal host switch", notes)

    def test_writes_coo_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-operating-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-operating-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-operating-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-operating-officer")
            notes = " ".join(profile["notes"])
            self.assertIn("operating cadence", notes)
            self.assertIn("does not imply TriMC formal host switch", notes)

    def test_writes_cfo_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-financial-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-financial-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-financial-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-financial-officer")
            notes = " ".join(profile["notes"])
            self.assertIn("budget guardrails", notes)
            self.assertIn("does not imply TriMC formal host switch", notes)

    def test_writes_live_binding_profiles_for_current_employees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(
                source_root,
                employee_ids=("ceo-chief-of-staff", "chief-product-officer", "chief-technology-officer"),
            )

            self.assertEqual(len(profile_paths), 3)

            ceo_profile = json.loads((source_root / ".github" / "binding-profiles" / "ceo-chief-of-staff.json").read_text(encoding="utf-8"))
            self.assertEqual(ceo_profile["liveEntry"]["path"], "TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md")
            self.assertEqual(ceo_profile["hostStage"], "current-copilot-host-live")
            self.assertNotIn("legacy-chief-of-staff-knowledge-object-set", [item["kind"] for item in ceo_profile["supportObjects"]])

            cpo_profile = json.loads((source_root / ".github" / "binding-profiles" / "chief-product-officer.json").read_text(encoding="utf-8"))
            self.assertEqual(cpo_profile["employeeDisplayName"], "小乔")
            self.assertEqual(cpo_profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-product-officer.agent.md")
            self.assertIn("layer contracts only", " ".join(cpo_profile["notes"]))

            cto_profile = json.loads((source_root / ".github" / "binding-profiles" / "chief-technology-officer.json").read_text(encoding="utf-8"))
            self.assertEqual(cto_profile["employeeDisplayName"], "小狄")
            self.assertEqual(cto_profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-technology-officer.agent.md")

    def test_ceo_binding_profile_notes_carry_session_launch_command(self) -> None:
        # LG-023 S5 定谳（2026-09-01）：binding profile 为模板重建（_render_host_binding_profile
        # 不读现存 JSON），notes 真源 = definition.notes——启动命令注记必须在生成器内，
        # 禁手改 binding JSON（手写下轮 employee_host_publish 再生即被冲掉）。
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("ceo-chief-of-staff",))
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            notes = " ".join(profile["notes"])
            self.assertIn("--append-system-prompt-file", notes)
            # 锁 landing zone 全径（.claude/hub/ 目录 + 文件名），分隔符无关——
            # notes 原文为 Windows 反斜杠启动命令正身，归一后比对（CTO 原案强度恢复：
            # 仅锁文件名会让注记路径漂入错误目录时测试仍绿；组长代修 2026-09-01 升强）。
            self.assertIn(
                ".claude/hub/ceo-chief-of-staff.session.md",
                notes.replace("\\", "/"),
            )
            self.assertIn("session-body.agent.md", notes)
            self.assertIn("supersedes", notes, "取代关系注记（D25 金丝雀证据）必须在场")
            self.assertIn("layer contracts only", notes)  # 消费边界注记仍前携


# ── 三源一致性校验（FADE-ASSESS-004）───────────────────────────────────────
# binding profile（派生记录）↔ contract（语义真源）↔ manifest（绑定事实真源）


def _consistent_contract() -> dict:
    return {
        "contract": {"version": "3.0", "type": "agent-contract", "agent_id": "test-engineer", "family": "Role"},
        "identity": {"display_name": "小柯", "role": "TestEngineer", "description": "测试工程师。"},
        "paths": {
            "soul": "test-engineer/soul.agent.md",
            "agent_body": "test-engineer/agent-body.agent.md",
            "agent_frontmatter": "test-engineer/agent-frontmatter.agent.md",
            "memory": "test-engineer/memory.agent.md",
            "colleagues": "test-engineer/colleagues-social.agent.md",
            "social": "test-engineer/colleagues-social.agent.md",
        },
        "runtime_baseline": {"host": "copilot-host", "tri_mc_status": "planned", "tri_mc_migration_ready": False},
    }


def _consistent_binding() -> dict:
    return {
        "bindingProfileId": "test-engineer-host-binding-v0.1",
        "objectSetId": "test-engineer-knowledge-workspace-v0.1",
        "status": "current-copilot-host-live",
        "employeeId": "test-engineer",
        "ownerRole": "TestEngineer",
        "hostStage": "current-copilot-host-live",
        "sourceManifest": "TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json",
        "supportManifest": "TriCompany-copilot-host-assets/host-object-manifest.json",
        "liveEntry": {
            "status": "current-copilot-host-live",
            "path": "TriMetaverse/.github/agents/test-engineer.agent.md",
            "identityRule": "reuse-existing-live-entry",
        },
        "supportObjects": [
            {"kind": "role-knowledge-workspace", "workspaceId": "test-engineer", "path": "TriCompany-copilot-host-assets/knowledge/roles/test-engineer", "tracking": "tracked"},
            {"kind": "employee-knowledge-workspace", "workspaceId": "test-engineer", "path": "TriCompany-copilot-host-assets/knowledge/employees/test-engineer", "tracking": "tracked"},
            {"kind": "org-shared-knowledge-workspace", "workspaceId": "shared", "path": "TriCompany-copilot-host-assets/knowledge/org/shared", "tracking": "tracked"},
            {"kind": "audit-knowledge-workspace", "workspaceId": "audit", "path": "TriCompany-copilot-host-assets/knowledge/audit", "tracking": "tracked"},
        ],
        "runtimeNamespaces": [{"kind": "employee-private-runtime-namespace", "namespace": "employee/test-engineer"}],
        "notes": ["TestEngineer 启用说明。"],
        "employeeDisplayName": "小柯",
    }


def _consistent_manifest_entry() -> dict:
    return {
        "status": "current-copilot-host-live",
        "target": "TriMetaverse/.github/agents/test-engineer.agent.md",
        "source": "TriCompany/source-agents/test-engineer/test-engineer.agent.md",
        "kind": "role-agent",
        "renderTemplate": "host-default",
    }


class BindingProfileConsistencyValidation(unittest.TestCase):
    def test_consistent_three_source_passes(self) -> None:
        report = validate_binding_profile_consistency(
            _consistent_binding(),
            _consistent_contract(),
            _consistent_manifest_entry(),
            manifest_status="active",
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.employee_id, "test-engineer")

    def test_employee_id_drift_is_error(self) -> None:
        binding = _consistent_binding()
        binding["employeeId"] = "test-engineer-drifted"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "A1" and issue.severity == "error" for issue in report.issues))

    def test_live_entry_status_drift_is_error(self) -> None:
        binding = _consistent_binding()
        binding["liveEntry"]["status"] = "source-declared-staging"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B1" and issue.severity == "error" for issue in report.issues))

    def test_target_drift_is_error(self) -> None:
        binding = _consistent_binding()
        binding["liveEntry"]["path"] = "TriMetaverse/.github/agents/other-employee.agent.md"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B2" and issue.severity == "error" for issue in report.issues))
        self.assertTrue(any(issue.rule == "B3" and issue.severity == "error" for issue in report.issues))

    def test_support_objects_missing_is_error(self) -> None:
        binding = _consistent_binding()
        binding["supportObjects"] = [
            entry
            for entry in binding["supportObjects"]
            if entry["kind"] != "employee-knowledge-workspace"
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "D1" and issue.severity == "error" for issue in report.issues))

    def test_employee_workspace_drift_is_error(self) -> None:
        binding = _consistent_binding()
        employee_obj = next(entry for entry in binding["supportObjects"] if entry["kind"] == "employee-knowledge-workspace")
        employee_obj["path"] = "TriCompany-copilot-host-assets/knowledge/employees/drifted"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "D3" and issue.severity == "error" for issue in report.issues))

    def test_host_stage_drift_is_error(self) -> None:
        binding = _consistent_binding()
        binding["hostStage"] = "support-payload-generated-only"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "C1" and issue.severity == "error" for issue in report.issues))

    def test_live_entry_existing_not_changed_is_equivalent(self) -> None:
        binding = _consistent_binding()
        binding["liveEntry"]["status"] = "live-entry-existing-not-changed"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])

    def test_staging_profile_with_manifest_entry_warns(self) -> None:
        binding = _consistent_binding()
        binding["status"] = "generated-staging"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent)
        self.assertTrue(any(issue.rule == "G1" and issue.severity == "warn" for issue in report.issues))

    def test_identity_rule_and_notes_are_not_validated(self) -> None:
        # 不可替代部分：identityRule 与 notes 不参与一致性校验（人工/生成保留字段）
        binding = _consistent_binding()
        binding["liveEntry"]["identityRule"] = "manual-custom-rule"
        binding["notes"] = ["任意人工维护说明。"]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])

    def test_missing_contract_is_error(self) -> None:
        report = validate_binding_profile_consistency(
            _consistent_binding(), None, _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "E1" and issue.severity == "error" for issue in report.issues))

    def test_missing_manifest_is_error(self) -> None:
        report = validate_binding_profile_consistency(
            _consistent_binding(), _consistent_contract(), _consistent_manifest_entry(), manifest_status=None
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "F1" and issue.severity == "error" for issue in report.issues))

    def test_manifest_missing_entry_with_live_status_is_error(self) -> None:
        report = validate_binding_profile_consistency(
            _consistent_binding(), _consistent_contract(), None, manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "C3" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_positive(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {
                "host": "claude",
                "status": "current-host-live",
                "path": "TriMetaverse/.claude/agents/test-engineer.md",
                "identityRule": "render-derived-from-manifest",
            }
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)

    def test_host_entries_claude_session_positive(self) -> None:
        # LG-023 S6：claude-session binding 条目过 B1-B6 全组（path 双派生一致：
        # B2 derive(manifest.target) 与 B3 derive(employeeId 规则) 同落 .claude/hub/*.session.md）
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {
                "host": "claude-session",
                "status": "current-host-live",
                "path": "TriMetaverse/.claude/hub/test-engineer.session.md",
                "identityRule": "render-derived-from-manifest",
            }
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)

    def test_host_entries_absent_is_allowed(self) -> None:
        # 兼容无非 copilot 承载记录的历史 profile（旧 profile 零改动）
        binding = _consistent_binding()
        self.assertNotIn("hostEntries", binding)
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])

    def test_host_entries_empty_list_is_allowed(self) -> None:
        # 空数组 = 旧 profile 兼容（与缺省等价）；manifest 缺失时也不产生条目级错误
        binding = _consistent_binding()
        binding["hostEntries"] = []
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])

        report_no_manifest = validate_binding_profile_consistency(
            binding, _consistent_contract(), None, manifest_status="active"
        )
        self.assertFalse(any(issue.rule == "B6" for issue in report_no_manifest.issues))

    def test_host_entries_unknown_host_is_error(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "trimc", "status": "current-host-live", "path": "TriMC/.github/agents/test-engineer.agent.md", "identityRule": "render-derived-from-manifest"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B4" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_duplicate_host_is_error(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "current-host-live", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"},
            {"host": "claude", "status": "current-host-live", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"},
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B4" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_copilot_rejected(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "copilot", "status": "current-host-live", "path": "TriMetaverse/.github/agents/test-engineer.agent.md", "identityRule": "reuse-existing-live-entry"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B5" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_unknown_status_is_error(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "copilot-host-live", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B1" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_missing_status_or_path_is_error(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = [{"host": "claude", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"}]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B0" and issue.severity == "error" for issue in report.issues))

        binding = _consistent_binding()
        binding["hostEntries"] = [{"host": "claude", "status": "current-host-live", "identityRule": "render-derived-from-manifest"}]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B0" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_missing_identity_rule_is_error(self) -> None:
        # identityRule 为每项必留的绑定决策证据（按宿主注册表派生）
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "current-host-live", "path": "TriMetaverse/.claude/agents/test-engineer.md"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B0" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_path_drift_is_error(self) -> None:
        # B2（manifest target 派生）与 B3（employeeId 派生）双拒绝
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "current-host-live", "path": "TriMetaverse/.claude/agents/drifted.md", "identityRule": "render-derived-from-manifest"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B2" and issue.severity == "error" for issue in report.issues))
        self.assertTrue(any(issue.rule == "B3" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_path_conflicts_with_live_entry(self) -> None:
        # 与 liveEntry 同路径 = 与 manifest target 宿主派生必然不一致 → B2 拒绝
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "current-host-live", "path": "TriMetaverse/.github/agents/test-engineer.agent.md", "identityRule": "render-derived-from-manifest"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B2" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_status_semantic_drift_is_error(self) -> None:
        # B1：status 与 manifest 条目 status 语义不一致（同 liveEntry B1）
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "not-published", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B1" and issue.severity == "error" for issue in report.issues))
        self.assertTrue(any(issue.rule == "B6" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_status_not_exact_derivation_is_error(self) -> None:
        # B6：语义兼容（live 家族）但非生成管线派生值 → 禁人工编辑拒绝
        binding = _consistent_binding()
        binding["hostEntries"] = [
            {"host": "claude", "status": "live-entry-existing-not-changed", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"}
        ]
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B6" and issue.severity == "error" for issue in report.issues))
        self.assertFalse(any(issue.rule == "B1" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_without_manifest_entry_is_error(self) -> None:
        # B6：manifest 无条目但 hostEntries 存在 → 宿主条目不可派生（整体拒绝）
        report = validate_binding_profile_consistency(
            {
                **_consistent_binding(),
                "hostEntries": [
                    {"host": "claude", "status": "current-host-live", "path": "TriMetaverse/.claude/agents/test-engineer.md", "identityRule": "render-derived-from-manifest"}
                ],
            },
            _consistent_contract(),
            None,
            manifest_status="active",
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B6" and issue.severity == "error" for issue in report.issues))

    def test_host_entries_not_list_is_error(self) -> None:
        binding = _consistent_binding()
        binding["hostEntries"] = "claude"
        report = validate_binding_profile_consistency(
            binding, _consistent_contract(), _consistent_manifest_entry(), manifest_status="active"
        )
        self.assertFalse(report.is_consistent)
        self.assertTrue(any(issue.rule == "B0" and issue.severity == "error" for issue in report.issues))


# ── hostEntries 生成/派生（manifest + HOST_RENDER_REGISTRY 单一真源）────────


def _claude_host_entry() -> dict:
    return {
        "host": "claude",
        "status": "current-host-live",
        "path": "TriMetaverse/.claude/agents/test-engineer.md",
        "identityRule": "render-derived-from-manifest",
    }


class HostEntriesGenerationValidation(unittest.TestCase):
    def test_host_entry_status_derivation_from_manifest(self) -> None:
        live_entry = _consistent_manifest_entry()
        self.assertEqual(derive_host_entry_status(live_entry), "current-host-live")
        self.assertIsNone(derive_host_entry_status(None))
        non_live = dict(live_entry)
        non_live["status"] = "migrated-module-local-live-entry"
        self.assertIsNone(derive_host_entry_status(non_live))

    def test_derive_host_entries_from_manifest(self) -> None:
        self.assertEqual(derive_host_entries(_consistent_manifest_entry()), [_claude_host_entry()])
        self.assertEqual(derive_host_entries(None), [])
        self.assertEqual(derive_host_entries({}), [])
        non_live = dict(_consistent_manifest_entry())
        non_live["status"] = "module-local-live-entry"
        self.assertEqual(derive_host_entries(non_live), [])

    def test_derive_host_entries_session_face_requires_session_body(self) -> None:
        # LG-023 S6：claude-session 条目只对声明 sessionBody 的 manifest 条目派生
        #（与渲染管线零行为语义对齐——binding 不得声明渲染管线永不落盘的面）。
        entry = _consistent_manifest_entry()
        self.assertEqual([e["host"] for e in derive_host_entries(entry)], ["claude"])
        entry_with_session = dict(entry)
        entry_with_session["sessionBody"] = "TriCompany/source-agents/test-engineer/session-body.agent.md"
        entries = derive_host_entries(entry_with_session)
        self.assertEqual([e["host"] for e in entries], ["claude", "claude-session"])
        session_entry = entries[1]
        self.assertEqual(session_entry["path"], "TriMetaverse/.claude/hub/test-engineer.session.md")
        self.assertEqual(session_entry["status"], "current-host-live")
        self.assertEqual(session_entry["identityRule"], "render-derived-from-manifest")
        # 非 live 条目即使声明 sessionBody 也不派生（live 家族门在前）
        non_live = dict(entry_with_session)
        non_live["status"] = "module-local-live-entry"
        self.assertEqual(derive_host_entries(non_live), [])

    def test_status_mapping_is_consistent(self) -> None:
        # hostEntries live 家族与 liveEntry live 家族同一语义等价集（同构扩展）
        self.assertEqual(
            HOST_ENTRY_LIVE_MANIFEST_STATUSES,
            LIVE_STATUS_TO_MANIFEST_STATUSES["current-copilot-host-live"],
        )
        self.assertEqual(
            HOST_ENTRY_STATUS_TO_MANIFEST_STATUSES["current-host-live"],
            LIVE_STATUS_TO_MANIFEST_STATUSES["current-copilot-host-live"],
        )
        self.assertIn("current-host-live", HOST_ENTRY_STATUS_TO_MANIFEST_STATUSES)
        # hostEntries 只承载非 copilot 宿主（copilot 由 liveEntry 唯一承载）
        entries = derive_host_entries(_consistent_manifest_entry())
        self.assertEqual([e["host"] for e in entries], ["claude"])
        self.assertNotIn("copilot", [e["host"] for e in entries])

    def test_render_with_manifest_entry_derives_host_entries(self) -> None:
        definition = DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE["test-engineer"]
        profile = render_host_binding_profile(definition, manifest_entry=_consistent_manifest_entry())
        self.assertEqual(profile["hostEntries"], [_claude_host_entry()])
        # 无 manifest（旧生成场景）→ 旧 profile 形状，无 hostEntries
        self.assertNotIn("hostEntries", render_host_binding_profile(definition))

    def test_write_with_manifest_derives_host_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            manifest = {
                "manifestId": "trimetaverse-live-agent-discovery-publish-v0.1",
                "status": "active",
                "liveEntries": [_consistent_manifest_entry()],
            }
            profile_paths = write_host_binding_profiles(
                source_root, employee_ids=("test-engineer",), manifest=manifest
            )
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["hostEntries"], [_claude_host_entry()])

            # 无 manifest → 旧 profile 形状（既有消费方零改动）
            other_root = Path(temp_dir) / "TriCompanyLegacy"
            legacy_paths = write_host_binding_profiles(other_root, employee_ids=("test-engineer",))
            legacy_profile = json.loads(legacy_paths[0].read_text(encoding="utf-8"))
            self.assertNotIn("hostEntries", legacy_profile)

    def test_end_to_end_validate_binding_with_host_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            contract_dir = source_root / "source-agents" / "test-engineer"
            contract_dir.mkdir(parents=True)
            contract_path = contract_dir / "test-engineer.contract.yaml"
            contract_path.write_text(
                "contract:\n"
                "  version: \"3.0\"\n"
                "  type: agent-contract\n"
                "  agent_id: test-engineer\n"
                "  family: Role\n"
                "identity:\n"
                "  display_name: 小柯\n"
                "  role: TestEngineer\n"
                "  description: 测试工程师。\n"
                "paths:\n"
                "  soul: test-engineer/soul.agent.md\n"
                "  agent_body: test-engineer/agent-body.agent.md\n"
                "  memory: test-engineer/memory.agent.md\n",
                encoding="utf-8",
            )
            binding_dir = source_root / ".github" / "binding-profiles"
            binding_dir.mkdir(parents=True)
            binding_path = binding_dir / "test-engineer.json"
            binding_with_host_entries = _consistent_binding()
            binding_with_host_entries["hostEntries"] = [_claude_host_entry()]
            binding_path.write_text(json.dumps(binding_with_host_entries, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest_dir = source_root / "source-agents" / "registries"
            manifest_dir.mkdir(parents=True)
            manifest_path = manifest_dir / "trimetaverse-live-agent-publish-manifest.json"
            manifest_path.write_text(
                json.dumps({"manifestId": "trimetaverse-live-agent-discovery-publish-v0.1", "status": "active", "liveEntries": [_consistent_manifest_entry()]}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            report = validate_employee_binding(source_root, "test-engineer")
            self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])
            self.assertEqual(report.error_count, 0)
            self.assertEqual(report.employee_id, "test-engineer")

    def test_end_to_end_validate_employee_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            contract_dir = source_root / "source-agents" / "test-engineer"
            contract_dir.mkdir(parents=True)
            contract_path = contract_dir / "test-engineer.contract.yaml"
            contract_path.write_text(
                "contract:\n"
                "  version: \"3.0\"\n"
                "  type: agent-contract\n"
                "  agent_id: test-engineer\n"
                "  family: Role\n"
                "identity:\n"
                "  display_name: 小柯\n"
                "  role: TestEngineer\n"
                "  description: 测试工程师。\n"
                "paths:\n"
                "  soul: test-engineer/soul.agent.md\n"
                "  agent_body: test-engineer/agent-body.agent.md\n"
                "  memory: test-engineer/memory.agent.md\n",
                encoding="utf-8",
            )
            binding_dir = source_root / ".github" / "binding-profiles"
            binding_dir.mkdir(parents=True)
            binding_path = binding_dir / "test-engineer.json"
            binding_path.write_text(json.dumps(_consistent_binding(), ensure_ascii=False, indent=2), encoding="utf-8")
            manifest_dir = source_root / "source-agents" / "registries"
            manifest_dir.mkdir(parents=True)
            manifest_path = manifest_dir / "trimetaverse-live-agent-publish-manifest.json"
            manifest_path.write_text(
                json.dumps({"manifestId": "trimetaverse-live-agent-discovery-publish-v0.1", "status": "active", "liveEntries": [_consistent_manifest_entry()]}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            report = validate_employee_binding(source_root, "test-engineer")
            self.assertTrue(report.is_consistent, [issue.message for issue in report.issues])
            self.assertEqual(report.employee_id, "test-engineer")


if __name__ == "__main__":
    unittest.main()