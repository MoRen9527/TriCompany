from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


def dispatch_task_payload(
    *,
    task_kind: str,
    payload: dict[str, Any],
    task_config: dict[str, Any],
    delivery_channel: str | None,
    delivery_target: str | None,
) -> dict[str, object]:
    channel = _resolve_channel(task_kind, task_config, delivery_channel)
    target = str(task_config.get("deliveryTarget") or delivery_target or "").strip()
    delivery_mode = str(task_config.get("deliveryMode") or _default_delivery_mode(channel)).strip().lower()

    if delivery_mode == "render-only" or channel in {"", "file", "audit"}:
        return {
            "taskStatus": "completed",
            "deliveryStatus": "rendered",
            "deliveryChannel": channel or "file",
            "deliveryTarget": target or "knowledge/employees/ceo-chief-of-staff/audit",
            "note": "payload rendered for manual dispatch",
        }

    if channel not in {"webhook", "email-gateway", "host-dispatcher"}:
        raise ValueError(f"Unsupported delivery channel: {channel}")

    endpoint = _resolve_endpoint(channel=channel, target=target, task_config=task_config)
    if not endpoint:
        return {
            "taskStatus": "blocked",
            "deliveryStatus": "blocked",
            "deliveryChannel": channel,
            "deliveryTarget": target,
            "note": "delivery endpoint not configured",
        }

    request_payload = payload if channel != "host-dispatcher" else {
        "taskKind": task_kind,
        "deliveryChannel": channel,
        "deliveryTarget": target,
        "payload": payload,
    }
    response = _post_json(endpoint=endpoint, payload=request_payload, headers=_resolve_headers(task_config))
    ok = 200 <= response["responseStatusCode"] < 300
    return {
        "taskStatus": "completed" if ok else "failed",
        "deliveryStatus": "delivered" if ok else "failed",
        "deliveryChannel": channel,
        "deliveryTarget": endpoint,
        "responseStatusCode": response["responseStatusCode"],
        "responseBodyExcerpt": response["responseBodyExcerpt"],
        "note": "payload dispatched to delivery endpoint" if ok else "delivery endpoint returned an error",
    }


def _resolve_channel(task_kind: str, task_config: dict[str, Any], delivery_channel: str | None) -> str:
    explicit = str(task_config.get("deliveryChannel") or delivery_channel or "").strip().lower()
    if explicit:
        return explicit
    if task_kind == "email" and task_config.get("gatewayUrl"):
        return "email-gateway"
    if task_config.get("webhookUrl"):
        return "webhook"
    return "file"


def _default_delivery_mode(channel: str) -> str:
    return "dispatch" if channel in {"webhook", "email-gateway", "host-dispatcher"} else "render-only"


def _resolve_endpoint(*, channel: str, target: str, task_config: dict[str, Any]) -> str:
    if target:
        return target
    if channel == "webhook":
        return str(task_config.get("webhookUrl") or "").strip()
    if channel == "email-gateway":
        return str(task_config.get("gatewayUrl") or task_config.get("emailGatewayUrl") or "").strip()
    if channel == "host-dispatcher":
        direct = str(task_config.get("dispatcherUrl") or "").strip()
        if direct:
            return direct
        env_name = str(task_config.get("dispatcherUrlEnv") or "TRICOMPANY_HOST_DISPATCHER_URL").strip()
        return os.getenv(env_name, "").strip()
    return ""


def _resolve_headers(task_config: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json; charset=utf-8"}
    raw_headers = task_config.get("headers")
    if isinstance(raw_headers, dict):
        for key, value in raw_headers.items():
            text = str(value).strip()
            if text:
                headers[str(key)] = text
    auth_token = str(task_config.get("authToken") or "").strip()
    if not auth_token:
        env_name = str(task_config.get("authTokenEnv") or "").strip()
        if env_name:
            auth_token = os.getenv(env_name, "").strip()
    if auth_token:
        headers.setdefault("Authorization", f"Bearer {auth_token}")
    return headers


def _post_json(*, endpoint: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, object]:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(endpoint, data=raw, headers=headers, method="POST")
    try:
        with request.urlopen(http_request, timeout=10) as response:
            body = response.read(1024).decode("utf-8", errors="replace")
            return {
                "responseStatusCode": int(response.status),
                "responseBodyExcerpt": body,
            }
    except error.HTTPError as exc:
        body = exc.read(1024).decode("utf-8", errors="replace")
        return {
            "responseStatusCode": int(exc.code),
            "responseBodyExcerpt": body,
        }