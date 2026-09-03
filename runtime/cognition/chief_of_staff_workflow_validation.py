from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_cognition import CHIEF_OF_STAFF_ID
from runtime.cognition.chief_of_staff_workflow_bridge import (
    ActionItem,
    ChiefOfStaffWorkflowBridge,
    DailyClosePayload,
    MeetingEndPayload,
    MeetingStartPayload,
    main as workflow_bridge_main,
)


SOURCE_AGENT_KIT_PARTS = ("TriCompany", "source-agents", "ceo-chief-of-staff")
MEMORY_FILE_NAME = "memory.agent.md"
SOUL_FILE_NAME = "soul.agent.md"
COLLEAGUES_FILE_NAME = "colleagues.agent.md"
SOCIAL_FILE_NAME = "social.agent.md"
SOUL_BODY = "自然、利落、有温度"
COLLEAGUES_BODY = "磨人是当前直接汇报对象"
SOCIAL_BODY = "非正式场景优先自然称呼"
WEEKLY_MEETING_NAME = "TriMetaverse 每周经营同步会"
SOURCE_ROOT = Path(__file__).resolve().parents[2]
HOOK_SCRIPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "TriMetaverse"
    / ".github"
    / "hooks"
    / "ceo-chief-of-staff-workflow-sync.py"
)
HOOK_SUCCESS_MESSAGE = (
    "chief-of-staff workflow bridge auto-synced repo memory after workflow writeback"
)


def _write_default_assets(agents_root: Path, memory_body: str) -> None:
    _write_asset(agents_root / MEMORY_FILE_NAME, "Memory", memory_body)
    _write_asset(agents_root / SOUL_FILE_NAME, "Soul", SOUL_BODY)
    _write_asset(agents_root / COLLEAGUES_FILE_NAME, "Colleagues", COLLEAGUES_BODY)
    _write_asset(agents_root / SOCIAL_FILE_NAME, "Social", SOCIAL_BODY)


