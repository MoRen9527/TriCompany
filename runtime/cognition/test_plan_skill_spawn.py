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
        "verdict": "pass", "bidirectional_ok": True, "counts": {"migrate": 1, "keep": 0, "carry_over": 0, "top_level": 1},
        "migrate": [], "keep": [], "carry_over": [],
        "families": [{"family_id": "A", "family_name": "f", "items": [{"item_id": "i", "desc": "d", "status": "planned"}]}],
        "agent_readings": [{"agent": "cos", "action": "a", "domain": "tree", "disposition": "keep",
                            "annotation": "an", "rationale": "r", "evidence_ref": ["plan.json"]}],
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


# ── DP-20261123-013 自纠重试一层（照校验器实锚·五态/sanction）──


def _bad_sheet() -> dict:
    s = _sheet([{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}])
    s["agent_readings"] = [
        {"agent": "cos", "action": "a", "domain": "tree",
         "disposition": "pending_review", "annotation": "an", "rationale": "r", "evidence_ref": ["plan.json"]},
    ]
    return s


class SelfCorrectRetryTest(unittest.TestCase):
    def test_invalid_disposition_triggers_one_retry_then_pass(self):
        good = _sheet([{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}])
        good["agent_readings"] = [
            {"agent": "cos", "action": "a", "domain": "tree",
             "disposition": "keep", "annotation": "an", "rationale": "r", "evidence_ref": ["plan.json"]},
        ]
        seq = [{"rc": 0, "out": json.dumps(_bad_sheet(), ensure_ascii=False), "err": ""},
               {"rc": 0, "out": json.dumps(good, ensure_ascii=False), "err": ""}]
        with tempfile.TemporaryDirectory() as d, mock.patch.object(m, "_spawn_seat", side_effect=seq) as sp:
            rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)
            self.assertTrue(out["self_correct"]["retried"])
            self.assertEqual(sp.call_count, 2)
            # 第二次 spawn 带纠正提示
            self.assertIn("自纠重试", sp.call_args.kwargs.get("extra_hint", ""))

    def test_retry_exhausted_fails_closed(self):
        seq = [{"rc": 0, "out": json.dumps(_bad_sheet(), ensure_ascii=False), "err": ""},
               {"rc": 0, "out": json.dumps(_bad_sheet(), ensure_ascii=False), "err": ""}]
        with tempfile.TemporaryDirectory() as d, mock.patch.object(m, "_spawn_seat", side_effect=seq):
            rc, out = m.run(_args(d))
            self.assertEqual(rc, 2)
            self.assertIn("self-correct retry exhausted", out["verdict"])
            self.assertIn("violations_after", out["self_correct"])

    def test_valid_readings_no_retry(self):
        s = _sheet([{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}])
        s["agent_readings"] = [
            {"agent": "cos", "action": "a", "domain": "top_level", "disposition": "pending_ledger",
             "sanction": "封", "annotation": "an", "rationale": "r", "evidence_ref": ["plan.json"]},
        ]
        with tempfile.TemporaryDirectory() as d, mock.patch.object(m, "_spawn_seat", side_effect=[{"rc": 0, "out": json.dumps(s, ensure_ascii=False), "err": ""}]) as sp:
            rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)
            self.assertFalse(out["self_correct"]["retried"])
            self.assertEqual(sp.call_count, 1)


class SeatSandbox019Test(unittest.TestCase):
    """DP-20261123-019：席 cwd=sandbox（非 run_dir）+ prompt 禁写。"""

    def test_spawn_cwd_is_sandbox_not_run_dir(self):
        import subprocess as _sp
        seen = {}

        class FakeR:
            returncode = 0
            stdout = '{"x": 1}'
            stderr = ''

        def fake_run(cmd, **kw):
            seen['cwd'] = kw.get('cwd')
            return FakeR()

        with tempfile.TemporaryDirectory() as rd, mock.patch.object(_sp, 'run', side_effect=fake_run):
            m._spawn_seat('cos', Path(rd), 'r1', timeout_s=5)
            self.assertTrue(Path(seen['cwd']).name.startswith('fade-seat-sandbox-'))
            self.assertNotEqual(Path(seen['cwd']).resolve(), Path(rd).resolve())

    def test_prompt_forbids_file_writes(self):
        self.assertIn('禁创建/修改/删除任何文件', m._PLAN_PROMPT_HEAD)


if __name__ == "__main__":
    unittest.main()
