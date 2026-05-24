from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib import error, request

from runtime.cognition.contracts.provider_contract import (
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)


@dataclass(frozen=True)
class HttpExternalBackendConfig:
    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 5.0


class HttpExternalCognitionBackend:
    """Minimal HTTP backend for external cognition providers.

    This is still a generic transport layer, not a vendor SDK. It lets the
    adapter talk to a remote-compatible backend with explicit auth and timeout
    behavior so later Honcho / Supermemory style SDK wiring has a tested seam.
    """

    def __init__(self, config: HttpExternalBackendConfig) -> None:
        self._config = config

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        payload = {
            "actor_id": query.actor_id,
            "text": query.text,
            "namespaces": list(query.namespaces),
        }
        response = self._post_json("/prefetch", payload)
        raw_results = response.get("results", [])
        for item in raw_results:
            namespace = item.get("namespace")
            content = item.get("content")
            if not isinstance(namespace, str) or not isinstance(content, str):
                continue
            score_value = item.get("score")
            score = float(score_value) if isinstance(score_value, (int, float)) else None
            yield RecallResult(
                provider_name="http-external-backend",
                namespace=namespace,
                content=content,
                score=score,
            )

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        payload = {
            "actor_id": actor_id,
            "user_content": user_content,
            "assistant_content": assistant_content,
            "namespace_bundle": self._bundle_payload(namespace_bundle),
        }
        self._post_json("/sync-turn", payload)

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        payload = {
            "actor_id": actor_id,
            "messages": list(messages),
            "namespace_bundle": self._bundle_payload(namespace_bundle),
        }
        self._post_json("/session-end", payload)

    def _bundle_payload(self, namespace_bundle: NamespaceBundle) -> dict[str, Any]:
        return {
            "actor_id": namespace_bundle.actor_id,
            "private_namespace": namespace_bundle.private_namespace.key,
            "org_shared_namespace": namespace_bundle.org_shared_namespace.key,
            "audit_namespace": namespace_bundle.audit_namespace.key,
        }

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=self._build_url(path),
            data=encoded,
            headers=self._headers(),
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self._config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"HTTP external cognition backend request failed for {path} with status {exc.code}: {body or exc.reason}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"HTTP external cognition backend request failed for {path}: {exc}"
            ) from exc

        if not body.strip():
            return {}
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"HTTP external cognition backend returned invalid JSON for {path}: {body}"
            ) from exc
        if not isinstance(decoded, dict):
            raise RuntimeError(
                f"HTTP external cognition backend returned non-object JSON for {path}: {decoded}"
            )
        return decoded

    def _build_url(self, path: str) -> str:
        return f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"