from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence
from urllib import error, request

from runtime.cognition.contracts.provider_contract import (
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)


SUPERMEMORY_ADD_PATH = "/v3/documents"
SUPERMEMORY_SEARCH_PATH = "/v4/search"
DEFAULT_SEARCH_MODE = "hybrid"


@dataclass(frozen=True)
class SupermemoryBackendConfig:
    api_key: str
    base_url: str = "https://api.supermemory.ai"
    timeout_seconds: float = 5.0
    max_retries: int = 2
    retry_statuses: tuple[int, ...] = (408, 409, 429, 500, 502, 503, 504)
    backoff_seconds: tuple[float, ...] = (0.2, 0.5, 1.0)
    search_mode: str = DEFAULT_SEARCH_MODE
    limit: int = 5
    threshold: float = 0.6
    rerank: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)
    use_bearer_auth: bool = True


class SupermemoryExternalBackend:
    """Official Supermemory HTTP schema adapter.

    Uses documented endpoints:
    - POST /v3/documents for writes
    - POST /v4/search for recall
    """

    def __init__(self, config: SupermemoryBackendConfig) -> None:
        self._config = config

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        results: list[RecallResult] = []
        for namespace in query.namespaces:
            payload: dict[str, Any] = {
                "q": query.text,
                "containerTag": self.namespace_to_container_tag(namespace),
                "searchMode": self._config.search_mode,
                "limit": self._config.limit,
                "threshold": self._config.threshold,
            }
            if self._config.rerank:
                payload["rerank"] = True

            response = self._post_json(SUPERMEMORY_SEARCH_PATH, payload)
            raw_results = response.get("results", [])
            if not isinstance(raw_results, list):
                continue
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                content = item.get("memory") or item.get("chunk")
                if not isinstance(content, str) or not content.strip():
                    continue
                similarity = item.get("similarity")
                score = float(similarity) if isinstance(similarity, (int, float)) else None
                results.append(
                    RecallResult(
                        provider_name="supermemory",
                        namespace=namespace,
                        content=content,
                        score=score,
                    )
                )
        return results

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        content = (
            f"actor: {actor_id}\n"
            f"user: {user_content}\n"
            f"assistant: {assistant_content}"
        )
        metadata = self._base_metadata(namespace_bundle.private_namespace.key)
        metadata["recordType"] = "turn-sync"
        self._add_document(
            content=content,
            container_tag=self.namespace_to_container_tag(namespace_bundle.private_namespace.key),
            custom_id=f"turn-{actor_id}",
            metadata=metadata,
        )

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        user_messages = [str(item.get("content", "")) for item in messages if item.get("role") == "user"]
        assistant_messages = [str(item.get("content", "")) for item in messages if item.get("role") == "assistant"]
        last_user = user_messages[-1] if user_messages else ""
        last_assistant = assistant_messages[-1] if assistant_messages else ""

        shared_content = (
            f"actor: {actor_id}\n"
            f"messageCount: {len(messages)}\n"
            f"sharedConclusion: {last_assistant or last_user}"
        )
        self._add_document(
            content=shared_content,
            container_tag=self.namespace_to_container_tag(namespace_bundle.org_shared_namespace.key),
            custom_id=f"session-shared-{actor_id}",
            metadata={
                **self._base_metadata(namespace_bundle.org_shared_namespace.key),
                "recordType": "session-shared-summary",
            },
        )

        audit_content = (
            f"actor: {actor_id}\n"
            f"privateNamespace: {namespace_bundle.private_namespace.key}\n"
            f"orgSharedNamespace: {namespace_bundle.org_shared_namespace.key}\n"
            f"auditNamespace: {namespace_bundle.audit_namespace.key}\n"
            f"lastUser: {last_user}\n"
            f"lastAssistant: {last_assistant}"
        )
        self._add_document(
            content=audit_content,
            container_tag=self.namespace_to_container_tag(namespace_bundle.audit_namespace.key),
            custom_id=f"session-audit-{actor_id}",
            metadata={
                **self._base_metadata(namespace_bundle.audit_namespace.key),
                "recordType": "session-audit-trace",
            },
        )

    def _add_document(
        self,
        *,
        content: str,
        container_tag: str,
        custom_id: str,
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "content": content,
            "containerTag": container_tag,
            "customId": custom_id,
            "metadata": dict(metadata),
            "taskType": "memory",
        }
        return self._post_json(SUPERMEMORY_ADD_PATH, payload)

    def _base_metadata(self, namespace: str) -> dict[str, Any]:
        return {
            **dict(self._config.metadata),
            "namespace": namespace,
        }

    def namespace_to_container_tag(self, namespace: str) -> str:
        container_tag = namespace.replace("/", ":")
        if len(container_tag) > 100:
            raise ValueError(
                f"Supermemory containerTag exceeds 100 chars after namespace mapping: {namespace}"
            )
        return container_tag

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._config.use_bearer_auth:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        else:
            headers["x-supermemory-api-key"] = self._config.api_key
        return headers

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        attempt = 0
        while True:
            try:
                return self._post_json_once(path, payload)
            except RuntimeError as exc:
                status = _status_from_error(exc)
                should_retry = status in self._config.retry_statuses if status is not None else False
                if not should_retry or attempt >= self._config.max_retries:
                    raise
                delay = self._config.backoff_seconds[min(attempt, len(self._config.backoff_seconds) - 1)]
                time.sleep(delay)
                attempt += 1

    def _post_json_once(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
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
                f"Supermemory request failed for {path} with status {exc.code}: {_extract_error_message(body)}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Supermemory request failed for {path}: {exc}") from exc

        if not body.strip():
            return {}
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Supermemory returned invalid JSON for {path}: {body}"
            ) from exc
        if not isinstance(decoded, dict):
            raise RuntimeError(
                f"Supermemory returned non-object JSON for {path}: {decoded}"
            )
        return decoded

    def _build_url(self, path: str) -> str:
        return f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"


def _extract_error_message(body: str) -> str:
    if not body.strip():
        return "empty response body"
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError:
        return body
    if isinstance(decoded, dict):
        for key in ("message", "error", "detail"):
            value = decoded.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = value.get("message") or value.get("detail")
                if isinstance(nested, str):
                    return nested
    return body


def _status_from_error(exc: RuntimeError) -> int | None:
    text = str(exc)
    marker = "status "
    if marker not in text:
        return None
    after = text.split(marker, 1)[1]
    digits = []
    for char in after:
        if char.isdigit():
            digits.append(char)
            continue
        break
    if not digits:
        return None
    return int("".join(digits))