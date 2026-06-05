from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_ipd_case_root, chief_of_staff_ipd_cases_root


IPD_CASE_SCHEMA_VERSION = "1.0"
INTAKE_REQUIRED_APPROVERS = ("CEOChiefOfStaff", "CEO")
STAGE_REQUIRED_APPROVERS = ("CEOChiefOfStaff", "CEO")

_STAGE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "stageKey": "discovery",
        "phaseKey": "DISCOVERY",
        "title": "Discovery / 任务澄清",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": ("CEOChiefOfStaff", "CEO", "ChiefMarketingOfficer", "ChiefTechnologyOfficer"),
        "schemaHint": {
            "objectType": "IPD_DISCOVERY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "CEO / 总助正式任务",
            "intake briefing",
            "上游业务背景与当前阶段边界",
        ),
        "outputRequirements": (
            "沉淀任务意图、目标边界、成功信号和 Discovery 真源草稿。",
            "补齐最小 raw evidence pack、参考链接和后续需要验证的问题。",
        ),
        "superDevReferenceStages": ("research", "baseline"),
    },
    {
        "stageKey": "intelligence",
        "phaseKey": "INTELLIGENCE",
        "title": "Intelligence / 结构化输入",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": (
            "CEOChiefOfStaff",
            "ChiefMarketingOfficer",
            "ChiefOperatingOfficer",
            "ChiefFinancialOfficer",
            "ChiefTechnologyOfficer",
        ),
        "schemaHint": {
            "objectType": "IPD_INTELLIGENCE_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "Discovery package",
            "市场证据与机会线索",
            "运营约束",
            "预算护栏",
        ),
        "outputRequirements": (
            "把 Discovery 原始材料整理为结构化 Intelligence 输入包。",
            "收口 PRD、项目计划、验收标准和进入设计阶段的前门。",
        ),
        "superDevReferenceStages": ("docs", "docs_confirm", "prd"),
    },
    {
        "stageKey": "designing",
        "phaseKey": "DESIGNING",
        "title": "Designing / 技术设计",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "IPD_DESIGN_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "PRD",
            "项目计划",
            "验收标准",
        ),
        "outputRequirements": (
            "产出技术路线、工程门禁、任务拆解和 branch / phase handoff。",
            "明确 TriDev phase engine 接入要求与版本包约束。",
        ),
        "superDevReferenceStages": ("architecture", "uiux", "spec"),
    },
    {
        "stageKey": "coding",
        "phaseKey": "CODING",
        "title": "Coding / 开发实现",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_CODING_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "技术方案",
            "开发任务",
            "工程门禁",
        ),
        "outputRequirements": (
            "提交开发产物、实现证据、失败 / 回滚记录和候选发布 bundle。",
            "明确可进入验证阶段的代码、artifact 和执行摘要。",
        ),
        "superDevReferenceStages": ("frontend", "backend"),
    },
    {
        "stageKey": "verify-integration",
        "phaseKey": "VERIFY-INTEGRATION",
        "title": "Verify-Integration / 集成验证",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_VERIFY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "coding package",
            "测试计划",
        ),
        "outputRequirements": (
            "提交系统级验证结果、缺陷清单和集成测试证据。",
            "明确是否允许进入 redteam。",
        ),
        "superDevReferenceStages": ("quality",),
    },
    {
        "stageKey": "redteam",
        "phaseKey": "REDTEAM",
        "title": "Redteam / 对抗审查",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("CEOChiefOfStaff",),
        "schemaHint": {
            "objectType": "TRIDEV_REDTEAM_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "verify package",
            "攻击面与安全关注点",
        ),
        "outputRequirements": (
            "提交红队 / 安全对抗审查结果和高风险问题清单。",
            "明确是否允许进入 QA。",
        ),
        "superDevReferenceStages": ("quality",),
    },
    {
        "stageKey": "qa",
        "phaseKey": "QA",
        "title": "QA / 质量门禁",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_QA_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "verify package",
            "redteam package",
        ),
        "outputRequirements": (
            "提交统一质量评分、release readiness 结论和待修问题。",
            "形成 candidate delivery manifest / report，并明确是否允许部署。",
        ),
        "superDevReferenceStages": ("quality", "preview_confirm"),
    },
    {
        "stageKey": "deployment",
        "phaseKey": "DEPLOYMENT",
        "title": "Deployment / 部署交付",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefOperatingOfficer", "ChiefFinancialOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_DEPLOYMENT_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "qa package",
            "release bundle",
            "deployment checklist",
        ),
        "outputRequirements": (
            "提交部署证据、发布说明、上线窗口和 rollout 计划。",
            "明确是否进入上线后 assurance 观察。",
        ),
        "superDevReferenceStages": ("delivery", "rehearsal"),
    },
    {
        "stageKey": "assurance",
        "phaseKey": "ASSURANCE",
        "title": "Assurance / 运行保障",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefOperatingOfficer", "ChiefFinancialOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_ASSURANCE_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "deployment package",
            "运行观察指标",
            "恢复动作",
        ),
        "outputRequirements": (
            "提交运行保障结论、恢复验证、成本影响和 assurance evidence。",
            "明确是否达到可交付状态。",
        ),
        "superDevReferenceStages": ("delivery", "rehearsal"),
    },
    {
        "stageKey": "delivery",
        "phaseKey": "DELIVERY",
        "title": "Delivery / 最终交付",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": (
            "CEOChiefOfStaff",
            "CEO",
            "ChiefOperatingOfficer",
            "ChiefFinancialOfficer",
            "ChiefProductOfficer",
            "ChiefTechnologyOfficer",
        ),
        "schemaHint": {
            "objectType": "TRIDEV_DELIVERY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "assurance package",
            "最终交付清单",
            "版本签发材料",
        ),
        "outputRequirements": (
            "形成最终交付结论、final delivery manifest / report、版本化 gate package 和后续行动。",
            "确认 closeout、继续迭代或新一轮 intake。",
        ),
        "superDevReferenceStages": ("delivery",),
    },
)

_TRIDEV_RUN_MODE = "ipd-autopilot"
_AUTOPILOT_NOTE = "由 IPD autopilot 自动推进。"
_REAL_EXECUTION_STAGE_KEYS = (
    "coding",
    "verify-integration",
    "redteam",
    "qa",
    "deployment",
    "assurance",
    "delivery",
)
_REAL_EXECUTION_RESERVED_FILENAMES = {
    "release.zip",
    "release.sha256",
    "delivery-manifest.json",
    "gate-ledger.json",
    "workflow-summary.md",
    "events.jsonl",
    "artifact-bindings.json",
    "reference-evidence.json",
    "validation-report.json",
    "run-metadata.json",
    "release-file-manifest.json",
    "release-verification-report.json",
}
_REAL_EXECUTION_BLOCK_REASON = (
    "当前阶段需要真实工程执行证据（源码、测试、部署或运行产物），"
    "不能只依赖 workbench/docs/autopilot 生成物自动放行。"
)


