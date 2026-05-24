from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence


class MemoryScope(str, Enum):
    EMPLOYEE_PRIVATE = "employee-private"
    ORG_SHARED = "org-shared"
    SESSION_TRANSIENT = "session-transient"
    AUDIT = "audit"


@dataclass(frozen=True)
class CognitionNamespace:
    key: str
    scope: MemoryScope
    owner: str
    description: str


@dataclass(frozen=True)
class NamespaceBundle:
    actor_id: str
    private_namespace: CognitionNamespace
    org_shared_namespace: CognitionNamespace
    audit_namespace: CognitionNamespace


@dataclass(frozen=True)
class RecallQuery:
    actor_id: str
    text: str
    namespaces: tuple[str, ...]


@dataclass(frozen=True)
class RecallResult:
    provider_name: str
    namespace: str
    content: str
    score: Optional[float] = None


@dataclass(frozen=True)
class ConsolidationWrite:
    namespace: str
    scope: MemoryScope
    content: str
    reason: str


class CognitionProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    def scopes_supported(self) -> Iterable[MemoryScope]:
        ...

    def system_prompt_block(self, actor_id: str) -> str:
        ...

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
