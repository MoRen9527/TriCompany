from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import runtime.cognition.ipd_case_engine as ipd_case_engine_module
from runtime.cognition.chief_of_staff_ipd_case import (
    _infer_related_modules,
    _resolve_related_modules,
    main as ipd_case_main,
)
from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_ipd_case_root
from runtime.cognition.ipd_case_engine import (
    _draft_template,
    _stage_standard_flow,
    freeze_ipd_case,
    initialize_ipd_case,
    read_ipd_case,
    record_intake_signoff,
    rollback_ipd_case,
    record_stage_signoff,
    run_discovery_stage_automation,
    run_intelligence_stage_automation,
    run_case_autopilot,
    submit_stage_output,
    unfreeze_ipd_case,
)
from runtime.cognition.tasks.checkpoint_task import run_checkpoint_task


class ChiefOfStaffIpdCaseValidationTest(unittest.TestCase):
    def _full_slot_answers(self) -> dict[str, str]:
        return {
            "competitorReference": "Cursor、Devin、Linear",
            "targetUserScenario": "先服务 CEOChiefOfStaff 与产品/技术负责人，验证公司级研发任务分派场景",
            "deliveryWindow": "先在 1 周内完成 Discovery、Intelligence 和 PRD 验证",
            "budgetGuardrail": "首轮只允许现有人力和少量工具试验成本",
            "successMetric": "证明 IPD 能控制住入口补槽、任务分派和 Discovery/Intelligence 路由",
            "mustHaveScope": "首轮必须交付 intake briefing、Discovery/Intelligence work item 与 owner-action package",
            "explicitOutOfScope": "不涉及正式宿主切换、不涉及链上实现、不涉及大规模运营自动化",
        }

    def _platform_slot_answers(self) -> dict[str, str]:
        return {
            "competitorReference": "OpenAI API Platform、OpenRouter、One API",
            "targetUserScenario": "先服务内部产品负责人和技术负责人，验证统一模型 API 平台入口",
            "deliveryWindow": "1 周内完成 Discovery 与 Intelligence",
            "budgetGuardrail": "首轮只允许现有人力和少量工具试验成本",
            "successMetric": "自动形成 discovery / intelligence markdown package",
            "mustHaveScope": "自动形成 discovery / intelligence markdown package 并可提交 stage output",
            "explicitOutOfScope": "不涉及正式宿主切换",
        }

    def _platform_carry_forward_slot_answers(self) -> dict[str, str]:
        return {
            "competitorReference": "LiteLLM、sub2api、OpenRouter、OpenAI API Platform",
            "targetUserScenario": "先服务内部产品负责人和技术负责人，验证统一模型 API 平台入口",
            "deliveryWindow": "1 周内完成 Discovery 与 Intelligence",
            "budgetGuardrail": "首轮只允许现有人力和少量工具试验成本",
            "successMetric": "自动形成 discovery markdown package，并保证 seeded competitors 不静默丢失",
            "mustHaveScope": "TriAvatar 前端入口保持原有功能可用；TriStaciss 后端完成模型 API 转接平台首版主线；自动形成 discovery markdown package 并完成 carry-forward 守门",
            "explicitOutOfScope": "不涉及正式宿主切换",
        }

    def _initialize_clarified_case(self, workspace_root: Path, case_id: str) -> None:
        initialize_ipd_case(
            case_id=case_id,
            title="自动化开发执行闭环",
            objective="验证入口补槽、专业判断与冻结阻塞",
            task_description="CEO 提需求，总助补槽后再分派给 CMO/CPO/CTO/COO/CFO。",
            slot_answers=self._full_slot_answers(),
            require_clarification_slots=True,
            workspace_root=str(workspace_root),
        )

    def _initialize_platform_case(self, workspace_root: Path, case_id: str) -> None:
        initialize_ipd_case(
            case_id=case_id,
            title="完整模型 API 平台 MVP 回放",
            objective="验证 discovery / intelligence 自动执行器",
            task_description="围绕完整模型 API 平台 MVP 做 discovery 和 intelligence 自动研究。",
            slot_answers=self._platform_slot_answers(),
            require_clarification_slots=True,
            workspace_root=str(workspace_root),
        )

    def _initialize_platform_carry_forward_case(self, workspace_root: Path, case_id: str) -> None:
        initialize_ipd_case(
            case_id=case_id,
            title="模型 API 平台 carry-forward 守门验证",
            objective="以 TriAvatar 作为现役前端入口、TriStaciss 作为后端模型 API 转接平台真源，验证 Discovery seeded competitor carry-forward guard。",
            task_description="围绕模型 API 平台 Discovery 自动化验证 seeded competitors 是否被完整带入后续引用，并保留 TriAvatar / TriStaciss 的当前项目边界输入。",
            slot_answers=self._platform_carry_forward_slot_answers(),
            require_clarification_slots=True,
            workspace_root=str(workspace_root),
        )

    def _approve_intake(self, workspace_root: Path, case_id: str) -> dict[str, object]:
        record_intake_signoff(case_id, role="CEO", workspace_root=str(workspace_root))
        return record_intake_signoff(case_id, role="CEOChiefOfStaff", workspace_root=str(workspace_root))

    def _approve_stage(
        self,
        workspace_root: Path,
        case_id: str,
        stage_key: str,
        *,
        ceo_decision: str = "approved",
        ceo_note: str = "",
        chief_decision: str = "approved",
        chief_note: str = "",
    ) -> dict[str, object]:
        record_stage_signoff(
            case_id,
            stage_key=stage_key,
            role="CEO",
            decision=ceo_decision,
            note=ceo_note,
            workspace_root=str(workspace_root),
        )
        return record_stage_signoff(
            case_id,
            stage_key=stage_key,
            role="CEOChiefOfStaff",
            decision=chief_decision,
            note=chief_note,
            workspace_root=str(workspace_root),
        )

    def _advance_case_to_intelligence(self, workspace_root: Path, case_id: str) -> None:
        self._initialize_clarified_case(workspace_root, case_id)
        self._approve_intake(workspace_root, case_id)
        submit_stage_output(
            case_id,
            stage_key="discovery",
            submitted_by="ChiefProductOfficer",
            summary="Discovery 已提交",
            evidence=("manual/discovery-reference-pack.json",),
            workspace_root=str(workspace_root),
        )
        self._approve_stage(workspace_root, case_id, "discovery")

    def _advance_platform_case_to_intelligence(self, workspace_root: Path, case_id: str) -> None:
        self._initialize_platform_case(workspace_root, case_id)
        self._approve_intake(workspace_root, case_id)
        submit_stage_output(
            case_id,
            stage_key="discovery",
            submitted_by="ChiefProductOfficer",
            summary="Discovery 已提交",
            evidence=("manual/discovery-reference-pack.json",),
            workspace_root=str(workspace_root),
        )
        self._approve_stage(workspace_root, case_id, "discovery")

    def test_intake_signatures_and_release_version_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-SIGN-INTAKE-001")

            result = self._approve_intake(workspace_root, "IPD-SIGN-INTAKE-001")
            self.assertEqual(result["status"], "waiting-stage-output")
            intake_brief = json.loads(
                (chief_of_staff_ipd_case_root("IPD-SIGN-INTAKE-001", workspace_root) / "intake-brief.json").read_text(encoding="utf-8")
            )
            self.assertEqual(intake_brief["requiredApprovers"], ["CEO", "CEOChiefOfStaff"])
            self.assertTrue(intake_brief["packageHash"].startswith("0x"))
            self.assertEqual(intake_brief["release"]["status"], "issued")
            self.assertEqual(intake_brief["release"]["version"], "IPD-SIGN-INTAKE-001-INTAKE-V001")
            self.assertEqual([item["role"] for item in intake_brief["signatureChain"]], ["CEO", "CEOChiefOfStaff"])
            self.assertEqual(intake_brief["signatureChain"][0]["verificationStatus"], "not-required")
            self.assertEqual(intake_brief["signatureChain"][1]["verifiedRoles"], ["CEO"])
            self.assertTrue(intake_brief["signatureChain"][0]["signerAddress"].startswith("0x"))

    def test_stage_output_signature_chain_and_release_version_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-SIGN-STAGE-001")
            self._approve_intake(workspace_root, "IPD-SIGN-STAGE-001")

            submit_stage_output(
                "IPD-SIGN-STAGE-001",
                stage_key="discovery",
                submitted_by="ChiefProductOfficer",
                summary="Discovery 已提交",
                evidence=("manual/discovery-reference-pack.json",),
                workspace_root=str(workspace_root),
            )
            pending_output = json.loads(
                (chief_of_staff_ipd_case_root("IPD-SIGN-STAGE-001", workspace_root) / "outputs" / "01-discovery.json").read_text(encoding="utf-8")
            )
            self.assertEqual([item["role"] for item in pending_output["signatureChain"]], ["ChiefProductOfficer", "CEO", "CEOChiefOfStaff"])
            self.assertEqual(pending_output["signatureChain"][0]["status"], "approved")
            self.assertEqual(pending_output["signatureChain"][0]["verificationStatus"], "not-required")
            self.assertEqual(pending_output["release"]["status"], "draft")

            result = self._approve_stage(workspace_root, "IPD-SIGN-STAGE-001", "discovery")
            self.assertEqual(result["currentStageKey"], "intelligence")
            stage_output = json.loads(
                (chief_of_staff_ipd_case_root("IPD-SIGN-STAGE-001", workspace_root) / "outputs" / "01-discovery.json").read_text(encoding="utf-8")
            )
            self.assertEqual(stage_output["release"]["status"], "issued")
            self.assertEqual(stage_output["release"]["version"], "IPD-SIGN-STAGE-001-DISCOVERY-V001")
            self.assertEqual(stage_output["signatureChain"][1]["verifiedRoles"], ["ChiefProductOfficer"])
            self.assertEqual(stage_output["signatureChain"][2]["verifiedRoles"], ["ChiefProductOfficer", "CEO"])
            self.assertTrue(stage_output["signatureChain"][2]["publicKey"].startswith("0x04"))

    def test_cli_signing_arguments_drive_intake_and_stage_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-CLI-SIGN-001")
            private_key = "0x" + ("11" * 32)
            commands = [
                [
                    "intake-approve",
                    "--case-id",
                    "IPD-CLI-SIGN-001",
                    "--role",
                    "CEO",
                    "--decision",
                    "approved",
                    "--mnemonic",
                    "ceo intake signature chain release package owner proof company review hash verify",
                    "--workspace-root",
                    str(workspace_root),
                ],
                [
                    "intake-approve",
                    "--case-id",
                    "IPD-CLI-SIGN-001",
                    "--role",
                    "CEOChiefOfStaff",
                    "--decision",
                    "approved",
                    "--signing-key",
                    private_key,
                    "--workspace-root",
                    str(workspace_root),
                ],
                [
                    "submit",
                    "--case-id",
                    "IPD-CLI-SIGN-001",
                    "--stage-key",
                    "discovery",
                    "--submitted-by",
                    "ChiefProductOfficer",
                    "--summary",
                    "Discovery 已提交",
                    "--evidence",
                    "manual/discovery-reference-pack.json",
                    "--mnemonic",
                    "owner discovery package hash signature flow release check company stage evidence verify",
                    "--workspace-root",
                    str(workspace_root),
                ],
                [
                    "signoff",
                    "--case-id",
                    "IPD-CLI-SIGN-001",
                    "--stage-key",
                    "discovery",
                    "--role",
                    "CEO",
                    "--decision",
                    "approved",
                    "--signing-key",
                    private_key,
                    "--workspace-root",
                    str(workspace_root),
                ],
                [
                    "signoff",
                    "--case-id",
                    "IPD-CLI-SIGN-001",
                    "--stage-key",
                    "discovery",
                    "--role",
                    "CEOChiefOfStaff",
                    "--decision",
                    "approved",
                    "--mnemonic",
                    "chief verify ceo signature and issue release version company final approval hash",
                    "--workspace-root",
                    str(workspace_root),
                ],
            ]
            for argv in commands:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = ipd_case_main(argv)
                self.assertEqual(exit_code, 0)

            payload = read_ipd_case("IPD-CLI-SIGN-001", workspace_root=str(workspace_root))
            self.assertEqual(payload["currentStageKey"], "intelligence")
            discovery_stage = next(stage for stage in payload["stages"] if stage["stageKey"] == "discovery")
            self.assertEqual(discovery_stage["releaseVersion"], "IPD-CLI-SIGN-001-DISCOVERY-V001")
            self.assertEqual(discovery_stage["releaseStatus"], "issued")

    def test_source_workspace_writes_ipd_case_into_support_root_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            source_root = workspace_root / "TriCompany"
            support_root = workspace_root / "TriMetaverse" / "TriCompany-copilot-host-assets"
            (source_root / ".github").mkdir(parents=True, exist_ok=True)
            (source_root / "runtime").mkdir(parents=True, exist_ok=True)
            support_root.mkdir(parents=True, exist_ok=True)

            initialize_ipd_case(
                case_id="IPD-SUPPORT-001",
                title="support root",
                objective="验证动态 IPD case 落到 support root",
                task_description="把总助动态运营数据写入 support root，而不是 source knowledge 目录。",
                workspace_root=str(source_root),
            )

            case_root = chief_of_staff_ipd_case_root("IPD-SUPPORT-001", source_root)
            self.assertTrue(case_root.is_dir())
            self.assertEqual(case_root.parent.parent.parent, support_root / "knowledge" / "employees" / "ceo-chief-of-staff" / "workbench")
            self.assertFalse((source_root / "knowledge" / "employees" / "ceo-chief-of-staff" / "workbench" / "ipd" / "cases" / "IPD-SUPPORT-001").exists())

    def test_task_intake_auto_generates_date_slug_case_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "task-intake",
                        "--workspace-root",
                        str(workspace_root),
                        "做一个完整模型 API 平台 MVP，用于验证 discovery 与 intelligence 的自动资料生成。",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertRegex(payload["caseId"], r"^IPD-\d{8}-PLATFORM-001$")

    def test_infer_related_modules_uses_central_module_map_for_platform_tasks(self) -> None:
        modules = _infer_related_modules(
            "做一个完整模型 API 平台，包含 Web 前端聊天入口、多 provider 模型路由、测试验收和部署上线。"
        )

        self.assertEqual(modules[0], "TriCompany")
        self.assertIn("TriStaciss", modules)
        self.assertIn("TriAvatar", modules)
        self.assertIn("TriDev", modules)
        self.assertIn("TriTest", modules)
        self.assertIn("TriDeployment", modules)

    def test_infer_related_modules_adds_pc_host_and_local_runtime_stack(self) -> None:
        modules = _infer_related_modules(
            "做一个本地 copilot-host IDE 扩展和 CLI 协同工具，支持多 host 切换与本地域节点执行。"
        )

        self.assertEqual(modules[0], "TriCompany")
        self.assertIn("TriHost", modules)
        self.assertIn("TriMC", modules)
        self.assertIn("TriPilot", modules)
        self.assertIn("Tride", modules)
        self.assertIn("vscodium", modules)
        self.assertIn("TriLC", modules)

    def test_task_intake_default_auto_uses_cpo_module_router_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            with (
                mock.patch("runtime.cognition.chief_of_staff_ipd_case._cpo_module_router_is_configured", return_value=True),
                mock.patch(
                    "runtime.cognition.chief_of_staff_ipd_case._invoke_cpo_module_router",
                    return_value=("TriCompany", "TriMem", "TriWeb4"),
                ) as cpo_router,
            ):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = ipd_case_main(
                        [
                            "task-intake",
                            "--case-id",
                            "IPD-CPO-ROUTING-001",
                            "--workspace-root",
                            str(workspace_root),
                            "做一个用户身份绑定和钱包合约交互的产品入口。",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            cpo_router.assert_called_once()
            case_payload = read_ipd_case("IPD-CPO-ROUTING-001", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["relatedModules"], ["TriCompany", "TriMem", "TriWeb4"])

    def test_task_intake_deterministic_mode_skips_cpo_module_router(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            with mock.patch(
                "runtime.cognition.chief_of_staff_ipd_case._invoke_cpo_module_router",
                side_effect=AssertionError("CPO router should not be called"),
            ):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = ipd_case_main(
                        [
                            "task-intake",
                            "--case-id",
                            "IPD-DETERMINISTIC-ROUTING-001",
                            "--module-routing-mode",
                            "deterministic",
                            "--workspace-root",
                            str(workspace_root),
                            "做一个完整模型 API 平台，包含 Web 前端、测试验收和部署上线。",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            case_payload = read_ipd_case("IPD-DETERMINISTIC-ROUTING-001", workspace_root=str(workspace_root))
            self.assertIn("TriStaciss", case_payload["relatedModules"])
            self.assertIn("TriAvatar", case_payload["relatedModules"])
            self.assertIn("TriTest", case_payload["relatedModules"])
            self.assertIn("TriDeployment", case_payload["relatedModules"])

    def test_cpo_module_routing_mode_requires_configured_router(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "CPO module routing failed"):
                _resolve_related_modules("做一个用户身份绑定入口。", mode="cpo")

    def test_intake_approvals_start_first_stage_and_generate_discovery_work_item(self) -> None:
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
            self.assertEqual(result["entryCheckpoint"], "ceo-demand")
            result = self._approve_intake(workspace_root, "IPD-001")
            self.assertEqual(result["status"], "waiting-stage-output")
            self.assertEqual(result["currentStageKey"], "discovery")
            self.assertEqual(result["entryCheckpoint"], "task-dispatch")

            case_payload = read_ipd_case("IPD-001", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["entryCheckpoint"], "task-dispatch")
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
                ["CEO", "CEOChiefOfStaff"],
            )
            current_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            work_item_path = Path(current_stage["workItemPath"])
            self.assertTrue(work_item_path.exists())
            work_item = json.loads(work_item_path.read_text(encoding="utf-8"))
            self.assertEqual(work_item["businessOwner"], "ChiefProductOfficer")
            self.assertEqual(work_item["actingOwner"], "ChiefProductOfficer")
            self.assertEqual(work_item["moduleExecutor"], "TriDev")
            self.assertEqual(work_item["gateOwner"], "ChiefProductOfficer")
            self.assertEqual(work_item["ownerRole"], "ChiefProductOfficer")
            self.assertEqual(work_item["phaseKey"], "DISCOVERY")
            self.assertEqual(work_item["schemaHint"]["objectType"], "IPD_DISCOVERY_PACKAGE")
            self.assertEqual(work_item["draftTemplate"]["objectType"], "IPD_DISCOVERY_PACKAGE")
            self.assertEqual(work_item["standardFlow"]["referenceRoot"], "TriMetaverse/reference/discovery/IPD-001")
            self.assertEqual(
                work_item["standardFlow"]["summaryDocument"]["path"],
                "TriMetaverse/reference/discovery/IPD-001/discovery-reference-functional-brief.md",
            )
            self.assertEqual(
                [document["name"] for document in work_item["standardFlow"]["packageDocuments"]],
                [
                    "DiscoveryCompetitorLandscape",
                    "DiscoveryCommonCapabilityMatrix",
                    "DiscoveryHighlightOpportunityMemo",
                ],
            )
            self.assertIn(
                "reference-source-catalog.json",
                work_item["standardFlow"]["catalogPath"],
            )
            discovery_reference_root = workspace_root / "TriMetaverse" / "reference" / "discovery" / "IPD-001"
            self.assertTrue((discovery_reference_root / "reference-source-catalog.json").exists())
            self.assertTrue((discovery_reference_root / "discovery-reference-functional-brief.md").exists())
            self.assertTrue((discovery_reference_root / "discovery-competitor-landscape.md").exists())
            self.assertTrue((discovery_reference_root / "discovery-common-capability-matrix.md").exists())
            self.assertTrue((discovery_reference_root / "discovery-highlight-opportunity-memo.md").exists())
            self.assertEqual(
                work_item["participantRoles"],
                ["CEOChiefOfStaff", "CEO", "ChiefMarketingOfficer", "ChiefTechnologyOfficer"],
            )
            self.assertEqual(work_item["intake"]["briefPath"], intake_brief_path.as_posix())
            self.assertIn("workbench/ipd/cases/IPD-001/intake-brief.json", work_item["inputRefs"])
            self.assertEqual(work_item["requiredApprovers"], ["ChiefProductOfficer", "CEO", "CEOChiefOfStaff"])

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
            self._approve_intake(workspace_root, "IPD-002")

            case_payload = read_ipd_case("IPD-002", workspace_root=str(workspace_root))
            while case_payload["status"] != "completed":
                stage_key = case_payload["currentStageKey"]
                stage = next(item for item in case_payload["stages"] if item["stageKey"] == stage_key)
                evidence_refs = [f"evidence/{stage_key}.md"]
                if stage_key in {"coding", "verify-integration", "redteam", "qa", "deployment", "assurance", "delivery"}:
                    evidence_refs = [f"TriDev/src/{stage_key}_evidence.py"]
                submit_stage_output(
                    "IPD-002",
                    stage_key=stage_key,
                    submitted_by=stage["actingOwner"],
                    summary=f"{stage_key} 已提交",
                    details=(f"{stage_key} 细化结果",),
                    evidence=evidence_refs,
                    workspace_root=str(workspace_root),
                )
                result = self._approve_stage(workspace_root, "IPD-002", stage_key)
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
            self._approve_intake(workspace_root, "IPD-003")
            submit_stage_output(
                "IPD-003",
                stage_key="discovery",
                submitted_by="ChiefProductOfficer",
                summary="首版 discovery package",
                workspace_root=str(workspace_root),
            )
            record_stage_signoff(
                "IPD-003",
                stage_key="discovery",
                role="CEO",
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
                submitted_by="ChiefProductOfficer",
                summary="二版 discovery package",
                details=("补充任务边界、raw evidence 和后续待验证问题",),
                workspace_root=str(workspace_root),
            )
            result = self._approve_stage(workspace_root, "IPD-003", "discovery")
            self.assertEqual(result["currentStageKey"], "intelligence")

            case_payload = read_ipd_case("IPD-003", workspace_root=str(workspace_root))
            intelligence_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "intelligence")
            intelligence_work_item = json.loads(Path(intelligence_stage["workItemPath"]).read_text(encoding="utf-8"))
            self.assertEqual(intelligence_work_item["standardFlow"]["referenceRoot"], "TriMetaverse/reference/intelligence/IPD-003")
            self.assertEqual(
                intelligence_work_item["standardFlow"]["analysisDocument"]["path"],
                "TriMetaverse/reference/intelligence/IPD-003/intelligence-capability-extraction-matrix.md",
            )
            self.assertEqual(
                [document["name"] for document in intelligence_work_item["standardFlow"]["packageDocuments"]],
                [
                    "IntelligenceOpenSourceLandscape",
                    "IntelligenceCodegraphAnalysis",
                    "IntelligenceArchitectureOptionMemo",
                ],
            )
            self.assertIn(
                "CodeGraph",
                " ".join(intelligence_work_item["standardFlow"]["requiredActions"]),
            )
            intelligence_reference_root = workspace_root / "TriMetaverse" / "reference" / "intelligence" / "IPD-003"
            self.assertTrue((intelligence_reference_root / "reference-source-catalog.json").exists())
            self.assertTrue((intelligence_reference_root / "intelligence-capability-extraction-matrix.md").exists())
            self.assertTrue((intelligence_reference_root / "intelligence-opensource-landscape.md").exists())
            self.assertTrue((intelligence_reference_root / "intelligence-codegraph-analysis.md").exists())
            self.assertTrue((intelligence_reference_root / "intelligence-architecture-option-memo.md").exists())

    def test_rollback_reactivates_target_stage_and_resets_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-ROLLBACK-001",
                title="rollback",
                objective="验证 case rollback",
                task_description="把已推进到 designing 的 case 回退到 discovery。",
                workspace_root=str(workspace_root),
            )
            self._approve_intake(workspace_root, "IPD-ROLLBACK-001")

            for stage_key, owner_role in (
                ("discovery", "ChiefProductOfficer"),
                ("intelligence", "ChiefProductOfficer"),
            ):
                submit_stage_output(
                    "IPD-ROLLBACK-001",
                    stage_key=stage_key,
                    submitted_by=owner_role,
                    summary=f"{stage_key} 已提交",
                    evidence=(f"manual/{stage_key}.json",),
                    workspace_root=str(workspace_root),
                )
                self._approve_stage(workspace_root, "IPD-ROLLBACK-001", stage_key)

            result = rollback_ipd_case(
                "IPD-ROLLBACK-001",
                stage_key="discovery",
                reason="需要重写范围和完整 PRD 前的 discovery 边界。",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["currentStageKey"], "discovery")
            self.assertEqual(result["rollbackTargetStageKey"], "discovery")
            self.assertEqual(result["previousStageKey"], "designing")
            self.assertEqual(result["status"], "waiting-stage-output")
            self.assertEqual(result["resetStageKeys"], ["discovery", "intelligence", "designing", "coding", "verify-integration", "redteam", "qa", "deployment", "assurance", "delivery"])

            case_payload = read_ipd_case("IPD-ROLLBACK-001", workspace_root=str(workspace_root))
            discovery_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            intelligence_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "intelligence")
            self.assertEqual(case_payload["status"], "waiting-stage-output")
            self.assertEqual(case_payload["currentStageKey"], "discovery")
            self.assertEqual(discovery_stage["status"], "in-progress")
            self.assertEqual(discovery_stage["outputPath"], "")
            self.assertTrue(discovery_stage["workItemPath"].endswith("01-discovery.json"))
            self.assertEqual(intelligence_stage["status"], "pending")
            self.assertEqual(intelligence_stage["outputPath"], "")

    def test_rollback_to_ceo_demand_resets_case_to_intake_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._advance_case_to_intelligence(workspace_root, "IPD-ROLLBACK-INTAKE-001")

            result = rollback_ipd_case(
                "IPD-ROLLBACK-INTAKE-001",
                stage_key="ceo-demand",
                reason="需要回到 CEO 提需求重新确认任务边界。",
                workspace_root=str(workspace_root),
            )

            self.assertEqual(result["rollbackTargetNodeKey"], "ceo-demand")
            self.assertEqual(result["rollbackTargetNodeType"], "ceo-demand")
            self.assertEqual(result["rollbackTargetStageKey"], "")
            self.assertEqual(result["status"], "awaiting-intake-approvals")
            self.assertEqual(result["currentStageKey"], "")
            self.assertEqual(
                result["resetStageKeys"],
                ["discovery", "intelligence", "designing", "coding", "verify-integration", "redteam", "qa", "deployment", "assurance", "delivery"],
            )

            case_payload = read_ipd_case("IPD-ROLLBACK-INTAKE-001", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["status"], "awaiting-intake-approvals")
            self.assertEqual(case_payload["currentStageKey"], "")
            self.assertEqual(case_payload["currentWorkItemPath"], "")
            self.assertTrue(all(stage["status"] == "pending" for stage in case_payload["stages"]))
            intake_approvals = {item["role"]: item["status"] for item in case_payload["intake"]["approvals"]}
            self.assertEqual(intake_approvals["CEOChiefOfStaff"], "pending")
            self.assertEqual(intake_approvals["CEO"], "pending")

    def test_rollback_to_task_dispatch_alias_reactivates_discovery_dispatch_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._advance_case_to_intelligence(workspace_root, "IPD-ROLLBACK-DISPATCH-001")

            result = rollback_ipd_case(
                "IPD-ROLLBACK-DISPATCH-001",
                stage_key="task-dispatch",
                reason="需要回到总助分派后的 Discovery 接单节点。",
                workspace_root=str(workspace_root),
            )

            self.assertEqual(result["rollbackTargetNodeKey"], "task-dispatch")
            self.assertEqual(result["rollbackTargetNodeType"], "task-dispatch")
            self.assertEqual(result["rollbackTargetStageKey"], "discovery")
            self.assertEqual(result["status"], "waiting-stage-output")
            self.assertEqual(result["currentStageKey"], "discovery")

            case_payload = read_ipd_case("IPD-ROLLBACK-DISPATCH-001", workspace_root=str(workspace_root))
            discovery_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            self.assertEqual(case_payload["status"], "waiting-stage-output")
            self.assertEqual(discovery_stage["status"], "in-progress")
            self.assertTrue(discovery_stage["workItemPath"].endswith("01-discovery.json"))

    def test_cli_rollback_outputs_reactivated_case_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-ROLLBACK-CLI-001",
                title="rollback cli",
                objective="验证 CLI rollback",
                task_description="通过 CLI 回退 case。",
                workspace_root=str(workspace_root),
            )
            self._approve_intake(workspace_root, "IPD-ROLLBACK-CLI-001")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "rollback",
                        "--case-id",
                        "IPD-ROLLBACK-CLI-001",
                        "--stage-key",
                        "discovery",
                        "--reason",
                        "重新测试完整 IPD 流程。",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["currentStageKey"], "discovery")
            self.assertEqual(payload["rollbackTargetStageKey"], "discovery")
            self.assertEqual(payload["status"], "waiting-stage-output")

    def test_cli_rollback_to_ceo_demand_outputs_intake_checkpoint_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._advance_case_to_intelligence(workspace_root, "IPD-ROLLBACK-CLI-INTAKE-001")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "rollback",
                        "--case-id",
                        "IPD-ROLLBACK-CLI-INTAKE-001",
                        "--stage-key",
                        "ceo-demand",
                        "--reason",
                        "重新回到 CEO 提需求阶段。",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["rollbackTargetNodeKey"], "ceo-demand")
            self.assertEqual(payload["currentStageKey"], "")
            self.assertEqual(payload["status"], "awaiting-intake-approvals")

    def test_autopilot_pauses_for_owner_action_before_stage_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-AUTO-001",
                title="autopilot",
                objective="自动推进",
                task_description="验证 autopilot 默认先停在 CPO/CTO owner action。",
                workspace_root=str(workspace_root),
            )
            result = run_case_autopilot(
                "IPD-AUTO-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
            )
            self.assertEqual(result["status"], "paused-owner-action")
            self.assertEqual(result["entryCheckpoint"], "task-dispatch")
            self.assertEqual(result["pendingRole"], "ChiefProductOfficer")
            self.assertEqual(result["pendingStageKey"], "discovery")
            self.assertEqual(result["caseStatus"], "waiting-stage-output")
            self.assertEqual(result["completedStageCount"], 0)
            case_payload = read_ipd_case("IPD-AUTO-001", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["status"], "waiting-stage-output")
            self.assertEqual(case_payload["currentStageKey"], "discovery")
            case_root = chief_of_staff_ipd_case_root("IPD-AUTO-001", workspace_root)
            owner_action_path = case_root / "owner-action-packages" / "01-discovery.json"
            self.assertTrue(owner_action_path.exists())
            self.assertFalse((case_root / "participant-records").exists())
            self.assertFalse((case_root / "autopilot-packages").exists())
            owner_action = json.loads(owner_action_path.read_text(encoding="utf-8"))
            self.assertEqual(owner_action["workItemRef"], "workbench/ipd/cases/IPD-AUTO-001/work-items/01-discovery.json")
            self.assertEqual(owner_action["intakeBriefRef"], "workbench/ipd/cases/IPD-AUTO-001/intake-brief.json")
            self.assertEqual(
                owner_action["inputRefs"],
                [
                    "workbench/ipd/cases/IPD-AUTO-001/intake-brief.json",
                    "workbench/ipd/cases/IPD-AUTO-001/case.json",
                ],
            )
            self.assertEqual(owner_action["draftTemplate"]["objectType"], "IPD_DISCOVERY_PACKAGE")
            self.assertEqual(owner_action["submissionTemplate"]["submittedBy"], "ChiefProductOfficer")
            self.assertEqual(owner_action["standardFlow"]["referenceRoot"], "TriMetaverse/reference/discovery/IPD-AUTO-001")
            self.assertIn(
                "TriMetaverse/reference/discovery/IPD-AUTO-001/reference-source-catalog.json",
                owner_action["submissionTemplate"]["evidence"],
            )
            self.assertIn(
                "提交前必须完成 reference-source-catalog.json、discovery-reference-functional-brief.md，以及竞品/共性功能/亮点功能三份 markdown package。",
                owner_action["handoffChecklist"],
            )
            self.assertIn("chief_of_staff_ipd_case discovery", owner_action["recommendedCommands"][0])
            self.assertIn("--object-path <primary-output-object-path>", owner_action["recommendedCommands"][1])
            self.assertIn("chief_of_staff_ipd_case freeze", owner_action["recommendedCommands"][2])
            self.assertIn("chief_of_staff_ipd_case unfreeze", owner_action["recommendedCommands"][3])
            self.assertIn("<freeze-role-or-CEOChiefOfStaff>", owner_action["recommendedCommands"][3])
            self.assertNotIn("tridevOwnerAdapterBundle", owner_action)

    def test_designing_qa_assurance_templates_expose_scorecard_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-TEMPLATE-001",
                title="template schema",
                objective="验证 designing/qa/assurance 模板字段和评分卡 schema",
                task_description="补齐后续阶段模板字段和 scorecard schema。",
                slot_answers=self._platform_slot_answers(),
                require_clarification_slots=True,
                workspace_root=str(workspace_root),
            )
            case_payload = read_ipd_case("IPD-TEMPLATE-001", workspace_root=str(workspace_root))
            stages = {stage["stageKey"]: stage for stage in case_payload["stages"]}

            designing_flow = _stage_standard_flow(case_payload, stages["designing"])
            self.assertEqual(
                [document["name"] for document in designing_flow["packageDocuments"]],
                [
                    "DesignArchitectureDecisionRecord",
                    "DesignTestBaseline",
                    "DesignSecurityAndRedteamMemo",
                    "DesignPhaseHandoffPlan",
                ],
            )
            designing_draft = _draft_template(case_payload, stages["designing"], written_at="2026-06-14T00:00:00+08:00")
            self.assertEqual(designing_draft["objectType"], "IPD_DESIGN_PACKAGE")
            self.assertIn("designArtifacts", designing_draft["templateFields"])
            self.assertEqual(designing_draft["scorecardSchema"]["schemaName"], "DesignReviewScorecard")
            self.assertEqual(
                [item["key"] for item in designing_draft["scorecardSchema"]["dimensions"]],
                [
                    "architecture-clarity",
                    "contract-completeness",
                    "testability",
                    "security-by-design",
                    "delivery-phasing",
                ],
            )

            qa_flow = _stage_standard_flow(case_payload, stages["qa"])
            self.assertEqual(
                [document["name"] for document in qa_flow["packageDocuments"]],
                [
                    "QaReleaseReadinessReview",
                    "QaDefectAndRiskTriage",
                    "QaCandidateDeliveryNarrative",
                ],
            )
            qa_draft = _draft_template(case_payload, stages["qa"], written_at="2026-06-14T00:00:00+08:00")
            self.assertEqual(qa_draft["objectType"], "TRIDEV_QA_PACKAGE")
            self.assertIn("qualityOutputs", qa_draft["templateFields"])
            self.assertEqual(qa_draft["scorecardSchema"]["schemaName"], "QaScorecard")
            self.assertEqual(qa_draft["scorecardSchema"]["releaseDecisionEnum"], ["blocked", "conditional", "ready"])
            self.assertEqual(len(qa_draft["scorecardSchema"]["dimensions"]), 10)

            assurance_flow = _stage_standard_flow(case_payload, stages["assurance"])
            self.assertEqual(
                [document["name"] for document in assurance_flow["packageDocuments"]],
                [
                    "AssuranceRuntimeObservation",
                    "AssuranceRecoveryValidationMemo",
                    "AssuranceCostAndRiskReview",
                ],
            )
            assurance_draft = _draft_template(case_payload, stages["assurance"], written_at="2026-06-14T00:00:00+08:00")
            self.assertEqual(assurance_draft["objectType"], "TRIDEV_ASSURANCE_PACKAGE")
            self.assertIn("assuranceOutputs", assurance_draft["templateFields"])
            self.assertEqual(assurance_draft["scorecardSchema"]["schemaName"], "AssuranceScorecard")
            self.assertEqual(assurance_draft["scorecardSchema"]["deliveryDecisionEnum"], ["blocked", "conditional", "ready"])
            self.assertEqual(
                [item["key"] for item in assurance_draft["scorecardSchema"]["dimensions"]],
                [
                    "availability",
                    "recovery",
                    "alerting-and-observability",
                    "performance",
                    "cost-discipline",
                    "residual-risk",
                ],
            )

    def test_autopilot_owner_action_package_embeds_tridev_owner_adapter_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            tridev_root = workspace_root / "TriDev"
            support_root = workspace_root / "TriMetaverse" / "TriDev-copilot-host-assets"
            run_id = "ipd-ipd-auto-bridge-001"
            run_dir = support_root / "docs" / "runs" / run_id
            tridev_root.mkdir(parents=True, exist_ok=True)
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "run-metadata.json").write_text(json.dumps({"runId": run_id}), encoding="utf-8")
            (run_dir / "workflow-state.json").write_text(
                json.dumps(
                    {
                        "currentStage": "DISCOVERY",
                        "nextAction": "record-phase-result",
                        "executionMode": "manual",
                        "knowledgeBundlePath": f"docs/runs/{run_id}/knowledge-bundle.json",
                        "promptContextPath": f"docs/runs/{run_id}/host-prompt-context.json",
                        "taskPlanPath": f"docs/runs/{run_id}/coding-task-plan.json",
                        "roleWorkPlanPath": f"docs/runs/{run_id}/role-work-plan.json",
                        "executorBriefPath": f"docs/runs/{run_id}/executor-brief.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "role-adapters.json").write_text(
                json.dumps(
                    {
                        "stage": "DISCOVERY",
                        "nextAction": "record-phase-result",
                        "executionMode": "manual",
                        "adapters": [
                            {
                                "role": "ChiefProductOfficer",
                                "adapterType": "acting-owner",
                                "recommendedCommand": "python -m tridev.cli phase --root . --run-id <run-id> --stage DISCOVERY --status completed --artifact <path>",
                                "executionAdapter": {
                                    "subcommand": "phase",
                                    "action": "record-phase-result",
                                },
                            }
                        ],
                        "stageAdapters": [
                            {
                                "stage": "DISCOVERY",
                                "adapters": [
                                    {
                                        "role": "ChiefProductOfficer",
                                        "adapterType": "business-owner",
                                        "recommendedCommand": "python -m tridev.cli phase --root . --run-id <run-id> --stage DISCOVERY --status completed --artifact <path>",
                                        "executionAdapter": {
                                            "subcommand": "phase",
                                            "action": "record-phase-result",
                                        },
                                    },
                                    {
                                        "role": "ChiefProductOfficer",
                                        "adapterType": "acting-owner",
                                        "recommendedCommand": "python -m tridev.cli phase --root . --run-id <run-id> --stage DISCOVERY --status completed --artifact <path>",
                                        "executionAdapter": {
                                            "subcommand": "phase",
                                            "action": "record-phase-result",
                                        },
                                    },
                                    {
                                        "role": "ChiefProductOfficer",
                                        "adapterType": "gate-owner",
                                        "recommendedCommand": "python -m tridev.cli gate --root . --run-id <run-id> --stage DISCOVERY --status approved --approved-by ChiefProductOfficer",
                                        "executionAdapter": {
                                            "subcommand": "gate",
                                            "action": "approve-gate",
                                        },
                                    },
                                    {
                                        "role": "TriDev",
                                        "adapterType": "module-executor",
                                        "recommendedCommand": "python -m tridev.cli task-step --root . --run-id <run-id> --task-id <task-id> --status completed --artifact <path>",
                                        "executionAdapter": {
                                            "subcommand": "task-step",
                                            "action": "record-task-step",
                                        },
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            initialize_ipd_case(
                case_id="IPD-AUTO-BRIDGE-001",
                title="autopilot bridge",
                objective="验证 owner action package 接入 TriDev owner adapter bundle",
                task_description="在 owner action 暂停点直接产出 case 级 owner adapter bundle。",
                workspace_root=str(workspace_root),
            )
            mock_tridev_workflow = mock.Mock()
            mock_tridev_workflow.support_root_path.return_value = support_root
            with mock.patch("runtime.cognition.ipd_case_engine._load_tridev_workflow_module", return_value=mock_tridev_workflow):
                result = run_case_autopilot(
                    "IPD-AUTO-BRIDGE-001",
                    workspace_root=str(workspace_root),
                    tridev_root=str(tridev_root),
                )
            self.assertEqual(result["status"], "paused-owner-action")
            self.assertEqual(result["entryCheckpoint"], "task-dispatch")
            owner_action_path = chief_of_staff_ipd_case_root("IPD-AUTO-BRIDGE-001", workspace_root) / "owner-action-packages" / "01-discovery.json"
            owner_action = json.loads(owner_action_path.read_text(encoding="utf-8"))
            bundle = owner_action["tridevOwnerAdapterBundle"]
            self.assertEqual(bundle["status"], "ready")
            self.assertEqual(bundle["runId"], run_id)
            self.assertEqual(bundle["targetStage"], "DISCOVERY")
            self.assertTrue(bundle["runCurrentStageMatchesTargetStage"])
            self.assertEqual(bundle["nextAction"], "record-phase-result")
            self.assertEqual(bundle["executionMode"], "manual")
            self.assertEqual(bundle["ownerRole"], "ChiefProductOfficer")
            self.assertEqual(bundle["roleAdaptersPath"], f"docs/runs/{run_id}/role-adapters.json")
            self.assertEqual(bundle["workflowStatePath"], f"docs/runs/{run_id}/workflow-state.json")
            self.assertEqual({item["adapterType"] for item in bundle["ownerAdapters"]}, {"business-owner", "acting-owner", "gate-owner"})
            self.assertEqual([item["role"] for item in bundle["supportingAdapters"]], ["TriDev"])
            self.assertIn(f"docs/runs/{run_id}/knowledge-bundle.json", bundle["evidenceRefs"])

    def test_chief_of_staff_cannot_sign_before_ceo_on_stage_or_intake(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-003A",
                title="签核顺序",
                objective="验证 CEO 先签、总助后验",
                task_description="验证签核顺序门禁。",
                created_by="CEO",
                workspace_root=str(workspace_root),
            )
            with self.assertRaisesRegex(ValueError, "CEOChiefOfStaff cannot sign before CEO"):
                record_intake_signoff("IPD-003A", role="CEOChiefOfStaff", workspace_root=str(workspace_root))

            record_intake_signoff("IPD-003A", role="CEO", workspace_root=str(workspace_root))
            record_intake_signoff("IPD-003A", role="CEOChiefOfStaff", workspace_root=str(workspace_root))
            submit_stage_output(
                "IPD-003A",
                stage_key="discovery",
                submitted_by="ChiefProductOfficer",
                summary="discovery package 已提交",
                workspace_root=str(workspace_root),
            )
            with self.assertRaisesRegex(ValueError, "CEOChiefOfStaff cannot sign before CEO"):
                record_stage_signoff(
                    "IPD-003A",
                    stage_key="discovery",
                    role="CEOChiefOfStaff",
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
            self.assertEqual(payload["entryCheckpoint"], "ceo-demand")
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
            self.assertEqual(intake_brief["clarificationSheet"]["status"], "needs-ceo-clarification")
            self.assertIn("competitorReference", intake_brief["clarificationSheet"]["missingSlotKeys"])
            self.assertEqual(
                intake_brief["briefing"]["ownerProposal"],
                ["总助先把任务转成 intake briefing；CMO / COO / CFO / CPO / CTO 再按节点继续细化。"],
            )

    def test_task_intake_blocks_discovery_until_ceo_fills_critical_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "task-intake",
                        "--case-id",
                        "IPD-CLARIFY-001",
                        "--workspace-root",
                        str(workspace_root),
                        "做一个自动化开发软件，在公司级别从下发任务到总助评估分派各部门，部分负责人细化，按公司流程有序进行开发和交付，验收，长期运维",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "awaiting-intake-approvals")
            self.assertEqual(payload["intakeClarificationStatus"], "needs-ceo-clarification")
            self.assertIn("competitorReference", payload["missingIntakeSlotKeys"])

            result = record_intake_signoff("IPD-CLARIFY-001", role="CEO", workspace_root=str(workspace_root))
            self.assertEqual(result["status"], "awaiting-intake-approvals")
            self.assertEqual(result["entryCheckpoint"], "ceo-demand")
            self.assertEqual(result["currentStageKey"], "")
            self.assertIn("competitorReference", result["missingIntakeSlotKeys"])

    def test_autopilot_pauses_at_ceo_demand_when_intake_clarification_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            ipd_case_main(
                [
                    "task-intake",
                    "--case-id",
                    "IPD-AUTO-CLARIFY-001",
                    "--workspace-root",
                    str(workspace_root),
                    "做一个自动化开发软件，在公司级别从下发任务到总助评估分派各部门，部分负责人细化，按公司流程有序进行开发和交付，验收，长期运维",
                ]
            )

            result = run_case_autopilot(
                "IPD-AUTO-CLARIFY-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
            )

            self.assertEqual(result["status"], "paused-intake-clarification")
            self.assertEqual(result["entryCheckpoint"], "ceo-demand")
            self.assertEqual(result["pendingRole"], "CEO")
            self.assertEqual(result["pendingStageKey"], "")
            self.assertIn("competitorReference", result["missingSlotKeys"])

    def test_chief_of_staff_can_freeze_after_clarification_ready_when_feasibility_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-FREEZE-INTAKE-001")

            result = freeze_ipd_case(
                "IPD-FREEZE-INTAKE-001",
                role="CEOChiefOfStaff",
                reason="总助评估当前资源、目标和范围不匹配，项目暂不可行。",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["status"], "paused-frozen")
            self.assertEqual(result["currentStageKey"], "")
            self.assertEqual(result["freezeControl"]["frozenByRole"], "CEOChiefOfStaff")
            self.assertEqual(result["freezeControl"]["domain"], "feasibility")
            self.assertEqual(result["freezeControl"]["status"], "frozen")

            with self.assertRaisesRegex(ValueError, "case is frozen"):
                record_intake_signoff("IPD-FREEZE-INTAKE-001", role="CEO", workspace_root=str(workspace_root))

            resumed = unfreeze_ipd_case(
                "IPD-FREEZE-INTAKE-001",
                role="CEOChiefOfStaff",
                note="预算窗口和目标范围已补齐，允许恢复评估。",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(resumed["status"], "awaiting-intake-approvals")
            self.assertEqual(resumed["freezeControl"]["status"], "resolved")

            after_resume = self._approve_intake(workspace_root, "IPD-FREEZE-INTAKE-001")
            self.assertEqual(after_resume["status"], "waiting-stage-output")
            self.assertEqual(after_resume["currentStageKey"], "discovery")

    def test_cmo_can_freeze_discovery_when_market_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-FREEZE-DISCOVERY-001")
            self._approve_intake(workspace_root, "IPD-FREEZE-DISCOVERY-001")

            result = freeze_ipd_case(
                "IPD-FREEZE-DISCOVERY-001",
                role="ChiefMarketingOfficer",
                reason="CMO 调研后判断这不是市场真实需求，当前不应继续投入。",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["status"], "paused-frozen")
            self.assertEqual(result["currentStageKey"], "discovery")
            self.assertEqual(result["freezeControl"]["frozenByRole"], "ChiefMarketingOfficer")
            self.assertEqual(result["freezeControl"]["domain"], "market-demand")

            case_payload = read_ipd_case("IPD-FREEZE-DISCOVERY-001", workspace_root=str(workspace_root))
            discovery_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            self.assertEqual(discovery_stage["status"], "frozen")
            self.assertIn("市场真实需求", discovery_stage["blockedReason"])

            resumed = unfreeze_ipd_case(
                "IPD-FREEZE-DISCOVERY-001",
                role="ChiefMarketingOfficer",
                note="新的市场证据表明仍值得继续验证。",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(resumed["status"], "waiting-stage-output")
            self.assertEqual(resumed["currentStageKey"], "discovery")

    def test_assigned_roles_can_freeze_case_during_their_responsible_stage(self) -> None:
        scenarios = (
            ("IPD-FREEZE-CPO-001", "ChiefProductOfficer", "product-scope"),
            ("IPD-FREEZE-CTO-001", "ChiefTechnologyOfficer", "technical-feasibility"),
            ("IPD-FREEZE-COO-001", "ChiefOperatingOfficer", "operations"),
            ("IPD-FREEZE-CFO-001", "ChiefFinancialOfficer", "finance"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            for case_id, role, expected_domain in scenarios:
                self._advance_case_to_intelligence(workspace_root, case_id)
                result = freeze_ipd_case(
                    case_id,
                    role=role,
                    reason=f"{role} 基于当前专业判断决定冻结项目。",
                    workspace_root=str(workspace_root),
                )
                self.assertEqual(result["status"], "paused-frozen")
                self.assertEqual(result["currentStageKey"], "intelligence")
                self.assertEqual(result["freezeControl"]["frozenByRole"], role)
                self.assertEqual(result["freezeControl"]["domain"], expected_domain)

                resumed = unfreeze_ipd_case(
                    case_id,
                    role=role,
                    note=f"{role} 确认冻结条件已满足，项目恢复。",
                    workspace_root=str(workspace_root),
                )
                self.assertEqual(resumed["status"], "waiting-stage-output")
                self.assertEqual(resumed["currentStageKey"], "intelligence")

    def test_future_matrix_role_can_freeze_after_joining_ipd(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._advance_case_to_intelligence(workspace_root, "IPD-FREEZE-FUTURE-001")
            extended_matrix = ipd_case_engine_module._INTAKE_STAGE_ROLE_ASSIGNMENT_MATRIX + (
                {
                    "role": "ChiefRiskOfficer",
                    "stageKeys": ("intelligence",),
                    "taskType": "risk-judgment",
                    "status": "placeholder",
                    "canFreezeCase": True,
                    "responsibility": "从风险治理视角评估是否需要冻结项目。",
                    "deliverables": ("风险冻结判断",),
                },
            )
            with mock.patch.object(ipd_case_engine_module, "_INTAKE_STAGE_ROLE_ASSIGNMENT_MATRIX", extended_matrix):
                result = freeze_ipd_case(
                    "IPD-FREEZE-FUTURE-001",
                    role="ChiefRiskOfficer",
                    reason="未来新增风险岗位判断当前风险不可接受，项目需冻结。",
                    workspace_root=str(workspace_root),
                )
            self.assertEqual(result["status"], "paused-frozen")
            self.assertEqual(result["freezeControl"]["frozenByRole"], "ChiefRiskOfficer")

    def test_cli_discovery_command_generates_and_submits_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_platform_case(workspace_root, "IPD-20260611-PLATFORM-001")
            self._approve_intake(workspace_root, "IPD-20260611-PLATFORM-001")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "discovery",
                        "--case-id",
                        "IPD-20260611-PLATFORM-001",
                        "--submit",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["submitted"])
            self.assertEqual(payload["automationStageKey"], "discovery")
            self.assertEqual(payload["status"], "awaiting-stage-approvals")
            discovery_root = workspace_root / "TriMetaverse" / "reference" / "discovery" / "IPD-20260611-PLATFORM-001"
            self.assertTrue((discovery_root / "reference-source-catalog.json").exists())
            competitor_landscape = (discovery_root / "discovery-competitor-landscape.md").read_text(encoding="utf-8")
            self.assertIn("OpenRouter", competitor_landscape)

    def test_cli_discovery_command_carries_all_seeded_competitors_across_catalog_brief_and_landscape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_platform_carry_forward_case(workspace_root, "IPD-20260610-PLATFORM-CARRY-001")
            self._approve_intake(workspace_root, "IPD-20260610-PLATFORM-CARRY-001")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "discovery",
                        "--case-id",
                        "IPD-20260610-PLATFORM-CARRY-001",
                        "--submit",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            discovery_root = workspace_root / "TriMetaverse" / "reference" / "discovery" / "IPD-20260610-PLATFORM-CARRY-001"
            source_catalog = json.loads((discovery_root / "reference-source-catalog.json").read_text(encoding="utf-8"))
            source_names = {str(entry.get("name") or "") for entry in source_catalog.get("sources", [])}
            functional_brief = (discovery_root / "discovery-reference-functional-brief.md").read_text(encoding="utf-8")
            competitor_landscape = (discovery_root / "discovery-competitor-landscape.md").read_text(encoding="utf-8")
            for expected in ("LiteLLM", "sub2api", "OpenRouter", "OpenAI API Platform"):
                self.assertIn(expected, source_names)
                self.assertIn(expected, functional_brief)
                self.assertIn(expected, competitor_landscape)

            source_by_name = {
                str(entry.get("name") or ""): entry
                for entry in source_catalog.get("sources", [])
                if isinstance(entry, dict)
            }
            self.assertEqual(source_by_name["LiteLLM"]["sourceId"], "litellm-docs")
            self.assertEqual(source_by_name["sub2api"]["sourceId"], "sub2api-reference")
            self.assertEqual(source_by_name["LiteLLM"]["captureStatus"], "link-registered")
            self.assertEqual(source_by_name["sub2api"]["captureStatus"], "link-registered")
            self.assertIn("https://docs.litellm.ai/docs/", source_by_name["LiteLLM"]["sourceUrl"])
            self.assertIn("https://github.com/Wei-Shaw/sub2api/blob/main/README.md", source_by_name["sub2api"]["sourceUrl"])
            self.assertNotIn("manual-to-confirm", functional_brief)
            self.assertNotIn("待补官方来源", competitor_landscape)

    def test_cli_discovery_command_preserves_platform_boundary_sources_for_project_delivery_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_platform_carry_forward_case(workspace_root, "IPD-20260610-PLATFORM-BOUNDARY-001")
            self._approve_intake(workspace_root, "IPD-20260610-PLATFORM-BOUNDARY-001")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "discovery",
                        "--case-id",
                        "IPD-20260610-PLATFORM-BOUNDARY-001",
                        "--submit",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            discovery_root = workspace_root / "TriMetaverse" / "reference" / "discovery" / "IPD-20260610-PLATFORM-BOUNDARY-001"
            source_catalog = json.loads((discovery_root / "reference-source-catalog.json").read_text(encoding="utf-8"))
            source_names = {str(entry.get("name") or "") for entry in source_catalog.get("sources", [])}
            functional_brief = (discovery_root / "discovery-reference-functional-brief.md").read_text(encoding="utf-8")
            competitor_landscape = (discovery_root / "discovery-competitor-landscape.md").read_text(encoding="utf-8")
            self.assertIn("TriAvatar README", source_names)
            self.assertIn("Tristaciss Phase C ingress design", source_names)
            self.assertIn("TriAvatar README", functional_brief)
            self.assertIn("Tristaciss Phase C ingress design", functional_brief)
            self.assertIn("TriAvatar/README.md", competitor_landscape)
            self.assertIn("TriStaciss/docs/tristaciss-openai-ingress-phase-c-design.md", competitor_landscape)

    def test_cli_discovery_command_blocks_submit_when_seeded_competitor_is_missing_from_brief_or_landscape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_platform_carry_forward_case(workspace_root, "IPD-20260610-PLATFORM-CARRY-NEG-001")
            self._approve_intake(workspace_root, "IPD-20260610-PLATFORM-CARRY-NEG-001")

            original_write_discovery_documents = ipd_case_engine_module._write_discovery_documents

            def _write_incomplete_documents(*args, **kwargs):
                refs = original_write_discovery_documents(*args, **kwargs)
                reference_root = workspace_root / "TriMetaverse" / "reference" / "discovery" / "IPD-20260610-PLATFORM-CARRY-NEG-001"
                brief_path = reference_root / "discovery-reference-functional-brief.md"
                landscape_path = reference_root / "discovery-competitor-landscape.md"
                brief_path.write_text(brief_path.read_text(encoding="utf-8").replace("LiteLLM", ""), encoding="utf-8")
                landscape_path.write_text(landscape_path.read_text(encoding="utf-8").replace("LiteLLM", ""), encoding="utf-8")
                return refs

            with mock.patch.object(ipd_case_engine_module, "_write_discovery_documents", side_effect=_write_incomplete_documents):
                with self.assertRaisesRegex(ValueError, "discovery seeded competitor carry-forward validation failed"):
                    ipd_case_main(
                        [
                            "discovery",
                            "--case-id",
                            "IPD-20260610-PLATFORM-CARRY-NEG-001",
                            "--submit",
                            "--workspace-root",
                            str(workspace_root),
                        ]
                    )

    def test_case_category_and_reference_theme_can_separate_process_from_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            result = initialize_ipd_case(
                case_id="IPD-20260611-PLATFORM-009",
                title="IPD 流程完善",
                objective="先完善 IPD discovery/intelligence 自动化，再固化流程。",
                task_description="完善 IPD discovery/intelligence 自动化，使其可复用到任何 CEO demand 项目。",
                case_category="process-improvement",
                reference_theme="WORKFLOW",
                slot_answers={
                    **self._full_slot_answers(),
                    "competitorReference": "Acme Flow",
                },
                require_clarification_slots=True,
                workspace_root=str(workspace_root),
            )
            self.assertEqual(result["caseCategory"], "process-improvement")
            self.assertEqual(result["referenceTheme"], "WORKFLOW")
            self.assertEqual(result["executionFlow"], "agile-improvement")

            case_payload = read_ipd_case("IPD-20260611-PLATFORM-009", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["intake"]["caseCategory"], "process-improvement")
            self.assertEqual(case_payload["intake"]["referenceTheme"], "WORKFLOW")
            self.assertEqual([stage["stageKey"] for stage in case_payload["stages"]], [
                "backlog",
                "sprint-planning",
                "sprint-execution",
                "sprint-review",
                "retrospective",
                "validation-handoff",
            ])

            approved = self._approve_intake(workspace_root, "IPD-20260611-PLATFORM-009")
            self.assertEqual(approved["currentStageKey"], "backlog")
            self.assertEqual(approved["entryCheckpoint"], "task-dispatch")

            sources = ipd_case_engine_module._build_intelligence_sources(case_payload)
            source_names = {item["name"] for item in sources}
            self.assertIn("OpenHands", source_names)
            self.assertIn("Continue", source_names)
            self.assertNotIn("OpenAI API Platform", source_names)

    def test_tricompany_artifact_paths_resolve_to_source_repo_from_both_workspace_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            tricompany_root = workspace_root / "TriCompany"
            trimetaverse_root = workspace_root / "TriMetaverse"
            (tricompany_root / "docs").mkdir(parents=True, exist_ok=True)
            (tricompany_root / "runtime").mkdir(parents=True, exist_ok=True)
            trimetaverse_root.mkdir(parents=True, exist_ok=True)
            (trimetaverse_root / "TriCompany" / "docs").mkdir(parents=True, exist_ok=True)

            artifact_ref = "TriCompany/docs/workflow/agile-improvement/IPD-TEST-001/02-sprint-plan.md"
            expected = tricompany_root / "docs" / "workflow" / "agile-improvement" / "IPD-TEST-001" / "02-sprint-plan.md"

            from_source_root = ipd_case_engine_module._resolve_workspace_artifact_path(artifact_ref, str(tricompany_root))
            from_central_root = ipd_case_engine_module._resolve_workspace_artifact_path(artifact_ref, str(trimetaverse_root))

            self.assertEqual(from_source_root, expected)
            self.assertEqual(from_central_root, expected)

    def test_cli_task_intake_can_explicitly_mark_project_delivery_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "task-intake",
                        "--case-id",
                        "IPD-20260611-PLATFORM-001",
                        "--case-category",
                        "project-delivery",
                        "--reference-theme",
                        "PLATFORM",
                        "--workspace-root",
                        str(workspace_root),
                        "开发一个模型 API 中转平台",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["caseCategory"], "project-delivery")
            self.assertEqual(payload["referenceTheme"], "PLATFORM")

            case_payload = read_ipd_case("IPD-20260611-PLATFORM-001", workspace_root=str(workspace_root))
            self.assertEqual(case_payload["intake"]["caseCategory"], "project-delivery")
            self.assertEqual(case_payload["intake"]["referenceTheme"], "PLATFORM")

    def test_process_improvement_backlog_stage_supports_chief_of_staff_final_signoff_after_owner_submit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-20260611-WORKFLOW-011",
                title="流程优化敏捷收口验证",
                objective="验证流程优化 case 中总助 owner/final signoff 的重复角色链路。",
                task_description="让 process-improvement case 走 backlog 到 sprint-planning，并验证总助 owner + 最终签发场景。",
                case_category="process-improvement",
                reference_theme="WORKFLOW",
                slot_answers=self._full_slot_answers(),
                require_clarification_slots=True,
                workspace_root=str(workspace_root),
            )
            self._approve_intake(workspace_root, "IPD-20260611-WORKFLOW-011")

            submitted = submit_stage_output(
                "IPD-20260611-WORKFLOW-011",
                stage_key="backlog",
                submitted_by="CEOChiefOfStaff",
                summary="backlog 已整理完毕",
                details=("已将流程优化需求拆成 sprint backlog。",),
                evidence=("docs/workflow/agile-improvement/backlog.md",),
                object_path="docs/workflow/agile-improvement/backlog-package.json",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(submitted["status"], "awaiting-stage-approvals")

            pending = read_ipd_case("IPD-20260611-WORKFLOW-011", workspace_root=str(workspace_root))
            backlog_stage = next(stage for stage in pending["stages"] if stage["stageKey"] == "backlog")
            self.assertEqual(backlog_stage["requiredApprovers"], ["CEOChiefOfStaff", "CEO", "CEOChiefOfStaff"])
            self.assertEqual([item["status"] for item in backlog_stage["approvals"]], ["approved", "pending", "pending"])

            signed_by_ceo = record_stage_signoff(
                "IPD-20260611-WORKFLOW-011",
                stage_key="backlog",
                role="CEO",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(signed_by_ceo["status"], "awaiting-stage-approvals")

            advanced = record_stage_signoff(
                "IPD-20260611-WORKFLOW-011",
                stage_key="backlog",
                role="CEOChiefOfStaff",
                workspace_root=str(workspace_root),
            )
            self.assertEqual(advanced["currentStageKey"], "sprint-planning")

            case_payload = read_ipd_case("IPD-20260611-WORKFLOW-011", workspace_root=str(workspace_root))
            backlog_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "backlog")
            self.assertEqual(backlog_stage["status"], "completed")
            self.assertEqual(backlog_stage["releaseStatus"], "issued")
            self.assertEqual(backlog_stage["releaseIssuedByRole"], "CEOChiefOfStaff")

            stage_output = json.loads(Path(backlog_stage["outputPath"]).read_text(encoding="utf-8"))
            self.assertEqual(
                [item["role"] for item in stage_output["signatureChain"]],
                ["CEOChiefOfStaff", "CEO", "CEOChiefOfStaff"],
            )
            self.assertEqual(stage_output["release"]["status"], "issued")

    def test_intelligence_automation_can_submit_and_record_codegraph_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._advance_platform_case_to_intelligence(workspace_root, "IPD-20260611-PLATFORM-002")

            with mock.patch.object(
                ipd_case_engine_module,
                "_collect_codegraph_insights",
                return_value={
                    "sourceId": "sub2api-local-reference",
                    "name": "Sub2API",
                    "localPath": "TriMetaverse/reference/sub2api",
                    "status": "ready",
                    "statusOutput": "indexed files: 42",
                    "contextMarkdown": "# CodeGraph Context\n\n- gateway layer\n- billing layer\n",
                },
            ):
                result = run_intelligence_stage_automation(
                    "IPD-20260611-PLATFORM-002",
                    workspace_root=str(workspace_root),
                    submit=True,
                    enable_codegraph=True,
                )
            self.assertTrue(result["submitted"])
            self.assertEqual(result["automationStageKey"], "intelligence")
            self.assertEqual(result["status"], "awaiting-stage-approvals")
            intelligence_root = workspace_root / "TriMetaverse" / "reference" / "intelligence" / "IPD-20260611-PLATFORM-002"
            codegraph_analysis = (intelligence_root / "intelligence-codegraph-analysis.md").read_text(encoding="utf-8")
            self.assertIn("gateway layer", codegraph_analysis)
            stage_output = chief_of_staff_ipd_case_root("IPD-20260611-PLATFORM-002", workspace_root) / "outputs" / "02-intelligence.json"
            self.assertTrue(stage_output.exists())

    def test_workflow_delivery_case_can_auto_submit_discovery_and_intelligence_with_super_dev_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            case_id = "IPD-TEST-WORKFLOW-001"
            initialize_ipd_case(
                case_id=case_id,
                title="AI 自动化开发软件",
                objective="验证标准 IPD 下 Discovery 与 Intelligence 自动化可围绕 super-dev 参考系提交 package。",
                task_description="围绕 AI 自动化开发软件，验证 Discovery / Intelligence 自动执行器在标准 IPD case 中的 live 产物能力。",
                case_category="project-delivery",
                reference_theme="WORKFLOW",
                slot_answers={
                    "competitorReference": "Super-dev、Superpowers、spec-kit、openspec",
                    "targetUserScenario": "先服务 CEOChiefOfStaff、CPO、CTO，在公司级研发任务进入 IPD 时使用",
                    "deliveryWindow": "先在 1 周内完成入口补槽、总助分派、Discovery 和 Intelligence 自动化验证",
                    "budgetGuardrail": "首轮仅使用现有人力和少量工具试验成本",
                    "successMetric": "证明 CEO demand 能稳定进入 intake，补槽后能稳定分派并产出 Discovery / Intelligence package，而且这两个阶段是由 owner 自动完成。",
                    "mustHaveScope": "必须交付 ceo-demand、task-dispatch、entryCheckpoint、Discovery/Intelligence 自动化及流程教程",
                    "explicitOutOfScope": "不在本 case 内直接开发模型 API 中转平台，不涉及正式宿主切换，不涉及生产级上线",
                },
                require_clarification_slots=True,
                workspace_root=str(workspace_root),
            )
            approved = self._approve_intake(workspace_root, case_id)
            self.assertEqual(approved["currentStageKey"], "discovery")

            discovery_result = run_discovery_stage_automation(
                case_id,
                workspace_root=str(workspace_root),
                submit=True,
            )
            self.assertTrue(discovery_result["submitted"])
            self.assertEqual(discovery_result["automationStageKey"], "discovery")
            discovery_root = workspace_root / "TriMetaverse" / "reference" / "discovery" / case_id
            competitor_landscape = (discovery_root / "discovery-competitor-landscape.md").read_text(encoding="utf-8")
            self.assertIn("super-dev", competitor_landscape)

            self._approve_stage(workspace_root, case_id, "discovery")

            with mock.patch.object(
                ipd_case_engine_module,
                "_collect_codegraph_insights",
                return_value={
                    "sourceId": "super-dev-vendor-reference",
                    "name": "super-dev",
                    "localPath": "TriDev/vendor/super-dev",
                    "status": "ready",
                    "statusOutput": "indexed files: 12",
                    "contextMarkdown": "# CodeGraph Context\n\n- resume and continue\n- knowledge bundle\n",
                },
            ):
                intelligence_result = run_intelligence_stage_automation(
                    case_id,
                    workspace_root=str(workspace_root),
                    submit=True,
                    enable_codegraph=True,
                )
            self.assertTrue(intelligence_result["submitted"])
            self.assertEqual(intelligence_result["automationStageKey"], "intelligence")
            intelligence_root = workspace_root / "TriMetaverse" / "reference" / "intelligence" / case_id
            landscape = (intelligence_root / "intelligence-opensource-landscape.md").read_text(encoding="utf-8")
            self.assertIn("| super-dev |", landscape)
            source_catalog = json.loads((intelligence_root / "reference-source-catalog.json").read_text(encoding="utf-8"))
            self.assertIn(
                "TriDev/vendor/super-dev",
                [entry.get("localPath", "") for entry in source_catalog.get("sources", [])],
            )
            stage_output = chief_of_staff_ipd_case_root(case_id, workspace_root) / "outputs" / "02-intelligence.json"
            self.assertTrue(stage_output.exists())

    def test_cli_can_unfreeze_frozen_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-FREEZE-CLI-001")
            freeze_ipd_case(
                "IPD-FREEZE-CLI-001",
                role="CEOChiefOfStaff",
                reason="等待 CEO 补齐冻结条件对应的资源确认。",
                workspace_root=str(workspace_root),
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "unfreeze",
                        "--case-id",
                        "IPD-FREEZE-CLI-001",
                        "--role",
                        "CEOChiefOfStaff",
                        "--note",
                        "资源约束已解除，恢复推进。",
                        "--workspace-root",
                        str(workspace_root),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "awaiting-intake-approvals")
            self.assertEqual(payload["freezeControl"]["status"], "resolved")

    def test_autopilot_pauses_cleanly_when_case_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._initialize_clarified_case(workspace_root, "IPD-FREEZE-AUTO-001")
            self._approve_intake(workspace_root, "IPD-FREEZE-AUTO-001")
            freeze_ipd_case(
                "IPD-FREEZE-AUTO-001",
                role="ChiefMarketingOfficer",
                reason="等待新增市场验证结论。",
                workspace_root=str(workspace_root),
            )

            result = run_case_autopilot(
                "IPD-FREEZE-AUTO-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
            )
            self.assertEqual(result["status"], "paused-frozen")
            self.assertEqual(result["pendingRole"], "ChiefMarketingOfficer")
            self.assertEqual(result["pendingStageKey"], "discovery")
            self.assertEqual(result["freezeControl"]["status"], "frozen")

    def test_slot_filled_case_routes_discovery_and_intelligence_role_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            ipd_case_main(
                [
                    "task-intake",
                    "--case-id",
                    "IPD-ROLE-001",
                    "--workspace-root",
                    str(workspace_root),
                    "做一个自动化开发软件，在公司级别从下发任务到总助评估分派各部门，部分负责人细化，按公司流程有序进行开发和交付，验收，长期运维",
                ]
            )
            ipd_case_main(
                [
                    "init",
                    "--case-id",
                    "IPD-ROLE-001",
                    "--title",
                    "自动化开发执行闭环",
                    "--objective",
                    "验证 CEO 入口补槽、角色分派和 Discovery/Intelligence 路由",
                    "--task-description",
                    "CEO 提需求，总助补槽后再分派给 CMO/CPO/CTO/COO/CFO。",
                    "--slot-answer",
                    "competitorReference=Cursor、Devin、Linear",
                    "--slot-answer",
                    "targetUserScenario=先服务 CEOChiefOfStaff 与产品/技术负责人，验证公司级研发任务分派场景",
                    "--slot-answer",
                    "deliveryWindow=先在 1 周内完成 Discovery、Intelligence 和 PRD 验证",
                    "--slot-answer",
                    "budgetGuardrail=首轮只允许现有人力和少量工具试验成本",
                    "--slot-answer",
                    "successMetric=证明 IPD 能控制住入口补槽、任务分派和 Discovery/Intelligence 路由",
                    "--slot-answer",
                    "mustHaveScope=首轮必须交付 intake briefing、Discovery/Intelligence work item 与 owner-action package",
                    "--slot-answer",
                    "explicitOutOfScope=不涉及正式宿主切换、不涉及链上实现、不涉及大规模运营自动化",
                    "--workspace-root",
                    str(workspace_root),
                ]
            )

            result = self._approve_intake(workspace_root, "IPD-ROLE-001")
            self.assertEqual(result["status"], "waiting-stage-output")
            self.assertEqual(result["currentStageKey"], "discovery")
            self.assertEqual(result["intakeClarificationStatus"], "ready-for-dispatch")

            autopilot_result = run_case_autopilot(
                "IPD-ROLE-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
            )
            self.assertEqual(autopilot_result["status"], "paused-owner-action")
            discovery_owner_action = json.loads(
                (
                    chief_of_staff_ipd_case_root("IPD-ROLE-001", workspace_root)
                    / "owner-action-packages"
                    / "01-discovery.json"
                ).read_text(encoding="utf-8")
            )
            discovery_roles = {item["role"]: item for item in discovery_owner_action["roleAssignmentMatrix"]}
            self.assertEqual(discovery_roles["ChiefProductOfficer"]["status"], "active")
            self.assertEqual(discovery_roles["ChiefMarketingOfficer"]["status"], "placeholder")
            self.assertIn("Discovery/Intelligence/Delivery", discovery_roles["ChiefProductOfficer"]["responsibility"])
            self.assertIn("竞品/功能/官方手册研究", discovery_roles["ChiefProductOfficer"]["deliverables"])
            self.assertIn("真实需求", discovery_roles["ChiefMarketingOfficer"]["responsibility"])

            submit_stage_output(
                "IPD-ROLE-001",
                stage_key="discovery",
                submitted_by="ChiefProductOfficer",
                summary="Discovery 已提交",
                evidence=("manual/discovery-reference-pack.json",),
                workspace_root=str(workspace_root),
            )
            self._approve_stage(workspace_root, "IPD-ROLE-001", "discovery")

            autopilot_result = run_case_autopilot(
                "IPD-ROLE-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
            )
            self.assertEqual(autopilot_result["status"], "paused-owner-action")
            self.assertEqual(autopilot_result["entryCheckpoint"], "intelligence")
            self.assertEqual(autopilot_result["pendingStageKey"], "intelligence")
            intelligence_owner_action = json.loads(
                (
                    chief_of_staff_ipd_case_root("IPD-ROLE-001", workspace_root)
                    / "owner-action-packages"
                    / "02-intelligence.json"
                ).read_text(encoding="utf-8")
            )
            intelligence_roles = {item["role"]: item for item in intelligence_owner_action["roleAssignmentMatrix"]}
            self.assertEqual(intelligence_roles["ChiefTechnologyOfficer"]["status"], "active")
            self.assertEqual(intelligence_roles["ChiefFinancialOfficer"]["status"], "placeholder")
            self.assertEqual(intelligence_roles["ChiefOperatingOfficer"]["status"], "placeholder")
            self.assertIn("代码研究、设计与开发", intelligence_roles["ChiefTechnologyOfficer"]["responsibility"])
            self.assertIn("IntelligenceCodegraphAnalysis", intelligence_roles["ChiefTechnologyOfficer"]["deliverables"])

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
            self.assertEqual(
                [approval["role"] for approval in case_payload["intake"]["approvals"]],
                ["CEO", "CEOChiefOfStaff"],
            )

    def test_cli_autopilot_command_pauses_for_owner_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-CLI-AUTO-001",
                title="CLI autopilot",
                objective="验证 CLI autopilot",
                task_description="通过 CLI 命令自动推进。",
                workspace_root=str(workspace_root),
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "autopilot",
                        "--case-id",
                        "IPD-CLI-AUTO-001",
                        "--workspace-root",
                        str(workspace_root),
                        "--no-tridev-bridge",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "paused-owner-action")
            self.assertEqual(payload["pendingRole"], "ChiefProductOfficer")
            self.assertEqual(payload["pendingStageKey"], "discovery")
            self.assertEqual(payload["tridevBridgeEnabled"], False)

    def test_coding_stage_rejects_docs_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-AUTO-EXEC-001",
                title="execution gate",
                objective="验证 coding 阶段必须提交真实工程证据",
                task_description="在 coding 阶段不能只交 docs / workbench 产物。",
                workspace_root=str(workspace_root),
            )
            self._approve_intake(workspace_root, "IPD-AUTO-EXEC-001")
            for stage_key, owner_role in (
                ("discovery", "ChiefProductOfficer"),
                ("intelligence", "ChiefProductOfficer"),
                ("designing", "ChiefTechnologyOfficer"),
            ):
                submit_stage_output(
                    "IPD-AUTO-EXEC-001",
                    stage_key=stage_key,
                    submitted_by=owner_role,
                    summary=f"{stage_key} 已提交",
                    evidence=(f"manual/{stage_key}.json",),
                    workspace_root=str(workspace_root),
                )
                self._approve_stage(workspace_root, "IPD-AUTO-EXEC-001", stage_key)

            with self.assertRaisesRegex(ValueError, "requires at least one real source/test/deploy evidence path"):
                submit_stage_output(
                    "IPD-AUTO-EXEC-001",
                    stage_key="coding",
                    submitted_by="ChiefTechnologyOfficer",
                    summary="coding docs only",
                    evidence=(
                        "docs/ipd-autopilot/IPD-AUTO-EXEC-001/04-coding.md",
                        "workbench/ipd/cases/IPD-AUTO-EXEC-001/autopilot-packages/04-coding.json",
                    ),
                    workspace_root=str(workspace_root),
                )

    def test_discovery_stage_rejects_generated_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-AUTO-DISCOVERY-001",
                title="discovery evidence gate",
                objective="验证 discovery 阶段也不能只交 workbench/autopilot 生成物。",
                task_description="在 discovery 阶段必须至少有一类非生成型提交证据。",
                workspace_root=str(workspace_root),
            )
            self._approve_intake(workspace_root, "IPD-AUTO-DISCOVERY-001")

            with self.assertRaisesRegex(ValueError, "requires at least one non-generated evidence path"):
                submit_stage_output(
                    "IPD-AUTO-DISCOVERY-001",
                    stage_key="discovery",
                    submitted_by="ChiefProductOfficer",
                    summary="discovery generated only",
                    evidence=(
                        "workbench/ipd/cases/IPD-AUTO-DISCOVERY-001/participant-records/01-discovery.json",
                        "workbench/ipd/cases/IPD-AUTO-DISCOVERY-001/autopilot-packages/01-discovery.json",
                    ),
                    object_path="workbench/ipd/cases/IPD-AUTO-DISCOVERY-001/autopilot-packages/01-discovery.json",
                    workspace_root=str(workspace_root),
                )

    def test_reconcile_invalidates_completed_case_without_real_execution_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            case_root = chief_of_staff_ipd_case_root("IPD-AUDIT-001", workspace_root)
            initialize_ipd_case(
                case_id="IPD-AUDIT-001",
                title="audit invalid delivery",
                objective="验证历史假交付会被拉回",
                task_description="旧版 autopilot 直接把文档产物签成完成。",
                workspace_root=str(workspace_root),
            )
            case_payload = read_ipd_case("IPD-AUDIT-001", workspace_root=str(workspace_root))
            for stage in case_payload["stages"]:
                stage["status"] = "completed"
                stage["completedAt"] = "2026-05-27T00:00:00+08:00"
                stage["submittedAt"] = "2026-05-27T00:00:00+08:00"
                stage["outputPath"] = (case_root / "outputs" / f"{stage['stageKey']}.json").as_posix()
                stage["outputSummary"] = f"{stage['stageKey']} fake completed"
                stage["approvals"] = [
                    {"role": "CEOChiefOfStaff", "status": "approved", "note": "", "updatedAt": "2026-05-27T00:00:00+08:00"},
                    {"role": "CEO", "status": "approved", "note": "", "updatedAt": "2026-05-27T00:00:00+08:00"},
                ]
            case_payload["status"] = "completed"
            case_payload["currentStageKey"] = ""
            case_payload["currentWorkItemPath"] = ""
            (case_root / "outputs").mkdir(parents=True, exist_ok=True)
            for stage in case_payload["stages"]:
                output_payload = {
                    "schemaVersion": "1.0",
                    "kind": "ipd-stage-output",
                    "caseId": "IPD-AUDIT-001",
                    "stageKey": stage["stageKey"],
                    "phaseKey": stage["phaseKey"],
                    "businessOwner": stage["businessOwner"],
                    "actingOwner": stage["actingOwner"],
                    "moduleExecutor": stage["moduleExecutor"],
                    "gateOwner": stage["gateOwner"],
                    "ownerRole": stage["ownerRole"],
                    "participantRoles": list(stage.get("participantRoles", [])),
                    "submittedAt": "2026-05-27T00:00:00+08:00",
                    "summary": f"{stage['stageKey']} fake completed",
                    "details": [],
                    "evidence": [f"docs/ipd-autopilot/IPD-AUDIT-001/{stage['stageKey']}.md"],
                    "objectPath": f"workbench/ipd/cases/IPD-AUDIT-001/autopilot-packages/{stage['stageKey']}.json",
                }
                output_path = Path(stage["outputPath"])
                output_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (case_root / "case.json").write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            summary = ipd_case_main(
                [
                    "step",
                    "--case-id",
                    "IPD-AUDIT-001",
                    "--workspace-root",
                    str(workspace_root),
                ]
            )
            self.assertEqual(summary, 0)
            audited_case = read_ipd_case("IPD-AUDIT-001", workspace_root=str(workspace_root))
            self.assertEqual(audited_case["status"], "blocked")
            self.assertEqual(audited_case["currentStageKey"], "coding")
            coding_stage = next(stage for stage in audited_case["stages"] if stage["stageKey"] == "coding")
            self.assertEqual(coding_stage["status"], "rejected")
            self.assertIn("真实工程执行证据", coding_stage["blockedReason"])
            delivery_stage = next(stage for stage in audited_case["stages"] if stage["stageKey"] == "delivery")
            self.assertEqual(delivery_stage["status"], "pending")

    def test_reconcile_invalidates_completed_discovery_with_generated_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            case_root = chief_of_staff_ipd_case_root("IPD-AUDIT-DISC-001", workspace_root)
            initialize_ipd_case(
                case_id="IPD-AUDIT-DISC-001",
                title="audit invalid discovery",
                objective="验证 discovery 阶段也不能被生成物假完成。",
                task_description="旧版流程把生成物当成 discovery 完成证据。",
                workspace_root=str(workspace_root),
            )
            case_payload = read_ipd_case("IPD-AUDIT-DISC-001", workspace_root=str(workspace_root))
            discovery_stage = next(stage for stage in case_payload["stages"] if stage["stageKey"] == "discovery")
            discovery_stage["status"] = "completed"
            discovery_stage["completedAt"] = "2026-05-27T00:00:00+08:00"
            discovery_stage["submittedAt"] = "2026-05-27T00:00:00+08:00"
            discovery_stage["outputPath"] = (case_root / "outputs" / "discovery.json").as_posix()
            discovery_stage["outputSummary"] = "discovery fake completed"
            discovery_stage["approvals"] = [
                {"role": "ChiefProductOfficer", "status": "approved", "note": "", "updatedAt": "2026-05-27T00:00:00+08:00"},
                {"role": "CEO", "status": "approved", "note": "", "updatedAt": "2026-05-27T00:00:00+08:00"},
                {"role": "CEOChiefOfStaff", "status": "approved", "note": "", "updatedAt": "2026-05-27T00:00:00+08:00"},
            ]
            case_payload["status"] = "completed"
            case_payload["currentStageKey"] = ""
            case_payload["currentWorkItemPath"] = ""
            (case_root / "outputs").mkdir(parents=True, exist_ok=True)
            output_payload = {
                "schemaVersion": "1.0",
                "kind": "ipd-stage-output",
                "caseId": "IPD-AUDIT-DISC-001",
                "stageKey": "discovery",
                "phaseKey": discovery_stage["phaseKey"],
                "businessOwner": discovery_stage["businessOwner"],
                "actingOwner": discovery_stage["actingOwner"],
                "moduleExecutor": discovery_stage["moduleExecutor"],
                "gateOwner": discovery_stage["gateOwner"],
                "ownerRole": discovery_stage["ownerRole"],
                "participantRoles": list(discovery_stage.get("participantRoles", [])),
                "submittedAt": "2026-05-27T00:00:00+08:00",
                "summary": "discovery fake completed",
                "details": [],
                "evidence": ["workbench/ipd/cases/IPD-AUDIT-DISC-001/autopilot-packages/01-discovery.json"],
                "objectPath": "workbench/ipd/cases/IPD-AUDIT-DISC-001/autopilot-packages/01-discovery.json",
            }
            Path(discovery_stage["outputPath"]).write_text(
                json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (case_root / "case.json").write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            summary = ipd_case_main(
                [
                    "step",
                    "--case-id",
                    "IPD-AUDIT-DISC-001",
                    "--workspace-root",
                    str(workspace_root),
                ]
            )
            self.assertEqual(summary, 0)
            audited_case = read_ipd_case("IPD-AUDIT-DISC-001", workspace_root=str(workspace_root))
            self.assertEqual(audited_case["status"], "blocked")
            self.assertEqual(audited_case["currentStageKey"], "discovery")
            discovery_stage = next(stage for stage in audited_case["stages"] if stage["stageKey"] == "discovery")
            self.assertEqual(discovery_stage["status"], "rejected")
            self.assertIn("非 workbench/knowledge/autopilot", discovery_stage["blockedReason"])

    def test_autopilot_can_pause_for_manual_ceo_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-AUTO-MANUAL-001",
                title="manual ceo",
                objective="验证 CEO 人工签核暂停",
                task_description="autopilot 在 CEO 签核点暂停。",
                workspace_root=str(workspace_root),
            )
            result = run_case_autopilot(
                "IPD-AUTO-MANUAL-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
                auto_approve_roles=("CEOChiefOfStaff",),
            )
            self.assertEqual(result["status"], "paused-manual-approval")
            self.assertEqual(result["entryCheckpoint"], "ceo-demand")
            self.assertEqual(result["pendingRole"], "CEO")
            self.assertEqual(result["caseStatus"], "awaiting-intake-approvals")

    def test_autopilot_auto_signoff_still_records_web3_signature_material(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-AUTO-WEB3-001",
                title="autopilot web3 signoff",
                objective="验证启用 web3-simulated 签核后 autopilot 仍可自动签核。",
                task_description="autopilot 应为默认自动批准岗位写入签名材料，然后在 owner action 点暂停。",
                workspace_root=str(workspace_root),
            )
            result = run_case_autopilot(
                "IPD-AUTO-WEB3-001",
                workspace_root=str(workspace_root),
                enable_tridev_bridge=False,
            )
            self.assertEqual(result["status"], "paused-owner-action")
            self.assertEqual(result["pendingRole"], "ChiefProductOfficer")

            case_payload = read_ipd_case("IPD-AUTO-WEB3-001", workspace_root=str(workspace_root))
            approvals = case_payload["intake"]["approvals"]
            self.assertEqual([item["role"] for item in approvals], ["CEO", "CEOChiefOfStaff"])
            self.assertTrue(all(item["status"] == "approved" for item in approvals))
            self.assertTrue(all(str(item.get("signature") or "").startswith("0x") for item in approvals))
            self.assertTrue(all(str(item.get("publicKey") or "").startswith("0x04") for item in approvals))
            self.assertTrue(all(item.get("credentialType") == "simulated-mnemonic" for item in approvals))

    def test_cli_autopilot_manual_ceo_signoff_pauses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            initialize_ipd_case(
                case_id="IPD-CLI-AUTO-MANUAL-001",
                title="CLI manual ceo",
                objective="验证 CLI manual-ceo-signoff",
                task_description="通过 CLI 命令触发 CEO 人工签核暂停。",
                workspace_root=str(workspace_root),
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = ipd_case_main(
                    [
                        "autopilot",
                        "--case-id",
                        "IPD-CLI-AUTO-MANUAL-001",
                        "--workspace-root",
                        str(workspace_root),
                        "--no-tridev-bridge",
                        "--manual-ceo-signoff",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "paused-manual-approval")
            self.assertEqual(payload["entryCheckpoint"], "ceo-demand")
            self.assertEqual(payload["pendingRole"], "CEO")


if __name__ == "__main__":
    unittest.main(verbosity=2)
