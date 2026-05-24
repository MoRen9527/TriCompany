from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WikiPageSpec:
    spec_id: str
    page_id: str
    title: str
    page_status: str
    topic_tags: tuple[str, ...]
    include_topics: tuple[str, ...]
    exclude_topics: tuple[str, ...]
    keyword_hints: tuple[str, ...]
    source_ids: tuple[str, ...]
    reviewer_roles: tuple[str, ...]
    primary_reviewer: str
    approval_sla_hours: int | None
    max_sources: int | None = None