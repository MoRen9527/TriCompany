from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from runtime.cognition.kernel.wiki_page_spec_registry import WikiPageSpecRegistry


@dataclass(frozen=True)
class ReviewPolicy:
    reviewer_route: tuple[str, ...]
    primary_reviewer: str
    approval_sla_hours: int
    approval_due_at: str


def resolve_review_policy(
    *,
    page_id: str,
    topic_tags: tuple[str, ...],
    updated_at: str,
    wiki_root: str | Path,
) -> ReviewPolicy:
    spec_registry = WikiPageSpecRegistry(Path(wiki_root) / "page-specs.json")
    spec = spec_registry.find_by_page_id(page_id)
    if spec is not None and spec.reviewer_roles:
        reviewer_route = spec.reviewer_roles
        primary_reviewer = spec.primary_reviewer or spec.reviewer_roles[0]
        approval_sla_hours = spec.approval_sla_hours or _default_sla(topic_tags)
    else:
        reviewer_route, primary_reviewer, approval_sla_hours = _fallback_policy(topic_tags)

    return ReviewPolicy(
        reviewer_route=reviewer_route,
        primary_reviewer=primary_reviewer,
        approval_sla_hours=approval_sla_hours,
        approval_due_at=_build_due_at(updated_at, approval_sla_hours),
    )


def _fallback_policy(topic_tags: tuple[str, ...]) -> tuple[tuple[str, ...], str, int]:
    normalized = {_normalize_tag(item) for item in topic_tags}
    if {"automation", "workbench", "dispatcher"} & normalized:
        return ("ChiefTechnologyOfficer", "CEOChiefOfStaff"), "ChiefTechnologyOfficer", 24
    if {"governance", "knowledge-system", "recall"} & normalized:
        return ("ChiefOperatingOfficer", "CEOChiefOfStaff"), "ChiefOperatingOfficer", 48
    return ("CEOChiefOfStaff",), "CEOChiefOfStaff", 48


def _default_sla(topic_tags: tuple[str, ...]) -> int:
    return _fallback_policy(topic_tags)[2]


def _build_due_at(updated_at: str, approval_sla_hours: int) -> str:
    try:
        parsed = datetime.fromisoformat(updated_at)
    except ValueError:
        parsed = datetime.now(timezone.utc).astimezone()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    due_at = parsed + timedelta(hours=approval_sla_hours)
    return due_at.astimezone().isoformat(timespec="seconds")


def _normalize_tag(value: str) -> str:
    return value.strip().lower().replace("_", "-")