from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Iterable, Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.contracts.provider_contract import NamespaceBundle, RecallQuery, RecallResult
from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.external_adapter import ExternalCognitionAdapter, ExternalCognitionBackend
from runtime.cognition.providers.org_shared import OrgSharedProvider


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
USER_CONTENT = "请把本轮经营判断同步到外部认知后端"
ASSISTANT_CONTENT = "已同步到模拟外部认知后端"
REMOTE_PRIVATE_CONTENT = "外部后端保存的私域经营结论"
REMOTE_SHARED_CONTENT = "外部后端保存的组织共享结论"
ROGUE_NAMESPACE = "employee/rogue-actor"
ROGUE_CONTENT = "不应被当前 actor 召回的越界内容"


class RecordingExternalBackend(ExternalCognitionBackend):
    def __init__(self) -> None:
        self._entries: dict[str, list[str]] = {}
        self.synced_turns: list[str] = []
        self.session_end_calls: list[str] = []

    def add_entry(self, namespace: str, content: str) -> None:
        self._entries.setdefault(namespace, []).append(content)

    def read_namespace(self, namespace: str) -> str:
        return "\n".join(self._entries.get(namespace, []))

    def prefetch(self, query: RecallQuery) -> Iterable[RecallResult]:
        for namespace, items in self._entries.items():
            if not items:
                continue
            yield RecallResult(
                provider_name="backend-raw",
                namespace=namespace,
                content="\n".join(items),
                score=0.9 if namespace in query.namespaces else 0.1,
            )

    def sync_turn(
        self,
        actor_id: str,
        user_content: str,
        assistant_content: str,
        namespace_bundle: NamespaceBundle,
    ) -> None:
        self.synced_turns.append(actor_id)
        self.add_entry(
            namespace_bundle.private_namespace.key,
            (
                f"- actor: {actor_id}\n"
                f"- external-user: {user_content}\n"
                f"- external-assistant: {assistant_content}"
            ),
        )

    def on_session_end(
        self,
        actor_id: str,
        messages: Sequence[Mapping[str, str]],
        namespace_bundle: NamespaceBundle,
    ) -> None:
        self.session_end_calls.append(actor_id)
        assistant_messages = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
        user_messages = [m.get("content", "") for m in messages if m.get("role") == "user"]
        summary = ""
        if assistant_messages:
            summary = assistant_messages[-1]
        elif user_messages:
            summary = user_messages[-1]
        self.add_entry(
            namespace_bundle.org_shared_namespace.key,
            f"- actor: {actor_id}\n- external-shared-summary: {summary}",
        )


class ExternalAdapterValidationTest(unittest.TestCase):
    def test_external_adapter_filters_results_to_query_namespaces(self) -> None:
        backend = RecordingExternalBackend()
        kernel = MetaCognitionKernel()
        kernel.register_actor(
            actor_id=CHIEF_OF_STAFF_ID,
            role_name="ChiefOfStaff",
            display_name="小贾",
        )
        bundle = kernel.namespaces_for(CHIEF_OF_STAFF_ID)
        backend.add_entry(bundle.private_namespace.key, REMOTE_PRIVATE_CONTENT)
        backend.add_entry(bundle.org_shared_namespace.key, REMOTE_SHARED_CONTENT)
        backend.add_entry(ROGUE_NAMESPACE, ROGUE_CONTENT)
        kernel.register_provider(ExternalCognitionAdapter("honcho", backend))

        context = kernel.prefetch_context(
            CHIEF_OF_STAFF_ID,
            "请召回当前 actor 在外部后端中的经营结论",
        )

        self.assertIn("[external-honcho::employee/ceo-chief-of-staff]", context)
        self.assertIn("[external-honcho::org/shared]", context)
        self.assertIn(REMOTE_PRIVATE_CONTENT, context)
        self.assertIn(REMOTE_SHARED_CONTENT, context)
        self.assertNotIn(ROGUE_NAMESPACE, context)
        self.assertNotIn(ROGUE_CONTENT, context)

    def test_external_adapter_coexists_with_builtin_providers_and_supports_recall(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = RecordingExternalBackend()
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            kernel.register_provider(BuiltinMarkdownProvider(temp_dir))
            kernel.register_provider(OrgSharedProvider(temp_dir))
            kernel.register_provider(ExternalCognitionAdapter("honcho", backend))

            kernel.sync_turn(
                actor_id=CHIEF_OF_STAFF_ID,
                user_content=USER_CONTENT,
                assistant_content=ASSISTANT_CONTENT,
            )
            messages = [
                {"role": "user", "content": USER_CONTENT},
                {"role": "assistant", "content": ASSISTANT_CONTENT},
            ]
            kernel.session_end(CHIEF_OF_STAFF_ID, messages)

            root = Path(temp_dir)
            self.assertTrue((root / "employee" / f"{CHIEF_OF_STAFF_ID}.md").exists())
            self.assertTrue((root / "org" / "shared.md").exists())
            self.assertTrue((root / "org" / "audit.md").exists())
            self.assertEqual(backend.synced_turns, [CHIEF_OF_STAFF_ID])
            self.assertEqual(backend.session_end_calls, [CHIEF_OF_STAFF_ID])
            self.assertIn(USER_CONTENT, backend.read_namespace(f"employee/{CHIEF_OF_STAFF_ID}"))
            self.assertIn(ASSISTANT_CONTENT, backend.read_namespace("org/shared"))

            reloaded_kernel = MetaCognitionKernel()
            reloaded_kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            reloaded_kernel.register_provider(BuiltinMarkdownProvider(temp_dir))
            reloaded_kernel.register_provider(OrgSharedProvider(temp_dir))
            reloaded_kernel.register_provider(ExternalCognitionAdapter("honcho", backend))

            context = reloaded_kernel.prefetch_context(
                CHIEF_OF_STAFF_ID,
                "请同时召回本地与外部后端的经营结论",
            )

            self.assertIn("[builtin-markdown::employee/ceo-chief-of-staff]", context)
            self.assertIn("[org-shared::org/shared]", context)
            self.assertIn("[external-honcho::employee/ceo-chief-of-staff]", context)
            self.assertIn("[external-honcho::org/shared]", context)
            self.assertIn(USER_CONTENT, context)
            self.assertIn(ASSISTANT_CONTENT, context)


if __name__ == "__main__":
    unittest.main(verbosity=2)