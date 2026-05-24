from __future__ import annotations

import json
from datetime import datetime, timezone

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root
from runtime.cognition.dispatch.host_dispatcher import dispatch_task_payload


def run_email_task(
    *,
    email_id: str,
    task_config: dict[str, object],
    workspace_root: str | None = None,
    trigger_mode: str = "scheduled",
    delivery_channel: str | None = None,
    delivery_target: str | None = None,
) -> dict[str, object]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("email-delivery-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "emailId": email_id,
        "to": _as_list(task_config.get("to")),
        "cc": _as_list(task_config.get("cc")),
        "subject": str(task_config.get("subject") or email_id),
        "body": str(task_config.get("body") or ""),
        "deliveryMode": str(task_config.get("deliveryMode") or "render-only"),
        "generatedAt": _timestamp_now(),
    }
    dispatch_result = dispatch_task_payload(
        task_kind="email",
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
        "note": str(dispatch_result.get("note") or "email payload rendered for manual dispatch"),
    }


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")