from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_wiki_root
from runtime.cognition.kernel.wiki_page_registry import StoredWikiPage, WikiPageRegistry
from runtime.cognition.tasks.approval_timing import evaluate_approval_timing
from runtime.cognition.tasks.wiki_governance_summary import build_wiki_governance_summary


def build_approval_queue_digest(
    *,
    workspace_root: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    generated_at = generated_at or _timestamp_now()
    all_pages = [_page_snapshot(page, generated_at) for page in registry.list_pages()]
    pending_pages = [page for page in all_pages if page["pageStatus"] == "reviewing" and page["approvalStatus"] != "approved"]
    return {
        "generatedAt": generated_at,
        "overall": build_wiki_governance_summary(all_pages),
        "queue": build_wiki_governance_summary(pending_pages),
        "pendingPages": pending_pages,
    }


def build_approval_queue_reminder_task_config(
    base_task_config: dict[str, Any],
    *,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    digest = build_approval_queue_digest(workspace_root=workspace_root)
    queue = digest["queue"]
    overall = digest["overall"]
    task_config = dict(base_task_config)
    task_config["title"] = str(base_task_config.get("title") or "总助审批队列提醒")
    task_config["message"] = _render_reminder_message(digest)
    task_config["assignee"] = str(base_task_config.get("assignee") or "CEOChiefOfStaff")
    task_config["severity"] = _resolve_severity(queue=queue)
    task_config["dueAt"] = _earliest_due_at(digest["pendingPages"])
    task_config["governanceDigest"] = {
        "generatedAt": digest["generatedAt"],
        "pendingCount": queue["pendingCount"],
        "warningCount": queue["warningCount"],
        "overdueCount": queue["overdueCount"],
        "routeCoverageCount": overall["routeCoverageCount"],
        "primaryReviewerCoverageCount": overall["primaryReviewerCoverageCount"],
        "slaCoverageCount": overall["slaCoverageCount"],
    }
    return task_config


def build_approval_queue_email_task_config(
    base_task_config: dict[str, Any],
    *,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    digest = build_approval_queue_digest(workspace_root=workspace_root)
    queue = digest["queue"]
    overall = digest["overall"]
    task_config = dict(base_task_config)
    task_config["subject"] = _render_email_subject(digest)
    task_config["body"] = _render_email_body(digest)
    if base_task_config.get("deliveryMode") is not None:
        task_config["deliveryMode"] = str(base_task_config.get("deliveryMode") or "render-only")
    task_config["governanceDigest"] = {
        "generatedAt": digest["generatedAt"],
        "pendingCount": queue["pendingCount"],
        "warningCount": queue["warningCount"],
        "overdueCount": queue["overdueCount"],
        "routeCoverageCount": overall["routeCoverageCount"],
        "primaryReviewerCoverageCount": overall["primaryReviewerCoverageCount"],
        "slaCoverageCount": overall["slaCoverageCount"],
    }
    return task_config


def _page_snapshot(page: StoredWikiPage, generated_at: str) -> dict[str, Any]:
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


def _render_reminder_message(digest: dict[str, Any]) -> str:
    queue = digest["queue"]
    overall = digest["overall"]
    pending_pages = digest["pendingPages"]
    if not pending_pages:
        return (
            f"当前审批队列无 reviewing 待审批页；治理覆盖 route {overall['routeCoverageCount']} / {overall['pageCount']}、"
            f"owner {overall['primaryReviewerCoverageCount']} / {overall['pageCount']}、SLA {overall['slaCoverageCount']} / {overall['pageCount']}。"
        )

    owner_line = _owner_line(queue.get("reviewerOwners") or [])
    route_line = _route_line(queue.get("reviewerRoutes") or [])
    focus_line = _focus_line(pending_pages)
    return (
        f"当前审批队列 {queue['pendingCount']} 页待审批，其中 {queue['warningCount']} 页即将超时、"
        f"{queue['overdueCount']} 页已超时。{owner_line}。{route_line}。{focus_line}。"
    )


def _render_email_subject(digest: dict[str, Any]) -> str:
    queue = digest["queue"]
    return f"总助审批队列状态：待审批 {queue['pendingCount']} / 预警 {queue['warningCount']} / 超时 {queue['overdueCount']}"


def _render_email_body(digest: dict[str, Any]) -> str:
    queue = digest["queue"]
    overall = digest["overall"]
    lines = [
        "总助审批治理快照",
        "",
        f"- 生成时间：{digest['generatedAt']}",
        f"- 当前待审批：{queue['pendingCount']}",
        f"- 即将超时：{queue['warningCount']}",
        f"- 已超时：{queue['overdueCount']}",
        f"- Route 覆盖：{overall['routeCoverageCount']} / {overall['pageCount']}",
        f"- Owner 覆盖：{overall['primaryReviewerCoverageCount']} / {overall['pageCount']}",
        f"- SLA 覆盖：{overall['slaCoverageCount']} / {overall['pageCount']}",
        "",
        "Reviewer Owner 负载",
        "",
    ]

    owner_rows = queue.get("reviewerOwners") or []
    if not owner_rows:
        lines.append("- 当前无待审批 owner lane。")
    else:
        for owner in owner_rows:
            lines.append(
                f"- {owner['reviewer']}：待审批 {owner['pendingCount']}，预警 {owner['warningCount']}，超时 {owner['overdueCount']}"
            )
    lines.extend(["", "Reviewer Route 分布", ""])

    route_rows = queue.get("reviewerRoutes") or []
    if not route_rows:
        lines.append("- 当前无待审批 reviewer route。")
    else:
        for route in route_rows:
            earliest_due_at = route["earliestDueAt"] or "当前无审批截止"
            lines.append(
                f"- {route['routeLabel']}：待审批 {route['pendingCount']}，预警 {route['warningCount']}，超时 {route['overdueCount']}，最早审批截止 {earliest_due_at}"
            )

    lines.extend(["", "待处理页面", ""])
    pending_pages = digest["pendingPages"]
    if not pending_pages:
        lines.append("- 当前没有 reviewing 待审批页面。")
    else:
        for page in pending_pages[:5]:
            route = " -> ".join(str(item) for item in page["reviewerRoute"] if str(item).strip()) or "未配置"
            lines.append(
                f"- {page['title']} | primary reviewer {page['primaryReviewer'] or '未配置'} | reviewer route {route} | {page['approvalTimeToDue']}"
            )
    return "\n".join(lines)


def _resolve_severity(*, queue: dict[str, Any]) -> str:
    if int(queue["overdueCount"]):
        return "critical"
    if int(queue["warningCount"]):
        return "high"
    if int(queue["pendingCount"]):
        return "medium"
    return "normal"


def _owner_line(owner_rows: list[dict[str, Any]]) -> str:
    if not owner_rows:
        return "当前没有待审批 reviewer owner"
    return "Reviewer owner: " + "；".join(
        f"{item['reviewer']}({item['pendingCount']}，预警 {item['warningCount']}，超时 {item['overdueCount']})"
        for item in owner_rows[:3]
    )


def _route_line(route_rows: list[dict[str, Any]]) -> str:
    if not route_rows:
        return "当前没有待审批 reviewer route"
    return "Reviewer route: " + "；".join(
        f"{item['routeLabel']}({item['pendingCount']}，预警 {item['warningCount']}，超时 {item['overdueCount']})"
        for item in route_rows[:3]
    )


def _focus_line(pending_pages: list[dict[str, Any]]) -> str:
    ordered_pages = sorted(
        pending_pages,
        key=lambda item: (
            item["approvalAlertLevel"] != "overdue",
            item["approvalAlertLevel"] != "warning",
            str(item["approvalDueAt"] or "9999-12-31T23:59:59+00:00"),
            str(item["title"]),
        ),
    )
    top_items = ordered_pages[:3]
    return "优先处理: " + "；".join(
        f"{item['title']}（{item['approvalTimeToDue']}）"
        for item in top_items
    )


def _earliest_due_at(pending_pages: list[dict[str, Any]]) -> str:
    due_values = [str(page["approvalDueAt"]).strip() for page in pending_pages if str(page.get("approvalDueAt") or "").strip()]
    return min(due_values) if due_values else ""


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")