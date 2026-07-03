from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.ipd_case_engine import (
    freeze_ipd_case,
    INTAKE_REQUIRED_APPROVERS,
    initialize_ipd_case,
    read_ipd_case,
    record_intake_signoff,
    rollback_ipd_case,
    record_stage_signoff,
    reconcile_all_ipd_cases,
    reconcile_ipd_case,
    run_discovery_stage_automation,
    run_intelligence_stage_automation,
    run_case_autopilot,
    submit_stage_output,
    unfreeze_ipd_case,
)
from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_ipd_cases_root


_CASE_SHORT_NAME_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("平台", "platform", "gateway", "模型", "api"), "PLATFORM"),
    (("流程", "workflow", "runtime", "orchestration", "编排"), "WORKFLOW"),
    (("训练", "training", "教程", "guide"), "TRAINING"),
    (("测试", "qa", "validation", "verify"), "VALIDATION"),
    (("部署", "deployment", "release", "上线"), "DEPLOYMENT"),
    (("研发", "engineering", "develop", "开发"), "ENGINEERING"),
)
_CASE_SHORT_NAME_STOPWORDS = {
    "IPD",
    "CEO",
    "CTO",
    "CPO",
    "COO",
    "CFO",
    "MVP",
    "PRD",
    "TRICOMPANY",
    "TRIDEV",
    "DISCOVERY",
    "INTELLIGENCE",
    "DESIGNING",
    "CODING",
    "DELIVERY",
    "STAGE",
    "CASE",
    "TASK",
}

# Derived from the project-level module source of truth:
# - TriMetaverse/docs/三元宇宙架构与模块说明.md
# - TriMetaverse/docs/registry/business-strategy-module-map.md
# The intake-side inference keeps TriCompany as the default coordinator, then
# adds modules whose central responsibilities are explicitly mentioned by the
# task description.
_MODULE_ROUTING_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("TriMetaverse",), ("架构", "模块说明", "reference", "中央", "registry", "项目级", "模块边界")),
    (("TriMC",), ("runtime", "planner", "context", "agent runtime", "interaction", "服务域", "工具编排", "模型调用", "harness", "cron")),
    (("TriHost",), ("宿主", "host", "copilot-host", "正式接管", "多 host", "切换")),
    (("TriSkill",), ("skill", "技能", "技能封装")),
    (("TriLC",), ("本地", "local", "本地域", "detached", "tool bus", "本地节点")),
    (("TriPilot", "Tride", "vscodium"), ("桌面", "pc 端", "ide", "vscode", "vscodium", "cli", "扩展", "插件", "vibe coding", "webview")),
    (("TriStaciss",), ("模型 api", "模型api", "api 平台", "统一模型", "多 provider", "provider", "openai", "claude", "sdk", "接口转换", "模型路由", "中转平台")),
    (("TriAvatar",), ("web 端", "web入口", "前端", "浏览器", "browser", "聊天", "chat", "群聊", "avatar", "分身", "宠物")),
    (("TriGateway",), ("网关", "gateway", "消息", "message", "队列", "queue", "社交通道")),
    (("TriDev",), ("开发", "研发", "工程", "交付", "discovery", "intelligence", "designing", "coding", "delivery", "gate", "autopilot", "shadow test")),
    (("TriDeployment",), ("部署", "上线", "发布", "deployment", "rollout", "gitops", "k8s", "镜像")),
    (("TriTest",), ("测试", "回归", "qa", "质量", "验收", "verify", "validation", "redteam", "assurance", "ci")),
    (("TriMobile",), ("移动端", "mobile", "ios", "android", "app", "小程序")),
    (("TriMem",), ("用户系统", "用户", "账号", "身份", "登录", "认证", "鉴权", "数据库", "schema", "profile")),
    (("TriWeb4",), ("wallet", "钱包", "合约", "web3", "web4", "dapp", "contract")),
    (("TriChain",), ("公链", "链上", "onchain", "区块链", "主网", "rpc")),
)
_LOCAL_EXECUTION_HINTS: tuple[str, ...] = ("本地", "local", "本地域", "tool bus", "本地节点", "detached")
_MODULE_ROUTING_MODES = ("deterministic", "cpo", "auto")
_CPO_MODULE_ROUTER_COMMAND_ENV = "TRICOMPANY_CPO_MODULE_ROUTER_COMMAND"
_CPO_MODULE_ROUTER_TIMEOUT_ENV = "TRICOMPANY_CPO_MODULE_ROUTER_TIMEOUT_SECONDS"
_DEFAULT_CPO_MODULE_ROUTER_TIMEOUT_SECONDS = 20.0
_SOURCE_OF_TRUTH_REFS: tuple[str, ...] = (
    "TriMetaverse/docs/三元宇宙架构与模块说明.md",
    "TriMetaverse/docs/registry/business-strategy-module-map.md",
)
_MODULE_NAME_ALIASES = {
    "trimetaverse": "TriMetaverse",
    "tricompany": "TriCompany",
    "trimc": "TriMC",
    "trihost": "TriHost",
    "triskill": "TriSkill",
    "trilc": "TriLC",
    "tripilot": "TriPilot",
    "tride": "Tride",
    "vscodium": "vscodium",
    "tristaciss": "TriStaciss",
    "tristacis": "TriStaciss",
    "triavatar": "TriAvatar",
    "trigateway": "TriGateway",
    "trigatway": "TriGateway",
    "tridev": "TriDev",
    "trideployment": "TriDeployment",
    "tritest": "TriTest",
    "trimobile": "TriMobile",
    "trimem": "TriMem",
    "triweb4": "TriWeb4",
    "trichain": "TriChain",
}
_MODULE_CATALOG: tuple[str, ...] = tuple(dict.fromkeys(_MODULE_NAME_ALIASES.values()))


