from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root
from runtime.cognition.dispatch.host_dispatcher import dispatch_task_payload


def run_reminder_task(
    *,
    reminder_id: str,
    task_config: dict[str, Any],
    workspace_root: str | None = None,
    trigger_mode: str = "scheduled",
    delivery_channel: str | None = None,
    delivery_target: str | None = None,
) -> dict[str, object]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("reminder-delivery-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "reminderId": reminder_id,
        "title": str(task_config.get("title") or reminder_id),
        "message": str(task_config.get("message") or ""),
        "assignee": str(task_config.get("assignee") or "CEOChiefOfStaff"),
        "dueAt": str(task_config.get("dueAt") or ""),
        "severity": str(task_config.get("severity") or "normal"),
        "channel": str(task_config.get("channel") or "audit"),
        "generatedAt": _timestamp_now(),
    }
    dispatch_result = dispatch_task_payload(
        task_kind="reminder",
        payload=payload,
        task_config=task_config,
        delivery_channel=delivery_channel,
        delivery_target=delivery_target,
    )
    payload["delivery"] = dispatch_result
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": str(dispatch_result.get("taskStatus") or "completed"),
        "deliveryStatus": str(dispatch_result.get("deliveryStatus") or "rendered"),
        "artifactPaths": [path.as_posix()],
        "note": str(dispatch_result.get("note") or "reminder payload generated"),
    }


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")