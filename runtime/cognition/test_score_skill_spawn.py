"""score_skill_spawn 件①单测（notice-207 二款·硬序断言＋spawn 面·2026-11-19）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition.score_skill_spawn import run as run_spawn
from runtime.cognition import score_skill_spawn as m


def _args(run: Path, run_id: str = "r") -> object:
    import argparse
    return argparse.Namespace(run_dir=str(run), run_id=run_id,
                              spawn_timeout=1, check_time="2026-11-19T00:00:00+00:00")


class HardOrderGateTest(unittest.TestCase):
    """硬序断言案族（禁并行禁倒置·替身禁令同族）。"""

    def test_score_json_missing_refused(self) -> None:
        """score.json 缺=硬序拒 exit 2（客观分未落禁主观分 spawn）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            code, out = run_spawn(_args(run))
            self.assertEqual(code, 2)
            self.assertFalse(out["hard_order_gate"]["ok"])
            self.assertIn("硬序拒", out["hard_order_gate"]["reason"])
            self.assertNotIn("written", out)  # 零替身 score-skill

    def test_score_json_present_gate_ok_and_faces_absent_noted(self) -> None:
        """score.json 在=gate 过·spawn 缺席（timeout 1s 面注零冒充）→score-skill 落卷。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "score.json").write_text(
                json.dumps({"verdict": "pass", "machine": 65}), encoding="utf-8")
            with mock.patch(
                "runtime.cognition.score_skill_spawn._spawn_seat",
                side_effect=lambda seat, rd, timeout_s=900: {
                    "rc": -1, "sheet": None, "raw_out": "", "err": "probe-absent"},
            ):
                code, out = run_spawn(_args(run))
            self.assertEqual(code, 2)  # 全席缺席=2（缺席注不冒充）
            self.assertTrue(out["hard_order_gate"]["ok"])
            self.assertIn("written", out)  # score-skill.json 落卷（absent 注形）
            skill = json.loads((run / "score-skill.json").read_text(encoding="utf-8"))
            self.assertTrue(skill["judge_faces"]["initial"].get("absent"))
            self.assertTrue(skill["judge_faces"]["joint"][0].get("absent"))
            self.assertEqual(skill["weight_face"]["total_basis"], 100)

    def test_faces_present_form(self) -> None:
        """两席面在形：initial=COS＋joint=[COO] 组装直证。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "score.json").write_text(
                json.dumps({"verdict": "pass"}), encoding="utf-8")

            def fake(seat, rd, timeout_s=900):
                return {"rc": 0, "sheet": {"seat": seat, "scores": {"I1": 12, "I2": 9, "I3": 8}},
                        "raw_out": "", "err": ""}

            with mock.patch(
                "runtime.cognition.score_skill_spawn._spawn_seat",
                side_effect=fake,
            ):
                code, out = run_spawn(_args(run))
            self.assertEqual(code, 0)
            self.assertEqual(out["absent_seats"], [])
            skill = json.loads((run / "score-skill.json").read_text(encoding="utf-8"))
            self.assertEqual(skill["judge_faces"]["initial"]["seat"], "cos")
            self.assertEqual(skill["judge_faces"]["joint"][0]["seat"], "coo")


class ParseHardeningTest(unittest.TestCase):
    """B 件 parse 加固（CEO 批 A+B·CTO 详规）：正常/尾部配平/partial salvage/truncated_output。"""

    def _spawn_with_stdout(self, stdout: str) -> dict:
        import subprocess as _sp
        from unittest import mock

        class FakeR:
            returncode = 0

        with mock.patch.object(_sp, "run", return_value=FakeR()) as _:
            FakeR.stdout = stdout
            # subprocess.run(...) capture_output => 用 TextIOWrapper? 直接伪造返回对象字段
            fake = mock.Mock(returncode=0, stdout=stdout, stderr="")
            with mock.patch.object(_sp, "run", return_value=fake):
                return m._spawn_seat("cos", Path(tempfile.mkdtemp()), timeout_s=5)

    def test_normal_json(self):
        r = self._spawn_with_stdout('{"scores": {"I1": 10}, "improvements": []}')
        self.assertIsInstance(r.get("sheet"), dict)
        self.assertEqual(r["sheet"]["scores"]["I1"], 10)

    def test_tail_balance(self):
        r = self._spawn_with_stdout('noise... {"scores": {"I1": 9}, "ok": true} trailing-junk')
        self.assertIsInstance(r.get("sheet"), dict)
        self.assertEqual(r["sheet"]["scores"]["I1"], 9)
        self.assertIsNone(r.get("partial"))

    def test_partial_salvage_scores(self):
        r = self._spawn_with_stdout('{"scores": {"I1": 8, "I2": 7}, "improvements": [{"title": "tru')
        self.assertTrue(r.get("partial"))
        self.assertTrue(r.get("truncated"))
        self.assertEqual(r["scores"]["I2"], 7)

    def test_truncated_without_scores_fail_loud(self):
        r = self._spawn_with_stdout('{"improvements": [{"title": "abc')
        self.assertFalse(r.get("absent", True) and False)   # absent=False 显式
        self.assertEqual(r.get("absent"), False)
        self.assertEqual(r.get("err_class"), "truncated_output")
        self.assertTrue(r.get("truncated"))


