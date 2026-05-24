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
from runtime.cognition.providers.external_http_backend import (
    HttpExternalBackendConfig,
    HttpExternalCognitionBackend,
)
from runtime.cognition.providers.org_shared import OrgSharedProvider


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
API_KEY = "secret-token"
USER_CONTENT = "请把经营结论同步到远端 cognition API"
ASSISTANT_CONTENT = "已同步到 HTTP 外部后端"
REMOTE_PRIVATE_CONTENT = "HTTP 外部后端返回的私域经营记录"
REMOTE_SHARED_CONTENT = "HTTP 外部后端返回的共享经营记录"
PREFETCH_PATH = "/prefetch"
SYNC_TURN_PATH = "/sync-turn"
SESSION_END_PATH = "/session-end"
ORG_SHARED_NAMESPACE = "org/shared"


class LocalBackendServer:
    def __init__(
        self,
        *,
        prefetch_status: int = 200,
        prefetch_results: list[dict] | None = None,
        prefetch_delay: float = 0.0,
    ) -> None:
        self.prefetch_status = prefetch_status
        self.prefetch_results = prefetch_results or []
        self.prefetch_delay = prefetch_delay
        self.requests: list[dict] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "LocalBackendServer":
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length).decode("utf-8")
                body = json.loads(raw_body) if raw_body else {}
                outer.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers.items()),
                        "body": body,
                    }
                )

                if self.path == PREFETCH_PATH and outer.prefetch_delay > 0:
                    time.sleep(outer.prefetch_delay)

                if self.path == PREFETCH_PATH:
                    self.send_response(outer.prefetch_status)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    payload = (
                        {"results": outer.prefetch_results}
                        if outer.prefetch_status == 200
                        else {"error": "unauthorized"}
                    )
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    payload = {"ok": True}

                try:
                    self.wfile.write(json.dumps(payload).encode("utf-8"))
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
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
        host, port = self._server.server_address
        return f"http://{host}:{port}"


class HttpExternalBackendValidationTest(unittest.TestCase):
    def test_http_backend_sends_auth_headers_and_coexists_with_builtin_providers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with LocalBackendServer(
                prefetch_results=[
                    {
                        "namespace": f"employee/{CHIEF_OF_STAFF_ID}",
                        "content": REMOTE_PRIVATE_CONTENT,
                        "score": 0.95,
                    },
                    {
                        "namespace": ORG_SHARED_NAMESPACE,
                        "content": REMOTE_SHARED_CONTENT,
                        "score": 0.9,
                    },
                ]
            ) as server:
                backend = HttpExternalCognitionBackend(
                    HttpExternalBackendConfig(
                        base_url=server.base_url,
                        api_key=API_KEY,
                        timeout_seconds=1.0,
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
                kernel.register_provider(ExternalCognitionAdapter("honcho-http", backend))

                kernel.sync_turn(
                    actor_id=CHIEF_OF_STAFF_ID,
                    user_content=USER_CONTENT,
                    assistant_content=ASSISTANT_CONTENT,
                )
                kernel.session_end(
                    CHIEF_OF_STAFF_ID,
                    [
                        {"role": "user", "content": USER_CONTENT},
                        {"role": "assistant", "content": ASSISTANT_CONTENT},
                    ],
                )
                context = kernel.prefetch_context(
                    CHIEF_OF_STAFF_ID,
                    "请同时召回本地与 HTTP 外部后端的经营结论",
                )

                self.assertIn("[external-honcho-http::employee/ceo-chief-of-staff]", context)
                self.assertIn("[external-honcho-http::org/shared]", context)
                self.assertIn(REMOTE_PRIVATE_CONTENT, context)
                self.assertIn(REMOTE_SHARED_CONTENT, context)

                sync_request = next(item for item in server.requests if item["path"] == SYNC_TURN_PATH)
                end_request = next(item for item in server.requests if item["path"] == SESSION_END_PATH)
                prefetch_request = next(item for item in server.requests if item["path"] == PREFETCH_PATH)
                self.assertEqual(sync_request["headers"].get("Authorization"), f"Bearer {API_KEY}")
                self.assertEqual(end_request["headers"].get("Authorization"), f"Bearer {API_KEY}")
                self.assertEqual(prefetch_request["headers"].get("Authorization"), f"Bearer {API_KEY}")
                self.assertEqual(sync_request["body"]["actor_id"], CHIEF_OF_STAFF_ID)
                self.assertEqual(end_request["body"]["namespace_bundle"]["org_shared_namespace"], ORG_SHARED_NAMESPACE)
                self.assertEqual(
                    prefetch_request["body"]["namespaces"],
                    [f"employee/{CHIEF_OF_STAFF_ID}", ORG_SHARED_NAMESPACE],
                )

    def test_http_backend_prefetch_raises_on_unauthorized(self) -> None:
        with LocalBackendServer(prefetch_status=401) as server:
            backend = HttpExternalCognitionBackend(
                HttpExternalBackendConfig(
                    base_url=server.base_url,
                    api_key=API_KEY,
                    timeout_seconds=1.0,
                )
            )
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            query = kernel.build_recall_queries(
                CHIEF_OF_STAFF_ID,
                "请召回当前经营结论",
            )[0]

            with self.assertRaises(RuntimeError) as error_context:
                list(backend.prefetch(query))

            self.assertIn("status 401", str(error_context.exception))
            self.assertIn(PREFETCH_PATH, str(error_context.exception))

    def test_http_backend_sync_turn_raises_on_timeout(self) -> None:
        with LocalBackendServer(prefetch_delay=0.2) as server:
            backend = HttpExternalCognitionBackend(
                HttpExternalBackendConfig(
                    base_url=server.base_url,
                    api_key=API_KEY,
                    timeout_seconds=0.05,
                )
            )
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            query = kernel.build_recall_queries(
                CHIEF_OF_STAFF_ID,
                "请召回当前经营结论",
            )[0]

            with self.assertRaises(RuntimeError) as error_context:
                list(backend.prefetch(query))

            self.assertIn(PREFETCH_PATH, str(error_context.exception))
            self.assertTrue(
                "timed out" in str(error_context.exception).lower()
                or "timeout" in str(error_context.exception).lower()
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)