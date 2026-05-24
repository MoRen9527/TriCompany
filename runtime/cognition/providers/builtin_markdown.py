from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from runtime.cognition.contracts.provider_contract import (
    ConsolidationWrite,
    CognitionProvider,
    MemoryScope,
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)
from runtime.cognition.providers.storage import FileBackedCognitionStore


class BuiltinMarkdownProvider(CognitionProvider):
    """Built-in markdown-backed private memory provider."""

    name = "builtin-markdown"
    is_external = False

    def __init__(self, storage_root: str | None = None) -> None:
        self.store = FileBackedCognitionStore(storage_root)

    def scopes_supported(self) -> Iterable[MemoryScope]:
        return (MemoryScope.EMPLOYEE_PRIVATE,)

    def system_prompt_block(self, actor_id: str) -> str:
        return f"Builtin markdown cognition enabled for {actor_id}."

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        for namespace in query.namespaces:
            if not namespace.startswith("employee/"):
                continue
            content = self.store.read_namespace(namespace)
            if content:
                yield RecallResult(
                    provider_name=self.name,
                    namespace=namespace,
                    content=content,
                    score=0.7,
                )

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        body = (
            f"- actor: {actor_id}\n"
            f"- user: {user_content}\n"
            f"- assistant: {assistant_content}"
        )
        self.store.append_entry(
            namespace_bundle.private_namespace.key,
            title=f"turn-sync-{actor_id}",
            body=body,
            provider_name=self.name,
        )

    def consolidate_session(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> Iterable[ConsolidationWrite]:
        user_messages = [m.get("content", "") for m in messages if m.get("role") == "user"]
        assistant_messages = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
        last_user = user_messages[-1] if user_messages else ""
        last_assistant = assistant_messages[-1] if assistant_messages else ""
        yield ConsolidationWrite(
            namespace=namespace_bundle.private_namespace.key,
            scope=MemoryScope.EMPLOYEE_PRIVATE,
            content=(
                f"- actor: {actor_id}\n"
                f"- message-count: {len(messages)}\n"
                f"- last-user: {last_user}\n"
                f"- last-assistant: {last_assistant}"
            ),
            reason="session-private-summary",
        )

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        writes = self.consolidate_session(actor_id, messages, namespace_bundle)
        self.store.persist_consolidation_writes(writes, provider_name=self.name)
