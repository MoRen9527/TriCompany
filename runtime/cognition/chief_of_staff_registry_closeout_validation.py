from __future__ import annotations

import json
import sys
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_wiki_paths import (
    chief_of_staff_audit_root,
    chief_of_staff_schedule_root,
)
from runtime.cognition.dispatch.task_resolver import resolve_schedule_task
from runtime.cognition.kernel.schedule_registry import ScheduleRegistry


class ChiefOfStaffRegistryCloseoutValidationTest(unittest.TestCase):
    def test_registry_closeout_schedule_dispatches_payload_and_writes_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            closeout_path = self._seed_closeout_source(workspace_root)
            server, thread, base_url = _start_dispatch_server()
            self.addCleanup(_stop_dispatch_server, server, thread)
            self._seed_schedule(
                workspace_root,
                source_path=closeout_path,
                delivery_base_url=base_url,
            )

            registry = ScheduleRegistry(chief_of_staff_schedule_root(workspace_root))
            schedule = registry.list_specs()[0]
            result = resolve_schedule_task(
                schedule,
                workspace_root=str(workspace_root),
            ).execute()

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["deliveryStatus"], "delivered")

            audit_root = chief_of_staff_audit_root(workspace_root)
            audit_records = sorted(audit_root.glob("registry-closeout-*.json"))
            self.assertEqual(len(audit_records), 1)

            audit_payload = json.loads(audit_records[0].read_text(encoding="utf-8"))
            self.assertEqual(audit_payload["objectType"], "CENTRAL_REGISTRY_CLOSEOUT")
            self.assertEqual(
                audit_payload["closeout"]["objectType"],
                "CENTRAL_REGISTRY_CLOSEOUT",
            )
            self.assertEqual(audit_payload["registryFindingCount"], 2)
            self.assertEqual(audit_payload["delivery"]["deliveryStatus"], "delivered")
            self.assertEqual(audit_payload["sourcePath"], closeout_path.as_posix())

            requests = list(getattr(server, "received", []))
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]["path"], "/closeout")

            request_payload = json.loads(requests[0]["body"])
            self.assertEqual(request_payload["objectType"], "CENTRAL_REGISTRY_CLOSEOUT")
            self.assertEqual(
                request_payload["closeoutSubject"],
                "PC 端软件层与 TriLC closeout",
            )
            self.assertEqual(
                request_payload["closeout"]["payload"]["closeoutDecision"],
                "writeback-approved",
            )

    def _seed_closeout_source(self, workspace_root: Path) -> Path:
        closeout_root = workspace_root / "docs" / "workflow" / "handoff-templates"
        closeout_root.mkdir(parents=True, exist_ok=True)
        closeout_path = closeout_root / "central-registry-closeout.example.json"
        closeout_path.write_text(
            json.dumps(
                {
                    "objectType": "CENTRAL_REGISTRY_CLOSEOUT",
                    "objectId": "CRC-20260423-001",
                    "title": "PC 端软件层与 TriLC closeout",
                    "status": "approved",
                    "ownerRole": "CEOChiefOfStaff",
                    "summary": "closeout validation sample",
                    "payload": {
                        "closeoutSubject": "PC 端软件层与 TriLC closeout",
                        "scopeDecision": {
                            "route": "parallel-registry-closeout",
                            "modules": ["Tripilot", "Tride", "vscodium", "TriLC"],
                        },
                        "registryFindings": [
                            {
                                "registry": "TripilotProductRegistry",
                                "summary": "桌面入口承接用户触达",
                            },
                            {
                                "registry": "TriLCCodeRegistry",
                                "summary": "本地控制器保持 runtime / planner 边界",
                            },
                        ],
                        "closeoutDecision": "writeback-approved",
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return closeout_path

    def _seed_schedule(
        self,
        workspace_root: Path,
        *,
        source_path: Path,
        delivery_base_url: str,
    ) -> None:
        schedule_root = chief_of_staff_schedule_root(workspace_root)
        schedule_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "objectType": "SCHEDULE_SPEC",
            "objectId": "chief-of-staff-central-registry-closeout",
            "title": "总助中央收口桥接",
            "status": "approved",
            "priority": "high",
            "ownerRole": "CEOChiefOfStaff",
            "createdAt": "2026-04-23T09:00:00+08:00",
            "updatedAt": "2026-04-23T09:00:00+08:00",
            "timebox": {"scope": "weekly", "label": "closeout validation"},
            "summary": "dispatch central registry closeout payload",
            "relatedModules": ["TriCompany", "TriMetaverse"],
            "evidence": [
                {
                    "source": "docs/workflow/central-registry-closeout.schema.json",
                    "kind": "document",
                }
            ],
            "nextActions": [
                {"owner": "CEOChiefOfStaff", "action": "dispatch registry closeout"}
            ],
            "workflowRefs": [
                {"phase": "DESIGNING", "artifact": "central-registry-closeout"}
            ],
            "payload": {
                "targetType": "registry-closeout",
                "targetRef": "chief-of-staff-central-registry-closeout",
                "targetVersion": "v0.1",
                "scheduleType": "cron",
                "scheduleExpression": "* * * * *",
                "executionHost": "copilot-chat",
                "approvalGate": "manual-only",
                "failurePolicy": "freeze",
                "auditRequired": True,
                "enabled": True,
                "concurrencyPolicy": "forbid-overlap",
                "stopConditions": ["manual-stop"],
                "deliveryChannel": "webhook",
                "deliveryTarget": f"{delivery_base_url}/closeout",
                "note": "registry closeout validation",
                "taskConfig": {
                    "sourcePath": source_path.as_posix(),
                },
            },
            "metadata": {"validation": True},
        }
        (
            schedule_root / "01-chief-of-staff-central-registry-closeout.json"
        ).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


class _DispatchRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length") or "0")
        raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        requests = getattr(self.server, "received", [])
        requests.append({
            "path": self.path,
            "body": raw_body,
        })
        setattr(self.server, "received", requests)
        self.send_response(202)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(b'{"status":"accepted"}')

    def log_message(self, format: str, *args: object) -> None:
        return None


def _start_dispatch_server() -> tuple[ThreadingHTTPServer, Thread, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DispatchRequestHandler)
    setattr(server, "received", [])
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = server.server_address
    host = str(address[0])
    port = int(address[1])
    return server, thread, f"http://{host}:{port}"


def _stop_dispatch_server(server: ThreadingHTTPServer, thread: Thread) -> None:
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)