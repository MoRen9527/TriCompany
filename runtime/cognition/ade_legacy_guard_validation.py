"""ade_legacy_guard 用例——批准形豁免/未审定红/豁免文件三性验证。"""

from __future__ import annotations

import unittest

from runtime.cognition.ade_legacy_guard import (
    approved_forms_absent,
    unapproved_hits,
)


class AdeLegacyGuardTest(unittest.TestCase):
    def test_approved_etymology_form_exempt(self):
        """批准形④「前称 ADE」溯源注记不红。"""
        line = "- **工作名**：小布（已在 orchestration 文档和 FADE 协议（v2.0.0 前称 ADE spec）中预定义）"
        self.assertEqual(unapproved_hits(line), [])
        self.assertFalse(approved_forms_absent(line))

    def test_era_tag_exempt(self):
        """时代标签（ADE-B/phase-X）与契约值（ade-report）豁免。"""
        for line in (
            "# -- ADE-B multi-host render registry (CEO 2026-08-19 定调, §三 ADE-B)",
            "ADE_PROTOCOL: str = \"ade-report\"",
            "- **ADE 整合阶段 0/1/2 代码落地（2026-08-20）**",
        ):
            self.assertEqual(unapproved_hits(line), [])

    def test_unapproved_usage_red(self):
        """未审定 ADE 用法（旧概念直呼）即红。"""
        line = "1. 按照 ADE 模式执行部署：Agent 规划步骤 → CLI 逐步执行。"
        self.assertTrue(approved_forms_absent(line))
        self.assertEqual(len(unapproved_hits(line)), 1)

    def test_clean_line_pass(self):
        """正名后行（确定性执行规程（FADE DCE 段））无 ADE 即静默。"""
        line = "1. 按照确定性执行规程（FADE DCE 段）执行部署：Agent 规划步骤 → CLI 逐步执行。"
        self.assertEqual(unapproved_hits(line), [])


if __name__ == "__main__":
    unittest.main()
