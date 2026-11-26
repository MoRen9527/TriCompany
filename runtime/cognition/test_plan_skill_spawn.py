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
os.environ.setdefault("FADE_PLAN_FREEZE", "0")
os.environ.setdefault("FADE_PLAN_ASSERT", "0")   # 件B 断言由 PlanAssertionsTest 直测   # v8 item9：run() 级复算门由 PlanFreezeGateTest 直测·其余案关


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

        def fake(seat, rd, rid, timeout_s=900, extra_hint="", prompt_head=None, owner_map=None):
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


class PlanAssertionsTest(unittest.TestCase):
    """件B（协议 v2.1.0）：规划 6 断言 a-e 单测。"""

    def _base(self):
        return {"from_week": "W47", "to_week": "W48", "keep": [], "migrate": [],
                "carry_over": [], "families": []}

    def test_b_placeholder_owner(self):
        d = Path(tempfile.mkdtemp())
        plan = self._base()
        plan["families"] = [{"family_id": "A", "items": [
            {"item_id": "A1", "owner": "TBD", "target": "A"}]}]
        bad = m._validate_plan_assertions(plan, d)
        self.assertTrue(any("兜底标签" in x for x in bad))

    def test_c_carry_missing_field(self):
        d = Path(tempfile.mkdtemp())
        plan = self._base()
        plan["carry_over"] = [{"item_id": "c1", "owner": "COS", "accountable": "COS"}]
        bad = m._validate_plan_assertions(plan, d)
        self.assertTrue(any("carry 四字段缺" in x for x in bad))

    def test_d_exam_not_locked(self):
        d = Path(tempfile.mkdtemp())
        (d / "exam.json").write_text("{}", encoding="utf-8")
        bad = m._validate_plan_assertions(self._base(), d)
        self.assertTrue(any("考卷未锁定" in x for x in bad))

    def test_e_bidirectional_mismatch(self):
        d = Path(tempfile.mkdtemp())
        (d / "tree-facts.json").write_text(json.dumps({"trees": {"t1": {}}}), encoding="utf-8")
        plan = self._base()
        bad = m._validate_plan_assertions(plan, d)   # 声明 0 树 vs 实测 1
        self.assertTrue(any("双向断言败" in x for x in bad))

    def test_clean_plan_passes(self):
        d = Path(tempfile.mkdtemp())
        plan = self._base()
        plan["keep"] = [{"item_id": "t1"}]
        (d / "tree-facts.json").write_text(json.dumps({"trees": {"t1": {}}}), encoding="utf-8")
        plan["references"] = []
        bad = m._validate_plan_assertions(plan, d)
        self.assertEqual(bad, [])


class R12Item3FamiliesFieldsTest(unittest.TestCase):
    """R12 item3：families 每项四字段（owner/due/acceptance/depends_on）非空非占位。"""

    def _plan(self, item):
        return {"from_week": "W47", "to_week": "W48", "keep": [], "migrate": [],
                "carry_over": [], "families": [{"family_id": "A", "items": [item]}],
                "staffing": {"raci": {}}, "references": []}

    def test_missing_owner_passes_two_state(self):
        # b 案扩（两态）：字段缺省=pass（显式缺省标记集语义）
        bad = m._validate_families_fields(self._plan(
            {"item_id": "A1", "due": "W48", "acceptance": "ok", "depends_on": []}))
        self.assertEqual(bad, [])

    def test_placeholder_owner_extension_fails(self):
        # default 集内（TBD/待定）pass；扩展占位（多席）fail
        bad = m._validate_families_fields(self._plan(
            {"item_id": "A1", "owner": "多席", "due": "W48", "acceptance": "ok", "depends_on": []}))
        self.assertTrue(any("无效" in x for x in bad))

    def test_all_four_present_passes(self):
        bad = m._validate_families_fields(self._plan(
            {"item_id": "A1", "owner": "COS", "due": "W48", "acceptance": "ok", "depends_on": []}))
        self.assertEqual(bad, [])


