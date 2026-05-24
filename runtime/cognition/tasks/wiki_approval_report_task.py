from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.chief_of_staff_wiki_paths import (
    chief_of_staff_approval_report_root,
    chief_of_staff_audit_root,
    chief_of_staff_schedule_root,
    chief_of_staff_wiki_root,
)
from runtime.cognition.kernel.schedule_registry import ScheduleRegistry
from runtime.cognition.kernel.wiki_page_registry import StoredWikiPage, WikiPageRegistry
from runtime.cognition.tasks.approval_timing import evaluate_approval_timing
from runtime.cognition.tasks.registry_closeout_summary import build_registry_closeout_bridge
from runtime.cognition.tasks.wiki_governance_summary import build_wiki_governance_summary


def build_chief_of_staff_approval_report(
    *,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
) -> dict[str, object]:
    generated_at = _timestamp_now()
    registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    schedule_registry = ScheduleRegistry(chief_of_staff_schedule_root(workspace_root))
    all_pages = [_page_snapshot(page, generated_at) for page in registry.list_pages()]
    pages = [page for page in all_pages if page["pageStatus"] == "reviewing" and page["approvalStatus"] != "approved"]
    governance = build_wiki_governance_summary(all_pages)
    closeout_bridge = build_registry_closeout_bridge(
        schedules=schedule_registry.list_specs(),
        workspace_root=workspace_root,
    )
    summary = {
        "pageCount": governance["pageCount"],
        "pendingCount": governance["pendingCount"],
        "warningCount": governance["warningCount"],
        "overdueCount": governance["overdueCount"],
        "routeCoverageCount": governance["routeCoverageCount"],
        "primaryReviewerCoverageCount": governance["primaryReviewerCoverageCount"],
        "slaCoverageCount": governance["slaCoverageCount"],
        "dueTrackedCount": governance["dueTrackedCount"],
        "dueTrackedExpectedCount": governance["dueTrackedExpectedCount"],
        "closeoutScheduleCount": closeout_bridge["scheduleCount"],
        "closeoutRenderedCount": closeout_bridge["renderedCount"],
        "closeoutDeliveredCount": closeout_bridge["deliveredCount"],
        "closeoutPendingRunCount": closeout_bridge["pendingRunCount"],
    }
    payload = {
        "generatedAt": generated_at,
        "triggerMode": trigger_mode,
        "summary": summary,
        "governance": governance,
        "closeoutBridge": closeout_bridge,
        "pages": pages,
    }

    report_root = chief_of_staff_approval_report_root(workspace_root)
    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / "snapshot.json"
    markdown_path = report_root / "summary.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")

    audit_path = _write_audit(payload=payload, workspace_root=workspace_root)
    return {
        "status": "completed",
        "artifactPaths": [json_path.as_posix(), markdown_path.as_posix(), audit_path.as_posix()],
        "note": "approval report rebuilt",
    }


def _page_snapshot(page: StoredWikiPage, generated_at: str) -> dict[str, object]:
    return {
        "pageId": page.page_id,
        "title": page.title,
        "pageStatus": page.page_status,
        "approvalStatus": page.approval_status,
        "reviewerRoute": list(page.reviewer_route),
        "primaryReviewer": page.primary_reviewer,
        "approvalSlaHours": page.approval_sla_hours,
        "approvalDueAt": page.approval_due_at,
        "updatedAt": page.updated_at,
        **evaluate_approval_timing(
            approval_due_at=page.approval_due_at,
            approval_sla_hours=page.approval_sla_hours,
            reference_time=generated_at,
        ),
    }


