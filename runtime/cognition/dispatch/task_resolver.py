from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from runtime.cognition.contracts.schedule_spec_contract import ScheduleSpec
from runtime.cognition.tasks.approval_queue_digest import (
    build_approval_queue_email_task_config,
    build_approval_queue_reminder_task_config,
)
from runtime.cognition.tasks.checkpoint_task import run_checkpoint_task
from runtime.cognition.tasks.email_task import run_email_task
from runtime.cognition.tasks.operating_review_closeout_task import run_operating_review_closeout_task
from runtime.cognition.tasks.registry_closeout_task import run_registry_closeout_task
from runtime.cognition.tasks.reminder_task import run_reminder_task
from runtime.cognition.tasks.wiki_approval_report_task import build_chief_of_staff_approval_report
from runtime.cognition.tasks.wiki_approval_task import record_wiki_approval
from runtime.cognition.tasks.wiki_promotion_task import promote_chief_of_staff_page
from runtime.cognition.tasks.wiki_recall_checkpoint_task import run_wiki_recall_checkpoint


@dataclass(frozen=True)
class ResolvedTask:
    task_name: str
    execute: Callable[[], dict[str, object]]


def resolve_schedule_task(schedule: ScheduleSpec, *, workspace_root: str | None = None) -> ResolvedTask:
    target_type = schedule.payload.target_type
    if target_type == "wiki-refresh":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: _run_wiki_refresh(schedule, workspace_root),
        )
    if target_type == "wiki-refresh-batch":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: _run_wiki_batch_refresh(schedule, workspace_root),
        )
    if target_type == "wiki-promotion":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: promote_chief_of_staff_page(
                page_id=_page_id(schedule),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
            ),
        )
    if target_type == "wiki-approval":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: record_wiki_approval(
                page_id=_page_id(schedule),
                decision=str(schedule.payload.task_config.get("decision") or "approved"),
                reviewer=str(schedule.payload.task_config.get("reviewer") or schedule.owner_role),
                note=str(schedule.payload.task_config.get("note") or ""),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
            ),
        )
    if target_type == "wiki-approval-report":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: build_chief_of_staff_approval_report(
                workspace_root=workspace_root,
                trigger_mode="scheduled",
            ),
        )
    if target_type == "reminder":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: run_reminder_task(
                reminder_id=schedule.payload.target_ref,
                task_config=_resolved_notification_task_config(schedule, workspace_root=workspace_root),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
                delivery_channel=schedule.payload.delivery_channel,
                delivery_target=schedule.payload.delivery_target,
            ),
        )
    if target_type == "email":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: run_email_task(
                email_id=schedule.payload.target_ref,
                task_config=_resolved_notification_task_config(schedule, workspace_root=workspace_root),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
                delivery_channel=schedule.payload.delivery_channel,
                delivery_target=schedule.payload.delivery_target,
            ),
        )
    if target_type == "registry-closeout":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: run_registry_closeout_task(
                closeout_id=schedule.payload.target_ref,
                task_config=schedule.payload.task_config,
                workspace_root=workspace_root,
                trigger_mode="scheduled",
                delivery_channel=schedule.payload.delivery_channel,
                delivery_target=schedule.payload.delivery_target,
            ),
        )
    if target_type == "operating-review-closeout":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: run_operating_review_closeout_task(
                operating_review_path=str(schedule.payload.task_config.get("operatingReviewPath") or ""),
                closeout_path=str(schedule.payload.task_config.get("closeoutPath") or schedule.payload.task_config.get("sourcePath") or ""),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
                delivery_channel=schedule.payload.delivery_channel,
                delivery_target=schedule.payload.delivery_target,
            ),
        )
    if target_type == "checkpoint":
        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: run_checkpoint_task(
                checkpoint_id=schedule.payload.target_ref,
                task_config=schedule.payload.task_config,
                workspace_root=workspace_root,
                trigger_mode="scheduled",
            ),
        )
    if target_type == "wiki-workbench":
        from runtime.cognition.tasks.wiki_workbench_task import build_chief_of_staff_knowledge_workbench

        return ResolvedTask(
            task_name=schedule.payload.target_ref,
            execute=lambda: build_chief_of_staff_knowledge_workbench(
                workspace_root=workspace_root,
                trigger_mode="scheduled",
            ),
        )

    target_ref = schedule.payload.target_ref
    if target_type != "custom":
        raise ValueError(f"Unsupported schedule targetType: {target_type}")
    if target_ref == "chief-of-staff-wiki-refresh-current-state":
        return ResolvedTask(
            task_name=target_ref,
            execute=lambda: _run_wiki_refresh(schedule, workspace_root),
        )
    if target_ref == "chief-of-staff-wiki-promote-current-state":
        return ResolvedTask(
            task_name=target_ref,
            execute=lambda: promote_chief_of_staff_page(
                page_id=_page_id(schedule),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
            ),
        )
    if target_ref == "chief-of-staff-wiki-recall-check-current-state":
        return ResolvedTask(
            task_name=target_ref,
            execute=lambda: run_wiki_recall_checkpoint(
                page_id=_page_id(schedule),
                workspace_root=workspace_root,
                trigger_mode="scheduled",
                recall_mode=str(schedule.payload.task_config.get("recallMode") or "stable-only"),
            ),
        )
    raise ValueError(f"Unsupported schedule targetRef: {target_ref}")


def _run_wiki_refresh(schedule: ScheduleSpec, workspace_root: str | None) -> dict[str, object]:
    from runtime.cognition.runners.wiki_refresh_runner import run_chief_of_staff_wiki_refresh

    result = run_chief_of_staff_wiki_refresh(
        page_id=_page_id(schedule),
        title=str(schedule.payload.task_config.get("title") or "总助 LLM wiki 半自动整理现状页"),
        workspace_root=workspace_root,
        trigger_mode="scheduled",
    )
    return {
        "status": result.status,
        "artifactPaths": [result.output_page_path.as_posix(), result.audit_path.as_posix()],
        "note": "scheduled wiki refresh completed",
    }


def _run_wiki_batch_refresh(schedule: ScheduleSpec, workspace_root: str | None) -> dict[str, object]:
    from runtime.cognition.runners.wiki_batch_refresh_runner import run_chief_of_staff_wiki_batch_refresh

    spec_ids = schedule.payload.task_config.get("specIds") or []
    result = run_chief_of_staff_wiki_batch_refresh(
        spec_ids=tuple(str(item) for item in spec_ids) if isinstance(spec_ids, list) else None,
        workspace_root=workspace_root,
        trigger_mode="scheduled",
    )
    return {
        "status": result.status,
        "artifactPaths": list(result.artifact_paths),
        "note": "scheduled wiki batch refresh completed",
    }


def _page_id(schedule: ScheduleSpec) -> str:
    return str(schedule.payload.task_config.get("pageId") or "chief-of-staff-llm-wiki-semi-auto-current-state")


def _resolved_notification_task_config(schedule: ScheduleSpec, *, workspace_root: str | None) -> dict[str, object]:
    task_config = dict(schedule.payload.task_config)
    content_template = str(task_config.get("contentTemplate") or "").strip().lower()
    if content_template != "approval-queue-governance":
        return task_config
    if schedule.payload.target_type == "reminder":
        return build_approval_queue_reminder_task_config(task_config, workspace_root=workspace_root)
    if schedule.payload.target_type == "email":
        return build_approval_queue_email_task_config(task_config, workspace_root=workspace_root)
    return task_config