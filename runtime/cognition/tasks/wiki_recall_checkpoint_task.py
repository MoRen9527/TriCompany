from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.chief_of_staff_cognition import CHIEF_OF_STAFF_ID, build_ceo_chief_of_staff_kernel
from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root


def run_wiki_recall_checkpoint(
    *,
    page_id: str,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
    recall_mode: str = "stable-only",
) -> dict[str, object]:
    storage_root = None
    if workspace_root is not None:
        storage_root = str(Path(workspace_root) / ".tricompany-cognition")
    include_all_wiki_recall = recall_mode == "all-pages"
    kernel = build_ceo_chief_of_staff_kernel(
        storage_root=storage_root,
        workspace_root=workspace_root,
        include_repo_assets=False,
        include_stable_wiki_recall=not include_all_wiki_recall,
        include_all_wiki_recall=include_all_wiki_recall,
    )
    context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, "请召回总助 wiki 页面")
    status = "completed" if page_id in context else "blocked"
    reason = (
        f"{recall_mode} wiki page successfully entered recall"
        if status == "completed"
        else f"target wiki page is not yet visible in {recall_mode} recall"
    )
    audit_path = _write_recall_checkpoint(
        page_id=page_id,
        trigger_mode=trigger_mode,
        recall_mode=recall_mode,
        status=status,
        reason=reason,
        context_excerpt=context,
        workspace_root=workspace_root,
    )
    return {
        "status": status,
        "artifactPaths": [audit_path.as_posix()],
        "note": reason,
    }


def _write_recall_checkpoint(
    *,
    page_id: str,
    trigger_mode: str,
    recall_mode: str,
    status: str,
    reason: str,
    context_excerpt: str,
    workspace_root: str | None,
):
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("wiki-recall-checkpoint-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "pageId": page_id,
        "recallMode": recall_mode,
        "status": status,
        "reason": reason,
        "checkedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "contextExcerpt": context_excerpt,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path