from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from runtime.cognition.runners.cron_runner import run_due_chief_of_staff_schedules


@dataclass(frozen=True)
class ResidentRunSummary:
    cycle_count: int
    total_schedule_runs: int
    run_record_paths: tuple[str, ...]


def run_resident_chief_of_staff_schedules(
    *,
    workspace_root: str | None = None,
    interval_seconds: float = 60.0,
    max_cycles: int | None = None,
    now_provider: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> ResidentRunSummary:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than 0")

    cycle_count = 0
    total_schedule_runs = 0
    run_record_paths: list[str] = []
    sleeper = sleep_fn or time.sleep

    while max_cycles is None or cycle_count < max_cycles:
        current_time = now_provider() if now_provider is not None else None
        result = run_due_chief_of_staff_schedules(
            workspace_root=workspace_root,
            now=current_time,
        )
        cycle_count += 1
        total_schedule_runs += result.schedule_count
        run_record_paths.extend(result.run_record_paths)
        if max_cycles is not None and cycle_count >= max_cycles:
            break
        sleeper(interval_seconds)

    return ResidentRunSummary(
        cycle_count=cycle_count,
        total_schedule_runs=total_schedule_runs,
        run_record_paths=tuple(run_record_paths),
    )