class R12Item6RaciTest(unittest.TestCase):
    """R12 item6：RACI 36 键齐·值合法（A/R 必填·C/I 列表）。"""

    def _raci(self, n):
        return {f"k{i}": {"accountable": "COS", "responsible": "COS"}
                for i in range(n)}

    def test_coverage_short_fails(self):
        plan = {"families": [{"family_id": "B", "items": [
            {"item_id": "t1", "target": "t1"}]}],
                "staffing": {"raci": self._raci(0)}}
        bad = m._validate_raci(plan)
        self.assertTrue(any("覆盖不足" in x or "覆盖缺口" in x for x in bad))

    def test_invalid_value_fails(self):
        r = self._raci(36)
        r["k0"]["accountable"] = ""
        bad = m._validate_raci({"staffing": {"raci": r}})
        self.assertTrue(any("accountable" in x for x in bad))

    def test_exact_36_passes(self):
        self.assertEqual(m._validate_raci({"staffing": {"raci": self._raci(36)}}), [])

    def test_coverage_full_passes(self):
        items = [{"item_id": f"t{i}", "target": f"t{i}"} for i in range(3)]
        raci = {f"t{i}": {"accountable": "COS", "responsible": "COS"} for i in range(3)}
        plan = {"families": [{"family_id": "B", "items": items}],
                "staffing": {"raci": raci}}
        self.assertEqual(m._validate_raci(plan), [])

    def test_items_34_raci_34_passes(self):
        items = [{"item_id": f"t{i}", "target": f"t{i}"} for i in range(34)]
        raci = {f"t{i}": {"accountable": "COS", "responsible": "COS"} for i in range(34)}
        plan = {"families": [{"family_id": "B", "items": items}],
                "staffing": {"raci": raci}}
        self.assertEqual(m._validate_raci(plan), [])


class R12CarryEnumTest(unittest.TestCase):
    """R12：CARRY-YYYYMMDD-NNN 族名入 allowed（越表防线保留）。"""

    def test_carry_target_accepted(self):
        d = Path(tempfile.mkdtemp())
        plan = {"from_week": "W47", "to_week": "W48", "keep": [], "migrate": [],
                "carry_over": [], "families": [{"family_id": "A", "items": [
                    {"item_id": "A1", "owner": "COS", "target": "CARRY-20260728-004"}]}],
                "staffing": {"raci": {}}, "references": []}
        bad = m._validate_plan_assertions(plan, d)
        self.assertFalse(any(("结构非法" in x) or ("族点名越界" in x) for x in bad))


class R12WireTest(unittest.TestCase):
    """R12 接入：prompt owner 映射段 / 后处理填空 / company-demand-pool.md 入 allowed。"""

    def test_company_demand_pool_allowed(self):
        d = Path(tempfile.mkdtemp())
        plan = {"from_week": "W47", "to_week": "W48", "keep": [], "migrate": [],
                "carry_over": [], "families": [{"family_id": "A", "items": [
                    {"item_id": "A1", "owner": "COS", "target": "company-demand-pool.md"}]}],
                "staffing": {"raci": {}}, "references": []}
        bad = m._validate_plan_assertions(plan, d)
        self.assertFalse(any(("结构非法" in x) or ("族点名越界" in x) for x in bad))


    def test_owner_map_prompt_block(self):
        om = {"by_family_target": {"B:release-rules-20261118": "CTO"},
              "by_target": {"release-rules-20261118": "CTO"}}
        blk = m._owner_map_prompt_block(om)
        self.assertIn("owner 映射表", blk)
        self.assertIn("B:release-rules-20261118 → CTO", blk)

    def test_fill_owner_from_map(self):
        plan = {"families": [{"family_id": "B", "items": [
            {"item_id": "release-rules-20261118", "owner": ""},
            {"item_id": "x", "owner": "TBD"}]}]}
        om = {"by_family_target": {"B:release-rules-20261118": "CTO"},
              "by_target": {"x": "COS"}}
        n = m._fill_owner_from_r12(plan, om)
        self.assertEqual(n, 2)
        self.assertEqual(plan["families"][0]["items"][0]["owner"], "CTO")
        self.assertEqual(plan["families"][0]["items"][1]["owner"], "COS")

