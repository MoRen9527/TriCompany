from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.external_adapter import ExternalCognitionAdapter
from runtime.cognition.providers.org_shared import OrgSharedProvider
from runtime.cognition.providers.supermemory_sdk_backend import (
    SupermemorySdkBackendConfig,
    SupermemorySdkExternalBackend,
)


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
USER_CONTENT = "请把这轮经营记录同步到 SDK provider"
ASSISTANT_CONTENT = "已通过 SDK provider 完成同步"
SEARCH_QUERY = "请召回当前经营结论"
PRIVATE_NAMESPACE = f"employee/{CHIEF_OF_STAFF_ID}"
PRIVATE_CONTAINER_TAG = f"employee:{CHIEF_OF_STAFF_ID}"
ORG_SHARED_CONTAINER_TAG = "org:shared"
AUDIT_CONTAINER_TAG = "org:audit"


class FakeDocumentsClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        return {"id": f"doc_{len(self.calls)}", "status": "ok"}


class FakeSearchDocumentsClient:
    def __init__(self, responses: list[Mapping[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        if self._responses:
            return self._responses.pop(0)
        return {"results": []}


class FakeSearchClient:
    def __init__(self, responses: list[Mapping[str, Any]]) -> None:
        self.documents = FakeSearchDocumentsClient(responses)


class FakeSupermemoryClient:
    def __init__(self, responses: list[Mapping[str, Any]]) -> None:
        self.documents = FakeDocumentsClient()
        self.search = FakeSearchClient(responses)


class SupermemorySdkValidationTest(unittest.TestCase):
    def test_supermemory_sdk_backend_maps_sdk_calls_for_add_and_search(self) -> None:
        client = FakeSupermemoryClient(
            [
                {"results": [{"memory": "私域结论：现金流优先", "similarity": 0.91}]},
                {"results": [{"chunk": "共享结论：先做 SDK seam 验证", "similarity": 0.84}]},
            ]
        )
        backend = SupermemorySdkExternalBackend(
            client,
            SupermemorySdkBackendConfig(metadata={"workspace": "tricompany"}),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            kernel.register_provider(BuiltinMarkdownProvider(temp_dir))
            kernel.register_provider(OrgSharedProvider(temp_dir))
            kernel.register_provider(ExternalCognitionAdapter("supermemory-sdk", backend))

            kernel.sync_turn(CHIEF_OF_STAFF_ID, USER_CONTENT, ASSISTANT_CONTENT)
            kernel.session_end(
                CHIEF_OF_STAFF_ID,
                [
                    {"role": "user", "content": USER_CONTENT},
                    {"role": "assistant", "content": ASSISTANT_CONTENT},
                ],
            )
            context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, SEARCH_QUERY)

        self.assertIn("[external-supermemory-sdk::employee/ceo-chief-of-staff]", context)
        self.assertIn("[external-supermemory-sdk::org/shared]", context)
        self.assertIn("私域结论：现金流优先", context)
        self.assertIn("共享结论：先做 SDK seam 验证", context)

        self.assertEqual(len(client.documents.calls), 3)
        self.assertEqual(client.documents.calls[0]["containerTag"], PRIVATE_CONTAINER_TAG)
        self.assertEqual(client.documents.calls[1]["containerTag"], ORG_SHARED_CONTAINER_TAG)
        self.assertEqual(client.documents.calls[2]["containerTag"], AUDIT_CONTAINER_TAG)
        self.assertEqual(client.documents.calls[0]["metadata"]["namespace"], PRIVATE_NAMESPACE)
        self.assertEqual(client.documents.calls[0]["metadata"]["workspace"], "tricompany")

        search_calls = client.search.documents.calls
        self.assertEqual(len(search_calls), 2)
        self.assertEqual(search_calls[0]["containerTag"], PRIVATE_CONTAINER_TAG)
        self.assertEqual(search_calls[0]["q"], SEARCH_QUERY)
        self.assertEqual(search_calls[1]["containerTag"], ORG_SHARED_CONTAINER_TAG)
        self.assertEqual(search_calls[0]["searchMode"], "hybrid")

    def test_supermemory_sdk_backend_rejects_oversized_container_tag(self) -> None:
        client = FakeSupermemoryClient([])
        backend = SupermemorySdkExternalBackend(client)

        with self.assertRaises(ValueError) as error_context:
            backend.namespace_to_container_tag("employee/" + "x" * 110)

        self.assertIn("containerTag exceeds 100 chars", str(error_context.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)