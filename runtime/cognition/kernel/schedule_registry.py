from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.cognition.contracts.schedule_spec_contract import SchedulePayload, ScheduleSpec


_SCHEDULE_PAYLOAD_KEYS = {
    "targetType",
    "targetRef",
    "targetVersion",
    "scheduleType",
    "scheduleExpression",
    "executionHost",
    "approvalGate",
    "failurePolicy",
    "auditRequired",
    "enabled",
    "concurrencyPolicy",
    "stopConditions",
    "deliveryChannel",
    "deliveryTarget",
    "inputTemplate",
    "maxRuntimeMinutes",
    "retryLimit",
    "note",
    "taskConfig",
}


class ScheduleRegistry:
    def __init__(self, schedule_root: str | Path) -> None:
        self.schedule_root = Path(schedule_root)

    def list_specs(self) -> list[ScheduleSpec]:
        if not self.schedule_root.exists():
            return []

        specs: list[ScheduleSpec] = []
        for path in sorted(self.schedule_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            schedule_payload = payload.get("payload") or {}
            task_config = _task_config(schedule_payload)
            specs.append(
                ScheduleSpec(
                    object_id=str(payload.get("objectId") or path.stem),
                    title=str(payload.get("title") or path.stem),
                    status=str(payload.get("status") or "draft"),
                    owner_role=str(payload.get("ownerRole") or "CEOChiefOfStaff"),
                    summary=str(payload.get("summary") or ""),
                    schedule_path=path,
                    payload=SchedulePayload(
                        target_type=str(schedule_payload.get("targetType") or "custom"),
                        target_ref=str(schedule_payload.get("targetRef") or ""),
                        target_version=_maybe_string(schedule_payload.get("targetVersion")),
                        schedule_type=str(schedule_payload.get("scheduleType") or "one-shot"),
                        schedule_expression=str(schedule_payload.get("scheduleExpression") or ""),
                        execution_host=str(schedule_payload.get("executionHost") or "copilot-chat"),
                        approval_gate=str(schedule_payload.get("approvalGate") or "manual-only"),
                        failure_policy=str(schedule_payload.get("failurePolicy") or "freeze"),
                        audit_required=bool(schedule_payload.get("auditRequired", True)),
                        enabled=bool(schedule_payload.get("enabled", False)),
                        concurrency_policy=str(schedule_payload.get("concurrencyPolicy") or "forbid-overlap"),
                        stop_conditions=tuple(schedule_payload.get("stopConditions") or ()),
                        delivery_channel=_maybe_string(schedule_payload.get("deliveryChannel")),
                        delivery_target=_maybe_string(schedule_payload.get("deliveryTarget")),
                        input_template=_maybe_string(schedule_payload.get("inputTemplate")),
                        max_runtime_minutes=_maybe_int(schedule_payload.get("maxRuntimeMinutes")),
                        retry_limit=_maybe_int(schedule_payload.get("retryLimit")),
                        note=_maybe_string(schedule_payload.get("note")),
                        task_config=task_config,
                    ),
                )
            )
        return specs


def _maybe_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _maybe_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _task_config(schedule_payload: dict[str, Any]) -> dict[str, Any]:
    raw_task_config = schedule_payload.get("taskConfig")
    if isinstance(raw_task_config, dict):
        return dict(raw_task_config)
    return {
        key: value
        for key, value in schedule_payload.items()
        if key not in _SCHEDULE_PAYLOAD_KEYS
    }