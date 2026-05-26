from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
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
        "ownerRole": "CEOChiefOfStaff",
        "participantRoles": ("CEO", "ChiefMarketingOfficer"),
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
        "ownerRole": "ChiefProductOfficer",
        "participantRoles": (
            "CEOChiefOfStaff",
            "ChiefMarketingOfficer",
            "ChiefOperatingOfficer",
            "ChiefFinancialOfficer",
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
        "ownerRole": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "TriDev"),
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
        "ownerRole": "TriDev",
        "participantRoles": ("ChiefTechnologyOfficer", "TriTest"),
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
        "ownerRole": "TriTest",
        "participantRoles": ("TriDev", "ChiefTechnologyOfficer"),
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
        "ownerRole": "TriTest",
        "participantRoles": ("ChiefTechnologyOfficer", "TriDev"),
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
        "ownerRole": "TriTest",
        "participantRoles": ("ChiefProductOfficer", "ChiefTechnologyOfficer", "TriDev"),
        "schemaHint": {
            "objectType": "TRIDEV_QA_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "verify package",
            "redteam package",
        ),
        "outputRequirements": (
            "提交统一质量评分、放行结论和待修问题。",
            "明确是否允许部署。",
        ),
        "superDevReferenceStages": ("quality", "preview_confirm"),
    },
    {
        "stageKey": "deployment",
        "phaseKey": "DEPLOYMENT",
        "title": "Deployment / 部署交付",
        "ownerRole": "TriDeployment",
        "participantRoles": ("TriDev", "ChiefOperatingOfficer", "ChiefFinancialOfficer"),
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
            "明确是否进入 assurance 观察。",
        ),
        "superDevReferenceStages": ("delivery",),
    },
    {
        "stageKey": "assurance",
        "phaseKey": "ASSURANCE",
        "title": "Assurance / 运行保障",
        "ownerRole": "ChiefOperatingOfficer",
        "participantRoles": ("ChiefFinancialOfficer", "TriDeployment", "TriTest"),
        "schemaHint": {
            "objectType": "IPD_ASSURANCE_PACKAGE",
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
        "ownerRole": "CEOChiefOfStaff",
        "participantRoles": (
            "CEO",
            "ChiefOperatingOfficer",
            "ChiefFinancialOfficer",
            "ChiefProductOfficer",
            "ChiefTechnologyOfficer",
        ),
        "schemaHint": {
            "objectType": "IPD_DELIVERY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "assurance package",
            "最终交付清单",
            "版本签发材料",
        ),
        "outputRequirements": (
            "形成最终交付结论、版本化 gate package 和后续行动。",
            "确认 closeout、继续迭代或新一轮 intake。",
        ),
        "superDevReferenceStages": ("delivery",),
    },
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
                "ownerRole": template["ownerRole"],
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
    if submitted_by != stage["ownerRole"]:
        raise ValueError(f"{submitted_by} cannot submit stage owned by {stage['ownerRole']}")
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


def _reconcile_case_payload(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    now = _timestamp_now()
    advanced = False
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
            "ownerRole": stage["ownerRole"],
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
        "ownerRole": stage["ownerRole"],
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
        "ownerRole": stage["ownerRole"],
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
        "ownerRole": stage["ownerRole"],
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
        "currentOwnerRole": current_stage["ownerRole"] if current_stage else "",
        "currentWorkItemPath": case_payload.get("currentWorkItemPath") or "",
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "advanced": advanced,
        "casePath": _case_file_path(case_payload["caseId"], workspace_root).as_posix(),
        "intakeBriefPath": str(case_payload["intake"].get("briefPath") or ""),
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
        f"{stage['ownerRole']} 需要基于 CEO / 总助已整理并获签核的 intake briefing，"
        f"围绕目标“{case_payload['intake']['objective']}”推进 {stage['title']}（{stage['phaseKey']}）{participant_text}，"
        f"并在提交后等待总助初签与 CEO 终签。"
    )


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
