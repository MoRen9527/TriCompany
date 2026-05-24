from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, workspace_root as resolve_workspace_root
from runtime.cognition.dispatch.host_dispatcher import dispatch_task_payload


def run_registry_closeout_task(
    *,
    closeout_id: str,
    task_config: dict[str, Any],
    workspace_root: str | None = None,
    trigger_mode: str = "scheduled",
    delivery_channel: str | None = None,
    delivery_target: str | None = None,
) -> dict[str, object]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("registry-closeout-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"

    closeout_object, source_path = _resolve_closeout_object(task_config, workspace_root)
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "closeoutId": closeout_id,
        "generatedAt": _timestamp_now(),
        "sourcePath": source_path,
        "objectType": str(closeout_object.get("objectType") or "CENTRAL_REGISTRY_CLOSEOUT"),
        "objectId": str(closeout_object.get("objectId") or closeout_id),
        "closeoutSubject": _closeout_subject(closeout_object, fallback=closeout_id),
        "scopeDecision": _scope_decision(closeout_object),
        "registryFindingCount": _registry_finding_count(closeout_object),
        "closeout": closeout_object,
    }
    trigger_source = task_config.get("triggerSource")
    if isinstance(trigger_source, dict):
        payload["triggerSource"] = {
            "objectType": str(trigger_source.get("objectType") or ""),
            "objectId": str(trigger_source.get("objectId") or ""),
            "sourcePath": str(trigger_source.get("sourcePath") or ""),
        }
    dispatch_result = dispatch_task_payload(
        task_kind="registry-closeout",
        payload=payload,
        task_config=task_config,
        delivery_channel=delivery_channel,
        delivery_target=delivery_target,
    )
    payload["delivery"] = dispatch_result
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": str(dispatch_result.get("taskStatus") or "completed"),
        "deliveryStatus": str(dispatch_result.get("deliveryStatus") or "rendered"),
        "artifactPaths": [path.as_posix()],
        "note": str(dispatch_result.get("note") or "registry closeout payload generated"),
    }


def _resolve_closeout_object(
    task_config: dict[str, Any],
    workspace_root: str | None,
) -> tuple[dict[str, Any], str]:
    inline_object = task_config.get("closeoutObject")
    if isinstance(inline_object, dict):
        return _validated_closeout_object(dict(inline_object)), "inline:taskConfig.closeoutObject"

    source_path = str(task_config.get("sourcePath") or "").strip()
    if not source_path:
        raise ValueError("registry-closeout task requires sourcePath or closeoutObject")

    resolved_path = _resolve_source_path(source_path, workspace_root)
    loaded = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("registry-closeout sourcePath must point to a JSON object")
    return _validated_closeout_object(dict(loaded)), resolved_path.as_posix()


def _resolve_source_path(source_path: str, workspace_root: str | None) -> Path:
    path = Path(source_path)
    if path.is_absolute():
        return path
    return (resolve_workspace_root(workspace_root) / path).resolve()


def _validated_closeout_object(closeout_object: dict[str, Any]) -> dict[str, Any]:
    object_type = str(closeout_object.get("objectType") or "").strip()
    if object_type != "CENTRAL_REGISTRY_CLOSEOUT":
        raise ValueError(f"registry-closeout task expected CENTRAL_REGISTRY_CLOSEOUT, got {object_type or 'empty'}")

    payload = closeout_object.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("registry-closeout task requires payload to be a JSON object")
    return closeout_object


def _closeout_subject(closeout_object: dict[str, Any], *, fallback: str) -> str:
    payload = closeout_object.get("payload")
    if isinstance(payload, dict):
        subject = str(payload.get("closeoutSubject") or "").strip()
        if subject:
            return subject
    title = str(closeout_object.get("title") or "").strip()
    return title or fallback


def _scope_decision(closeout_object: dict[str, Any]) -> str | None:
    payload = closeout_object.get("payload")
    if not isinstance(payload, dict):
        return None
    value = payload.get("scopeDecision")
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)


def _registry_finding_count(closeout_object: dict[str, Any]) -> int:
    payload = closeout_object.get("payload")
    if not isinstance(payload, dict):
        return 0
    findings = payload.get("registryFindings")
    return len(findings) if isinstance(findings, list) else 0


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")