"""plan_skill_spawn 单测（DP-20261123-010 出题自检面）。

覆盖：
  ① objective 三式前缀命中率自检（零命中=stderr warn·读数入 out.exam_prefix_hits）
  ② exam 独立落卷（plan.json 剥 exam 段/职责分离回归钉）
  ③ 全前缀命中=零 warn

spawn 面以 mock 替身（不触网/不耗 API）。
"""
from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from runtime.cognition import plan_skill_spawn as m


def _args(run_dir: str) -> argparse.Namespace:
    return argparse.Namespace(run_dir=run_dir, run_id="DP-010-test",
                              from_week="W47", to_week="W48", spawn_timeout=5)


def _sheet(exam_objective: list) -> dict:
    return {
        "plan_version": "1.0.0", "run_id": "x", "from_week": "W47", "to_week": "W48",
        "verdict": "pass", "counts": {"migrate": 1, "keep": 0, "carry_over": 0, "top_level": 1},
        "migrate": [], "keep": [], "carry_over": [],
        "families": [{"family_id": "A", "family_name": "f", "items": [{"item_id": "i", "desc": "d", "status": "planned"}]}],
        "agent_readings": [{"agent": "cos", "action": "a", "rationale": "r", "evidence_ref": "plan.json"}],
        "check_time": "2026-11-23T00:00:00+00:00",
        "exam": {"schema_version": "1.0.0", "objective": exam_objective,
                 "subjective": [{"id": "S1", "dimension": "d", "question": "q", "rubric": "r", "weight": 10}]},
    }


def _patch_spawn(sheet: dict):
    return mock.patch.object(m, "_spawn_seat",
                             return_value={"rc": 0, "out": json.dumps(sheet, ensure_ascii=False), "err": ""})


class PrefixSelfCheckTest(unittest.TestCase):
    def test_zero_hit_warns_and_counts(self):
        objs = [{"id": "O1", "dimension": "d", "assertion": "plan.json 为 JSON 对象", "weight": 5}]
        with tempfile.TemporaryDirectory() as d, _patch_spawn(_sheet(objs)):
            err = io.StringIO()
            with redirect_stderr(err):
                rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)
            self.assertEqual(out["exam_prefix_hits"], {"hits": 0, "total": 1})
            self.assertIn("三式前缀命中 0/1", err.getvalue())

    def test_all_hit_no_warn(self):
        objs = [
            {"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5},
            {"id": "O2", "dimension": "d", "assertion": "json_field:plan.json::verdict::eq:pass", "weight": 5},
            {"id": "O3", "dimension": "d", "assertion": "regex:plan.json::families", "weight": 5},
        ]
        with tempfile.TemporaryDirectory() as d, _patch_spawn(_sheet(objs)):
            err = io.StringIO()
            with redirect_stderr(err):
                rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)
            self.assertEqual(out["exam_prefix_hits"], {"hits": 3, "total": 3})
            self.assertNotIn("WARN", err.getvalue())

    def test_exam_split_responsibility(self):
        objs = [{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}]
        with tempfile.TemporaryDirectory() as d, _patch_spawn(_sheet(objs)):
            m.run(_args(d))
            run_dir = Path(d)
            plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
            exam = json.loads((run_dir / "exam.json").read_text(encoding="utf-8"))
            self.assertNotIn("exam", plan)              # 职责分离：plan 剥 exam 段
            self.assertEqual(len(exam["objective"]), 1)
            self.assertEqual(len(exam["subjective"]), 1)


if __name__ == "__main__":
    unittest.main()
