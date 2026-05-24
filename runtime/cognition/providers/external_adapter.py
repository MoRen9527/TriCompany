from __future__ import annotations

from typing import Any, Iterable, Mapping, Protocol, Sequence

from runtime.cognition.contracts.provider_contract import (
    CognitionProvider,
    MemoryScope,
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)


class ExternalCognitionBackend(Protocol):
    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        ...

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        ...

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        ...


class NullExternalCognitionBackend:
    def prefetch(self, _query: RecallQuery) -> Iterable[RecallResult]:
        return ()

    def sync_turn(
        self,
        _actor_id: str,
        _user_content: str,
        _assistant_content: str,
        _namespace_bundle: NamespaceBundle,
    ) -> None:
        return None

    def on_session_end(
        self,
        _actor_id: str,
        _messages: Sequence[Mapping[str, Any]],
        _namespace_bundle: NamespaceBundle,
    ) -> None:
        return None


class ExternalCognitionAdapter(CognitionProvider):
    """Adapter wrapper for future Honcho / Supermemory style providers."""

    is_external = True

    def __init__(
        self,
        backend_name: str,
        backend: ExternalCognitionBackend | None = None,
    ) -> None:
        self._backend_name = backend_name
        self._backend = backend or NullExternalCognitionBackend()

    @property
    def name(self) -> str:
        return f"external-{self._backend_name}"

    def scopes_supported(self) -> Iterable[MemoryScope]:
        return (MemoryScope.EMPLOYEE_PRIVATE, MemoryScope.ORG_SHARED)

    def system_prompt_block(self, actor_id: str) -> str:
        return f"External cognition adapter {self._backend_name} prepared for {actor_id}."

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        for result in self._backend.prefetch(query):
            if result.namespace not in query.namespaces:
                continue
            yield RecallResult(
                provider_name=self.name,
                namespace=result.namespace,
                content=result.content,
                score=result.score,
            )

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        self._backend.sync_turn(
            actor_id,
            user_content,
            assistant_content,
            namespace_bundle,
        )

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        self._backend.on_session_end(actor_id, messages, namespace_bundle)
