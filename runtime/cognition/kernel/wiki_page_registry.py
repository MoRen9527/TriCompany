from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from runtime.cognition.contracts.wiki_source_contract import WikiPage
from runtime.cognition.kernel.reviewer_router import resolve_review_policy
from runtime.cognition.kernel.wiki_frontmatter import metadata_string_tuple, split_frontmatter


_IGNORED_PAGE_NAMES = {"README.md", "page-template.md"}
_FRONTMATTER_ORDER = (
    "pageId",
    "title",
    "topicTags",
    "pageStatus",
    "updatedAt",
    "approvalStatus",
    "reviewerRoute",
    "primaryReviewer",
    "approvalSlaHours",
    "approvalDueAt",
    "reviewedBy",
    "reviewedAt",
    "approvalNote",
    "sourceRefs",
)


@dataclass(frozen=True)
class StoredWikiPage:
    page_id: str
    title: str
    topic_tags: tuple[str, ...]
    page_status: str
    updated_at: str
    source_refs: tuple[str, ...]
    page_path: Path
    body: str
    approval_status: str
    reviewed_by: str
    reviewed_at: str
    approval_note: str
    reviewer_route: tuple[str, ...]
    primary_reviewer: str
    approval_sla_hours: int | None
    approval_due_at: str


class WikiPageRegistry:
    def __init__(self, wiki_root: str | Path) -> None:
        self.wiki_root = Path(wiki_root)

    def path_for(self, page_id: str) -> Path:
        return self.wiki_root / f"{page_id}.md"

    def list_pages(self) -> list[StoredWikiPage]:
        if not self.wiki_root.exists():
            return []
        pages: list[StoredWikiPage] = []
        for path in sorted(self.wiki_root.glob("*.md")):
            if path.name in _IGNORED_PAGE_NAMES:
                continue
            page = self.load_page_path(path)
            if page is not None:
                pages.append(page)
        return pages

    def load_page(self, page_id: str) -> StoredWikiPage | None:
        return self.load_page_path(self.path_for(page_id))

    def load_page_path(self, page_path: str | Path) -> StoredWikiPage | None:
        path = Path(page_path)
        if not path.exists():
            return None
        metadata, body = split_frontmatter(path.read_text(encoding="utf-8"))
        page_id = str(metadata.get("pageId") or path.stem)
        return StoredWikiPage(
            page_id=page_id,
            title=str(metadata.get("title") or path.stem),
            topic_tags=metadata_string_tuple(metadata, "topicTags"),
            page_status=str(metadata.get("pageStatus") or "working"),
            updated_at=str(metadata.get("updatedAt") or ""),
            source_refs=metadata_string_tuple(metadata, "sourceRefs"),
            page_path=path,
            body=body,
            approval_status=_approval_status(metadata, str(metadata.get("pageStatus") or "working")),
            reviewed_by=str(metadata.get("reviewedBy") or metadata.get("approvedBy") or ""),
            reviewed_at=str(metadata.get("reviewedAt") or metadata.get("approvedAt") or ""),
            approval_note=str(metadata.get("approvalNote") or ""),
            reviewer_route=metadata_string_tuple(metadata, "reviewerRoute"),
            primary_reviewer=str(metadata.get("primaryReviewer") or ""),
            approval_sla_hours=_metadata_int(metadata, "approvalSlaHours"),
            approval_due_at=str(metadata.get("approvalDueAt") or ""),
        )

    def update_page_status(self, page_id: str, *, new_status: str, updated_at: str) -> Path:
        page = self.load_page(page_id)
        if page is None:
            raise FileNotFoundError(f"Wiki page not found: {page_id}")

        updates: dict[str, object] = {
            "pageStatus": new_status,
            "updatedAt": updated_at,
        }
        if new_status == "reviewing" and page.approval_status not in {"approved", "rejected"}:
            review_policy = resolve_review_policy(
                page_id=page.page_id,
                topic_tags=page.topic_tags,
                updated_at=updated_at,
                wiki_root=self.wiki_root,
            )
            updates["approvalStatus"] = "pending"
            updates["reviewerRoute"] = list(review_policy.reviewer_route)
            updates["primaryReviewer"] = review_policy.primary_reviewer
            updates["approvalSlaHours"] = review_policy.approval_sla_hours
            updates["approvalDueAt"] = review_policy.approval_due_at
        return self.update_page_metadata(page_id, updates=updates)

    def update_page_approval(
        self,
        page_id: str,
        *,
        approval_status: str,
        reviewed_by: str,
        reviewed_at: str,
        approval_note: str,
        updated_at: str,
    ) -> Path:
        page = self.load_page(page_id)
        if page is None:
            raise FileNotFoundError(f"Wiki page not found: {page_id}")
        if page.reviewer_route and reviewed_by not in page.reviewer_route:
            raise ValueError(f"Reviewer {reviewed_by} is not assigned to page route: {page_id}")
        return self.update_page_metadata(
            page_id,
            updates={
                "approvalStatus": approval_status,
                "reviewedBy": reviewed_by,
                "reviewedAt": reviewed_at,
                "approvalNote": approval_note,
                "updatedAt": updated_at,
            },
        )

    def update_page_metadata(self, page_id: str, *, updates: dict[str, object]) -> Path:
        page_path = self.path_for(page_id)
        if not page_path.exists():
            raise FileNotFoundError(f"Wiki page not found: {page_id}")

        metadata, body = split_frontmatter(page_path.read_text(encoding="utf-8"))
        for key, value in updates.items():
            if value is None:
                metadata.pop(key, None)
                continue
            if isinstance(value, (list, tuple)):
                items = [str(item).strip() for item in value if str(item).strip()]
                if not items:
                    metadata.pop(key, None)
                    continue
                metadata[key] = items
                continue
            if isinstance(value, str) and not value.strip() and key not in {"approvalNote", "reviewedBy", "reviewedAt"}:
                metadata.pop(key, None)
                continue
            metadata[key] = value

        if "approvalStatus" not in metadata:
            metadata["approvalStatus"] = _default_approval_status(str(metadata.get("pageStatus") or "working"))

        page_path.write_text(_render_page_text(metadata, body), encoding="utf-8")
        return page_path

    def write_page(self, page: WikiPage) -> Path:
        path = page.page_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render_page(page), encoding="utf-8")
        return path


