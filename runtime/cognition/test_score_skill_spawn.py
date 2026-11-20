"""score_skill_spawn 件①单测（notice-207 二款·硬序断言＋spawn 面·2026-11-19）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition.score_skill_spawn import run as run_spawn


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


if __name__ == "__main__":
    unittest.main()
