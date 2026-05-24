from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import workspace_root as resolve_workspace_root
from runtime.cognition.tasks.registry_closeout_task import run_registry_closeout_task


def run_operating_review_closeout_task(
    *,
    operating_review_path: str,
    closeout_path: str,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
    delivery_channel: str | None = None,
    delivery_target: str | None = None,
) -> dict[str, object]:
    if not str(operating_review_path).strip() or not str(closeout_path).strip():
        raise ValueError("operating review closeout bridge requires both operating_review_path and closeout_path")

    operating_review, resolved_review_path = _load_object(
        source_path=operating_review_path,
        expected_object_type="OPERATING_REVIEW",
        workspace_root=workspace_root,
    )
    closeout_object, resolved_closeout_path = _load_object(
        source_path=closeout_path,
        expected_object_type="CENTRAL_REGISTRY_CLOSEOUT",
        workspace_root=workspace_root,
    )
    _validate_trigger_chain(
        operating_review=operating_review,
        closeout_object=closeout_object,
        operating_review_path=resolved_review_path,
        closeout_path=resolved_closeout_path,
    )

    closeout_id = str(closeout_object.get("objectId") or resolved_closeout_path.stem)
    return run_registry_closeout_task(
        closeout_id=closeout_id,
        task_config={
            "sourcePath": resolved_closeout_path.as_posix(),
            "triggerSource": {
                "objectType": "OPERATING_REVIEW",
                "objectId": str(operating_review.get("objectId") or ""),
                "sourcePath": resolved_review_path.as_posix(),
            },
        },
        workspace_root=workspace_root,
        trigger_mode=trigger_mode,
        delivery_channel=delivery_channel,
        delivery_target=delivery_target,
    )


def _load_object(
    *,
    source_path: str,
    expected_object_type: str,
    workspace_root: str | None,
) -> tuple[dict[str, Any], Path]:
    resolved_path = _resolve_source_path(source_path, workspace_root)
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{expected_object_type} source must be a JSON object")
    object_type = str(payload.get("objectType") or "").strip()
    if object_type != expected_object_type:
        raise ValueError(f"expected {expected_object_type}, got {object_type or 'empty'}")
    return payload, resolved_path


def _resolve_source_path(source_path: str, workspace_root: str | None) -> Path:
    path = Path(source_path)
    if path.is_absolute():
        return path
    return (resolve_workspace_root(workspace_root) / path).resolve()


def _validate_trigger_chain(
    *,
    operating_review: dict[str, Any],
    closeout_object: dict[str, Any],
    operating_review_path: Path,
    closeout_path: Path,
) -> None:
    operating_review_id = str(operating_review.get("objectId") or "").strip()
    if not operating_review_id:
        raise ValueError("OPERATING_REVIEW object must include objectId")

    depends_on = closeout_object.get("dependsOn")
    if isinstance(depends_on, list) and operating_review_id in {str(item) for item in depends_on}:
        return

    raise ValueError(
        "operating review closeout bridge requires CENTRAL_REGISTRY_CLOSEOUT.dependsOn to include "
        f"{operating_review_id} ({operating_review_path.as_posix()} -> {closeout_path.as_posix()})"
    )