def _render_markdown(payload: dict[str, object]) -> str:
    governance = payload["governance"]
    summary = payload["summary"]
    lines = [
        "# 总助审批报表",
        "",
        f"- 生成时间：{payload['generatedAt']}",
        f"- 待审批页数：{summary['pendingCount']}",
        f"- 即将超时页数：{summary['warningCount']}",
        f"- SLA 已超时页数：{summary['overdueCount']}",
        "",
        "## 治理摘要",
        "",
        f"- 总页数：{summary['pageCount']}",
        f"- Reviewer route 覆盖：{summary['routeCoverageCount']} / {summary['pageCount']}",
        f"- Primary reviewer 覆盖：{summary['primaryReviewerCoverageCount']} / {summary['pageCount']}",
        f"- SLA 覆盖：{summary['slaCoverageCount']} / {summary['pageCount']}",
        f"- 审批截止已生成：{summary['dueTrackedCount']} / {summary['dueTrackedExpectedCount']} 个待审批页",
        "",
        "## Central Registry Closeout",
        "",
        f"- 已接入 closeout schedule：{summary['closeoutScheduleCount']}",
        f"- 最近 rendered：{summary['closeoutRenderedCount']}",
        f"- 最近 delivered：{summary['closeoutDeliveredCount']}",
        f"- 尚未执行：{summary['closeoutPendingRunCount']}",
        "",
        "## Reviewer Owner 负载",
        "",
    ]
    closeout_rows = payload.get("closeoutBridge", {}).get("entries") or []
    if not closeout_rows:
        lines.append("- 当前没有接入 central registry closeout bridge。")
        lines.append("")
    else:
        for item in closeout_rows:
            trigger_source = "未记录"
            if item.get("latestTriggerObjectType") or item.get("latestTriggerObjectId"):
                trigger_source = (
                    f"{item.get('latestTriggerObjectType') or 'unknown'} / "
                    f"{item.get('latestTriggerObjectId') or 'unknown'}"
                )
            lines.extend(
                [
                    f"### {item['title']}",
                    "",
                    f"- scheduleId：{item['scheduleId']}",
                    f"- targetType：{item['targetType']}",
                    f"- targetRef：{item['targetRef']}",
                    f"- 最近派发：{item['latestGeneratedAt'] or '尚未生成'}",
                    f"- 最近状态：{item['latestDeliveryStatus']}",
                    f"- 最近触发源：{trigger_source}",
                    f"- 最近 findings：{item['latestRegistryFindingCount']}",
                    f"- sourcePath：{item['sourcePath'] or '未配置'}",
                    f"- operatingReviewPath：{item['operatingReviewPath'] or '未配置'}",
                    "",
                ]
            )

    owner_rows = governance.get("reviewerOwners") or []
    if not owner_rows:
        lines.append("- 当前没有可统计的 reviewer owner。")
        lines.append("")
    else:
        for owner in owner_rows:
            route_labels = ", ".join(owner["routeLabels"]) if owner["routeLabels"] else "未配置"
            lines.extend(
                [
                    f"### {owner['reviewer']}",
                    "",
                    f"- 页面数：{owner['pageCount']}",
                    f"- Stable / Reviewing / Working：{owner['stableCount']} / {owner['reviewingCount']} / {owner['workingCount']}",
                    f"- 当前待审批：{owner['pendingCount']}",
                    f"- 当前预警：{owner['warningCount']}",
                    f"- 当前超时：{owner['overdueCount']}",
                    f"- 涉及 route：{route_labels}",
                    "",
                ]
            )

    lines.extend(["## Route 分布", ""])
    route_rows = governance.get("reviewerRoutes") or []
    if not route_rows:
        lines.append("- 当前没有可统计的 reviewer route。")
        lines.append("")
    else:
        for route in route_rows:
            primary_reviewers = ", ".join(route["primaryReviewers"]) if route["primaryReviewers"] else "未配置"
            earliest_due_at = route["earliestDueAt"] or "当前无审批截止"
            lines.extend(
                [
                    f"### {route['routeLabel']}",
                    "",
                    f"- 页面数：{route['pageCount']}",
                    f"- Stable / Reviewing / Working：{route['stableCount']} / {route['reviewingCount']} / {route['workingCount']}",
                    f"- 当前待审批：{route['pendingCount']}",
                    f"- 当前预警：{route['warningCount']}",
                    f"- 当前超时：{route['overdueCount']}",
                    f"- Primary reviewer：{primary_reviewers}",
                    f"- 最早审批截止：{earliest_due_at}",
                    "",
                ]
            )

    lines.extend(["## 待补治理配置", ""])
    missing_rows = governance.get("missingPolicyPages") or []
    if not missing_rows:
        lines.append("- 当前所有页面都已具备 route / owner / SLA 治理配置。")
        lines.append("")
    else:
        for item in missing_rows:
            lines.extend(
                [
                    f"### {item['title']}",
                    "",
                    f"- 页面 ID：{item['pageId']}",
                    f"- 页面状态：{item['pageStatus']}",
                    f"- 待补字段：{', '.join(item['missingFields'])}",
                    "",
                ]
            )

    lines.extend(["## 待审批页面清单", ""])
    pages = payload.get("pages") or []
    if not pages:
        lines.append("- 当前没有待审批页面。")
        lines.append("")
        return "\n".join(lines)
    for page in pages:
        route = ", ".join(page["reviewerRoute"]) if page["reviewerRoute"] else "未配置"
        lines.extend(
            [
                f"### {page['title']}",
                "",
                f"- 页面 ID：{page['pageId']}",
                f"- 审批状态：{page['approvalStatus']}",
                f"- Primary reviewer：{page['primaryReviewer'] or '未配置'}",
                f"- Reviewer route：{route}",
                f"- SLA：{page['approvalSlaHours'] or '未配置'} 小时",
                f"- 应完成时间：{page['approvalDueAt'] or '未生成'}",
                f"- 审批态势：{page['approvalTimeToDue']}",
                f"- 是否预警：{'是' if page['approvalWarning'] else '否'}",
                f"- 是否超时：{'是' if page['approvalOverdue'] else '否'}",
                "",
            ]
        )
    return "\n".join(lines)


def _write_audit(*, payload: dict[str, object], workspace_root: str | None) -> Path:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("wiki-approval-report-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    body = {
        "runId": run_id,
        "generatedAt": payload["generatedAt"],
        "status": "completed",
        "summary": payload["summary"],
        "closeoutBridge": payload.get("closeoutBridge"),
        "pageCount": len(payload.get("pages") or []),
    }
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")