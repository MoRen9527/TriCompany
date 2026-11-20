"""duty_collection_auto ③案族（notice-214 款一·T+10min 自动采集窗·2026-11-19）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from runtime.cognition.duty_collection_auto import run


def _mk_run(root: Path, trigger_time: str, stages: str = "pass",
            with_collection: bool = False) -> Path:
    rd = root / "run"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "joint-review-trigger.json").write_text(json.dumps({
        "loop_run_id": "shift-W46-test", "trigger_time": trigger_time,
        "round_state": "pending-ceo-ruling"}), encoding="utf-8")
    for name in ("preflight.json", "qualify.json", "plan.json", "dce.json",
                 "verify.json", "score.json", "close.json"):
        (rd / name).write_text(json.dumps({"verdict": stages}), encoding="utf-8")
    if with_collection:
        (rd / "collection-score.json").write_text('{"score_version": "x"}',
                                                  encoding="utf-8")
    return rd


class CollectionAutoTest(unittest.TestCase):
    def test_window_not_reached_skip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = _mk_run(Path(td), "2026-11-19T00:00:00+00:00")
            now = datetime(2026, 11, 19, 0, 5, tzinfo=timezone.utc)  # T+5min
            code, out = run(rd, now=now)
            self.assertEqual(code, 0)
            self.assertEqual(out["action"], "skip")
            self.assertFalse((rd / "collection-score.json").exists())

    def test_window_reached_collects_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = _mk_run(Path(td), "2026-11-19T00:00:00+00:00")
            now = datetime(2026, 11, 19, 0, 12, tzinfo=timezone.utc)  # T+12min
            code, out = run(rd, now=now)
            self.assertEqual(code, 0)
            self.assertEqual(out["action"], "collected")
            self.assertEqual(out["verdict"], "pass")
            doc = json.loads((rd / "collection-score.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["entries"][0]["family_id"], "collection")
            self.assertEqual(doc["entries"][0]["verdict"], "pass")
            self.assertTrue(doc["entries"][0]["rationale"].strip())  # 禁裸判锚
            self.assertEqual(doc["run_id"], "shift-W46-test")

    def test_stage_fail_collects_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = _mk_run(Path(td), "2026-11-19T00:00:00+00:00", stages="fail")
            now = datetime(2026, 11, 19, 0, 12, tzinfo=timezone.utc)
            code, out = run(rd, now=now)
            self.assertEqual(out["verdict"], "fail")  # 缺/红面=机器采集 fail

    def test_idempotent_already_collected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = _mk_run(Path(td), "2026-11-19T00:00:00+00:00", with_collection=True)
            now = datetime(2026, 11, 19, 1, 0, tzinfo=timezone.utc)
            code, out = run(rd, now=now)
            self.assertEqual(out["action"], "already_collected（幂等零重复）")


if __name__ == "__main__":
    unittest.main()
