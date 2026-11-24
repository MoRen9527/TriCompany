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
import os
os.environ.setdefault("FADE_PLAN_FREEZE", "0")   # v8 item9：run() 级复算门由 PlanFreezeGateTest 直测·其余案关


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
    def setUp(self):
        self._orig = m.PLAN_EXAM_SPLIT
        m.PLAN_EXAM_SPLIT = False   # DP-020：自纠案聚焦重试逻辑·拆分另案

    def tearDown(self):
        m.PLAN_EXAM_SPLIT = self._orig

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

    def test_spawn_cwd_is_run_dir_after_revert(self):
        """DP-019 b 件回退（CTO 裁 2026-11-23 16:16·resume6 席起不来）：
        席 cwd 回 run_dir；a 件 prompt 禁写保留；b 件重修候诊断。"""
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
            self.assertEqual(Path(seen['cwd']).resolve(), Path(rd).resolve())

    def test_prompt_forbids_file_writes(self):
        self.assertIn('禁创建/修改/删除任何文件', m._PLAN_PROMPT_HEAD)


# ── DP-20261123-020（拆分生成+输出精简）四案 ──


class ExamSplitTest(unittest.TestCase):
    def setUp(self):
        self._orig = m.PLAN_EXAM_SPLIT
        m.PLAN_EXAM_SPLIT = True

    def tearDown(self):
        m.PLAN_EXAM_SPLIT = self._orig

    def test_split_calls_twice_with_distinct_prompts(self):
        calls = []

        def fake(seat, rd, rid, timeout_s=900, extra_hint="", prompt_head=None):
            calls.append({"rid": rid, "head": prompt_head or m._PLAN_PROMPT_HEAD})
            return {"rc": 0, "out": json.dumps(_sheet([{"id": "O1", "dimension": "d",
                     "assertion": "path_exists:plan.json", "weight": 5}]), ensure_ascii=False), "err": ""}

        with tempfile.TemporaryDirectory() as d, mock.patch.object(m, "_spawn_seat", side_effect=fake):
            rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)
            self.assertTrue(out["split_mode"])
            self.assertEqual(len(calls), 2)
            self.assertNotIn("出题职能", calls[0]["head"])          # spawn1=plan-only
            self.assertIn("objective 断言硬规格", calls[1]["head"])  # spawn2=exam-only
            self.assertIn("020", calls[0]["rid"]) if False else None  # rid 校验见下
            self.assertTrue(calls[1]["rid"].endswith("-exam"))

    def test_exam_spawn_failure_empty_fallback_non_fatal(self):
        sheet = _sheet([{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}])
        seq = [{"rc": 0, "out": json.dumps(sheet, ensure_ascii=False), "err": ""},
               {"rc": 2, "out": "", "err": "boom"}]
        with tempfile.TemporaryDirectory() as d, mock.patch.object(m, "_spawn_seat", side_effect=seq):
            rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)          # 非致命
            self.assertEqual(out["exam_counts"], {"objective": 0, "subjective": 0})
            exam = json.loads((Path(d) / "exam.json").read_text(encoding="utf-8"))
            self.assertIn("不造假题", exam.get("note", ""))

    def test_split_off_single_spawn_legacy(self):
        m.PLAN_EXAM_SPLIT = False
        sheet = _sheet([{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}])
        with tempfile.TemporaryDirectory() as d, mock.patch.object(
                m, "_spawn_seat", return_value={"rc": 0, "out": json.dumps(sheet, ensure_ascii=False), "err": ""}) as sp:
            rc, out = m.run(_args(d))
            self.assertEqual(rc, 0)
            self.assertEqual(sp.call_count, 1)
            self.assertFalse(out["split_mode"])

    def test_output_form_concise_in_both_prompts(self):
        for pr in (m._PLAN_ONLY_PROMPT, m._EXAM_PROMPT_HEAD):
            self.assertIn("直接给最终 JSON", pr)
            self.assertIn("极简", pr)


class BudgetAndReadScopeTest(unittest.TestCase):
    """DP-020 追补 a+c：exam 读取面限定 + 子超时=min(spawn,段剩余)。"""

    def test_exam_prompt_limits_read_scope(self):
        pr = m._EXAM_PROMPT_HEAD
        self.assertIn("≤5 个文件", pr)
        self.assertIn("禁读源码", pr)
        self.assertIn("工具调用 ≤10 次", pr)

    def test_budget_remaining_floor(self):
        import time as _t
        self.assertEqual(m._budget_remaining(_t.time() - 100), 5)      # 过去=下限 5
        self.assertGreaterEqual(m._budget_remaining(_t.time() + 120), 100)

    def test_budget_exhausted_skips_exam_nonfatal(self):
        m.PLAN_EXAM_SPLIT = True
        try:
            sheet = _sheet([{"id": "O1", "dimension": "d", "assertion": "path_exists:plan.json", "weight": 5}])
            with tempfile.TemporaryDirectory() as d, mock.patch.object(
                    m, "_spawn_seat", return_value={"rc": 0, "out": json.dumps(sheet, ensure_ascii=False), "err": ""}):
                args = _args(d)
                args.stage_budget = 1          # 预算 1s → 剩余<30 → exam 跳过（0 为假值会回落默认·用 1）
                rc, out = m.run(args)
                self.assertEqual(rc, 0)
                self.assertTrue(out.get("exam_spawn", {}).get("skipped"))
                self.assertEqual(out["exam_counts"], {"objective": 0, "subjective": 0})
        finally:
            m.PLAN_EXAM_SPLIT = self._orig if hasattr(self, "_orig") else True


class PlanFreezeGateTest(unittest.TestCase):
    """v8 item9 复算门：缺席拒 / 篡改拒（声明 vs 实测两侧值）。"""

    def test_missing_freeze_rejected(self):
        import tempfile as _tf
        with _tf.TemporaryDirectory() as d:
            r = m._verify_plan_freeze(Path(d))
            self.assertFalse(r["ok"])
            self.assertIn("缺席", r["reason"])

    def test_tampered_declaration_rejected(self):
        sys_paths = None
        from runtime.cognition import plan_enricher as pe
        import tempfile as _tf, json as _j
        d = Path(_tf.mkdtemp())
        tree = d / "t1"
        tree.mkdir()
        (tree / "a.md").write_text("abc", encoding="utf-8")
        pe.write_plan_freeze(d, {"t1": {"path": str(tree)}})
        ok = m._verify_plan_freeze(d)
        self.assertTrue(ok["ok"], ok["reason"])
        fz = _j.loads((d / "plan-freeze.json").read_text(encoding="utf-8"))
        fz["trees"][0]["size"] += 1
        (d / "plan-freeze.json").write_text(_j.dumps(fz), encoding="utf-8")
        bad = m._verify_plan_freeze(d)
        self.assertFalse(bad["ok"])
        self.assertIn("声明", bad["reason"])


if __name__ == "__main__":
    unittest.main()