class FacesJudgementIntegrationTest(unittest.TestCase):
    """B 件 run 面三支判定（CTO 详规）：normal→sheet / partial→scores 降级留标 / truncated→absent+err_class。"""

    def test_faces_three_branches(self):
        import argparse
        from unittest import mock
        d = Path(tempfile.mkdtemp())
        (d / "score.json").write_text('{"verdict": "pass"}', encoding="utf-8")

        def fake(seat, rd, timeout_s=900):
            if seat == m.SEATS[0]:
                return {"rc": 0, "sheet": {"scores": {"I1": 10}, "improvements": []}, "raw_out": "", "err": ""}
            if seat == m.SEATS[1]:
                return {"rc": 0, "partial": True, "truncated": True, "scores": {"I1": 7, "I2": 6, "I3": 5}, "raw_out": "", "err": "trunc"}
            return {"rc": 0, "absent": False, "truncated": True, "err_class": "truncated_output",
                    "raw_out": "", "err": "x"}

        with mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              mock.patch.object(m, "_spawn_seat", side_effect=fake):
            rc, out = m.run(argparse.Namespace(run_dir=str(d), run_id="r", spawn_timeout=5,
                                              check_time="2026-11-24T00:00:00Z"))
        f0, f1 = out["faces"][m.SEATS[0]], out["faces"][m.SEATS[1]]
        self.assertEqual(f0["scores"]["I1"], 10)
        self.assertTrue(f1["partial"])
        self.assertTrue(f1["truncated"])
        self.assertEqual(f1["scores"]["I1"], 7)
        self.assertEqual(f1["total_100"] is not None, True)   # 判级面可用（100 制派生）


class ReasoningConcisionPromptTest(unittest.TestCase):
    """DP-048：prompt 条①勘正（直接输出 JSON/reasoning≤10 行）+ 条 b（>10 步定稿即出）。"""

    def test_prompt_has_concision_rules(self):
        pr = m._DSHPROMPT_HEAD
        self.assertIn("直接输出最终 JSON", pr)
        self.assertIn("reasoning 保持精简（≤10 行）", pr)
        self.assertIn("若 reasoning 超过 10 步仍未定稿", pr)
        self.assertNotIn("先在 reasoning 内完成全部推演", pr)   # 旧条①退役

    def test_other_seven_rules_intact(self):
        pr = m._DSHPROMPT_HEAD
        for frag in ("rationale 每项≤30 字", "≤120 字", "必须出现在「improvements」之前",
                     "每席≤3 条", "五必填字段"):
            self.assertIn(frag, pr)


class SubjectivePromptSpecTest(unittest.TestCase):
    """I 卷链内化 ①a：段 7 prompt 含 subjective_score 硬规格（COS 形 I1≤4/I2≤3/I3≤3）。"""

    def test_prompt_contains_subjective_spec(self):
        self.assertIn("subjective_score", m._DSHPROMPT_HEAD)
        self.assertIn("0-4", m._DSHPROMPT_HEAD)
        self.assertIn("judge 不预换算", m._DSHPROMPT_HEAD)
        self.assertIn("subjective-score.json", m._DSHPROMPT_HEAD)
        # A5（CEO 架构令）：wrong_order 判读段
        self.assertIn("wrong_order 判读", m._DSHPROMPT_HEAD)
        self.assertIn("判「要不要紧」", m._DSHPROMPT_HEAD)


