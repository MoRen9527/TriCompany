from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, cast

from runtime.cognition.contracts.namespace_policy import (
    DEFAULT_NAMESPACE_POLICY,
    NamespacePolicy,
)
from runtime.cognition.contracts.provider_contract import (
    ConsolidationWrite,
    CognitionProvider,
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)
from runtime.cognition.kernel.recall_context import build_recall_context_block


@dataclass(frozen=True)
class ActorProfile:
    actor_id: str
    role_name: str
    display_name: str


class MetaCognitionKernel:
    """Shared kernel for all virtual-company roles.

    The kernel is shared, but each actor keeps a private namespace while the
    organization also exposes one audited shared namespace.
    """

    def __init__(self, policy: NamespacePolicy | None = None) -> None:
        self.policy = policy or DEFAULT_NAMESPACE_POLICY
        self._providers: Dict[str, CognitionProvider] = {}
        self._actors: Dict[str, ActorProfile] = {}
        self._external_provider_name: str | None = None

    def register_actor(self, actor_id: str, role_name: str, display_name: str) -> None:
        self._actors[actor_id] = ActorProfile(
            actor_id=actor_id,
            role_name=role_name,
            display_name=display_name,
        )

    def register_provider(self, provider: CognitionProvider) -> None:
        if getattr(provider, "is_external", False):
            if self._external_provider_name is not None:
                raise ValueError(
                    "Only one external cognition provider can be active at a time: "
                    f"{self._external_provider_name} is already registered."
                )
            self._external_provider_name = provider.name
        self._providers[provider.name] = provider

    def actor(self, actor_id: str) -> ActorProfile:
        return self._actors[actor_id]

    def namespaces_for(self, actor_id: str) -> NamespaceBundle:
        actor = self.actor(actor_id)
        return self.policy.resolve(actor.actor_id, actor.role_name)

    def build_recall_queries(self, actor_id: str, message: str) -> List[RecallQuery]:
        bundle = self.namespaces_for(actor_id)
        return [
            RecallQuery(
                actor_id=actor_id,
                text=message,
                namespaces=(
                    bundle.private_namespace.key,
                    bundle.org_shared_namespace.key,
                ),
            )
        ]

    def prefetch(self, actor_id: str, message: str) -> List[RecallResult]:
        results: List[RecallResult] = []
        for query in self.build_recall_queries(actor_id, message):
            for provider in self._providers.values():
                results.extend(provider.prefetch(query))
        return results

    def prefetch_context(self, actor_id: str, message: str) -> str:
        return build_recall_context_block(self.prefetch(actor_id, message))

    def sync_turn(self, actor_id: str, user_content: str, assistant_content: str) -> None:
        bundle = self.namespaces_for(actor_id)
        for provider in self._providers.values():
            provider.sync_turn(actor_id, user_content, assistant_content, bundle)

    def plan_session_consolidation(
        self,
        actor_id: str,
        messages: Iterable[dict],
    ) -> List[ConsolidationWrite]:
        bundle = self.namespaces_for(actor_id)
        message_list = list(messages)
        allowed_namespaces = {
            bundle.private_namespace.key: bundle.private_namespace.scope,
            bundle.org_shared_namespace.key: bundle.org_shared_namespace.scope,
            bundle.audit_namespace.key: bundle.audit_namespace.scope,
        }
        writes: List[ConsolidationWrite] = []
        for provider in self._providers.values():
            consolidate_session = getattr(provider, "consolidate_session", None)
            if not callable(consolidate_session):
                continue
            provider_writes = cast(
                Iterable[ConsolidationWrite],
                consolidate_session(actor_id, message_list, bundle),
            )
            for write in provider_writes:
                expected_scope = allowed_namespaces.get(write.namespace)
                if expected_scope is None:
                    raise ValueError(
                        "Consolidation target must stay inside the actor bundle: "
                        f"{write.namespace}"
                    )
                if write.scope != expected_scope:
                    raise ValueError(
                        "Consolidation scope mismatch for namespace "
                        f"{write.namespace}: expected {expected_scope}, got {write.scope}."
                    )
                writes.append(write)
        return writes

    def session_end(self, actor_id: str, messages: Iterable[dict]) -> None:
        bundle = self.namespaces_for(actor_id)
        message_list = list(messages)
        for provider in self._providers.values():
            provider.on_session_end(actor_id, message_list, bundle)
