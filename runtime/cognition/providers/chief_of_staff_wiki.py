from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from runtime.cognition.contracts.provider_contract import (
    CognitionProvider,
    MemoryScope,
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)
from runtime.cognition.kernel.wiki_page_registry import StoredWikiPage, WikiPageRegistry


_STATUS_SCORES = {
    "stable": 0.85,
    "reviewing": 0.7,
    "working": 0.55,
}


class ChiefOfStaffWikiProvider(CognitionProvider):
    """Read-only provider that exposes chief-of-staff wiki pages to recall."""

    is_external = False

    def __init__(
        self,
        *,
        actor_id: str,
        wiki_root: str | Path,
        provider_name: str = "chief-of-staff-wiki",
        allowed_page_statuses: tuple[str, ...] = ("working", "reviewing", "stable"),
    ) -> None:
        self.actor_id = actor_id
        self.wiki_root = Path(wiki_root)
        self._name = provider_name
        self.allowed_page_statuses = tuple(status.lower() for status in allowed_page_statuses)

    @property
    def name(self) -> str:
        return self._name

    def scopes_supported(self) -> Iterable[MemoryScope]:
        return (MemoryScope.ORG_SHARED,)

    def system_prompt_block(self, actor_id: str) -> str:
        return f"Stable chief-of-staff wiki recall is available for {actor_id}."

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        if query.actor_id != self.actor_id or "org/shared" not in query.namespaces:
            return []

        results: list[RecallResult] = []
        for page in self._page_snapshots():
            content = self._render_page_snapshot(page)
            if content:
                results.append(
                    RecallResult(
                        provider_name=self.name,
                        namespace="org/shared",
                        content=content,
                        score=_STATUS_SCORES.get(page.page_status.lower(), 0.5),
                    )
                )
        return results

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        return None

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        return None

    def _page_snapshots(self) -> list[StoredWikiPage]:
        registry = WikiPageRegistry(self.wiki_root)
        return [
            page
            for page in registry.list_pages()
            if page.page_status.lower() in self.allowed_page_statuses
        ]

    def _render_page_snapshot(self, page: StoredWikiPage) -> str:
        source_line = ", ".join(page.source_refs) if page.source_refs else "none"
        clean_body = page.body.strip()
        if not clean_body:
            return ""
        review_lines = []
        if page.reviewed_by:
            review_lines.append(f"- reviewed-by: {page.reviewed_by}")
        if page.reviewed_at:
            review_lines.append(f"- reviewed-at: {page.reviewed_at}")
        if page.approval_note:
            review_lines.append(f"- approval-note: {page.approval_note}")
        review_block = "\n".join(review_lines)
        if review_block:
            review_block = f"{review_block}\n"
        return (
            f"## {page.title}\n"
            f"- page-id: {page.page_id}\n"
            f"- page-status: {page.page_status}\n"
            f"- approval-status: {page.approval_status}\n"
            f"- source: {page.page_path.as_posix()}\n"
            f"- source-refs: {source_line}\n\n"
            f"{review_block}"
            f"{clean_body}"
        )


class ChiefOfStaffStableWikiProvider(ChiefOfStaffWikiProvider):
    def __init__(self, *, actor_id: str, wiki_root: str | Path, provider_name: str = "chief-of-staff-wiki") -> None:
        super().__init__(
            actor_id=actor_id,
            wiki_root=wiki_root,
            provider_name=provider_name,
            allowed_page_statuses=("stable",),
        )


class ChiefOfStaffAllWikiProvider(ChiefOfStaffWikiProvider):
    def __init__(self, *, actor_id: str, wiki_root: str | Path, provider_name: str = "chief-of-staff-wiki") -> None:
        super().__init__(
            actor_id=actor_id,
            wiki_root=wiki_root,
            provider_name=provider_name,
            allowed_page_statuses=("working", "reviewing", "stable"),
        )