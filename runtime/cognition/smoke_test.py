from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.contracts.provider_contract import (
    CognitionProvider,
    MemoryScope,
    NamespaceBundle,
    RecallQuery,
    RecallResult,
)
from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
CHIEF_PRODUCT_OFFICER_ID = "chief-product-officer"
CHIEF_OF_STAFF_PRIVATE_NAMESPACE = f"employee/{CHIEF_OF_STAFF_ID}"
CHIEF_PRODUCT_OFFICER_PRIVATE_NAMESPACE = f"employee/{CHIEF_PRODUCT_OFFICER_ID}"
USER_CONTENT = "请收口本轮 shadow-test"
ASSISTANT_CONTENT = "已整理完成"


class RecordingProvider(CognitionProvider):
    name = "recording"

    def __init__(self) -> None:
        self.prefetch_queries: list[RecallQuery] = []
        self.synced_turns: list[tuple[str, str, str, NamespaceBundle]] = []
        self.session_end_calls: list[tuple[str, Sequence[Mapping[str, Any]], NamespaceBundle]] = []

    def scopes_supported(self) -> Iterable[MemoryScope]:
        return (
            MemoryScope.EMPLOYEE_PRIVATE,
            MemoryScope.ORG_SHARED,
            MemoryScope.AUDIT,
        )

    def system_prompt_block(self, actor_id: str) -> str:
        return f"recording provider ready for {actor_id}"

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        self.prefetch_queries.append(query)
        for namespace in query.namespaces:
            yield RecallResult(
                provider_name=self.name,
                namespace=namespace,
                content=f"prefetched:{query.actor_id}:{namespace}",
                score=1.0,
            )

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        self.synced_turns.append(
            (actor_id, user_content, assistant_content, namespace_bundle)
        )

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, Any]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        self.session_end_calls.append((actor_id, messages, namespace_bundle))


class MetaCognitionKernelSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel = MetaCognitionKernel()
        self.provider = RecordingProvider()
        self.kernel.register_provider(self.provider)
        self.kernel.register_actor(
            actor_id=CHIEF_OF_STAFF_ID,
            role_name="ChiefOfStaff",
            display_name="小贾",
        )
        self.kernel.register_actor(
            actor_id=CHIEF_PRODUCT_OFFICER_ID,
            role_name="ChiefProductOfficer",
            display_name="CPO",
        )

    def test_namespace_policy_keeps_private_and_shared_boundaries(self) -> None:
        chief_of_staff = self.kernel.namespaces_for(CHIEF_OF_STAFF_ID)
        chief_product_officer = self.kernel.namespaces_for(CHIEF_PRODUCT_OFFICER_ID)

        self.assertEqual(chief_of_staff.private_namespace.key, CHIEF_OF_STAFF_PRIVATE_NAMESPACE)
        self.assertEqual(
            chief_product_officer.private_namespace.key,
            CHIEF_PRODUCT_OFFICER_PRIVATE_NAMESPACE,
        )
        self.assertNotEqual(
            chief_of_staff.private_namespace.key,
            chief_product_officer.private_namespace.key,
        )
        self.assertEqual(
            chief_of_staff.org_shared_namespace.key,
            chief_product_officer.org_shared_namespace.key,
        )
        self.assertEqual(
            chief_of_staff.audit_namespace.key,
            chief_product_officer.audit_namespace.key,
        )

    def test_prefetch_queries_private_and_org_shared_namespaces(self) -> None:
        results = self.kernel.prefetch(
            actor_id=CHIEF_OF_STAFF_ID,
            message="同步本轮会议结论",
        )

        self.assertEqual(len(self.provider.prefetch_queries), 1)
        query = self.provider.prefetch_queries[0]
        self.assertEqual(query.actor_id, CHIEF_OF_STAFF_ID)
        self.assertEqual(query.namespaces, (CHIEF_OF_STAFF_PRIVATE_NAMESPACE, "org/shared"))
        self.assertEqual(
            [result.namespace for result in results],
            [CHIEF_OF_STAFF_PRIVATE_NAMESPACE, "org/shared"],
        )

    def test_sync_turn_and_session_end_share_same_bundle(self) -> None:
        self.kernel.sync_turn(
            actor_id=CHIEF_OF_STAFF_ID,
            user_content=USER_CONTENT,
            assistant_content=ASSISTANT_CONTENT,
        )
        messages = [
            {"role": "user", "content": USER_CONTENT},
            {"role": "assistant", "content": ASSISTANT_CONTENT},
        ]
        self.kernel.session_end(CHIEF_OF_STAFF_ID, messages)

        self.assertEqual(len(self.provider.synced_turns), 1)
        self.assertEqual(len(self.provider.session_end_calls), 1)
        sync_actor_id, user_content, assistant_content, sync_bundle = self.provider.synced_turns[0]
        end_actor_id, end_messages, end_bundle = self.provider.session_end_calls[0]
        self.assertEqual(sync_actor_id, CHIEF_OF_STAFF_ID)
        self.assertEqual(end_actor_id, CHIEF_OF_STAFF_ID)
        self.assertEqual(user_content, USER_CONTENT)
        self.assertEqual(assistant_content, ASSISTANT_CONTENT)
        self.assertEqual(end_messages, messages)
        self.assertEqual(sync_bundle.private_namespace.key, end_bundle.private_namespace.key)
        self.assertEqual(sync_bundle.org_shared_namespace.key, end_bundle.org_shared_namespace.key)
        self.assertEqual(sync_bundle.audit_namespace.key, end_bundle.audit_namespace.key)


if __name__ == "__main__":
    unittest.main(verbosity=2)