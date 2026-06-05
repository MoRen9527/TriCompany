from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.ipd_case_engine import (
    initialize_ipd_case,
    read_ipd_case,
    record_intake_signoff,
    record_stage_signoff,
    reconcile_all_ipd_cases,
    reconcile_ipd_case,
    run_case_autopilot,
    submit_stage_output,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage chief-of-staff IPD cases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    task_intake_parser = subparsers.add_parser(
        "task-intake",
        help="Accept a CEO/chief-of-staff freeform task and create a rough IPD intake briefing draft.",
    )
    task_intake_parser.add_argument("task", nargs="+")
    task_intake_parser.add_argument("--case-id")
    task_intake_parser.add_argument("--title")
    task_intake_parser.add_argument("--objective")
    task_intake_parser.add_argument("--priority", default="high")
    task_intake_parser.add_argument("--created-by", default="CEOChiefOfStaff")
    task_intake_parser.add_argument("--related-module", action="append", default=[])
    task_intake_parser.add_argument("--constraint", action="append", default=[])
    task_intake_parser.add_argument("--require-approver", action="append", default=[])
    task_intake_parser.add_argument("--workspace-root")

    init_parser = subparsers.add_parser("init", help="Initialize or refine an IPD intake briefing.")
    init_parser.add_argument("--case-id", required=True)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--task-description", required=True)
    init_parser.add_argument("--created-by", default="CEOChiefOfStaff")
    init_parser.add_argument("--priority", default="high")
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
    intake_approve_parser.add_argument("--workspace-root")

    submit_parser = subparsers.add_parser("submit", help="Submit output for the current IPD stage.")
    submit_parser.add_argument("--case-id", required=True)
    submit_parser.add_argument("--stage-key", required=True)
    submit_parser.add_argument("--submitted-by", required=True)
    submit_parser.add_argument("--summary", required=True)
    submit_parser.add_argument("--detail", action="append", default=[])
    submit_parser.add_argument("--evidence", action="append", default=[])
    submit_parser.add_argument("--object-path", default="")
    submit_parser.add_argument("--workspace-root")

    signoff_parser = subparsers.add_parser("signoff", help="Record signoff for a submitted stage.")
    signoff_parser.add_argument("--case-id", required=True)
    signoff_parser.add_argument("--stage-key", required=True)
    signoff_parser.add_argument("--role", required=True)
    signoff_parser.add_argument("--decision", default="approved", choices=["approved", "rejected"])
    signoff_parser.add_argument("--note", default="")
    signoff_parser.add_argument("--workspace-root")

    status_parser = subparsers.add_parser("status", help="Read the current IPD case snapshot.")
    status_parser.add_argument("--case-id", required=True)
    status_parser.add_argument("--workspace-root")

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
            expected_delivery=args.expected_delivery,
            required_approvers=args.require_approver or ("CEOChiefOfStaff", "CEO"),
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "task-intake":
        task_description = _normalize_task_text(args.task)
        result = initialize_ipd_case(
            case_id=args.case_id or _generate_case_id(),
            title=args.title or _derive_title(task_description),
            objective=args.objective or _derive_objective(task_description),
            task_description=task_description,
            created_by=args.created_by,
            priority=args.priority,
            related_modules=args.related_module or _infer_related_modules(task_description),
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
            expected_delivery="形成公司级 IPD intake briefing 与后续节点放行判断。",
            required_approvers=args.require_approver or ("CEOChiefOfStaff", "CEO"),
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
            workspace_root=args.workspace_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "status":
        result = read_ipd_case(args.case_id, workspace_root=args.workspace_root)
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


def _generate_case_id() -> str:
    return "IPD-" + datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


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
    modules = ["TriCompany"]
    if any(keyword in task_description for keyword in ("开发", "交付", "软件", "工程", "测试", "上线", "部署")):
        modules.append("TriDev")
    return tuple(modules)


if __name__ == "__main__":
    raise SystemExit(main())
