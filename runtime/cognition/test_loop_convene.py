"""V2-1 白盒测试族（CTO 门禁三项：隔离断言/trigger 件字段值面勘/常规门）。"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.loop_convene import (
    CONVENE_MODE_DEFAULT,
    build_convene_letters,
    dimb_initial_judge,
    read_convene_mode,
)


class ConveneModeFieldTest(unittest.TestCase):
    """门禁②·trigger 件字段值面勘：convene_mode 字段值面三态+fail-safe。"""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="lc-mode-"))

    def test_absent_file_failsafe_manual(self):
        mode, warn = read_convene_mode(self.dir)
        self.assertEqual(mode, CONVENE_MODE_DEFAULT)
        self.assertEqual(mode, "manual")
        self.assertIsNone(warn)

    def test_invalid_value_failsafe_manual_with_warn(self):
        (self.dir / "loop-convene.json").write_text(
            json.dumps({"convene_mode": "turbo"}), encoding="utf-8")
        mode, warn = read_convene_mode(self.dir)
        self.assertEqual(mode, "manual")
        self.assertIn("invalid", str(warn))

    def test_auto_declared(self):
        (self.dir / "loop-convene.json").write_text(
            json.dumps({"convene_mode": "auto"}), encoding="utf-8")
        mode, _ = read_convene_mode(self.dir)
        self.assertEqual(mode, "auto")

    def test_unreadable_json_failsafe(self):
        (self.dir / "loop-convene.json").write_text("{broken", encoding="utf-8")
        mode, warn = read_convene_mode(self.dir)
        self.assertEqual(mode, "manual")
        self.assertIn("unreadable", str(warn))


class IsolationTest(unittest.TestCase):
    """门禁①·隔离断言：召集面零写（纯读渲染·触发链零触）。"""

    def test_build_letters_pure_render(self):
        d = Path(tempfile.mkdtemp(prefix="lc-iso-"))
        before = sorted(str(p) for p in d.rglob("*"))
        letters = build_convene_letters("run-x", 11, "loop_next",
                                        {"subtotal": 59}, ["COS", "CTO"])
        after = sorted(str(p) for p in d.rglob("*"))
        self.assertEqual(before, after, "模板渲染零文件写入（隔离断言）")
        self.assertEqual(len(letters), 2)
        for l in letters:
            self.assertIn("联审召集", l["title"])
            self.assertIn("rationale 必附", l["body"])
            self.assertIn("席角判卷关注点", l["body"])

    def test_seven_seat_default(self):
        letters = build_convene_letters("run-y", 12, "pending_quorum", {"subtotal": 0})
        self.assertEqual(len(letters), 7)


class DimBInitialJudgeTest(unittest.TestCase):
    """③dimB 初判器白盒：机判可验族初判草卷形。"""

    def test_projects_machine_checks(self):
        d = Path(tempfile.mkdtemp(prefix="lc-dimb-"))
        (d / "score.json").write_text(json.dumps({
            "verdict": "shadow",
            "checks": [
                {"id": "B", "ok": True, "weight": 9, "detail": {"x": 1}},
                {"id": "C", "ok": False, "weight": 13, "detail": {"v": 2}},
            ]}), encoding="utf-8")
        init = dimb_initial_judge(d)
        self.assertEqual(init["verdict"], "shadow")
        self.assertEqual(len(init["entries"]), 2)
        self.assertEqual(init["entries"][0]["family_id"], "B")
        self.assertEqual(init["entries"][0]["verdict"], "pass")
        self.assertEqual(init["entries"][1]["verdict"], "fail")
        self.assertIn("机判初判", init["entries"][0]["rationale"])

    def test_absent_score_pending(self):
        init = dimb_initial_judge(Path(tempfile.mkdtemp(prefix="lc-empty-")))
        self.assertEqual(init["verdict"], "pending")
        self.assertEqual(init["entries"], [])


if __name__ == "__main__":
    unittest.main()