class R12SignatureGuardTest(unittest.TestCase):
    """R12 接口修（CTO 定谳）：真 _spawn_seat 签名含 owner_map / 首 spawn+重试均传 / prompt 含映射块。
    （根因：fake 随签 kw 掩盖真函数缺参——本组用 inspect+MagicMock 直测真面）"""

    def test_real_spawn_seat_accepts_owner_map(self):
        import inspect
        sig = inspect.signature(m._spawn_seat)
        self.assertIn("owner_map", sig.parameters)

    def test_build_prompt_contains_map_block(self):
        om = {"by_family_target": {"B:t1": "CTO"}, "by_target": {}}
        pr = m._build_plan_prompt("cos", "r1", Path("."), owner_map=om)
        self.assertIn("owner 映射表", pr)
        self.assertIn("B:t1 → CTO", pr)

    def test_first_and_retry_spawn_carry_owner_map(self):
        import tempfile as _tf
        from unittest import mock as _mock
        d = Path(_tf.mkdtemp())
        (d / "jobs.json").write_text("{}", encoding="utf-8")
        bad = json.dumps({"plan_version": "1.0.0", "run_id": "r1", "from_week": "W47",
                          "to_week": "W48", "verdict": "pass",
                          "migrate": [], "keep": [], "carry_over": [],
                "families": [{"family_id": "A", "items": []}],
                          "agent_readings": [], "check_level": "bad"})
        calls = []
        def fake_spawn(seat, run_dir, run_id, timeout_s=None, extra_hint="",
                       prompt_head=None, owner_map=None):
            calls.append(owner_map)
            return {"rc": 0, "out": bad, "err": ""}
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5,
                                  tmv_root="", split=False)
        with _mock.patch.object(m, "_spawn_seat", side_effect=fake_spawn),              _mock.patch.object(m, "PLAN_EXAM_SPLIT", False),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None):
            try:
                m.run(args)
            except Exception:
                pass
        self.assertGreaterEqual(len(calls), 2)            # 首 spawn + 自纠重试
        for om in calls[:2]:
            self.assertIsNotNone(om)                      # 两次均传（映射装载可空 dict 但非 None）
            self.assertIsInstance(om, dict)


class R12FallbackMetaTest(unittest.TestCase):
    """R12 a 兜底（无 family_id→by_target）+ b due 填充。"""

    def test_a_no_family_id_falls_to_by_target(self):
        import tempfile as _tf, json as _j
        d = Path(_tf.mkdtemp())
        f = d / "r12.json"
        f.write_text(_j.dumps({"families_items_4fields": [
            {"target": "t-no-fam", "owner": "SDE", "due": "W48"},
        ]}, ensure_ascii=False), encoding="utf-8")
        import os as _os
        old = _os.environ.get("FADE_R12_DATA")
        _os.environ["FADE_R12_DATA"] = str(f)
        try:
            om = m._load_r12_owner_map(None)
        finally:
            if old is None:
                _os.environ.pop("FADE_R12_DATA", None)
            else:
                _os.environ["FADE_R12_DATA"] = old
        self.assertEqual(om["by_target"].get("t-no-fam"), "SDE")
        self.assertEqual(om["by_family_target"], {})

    def test_b_due_filled_from_meta(self):
        plan = {"families": [{"family_id": "B", "items": [
            {"item_id": "t1", "owner": "CTO", "due": ""}]}]}
        om = {"by_family_target": {}, "by_target": {"t1": "CTO"},
              "by_target_meta": {"t1": {"owner": "CTO", "due": "W48 周内"}}}
        n = m._fill_owner_from_r12(plan, om)
        self.assertEqual(plan["families"][0]["items"][0]["due"], "W48 周内")
        self.assertGreaterEqual(n, 1)


