from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, Sequence

from runtime.cognition.contracts.provider_contract import (
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)
from runtime.cognition.providers.supermemory_backend import DEFAULT_SEARCH_MODE


class SupermemoryDocumentsClient(Protocol):
    def add(self, **kwargs: Any) -> Mapping[str, Any]:
        ...


class SupermemorySearchDocumentsClient(Protocol):
    def __call__(self, **kwargs: Any) -> Mapping[str, Any]:
        ...


class SupermemorySearchClient(Protocol):
    @property
    def documents(self) -> SupermemorySearchDocumentsClient:
        ...


class SupermemorySdkClient(Protocol):
    @property
    def documents(self) -> SupermemoryDocumentsClient:
        ...

    @property
    def search(self) -> SupermemorySearchClient:
        ...


@dataclass(frozen=True)
class SupermemorySdkBackendConfig:
    limit: int = 5
    threshold: float = 0.6
    search_mode: str = DEFAULT_SEARCH_MODE
    metadata: Mapping[str, Any] = field(default_factory=dict)
    task_type: str = "memory"


class SupermemorySdkExternalBackend:
    """SDK seam for Supermemory-backed cognition integration."""

    def __init__(
        self,
        client: SupermemorySdkClient,
        config: SupermemorySdkBackendConfig | None = None,
    ) -> None:
        self._client = client
        self._config = config or SupermemorySdkBackendConfig()

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        results: list[RecallResult] = []
        for namespace in query.namespaces:
            response = self._client.search.documents(
                q=query.text,
                containerTag=self.namespace_to_container_tag(namespace),
                limit=self._config.limit,
                threshold=self._config.threshold,
                searchMode=self._config.search_mode,
            )
            results.extend(self._map_search_results(namespace, response))
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
        self._add_document(
            content=content,
            container_tag=self.namespace_to_container_tag(namespace_bundle.private_namespace.key),
            custom_id=f"turn-{actor_id}",
            metadata={
                **self._base_metadata(namespace_bundle.private_namespace.key),
                "recordType": "turn-sync",
            },
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

        self._add_document(
            content=(
                f"actor: {actor_id}\n"
                f"messageCount: {len(messages)}\n"
                f"sharedConclusion: {last_assistant or last_user}"
            ),
            container_tag=self.namespace_to_container_tag(namespace_bundle.org_shared_namespace.key),
            custom_id=f"session-shared-{actor_id}",
            metadata={
                **self._base_metadata(namespace_bundle.org_shared_namespace.key),
                "recordType": "session-shared-summary",
            },
        )
        self._add_document(
            content=(
                f"actor: {actor_id}\n"
                f"privateNamespace: {namespace_bundle.private_namespace.key}\n"
                f"orgSharedNamespace: {namespace_bundle.org_shared_namespace.key}\n"
                f"auditNamespace: {namespace_bundle.audit_namespace.key}\n"
                f"lastUser: {last_user}\n"
                f"lastAssistant: {last_assistant}"
            ),
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
    ) -> Mapping[str, Any]:
        return self._client.documents.add(
            content=content,
            containerTag=container_tag,
            customId=custom_id,
            metadata=dict(metadata),
            taskType=self._config.task_type,
        )

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

    def _map_search_results(
        self,
        namespace: str,
        response: Mapping[str, Any],
    ) -> list[RecallResult]:
        raw_results = response.get("results", [])
        if not isinstance(raw_results, list):
            return []

        mapped_results: list[RecallResult] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            content = item.get("memory") or item.get("chunk")
            if not isinstance(content, str) or not content.strip():
                continue
            similarity = item.get("similarity")
            score = float(similarity) if isinstance(similarity, (int, float)) else None
            mapped_results.append(
                RecallResult(
                    provider_name="supermemory-sdk",
                    namespace=namespace,
                    content=content,
                    score=score,
                )
            )
        return mapped_results