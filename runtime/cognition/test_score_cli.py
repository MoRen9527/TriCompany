"""FADE-001 阶段 6 score cli 骨架单测（路径分立三态·CTO 精化一对表）。"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition import score_cli
from runtime.cognition.score_cli import run_score


def _args(**kw) -> argparse.Namespace:
    base = dict(
        run_dir="unused", run_id="shift-W46-test",
        from_week="W46", to_week="W47",
    )
    base.update(kw)
    return argparse.Namespace(**base)


class ScorePathSplitTest(unittest.TestCase):
    """三态路径分立（精化一：跑了但败≠引擎缺席·J7 升级面仅限缺席路径）。"""

    def test_engine_absent_is_j7_upgrade_path(self) -> None:
        with mock.patch.object(score_cli, "import_module", side_effect=ImportError):
            code, s = run_score(_args())
        self.assertEqual(code, 2)
        self.assertEqual(s["engine_state"], "engine_absent")
        self.assertTrue(any("J7" in r for r in s["reasons"]))

    def test_executed_ok(self) -> None:
        fake = mock.MagicMock()
        fake.run_score.return_value = {"total": 88, "items": []}
        with mock.patch.object(score_cli, "import_module", return_value=fake):
            code, s = run_score(_args())
        self.assertEqual(code, 0)
        self.assertEqual(s["engine_state"], "executed_ok")
        self.assertEqual(s["score"]["total"], 88)

    def test_executed_failed_not_absent(self) -> None:
        """跑了但抛异常=executed_failed 非缺席路径（告警级分立面）。"""
        fake = mock.MagicMock()
        fake.run_score.side_effect = RuntimeError("boom")
        with mock.patch.object(score_cli, "import_module", return_value=fake):
            code, s = run_score(_args())
        self.assertEqual(code, 2)
        self.assertEqual(s["engine_state"], "executed_failed")
        self.assertFalse(any("J7" in r for r in s["reasons"]))
        self.assertTrue(any("COS" in r for r in s["reasons"]))

    def test_non_dict_return_is_executed_failed(self) -> None:
        fake = mock.MagicMock()
        fake.run_score.return_value = "not a dict"
        with mock.patch.object(score_cli, "import_module", return_value=fake):
            code, s = run_score(_args())
        self.assertEqual(code, 2)
        self.assertEqual(s["engine_state"], "executed_failed")


class ScoreWriteTest(unittest.TestCase):
    def test_main_writes_score_json_engine_absent(self) -> None:
        from runtime.cognition.score_cli import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            argv = [
                "--run-dir", str(run), "--run-id", "r1",
                "--from-week", "W46", "--to-week", "W47",
            ]
            code = main(argv)  # 沙箱无 score_engine → engine_absent → 2
            self.assertEqual(code, 2)
            s = json.loads((run / "score.json").read_text(encoding="utf-8"))
            self.assertEqual(s["engine_state"], "engine_absent")
            self.assertEqual(s["verdict"], "fail")


if __name__ == "__main__":
    unittest.main()
