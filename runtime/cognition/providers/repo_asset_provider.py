from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from runtime.cognition.contracts.provider_contract import (
    CognitionProvider,
    MemoryScope,
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)


@dataclass(frozen=True)
class RepoAssetSource:
    label: str
    path: Path


class RepoBackedPrivateAssetProvider(CognitionProvider):
    """Read-only provider that exposes repo-backed durable role assets as recall context."""

    is_external = False

    def __init__(
        self,
        *,
        actor_id: str,
        asset_sources: Sequence[RepoAssetSource],
        provider_name: str = "repo-asset-bridge",
    ) -> None:
        self.actor_id = actor_id
        self.asset_sources = tuple(asset_sources)
        self._name = provider_name

    @property
    def name(self) -> str:
        return self._name

    def scopes_supported(self) -> Iterable[MemoryScope]:
        return (MemoryScope.EMPLOYEE_PRIVATE,)

    def system_prompt_block(self, actor_id: str) -> str:
        return f"Repo-backed durable assets are available for {actor_id}."

    def _snapshot(self) -> str:
        parts: list[str] = []
        for source in self.asset_sources:
            if not source.path.exists():
                continue
            content = source.path.read_text(encoding="utf-8").strip()
            if not content:
                continue
            parts.append(
                f"## {source.label}\n"
                f"- source: {source.path.as_posix()}\n\n"
                f"{content}"
            )
        return "\n\n".join(parts).strip()

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        private_namespace = f"employee/{self.actor_id}"
        if query.actor_id != self.actor_id or private_namespace not in query.namespaces:
            return []

        snapshot = self._snapshot()
        if not snapshot:
            return []

        return [
            RecallResult(
                provider_name=self.name,
                namespace=private_namespace,
                content=snapshot,
                score=1.0,
            )
        ]

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        return None

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        return None