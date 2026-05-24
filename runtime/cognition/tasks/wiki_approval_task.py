from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_wiki_root
from runtime.cognition.kernel.wiki_page_registry import WikiPageRegistry


def record_wiki_approval(
    *,
    page_id: str,
    decision: str,
    reviewer: str,
    note: str = "",
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
) -> dict[str, object]:
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approved", "rejected", "pending"}:
        raise ValueError(f"Unsupported approval decision: {decision}")

    page_registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    page = page_registry.load_page(page_id)
    if page is None:
        raise FileNotFoundError(f"Wiki page not found: {page_id}")

    reviewed_at = _timestamp_now()
    page_registry.update_page_approval(
        page_id,
        approval_status=normalized_decision,
        reviewed_by=reviewer,
        reviewed_at=reviewed_at,
        approval_note=note,
        updated_at=reviewed_at,
    )
    audit_path = _write_approval_audit(
        page_id=page_id,
        page_path=page.page_path,
        page_status=page.page_status,
        reviewer_route=page.reviewer_route,
        primary_reviewer=page.primary_reviewer,
        approval_due_at=page.approval_due_at,
        decision=normalized_decision,
        reviewer=reviewer,
        note=note,
        reviewed_at=reviewed_at,
        trigger_mode=trigger_mode,
        workspace_root=workspace_root,
    )
    return {
        "status": "completed",
        "artifactPaths": [page.page_path.as_posix(), audit_path.as_posix()],
        "note": f"page approval recorded as {normalized_decision}",
    }


def _write_approval_audit(
    *,
    page_id: str,
    page_path: Path,
    page_status: str,
    reviewer_route: tuple[str, ...],
    primary_reviewer: str,
    approval_due_at: str,
    decision: str,
    reviewer: str,
    note: str,
    reviewed_at: str,
    trigger_mode: str,
    workspace_root: str | None,
) -> Path:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("wiki-approval-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "pageId": page_id,
        "pagePath": page_path.as_posix(),
        "pageStatus": page_status,
        "reviewerRoute": list(reviewer_route),
        "primaryReviewer": primary_reviewer,
        "approvalDueAt": approval_due_at,
        "decision": decision,
        "reviewer": reviewer,
        "reviewedAt": reviewed_at,
        "note": note,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")