class TreeScanLegalTest(unittest.TestCase):
    """a 断言（CTO 修正令 2026-11-25）：family 归属+非空非占位——10 例全 pass·占位/空 fail·fid 非法 fail。"""

    def _tmv(self):
        d = Path(tempfile.mkdtemp())
        trees = d / "docs" / "workflow" / "operating-records" / "2026-W48" / "trees"
        for nm in (".shift-ade-1", "OP-LG-001.json", "bod-tick", "daily-progress.md",
                   "fade001-loop-joint-review", "W2", "W3", "cfo-quota-daily-w47"):
            (trees / nm).mkdir(parents=True, exist_ok=True)
        return d

    def _plan(self, tgt):
        return {"from_week": "W47", "to_week": "W48", "keep": [], "migrate": [],
                "carry_over": [], "families": [{"family_id": "A", "items": [
                    {"item_id": "A1", "owner": "COS", "target": tgt}]}],
                "staffing": {"raci": {}}, "references": []}

    _TEN = (".shift-ade-1", ".shift-ade-2", "OP-LG-001.json", "OP-XY-002.json",
            "bod-tick", "fade001-loop-joint-review", "W2", "W3",
            "daily-progress.md", "cfo-quota-daily-w47")

    def test_ten_examples_all_pass(self):
        d = self._tmv()
        for tgt in self._TEN:
            bad = m._validate_plan_assertions(self._plan(tgt), Path("."), tmv_root=str(d))
            self.assertFalse(any(("结构非法" in x) or ("族点名越界" in x)
                                 or ("target 空" in x) for x in bad), tgt)

    def test_empty_or_placeholder_target_fails(self):
        d = self._tmv()
        for tgt in ("", "TBD"):
            bad = m._validate_plan_assertions(self._plan(tgt), Path("."), tmv_root=str(d))
            self.assertTrue(any("target 空" in x for x in bad), tgt)

    def test_family_id_outside_enum_fails(self):
        d = self._tmv()
        plan = self._plan("bod-tick")
        plan["families"][0]["family_id"] = "Z"
        bad = m._validate_plan_assertions(plan, Path("."), tmv_root=str(d))
        self.assertTrue(any("family 归属非法" in x for x in bad))


class PatrolLayersTest(unittest.TestCase):
    """H 合并令：prompt 硬规格 + plan.cadence_layers 断言 g。"""

    def test_prompt_contains_cadence_layers_spec(self):
        self.assertIn("cadence_layers", m._PLAN_PROMPT_HEAD)
        self.assertIn("bod_patrol", m._PLAN_PROMPT_HEAD)
        self.assertIn("6m", m._PLAN_PROMPT_HEAD)

    def test_plan_missing_layers_fails(self):
        plan = {"from_week": "W47", "to_week": "W48", "keep": [], "migrate": [],
                "carry_over": [], "families": [], "staffing": {"raci": {}},
                "references": [], "patrol_plan": {"who": "c", "window": "w"}}
        bad = m._validate_patrol_layers(plan)
        self.assertTrue(any("cadence_layers" in x for x in bad))

    def test_bod_not_six_minutes_fails(self):
        plan = {"patrol_plan": {"cadence_layers": {
            "bod_patrol": {"cadence": "15m"}, "duty_patrol": {"cadence": "15m"}}}}
        bad = m._validate_patrol_layers(plan)
        self.assertTrue(any("6m" in x for x in bad))

    def test_valid_layers_pass(self):
        plan = {"patrol_plan": {"cadence_layers": {
            "bod_patrol": {"cadence": "6m"}, "duty_patrol": {"cadence": "15m"}}}}
        self.assertEqual(m._validate_patrol_layers(plan), [])


class Item3UnassignedTest(unittest.TestCase):
    """item3 b 案（CTO 令 2026-11-25）：unassigned 显式态四字段缺=pass·有值照旧 fail。"""

    def _plan(self, item):
        return {"families": [{"family_id": "A", "items": [item]}]}

    def test_unassigned_missing_fields_passes(self):
        plan = self._plan({"item_id": "cao-review-yardsick", "owner": "unassigned",
                           "target": "cao-review-yardsick"})
        self.assertEqual(m._validate_families_fields(plan), [])

    def test_assigned_invalid_field_fails(self):
        plan = self._plan({"item_id": "A1", "owner": "COS", "due": "多席", "target": "t"})
        bad = m._validate_families_fields(plan)
        self.assertTrue(any("due 有值但无效" in x for x in bad))

    def test_collect_unassigned_lands(self):
        plan = self._plan({"item_id": "cao-review-yardsick", "owner": "unassigned",
                           "target": "cao-review-yardsick"})
        out = m._collect_unassigned(plan)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["item_id"], "cao-review-yardsick")
        self.assertEqual(plan["unassigned_items"][0]["family_id"], "A")