def initialize_ipd_case(
    *,
    case_id: str,
    title: str,
    objective: str,
    task_description: str,
    created_by: str = "CEOChiefOfStaff",
    priority: str = "high",
    related_modules: Iterable[str] = (),
    constraints: Iterable[str] = (),
    opportunity_signals: Iterable[str] = (),
    business_model_fit: Iterable[str] = (),
    stage_fit: Iterable[str] = (),
    company_context: Iterable[str] = (),
    owner_proposal: Iterable[str] = (),
    resource_envelope: Iterable[str] = (),
    prerequisites: Iterable[str] = (),
    required_support: Iterable[str] = (),
    expected_outcomes: Iterable[str] = (),
    market_context: Iterable[str] = (),
    division_of_work: Iterable[str] = (),
    staffing_cost: Iterable[str] = (),
    other_cost: Iterable[str] = (),
    expected_delivery: str = "",
    required_approvers: Iterable[str] = INTAKE_REQUIRED_APPROVERS,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    now = _timestamp_now()
    normalized_case_id = _normalize_identifier(case_id)
    case_root = chief_of_staff_ipd_case_root(normalized_case_id, workspace_root)
    existing_case_payload: dict[str, Any] | None = None
    if case_root.exists():
        existing_case_payload = _load_case(normalized_case_id, workspace_root)
        if not _can_refine_intake(existing_case_payload):
            raise FileExistsError(f"IPD case already exists and cannot be reinitialized: {normalized_case_id}")
    else:
        case_root.mkdir(parents=True, exist_ok=True)
    approvals = _build_approvals(required_approvers, auto_approved_role=created_by, now=now)
    case_payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "caseId": normalized_case_id,
        "title": title.strip(),
        "status": "awaiting-intake-approvals",
        "priority": priority.strip() or "high",
        "relatedModules": _string_list(related_modules),
        "createdAt": str((existing_case_payload or {}).get("createdAt") or now),
        "updatedAt": now,
        "currentStageKey": "",
        "currentWorkItemPath": "",
        "intake": {
            "objective": objective.strip(),
            "taskDescription": task_description.strip(),
            "constraints": _string_list(constraints),
            "opportunitySignals": _merge_string_lists(opportunity_signals, market_context),
            "businessModelFit": _string_list(business_model_fit),
            "stageFit": _string_list(stage_fit),
            "companyContext": _string_list(company_context),
            "ownerProposal": _merge_string_lists(owner_proposal, division_of_work),
            "resourceEnvelope": _merge_string_lists(resource_envelope, staffing_cost, other_cost),
            "prerequisites": _string_list(prerequisites),
            "requiredSupport": _string_list(required_support),
            "expectedOutcomes": _string_list(expected_outcomes),
            "expectedDelivery": expected_delivery.strip(),
            "briefPath": "",
            "createdBy": created_by.strip() or "CEOChiefOfStaff",
            "createdAt": str(((existing_case_payload or {}).get("intake", {}) or {}).get("createdAt") or now),
            "approvals": approvals,
            "status": _approval_rollup(approvals),
        },
        "stages": [
            {
                "stageKey": template["stageKey"],
                "title": template["title"],
                "businessOwner": template["businessOwner"],
                "actingOwner": template["actingOwner"],
                "moduleExecutor": template["moduleExecutor"],
                "gateOwner": template["gateOwner"],
                "ownerRole": template["actingOwner"],
                "phaseKey": template["phaseKey"],
                "participantRoles": list(template["participantRoles"]),
                "status": "pending",
                "requiredApprovers": list(STAGE_REQUIRED_APPROVERS),
                "approvals": _build_approvals(STAGE_REQUIRED_APPROVERS, auto_approved_role=None, now=""),
                "schemaHint": dict(template["schemaHint"]),
                "inputRequirements": list(template["inputRequirements"]),
                "superDevReferenceStages": list(template["superDevReferenceStages"]),
                "workItemPath": "",
                "outputPath": "",
                "activatedAt": "",
                "submittedAt": "",
                "completedAt": "",
                "blockedReason": "",
                "outputSummary": "",
                "lastUpdatedAt": now,
            }
            for template in _STAGE_TEMPLATES
        ],
    }
    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
    _save_case(case_payload, workspace_root)
    _append_event(
        normalized_case_id,
        "intake-brief-refined" if existing_case_payload is not None else "case-initialized",
        {
            "createdBy": created_by,
            "intakeStatus": case_payload["intake"]["status"],
            "intakeBriefPath": intake_brief_path.as_posix(),
        },
        workspace_root=workspace_root,
    )
    return reconcile_ipd_case(normalized_case_id, workspace_root=workspace_root)


def reconcile_ipd_case(case_id: str, *, workspace_root: str | None = None) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    case_payload, summary = _reconcile_case_payload(case_payload, workspace_root=workspace_root)
    _save_case(case_payload, workspace_root)
    return summary


def reconcile_all_ipd_cases(*, workspace_root: str | None = None) -> dict[str, Any]:
    cases_root = chief_of_staff_ipd_cases_root(workspace_root)
    summaries: list[dict[str, Any]] = []
    if cases_root.exists():
        for case_root in sorted(path for path in cases_root.iterdir() if path.is_dir()):
            case_file = case_root / "case.json"
            if not case_file.exists():
                continue
            summaries.append(reconcile_ipd_case(case_root.name, workspace_root=workspace_root))
    return {
        "reconciledCaseCount": len(summaries),
        "advancedCaseCount": sum(1 for item in summaries if item["advanced"]),
        "completedCaseCount": sum(1 for item in summaries if item["status"] == "completed"),
        "cases": summaries,
    }


