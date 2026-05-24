from __future__ import annotations

import json
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root


def build_registry_closeout_bridge(
    *,
    schedules: list[Any],
    workspace_root: str | None,
) -> dict[str, Any]:
    closeout_target_types = {"registry-closeout", "operating-review-closeout"}
    entries: list[dict[str, Any]] = []
    latest_audits = load_registry_closeout_audits(workspace_root)
    for schedule in schedules:
        if schedule.payload.target_type not in closeout_target_types:
            continue
        latest = next(
            (
                audit
                for audit in latest_audits
                if audit.get("closeoutId") == schedule.payload.target_ref or audit.get("objectId") == schedule.payload.target_ref
            ),
            None,
        )
        delivery = latest.get("delivery") if isinstance(latest, dict) else None
        task_config = schedule.payload.task_config if isinstance(schedule.payload.task_config, dict) else {}
        entries.append(
            {
                "scheduleId": schedule.object_id,
                "title": schedule.title,
                "targetType": schedule.payload.target_type,
                "targetRef": schedule.payload.target_ref,
                "scheduleExpression": schedule.payload.schedule_expression,
                "enabled": schedule.payload.enabled,
                "approvalGate": schedule.payload.approval_gate,
                "sourcePath": str(task_config.get("closeoutPath") or task_config.get("sourcePath") or ""),
                "operatingReviewPath": str(task_config.get("operatingReviewPath") or ""),
                "note": schedule.payload.note or schedule.summary,
                "latestRunId": str((latest or {}).get("runId") or ""),
                "latestGeneratedAt": str((latest or {}).get("generatedAt") or ""),
                "latestObjectId": str((latest or {}).get("objectId") or ""),
                "latestCloseoutSubject": str((latest or {}).get("closeoutSubject") or ""),
                "latestRegistryFindingCount": int((latest or {}).get("registryFindingCount") or 0),
                "latestTriggerObjectType": str(((latest or {}).get("triggerSource") or {}).get("objectType") or ""),
                "latestTriggerObjectId": str(((latest or {}).get("triggerSource") or {}).get("objectId") or ""),
                "latestDeliveryStatus": str((delivery or {}).get("deliveryStatus") or "not-run"),
                "latestDeliveryChannel": str((delivery or {}).get("deliveryChannel") or ""),
                "latestDeliveryTarget": str((delivery or {}).get("deliveryTarget") or ""),
                "latestAuditPath": str((latest or {}).get("_path") or ""),
            }
        )
    return {
        "scheduleCount": len(entries),
        "renderedCount": sum(1 for item in entries if item["latestDeliveryStatus"] == "rendered"),
        "deliveredCount": sum(1 for item in entries if item["latestDeliveryStatus"] == "delivered"),
        "pendingRunCount": sum(1 for item in entries if item["latestDeliveryStatus"] == "not-run"),
        "entries": entries,
    }


def load_registry_closeout_audits(workspace_root: str | None) -> list[dict[str, Any]]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    if not audit_root.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(audit_root.glob("registry-closeout-*.json"), reverse=True)[:12]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        payload["_path"] = path.as_posix()
        records.append(payload)
    return records