def _render_page(page: WikiPage) -> str:
    metadata: dict[str, object] = {
        "pageId": page.page_id,
        "title": page.title,
        "topicTags": list(page.topic_tags),
        "pageStatus": page.page_status,
        "updatedAt": page.updated_at,
        "approvalStatus": page.approval_status or _default_approval_status(page.page_status),
        "sourceRefs": list(page.source_refs),
    }
    if page.reviewed_by:
        metadata["reviewedBy"] = page.reviewed_by
    if page.reviewed_at:
        metadata["reviewedAt"] = page.reviewed_at
    if page.approval_note:
        metadata["approvalNote"] = page.approval_note
    if page.reviewer_route:
        metadata["reviewerRoute"] = list(page.reviewer_route)
    if page.primary_reviewer:
        metadata["primaryReviewer"] = page.primary_reviewer
    if page.approval_sla_hours is not None:
        metadata["approvalSlaHours"] = page.approval_sla_hours
    if page.approval_due_at:
        metadata["approvalDueAt"] = page.approval_due_at

    facts = _render_bullets(page.facts)
    judgments = _render_bullets(page.judgments)
    open_questions = _render_bullets(page.open_questions)
    sources = _render_bullets(page.source_refs)
    body = (
        "## 摘要\n\n"
        f"{page.summary}\n\n"
        "## 当前整理事实\n\n"
        f"{facts}\n\n"
        "## 当前判断\n\n"
        f"{judgments}\n\n"
        "## 待确认问题\n\n"
        f"{open_questions}\n\n"
        "## 来源\n\n"
        f"{sources}\n"
    )
    return _render_page_text(metadata, body)


def _render_page_text(metadata: dict[str, object], body: str) -> str:
    return f"---\n{_render_frontmatter(metadata)}---\n\n{body.strip()}\n"


def _render_frontmatter(metadata: dict[str, object]) -> str:
    ordered_keys = list(_FRONTMATTER_ORDER)
    for key in metadata:
        if key not in ordered_keys:
            ordered_keys.append(key)

    lines: list[str] = []
    for key in ordered_keys:
        if key not in metadata:
            continue
        value = metadata[key]
        if isinstance(value, (list, tuple)):
            items = [str(item).strip() for item in value if str(item).strip()]
            if not items:
                continue
            lines.append(f"{key}:")
            for text in items:
                lines.append(f"  - {text}")
            continue

        text = str(value).strip()
        if not text and key in {"reviewedBy", "reviewedAt", "approvalNote", "primaryReviewer", "approvalDueAt"}:
            continue
        lines.append(f"{key}: {text}")
    return "\n".join(lines) + "\n"


def _render_bullets(items: tuple[str, ...]) -> str:
    if not items:
        return "- 暂无"
    return "\n".join(f"- {item}" for item in items)


def _approval_status(metadata: dict[str, object], page_status: str) -> str:
    raw_status = str(metadata.get("approvalStatus") or "").strip().lower()
    if raw_status:
        return raw_status
    return _default_approval_status(page_status)


def _default_approval_status(page_status: str) -> str:
    normalized = page_status.lower()
    if normalized == "stable":
        return "approved"
    if normalized == "reviewing":
        return "pending"
    return "draft"


def _metadata_int(metadata: dict[str, object], key: str) -> int | None:
    value = metadata.get(key)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None