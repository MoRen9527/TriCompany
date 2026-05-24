from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.external_adapter import ExternalCognitionAdapter
from runtime.cognition.providers.org_shared import OrgSharedProvider
from runtime.cognition.providers.supermemory_backend import (
    SUPERMEMORY_ADD_PATH,
    SUPERMEMORY_SEARCH_PATH,
    SupermemoryBackendConfig,
    SupermemoryExternalBackend,
)


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
API_KEY = "sm_test_key"
USER_CONTENT = "请同步这轮经营结论到 Supermemory"
ASSISTANT_CONTENT = "已同步到 Supermemory"
SEARCH_QUERY = "请召回当前经营结论"
PRIVATE_NAMESPACE = f"employee/{CHIEF_OF_STAFF_ID}"
PRIVATE_CONTAINER_TAG = f"employee:{CHIEF_OF_STAFF_ID}"
ORG_SHARED_CONTAINER_TAG = "org:shared"
AUDIT_CONTAINER_TAG = "org:audit"


class SupermemoryTestServer:
    def __init__(
        self,
        *,
        search_statuses: list[int] | None = None,
        search_payloads: list[dict] | None = None,
        document_statuses: list[int] | None = None,
        document_payloads: list[dict] | None = None,
    ) -> None:
        self.search_statuses = list(search_statuses or [200])
        self.search_payloads = list(search_payloads or [{"results": []}])
        self.document_statuses = list(document_statuses or [200, 200, 200])
        self.document_payloads = list(document_payloads or [{"id": "doc_1", "status": "ok"}] * 3)
        self.requests: list[dict] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "SupermemoryTestServer":
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length).decode("utf-8")
                body = json.loads(raw_body) if raw_body else {}
                outer.requests.append(
                    {"path": self.path, "headers": dict(self.headers.items()), "body": body}
                )

                if self.path == SUPERMEMORY_SEARCH_PATH:
                    status = outer.search_statuses.pop(0) if outer.search_statuses else 200
                    payload = outer.search_payloads.pop(0) if outer.search_payloads else {"results": []}
                elif self.path == SUPERMEMORY_ADD_PATH:
                    status = outer.document_statuses.pop(0) if outer.document_statuses else 200
                    payload = outer.document_payloads.pop(0) if outer.document_payloads else {"id": "doc_fallback", "status": "ok"}
                else:
                    status = 404
                    payload = {"message": "not found"}

                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(payload).encode("utf-8"))
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

            def log_message(self, format: str, *args: object) -> None:
                return None

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise RuntimeError("Server is not running")
        host = self._server.server_address[0]
        port = self._server.server_address[1]
        return f"http://{host}:{port}"


