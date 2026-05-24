from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SchedulePayload:
    target_type: str
    target_ref: str
    target_version: str | None
    schedule_type: str
    schedule_expression: str
    execution_host: str
    approval_gate: str
    failure_policy: str
    audit_required: bool
    enabled: bool
    concurrency_policy: str
    stop_conditions: tuple[str, ...]
    delivery_channel: str | None
    delivery_target: str | None
    input_template: str | None
    max_runtime_minutes: int | None
    retry_limit: int | None
    note: str | None
    task_config: dict[str, Any]


@dataclass(frozen=True)
class ScheduleSpec:
    object_id: str
    title: str
    status: str
    owner_role: str
    summary: str
    schedule_path: Path
    payload: SchedulePayload