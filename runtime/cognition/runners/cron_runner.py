from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_schedule_root
from runtime.cognition.contracts.run_record_contract import RunRecord
from runtime.cognition.dispatch.failure_policy import decide_failure_status
from runtime.cognition.dispatch.task_resolver import resolve_schedule_task
from runtime.cognition.kernel.schedule_registry import ScheduleRegistry
from runtime.cognition.runners.audit_sink import write_run_record


@dataclass(frozen=True)
class CronRunSummary:
    schedule_count: int
    run_record_paths: tuple[str, ...]


def run_due_chief_of_staff_schedules(
    *,
    workspace_root: str | None = None,
    now: datetime | None = None,
) -> CronRunSummary:
    registry = ScheduleRegistry(chief_of_staff_schedule_root(workspace_root))
    schedules = registry.list_specs()
    run_record_paths: list[str] = []
    current_time = now or datetime.now(timezone.utc).astimezone()

    for schedule in schedules:
        if not schedule.payload.enabled:
            continue
        if not _is_due(schedule.payload.schedule_type, schedule.payload.schedule_expression, current_time):
            continue
        if _already_executed_current_slot(schedule.object_id, schedule.payload.schedule_type, schedule.payload.schedule_expression, current_time, workspace_root):
            continue
        started_at = _timestamp(current_time)
        try:
            resolved = resolve_schedule_task(schedule, workspace_root=workspace_root)
            result = resolved.execute()
            ended_at = _timestamp(datetime.now(timezone.utc).astimezone())
            artifact_items = result.get("artifactPaths")
            artifact_paths = _artifact_paths(artifact_items)
            run_record = RunRecord(
                run_id=_build_schedule_run_id(schedule.object_id),
                schedule_id=schedule.object_id,
                target_ref=schedule.payload.target_ref,
                host=schedule.payload.execution_host,
                status=str(result.get("status") or "completed"),
                delivery_status=str(result.get("deliveryStatus") or "not-applicable"),
                started_at=started_at,
                ended_at=ended_at,
                artifact_paths=artifact_paths,
                note=str(result.get("note") or schedule.summary),
            )
        except Exception as error:
            ended_at = _timestamp(datetime.now(timezone.utc).astimezone())
            status, freeze_reason = decide_failure_status(schedule.payload.failure_policy, str(error))
            run_record = RunRecord(
                run_id=_build_schedule_run_id(schedule.object_id),
                schedule_id=schedule.object_id,
                target_ref=schedule.payload.target_ref,
                host=schedule.payload.execution_host,
                status=status,
                delivery_status="not-applicable",
                started_at=started_at,
                ended_at=ended_at,
                artifact_paths=(),
                freeze_reason=freeze_reason,
                note="schedule execution failed",
            )
        run_record_path = write_run_record(run_record, workspace_root=workspace_root)
        run_record_paths.append(run_record_path.as_posix())

    return CronRunSummary(
        schedule_count=len(run_record_paths),
        run_record_paths=tuple(run_record_paths),
    )


def _is_due(schedule_type: str, expression: str, current_time: datetime) -> bool:
    if schedule_type == "one-shot":
        try:
            return current_time >= datetime.fromisoformat(expression)
        except ValueError:
            return False
    if schedule_type == "cron":
        return _cron_matches(expression, current_time)
    if schedule_type == "daily":
        return True
    return False


def _cron_matches(expression: str, current_time: datetime) -> bool:
    parts = expression.split()
    if len(parts) != 5:
        return False
    minute, hour, day, month, weekday = parts
    checks = (
        _cron_field_matches(minute, current_time.minute),
        _cron_field_matches(hour, current_time.hour),
        _cron_field_matches(day, current_time.day),
        _cron_field_matches(month, current_time.month),
        _cron_field_matches(weekday, (current_time.weekday() + 1) % 7),
    )
    return all(checks)


def _cron_field_matches(field: str, value: int) -> bool:
    if field == "*":
        return True
    if field.startswith("*/"):
        step = int(field[2:])
        return step > 0 and value % step == 0
    return int(field) == value


def _build_schedule_run_id(schedule_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-%f")
    return f"schedule-run-{schedule_id}-{timestamp}"


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _artifact_paths(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()


def _already_executed_current_slot(
    schedule_id: str,
    schedule_type: str,
    schedule_expression: str,
    current_time: datetime,
    workspace_root: str | None,
) -> bool:
    audit_root = chief_of_staff_audit_root(workspace_root)
    if not audit_root.exists():
        return False

    records = sorted(audit_root.glob(f"schedule-run-{schedule_id}-*.json"), reverse=True)
    if not records:
        return False

    latest_record = json.loads(records[0].read_text(encoding="utf-8"))
    started_at = str(latest_record.get("startedAt") or "")
    try:
        previous_time = datetime.fromisoformat(started_at)
    except ValueError:
        return False
    return _same_execution_slot(schedule_type, schedule_expression, current_time, previous_time)


def _same_execution_slot(
    schedule_type: str,
    schedule_expression: str,
    current_time: datetime,
    previous_time: datetime,
) -> bool:
    if schedule_type == "one-shot":
        try:
            scheduled_at = datetime.fromisoformat(schedule_expression)
        except ValueError:
            return False
        return previous_time >= scheduled_at
    if schedule_type == "daily":
        return current_time.date() == previous_time.date()
    if schedule_type == "cron":
        return current_time.strftime("%Y-%m-%d-%H-%M") == previous_time.strftime("%Y-%m-%d-%H-%M")
    return False