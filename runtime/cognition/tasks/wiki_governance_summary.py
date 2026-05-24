from __future__ import annotations

from typing import Any

from runtime.cognition.tasks.approval_timing import evaluate_approval_timing


def build_wiki_governance_summary(pages: list[dict[str, Any]]) -> dict[str, Any]:
    pending_pages = [page for page in pages if _text(page.get("pageStatus")) == "reviewing" and _text(page.get("approvalStatus")) != "approved"]
    route_coverage_count = sum(1 for page in pages if _route_members(page.get("reviewerRoute")))
    primary_reviewer_coverage_count = sum(1 for page in pages if _text(page.get("primaryReviewer")))
    sla_coverage_count = sum(1 for page in pages if _sla_value(page.get("approvalSlaHours")) is not None)
    due_tracked_count = sum(1 for page in pending_pages if _text(page.get("approvalDueAt")))
    overdue_count = sum(1 for page in pending_pages if _page_is_overdue(page))
    warning_count = sum(1 for page in pending_pages if _page_is_warning(page))
    return {
        "pageCount": len(pages),
        "pendingCount": len(pending_pages),
        "warningCount": warning_count,
        "overdueCount": overdue_count,
        "routeCoverageCount": route_coverage_count,
        "primaryReviewerCoverageCount": primary_reviewer_coverage_count,
        "slaCoverageCount": sla_coverage_count,
        "dueTrackedCount": due_tracked_count,
        "dueTrackedExpectedCount": len(pending_pages),
        "reviewerOwners": _build_owner_buckets(pages),
        "reviewerRoutes": _build_route_buckets(pages),
        "missingPolicyPages": _build_missing_policy_pages(pages),
    }


def _build_owner_buckets(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for page in pages:
        reviewer = _text(page.get("primaryReviewer")) or "未配置"
        bucket = buckets.setdefault(
            reviewer,
            {
                "reviewer": reviewer,
                "pageCount": 0,
                "stableCount": 0,
                "reviewingCount": 0,
                "workingCount": 0,
                "pendingCount": 0,
                "warningCount": 0,
                "overdueCount": 0,
                "routeLabels": set(),
            },
        )
        bucket["pageCount"] += 1
        page_status = _text(page.get("pageStatus"))
        if page_status == "stable":
            bucket["stableCount"] += 1
        elif page_status == "reviewing":
            bucket["reviewingCount"] += 1
        elif page_status == "working":
            bucket["workingCount"] += 1
        if page_status == "reviewing" and _text(page.get("approvalStatus")) != "approved":
            bucket["pendingCount"] += 1
        if _page_is_warning(page):
            bucket["warningCount"] += 1
        if _page_is_overdue(page):
            bucket["overdueCount"] += 1
        route_label = _route_label(page.get("reviewerRoute"))
        if route_label:
            bucket["routeLabels"].add(route_label)

    items = []
    for bucket in buckets.values():
        items.append(
            {
                **bucket,
                "routeLabels": sorted(bucket["routeLabels"]),
            }
        )
    items.sort(
        key=lambda item: (
            -int(item["overdueCount"]),
            -int(item["warningCount"]),
            -int(item["pendingCount"]),
            -int(item["pageCount"]),
            item["reviewer"] == "未配置",
            str(item["reviewer"]),
        )
    )
    return items


def _build_route_buckets(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for page in pages:
        route_label = _route_label(page.get("reviewerRoute")) or "未配置"
        bucket = buckets.setdefault(
            route_label,
            {
                "routeLabel": route_label,
                "pageCount": 0,
                "stableCount": 0,
                "reviewingCount": 0,
                "workingCount": 0,
                "pendingCount": 0,
                "warningCount": 0,
                "overdueCount": 0,
                "primaryReviewers": set(),
                "earliestDueAt": "",
            },
        )
        bucket["pageCount"] += 1
        page_status = _text(page.get("pageStatus"))
        if page_status == "stable":
            bucket["stableCount"] += 1
        elif page_status == "reviewing":
            bucket["reviewingCount"] += 1
        elif page_status == "working":
            bucket["workingCount"] += 1
        if page_status == "reviewing" and _text(page.get("approvalStatus")) != "approved":
            bucket["pendingCount"] += 1
        if _page_is_warning(page):
            bucket["warningCount"] += 1
        if _page_is_overdue(page):
            bucket["overdueCount"] += 1
        primary_reviewer = _text(page.get("primaryReviewer"))
        if primary_reviewer:
            bucket["primaryReviewers"].add(primary_reviewer)
        due_at = _text(page.get("approvalDueAt"))
        if due_at and (not bucket["earliestDueAt"] or due_at < bucket["earliestDueAt"]):
            bucket["earliestDueAt"] = due_at

    items = []
    for bucket in buckets.values():
        items.append(
            {
                **bucket,
                "primaryReviewers": sorted(bucket["primaryReviewers"]),
            }
        )
    items.sort(
        key=lambda item: (
            -int(item["overdueCount"]),
            -int(item["warningCount"]),
            -int(item["pendingCount"]),
            -int(item["pageCount"]),
            item["routeLabel"] == "未配置",
            str(item["routeLabel"]),
        )
    )
    return items


def _build_missing_policy_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in pages:
        missing_fields: list[str] = []
        if not _route_members(page.get("reviewerRoute")):
            missing_fields.append("reviewer route")
        if not _text(page.get("primaryReviewer")):
            missing_fields.append("primary reviewer")
        if _sla_value(page.get("approvalSlaHours")) is None:
            missing_fields.append("approval SLA")
        if _text(page.get("pageStatus")) == "reviewing" and not _text(page.get("approvalDueAt")):
            missing_fields.append("approvalDueAt")
        if missing_fields:
            items.append(
                {
                    "pageId": _text(page.get("pageId")),
                    "title": _text(page.get("title")) or _text(page.get("pageId")),
                    "pageStatus": _text(page.get("pageStatus")),
                    "missingFields": missing_fields,
                }
            )
    items.sort(key=lambda item: (str(item["pageStatus"]), str(item["title"])))
    return items


def _route_label(value: Any) -> str:
    members = _route_members(value)
    if not members:
        return ""
    return " -> ".join(members)


def _route_members(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        members = tuple(_text(item) for item in value if _text(item))
        return tuple(member for member in members if member)
    text = _text(value)
    return (text,) if text else ()


def _sla_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _page_is_overdue(page: dict[str, Any]) -> bool:
    if isinstance(page.get("approvalOverdue"), bool):
        return bool(page.get("approvalOverdue"))
    return bool(
        evaluate_approval_timing(
            approval_due_at=_text(page.get("approvalDueAt")),
            approval_sla_hours=_sla_value(page.get("approvalSlaHours")),
        )["approvalOverdue"]
    )


def _page_is_warning(page: dict[str, Any]) -> bool:
    if isinstance(page.get("approvalWarning"), bool):
        return bool(page.get("approvalWarning"))
    return bool(
        evaluate_approval_timing(
            approval_due_at=_text(page.get("approvalDueAt")),
            approval_sla_hours=_sla_value(page.get("approvalSlaHours")),
        )["approvalWarning"]
    )