class R34BackfillTest(unittest.TestCase):
    """r34 时序修（CTO 令 2026-11-25）：段 7 卷写后补算 score I 族（35 落位·pending 清）。"""

    def test_backfill_sets_35(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        top = {"score_version": "t", "run_id": "r1", "engine_state": "executed_ok",
               "score": {"families": [
                   {"family_id": "I", "state": "partial", "score": None, "weight": 35},
                   {"family_id": "B", "state": "pass", "score": 6, "weight": 6}],
                   "total_score": 41.0, "total_pending_weight": 35,
                   "total_projection": 76.0,
                   "domain_breakdown": {"machine": 41.0, "collection": 0.0, "subjective": 0.0},
                   "run_state": "partial"}}
        (d / "score.json").write_text(json.dumps(top), encoding="utf-8")
        (d / "subjective-score.json").write_text(json.dumps({"entries": [
            {"criterion": "I1", "score": 4, "rationale": "r"},
            {"criterion": "I2", "score": 3, "rationale": "r"},
            {"criterion": "I3", "score": 3, "rationale": "r"}]}), encoding="utf-8")
        r = m._backfill_score_subjective(d, "r1")
        self.assertEqual(r["score"], 35.0)
        doc = json.loads((d / "score.json").read_text(encoding="utf-8"))
        fi = next(f for f in doc["score"]["families"] if f["family_id"] == "I")
        self.assertEqual(fi["state"], "subjective")
        self.assertEqual(fi["score"], 35.0)
        self.assertEqual(doc["score"]["total_pending_weight"], 0)
        self.assertEqual(doc["score"]["run_state"], "succeeded")
        self.assertEqual(doc["score"]["domain_breakdown"]["subjective"], 35.0)


class FourPieceABColumnsTest(unittest.TestCase):
    """四件③：score-skill A/B 双列分离（a/b 各自均值·非混打）。"""

    def test_ab_columns_in_skill(self):
        import tempfile as _tf, argparse
        from unittest import mock as _mock
        d = Path(_tf.mkdtemp())
        (d / "score.json").write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")   # 硬序门前置
        def fake(seat, run_dir, timeout_s=None, **kw):
            return {"rc": 0, "sheet": {"seat": seat, "scores": {"I1": 3},
                                       "dimensions": [
                                           {"dimension": "d1", "object": "a", "score": 80},
                                           {"dimension": "d1", "object": "b", "score": 60}],
                                       "improvements": []}, "err": ""}
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5, check_time="")
        with _mock.patch.object(m, "_spawn_seat", side_effect=fake),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None):
            try:
                m.run(args)
            except Exception:
                pass
        doc = json.loads((d / "score-skill.json").read_text(encoding="utf-8"))
        cols = doc.get("ab_columns") or {}
        self.assertTrue(cols)
        any_seat = next(iter(cols.values()))
        self.assertEqual(any_seat.get("a"), 80.0)
        self.assertEqual(any_seat.get("b"), 60.0)
        self.assertIn("双列分离", doc.get("ab_columns_note", ""))


class FourPieceFinalSummaryTest(unittest.TestCase):
    """③：段 7 final 非空=2 席（cos/coo）汇总。"""

    def test_final_two_seats(self):
        import tempfile as _tf, argparse
        from unittest import mock as _mock
        d = Path(_tf.mkdtemp())
        (d / "score.json").write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
        def fake(seat, run_dir, timeout_s=None, **kw):
            return {"rc": 0, "sheet": {"seat": seat, "scores": {"I1": 3},
                                       "dimensions": [{"dimension": "d1", "object": "a", "score": 80}],
                                       "improvements": []}, "err": ""}
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5, check_time="")
        with _mock.patch.object(m, "_spawn_seat", side_effect=fake),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None):
            try:
                m.run(args)
            except Exception:
                pass
        doc = json.loads((d / "score-skill.json").read_text(encoding="utf-8"))
        fin = ((doc.get("judge_faces") or {}).get("final")) or {}
        self.assertEqual(fin.get("seats"), ["cos", "coo"])
        self.assertIsNotNone(fin.get("average"))
        self.assertIn("汇总", str(fin.get("basis")))


if __name__ == "__main__":
    unittest.main()