class SupermemoryValidationTest(unittest.TestCase):
    def test_supermemory_backend_maps_vendor_payloads_for_add_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with SupermemoryTestServer(
                search_payloads=[
                    {
                        "results": [
                            {
                                "id": "mem_1",
                                "memory": "用户偏好函数式模式",
                                "similarity": 0.92,
                                "metadata": {"source": "memory"},
                                "updatedAt": "2026-04-17T00:00:00.000Z",
                                "version": 1,
                            }
                        ],
                        "timing": 12,
                        "total": 1,
                    },
                    {
                        "results": [
                            {
                                "id": "chunk_1",
                                "chunk": "组织共享结论：本轮先做验证基线",
                                "similarity": 0.88,
                                "metadata": {"source": "doc"},
                                "updatedAt": "2026-04-17T00:00:00.000Z",
                                "version": 1,
                            }
                        ],
                        "timing": 15,
                        "total": 1,
                    },
                ]
            ) as server:
                backend = SupermemoryExternalBackend(
                    SupermemoryBackendConfig(
                        api_key=API_KEY,
                        base_url=server.base_url,
                        timeout_seconds=1.0,
                        max_retries=0,
                        metadata={"workspace": "tricompany"},
                    )
                )
                kernel = MetaCognitionKernel()
                kernel.register_actor(
                    actor_id=CHIEF_OF_STAFF_ID,
                    role_name="ChiefOfStaff",
                    display_name="小贾",
                )
                kernel.register_provider(BuiltinMarkdownProvider(temp_dir))
                kernel.register_provider(OrgSharedProvider(temp_dir))
                kernel.register_provider(ExternalCognitionAdapter("supermemory", backend))

                kernel.sync_turn(CHIEF_OF_STAFF_ID, USER_CONTENT, ASSISTANT_CONTENT)
                kernel.session_end(
                    CHIEF_OF_STAFF_ID,
                    [
                        {"role": "user", "content": USER_CONTENT},
                        {"role": "assistant", "content": ASSISTANT_CONTENT},
                    ],
                )
                context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, SEARCH_QUERY)

                self.assertIn("[external-supermemory::employee/ceo-chief-of-staff]", context)
                self.assertIn("[external-supermemory::org/shared]", context)
                self.assertIn("用户偏好函数式模式", context)
                self.assertIn("组织共享结论：本轮先做验证基线", context)

                document_requests = [item for item in server.requests if item["path"] == SUPERMEMORY_ADD_PATH]
                search_requests = [item for item in server.requests if item["path"] == SUPERMEMORY_SEARCH_PATH]
                self.assertEqual(len(document_requests), 3)
                self.assertEqual(len(search_requests), 2)
                self.assertEqual(
                    document_requests[0]["headers"].get("Authorization"),
                    f"Bearer {API_KEY}",
                )
                self.assertEqual(document_requests[0]["body"]["containerTag"], PRIVATE_CONTAINER_TAG)
                self.assertEqual(document_requests[0]["body"]["taskType"], "memory")
                self.assertEqual(document_requests[1]["body"]["containerTag"], ORG_SHARED_CONTAINER_TAG)
                self.assertEqual(document_requests[2]["body"]["containerTag"], AUDIT_CONTAINER_TAG)
                self.assertEqual(document_requests[0]["body"]["metadata"]["namespace"], PRIVATE_NAMESPACE)
                self.assertEqual(document_requests[0]["body"]["metadata"]["workspace"], "tricompany")
                self.assertEqual(search_requests[0]["body"]["containerTag"], PRIVATE_CONTAINER_TAG)
                self.assertEqual(search_requests[0]["body"]["q"], SEARCH_QUERY)
                self.assertEqual(search_requests[1]["body"]["containerTag"], ORG_SHARED_CONTAINER_TAG)

    def test_supermemory_backend_retries_rate_limit_and_parses_error_body(self) -> None:
        with SupermemoryTestServer(
            search_statuses=[429, 200, 200],
            search_payloads=[
                {"message": "rate limit exceeded"},
                {"results": [], "timing": 9, "total": 0},
                {"results": [], "timing": 7, "total": 0},
            ],
        ) as server:
            backend = SupermemoryExternalBackend(
                SupermemoryBackendConfig(
                    api_key=API_KEY,
                    base_url=server.base_url,
                    timeout_seconds=1.0,
                    max_retries=1,
                    backoff_seconds=(0.0,),
                )
            )
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            query = kernel.build_recall_queries(CHIEF_OF_STAFF_ID, SEARCH_QUERY)[0]

            results = list(backend.prefetch(query))

            self.assertEqual(results, [])
            search_requests = [item for item in server.requests if item["path"] == SUPERMEMORY_SEARCH_PATH]
            self.assertEqual(len(search_requests), 3)
            self.assertEqual(search_requests[0]["body"]["containerTag"], PRIVATE_CONTAINER_TAG)
            self.assertEqual(search_requests[1]["body"]["containerTag"], PRIVATE_CONTAINER_TAG)
            self.assertEqual(search_requests[2]["body"]["containerTag"], ORG_SHARED_CONTAINER_TAG)

    def test_supermemory_backend_raises_on_non_retryable_vendor_error(self) -> None:
        with SupermemoryTestServer(
            search_statuses=[401],
            search_payloads=[{"error": {"message": "invalid api key"}}],
        ) as server:
            backend = SupermemoryExternalBackend(
                SupermemoryBackendConfig(
                    api_key=API_KEY,
                    base_url=server.base_url,
                    timeout_seconds=1.0,
                    max_retries=2,
                    backoff_seconds=(0.0,),
                )
            )
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            query = kernel.build_recall_queries(CHIEF_OF_STAFF_ID, SEARCH_QUERY)[0]

            with self.assertRaises(RuntimeError) as error_context:
                list(backend.prefetch(query))

            self.assertIn("status 401", str(error_context.exception))
            self.assertIn("invalid api key", str(error_context.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)