def _write_asset(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")


class ChiefOfStaffWorkflowValidationTest(unittest.TestCase):
    def test_cli_accepts_json_from_stdin_for_workflow_commands(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            source_kit_root = workspace_root.joinpath(*SOURCE_AGENT_KIT_PARTS)
            _write_default_assets(source_kit_root, "当前主档记忆由仓库手工维护")

            stdin_text = json.dumps(
                {
                    "meeting_name": "TriMetaverse 例行开始会",
                    "purpose": "确认本周会议进入正式记录",
                    "participants": ["CEO", "CEOChiefOfStaff"],
                    "background": "需要把 prompt 入口接到 cognition",
                    "agenda": ["开始会议自动写回"],
                    "expected_outputs": ["形成正式记录口径"],
                },
                ensure_ascii=False,
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), mock.patch("sys.stdin", io.StringIO(stdin_text)):
                exit_code = workflow_bridge_main(
                    [
                        "--workspace-root",
                        str(workspace_root),
                        "--storage-root",
                        store_dir,
                        "meeting-start",
                        "--json-stdin",
                    ]
                )

            private_text = Path(store_dir).joinpath("employee", CHIEF_OF_STAFF_ID + ".md")
            self.assertEqual(exit_code, 0)
            self.assertIn("meeting-start", stdout.getvalue())
            self.assertIn("workflow-meeting-start", private_text.read_text(encoding="utf-8"))

    def test_host_hook_auto_syncs_repo_memory_after_workflow_writeback(self) -> None:
        if not HOOK_SCRIPT_PATH.exists():
            self.skipTest(f"workflow hook script not found at {HOOK_SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            source_kit_root = workspace_root.joinpath(*SOURCE_AGENT_KIT_PARTS)
            _write_default_assets(source_kit_root, "repo memory remains source of truth")

            bridge = ChiefOfStaffWorkflowBridge(
                storage_root=store_dir,
                workspace_root=workspace_root,
            )
            bridge.record_meeting_start(
                MeetingStartPayload(
                    meeting_name="Weekly start sync",
                    purpose="enter formal record mode",
                    participants=("CEO", "CEOChiefOfStaff"),
                    background="wire workflow bridge to host hook",
                    agenda=("auto sync",),
                    expected_outputs=("repo digest",),
                )
            )

            hook_input = json.dumps(
                {
                    "tool_name": "run_in_terminal",
                    "tool_input": {
                        "command": (
                            "python -m runtime.cognition.chief_of_staff_workflow_bridge "
                            "meeting-start --json meeting-start.payload.json"
                        )
                    },
                },
                ensure_ascii=True,
            )
            env = os.environ.copy()
            env["TRIMETAVERSE_REPO_ROOT"] = str(workspace_root)
            env["TRICOMPANY_COGNITION_SUPPORT_ROOT"] = str(SOURCE_ROOT)
            env["TRICOMPANY_COGNITION_STORAGE_ROOT"] = store_dir

            result = subprocess.run(
                [sys.executable, str(HOOK_SCRIPT_PATH)],
                input=hook_input,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                cwd=workspace_root,
            )

            output = json.loads(result.stdout)
            memory_text = (source_kit_root / MEMORY_FILE_NAME).read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0)
            self.assertTrue(output["continue"])
            self.assertIn(HOOK_SUCCESS_MESSAGE, output.get("systemMessage", ""))
            self.assertIn("chief-of-staff-cognition-sync:start", memory_text)
            self.assertIn("chief-of-staff-cognition-sync:end", memory_text)
            self.assertIn("meeting-start", memory_text)

    def test_workflow_writebacks_persist_to_private_shared_and_audit_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            source_kit_root = workspace_root.joinpath(*SOURCE_AGENT_KIT_PARTS)
            _write_default_assets(source_kit_root, "总助主档仍以仓库文件为准")

            bridge = ChiefOfStaffWorkflowBridge(
                storage_root=store_dir,
                workspace_root=workspace_root,
            )
            bridge.record_meeting_start(
                MeetingStartPayload(
                    meeting_name=WEEKLY_MEETING_NAME,
                    purpose="确认本周经营主线",
                    participants=("CEO", "CEOChiefOfStaff"),
                    background="需要同步白皮书和 MVP 变更",
                    agenda=("白皮书缺口", "MVP 重排"),
                    expected_outputs=("确定下一步动作",),
                )
            )
            bridge.record_meeting_end(
                MeetingEndPayload(
                    meeting_name=WEEKLY_MEETING_NAME,
                    conclusions=("继续保持 Copilot-host 正式接管边界",),
                    frozen_items=("不提前写成 TriMC 正式宿主",),
                    escalations=("CTO/CPO 上岗前不扩宿主边界",),
                    action_items=(
                        ActionItem(
                            owner="CEOChiefOfStaff",
                            action="同步更新 operating record",
                            due_at="2026-04-19T23:00:00+08:00",
                        ),
                    ),
                    backfill_targets=(
                        "docs/workflow/operating-records/2026-W15/OP-202604-W15-001.unresolved-items.md",
                    ),
                    follow_up_entry="下一轮 CTO/CPO 摸底会",
                )
            )
            bridge.record_daily_close(
                DailyClosePayload(
                    date_label="2026-04-19",
                    summary="完成 cognition bridge 下一步 workflow 写回设计",
                    completed_items=("会议入口写回桥",),
                    unresolved_items=("等待 CTO/CPO 上岗",),
                    next_actions=(
                        ActionItem(
                            owner="CEOChiefOfStaff",
                            action="同步 memory 与 cognition 摘录",
                        ),
                    ),
                    docs_to_update=(
                        "docs/registry/code-state.md",
                        "docs/engineering/STATE.md",
                    ),
                )
            )

            private_text = bridge.store.read_namespace(f"employee/{CHIEF_OF_STAFF_ID}")
            shared_text = bridge.store.read_namespace("org/shared")
            audit_text = bridge.store.read_namespace("org/audit")

            self.assertIn("workflow-meeting-start", private_text)
            self.assertIn("workflow-meeting-end", private_text)
            self.assertIn("workflow-daily-close", private_text)
            self.assertIn(WEEKLY_MEETING_NAME, shared_text)
            self.assertIn("2026-04-19", shared_text)
            self.assertIn("source-entrypoint: 结束会议", audit_text)
            self.assertIn("source-entrypoint: 日常收口", audit_text)

    def test_bidirectional_sync_imports_repo_snapshot_and_exports_managed_digest(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            source_kit_root = workspace_root.joinpath(*SOURCE_AGENT_KIT_PARTS)
            _write_default_assets(source_kit_root, "当前主档记忆由仓库手工维护")

            bridge = ChiefOfStaffWorkflowBridge(
                storage_root=store_dir,
                workspace_root=workspace_root,
            )
            bridge.record_daily_close(
                DailyClosePayload(
                    date_label="2026-04-19",
                    summary="已完成 memory 双向同步桥验证",
                    completed_items=("repo-backed recall", "workflow writeback"),
                    unresolved_items=("等待真实宿主接线",),
                    next_actions=(
                        ActionItem(owner="CEOChiefOfStaff", action="保持 repo 主档为准"),
                    ),
                    docs_to_update=("TriCompany/source-agents/ceo-chief-of-staff/memory.agent.md",),
                )
            )
            result = bridge.sync_repo_memory_bidirectional(limit=3)

            private_text = bridge.store.read_namespace(f"employee/{CHIEF_OF_STAFF_ID}")
            memory_text = (source_kit_root / MEMORY_FILE_NAME).read_text(
                encoding="utf-8"
            )

            self.assertTrue(result.imported)
            self.assertTrue(result.exported)
            self.assertGreaterEqual(result.managed_entry_count, 1)
            self.assertIn("repo-memory-import", private_text)
            self.assertIn("source-hash:", private_text)
            self.assertIn("## Cognition 同步摘录", memory_text)
            self.assertIn("本节由 runtime/cognition workflow bridge 维护", memory_text)
            self.assertIn("daily-close", memory_text)
            self.assertIn("hash:", memory_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)