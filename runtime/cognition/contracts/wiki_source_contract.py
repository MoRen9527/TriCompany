from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WikiSource:
    source_id: str
    title: str
    source_type: str
    source_path: Path
    topic_hints: tuple[str, ...]
    trust_level: str
    captured_at: str
    body: str


@dataclass(frozen=True)
class WikiPage:
    page_id: str
    title: str
    topic_tags: tuple[str, ...]
    page_path: Path
    page_status: str
    updated_at: str
    source_refs: tuple[str, ...]
    summary: str
    facts: tuple[str, ...]
    judgments: tuple[str, ...]
    open_questions: tuple[str, ...]
    approval_status: str = "draft"
    reviewed_by: str = ""
    reviewed_at: str = ""
    approval_note: str = ""
    reviewer_route: tuple[str, ...] = ()
    primary_reviewer: str = ""
    approval_sla_hours: int | None = None
    approval_due_at: str = ""