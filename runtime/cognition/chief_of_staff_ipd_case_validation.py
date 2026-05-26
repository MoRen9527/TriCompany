from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_ipd_case import main as ipd_case_main
from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_ipd_case_root
from runtime.cognition.ipd_case_engine import (
    initialize_ipd_case,
    read_ipd_case,
    record_intake_signoff,
    record_stage_signoff,
    submit_stage_output,
)
from runtime.cognition.tasks.checkpoint_task import run_checkpoint_task


class ChiefOfStaffIpdCaseValidationTest(unittest.TestCase):
    def test_intake_approvals_start_first_stage_and_generate_cmo_work_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            result = initialize_ipd_case(
                case_id="IPD-001",
                title="自动化开发执行闭环",
                objective="建立从 CEO 任务到交付收口的最小 IPD 引擎",
                task_description="CEO 和总助只提总要求，后续由各 O 细化推进。",
                related_modules=("TriCompany", "TriDev"),
                opportunity_signals=("AI coding 与 agent workflow 正在成为增量热点。",),
                business_model_fit=("符合当前低成本先跑通可收费最小闭环的商业模式。",),
                stage_fit=("符合当前 Copilot-host 正式接管阶段，先验证最小 company workflow slice。",),
                company_context=("TriCompany 已有最小 IPD runtime slice，可先跑通公司级流程闭环。",),
                owner_proposal=("总助先做入口 briefing，后续由各个 O 按节点细化。",),
                resource_envelope=("预计 CTO / TriDev 首轮投入 2-3 人天，当前主要为试验时间和工具成本。",),
                prerequisites=("CEO 确认进入 IPD 主动交付线。",),
                required_support=("CMO / COO / CFO / CPO / CTO 需按节点补齐专业判断。",),
                expected_outcomes=("形成一条可重复运行的最小 IPD 闭环。",),
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["status"], "awaiting-intake-approvals")
            result = record_intake_signoff(
                "IPD-001",
                role="CEO",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["status"], "waiting-stage-output")
            self.assertEqual(result["currentStageKey"], "discovery")

            case_payload = read_ipd_case("IPD-001", workspace_root=str(workspace_root))
            intake_brief_path = chief_of_staff_ipd_case_root("IPD-001", workspace_root) / "intake-brief.json"
            self.assertTrue(intake_brief_path.exists())
            intake_brief = json.loads(intake_brief_path.read_text(encoding="utf-8"))
            self.assertEqual(intake_brief["kind"], "ipd-intake-brief")
            self.assertEqual(
                intake_brief["briefing"]["opportunitySignals"],
                ["AI coding 与 agent workflow 正在成为增量热点。"],
            )
            self.assertEqual(
                intake_brief["briefing"]["businessModelFit"],
                ["符合当前低成本先跑通可收费最小闭环的商业模式。"],
            )
            self.assertEqual(
                intake_brief["requiredApprovers"],
                ["CEOChiefOfStaff", "CEO"],
            )
            current_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            work_item_path = Path(current_stage["workItemPath"])
            self.assertTrue(work_item_path.exists())
            work_item = json.loads(work_item_path.read_text(encoding="utf-8"))
            self.assertEqual(work_item["ownerRole"], "CEOChiefOfStaff")
            self.assertEqual(work_item["phaseKey"], "DISCOVERY")
            self.assertEqual(work_item["schemaHint"]["objectType"], "IPD_DISCOVERY_PACKAGE")
            self.assertEqual(work_item["draftTemplate"]["objectType"], "IPD_DISCOVERY_PACKAGE")
            self.assertEqual(
                work_item["participantRoles"],
                ["CEO", "ChiefMarketingOfficer"],
            )
            self.assertEqual(work_item["intake"]["briefPath"], intake_brief_path.as_posix())
            self.assertIn("workbench/ipd/cases/IPD-001/intake-brief.json", work_item["inputRefs"])
            self.assertEqual(work_item["requiredApprovers"], ["CEOChiefOfStaff", "CEO"])

    def test_case_can_run_end_to_end_until_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-002",
                title="端到端 IPD 闭环",
                objective="从总要求自动推进到总助收口",
                task_description="验证每个节点由 owner 提交，CEO 和总助签核后自动进入下一节点。",
                related_modules=("TriCompany", "TriDev"),
                workspace_root=str(workspace_root),
            )
            record_intake_signoff("IPD-002", role="CEO", workspace_root=str(workspace_root))

            case_payload = read_ipd_case("IPD-002", workspace_root=str(workspace_root))
            while case_payload["status"] != "completed":
                stage_key = case_payload["currentStageKey"]
                stage = next(item for item in case_payload["stages"] if item["stageKey"] == stage_key)
                submit_stage_output(
                    "IPD-002",
                    stage_key=stage_key,
                    submitted_by=stage["ownerRole"],
                    summary=f"{stage_key} 已提交",
                    details=(f"{stage_key} 细化结果",),
                    evidence=(f"evidence/{stage_key}.md",),
                    workspace_root=str(workspace_root),
                )
                record_stage_signoff(
                    "IPD-002",
                    stage_key=stage_key,
                    role="CEOChiefOfStaff",
                    workspace_root=str(workspace_root),
                )
                result = record_stage_signoff(
                    "IPD-002",
                    stage_key=stage_key,
                    role="CEO",
                    workspace_root=str(workspace_root),
                )
                case_payload = read_ipd_case("IPD-002", workspace_root=str(workspace_root))
                if case_payload["status"] != "completed":
                    self.assertEqual(result["status"], "waiting-stage-output")

            self.assertEqual(case_payload["status"], "completed")
            self.assertEqual(case_payload["currentStageKey"], "")
            self.assertTrue(all(stage["status"] == "completed" for stage in case_payload["stages"]))

    def test_rejected_stage_blocks_case_until_owner_resubmits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-003",
                title="拒绝后重提",
                objective="验证节点拒绝后阻断并允许重提",
                task_description="CMO 节点先被拒绝，再重提通过。",
                workspace_root=str(workspace_root),
            )
            record_intake_signoff("IPD-003", role="CEO", workspace_root=str(workspace_root))
            submit_stage_output(
                "IPD-003",
                stage_key="discovery",
                submitted_by="CEOChiefOfStaff",
                summary="首版 discovery package",
                workspace_root=str(workspace_root),
            )
            record_stage_signoff(
                "IPD-003",
                stage_key="discovery",
                role="CEOChiefOfStaff",
                decision="rejected",
                note="证据不足",
                workspace_root=str(workspace_root),
            )
            case_payload = read_ipd_case("IPD-003", workspace_root=str(workspace_root))
            current_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            self.assertEqual(case_payload["status"], "blocked")
            self.assertEqual(current_stage["status"], "rejected")

            submit_stage_output(
                "IPD-003",
                stage_key="discovery",
                submitted_by="CEOChiefOfStaff",
                summary="二版 discovery package",
                details=("补充任务边界、raw evidence 和后续待验证问题",),
                workspace_root=str(workspace_root),
            )
            record_stage_signoff(
                "IPD-003",
                stage_key="discovery",
                role="CEOChiefOfStaff",
                workspace_root=str(workspace_root),
            )
            result = record_stage_signoff(
                "IPD-003",
                stage_key="discovery",
                role="CEO",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["currentStageKey"], "intelligence")

    def test_ceo_cannot_sign_before_chief_of_staff_on_stage_or_intake(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-003A",
                title="签核顺序",
                objective="验证总助先签、CEO 后签",
                task_description="验证签核顺序门禁。",
                created_by="CEO",
                workspace_root=str(workspace_root),
            )
            with self.assertRaisesRegex(ValueError, "CEO cannot sign before CEOChiefOfStaff"):
                record_intake_signoff("IPD-003A", role="CEO", workspace_root=str(workspace_root))

            record_intake_signoff("IPD-003A", role="CEOChiefOfStaff", workspace_root=str(workspace_root))
            record_intake_signoff("IPD-003A", role="CEO", workspace_root=str(workspace_root))
            submit_stage_output(
                "IPD-003A",
                stage_key="discovery",
                submitted_by="CEOChiefOfStaff",
                summary="discovery package 已提交",
                workspace_root=str(workspace_root),
            )
            with self.assertRaisesRegex(ValueError, "CEO cannot sign before CEOChiefOfStaff"):
                record_stage_signoff(
                    "IPD-003A",
                    stage_key="discovery",
                    role="CEO",
                    workspace_root=str(workspace_root),
                )

    def test_checkpoint_task_can_reconcile_ipd_case_and_emit_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-004",
                title="checkpoint bridge",
                objective="让 checkpoint 能重算 IPD case",
                task_description="验证 checkpointKind=ipd-case-step。",
                workspace_root=str(workspace_root),
            )
            result = run_checkpoint_task(
                checkpoint_id="ipd-case-step",
                task_config={
                    "checkpointKind": "ipd-case-step",
                    "caseId": "IPD-004",
                },
                workspace_root=str(workspace_root),
                trigger_mode="scheduled",
            )
            self.assertEqual(result["status"], "completed")
            artifact_path = Path(result["artifactPaths"][0])
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(artifact["checkpointKind"], "ipd-case-step")
            self.assertEqual(artifact["reconciledCaseCount"], 1)
            self.assertEqual(artifact["cases"][0]["caseId"], "IPD-004")
            self.assertTrue(artifact_path.exists())
            self.assertTrue(chief_of_staff_audit_root(workspace_root).exists())

    def test_cli_status_outputs_case_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-005",
                title="CLI 状态",
                objective="验证 CLI status",
                task_description="输出 case snapshot",
                workspace_root=str(workspace_root),
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "status",
                        "--case-id",
                        "IPD-005",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["caseId"], "IPD-005")
            self.assertTrue((chief_of_staff_ipd_case_root("IPD-005", workspace_root) / "case.json").exists())

    def test_cli_task_intake_initializes_intake_briefing_from_freeform_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "task-intake",
                        "--workspace-root",
                        str(workspace_root),
                        "做一个自动化开发软件，在公司级别从下发任务到总助评估分派各部门，部分负责人细化，按公司流程有序进行开发和交付，验收，长期运维",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["caseId"].startswith("IPD-"))
            case_root = chief_of_staff_ipd_case_root(payload["caseId"], workspace_root)
            self.assertTrue((case_root / "case.json").exists())
            intake_brief = json.loads((case_root / "intake-brief.json").read_text(encoding="utf-8"))
            self.assertIn("CEO / 总助正式下发任务", intake_brief["briefing"]["opportunitySignals"][0])
            self.assertEqual(
                intake_brief["briefing"]["ownerProposal"],
                ["总助先把任务转成 intake briefing；CMO / COO / CFO / CPO / CTO 再按节点继续细化。"],
            )

    def test_init_can_refine_existing_work_task_case_before_ceo_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            ipd_case_main(
                [
                    "task-intake",
                    "--case-id",
                    "IPD-006",
                    "--workspace-root",
                    str(workspace_root),
                    "下发任务到总助先做粗线条评估",
                ]
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "init",
                        "--case-id",
                        "IPD-006",
                        "--title",
                        "自动化开发执行闭环",
                        "--objective",
                        "建立从 CEO 任务到交付收口的最小 IPD 引擎",
                        "--task-description",
                        "CEO 和总助只提总要求，后续由各个 O 细化推进。",
                        "--opportunity-signal",
                        "AI coding 与 agent workflow 正在成为明显增量热点。",
                        "--business-model-fit",
                        "符合当前小成本先跑通可收费闭环、先验证再扩大的路线。",
                        "--stage-fit",
                        "符合当前 Copilot-host 正式接管阶段，先验证公司级最小 workflow slice。",
                        "--company-context",
                        "TriCompany 已有最小 IPD runtime slice，可先跑通公司级流程闭环。",
                        "--owner-proposal",
                        "总助先做入口 briefing，CMO/COO/CFO/CPO/CTO 再按节点继续细化。",
                        "--resource-envelope",
                        "预计 CTO / TriDev 首轮投入 2-3 人天，当前主要为时间与工具试验成本。",
                        "--prerequisite",
                        "CEO 确认进入 IPD 主动交付线。",
                        "--required-support",
                        "CMO / COO / CFO / CPO / CTO 需按节点补齐专业判断。",
                        "--expected-outcome",
                        "形成一条可重复运行的最小 IPD 闭环。",
                        "--related-module",
                        "TriCompany",
                        "--related-module",
                        "TriDev",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["caseId"], "IPD-006")
            case_payload = read_ipd_case("IPD-006", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["title"], "自动化开发执行闭环")
            self.assertEqual(case_payload["intake"]["businessModelFit"], ["符合当前小成本先跑通可收费闭环、先验证再扩大的路线。"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