def record_intake_signoff(
    case_id: str,
    *,
    role: str,
    decision: str = "approved",
    note: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    now = _timestamp_now()
    _update_approval(case_payload["intake"]["approvals"], role=role, decision=decision, note=note, now=now)
    case_payload["intake"]["status"] = _approval_rollup(case_payload["intake"]["approvals"])
    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
    case_payload["updatedAt"] = now
    _append_event(
        case_payload["caseId"],
        "intake-signoff-recorded",
        {
            "role": role,
            "decision": decision,
            "note": note,
            "intakeBriefPath": intake_brief_path.as_posix(),
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return reconcile_ipd_case(case_payload["caseId"], workspace_root=workspace_root)


def submit_stage_output(
    case_id: str,
    *,
    stage_key: str,
    submitted_by: str,
    summary: str,
    details: Iterable[str] = (),
    evidence: Iterable[str] = (),
    object_path: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    stage = _require_stage(case_payload, stage_key)
    if case_payload.get("currentStageKey") != stage_key:
        raise ValueError(f"current stage is {case_payload.get('currentStageKey') or 'none'}, not {stage_key}")
    if submitted_by != stage["actingOwner"]:
        raise ValueError(f"{submitted_by} cannot submit stage owned by {stage['actingOwner']}")
    _validate_stage_submission_evidence(stage, evidence=evidence, object_path=object_path)
    now = _timestamp_now()
    output_path = _write_stage_output(
        case_payload,
        stage,
        summary=summary,
        details=details,
        evidence=evidence,
        object_path=object_path,
        workspace_root=workspace_root,
        written_at=now,
    )
    stage["status"] = "submitted"
    stage["outputPath"] = output_path.as_posix()
    stage["submittedAt"] = now
    stage["blockedReason"] = ""
    stage["outputSummary"] = summary.strip()
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["lastUpdatedAt"] = now
    case_payload["status"] = "awaiting-stage-approvals"
    case_payload["updatedAt"] = now
    _append_event(
        case_payload["caseId"],
        "stage-output-submitted",
        {
            "stageKey": stage_key,
            "submittedBy": submitted_by,
            "outputPath": output_path.as_posix(),
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return _summary_for_case(case_payload, advanced=False)


def record_stage_signoff(
    case_id: str,
    *,
    stage_key: str,
    role: str,
    decision: str = "approved",
    note: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    stage = _require_stage(case_payload, stage_key)
    if stage["status"] != "submitted":
        raise ValueError(f"stage {stage_key} is not ready for signoff: {stage['status']}")
    now = _timestamp_now()
    _update_approval(stage["approvals"], role=role, decision=decision, note=note, now=now)
    stage["lastUpdatedAt"] = now
    case_payload["updatedAt"] = now
    _append_event(
        case_payload["caseId"],
        "stage-signoff-recorded",
        {
            "stageKey": stage_key,
            "role": role,
            "decision": decision,
            "note": note,
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return reconcile_ipd_case(case_payload["caseId"], workspace_root=workspace_root)


def read_ipd_case(case_id: str, *, workspace_root: str | None = None) -> dict[str, Any]:
    return _load_case(case_id, workspace_root)


def run_case_autopilot(
    case_id: str,
    *,
    workspace_root: str | None = None,
    tridev_root: str | None = None,
    enable_tridev_bridge: bool = True,
    strict_release_bundle: bool = True,
    auto_approve_roles: Iterable[str] = STAGE_REQUIRED_APPROVERS,
) -> dict[str, Any]:
    normalized_case_id = _normalize_identifier(case_id)
    auto_approve_roles_set = set(_string_list(auto_approve_roles))
    if not auto_approve_roles_set:
        raise ValueError("auto_approve_roles must include at least one role")
    activity: list[dict[str, Any]] = []
    tridev_root_path: Path | None = None
    tridev_workflow: ModuleType | None = None
    tridev_run_id = _default_tridev_run_id(normalized_case_id)
    if enable_tridev_bridge:
        tridev_root_path = _resolve_tridev_root(workspace_root=workspace_root, tridev_root=tridev_root)
        tridev_workflow = _load_tridev_workflow_module(tridev_root_path)
        tridev_run_id = _ensure_tridev_run(
            case_id=normalized_case_id,
            case_payload=_load_case(normalized_case_id, workspace_root),
            tridev_workflow=tridev_workflow,
            tridev_root=tridev_root_path,
        )

    reconcile_ipd_case(normalized_case_id, workspace_root=workspace_root)
    max_iterations = len(_STAGE_TEMPLATES) * 8 + 16
    for _ in range(max_iterations):
        case_payload = _load_case(normalized_case_id, workspace_root)
        status = str(case_payload.get("status") or "").strip()
        if status == "completed":
            _append_event(
                normalized_case_id,
                "autopilot-completed",
                {
                    "activityCount": len(activity),
                    "tridevRunId": tridev_run_id if enable_tridev_bridge else "",
                },
                workspace_root=workspace_root,
            )
            return {
                "caseId": normalized_case_id,
                "status": status,
                "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
                "stageCount": len(case_payload["stages"]),
                "tridevBridgeEnabled": enable_tridev_bridge,
                "tridevRunId": tridev_run_id if enable_tridev_bridge else "",
                "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
                "actions": activity,
            }
        if status == "blocked":
            current_stage = _current_stage(case_payload)
            raise RuntimeError(
                "autopilot stopped because case is blocked"
                + (f" at stage {current_stage['stageKey']}" if current_stage else "")
            )
        if status == "awaiting-intake-approvals":
            role = _next_pending_approval_role(case_payload["intake"]["approvals"])
            if not role:
                raise RuntimeError("awaiting-intake-approvals but no pending intake approver")
            if role not in auto_approve_roles_set:
                return _autopilot_manual_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_role=role,
                    pending_stage_key="",
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            result = record_intake_signoff(
                normalized_case_id,
                role=role,
                decision="approved",
                note=_AUTOPILOT_NOTE,
                workspace_root=workspace_root,
            )
            activity.append({"type": "intake-signoff", "role": role, "status": result["status"]})
            continue
        if status == "waiting-stage-output":
            stage = _current_stage(case_payload)
            if stage is None:
                raise RuntimeError("waiting-stage-output but no current stage")
            if _stage_requires_real_execution(stage["stageKey"]):
                return _autopilot_real_execution_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_stage_key=stage["stageKey"],
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            submission = _build_autopilot_stage_submission(
                case_payload,
                stage,
                workspace_root=workspace_root,
                enable_tridev_bridge=enable_tridev_bridge,
                tridev_workflow=tridev_workflow,
                tridev_root=tridev_root_path,
                tridev_run_id=tridev_run_id,
                strict_release_bundle=strict_release_bundle,
            )
            result = submit_stage_output(
                normalized_case_id,
                stage_key=stage["stageKey"],
                submitted_by=stage["actingOwner"],
                summary=submission["summary"],
                details=submission["details"],
                evidence=submission["evidence"],
                object_path=submission["objectPath"],
                workspace_root=workspace_root,
            )
            activity.append(
                {
                    "type": "stage-submit",
                    "stageKey": stage["stageKey"],
                    "ownerRole": stage["actingOwner"],
                    "status": result["status"],
                }
            )
            continue
        if status == "awaiting-stage-approvals":
            stage = _current_stage(case_payload)
            if stage is None:
                raise RuntimeError("awaiting-stage-approvals but no current stage")
            role = _next_pending_approval_role(stage["approvals"])
            if not role:
                raise RuntimeError(f"awaiting-stage-approvals but no pending approver: {stage['stageKey']}")
            if role not in auto_approve_roles_set:
                return _autopilot_manual_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_role=role,
                    pending_stage_key=stage["stageKey"],
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            result = record_stage_signoff(
                normalized_case_id,
                stage_key=stage["stageKey"],
                role=role,
                decision="approved",
                note=_AUTOPILOT_NOTE,
                workspace_root=workspace_root,
            )
            activity.append(
                {
                    "type": "stage-signoff",
                    "stageKey": stage["stageKey"],
                    "role": role,
                    "status": result["status"],
                }
            )
            continue

        summary = reconcile_ipd_case(normalized_case_id, workspace_root=workspace_root)
        activity.append({"type": "reconcile", "status": summary["status"], "advanced": summary["advanced"]})

    raise RuntimeError("autopilot exceeded maximum iteration limit")


def _reconcile_case_payload(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    now = _timestamp_now()
    advanced = False
    integrity_issue = _find_real_execution_integrity_issue(case_payload, workspace_root=workspace_root)
    if integrity_issue is not None:
        _apply_real_execution_integrity_issue(
            case_payload,
            issue_stage_key=integrity_issue["stageKey"],
            issue_reason=integrity_issue["reason"],
            workspace_root=workspace_root,
            now=now,
        )
        case_payload["updatedAt"] = now
        return case_payload, _summary_for_case(case_payload, advanced=False, workspace_root=workspace_root)
    intake_status = _approval_rollup(case_payload["intake"]["approvals"])
    case_payload["intake"]["status"] = intake_status
    current_stage = _current_stage(case_payload)

    if current_stage is None:
        if intake_status == "rejected":
            case_payload["status"] = "blocked"
        elif intake_status != "approved":
            case_payload["status"] = "awaiting-intake-approvals"
        else:
            next_stage = _next_pending_stage(case_payload)
            if next_stage is None:
                case_payload["status"] = "completed"
            else:
                _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                advanced = True
    else:
        if current_stage["status"] == "submitted":
            stage_approval_status = _approval_rollup(current_stage["approvals"])
            if stage_approval_status == "rejected":
                current_stage["status"] = "rejected"
                current_stage["blockedReason"] = "节点签核被拒绝，等待责任岗位重新提交。"
                case_payload["status"] = "blocked"
            elif stage_approval_status == "approved":
                current_stage["status"] = "completed"
                current_stage["completedAt"] = now
                current_stage["blockedReason"] = ""
                case_payload["currentStageKey"] = ""
                case_payload["currentWorkItemPath"] = ""
                next_stage = _next_pending_stage(case_payload)
                if next_stage is None:
                    case_payload["status"] = "completed"
                else:
                    _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                    advanced = True
            else:
                case_payload["status"] = "awaiting-stage-approvals"
        elif current_stage["status"] == "rejected":
            case_payload["status"] = "blocked"
        elif current_stage["status"] == "in-progress":
            case_payload["status"] = "waiting-stage-output"
        elif current_stage["status"] == "completed":
            case_payload["currentStageKey"] = ""
            case_payload["currentWorkItemPath"] = ""
            next_stage = _next_pending_stage(case_payload)
            if next_stage is None:
                case_payload["status"] = "completed"
            else:
                _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                advanced = True

    case_payload["updatedAt"] = now
    return case_payload, _summary_for_case(case_payload, advanced=advanced, workspace_root=workspace_root)


def _activate_stage(
    case_payload: dict[str, Any],
    stage_key: str,
    *,
    workspace_root: str | None,
    activated_at: str,
) -> None:
    stage = _require_stage(case_payload, stage_key)
    stage["status"] = "in-progress"
    stage["activatedAt"] = activated_at
    stage["blockedReason"] = ""
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["lastUpdatedAt"] = activated_at
    work_item_path = _write_stage_work_item(case_payload, stage, workspace_root=workspace_root, written_at=activated_at)
    stage["workItemPath"] = work_item_path.as_posix()
    case_payload["currentStageKey"] = stage_key
    case_payload["currentWorkItemPath"] = work_item_path.as_posix()
    case_payload["status"] = "waiting-stage-output"
    _append_event(
        case_payload["caseId"],
        "stage-activated",
        {
            "stageKey": stage_key,
            "ownerRole": stage["actingOwner"],
            "workItemPath": work_item_path.as_posix(),
        },
        workspace_root=workspace_root,
    )


def _write_stage_work_item(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> Path:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    work_items_root = case_root / "work-items"
    work_items_root.mkdir(parents=True, exist_ok=True)
    path = work_items_root / f"{_stage_index(stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-work-item",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "title": f"{case_payload['title']} / {stage['title']}",
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "status": stage["status"],
        "createdAt": written_at,
        "updatedAt": written_at,
        "priority": case_payload["priority"],
        "summary": _stage_summary(case_payload, stage),
        "intake": {
            "objective": case_payload["intake"]["objective"],
            "taskDescription": case_payload["intake"]["taskDescription"],
            "constraints": list(case_payload["intake"]["constraints"]),
            "opportunitySignals": list(case_payload["intake"]["opportunitySignals"]),
            "businessModelFit": list(case_payload["intake"]["businessModelFit"]),
            "stageFit": list(case_payload["intake"]["stageFit"]),
            "companyContext": list(case_payload["intake"]["companyContext"]),
            "ownerProposal": list(case_payload["intake"]["ownerProposal"]),
            "resourceEnvelope": list(case_payload["intake"]["resourceEnvelope"]),
            "prerequisites": list(case_payload["intake"]["prerequisites"]),
            "requiredSupport": list(case_payload["intake"]["requiredSupport"]),
            "expectedOutcomes": list(case_payload["intake"]["expectedOutcomes"]),
            "expectedDelivery": case_payload["intake"]["expectedDelivery"],
            "briefPath": case_payload["intake"]["briefPath"],
        },
        "requiredApprovers": list(stage["requiredApprovers"]),
        "relatedModules": list(case_payload["relatedModules"]),
        "inputRefs": _input_refs(case_payload),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "outputRequirements": list(_stage_template(stage["stageKey"])["outputRequirements"]),
        "superDevReferenceStages": list(stage.get("superDevReferenceStages", [])),
        "schemaHint": dict(stage["schemaHint"]),
        "draftTemplate": _draft_template(case_payload, stage, written_at=written_at),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_stage_output(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    summary: str,
    details: Iterable[str],
    evidence: Iterable[str],
    object_path: str,
    workspace_root: str | None,
    written_at: str,
) -> Path:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    outputs_root = case_root / "outputs"
    outputs_root.mkdir(parents=True, exist_ok=True)
    path = outputs_root / f"{_stage_index(stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-output",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "submittedAt": written_at,
        "summary": summary.strip(),
        "details": _string_list(details),
        "evidence": _string_list(evidence),
        "objectPath": object_path.strip(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _draft_template(case_payload: dict[str, Any], stage: dict[str, Any], *, written_at: str) -> dict[str, Any]:
    stage_key = stage["stageKey"]
    return {
        "kind": "ipd-engine-native-draft",
        "objectType": stage["schemaHint"]["objectType"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "summary": _stage_summary(case_payload, stage),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "requiredOutput": list(_stage_template(stage_key)["outputRequirements"]),
        "superDevReferenceStages": list(stage.get("superDevReferenceStages", [])),
        "workflowRefs": [
            {
                "relation": "phase-package-for",
                "phase": stage["phaseKey"],
                "runId": f"run-{case_payload['caseId']}",
                "branchId": _branch_id(case_payload["caseId"]),
            }
        ],
    }


def _summary_for_case(
    case_payload: dict[str, Any],
    *,
    advanced: bool,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    current_stage = _current_stage(case_payload)
    return {
        "caseId": case_payload["caseId"],
        "title": case_payload["title"],
        "status": case_payload["status"],
        "currentStageKey": case_payload.get("currentStageKey") or "",
        "currentOwnerRole": current_stage["actingOwner"] if current_stage else "",
        "currentWorkItemPath": case_payload.get("currentWorkItemPath") or "",
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "advanced": advanced,
        "casePath": _case_file_path(case_payload["caseId"], workspace_root).as_posix(),
        "intakeBriefPath": str(case_payload["intake"].get("briefPath") or ""),
    }


def _build_autopilot_stage_submission(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    enable_tridev_bridge: bool,
    tridev_workflow: ModuleType | None,
    tridev_root: Path | None,
    tridev_run_id: str,
    strict_release_bundle: bool,
) -> dict[str, Any]:
    participant_record = _write_stage_participant_record(case_payload, stage, workspace_root=workspace_root)
    details = [
        f"{stage['actingOwner']} 已完成 {stage['title']} 自动提交。",
        f"岗位参与记录已写入 {participant_record['reference']}。",
    ]
    evidence = [participant_record["reference"]]
    tridev_report: dict[str, Any] | None = None
    if enable_tridev_bridge:
        if tridev_workflow is None or tridev_root is None:
            raise RuntimeError("TriDev bridge is enabled but TriDev workflow context is missing")
        tridev_report = _run_tridev_stage_automation(
            case_payload,
            stage,
            tridev_workflow=tridev_workflow,
            tridev_root=tridev_root,
            tridev_run_id=tridev_run_id,
            strict_release_bundle=strict_release_bundle,
        )
        details.append(f"TriDev 阶段 {stage['phaseKey']} 已完成 phase result 与 gate。")
        if tridev_report.get("bundleReference"):
            details.append(f"交付 bundle 已生成并校验：{tridev_report['bundleReference']}。")
        evidence.extend(tridev_report["evidenceRefs"])

    autopilot_package = _write_stage_autopilot_package(
        case_payload,
        stage,
        participant_record=participant_record,
        tridev_report=tridev_report,
        workspace_root=workspace_root,
    )
    evidence.append(autopilot_package["reference"])
    summary = f"{stage['title']} 已由 autopilot 自动提交并进入签核。"
    return {
        "summary": summary,
        "details": details,
        "evidence": evidence,
        "objectPath": autopilot_package["path"].as_posix(),
    }


def _run_tridev_stage_automation(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    tridev_workflow: ModuleType,
    tridev_root: Path,
    tridev_run_id: str,
    strict_release_bundle: bool,
) -> dict[str, Any]:
    phase_key = str(stage.get("phaseKey") or "").strip()
    if not phase_key:
        raise ValueError(f"missing phaseKey for stage {stage.get('stageKey')}")
    stage_artifact = _write_tridev_stage_artifact(case_payload, stage, tridev_root=tridev_root)
    stage_artifact_ref = _relative_to_root(tridev_root, stage_artifact)
    tridev_workflow.record_phase_result(
        tridev_root,
        run_id=tridev_run_id,
        stage=phase_key,
        status="completed",
        artifact_refs=[stage_artifact_ref],
        summary=f"{case_payload['caseId']} {stage['stageKey']} 自动推进完成。",
        branch_id=_branch_id(case_payload["caseId"]),
    )
    tridev_workflow.record_gate(
        tridev_root,
        run_id=tridev_run_id,
        stage=phase_key,
        status="approved",
        approved_by=stage["actingOwner"],
        comments=_AUTOPILOT_NOTE,
    )

    phase_result_file = _tridev_run_dir(tridev_root, tridev_run_id) / "phase-results" / f"{phase_key.lower().replace('-', '_')}.json"
    evidence_refs = [
        stage_artifact_ref,
        _relative_to_root(tridev_root, phase_result_file),
        _relative_to_root(tridev_root, _tridev_run_dir(tridev_root, tridev_run_id) / "gate-ledger.json"),
    ]
    bundle_reference = ""
    if phase_key == "DELIVERY":
        manifest_path = tridev_workflow.generate_delivery_manifest(
            tridev_root,
            run_id=tridev_run_id,
            strict=strict_release_bundle,
        )
        bundle_path = tridev_workflow.create_release_bundle(
            tridev_root,
            run_id=tridev_run_id,
            strict=strict_release_bundle,
        )
        verification = tridev_workflow.verify_release_bundle(tridev_root, run_id=tridev_run_id)
        if not verification["valid"]:
            raise RuntimeError("TriDev release bundle verification failed during autopilot")
        run_index_path = tridev_workflow.generate_run_index(tridev_root)
        evidence_refs.extend(
            [
                _relative_to_root(tridev_root, Path(manifest_path)),
                _relative_to_root(tridev_root, Path(bundle_path)),
                _relative_to_root(tridev_root, _tridev_run_dir(tridev_root, tridev_run_id) / "artifacts" / "release.sha256"),
                _relative_to_root(tridev_root, Path(run_index_path)),
            ]
        )
        bundle_reference = _relative_to_root(tridev_root, Path(bundle_path))
    return {
        "runId": tridev_run_id,
        "stage": phase_key,
        "evidenceRefs": evidence_refs,
        "bundleReference": bundle_reference,
    }


def _write_stage_participant_record(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, Any]:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    participants_root = case_root / "participant-records"
    participants_root.mkdir(parents=True, exist_ok=True)
    filename = f"{_stage_index(stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    path = participants_root / filename
    records_roles: list[str] = []
    for role in [stage["actingOwner"], *list(stage.get("participantRoles", []))]:
        normalized_role = str(role).strip()
        if normalized_role and normalized_role not in records_roles:
            records_roles.append(normalized_role)
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-participant-record",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "generatedAt": _timestamp_now(),
        "records": [
            {
                "role": role,
                "status": "completed",
                "summary": f"{role} 已在 {stage['stageKey']} 阶段完成 autopilot 协同条目。",
            }
            for role in records_roles
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "path": path,
        "reference": f"workbench/ipd/cases/{case_payload['caseId']}/participant-records/{filename}",
    }


def _write_stage_autopilot_package(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    participant_record: dict[str, Any],
    tridev_report: dict[str, Any] | None,
    workspace_root: str | None,
) -> dict[str, Any]:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    autopilot_root = case_root / "autopilot-packages"
    autopilot_root.mkdir(parents=True, exist_ok=True)
    filename = f"{_stage_index(stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    path = autopilot_root / filename
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-autopilot-stage-package",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "generatedAt": _timestamp_now(),
        "participantRecordRef": participant_record["reference"],
        "tridev": tridev_report or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "path": path,
        "reference": f"workbench/ipd/cases/{case_payload['caseId']}/autopilot-packages/{filename}",
    }


def _resolve_tridev_root(*, workspace_root: str | None, tridev_root: str | None) -> Path:
    if str(tridev_root or "").strip():
        path = Path(str(tridev_root)).resolve()
        if not path.exists():
            raise FileNotFoundError(f"TriDev root not found: {path}")
        return path
    candidates: list[Path] = []
    if str(workspace_root or "").strip():
        workspace = Path(str(workspace_root)).resolve()
        candidates.append(workspace.parent / "TriDev")
    source_repo_root = Path(__file__).resolve().parents[2]
    candidates.append(source_repo_root.parent / "TriDev")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("TriDev root not found; pass --tridev-root explicitly")


def _load_tridev_workflow_module(tridev_root: Path) -> ModuleType:
    tridev_src = tridev_root / "src"
    if not tridev_src.exists():
        raise FileNotFoundError(f"TriDev src not found: {tridev_src}")
    tridev_src_text = str(tridev_src)
    if tridev_src_text not in sys.path:
        sys.path.insert(0, tridev_src_text)
    return importlib.import_module("tridev.workflow")


def _ensure_tridev_run(
    *,
    case_id: str,
    case_payload: dict[str, Any],
    tridev_workflow: ModuleType,
    tridev_root: Path,
) -> str:
    run_id = _default_tridev_run_id(case_id)
    metadata_file = _tridev_run_dir(tridev_root, run_id) / "run-metadata.json"
    if metadata_file.exists():
        return run_id
    reference_evidence = tridev_workflow.ReferenceEvidence(
        upstream="TriCompany-IPD",
        referencePath=f"workbench/ipd/cases/{case_id}/intake-brief.json",
        vendorPath="TriDev/vendor/super-dev",
        license="internal-governed-use",
        commit=case_payload["updatedAt"],
        capabilityMapping=[template["stageKey"] for template in _STAGE_TEMPLATES],
        exclusions=[],
    )
    tridev_workflow.create_run(
        tridev_root,
        task=case_payload["intake"]["taskDescription"],
        mode=_TRIDEV_RUN_MODE,
        branch_id=_branch_id(case_id),
        run_id=run_id,
        reference_evidence=reference_evidence,
    )
    return run_id


def _write_tridev_stage_artifact(case_payload: dict[str, Any], stage: dict[str, Any], *, tridev_root: Path) -> Path:
    artifact_root = tridev_root / "docs" / "ipd-autopilot" / case_payload["caseId"]
    artifact_root.mkdir(parents=True, exist_ok=True)
    path = artifact_root / f"{_stage_index(stage['stageKey']) + 1:02d}-{stage['stageKey']}.md"
    lines = [
        f"# {case_payload['caseId']} - {stage['title']}",
        "",
        f"- phase: {stage['phaseKey']}",
        f"- businessOwner: {stage['businessOwner']}",
        f"- actingOwner: {stage['actingOwner']}",
        f"- moduleExecutor: {stage['moduleExecutor']}",
        f"- participants: {', '.join(stage.get('participantRoles', []))}",
        f"- generatedAt: {_timestamp_now()}",
        "",
        "## Intake Objective",
        case_payload["intake"]["objective"],
        "",
        "## Stage Summary",
        f"{stage['title']} 已由 IPD autopilot 自动推进并写入 TriDev phase result / gate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _tridev_run_dir(tridev_root: Path, run_id: str) -> Path:
    return tridev_root / "docs" / "runs" / run_id


def _default_tridev_run_id(case_id: str) -> str:
    return "ipd-" + case_id.replace("_", "-").replace(".", "-").lower()


def _relative_to_root(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _next_pending_approval_role(approvals: list[dict[str, str]]) -> str:
    for approval in approvals:
        if approval["status"] == "pending":
            return approval["role"]
    return ""


def _autopilot_manual_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    pending_role: str,
    pending_stage_key: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-manual-approval",
        {
            "pendingRole": pending_role,
            "pendingStageKey": pending_stage_key,
            "caseStatus": case_status,
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-manual-approval",
        "caseStatus": case_status,
        "pendingRole": pending_role,
        "pendingStageKey": pending_stage_key,
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path or tridev_run_id),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _autopilot_real_execution_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    pending_stage_key: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-real-execution",
        {
            "pendingStageKey": pending_stage_key,
            "caseStatus": case_status,
            "reason": _REAL_EXECUTION_BLOCK_REASON,
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-real-execution",
        "caseStatus": case_status,
        "pendingStageKey": pending_stage_key,
        "reason": _REAL_EXECUTION_BLOCK_REASON,
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path or tridev_run_id),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _case_file_path(case_id: str, workspace_root: str | None) -> Path:
    return chief_of_staff_ipd_case_root(case_id, workspace_root) / "case.json"


def _intake_brief_file_path(case_id: str, workspace_root: str | None) -> Path:
    return chief_of_staff_ipd_case_root(case_id, workspace_root) / "intake-brief.json"


def _events_file_path(case_id: str, workspace_root: str | None) -> Path:
    return chief_of_staff_ipd_case_root(case_id, workspace_root) / "events.jsonl"


def _load_case(case_id: str, workspace_root: str | None) -> dict[str, Any]:
    normalized_case_id = _normalize_identifier(case_id)
    case_path = _case_file_path(normalized_case_id, workspace_root)
    if not case_path.exists():
        raise FileNotFoundError(f"IPD case not found: {normalized_case_id}")
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid case payload: {normalized_case_id}")
    _ensure_case_defaults(payload)
    return payload


def _save_case(case_payload: dict[str, Any], workspace_root: str | None) -> None:
    case_path = _case_file_path(case_payload["caseId"], workspace_root)
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_event(
    case_id: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> None:
    path = _events_file_path(case_id, workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "timestamp": _timestamp_now(),
        "eventType": event_type,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(body, ensure_ascii=False) + "\n")


def _ensure_case_defaults(case_payload: dict[str, Any]) -> None:
    intake = case_payload.setdefault("intake", {})
    intake["constraints"] = _string_list(intake.get("constraints", ()))
    intake["opportunitySignals"] = _merge_string_lists(intake.get("opportunitySignals", ()), intake.get("marketContext", ()))
    intake["businessModelFit"] = _string_list(intake.get("businessModelFit", ()))
    intake["stageFit"] = _string_list(intake.get("stageFit", ()))
    intake["companyContext"] = _string_list(intake.get("companyContext", ()))
    intake["ownerProposal"] = _merge_string_lists(intake.get("ownerProposal", ()), intake.get("roughDivisionOfWork", ()))
    intake["resourceEnvelope"] = _merge_string_lists(
        intake.get("resourceEnvelope", ()),
        intake.get("staffingCost", ()),
        intake.get("otherCosts", ()),
    )
    intake["prerequisites"] = _string_list(intake.get("prerequisites", ()))
    intake["requiredSupport"] = _string_list(intake.get("requiredSupport", ()))
    intake["expectedOutcomes"] = _string_list(intake.get("expectedOutcomes", ()))
    text_fields = (
        "objective",
        "taskDescription",
        "expectedDelivery",
        "briefPath",
        "createdBy",
        "createdAt",
        "status",
    )
    for field in text_fields:
        intake[field] = str(intake.get(field, "") or "").strip()
    intake["approvals"] = _normalize_approvals(intake.get("approvals"), INTAKE_REQUIRED_APPROVERS)
    for stage in case_payload.get("stages", []):
        if not isinstance(stage, dict):
            continue
        template = _stage_template(stage.get("stageKey", ""))
        stage["businessOwner"] = str(stage.get("businessOwner") or template["businessOwner"]).strip()
        stage["actingOwner"] = str(stage.get("actingOwner") or template["actingOwner"]).strip()
        stage["moduleExecutor"] = str(stage.get("moduleExecutor") or template["moduleExecutor"]).strip()
        stage["gateOwner"] = str(stage.get("gateOwner") or template["gateOwner"]).strip()
        stage["ownerRole"] = str(stage.get("ownerRole") or stage["actingOwner"]).strip()
        stage["requiredApprovers"] = list(STAGE_REQUIRED_APPROVERS)
        stage["approvals"] = _normalize_approvals(stage.get("approvals"), STAGE_REQUIRED_APPROVERS)
        stage["phaseKey"] = str(stage.get("phaseKey") or template["phaseKey"]).strip()
        stage["participantRoles"] = _string_list(stage.get("participantRoles", template["participantRoles"]))
        stage["inputRequirements"] = _string_list(stage.get("inputRequirements", template["inputRequirements"]))
        stage["superDevReferenceStages"] = _string_list(
            stage.get("superDevReferenceStages", template["superDevReferenceStages"])
        )
    case_payload["currentWorkItemPath"] = str(case_payload.get("currentWorkItemPath", "") or "").strip()


def _write_intake_brief(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> Path:
    path = _intake_brief_file_path(case_payload["caseId"], workspace_root)
    intake = case_payload["intake"]
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-intake-brief",
        "caseId": case_payload["caseId"],
        "title": case_payload["title"],
        "priority": case_payload["priority"],
        "status": intake["status"],
        "createdAt": intake["createdAt"],
        "updatedAt": written_at,
        "createdBy": intake["createdBy"],
        "relatedModules": list(case_payload["relatedModules"]),
        "requiredApprovers": [approval["role"] for approval in intake["approvals"]],
        "approvals": list(intake["approvals"]),
        "objective": intake["objective"],
        "taskDescription": intake["taskDescription"],
        "constraints": list(intake["constraints"]),
        "expectedDelivery": intake["expectedDelivery"],
        "briefing": {
            "opportunitySignals": list(intake["opportunitySignals"]),
            "businessModelFit": list(intake["businessModelFit"]),
            "stageFit": list(intake["stageFit"]),
            "companyContext": list(intake["companyContext"]),
            "ownerProposal": list(intake["ownerProposal"]),
            "resourceEnvelope": list(intake["resourceEnvelope"]),
            "prerequisites": list(intake["prerequisites"]),
            "requiredSupport": list(intake["requiredSupport"]),
            "expectedOutcomes": list(intake["expectedOutcomes"]),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _current_stage(case_payload: dict[str, Any]) -> dict[str, Any] | None:
    current_stage_key = str(case_payload.get("currentStageKey") or "").strip()
    if not current_stage_key:
        return None
    return next(
        (stage for stage in case_payload["stages"] if stage["stageKey"] == current_stage_key),
        None,
    )


def _can_refine_intake(case_payload: dict[str, Any]) -> bool:
    if str(case_payload.get("currentStageKey") or "").strip():
        return False
    return all(str(stage.get("status") or "pending") == "pending" for stage in case_payload.get("stages", []))


def _next_pending_stage(case_payload: dict[str, Any]) -> dict[str, Any] | None:
    return next((stage for stage in case_payload["stages"] if stage["status"] == "pending"), None)


def _require_stage(case_payload: dict[str, Any], stage_key: str) -> dict[str, Any]:
    return next(
        stage for stage in case_payload["stages"] if stage["stageKey"] == stage_key
    )


def _stage_template(stage_key: str) -> dict[str, Any]:
    return next(template for template in _STAGE_TEMPLATES if template["stageKey"] == stage_key)


def _stage_index(stage_key: str) -> int:
    return next(index for index, template in enumerate(_STAGE_TEMPLATES) if template["stageKey"] == stage_key)


def _input_refs(case_payload: dict[str, Any]) -> list[str]:
    refs = []
    if str(case_payload["intake"].get("briefPath") or "").strip():
        refs.append("workbench/ipd/cases/" + case_payload["caseId"] + "/intake-brief.json")
    refs.append("workbench/ipd/cases/" + case_payload["caseId"] + "/case.json")
    refs.extend(
        stage["outputPath"]
        for stage in case_payload["stages"]
        if str(stage.get("outputPath") or "").strip()
    )
    return refs


def _stage_summary(case_payload: dict[str, Any], stage: dict[str, Any]) -> str:
    participants = "、".join(_string_list(stage.get("participantRoles", ())))
    participant_text = f"并协同 {participants}" if participants else ""
    return (
        f"{stage['actingOwner']} 需要基于 CEO / 总助已整理并获签核的 intake briefing，"
        f"围绕目标“{case_payload['intake']['objective']}”推进 {stage['title']}（{stage['phaseKey']}）{participant_text}，"
        f"并在提交后等待总助初签与 CEO 终签。"
    )


def _stage_requires_real_execution(stage_key: str) -> bool:
    return str(stage_key or "").strip() in _REAL_EXECUTION_STAGE_KEYS


def _validate_stage_submission_evidence(
    stage: dict[str, Any],
    *,
    evidence: Iterable[str],
    object_path: str,
) -> None:
    if not _stage_requires_real_execution(stage.get("stageKey", "")):
        return
    refs = [*(_string_list(evidence)), str(object_path or "").strip()]
    if _has_real_execution_evidence(refs):
        return
    raise ValueError(
        f"stage {stage['stageKey']} requires at least one real source/test/deploy evidence path outside docs/workbench generated artifacts"
    )


def _has_real_execution_evidence(refs: Iterable[str]) -> bool:
    for ref in refs:
        normalized = str(ref or "").strip().replace("\\", "/")
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered.startswith(("docs/", "knowledge/", "workbench/")):
            continue
        if any(segment in lowered for segment in ("/docs/", "/knowledge/", "/workbench/")):
            continue
        if any(segment in lowered for segment in ("/participant-records/", "/autopilot-packages/", "/phase-results/")):
            continue
        if lowered.endswith(".md"):
            continue
        filename = Path(lowered).name
        if filename in _REAL_EXECUTION_RESERVED_FILENAMES:
            continue
        return True
    return False


def _find_real_execution_integrity_issue(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, str] | None:
    for stage in case_payload.get("stages", []):
        stage_key = str(stage.get("stageKey") or "").strip()
        if not _stage_requires_real_execution(stage_key):
            continue
        if str(stage.get("status") or "").strip() not in {"submitted", "completed"}:
            continue
        output_payload = _load_stage_output_payload(case_payload, stage, workspace_root=workspace_root)
        refs: list[str] = []
        if output_payload is not None:
            refs.extend(_string_list(output_payload.get("evidence", ())))
            refs.append(str(output_payload.get("objectPath") or "").strip())
        if _has_real_execution_evidence(refs):
            continue
        return {
            "stageKey": stage_key,
            "reason": _REAL_EXECUTION_BLOCK_REASON,
        }
    return None


def _load_stage_output_payload(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, Any] | None:
    output_path_text = str(stage.get("outputPath") or "").strip()
    if not output_path_text:
        return None
    output_path = Path(output_path_text)
    if not output_path.is_absolute():
        output_path = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root) / output_path
    if not output_path.exists():
        return None
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _apply_real_execution_integrity_issue(
    case_payload: dict[str, Any],
    *,
    issue_stage_key: str,
    issue_reason: str,
    workspace_root: str | None,
    now: str,
) -> None:
    issue_stage = _require_stage(case_payload, issue_stage_key)
    should_emit_event = (
        str(case_payload.get("status") or "").strip() != "blocked"
        or str(issue_stage.get("blockedReason") or "").strip() != issue_reason
    )
    reset_downstream = False
    for stage in case_payload["stages"]:
        if stage["stageKey"] == issue_stage_key:
            reset_downstream = True
            stage["status"] = "rejected"
            stage["outputPath"] = ""
            stage["submittedAt"] = ""
            stage["completedAt"] = ""
            stage["blockedReason"] = issue_reason
            stage["outputSummary"] = ""
            stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
            stage["lastUpdatedAt"] = now
            continue
        if not reset_downstream:
            continue
        _reset_stage_to_pending(stage, now=now)
    case_payload["status"] = "blocked"
    case_payload["currentStageKey"] = issue_stage_key
    case_payload["currentWorkItemPath"] = str(issue_stage.get("workItemPath") or "").strip()
    if should_emit_event:
        _append_event(
            case_payload["caseId"],
            "real-execution-evidence-missing",
            {
                "stageKey": issue_stage_key,
                "reason": issue_reason,
            },
            workspace_root=workspace_root,
        )


def _reset_stage_to_pending(stage: dict[str, Any], *, now: str) -> None:
    stage["status"] = "pending"
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["workItemPath"] = ""
    stage["outputPath"] = ""
    stage["activatedAt"] = ""
    stage["submittedAt"] = ""
    stage["completedAt"] = ""
    stage["blockedReason"] = ""
    stage["outputSummary"] = ""
    stage["lastUpdatedAt"] = now


def _build_approvals(
    roles: Iterable[str],
    *,
    auto_approved_role: str | None,
    now: str,
) -> list[dict[str, str]]:
    approvals: list[dict[str, str]] = []
    for index, role in enumerate(_string_list(roles)):
        auto_approved = auto_approved_role is not None and role == auto_approved_role and index == 0
        approvals.append(
            {
                "role": role,
                "status": "approved" if auto_approved else "pending",
                "note": "创建动作已视为当前角色签核" if auto_approved else "",
                "updatedAt": now if auto_approved else "",
            }
        )
    return approvals


def _merge_string_lists(*values: Iterable[str]) -> list[str]:
    merged: list[str] = []
    for value in values:
        merged.extend(_string_list(value))
    return merged


def _approval_snapshot(roles: Iterable[str]) -> list[dict[str, str]]:
    return [
        {
            "role": role,
            "status": "pending",
            "note": "",
        }
        for role in _string_list(roles)
    ]


def _normalize_approvals(
    approvals: object,
    required_roles: Iterable[str],
) -> list[dict[str, str]]:
    existing_by_role: dict[str, dict[str, Any]] = {}
    if isinstance(approvals, list):
        for item in approvals:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            if role:
                existing_by_role[role] = item
    normalized: list[dict[str, str]] = []
    prior_approved = True
    for role in _string_list(required_roles):
        existing = existing_by_role.get(role, {})
        status = str(existing.get("status") or "pending").strip() or "pending"
        if not prior_approved and status != "pending":
            status = "pending"
            note = ""
            updated_at = ""
        else:
            note = str(existing.get("note") or "").strip()
            updated_at = str(existing.get("updatedAt") or "").strip()
        normalized.append(
            {
                "role": role,
                "status": status,
                "note": note,
                "updatedAt": updated_at,
            }
        )
        prior_approved = prior_approved and status == "approved"
    return normalized


def _update_approval(
    approvals: list[dict[str, str]],
    *,
    role: str,
    decision: str,
    note: str,
    now: str,
) -> None:
    normalized = decision.strip().lower()
    if normalized not in {"approved", "rejected"}:
        raise ValueError(f"unsupported decision: {decision}")
    for index, approval in enumerate(approvals):
        if approval["role"] != role:
            continue
        for predecessor in approvals[:index]:
            if predecessor["status"] != "approved":
                raise ValueError(f"{role} cannot sign before {predecessor['role']}")
        approval["status"] = normalized
        approval["note"] = note.strip()
        approval["updatedAt"] = now
        return
    raise ValueError(f"approval role not found: {role}")


def _approval_rollup(approvals: list[dict[str, str]]) -> str:
    statuses = {str(item.get("status") or "pending") for item in approvals}
    if "rejected" in statuses:
        return "rejected"
    if statuses == {"approved"}:
        return "approved"
    return "pending"


def _normalize_identifier(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("case_id is required")
    normalized = []
    for character in text:
        if character.isalnum() or character in {"-", "_", "."}:
            normalized.append(character)
        else:
            normalized.append("-")
    identifier = "".join(normalized).strip("-")
    if not identifier:
        raise ValueError("case_id must contain at least one valid identifier character")
    return identifier


def _branch_id(case_id: str) -> str:
    return "ipd-" + case_id.replace(".", "-").replace("_", "-").lower()


def _string_list(values: Iterable[str]) -> list[str]:
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            items.append(text)
    return items


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
