from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_wiki_paths import (
    chief_of_staff_approval_report_root,
    chief_of_staff_audit_root,
    chief_of_staff_inbox_root,
    chief_of_staff_schedule_root,
    chief_of_staff_wiki_page_specs_path,
    chief_of_staff_wiki_root,
    chief_of_staff_workbench_root,
)
from runtime.cognition.runners.resident_runner import run_resident_chief_of_staff_schedules


class ChiefOfStaffScheduleStagingValidationTest(unittest.TestCase):
    def test_resident_runner_promotes_page_to_stable_and_executes_task_bus(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._seed_sources(workspace_root)
            self._seed_page_specs(workspace_root)

            server, thread, base_url = _start_dispatch_server()
            self.addCleanup(_stop_dispatch_server, server, thread)
            self._seed_schedules(workspace_root, delivery_base_url=base_url)

            ticks = iter(
                (
                    datetime(2026, 4, 21, 1, 0, tzinfo=timezone.utc).astimezone(),
                    datetime(2026, 4, 21, 1, 1, tzinfo=timezone.utc).astimezone(),
                )
            )
            summary = run_resident_chief_of_staff_schedules(
                workspace_root=str(workspace_root),
                interval_seconds=60,
                max_cycles=2,
                now_provider=lambda: next(ticks),
                sleep_fn=lambda _: None,
            )

            self.assertEqual(summary.cycle_count, 2)
            self.assertEqual(summary.total_schedule_runs, 20)

            page_text = (
                chief_of_staff_wiki_root(workspace_root)
                / "chief-of-staff-llm-wiki-semi-auto-current-state.md"
            ).read_text(encoding="utf-8")
            self.assertIn("pageStatus: stable", page_text)
            self.assertIn("approvalStatus: approved", page_text)
            self.assertIn("primaryReviewer: ChiefTechnologyOfficer", page_text)

            audit_root = chief_of_staff_audit_root(workspace_root)
            approval_records = sorted(audit_root.glob("wiki-approval-*.json"))
            approval_report_records = sorted(audit_root.glob("wiki-approval-report-*.json"))
            promotion_records = sorted(audit_root.glob("wiki-promotion-*.json"))
            recall_records = sorted(audit_root.glob("wiki-recall-checkpoint-*.json"))
            reminder_records = sorted(audit_root.glob("reminder-delivery-*.json"))
            email_records = sorted(audit_root.glob("email-delivery-*.json"))
            self.assertGreaterEqual(len(promotion_records), 2)
            self.assertGreaterEqual(len(approval_records), 2)
            self.assertGreaterEqual(len(approval_report_records), 2)
            self.assertGreaterEqual(len(recall_records), 2)
            self.assertGreaterEqual(len(reminder_records), 2)
            self.assertGreaterEqual(len(email_records), 2)

            last_recall = json.loads(recall_records[-1].read_text(encoding="utf-8"))
            self.assertEqual(last_recall["status"], "completed")
            self.assertEqual(last_recall["recallMode"], "all-pages")
            self.assertIn(
                "chief-of-staff-llm-wiki-semi-auto-current-state",
                last_recall["contextExcerpt"],
            )

            reminder_payload = json.loads(reminder_records[-1].read_text(encoding="utf-8"))
            email_payload = json.loads(email_records[-1].read_text(encoding="utf-8"))
            self.assertEqual(
                reminder_payload["delivery"]["deliveryStatus"],
                "delivered",
            )
            self.assertEqual(
                email_payload["delivery"]["deliveryStatus"],
                "delivered",
            )
            self.assertIn("治理覆盖 route", reminder_payload["message"])
            self.assertIn("预警", email_payload["subject"])
            self.assertIn("Reviewer Owner 负载", email_payload["body"])
            self.assertIn("Route 分布", email_payload["body"])

            approval_report_root = chief_of_staff_approval_report_root(workspace_root)
            self.assertTrue((approval_report_root / "snapshot.json").exists())
            self.assertTrue((approval_report_root / "summary.md").exists())
            approval_report = json.loads(
                (approval_report_root / "snapshot.json").read_text(encoding="utf-8")
            )
            approval_report_markdown = (
                approval_report_root / "summary.md"
            ).read_text(encoding="utf-8")
            self.assertIn("pendingCount", approval_report["summary"])
            self.assertIn("governance", approval_report)
            self.assertIn("reviewerOwners", approval_report["governance"])
            self.assertIn("warningCount", approval_report["summary"])
            self.assertEqual(approval_report["summary"]["closeoutScheduleCount"], 1)
            self.assertEqual(approval_report["summary"]["closeoutRenderedCount"], 1)
            self.assertIn("closeoutBridge", approval_report)
            self.assertEqual(approval_report["closeoutBridge"]["scheduleCount"], 1)
            self.assertEqual(
                approval_report["closeoutBridge"]["entries"][0]["targetType"],
                "operating-review-closeout",
            )
            self.assertEqual(
                approval_report["closeoutBridge"]["entries"][0]["latestTriggerObjectType"],
                "OPERATING_REVIEW",
            )
            self.assertEqual(
                approval_report["closeoutBridge"]["entries"][0]["latestTriggerObjectId"],
                "OR-202604-W14-001",
            )
            self.assertIn("Central Registry Closeout", approval_report_markdown)
            self.assertIn(
                "OPERATING_REVIEW / OR-202604-W14-001",
                approval_report_markdown,
            )

            requests = list(getattr(server, "received", []))
            self.assertGreaterEqual(len(requests), 4)
            self.assertTrue(any(request["path"] == "/reminder" for request in requests))
            self.assertTrue(any(request["path"] == "/email" for request in requests))

            workbench_root = chief_of_staff_workbench_root(workspace_root)
            self.assertTrue((workbench_root / "index.html").exists())
            self.assertTrue((workbench_root / "snapshot.json").exists())
            workbench_snapshot = json.loads(
                (workbench_root / "snapshot.json").read_text(encoding="utf-8")
            )
            workbench_html = (workbench_root / "index.html").read_text(encoding="utf-8")
            self.assertIn("总助知识工作台", workbench_html)
            self.assertIn("Chief Of Staff Knowledge Workbench", workbench_html)
            self.assertIn("Reviewer route", workbench_html)
            self.assertIn("即将超时", workbench_html)
            self.assertIn("SLA 超时", workbench_html)
            self.assertIn("治理态势", workbench_html)
            self.assertIn("Reviewer Lanes", workbench_html)
            self.assertIn("Central Registry Closeout", workbench_html)
            self.assertIn("最近审计", workbench_html)
            self.assertIn("knowledge/employees/ceo-chief-of-staff/wiki", workbench_html)
            self.assertEqual(workbench_snapshot["closeoutBridge"]["scheduleCount"], 1)
            self.assertEqual(
                workbench_snapshot["closeoutBridge"]["entries"][0]["targetType"],
                "operating-review-closeout",
            )
            self.assertEqual(
                workbench_snapshot["closeoutBridge"]["entries"][0]["latestTriggerObjectType"],
                "OPERATING_REVIEW",
            )
            self.assertEqual(
                workbench_snapshot["closeoutBridge"]["entries"][0]["latestTriggerObjectId"],
                "OR-202604-W14-001",
            )
            self.assertIn("OPERATING_REVIEW / OR-202604-W14-001", workbench_html)

    def _seed_operating_review_source(self, workspace_root: Path) -> None:
        review_root = workspace_root / "docs" / "workflow" / "operating-cycle-example"
        review_root.mkdir(parents=True, exist_ok=True)
        (review_root / "operating-review.sample.json").write_text(
            json.dumps(
                {
                    "objectType": "OPERATING_REVIEW",
                    "objectId": "OR-202604-W14-001",
                    "title": "resident staging validation operating review",
                    "status": "completed",
                    "ownerRole": "ChiefOperatingOfficer",
                    "summary": "staging validation operating review source",
                    "payload": {
                        "wins": [
                            "operating review can trigger central registry closeout"
                        ],
                        "corrections": [
                            "promote closeout to a formal schedule target"
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _seed_closeout_source(self, workspace_root: Path) -> None:
        closeout_root = workspace_root / "docs" / "workflow" / "handoff-templates"
        closeout_root.mkdir(parents=True, exist_ok=True)
        (
            closeout_root / "central-registry-closeout.example.json"
        ).write_text(
            json.dumps(
                {
                    "objectType": "CENTRAL_REGISTRY_CLOSEOUT",
                    "objectId": "CRC-20260423-001",
                    "title": "PC 端软件层与 TriLC closeout",
                    "status": "submitted",
                    "ownerRole": "CEOChiefOfStaff",
                    "summary": "schedule staging validation closeout source",
                    "dependsOn": ["OR-202604-W14-001"],
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

    def _seed_sources(self, workspace_root: Path) -> None:
        inbox_root = chief_of_staff_inbox_root(workspace_root)
        inbox_root.mkdir(parents=True, exist_ok=True)
        (
            inbox_root / "2026-04-21-chief-of-staff-meeting-note.md"
        ).write_text(
            "---\n"
            "sourceId: chief-of-staff-note-2026-04-21-001\n"
            "title: 总助阶段会议纪要\n"
            "sourceType: meeting-note\n"
            "topicHints:\n"
            "  - chief-of-staff\n"
            "  - llm-wiki\n"
            "trustLevel: raw\n"
            "capturedAt: 2026-04-21T09:00:00+08:00\n"
            "---\n\n"
            "- 已确认 schedule / cron staging 需要形成持续运行证据链。\n"
            "- 已确认所有 wiki 页都应进入 recall，但 stable 仍保留更高可信级别。\n"
            "- reviewing 页面进入 stable 前需要人工审批。\n",
            encoding="utf-8",
        )
        (
            inbox_root / "2026-04-21-chief-of-staff-phase-2-note.md"
        ).write_text(
            "---\n"
            "sourceId: chief-of-staff-note-2026-04-21-004\n"
            "title: 总助 phase-2 扩展记录\n"
            "sourceType: project-note\n"
            "topicHints:\n"
            "  - chief-of-staff\n"
            "  - llm-wiki\n"
            "  - workbench\n"
            "  - automation\n"
            "  - dispatcher\n"
            "trustLevel: curated\n"
            "capturedAt: 2026-04-21T09:05:00+08:00\n"
            "---\n\n"
            "- 当前已落地 resident runner、knowledge workbench 和 all-pages recall。\n"
            "- reminder / email 已准备接真实 dispatcher，不再只生成 render-only 文件。\n"
            "- reviewing 页面进入 stable 前仍要保留人工审批。\n",
            encoding="utf-8",
        )
        (
            inbox_root / "2026-04-21-chief-of-staff-scratch-note.md"
        ).write_text(
            "- 当前判断是先用两轮 scheduled refresh 作为 stable promotion 证据。\n"
            "- reviewing 到 stable 现在必须经过人工审批。\n",
            encoding="utf-8",
        )
        (inbox_root / "2026-04-21-chief-of-staff-facts.json").write_text(
            json.dumps(
                {
                    "sourceId": "chief-of-staff-note-2026-04-21-003",
                    "title": "总助阶段事实",
                    "sourceType": "json-record",
                    "topicHints": ["chief-of-staff", "facts"],
                    "trustLevel": "curated",
                    "capturedAt": "2026-04-21T09:10:00+08:00",
                    "facts": [
                        "scheduled refresh 需要至少运行两轮，才能支撑 stable promotion。",
                        "所有 wiki 页面都应参与 recall，但 stable 页面仍是更高可信级别。",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        (
            inbox_root / "2026-04-21-chief-of-staff-governance-note.md"
        ).write_text(
            "---\n"
            "sourceId: chief-of-staff-note-2026-04-21-005\n"
            "title: 总助治理推进记录\n"
            "sourceType: governance-note\n"
            "topicHints:\n"
            "  - chief-of-staff\n"
            "  - llm-wiki\n"
            "  - governance\n"
            "  - dispatcher\n"
            "  - approval-report\n"
            "trustLevel: curated\n"
            "capturedAt: 2026-04-21T09:20:00+08:00\n"
            "---\n\n"
            "- reviewing 页面已补 reviewer route、primary reviewer、approval SLA 和 approvalDueAt。\n"
            "- 当前已补 approval report，并将 overdue 状态同步进知识工作台。\n"
            "- 当前 reminder / email 已支持 webhook、email gateway 和 host dispatcher。\n",
            encoding="utf-8",
        )

    def _seed_page_specs(self, workspace_root: Path) -> None:
        chief_of_staff_wiki_root(workspace_root).mkdir(parents=True, exist_ok=True)
        chief_of_staff_wiki_page_specs_path(workspace_root).write_text(
            json.dumps(
                {
                    "pageSpecs": [
                        {
                            "specId": "chief-of-staff-current-state",
                            "pageId": "chief-of-staff-llm-wiki-current-state",
                            "title": "总助 LLM wiki 当前推进情况",
                            "pageStatus": "working",
                            "topicTags": [
                                "chief-of-staff",
                                "llm-wiki",
                                "knowledge-system",
                                "governance",
                            ],
                            "includeTopics": [
                                "chief-of-staff",
                                "llm-wiki",
                                "governance",
                            ],
                            "sourceIds": [
                                "chief-of-staff-note-2026-04-21-001",
                                "2026-04-21-chief-of-staff-scratch-note.md",
                                "chief-of-staff-note-2026-04-21-003",
                                "chief-of-staff-note-2026-04-21-005",
                            ],
                            "reviewerRoles": [
                                "ChiefOperatingOfficer",
                                "CEOChiefOfStaff",
                            ],
                            "primaryReviewer": "ChiefOperatingOfficer",
                            "approvalSlaHours": 48,
                        },
                        {
                            "specId": "chief-of-staff-semi-auto-current-state",
                            "pageId": "chief-of-staff-llm-wiki-semi-auto-current-state",
                            "title": "总助 LLM wiki 半自动整理现状页",
                            "pageStatus": "stable",
                            "topicTags": [
                                "chief-of-staff",
                                "llm-wiki",
                                "automation",
                                "dispatcher",
                            ],
                            "includeTopics": [
                                "chief-of-staff",
                                "llm-wiki",
                                "automation",
                                "dispatcher",
                            ],
                            "sourceIds": [
                                "chief-of-staff-note-2026-04-21-001",
                                "chief-of-staff-note-2026-04-21-004",
                                "chief-of-staff-note-2026-04-21-005",
                            ],
                            "reviewerRoles": [
                                "ChiefTechnologyOfficer",
                                "CEOChiefOfStaff",
                            ],
                            "primaryReviewer": "ChiefTechnologyOfficer",
                            "approvalSlaHours": 24,
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _seed_schedules(self, workspace_root: Path, *, delivery_base_url: str) -> None:
        schedule_root = chief_of_staff_schedule_root(workspace_root)
        schedule_root.mkdir(parents=True, exist_ok=True)
        self._seed_operating_review_source(workspace_root)
        self._seed_closeout_source(workspace_root)
        self._write_schedule(
            schedule_root / "01-chief-of-staff-wiki-refresh-current-state.json",
            object_id="chief-of-staff-wiki-refresh-current-state",
            title="总助 wiki batch refresh",
            target_type="wiki-refresh-batch",
            target_ref="chief-of-staff-wiki-refresh-current-state",
            task_config={
                "specIds": [
                    "chief-of-staff-current-state",
                    "chief-of-staff-semi-auto-current-state",
                ],
            },
        )
        self._write_schedule(
            schedule_root / "02-chief-of-staff-wiki-promote-current-state.json",
            object_id="chief-of-staff-wiki-promote-current-state",
            title="总助 wiki page promotion",
            target_type="wiki-promotion",
            target_ref="chief-of-staff-wiki-promote-current-state",
            task_config={
                "pageId": "chief-of-staff-llm-wiki-semi-auto-current-state",
            },
        )
        self._write_schedule(
            schedule_root / "03-chief-of-staff-wiki-approval-current-state.json",
            object_id="chief-of-staff-wiki-approval-current-state",
            title="总助 wiki manual approval",
            target_type="wiki-approval",
            target_ref="chief-of-staff-wiki-approval-current-state",
            task_config={
                "pageId": "chief-of-staff-llm-wiki-semi-auto-current-state",
                "decision": "approved",
                "reviewer": "ChiefTechnologyOfficer",
                "note": "resident runner validation approval",
            },
        )
        self._write_schedule(
            schedule_root / "04-chief-of-staff-workbench-sync.json",
            object_id="chief-of-staff-workbench-sync",
            title="总助知识工作台同步",
            target_type="wiki-workbench",
            target_ref="chief-of-staff-workbench-sync",
        )
        self._write_schedule(
            schedule_root / "05-chief-of-staff-approval-queue-reminder.json",
            object_id="chief-of-staff-approval-queue-reminder",
            title="总助审批队列提醒",
            target_type="reminder",
            target_ref="chief-of-staff-approval-queue-reminder",
            delivery_channel="webhook",
            delivery_target=f"{delivery_base_url}/reminder",
            task_config={
                "contentTemplate": "approval-queue-governance",
                "title": "总助审批队列提醒",
                "message": "检查 reviewing 页面是否仍待审批，并确认 stable promotion 阻塞是否合理。",
                "assignee": "CEOChiefOfStaff",
                "severity": "high",
            },
        )
        self._write_schedule(
            schedule_root / "06-chief-of-staff-approval-queue-email.json",
            object_id="chief-of-staff-approval-queue-email",
            title="总助审批队列邮件草稿",
            target_type="email",
            target_ref="chief-of-staff-approval-queue-email",
            delivery_channel="email-gateway",
            delivery_target=f"{delivery_base_url}/email",
            task_config={
                "contentTemplate": "approval-queue-governance",
                "to": ["ceo@tricompany.local"],
                "subject": "总助审批队列状态预警",
                "body": "请复核当前 reviewing 页面审批队列，并确认 stable promotion 的人工审批结果。",
            },
        )
        self._write_schedule(
            schedule_root / "07-chief-of-staff-approval-queue-checkpoint.json",
            object_id="chief-of-staff-approval-queue-checkpoint",
            title="总助审批队列检查点",
            target_type="checkpoint",
            target_ref="chief-of-staff-approval-queue-checkpoint",
            task_config={
                "checkpointKind": "approval-queue",
            },
        )
        self._write_schedule(
            schedule_root / "08-chief-of-staff-wiki-recall-check-current-state.json",
            object_id="chief-of-staff-wiki-recall-check-current-state",
            title="总助 wiki recall checkpoint",
            target_type="checkpoint",
            target_ref="chief-of-staff-wiki-recall-check-current-state",
            task_config={
                "checkpointKind": "wiki-recall",
                "pageId": "chief-of-staff-llm-wiki-semi-auto-current-state",
                "recallMode": "all-pages",
            },
        )
        self._write_schedule(
            schedule_root / "09-chief-of-staff-approval-report.json",
            object_id="chief-of-staff-approval-report",
            title="总助审批报表",
            target_type="wiki-approval-report",
            target_ref="chief-of-staff-approval-report",
        )
        self._write_schedule(
            schedule_root / "10-chief-of-staff-central-registry-closeout.json",
            object_id="chief-of-staff-central-registry-closeout",
            title="总助经营复盘后中央 registry 收口桥接",
            target_type="operating-review-closeout",
            target_ref="CRC-20260423-001",
            task_config={
                "operatingReviewPath": "docs/workflow/operating-cycle-example/operating-review.sample.json",
                "closeoutPath": "docs/workflow/handoff-templates/central-registry-closeout.example.json",
            },
        )

    def _write_schedule(
        self,
        path: Path,
        *,
        object_id: str,
        title: str,
        target_type: str,
        target_ref: str,
        task_config: dict[str, object] | None = None,
        delivery_channel: str = "file",
        delivery_target: str = "knowledge/employees/ceo-chief-of-staff/audit",
    ) -> None:
        payload = {
            "objectType": "SCHEDULE_SPEC",
            "objectId": object_id,
            "title": title,
            "status": "approved",
            "priority": "high",
            "ownerRole": "CEOChiefOfStaff",
            "createdAt": "2026-04-21T09:30:00+08:00",
            "updatedAt": "2026-04-21T09:30:00+08:00",
            "timebox": {"scope": "weekly", "label": "phase-1 staging"},
            "summary": "chief-of-staff schedule staging validation object",
            "relatedModules": ["TriCompany", "TriMetaverse"],
            "evidence": [
                {
                    "source": "docs/engineering/chief-of-staff-llm-wiki-priority-plan.md",
                    "kind": "document",
                }
            ],
            "nextActions": [
                {"owner": "CEOChiefOfStaff", "action": "run staging validation"}
            ],
            "workflowRefs": [
                {"phase": "DESIGNING", "artifact": "chief-of-staff-llm-wiki"}
            ],
            "payload": {
                "targetType": target_type,
                "targetRef": target_ref,
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
                "deliveryChannel": delivery_channel,
                "deliveryTarget": delivery_target,
                "note": "phase-1 chief-of-staff schedule staging",
                "taskConfig": task_config or {},
            },
            "metadata": {"validation": True},
        }
        path.write_text(
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