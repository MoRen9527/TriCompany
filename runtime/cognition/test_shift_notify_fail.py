"""shift_notify_fail F1 exit-code-aware 补丁单测（2026-11-19·白盒随卷）。

案族：exit 4 静默 log 零 SMTP／exit 5 停用知会 SMTP distinct subject／
其余码链失败告警照旧（P1 改点 C 原形零动）。
"""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

from runtime.cognition.shift_notify_fail import main


class F1ExitCodeAwareTest(unittest.TestCase):
    """F1 补丁三案族（CTO 复验卷候批项·值席域裁批准·形 B 静默 log 勘定）。"""

    def _run(self, chain_exit: str) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--chain-exit", chain_exit])
        return rc, buf.getvalue()

    def test_exit4_silent_log_zero_smtp(self) -> None:
        """exit 4=awaiting-ruling 设计内挂起——零 SMTP（误框噪音消除）+stdout log。"""
        with mock.patch(
            "runtime.cognition.weekly_plane_shift._notify_blocking",
        ) as m_notify:
            rc, out = self._run("4")
        self.assertEqual(rc, 0)
        m_notify.assert_not_called()  # 零 SMTP（F1 形 B 静默 log）
        self.assertIn("awaiting-ruling", out)
        self.assertIn("静默", out)
        self.assertIn("72h", out)  # 催办单值源=gate 72h 面注记在

    def test_exit5_terminated_smtp_distinct_subject(self) -> None:
        """exit 5=terminated 一次性停用事件——SMTP 知会 distinct subject。"""
        with mock.patch(
            "runtime.cognition.weekly_plane_shift._notify_blocking",
            return_value=[],
        ) as m_notify:
            rc, out = self._run("5")
        self.assertEqual(rc, 0)
        self.assertEqual(m_notify.call_count, 1)
        kwargs = m_notify.call_args.kwargs
        self.assertIn("terminated", kwargs["subject"])
        self.assertNotIn("失败告警", kwargs["subject"])  # 非链失败语义
        self.assertEqual(kwargs["context_id"], "weekly-shift-terminated")

    def test_other_exit_chain_fail_alert_unchanged(self) -> None:
        """其余码=链失败告警照旧（P1 改点 C 原形零动·exit 2 实证）。"""
        with mock.patch(
            "runtime.cognition.weekly_plane_shift._notify_blocking",
            return_value=[],
        ) as m_notify:
            rc, out = self._run("2")
        self.assertEqual(rc, 0)
        self.assertEqual(m_notify.call_count, 1)
        kwargs = m_notify.call_args.kwargs
        self.assertIn("链失败告警", kwargs["subject"])
        self.assertIn("exit=2", kwargs["subject"])


if __name__ == "__main__":
    unittest.main()