class _ModuleRoutingUnavailable(RuntimeError):
    pass


class _ModuleRoutingEscalationRequired(RuntimeError):
    pass


def _matches_module_hint(source_text: str, lowered: str, keyword: str) -> bool:
    return (keyword.lower() in lowered) if keyword.isascii() else (keyword in source_text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage chief-of-staff IPD cases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    task_intake_parser = subparsers.add_parser(
        "task-intake",
        help="Accept a CEO/chief-of-staff freeform task and create a rough IPD intake briefing draft.",
    )
    task_intake_parser.add_argument("task", nargs="+")
    task_intake_parser.add_argument(
        "--case-id",
        help="Optional governed IPD case id. Prefer date-first ids such as IPD-20260611-PLATFORM-001 or leave blank to auto-generate.",
    )
    task_intake_parser.add_argument("--title")
    task_intake_parser.add_argument("--objective")
    task_intake_parser.add_argument("--priority", default="high")
    task_intake_parser.add_argument("--created-by", default="CEOChiefOfStaff")
    task_intake_parser.add_argument("--case-category", default="")
    task_intake_parser.add_argument("--reference-theme", default="")
    task_intake_parser.add_argument("--related-module", action="append", default=[])
    task_intake_parser.add_argument(
        "--module-routing-mode",
        choices=_MODULE_ROUTING_MODES,
        default="auto",
        help=(
            "How task-intake infers related modules when --related-module is not provided: "
            "deterministic uses local rules, cpo requires a CPO router hook, auto tries CPO and falls back to deterministic."
        ),
    )
    task_intake_parser.add_argument("--constraint", action="append", default=[])
    task_intake_parser.add_argument(
        "--slot-answer",
        action="append",
        default=[],
        help="Fill one intake clarification slot as key=value, for example competitorReference=Cursor, Devin.",
    )
    task_intake_parser.add_argument("--require-approver", action="append", default=[])
    task_intake_parser.add_argument("--workspace-root")

    init_parser = subparsers.add_parser("init", help="Initialize or refine an IPD intake briefing.")
    init_parser.add_argument(
        "--case-id",
        required=True,
        help="Governed IPD case id. Prefer date-first ids such as IPD-20260611-PLATFORM-001.",
    )
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--task-description", required=True)
    init_parser.add_argument("--created-by", default="CEOChiefOfStaff")
    init_parser.add_argument("--priority", default="high")
    init_parser.add_argument("--case-category", default="")
    init_parser.add_argument("--reference-theme", default="")
    init_parser.add_argument("--related-module", action="append", default=[])
    init_parser.add_argument("--constraint", action="append", default=[])
    init_parser.add_argument("--opportunity-signal", action="append", default=[])
    init_parser.add_argument("--business-model-fit", action="append", default=[])
    init_parser.add_argument("--stage-fit", action="append", default=[])
    init_parser.add_argument("--company-context", action="append", default=[])
    init_parser.add_argument("--owner-proposal", action="append", default=[])
    init_parser.add_argument("--resource-envelope", action="append", default=[])
    init_parser.add_argument("--prerequisite", action="append", default=[])
    init_parser.add_argument("--required-support", action="append", default=[])
    init_parser.add_argument("--expected-outcome", action="append", default=[])
    init_parser.add_argument(
        "--slot-answer",
        action="append",
        default=[],
        help="Fill one intake clarification slot as key=value.",
    )
    init_parser.add_argument("--market-context", action="append", default=[], help=argparse.SUPPRESS)
    init_parser.add_argument("--division-of-work", action="append", default=[], help=argparse.SUPPRESS)
    init_parser.add_argument("--staffing-cost", action="append", default=[], help=argparse.SUPPRESS)
    init_parser.add_argument("--other-cost", action="append", default=[], help=argparse.SUPPRESS)
    init_parser.add_argument("--expected-delivery", default="")
    init_parser.add_argument("--require-approver", action="append", default=[])
    init_parser.add_argument("--workspace-root")

    intake_approve_parser = subparsers.add_parser("intake-approve", help="Record intake signoff.")
    intake_approve_parser.add_argument("--case-id", required=True)
    intake_approve_parser.add_argument("--role", required=True)
    intake_approve_parser.add_argument("--decision", default="approved", choices=["approved", "rejected"])
    intake_approve_parser.add_argument("--note", default="")
    intake_approve_parser.add_argument("--signing-key", default="")
    intake_approve_parser.add_argument("--mnemonic", default="")
    intake_approve_parser.add_argument("--workspace-root")

    freeze_parser = subparsers.add_parser("freeze", help="Temporarily freeze an IPD case until blocking conditions are cleared.")
    freeze_parser.add_argument("--case-id", required=True)
    freeze_parser.add_argument("--role", required=True)
    freeze_parser.add_argument("--reason", required=True)
    freeze_parser.add_argument("--domain", default="")
    freeze_parser.add_argument("--workspace-root")

    unfreeze_parser = subparsers.add_parser("unfreeze", help="Resume a frozen IPD case after blocking conditions are cleared.")
    unfreeze_parser.add_argument("--case-id", required=True)
    unfreeze_parser.add_argument("--role", required=True)
    unfreeze_parser.add_argument("--note", default="")
    unfreeze_parser.add_argument("--workspace-root")

    submit_parser = subparsers.add_parser("submit", help="Submit output for the current IPD stage.")
    submit_parser.add_argument("--case-id", required=True)
    submit_parser.add_argument("--stage-key", required=True)
    submit_parser.add_argument("--submitted-by", required=True)
    submit_parser.add_argument("--summary", required=True)
    submit_parser.add_argument("--detail", action="append", default=[])
    submit_parser.add_argument("--evidence", action="append", default=[])
    submit_parser.add_argument("--object-path", default="")
    submit_parser.add_argument("--signing-key", default="")
    submit_parser.add_argument("--mnemonic", default="")
    submit_parser.add_argument("--workspace-root")

    signoff_parser = subparsers.add_parser("signoff", help="Record signoff for a submitted stage.")
    signoff_parser.add_argument("--case-id", required=True)
    signoff_parser.add_argument("--stage-key", required=True)
    signoff_parser.add_argument("--role", required=True)
    signoff_parser.add_argument("--decision", default="approved", choices=["approved", "rejected"])
    signoff_parser.add_argument("--note", default="")
    signoff_parser.add_argument("--signing-key", default="")
    signoff_parser.add_argument("--mnemonic", default="")
    signoff_parser.add_argument("--workspace-root")

    rollback_parser = subparsers.add_parser(
        "rollback",
        help="Rollback a case to an earlier stage, or to ceo-demand / task-dispatch checkpoints.",
    )
    rollback_parser.add_argument("--case-id", required=True)
    rollback_parser.add_argument(
        "--stage-key",
        required=True,
        help="Target stage or checkpoint. Supports stage keys plus ceo-demand/intake and task-dispatch/dispatch.",
    )
    rollback_parser.add_argument("--reason", required=True)
    rollback_parser.add_argument("--workspace-root")

    status_parser = subparsers.add_parser("status", help="Read the current IPD case snapshot.")
    status_parser.add_argument("--case-id", required=True)
    status_parser.add_argument("--workspace-root")

    discovery_parser = subparsers.add_parser(
        "discovery",
        help="Automatically execute Discovery research, refresh markdown package files, and optionally submit the stage.",
    )
    discovery_parser.add_argument("--case-id", required=True)
    discovery_parser.add_argument("--submit", action="store_true")
    discovery_parser.add_argument("--workspace-root")

    intelligence_parser = subparsers.add_parser(
        "intelligence",
        help="Automatically execute Intelligence research, refresh markdown package files, optionally run CodeGraph, and optionally submit the stage.",
    )
    intelligence_parser.add_argument("--case-id", required=True)
    intelligence_parser.add_argument("--submit", action="store_true")
    intelligence_parser.add_argument("--no-codegraph", action="store_true")
    intelligence_parser.add_argument("--workspace-root")

    step_parser = subparsers.add_parser("step", help="Reconcile one case or all cases.")
    step_parser.add_argument("--case-id")
    step_parser.add_argument("--workspace-root")

    autopilot_parser = subparsers.add_parser(
        "autopilot",
        help="Autopilot an IPD case from intake approvals through all ten stages.",
    )
    autopilot_parser.add_argument("--case-id", required=True)
    autopilot_parser.add_argument("--workspace-root")
    autopilot_parser.add_argument("--tridev-root")
    autopilot_parser.add_argument("--no-tridev-bridge", action="store_true")
    autopilot_parser.add_argument("--non-strict-release", action="store_true")
    autopilot_parser.add_argument(
        "--auto-approve-role",
        action="append",
        default=[],
        help="Role that autopilot can auto-sign; default is CEOChiefOfStaff and CEO.",
    )
    autopilot_parser.add_argument(
        "--manual-ceo-signoff",
        action="store_true",
        help="Pause autopilot whenever the pending signer is CEO.",
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        result = initialize_ipd_case(
            case_id=args.case_id,
            title=args.title,
            objective=args.objective,
            task_description=args.task_description,
            created_by=args.created_by,
            priority=args.priority,
            case_category=args.case_category,
            reference_theme=args.reference_theme,
            related_modules=args.related_module,
            constraints=args.constraint,
            opportunity_signals=args.opportunity_signal,
            business_model_fit=args.business_model_fit,
            stage_fit=args.stage_fit,
            company_context=args.company_context,
            owner_proposal=args.owner_proposal,
            resource_envelope=args.resource_envelope,
            prerequisites=args.prerequisite,
            required_support=args.required_support,
            expected_outcomes=args.expected_outcome,
            market_context=args.market_context,
            division_of_work=args.division_of_work,
            staffing_cost=args.staffing_cost,
            other_cost=args.other_cost,
            slot_answers=_parse_slot_answers(args.slot_answer),
            require_clarification_slots=True,
            expected_delivery=args.expected_delivery,
            required_approvers=args.require_approver or INTAKE_REQUIRED_APPROVERS,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "task-intake":
        task_description = _normalize_task_text(args.task)
        result = initialize_ipd_case(
            case_id=args.case_id or _generate_case_id(task_description, workspace_root=args.workspace_root),
            title=args.title or _derive_title(task_description),
            objective=args.objective or _derive_objective(task_description),
            task_description=task_description,
            created_by=args.created_by,
            priority=args.priority,
            case_category=args.case_category,
            reference_theme=args.reference_theme,
            related_modules=args.related_module
            or _resolve_related_modules(task_description, mode=args.module_routing_mode),
            constraints=args.constraint,
            opportunity_signals=(
                f"CEO / 总助正式下发任务：{task_description}",
                "该事项需要先经过总助 intake briefing，再决定是否进入公司级 IPD 主动交付线。",
            ),
            business_model_fit=(
                "待总助结合当前“小成本先跑通可收费闭环、先验证再扩大”的路线判断是否成立。",
            ),
            stage_fit=(
                "待总助确认该事项是否落在当前 Copilot-host 正式接管阶段，而不是越界到 TriMC 正式宿主事项。",
            ),
            company_context=(
                "TriCompany 当前已具备最小 IPD runtime slice，可先承接 intake briefing、顺序放行和书面签核。",
            ),
            owner_proposal=(
                "总助先把任务转成 intake briefing；CMO / COO / CFO / CPO / CTO 再按节点继续细化。",
            ),
            resource_envelope=(
                "待总助结合任务复杂度补齐人力、时间、工具、预算窗口和是否需要 TriDev 接入。",
            ),
            prerequisites=(
                "CEO 确认该事项需要进入公司级 IPD 评估，而不是继续停留在口头任务或临时待办层。",
            ),
            required_support=(
                "CMO / COO / CFO / CPO / CTO 需按节点补齐市场、经营、预算、产品和技术判断。",
            ),
            expected_outcomes=(
                "形成一份可签核的 intake briefing，并在 CEO / 总助签核后决定是否正式进入 IPD 主动交付线。",
            ),
            slot_answers=_parse_slot_answers(args.slot_answer),
            require_clarification_slots=True,
            expected_delivery="形成公司级 IPD intake briefing 与后续节点放行判断。",
            required_approvers=args.require_approver or INTAKE_REQUIRED_APPROVERS,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "intake-approve":
        result = record_intake_signoff(
            args.case_id,
            role=args.role,
            decision=args.decision,
            note=args.note,
            signing_key=args.signing_key,
            mnemonic=args.mnemonic,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "freeze":
        result = freeze_ipd_case(
            args.case_id,
            role=args.role,
            reason=args.reason,
            domain=args.domain,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "unfreeze":
        result = unfreeze_ipd_case(
            args.case_id,
            role=args.role,
            note=args.note,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "submit":
        result = submit_stage_output(
            args.case_id,
            stage_key=args.stage_key,
            submitted_by=args.submitted_by,
            summary=args.summary,
            details=args.detail,
            evidence=args.evidence,
            object_path=args.object_path,
            signing_key=args.signing_key,
            mnemonic=args.mnemonic,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "signoff":
        result = record_stage_signoff(
            args.case_id,
            stage_key=args.stage_key,
            role=args.role,
            decision=args.decision,
            note=args.note,
            signing_key=args.signing_key,
            mnemonic=args.mnemonic,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "rollback":
        result = rollback_ipd_case(
            args.case_id,
            stage_key=args.stage_key,
            reason=args.reason,
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "status":
        result = read_ipd_case(args.case_id, workspace_root=args.workspace_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "discovery":
        result = run_discovery_stage_automation(
            args.case_id,
            workspace_root=args.workspace_root,
            submit=args.submit,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "intelligence":
        result = run_intelligence_stage_automation(
            args.case_id,
            workspace_root=args.workspace_root,
            submit=args.submit,
            enable_codegraph=not args.no_codegraph,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "step":
        if args.case_id:
            result = reconcile_ipd_case(args.case_id, workspace_root=args.workspace_root)
        else:
            result = reconcile_all_ipd_cases(workspace_root=args.workspace_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "autopilot":
        auto_approve_roles = args.auto_approve_role or ["CEOChiefOfStaff", "CEO"]
        if args.manual_ceo_signoff:
            auto_approve_roles = [role for role in auto_approve_roles if role != "CEO"]
            if not auto_approve_roles:
                auto_approve_roles = ["CEOChiefOfStaff"]
        result = run_case_autopilot(
            args.case_id,
            workspace_root=args.workspace_root,
            tridev_root=args.tridev_root,
            enable_tridev_bridge=not args.no_tridev_bridge,
            strict_release_bundle=not args.non_strict_release,
            auto_approve_roles=auto_approve_roles,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    raise ValueError(f"Unsupported command: {args.command}")

def _normalize_task_text(task_parts: list[str]) -> str:
    text = " ".join(str(part).strip() for part in task_parts if str(part).strip()).strip()
    if not text:
        raise ValueError("task is required")
    return text


def _generate_case_id(task_description: str, *, workspace_root: str | None = None) -> str:
    date_prefix = datetime.now().astimezone().strftime("%Y%m%d")
    short_name = _derive_case_short_name(task_description)
    pattern = re.compile(rf"^IPD-{date_prefix}-{re.escape(short_name)}-(\d{{3}})$")
    highest_sequence = 0
    cases_root = chief_of_staff_ipd_cases_root(workspace_root)
    if cases_root.exists():
        for child in cases_root.iterdir():
            if not child.is_dir():
                continue
            matched = pattern.match(child.name)
            if matched:
                highest_sequence = max(highest_sequence, int(matched.group(1)))
    return f"IPD-{date_prefix}-{short_name}-{highest_sequence + 1:03d}"


def _derive_case_short_name(task_description: str) -> str:
    source_text = str(task_description or "").strip()
    lowered = source_text.lower()
    for keywords, short_name in _CASE_SHORT_NAME_HINTS:
        if any((keyword.lower() in lowered) if keyword.isascii() else (keyword in source_text) for keyword in keywords):
            return short_name
    ascii_tokens = [
        token
        for token in re.findall(r"[A-Za-z0-9]+", source_text.upper())
        if token and token not in _CASE_SHORT_NAME_STOPWORDS
    ]
    if ascii_tokens:
        return "-".join(ascii_tokens[:2]).strip("-") or "CASE"
    return "CASE"


def _derive_title(task_description: str) -> str:
    separators = ("，", ",", "。", ".", "；", ";", "：", ":")
    title = task_description
    for separator in separators:
        if separator in title:
            title = title.split(separator, 1)[0].strip()
            break
    if len(title) > 24:
        title = title[:24].rstrip() + "..."
    return title or "CEO / 总助任务"


def _derive_objective(task_description: str) -> str:
    return f"将 CEO / 总助任务转译为可签核 intake briefing，并推进公司级 IPD 评估：{task_description}"


def _infer_related_modules(task_description: str) -> tuple[str, ...]:
    source_text = str(task_description or "").strip()
    lowered = source_text.lower()
    modules: list[str] = []

    def add_module(*names: str) -> None:
        for name in names:
            if name and name not in modules:
                modules.append(name)

    add_module("TriCompany")
    for module_names, keywords in _MODULE_ROUTING_HINTS:
        if any(_matches_module_hint(source_text, lowered, keyword) for keyword in keywords):
            add_module(*module_names)

    if any(name in modules for name in ("TriPilot", "Tride", "vscodium")) and any(
        _matches_module_hint(source_text, lowered, keyword) for keyword in _LOCAL_EXECUTION_HINTS
    ):
        add_module("TriLC")
    if "TriHost" in modules:
        add_module("TriMC")
    if any(name in modules for name in ("TriDeployment", "TriTest")):
        add_module("TriDev")
    return tuple(modules)


def _resolve_related_modules(task_description: str, *, mode: str = "auto") -> tuple[str, ...]:
    if mode not in _MODULE_ROUTING_MODES:
        raise ValueError(f"unsupported module routing mode: {mode}")
    deterministic_modules = _infer_related_modules(task_description)
    if mode == "deterministic":
        return deterministic_modules
    if mode == "auto" and not _cpo_module_router_is_configured():
        return deterministic_modules
    try:
        return _invoke_cpo_module_router(task_description, fallback_modules=deterministic_modules)
    except _ModuleRoutingEscalationRequired as exc:
        raise ValueError(f"CPO module routing requires BusinessStrategy escalation: {exc}") from exc
    except _ModuleRoutingUnavailable as exc:
        if mode == "cpo":
            raise ValueError(f"CPO module routing failed: {exc}") from exc
        print(f"CPO module routing unavailable; falling back to deterministic routing: {exc}", file=sys.stderr)
        return deterministic_modules


def _cpo_module_router_is_configured() -> bool:
    return bool(os.environ.get(_CPO_MODULE_ROUTER_COMMAND_ENV, "").strip())


def _invoke_cpo_module_router(task_description: str, *, fallback_modules: tuple[str, ...]) -> tuple[str, ...]:
    command = os.environ.get(_CPO_MODULE_ROUTER_COMMAND_ENV, "").strip()
    if not command:
        raise _ModuleRoutingUnavailable(f"{_CPO_MODULE_ROUTER_COMMAND_ENV} is not set")
    request_payload = {
        "requestType": "CPO_MODULE_ROUTING",
        "taskDescription": str(task_description or "").strip(),
        "fallbackRelatedModules": list(fallback_modules),
        "allowedModules": list(_MODULE_CATALOG),
        "sourceOfTruthRefs": list(_SOURCE_OF_TRUTH_REFS),
        "requiredOutput": {
            "relatedModules": ["TriCompany"],
            "confidence": "low|medium|high",
            "needsBusinessStrategyEscalation": False,
            "rationale": "<why these modules are product-relevant>",
        },
    }
    timeout_seconds = _cpo_module_router_timeout_seconds()
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(request_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            shell=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise _ModuleRoutingUnavailable(f"CPO router timed out after {timeout_seconds:g}s") from exc
    except OSError as exc:
        raise _ModuleRoutingUnavailable(f"CPO router could not start: {exc}") from exc
    if completed.returncode != 0:
        error_text = (completed.stderr or completed.stdout or "").strip()
        detail = f": {error_text}" if error_text else ""
        raise _ModuleRoutingUnavailable(f"CPO router exited with code {completed.returncode}{detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise _ModuleRoutingUnavailable("CPO router did not return valid JSON") from exc
    return _parse_cpo_module_routing_payload(payload)


def _cpo_module_router_timeout_seconds() -> float:
    raw_value = os.environ.get(_CPO_MODULE_ROUTER_TIMEOUT_ENV, "").strip()
    if not raw_value:
        return _DEFAULT_CPO_MODULE_ROUTER_TIMEOUT_SECONDS
    try:
        timeout_seconds = float(raw_value)
    except ValueError as exc:
        raise _ModuleRoutingUnavailable(f"{_CPO_MODULE_ROUTER_TIMEOUT_ENV} must be a number") from exc
    if timeout_seconds <= 0:
        raise _ModuleRoutingUnavailable(f"{_CPO_MODULE_ROUTER_TIMEOUT_ENV} must be greater than 0")
    return timeout_seconds


def _parse_cpo_module_routing_payload(payload: Any) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        raise _ModuleRoutingUnavailable("CPO router response must be a JSON object")
    if bool(payload.get("needsBusinessStrategyEscalation")):
        reason = str(payload.get("rationale") or payload.get("reason") or "module boundary is unclear").strip()
        raise _ModuleRoutingEscalationRequired(reason)
    modules_value = payload.get("relatedModules", payload.get("modules"))
    if not isinstance(modules_value, list):
        raise _ModuleRoutingUnavailable("CPO router response must include relatedModules as a list")
    return _normalize_related_modules(modules_value)


def _normalize_related_modules(raw_modules: list[Any]) -> tuple[str, ...]:
    modules: list[str] = ["TriCompany"]
    unknown_modules: list[str] = []
    for raw_module in raw_modules:
        normalized = _normalize_module_name(raw_module)
        if not normalized:
            text = str(raw_module or "").strip()
            if text:
                unknown_modules.append(text)
            continue
        if normalized not in modules:
            modules.append(normalized)
    if unknown_modules:
        raise _ModuleRoutingUnavailable(f"unknown module(s) from CPO router: {', '.join(unknown_modules)}")
    return tuple(modules)


def _normalize_module_name(raw_module: Any) -> str:
    text = str(raw_module or "").strip().strip("`")
    if not text:
        return ""
    return _MODULE_NAME_ALIASES.get(text.replace("-", "").replace("_", "").lower(), "")


def _parse_slot_answers(values: list[str]) -> dict[str, str]:
    answers: dict[str, str] = {}
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        if "=" not in text:
            raise ValueError(f"slot answer must be key=value: {text}")
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"slot answer must be key=value: {text}")
        answers[key] = value
    return answers


if __name__ == "__main__":
    raise SystemExit(main())
