from __future__ import annotations

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_wiki_root
from runtime.cognition.contracts.wiki_page_spec_contract import WikiPageSpec
from runtime.cognition.contracts.wiki_source_contract import WikiPage, WikiSource
from runtime.cognition.dispatch.wiki_compiler import compile_wiki_page
from runtime.cognition.kernel.wiki_page_registry import WikiPageRegistry


def compile_chief_of_staff_page(
    sources: list[WikiSource],
    *,
    page_id: str,
    title: str,
    updated_at: str,
    workspace_root: str | None = None,
    page_spec: WikiPageSpec | None = None,
) -> WikiPage:
    page_registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    existing_page = page_registry.load_page(page_id)
    page = compile_wiki_page(
        sources,
        page_id=page_id,
        title=title,
        page_path=page_registry.path_for(page_id),
        updated_at=updated_at,
        page_status=existing_page.page_status if existing_page is not None else (page_spec.page_status if page_spec is not None else "working"),
        approval_status=existing_page.approval_status if existing_page is not None else "draft",
        reviewed_by=existing_page.reviewed_by if existing_page is not None else "",
        reviewed_at=existing_page.reviewed_at if existing_page is not None else "",
        approval_note=existing_page.approval_note if existing_page is not None else "",
        topic_tags=(page_spec.topic_tags if page_spec is not None and page_spec.topic_tags else (existing_page.topic_tags if existing_page is not None else None)),
        reviewer_route=(page_spec.reviewer_roles if page_spec is not None and page_spec.reviewer_roles else (existing_page.reviewer_route if existing_page is not None else ())),
        primary_reviewer=(page_spec.primary_reviewer if page_spec is not None and page_spec.primary_reviewer else (existing_page.primary_reviewer if existing_page is not None else "")),
        approval_sla_hours=(page_spec.approval_sla_hours if page_spec is not None and page_spec.approval_sla_hours is not None else (existing_page.approval_sla_hours if existing_page is not None else None)),
        approval_due_at=existing_page.approval_due_at if existing_page is not None else "",
    )
    page_registry.write_page(page)
    return page