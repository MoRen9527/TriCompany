"""chain_runner S2 案族（notice-223 款二·段级重跑承载·段序程序化·2026-11-24）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition.chain_runner import run, _stage_argv, STAGES


def _args(**kw) -> object:
    import argparse
    base = dict(run_dir="", run_id="r", from_week="W47", to_week="W48",
                start_date="2026-11-23", resume_stage=None, stage_timeout=60)
    base.update(kw)
    return argparse.Namespace(**base)


class ChainRunnerS2Test(unittest.TestCase):
    """S2 段序程序化＋段级重跑案族（§六A·段前置真值断言·fail-closed 款三）。"""

    def test_stage_order_ten_stages(self) -> None:
        """十段序钉（notice-207 件①硬序承录面）：preflight→…→score_cli→
        score_skill_spawn→score_rubric→close_skill→close_cli 十段序零倒置。"""
        names = [s[0] for s in STAGES]
        self.assertEqual(len(names), 10)
        self.assertLess(names.index("score_cli"), names.index("score_skill_spawn"))
        self.assertLess(names.index("score_skill_spawn"), names.index("close_skill"))

    def test_resume_stage_out_of_range(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, rep = run(_args(run_dir=td, resume_stage=0))
            self.assertEqual(code, 3)
            self.assertIn("越段序", rep["resume_error"])

    def test_resume_stage_prev_artifact_red(self) -> None:
        """段级重跑前置真值断言红钉：段 6 起（score_cli 段）前置=段 5 verify
        产物缺→前置断言红 exit 3（跳段拒·§六A）。"""
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            code, rep = run(_args(run_dir=str(rd), resume_stage=6))
            self.assertEqual(code, 3)
            self.assertIn("前置断言红", rep["resume_error"])

    def test_fail_closed_stage_red(self) -> None:
        """段报错停 fail-closed 钉（款三·mock 子进程 rc=2→停链 failed_stage）。"""
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            for name, art in STAGES[:4]:
                (rd / art).write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
            with mock.patch(
                "runtime.cognition.chain_runner.subprocess.run",
                return_value=mock.Mock(returncode=2, stdout="", stderr="boom"),
            ):
                code, rep = run(_args(run_dir=str(rd), resume_stage=5))
            self.assertEqual(code, 2)
            self.assertEqual(rep["failed_stage"], "verify")

    def test_full_pass_green_shape(self) -> None:
        """全绿形钉：十段产物全在（mock 子进程 rc=0）→verdict=pass 零红。"""
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            for name, art in STAGES:
                (rd / art).write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
            with mock.patch(
                "runtime.cognition.chain_runner.subprocess.run",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ):
                code, rep = run(_args(run_dir=str(rd), resume_stage=1))
            self.assertEqual(code, 0)
            self.assertEqual(rep["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
