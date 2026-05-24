from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_wiki_paths import (
    chief_of_staff_audit_root,
    chief_of_staff_inbox_root,
    chief_of_staff_wiki_page_specs_path,
    chief_of_staff_wiki_root,
)
from runtime.cognition.runners.wiki_batch_refresh_runner import run_chief_of_staff_wiki_batch_refresh
from runtime.cognition.runners.wiki_refresh_runner import run_chief_of_staff_wiki_refresh
from runtime.cognition.tasks.approval_timing import evaluate_approval_timing
from runtime.cognition.tasks.wiki_governance_summary import build_wiki_governance_summary


class ChiefOfStaffLlmWikiValidationTest(unittest.TestCase):
    def test_wiki_refresh_creates_page_and_audit_from_page_spec_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._seed_sources(workspace_root)
            self._seed_page_specs(workspace_root)

            result = run_chief_of_staff_wiki_refresh(
                page_id="chief-of-staff-llm-wiki-current-state",
                title="总助 LLM wiki 当前推进情况",
                workspace_root=str(workspace_root),
            )

            self.assertEqual(result.status, "completed")
            self.assertGreaterEqual(len(result.input_sources), 4)
            self.assertTrue(result.output_page_path.exists())
            self.assertTrue(result.audit_path.exists())

            wiki_text = result.output_page_path.read_text(encoding="utf-8")
            self.assertIn("## 摘要", wiki_text)
            self.assertIn("## 来源", wiki_text)
            self.assertIn("approvalStatus: draft", wiki_text)
            self.assertIn("primaryReviewer: ChiefOperatingOfficer", wiki_text)
            self.assertIn("chief-of-staff-note-2026-04-21-005", wiki_text)

            audit_payload = json.loads(result.audit_path.read_text(encoding="utf-8"))
            self.assertEqual(audit_payload["status"], "completed")
            self.assertEqual(audit_payload["pageSpecId"], "chief-of-staff-current-state")
            self.assertEqual(audit_payload["outputPages"], ["chief-of-staff-llm-wiki-current-state"])

    def test_batch_refresh_generates_multiple_topic_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            self._seed_sources(workspace_root)
            self._seed_page_specs(workspace_root)

            result = run_chief_of_staff_wiki_batch_refresh(workspace_root=str(workspace_root))

            self.assertEqual(result.status, "completed")
            self.assertEqual(
                set(result.output_pages),
                {
                    "chief-of-staff-llm-wiki-current-state",
                    "chief-of-staff-llm-wiki-semi-auto-current-state",
                },
            )
            batch_audit = json.loads(result.audit_path.read_text(encoding="utf-8"))
            self.assertEqual(batch_audit["status"], "completed")
            self.assertEqual(
                set(batch_audit["pageSpecIds"]),
                {
                    "chief-of-staff-current-state",
                    "chief-of-staff-semi-auto-current-state",
                },
            )
            stable_page = (chief_of_staff_wiki_root(workspace_root) / "chief-of-staff-llm-wiki-semi-auto-current-state.md").read_text(encoding="utf-8")
            self.assertIn("reviewerRoute:", stable_page)
            self.assertIn("primaryReviewer: ChiefTechnologyOfficer", stable_page)

    def test_governance_summary_marks_pending_page_as_warning_near_due(self) -> None:
        page = {
            "pageId": "warning-page",
            "title": "Warning Page",
            "pageStatus": "reviewing",
            "approvalStatus": "pending",
            "reviewerRoute": ["ChiefOperatingOfficer", "CEOChiefOfStaff"],
            "primaryReviewer": "ChiefOperatingOfficer",
            "approvalSlaHours": 48,
            "approvalDueAt": "2026-04-21T21:00:00+08:00",
        }
        page.update(
            evaluate_approval_timing(
                approval_due_at=page["approvalDueAt"],
                approval_sla_hours=page["approvalSlaHours"],
                reference_time="2026-04-21T09:00:00+08:00",
            )
        )

        summary = build_wiki_governance_summary([page])

        self.assertEqual(summary["pendingCount"], 1)
        self.assertEqual(summary["warningCount"], 1)
        self.assertEqual(summary["overdueCount"], 0)

    def _seed_sources(self, workspace_root: Path) -> None:
        inbox_root = chief_of_staff_inbox_root(workspace_root)
        wiki_root = chief_of_staff_wiki_root(workspace_root)
        audit_root = chief_of_staff_audit_root(workspace_root)
        inbox_root.mkdir(parents=True, exist_ok=True)
        wiki_root.mkdir(parents=True, exist_ok=True)
        audit_root.mkdir(parents=True, exist_ok=True)

        (inbox_root / "2026-04-20-meeting-note.md").write_text(
            "---\n"
            "sourceId: chief-of-staff-note-2026-04-20-001\n"
            "title: 验证会议纪要\n"
            "sourceType: meeting-note\n"
            "topicHints:\n"
            "  - chief-of-staff\n"
            "  - llm-wiki\n"
            "trustLevel: raw\n"
            "capturedAt: 2026-04-20T12:00:00+08:00\n"
            "---\n\n"
            "- 已确认总助专属 LLM wiki 需要形成最小闭环。\n"
            "- 当前应先支持 inbox -> wiki -> audit。\n",
            encoding="utf-8",
        )
        (inbox_root / "2026-04-20-scratch-note.txt").write_text(
            "- 当前判断是先做半自动编译链。\n- 待确认问题是何时接回 recall。\n",
            encoding="utf-8",
        )
        (inbox_root / "2026-04-20-facts.json").write_text(
            json.dumps(
                {
                    "sourceId": "chief-of-staff-note-2026-04-20-003",
                    "title": "验证事实",
                    "sourceType": "json-record",
                    "topicHints": ["chief-of-staff", "facts"],
                    "trustLevel": "curated",
                    "capturedAt": "2026-04-20T12:05:00+08:00",
                    "facts": [
                        "当前首轮验证至少需要 3 份资料和 1 页 wiki。",
                        "audit 记录必须能追踪来源与输出页面。",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (inbox_root / "2026-04-21-governance-note.md").write_text(
            "---\n"
            "sourceId: chief-of-staff-note-2026-04-21-005\n"
            "title: 验证治理事实\n"
            "sourceType: governance-note\n"
            "topicHints:\n"
            "  - chief-of-staff\n"
            "  - llm-wiki\n"
            "  - governance\n"
            "  - dispatcher\n"
            "  - approval-report\n"
            "trustLevel: curated\n"
            "capturedAt: 2026-04-21T12:30:00+08:00\n"
            "---\n\n"
            "- 当前已把单页 refresh 扩成 page spec 驱动的多主题页批处理。\n"
            "- 当前已补 reviewer route、approval SLA 和 approval report。\n"
            "- 当前 reminder / email 已可接 webhook 或 host dispatcher。\n",
            encoding="utf-8",
        )

    def _seed_page_specs(self, workspace_root: Path) -> None:
        wiki_root = chief_of_staff_wiki_root(workspace_root)
        wiki_root.mkdir(parents=True, exist_ok=True)
        chief_of_staff_wiki_page_specs_path(workspace_root).write_text(
            json.dumps(
                {
                    "pageSpecs": [
                        {
                            "specId": "chief-of-staff-current-state",
                            "pageId": "chief-of-staff-llm-wiki-current-state",
                            "title": "总助 LLM wiki 当前推进情况",
                            "pageStatus": "working",
                            "topicTags": ["chief-of-staff", "llm-wiki", "knowledge-system", "governance"],
                            "includeTopics": ["chief-of-staff", "llm-wiki", "governance"],
                            "sourceIds": [
                                "chief-of-staff-note-2026-04-20-001",
                                "chief-of-staff-note-2026-04-20-003",
                                "2026-04-20-scratch-note.txt",
                                "chief-of-staff-note-2026-04-21-005",
                            ],
                            "reviewerRoles": ["ChiefOperatingOfficer", "CEOChiefOfStaff"],
                            "primaryReviewer": "ChiefOperatingOfficer",
                            "approvalSlaHours": 48,
                        },
                        {
                            "specId": "chief-of-staff-semi-auto-current-state",
                            "pageId": "chief-of-staff-llm-wiki-semi-auto-current-state",
                            "title": "总助 LLM wiki 半自动整理现状页",
                            "pageStatus": "stable",
                            "topicTags": ["chief-of-staff", "llm-wiki", "automation", "dispatcher"],
                            "includeTopics": ["chief-of-staff", "llm-wiki", "dispatcher"],
                            "sourceIds": [
                                "chief-of-staff-note-2026-04-20-001",
                                "chief-of-staff-note-2026-04-20-003",
                                "chief-of-staff-note-2026-04-21-005",
                            ],
                            "reviewerRoles": ["ChiefTechnologyOfficer", "CEOChiefOfStaff"],
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


if __name__ == "__main__":
    unittest.main(verbosity=2)