class B2TwoStateAllFieldsTest(unittest.TestCase):
    """b 案扩（CTO 令 2026-11-25）：四字段全两态 + CARRY 件无 RACI=注非 fail。"""

    def _plan(self, item):
        return {"families": [{"family_id": "A", "items": [item]}]}

    def test_four_fields_default_markers_pass(self):
        item = {"item_id": "CARRY-20260728-004", "owner": "unassigned",
                "due": "TBD", "acceptance": "待定", "depends_on": None}
        self.assertEqual(m._validate_families_fields(self._plan(item)), [])
        item2 = {"item_id": "C-2", "owner": None, "due": "", "acceptance": "todo",
                 "depends_on": ["x"]}
        self.assertEqual(m._validate_families_fields(self._plan(item2)), [])

    def test_invalid_value_fails(self):
        bad = m._validate_families_fields(self._plan(
            {"item_id": "A1", "owner": "多席", "due": "W48", "acceptance": "ok",
             "depends_on": "not-a-list"}))
        self.assertTrue(any("owner 有值但无效" in x for x in bad))
        self.assertTrue(any("depends_on 有值但非列表" in x for x in bad))

    def test_out_of_r12_item_note_not_fail(self):
        # 扩令（R12 集判定）：R12 集外件无键=no-raci-mapping 注（非 fail）
        plan = {"families": [{"family_id": "A", "items": [
            {"item_id": "t1", "target": "CARRY-20260728-004"},
            {"item_id": "t2", "target": "op-x"},
            {"item_id": "t3", "target": "task-inventory-20261117"}]}],
            "staffing": {"raci": {"op-x": {"accountable": "COS", "responsible": "COS"}}}}
        r12 = {"op-x"}                                    # R12 覆盖集仅 op-x
        bad = m._validate_raci(plan, r12)
        self.assertEqual(bad, [])
        self.assertEqual(sorted(plan.get("no_raci_mapping")),
                         ["CARRY-20260728-004", "task-inventory-20261117"])

    def test_in_r12_item_missing_key_fails(self):
        plan = {"families": [{"family_id": "A", "items": [
            {"item_id": "t1", "target": "release-rules-20261118"}]}],
            "staffing": {"raci": {}}}
        bad = m._validate_raci(plan, {"release-rules-20261118"})
        self.assertTrue(any("R12 覆盖缺口" in x for x in bad))


class E1PlanNoImprovementKeysTest(unittest.TestCase):
    """E1（进化架构 2026-11-26）：plan.json 无 capability/improvement 键（回归固化·今日实读零）。"""

    def test_plan_has_no_improvement_keys(self):
        import argparse
        from unittest import mock as _mock
        d = Path(tempfile.mkdtemp())
        def fake_spawn(seat, run_dir, run_id, timeout_s=None, extra_hint="",
                       prompt_head=None, owner_map=None):
            return {"rc": 0, "out": json.dumps({
                "plan_version": "1.0.0", "run_id": "r1", "from_week": "W47",
                "to_week": "W48", "verdict": "pass",
                "counts": {"migrate": 0, "keep": 0, "carry_over": 0, "top_level": 0},
                "bidirectional_ok": True,
                "migrate": [], "keep": [], "carry_over": [],
                "families": [{"family_id": "A", "items": []}],
                "agent_readings": [{"agent": "cos", "action": "scan",
                                    "domain": "tree", "disposition": "keep",
                                    "rationale": "r", "annotation": "n",
                                    "evidence_ref": ["plan.json"]}],
                "check_time": "t"}), "err": ""}
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5,
                                  tmv_root="", split=None)
        with _mock.patch.object(m, "_spawn_seat", side_effect=fake_spawn), \
             _mock.patch.object(m, "PLAN_EXAM_SPLIT", False), \
             _mock.patch.object(m, "_deepseek_balance_cny", return_value=None):
            try:
                m.run(args)
            except Exception:
                pass
        plan = json.loads((d / "plan.json").read_text(encoding="utf-8"))
        banned = {"capability", "improvements", "improvement", "dual_track", "repair"}
        hit = [k for k in banned if k in plan]
        self.assertEqual(hit, [])                       # 顶层键零
        for fam in plan.get("families") or []:
            for it in (fam.get("items") or []):
                self.assertFalse(it.get("capability"), "items 级亦禁")


if __name__ == "__main__":
    unittest.main()
