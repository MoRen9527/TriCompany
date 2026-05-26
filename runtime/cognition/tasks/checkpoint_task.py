from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_wiki_root
from runtime.cognition.kernel.wiki_page_registry import WikiPageRegistry
from runtime.cognition.tasks.approval_timing import evaluate_approval_timing
from runtime.cognition.tasks.wiki_recall_checkpoint_task import run_wiki_recall_checkpoint


def run_checkpoint_task(
    *,
    checkpoint_id: str,
    task_config: dict[str, Any],
    workspace_root: str | None = None,
    trigger_mode: str = "scheduled",
) -> dict[str, object]:
    checkpoint_kind = str(task_config.get("checkpointKind") or "generic").strip().lower()
    if checkpoint_kind == "wiki-recall":
        return run_wiki_recall_checkpoint(
            page_id=str(task_config.get("pageId") or ""),
            workspace_root=workspace_root,
            trigger_mode=trigger_mode,
            recall_mode=str(task_config.get("recallMode") or "all-pages"),
        )
    if checkpoint_kind == "approval-queue":
        return _run_approval_queue_checkpoint(
            checkpoint_id=checkpoint_id,
            workspace_root=workspace_root,
            trigger_mode=trigger_mode,
        )
    if checkpoint_kind == "ipd-case-step":
        return _run_ipd_case_checkpoint(
            checkpoint_id=checkpoint_id,
            task_config=task_config,
            workspace_root=workspace_root,
            trigger_mode=trigger_mode,
        )
    return _write_generic_checkpoint(
        checkpoint_id=checkpoint_id,
        task_config=task_config,
        workspace_root=workspace_root,
        trigger_mode=trigger_mode,
    )


def _run_approval_queue_checkpoint(
    *,
    checkpoint_id: str,
    workspace_root: str | None,
    trigger_mode: str,
) -> dict[str, object]:
    registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    pending_pages = [
        page
        for page in registry.list_pages()
        if page.page_status == "reviewing" and page.approval_status in {"pending", "rejected", "draft"}
    ]
    payload = {
        "checkpointKind": "approval-queue",
        "pendingPageCount": len(pending_pages),
        "warningPageCount": 0,
        "overduePageCount": 0,
        "pendingPages": [
            {
                "pageId": page.page_id,
                "title": page.title,
                "pageStatus": page.page_status,
                "approvalStatus": page.approval_status,
                "reviewerRoute": list(page.reviewer_route),
                "primaryReviewer": page.primary_reviewer,
                "approvalSlaHours": page.approval_sla_hours,
                "approvalDueAt": page.approval_due_at,
                "updatedAt": page.updated_at,
                **evaluate_approval_timing(
                    approval_due_at=page.approval_due_at,
                    approval_sla_hours=page.approval_sla_hours,
                ),
            }
            for page in pending_pages
        ],
    }
    payload["warningPageCount"] = sum(1 for page in payload["pendingPages"] if page["approvalWarning"])
    payload["overduePageCount"] = sum(1 for page in payload["pendingPages"] if page["approvalOverdue"])
    return _write_checkpoint_artifact(
        prefix="checkpoint-approval-queue",
        checkpoint_id=checkpoint_id,
        payload=payload,
        workspace_root=workspace_root,
        trigger_mode=trigger_mode,
        note="approval queue checkpoint generated",
    )


def _run_ipd_case_checkpoint(
    *,
    checkpoint_id: str,
    task_config: dict[str, Any],
    workspace_root: str | None,
    trigger_mode: str,
) -> dict[str, object]:
    from runtime.cognition.ipd_case_engine import reconcile_all_ipd_cases, reconcile_ipd_case

    case_id = str(task_config.get("caseId") or "").strip()
    if case_id:
        summary = reconcile_ipd_case(case_id, workspace_root=workspace_root)
        payload = {
            "checkpointKind": "ipd-case-step",
            "reconciledCaseCount": 1,
            "advancedCaseCount": 1 if summary["advanced"] else 0,
            "completedCaseCount": 1 if summary["status"] == "completed" else 0,
            "cases": [summary],
        }
    else:
        payload = {
            "checkpointKind": "ipd-case-step",
            **reconcile_all_ipd_cases(workspace_root=workspace_root),
        }
    return _write_checkpoint_artifact(
        prefix="checkpoint-ipd-case-step",
        checkpoint_id=checkpoint_id,
        payload=payload,
        workspace_root=workspace_root,
        trigger_mode=trigger_mode,
        note="ipd case checkpoint generated",
    )


def _write_generic_checkpoint(
    *,
    checkpoint_id: str,
    task_config: dict[str, Any],
    workspace_root: str | None,
    trigger_mode: str,
) -> dict[str, object]:
    payload = {
        "checkpointKind": str(task_config.get("checkpointKind") or "generic"),
        "summary": str(task_config.get("summary") or checkpoint_id),
        "details": task_config,
    }
    return _write_checkpoint_artifact(
        prefix="checkpoint-generic",
        checkpoint_id=checkpoint_id,
        payload=payload,
        workspace_root=workspace_root,
        trigger_mode=trigger_mode,
        note="generic checkpoint recorded",
    )


def _write_checkpoint_artifact(
    *,
    prefix: str,
    checkpoint_id: str,
    payload: dict[str, object],
    workspace_root: str | None,
    trigger_mode: str,
    note: str,
) -> dict[str, object]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime(f"{prefix}-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    body = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "checkpointId": checkpoint_id,
        "checkedAt": _timestamp_now(),
        **payload,
    }
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "completed",
        "artifactPaths": [path.as_posix()],
        "note": note,
    }


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")