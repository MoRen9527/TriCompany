from __future__ import annotations

import json
from pathlib import Path

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root
from runtime.cognition.contracts.run_record_contract import RunRecord


def write_run_record(
    record: RunRecord,
    *,
    workspace_root: str | None = None,
) -> Path:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    path = audit_root / f"{record.run_id}.json"
    payload = {
        "runId": record.run_id,
        "scheduleId": record.schedule_id,
        "targetRef": record.target_ref,
        "host": record.host,
        "status": record.status,
        "deliveryStatus": record.delivery_status,
        "startedAt": record.started_at,
        "endedAt": record.ended_at,
        "artifactPaths": list(record.artifact_paths),
        "freezeReason": record.freeze_reason,
        "note": record.note,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path