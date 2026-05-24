from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    schedule_id: str
    target_ref: str
    host: str
    status: str
    delivery_status: str
    started_at: str
    ended_at: str
    artifact_paths: tuple[str, ...]
    freeze_reason: str | None = None
    note: str | None = None