from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Any


def evaluate_approval_timing(
    *,
    approval_due_at: str,
    approval_sla_hours: int | None = None,
    reference_time: str | datetime | None = None,
) -> dict[str, Any]:
    due_at = _parse_datetime(approval_due_at)
    now = _resolve_reference_time(reference_time)
    warning_threshold_hours = _warning_threshold_hours(approval_sla_hours)
    warning_threshold_seconds = warning_threshold_hours * 3600 if warning_threshold_hours is not None else None

    if due_at is None:
        return {
            "approvalOverdue": False,
            "approvalWarning": False,
            "approvalAlertLevel": "none",
            "approvalRemainingHours": None,
            "approvalWarningThresholdHours": warning_threshold_hours,
            "approvalTimeToDue": "未生成",
        }

    remaining_seconds = int((due_at - now).total_seconds())
    remaining_hours = round(remaining_seconds / 3600, 1)
    overdue = remaining_seconds <= 0
    warning = bool(not overdue and warning_threshold_seconds is not None and remaining_seconds <= warning_threshold_seconds)
    alert_level = "overdue" if overdue else "warning" if warning else "normal"
    return {
        "approvalOverdue": overdue,
        "approvalWarning": warning,
        "approvalAlertLevel": alert_level,
        "approvalRemainingHours": remaining_hours,
        "approvalWarningThresholdHours": warning_threshold_hours,
        "approvalTimeToDue": _time_to_due_label(remaining_seconds, alert_level),
    }


def _resolve_reference_time(reference_time: str | datetime | None) -> datetime:
    if isinstance(reference_time, datetime):
        parsed = reference_time
    else:
        parsed = _parse_datetime(str(reference_time or ""))
    if parsed is None:
        parsed = datetime.now(timezone.utc).astimezone()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone()


def _parse_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone()


def _warning_threshold_hours(approval_sla_hours: int | None) -> int:
    if approval_sla_hours is None or approval_sla_hours <= 0:
        return 4
    return min(12, max(2, ceil(approval_sla_hours / 4)))


def _time_to_due_label(remaining_seconds: int, alert_level: str) -> str:
    duration = _format_duration(abs(remaining_seconds))
    if alert_level == "overdue":
        return f"已超时 {duration}"
    if alert_level == "warning":
        return f"剩余 {duration}，已进入预警窗口"
    return f"剩余 {duration}"


def _format_duration(total_seconds: int) -> str:
    total_minutes = max(1, total_seconds // 60)
    days, remainder_minutes = divmod(total_minutes, 60 * 24)
    hours, minutes = divmod(remainder_minutes, 60)
    if days:
        if hours:
            return f"{days} 天 {hours} 小时"
        return f"{days} 天"
    if hours:
        if minutes:
            return f"{hours} 小时 {minutes} 分钟"
        return f"{hours} 小时"
    return f"{minutes} 分钟"