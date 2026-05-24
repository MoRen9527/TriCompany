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


class ChiefOfStaffOperatingReviewCloseoutValidationTest(unittest.TestCase):
    def test_operating_review_bridge_dispatches_related_closeout_and_records_trigger_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            operating_review_path = self._seed_operating_review(workspace_root)
            closeout_path = self._seed_closeout(workspace_root)

            server, thread, base_url = _start_dispatch_server()
            self.addCleanup(_stop_dispatch_server, server, thread)
            self._seed_schedule(workspace_root, delivery_base_url=base_url)

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
            self.assertEqual(audit_payload["closeoutId"], "CRC-20260423-001")
            self.assertEqual(audit_payload["triggerMode"], "scheduled")
            self.assertEqual(
                audit_payload["triggerSource"]["objectType"],
                "OPERATING_REVIEW",
            )
            self.assertEqual(
                audit_payload["triggerSource"]["objectId"],
                "OR-202604-W14-001",
            )
            self.assertEqual(
                audit_payload["triggerSource"]["sourcePath"],
                operating_review_path.as_posix(),
            )
            self.assertEqual(audit_payload["sourcePath"], closeout_path.as_posix())

            requests = list(getattr(server, "received", []))
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]["path"], "/closeout")

            request_payload = json.loads(requests[0]["body"])
            self.assertEqual(
                request_payload["triggerSource"]["objectType"],
                "OPERATING_REVIEW",
            )
            self.assertEqual(
                request_payload["triggerSource"]["objectId"],
                "OR-202604-W14-001",
            )
            self.assertEqual(
                request_payload["closeout"]["dependsOn"],
                ["OR-202604-W14-001"],
            )

    def _seed_schedule(self, workspace_root: Path, *, delivery_base_url: str) -> None:
        schedule_root = chief_of_staff_schedule_root(workspace_root)
        schedule_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "objectType": "SCHEDULE_SPEC",
            "objectId": "chief-of-staff-operating-review-closeout",
            "title": "总助经营复盘后中央收口桥接",
            "status": "approved",
            "priority": "high",
            "ownerRole": "CEOChiefOfStaff",
            "createdAt": "2026-04-23T09:00:00+08:00",
            "updatedAt": "2026-04-23T09:00:00+08:00",
            "timebox": {"scope": "weekly", "label": "review closeout validation"},
            "summary": "dispatch central registry closeout payload from an operating review object",
            "relatedModules": ["TriCompany", "TriMetaverse"],
            "evidence": [
                {
                    "source": "docs/workflow/operating-review.schema.json",
                    "kind": "document",
                }
            ],
            "nextActions": [
                {
                    "owner": "CEOChiefOfStaff",
                    "action": "dispatch operating review closeout",
                }
            ],
            "workflowRefs": [
                {"phase": "DESIGNING", "artifact": "central-registry-closeout"}
            ],
            "payload": {
                "targetType": "operating-review-closeout",
                "targetRef": "CRC-20260423-001",
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
                "note": "operating review closeout validation",
                "taskConfig": {
                    "operatingReviewPath": "docs/workflow/operating-cycle-example/operating-review.sample.json",
                    "closeoutPath": "docs/workflow/handoff-templates/central-registry-closeout.example.json",
                },
            },
            "metadata": {"validation": True},
        }
        (
            schedule_root / "01-chief-of-staff-operating-review-closeout.json"
        ).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _seed_operating_review(self, workspace_root: Path) -> Path:
        review_root = workspace_root / "docs" / "workflow" / "operating-cycle-example"
        review_root.mkdir(parents=True, exist_ok=True)
        review_path = review_root / "operating-review.sample.json"
        review_path.write_text(
            json.dumps(
                {
                    "objectType": "OPERATING_REVIEW",
                    "objectId": "OR-202604-W14-001",
                    "title": "首轮试单经营复盘单",
                    "status": "completed",
                    "priority": "medium",
                    "ownerRole": "ChiefOperatingOfficer",
                    "createdAt": "2026-04-10T18:00:00Z",
                    "updatedAt": "2026-04-10T20:00:00Z",
                    "timebox": {
                        "scope": "weekly",
                        "startAt": "2026-04-03T00:00:00Z",
                        "endAt": "2026-04-09T23:59:59Z",
                        "label": "2026-W14 样例复盘",
                    },
                    "summary": "复盘已把 PC 端软件层、TriLC 和 vscodium 上游升级口径纳入下一步中央收口议程。",
                    "relatedModules": [
                        "TriMetaverse",
                        "Tripilot",
                        "Tride",
                        "vscodium",
                        "TriLC",
                    ],
                    "dependsOn": ["OP-202604-W14-001"],
                    "evidence": [],
                    "nextActions": [
                        {
                            "owner": "CEOChiefOfStaff",
                            "action": "发起 CRC-20260423-001，正式收口 PC 端软件层、TriLC 和 vscodium 上游升级口径",
                            "dueAt": "2026-04-23T12:00:00Z",
                        }
                    ],
                    "approvals": [],
                    "workflowRefs": [
                        {
                            "relation": "summarizes",
                            "phase": "DELIVERY",
                            "runId": "run-2026-04-cycle-01",
                            "branchId": "branch-prd-ai-content-trial",
                            "prdId": "PRD-AI-CONTENT-TRIAL",
                            "phaseResultRef": "docs/runs/run-2026-04-cycle-01/branch-prd-ai-content-trial/DELIVERY.phase-result.json",
                            "note": "复盘吸收交付阶段结果",
                        }
                    ],
                    "payload": {
                        "reviewWindow": "2026-W14",
                        "targetVsActual": [
                            "已识别 PC 端软件层与 TriLC 的协同口径需要在复盘后继续收口"
                        ],
                        "wins": [
                            "复盘已把 PC 端软件层、TriLC 和 vscodium 上游升级口径纳入下一步中央收口议程"
                        ],
                        "misses": [
                            "PC 端软件层、TriLC 与 vscodium 上游升级口径仍需靠单独 closeout 样板做跨模块 fan-in"
                        ],
                        "rootCauses": [
                            "跨模块边界在经营样例链和中央收口样板之间仍需要显式桥接"
                        ],
                        "corrections": [
                            "把 CRC-20260423-001 作为本轮复盘后的跨模块事实收口 companion sample"
                        ],
                        "nextCycleInput": [
                            "继续细化 PC 端软件层默认开放能力与需额外授权的本地自动化能力边界"
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return review_path

    def _seed_closeout(self, workspace_root: Path) -> Path:
        closeout_root = workspace_root / "docs" / "workflow" / "handoff-templates"
        closeout_root.mkdir(parents=True, exist_ok=True)
        closeout_path = closeout_root / "central-registry-closeout.example.json"
        closeout_path.write_text(
            json.dumps(
                {
                    "objectType": "CENTRAL_REGISTRY_CLOSEOUT",
                    "objectId": "CRC-20260423-001",
                    "title": "中央 registry 收口单：统一 PC 端软件层 / TriLC 协同与 vscodium 上游升级口径",
                    "status": "submitted",
                    "priority": "high",
                    "ownerRole": "CEOChiefOfStaff",
                    "createdAt": "2026-04-23T09:30:00Z",
                    "updatedAt": "2026-04-23T09:30:00Z",
                    "timebox": {
                        "scope": "ad-hoc",
                        "startAt": "2026-04-23T09:30:00Z",
                        "label": "pc-local-closeout-2026-04-23",
                    },
                    "summary": "针对 PC 端软件层、TriLC 本地化任务协同以及 vscodium 上游升级口径进行一次跨模块 registry 收口。",
                    "relatedModules": [
                        "TriMetaverse",
                        "Tride",
                        "Tripilot",
                        "vscodium",
                        "TriLC",
                    ],
                    "dependsOn": ["OR-202604-W14-001"],
                    "evidence": [
                        {
                            "source": "OR-202604-W14-001",
                            "kind": "document",
                            "note": "本轮经营复盘已把 PC 端软件层、TriLC 和 vscodium 上游升级口径纳入后续收口议程",
                        }
                    ],
                    "nextActions": [],
                    "approvals": [],
                    "payload": {
                        "closeoutSubject": "统一 PC 端软件层 / TriLC 协同与 vscodium 上游升级口径",
                        "scopeDecision": {
                            "scopeStatus": "central-boundary",
                            "businessStrategyRequired": True,
                        },
                        "registryFindings": [
                            {
                                "registryId": "TripilotProductRegistry",
                                "summary": "桌面入口承接用户触达",
                            },
                            {
                                "registryId": "TriLCCodeRegistry",
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