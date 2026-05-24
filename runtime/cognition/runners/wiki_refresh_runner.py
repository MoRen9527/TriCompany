from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_wiki_page_specs_path
from runtime.cognition.contracts.wiki_page_spec_contract import WikiPageSpec
from runtime.cognition.contracts.wiki_source_contract import WikiPage, WikiSource
from runtime.cognition.kernel.wiki_page_spec_registry import WikiPageSpecRegistry, select_sources_for_page_spec
from runtime.cognition.tasks.wiki_compile_task import compile_chief_of_staff_page
from runtime.cognition.tasks.wiki_ingest_task import ingest_chief_of_staff_sources


@dataclass(frozen=True)
class WikiRefreshRun:
    run_id: str
    trigger_mode: str
    input_sources: tuple[str, ...]
    output_page_id: str
    output_page_path: Path
    audit_path: Path
    status: str
    page_spec_id: str | None = None


def run_chief_of_staff_wiki_refresh(
    *,
    page_id: str,
    title: str,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
    page_spec_id: str | None = None,
    sources: list[WikiSource] | None = None,
) -> WikiRefreshRun:
    all_sources = list(sources) if sources is not None else ingest_chief_of_staff_sources(workspace_root=workspace_root)
    if not all_sources:
        raise ValueError("No inbox sources found for chief-of-staff wiki refresh.")

    page_spec = _resolve_page_spec(page_id=page_id, page_spec_id=page_spec_id, workspace_root=workspace_root)
    selected_sources = select_sources_for_page_spec(all_sources, page_spec) if page_spec is not None else all_sources
    if not selected_sources:
        raise ValueError(f"No matching inbox sources found for wiki page: {page_id}")

    timestamp = _timestamp_now()
    run_id = _build_run_id()
    page = compile_chief_of_staff_page(
        selected_sources,
        page_id=page_id,
        title=title,
        updated_at=timestamp,
        workspace_root=workspace_root,
        page_spec=page_spec,
    )
    audit_path = _write_audit_record(
        run_id=run_id,
        trigger_mode=trigger_mode,
        sources=selected_sources,
        page=page,
        workspace_root=workspace_root,
        page_spec=page_spec,
    )
    return WikiRefreshRun(
        run_id=run_id,
        trigger_mode=trigger_mode,
        input_sources=tuple(source.source_id for source in selected_sources),
        output_page_id=page.page_id,
        output_page_path=page.page_path,
        audit_path=audit_path,
        status="completed",
        page_spec_id=page_spec.spec_id if page_spec is not None else None,
    )


def _write_audit_record(
    *,
    run_id: str,
    trigger_mode: str,
    sources: list[WikiSource],
    page: WikiPage,
    workspace_root: str | None,
    page_spec: WikiPageSpec | None,
) -> Path:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    audit_path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "startedAt": _timestamp_now(),
        "inputSources": [source.source_id for source in sources],
        "outputPages": [page.page_id],
        "status": "completed",
        "notes": "chief-of-staff semi-automatic wiki refresh",
    }
    if page_spec is not None:
        payload["pageSpecId"] = page_spec.spec_id
    audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit_path


def _resolve_page_spec(*, page_id: str, page_spec_id: str | None, workspace_root: str | None) -> WikiPageSpec | None:
    registry = WikiPageSpecRegistry(chief_of_staff_wiki_page_specs_path(workspace_root))
    if page_spec_id is not None:
        return registry.load_spec(page_spec_id)
    return registry.find_by_page_id(page_id)


def _build_run_id() -> str:
    return datetime.now(timezone.utc).strftime("wiki-refresh-%Y-%m-%d-%H%M%S-%f")


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")