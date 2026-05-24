from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_wiki_page_specs_path
from runtime.cognition.kernel.wiki_page_spec_registry import WikiPageSpecRegistry
from runtime.cognition.runners.wiki_refresh_runner import WikiRefreshRun, run_chief_of_staff_wiki_refresh
from runtime.cognition.tasks.wiki_ingest_task import ingest_chief_of_staff_sources


@dataclass(frozen=True)
class WikiBatchRefreshRun:
    run_id: str
    trigger_mode: str
    spec_ids: tuple[str, ...]
    output_pages: tuple[str, ...]
    artifact_paths: tuple[str, ...]
    audit_path: Path
    status: str


def run_chief_of_staff_wiki_batch_refresh(
    *,
    spec_ids: tuple[str, ...] | None = None,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
) -> WikiBatchRefreshRun:
    sources = ingest_chief_of_staff_sources(workspace_root=workspace_root)
    if not sources:
        raise ValueError("No inbox sources found for chief-of-staff batch wiki refresh.")

    registry = WikiPageSpecRegistry(chief_of_staff_wiki_page_specs_path(workspace_root))
    available_specs = registry.list_specs()
    if spec_ids is not None:
        spec_id_set = {item.strip() for item in spec_ids if item.strip()}
        specs = [spec for spec in available_specs if spec.spec_id in spec_id_set]
    else:
        specs = available_specs
    if not specs:
        raise ValueError("No wiki page specs found for batch refresh.")

    refresh_runs: list[WikiRefreshRun] = []
    for spec in specs:
        refresh_runs.append(
            run_chief_of_staff_wiki_refresh(
                page_id=spec.page_id,
                title=spec.title,
                workspace_root=workspace_root,
                trigger_mode=trigger_mode,
                page_spec_id=spec.spec_id,
                sources=sources,
            )
        )

    run_id = datetime.now(timezone.utc).strftime("wiki-refresh-batch-%Y-%m-%d-%H%M%S-%f")
    audit_path = _write_batch_audit(
        run_id=run_id,
        refresh_runs=refresh_runs,
        trigger_mode=trigger_mode,
        workspace_root=workspace_root,
    )
    artifact_paths = [audit_path.as_posix()]
    for refresh_run in refresh_runs:
        artifact_paths.append(refresh_run.output_page_path.as_posix())
        artifact_paths.append(refresh_run.audit_path.as_posix())
    return WikiBatchRefreshRun(
        run_id=run_id,
        trigger_mode=trigger_mode,
        spec_ids=tuple(spec.spec_id for spec in specs),
        output_pages=tuple(refresh_run.output_page_id for refresh_run in refresh_runs),
        artifact_paths=tuple(artifact_paths),
        audit_path=audit_path,
        status="completed",
    )


def _write_batch_audit(
    *,
    run_id: str,
    refresh_runs: list[WikiRefreshRun],
    trigger_mode: str,
    workspace_root: str | None,
) -> Path:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "startedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "completed",
        "pageSpecIds": [item.page_spec_id for item in refresh_runs if item.page_spec_id],
        "outputPages": [item.output_page_id for item in refresh_runs],
        "childRuns": [item.run_id for item in refresh_runs],
        "inputSources": sorted({source_id for item in refresh_runs for source_id in item.input_sources}),
        "notes": "chief-of-staff multi-topic wiki batch refresh",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path