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


if __name__ == "__main__":
    unittest.main()
