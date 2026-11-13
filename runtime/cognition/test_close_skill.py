"""FADE-001 阶段 8 close skill 骨架单测（漏报护栏·CTO 精化二对表）。"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.close_skill import (
    _structure_gate,
    run_close,
    scan_stage_artifacts,
)


def _args(**kw) -> argparse.Namespace:
    base = dict(run_dir="unused", run_id="shift-W46-test",
                from_week="W46", to_week="W47")
    base.update(kw)
    return argparse.Namespace(**base)


class ScanStageArtifactsTest(unittest.TestCase):
    def test_empty_run_dir_notes_not_substitute(self) -> None:
        """全段缺件=notes 如实注记零替身读数·upgrade_list 空=extracted 合法态。"""
        with tempfile.TemporaryDirectory() as td:
            fails, notes = scan_stage_artifacts(Path(td))
            self.assertEqual(fails, [])
            self.assertEqual(len(notes), 5)
            self.assertTrue(all("absent" in n for n in notes))

    def test_fail_stage_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "plan.json").write_text(
                json.dumps({"verdict": "fail", "reasons": ["bidir 违"]}),
                encoding="utf-8",
            )
            fails, notes = scan_stage_artifacts(run)
            self.assertEqual(len(fails), 1)
            self.assertEqual(fails[0]["stage"], "plan.json")
            self.assertEqual(len(notes), 4)

    def test_upgrade_entry_five_field_spec(self) -> None:
        """升级条目五字段 spec（PM §二）：run_id/stage+trigger/routing/evidence/state。"""
        import re
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "plan.json").write_text(
                json.dumps({"verdict": "fail", "reasons": ["x"]}),
                encoding="utf-8",
            )
            rid = "shift-W46-20261115T160000Z"
            fails, _ = scan_stage_artifacts(run, run_id=rid)
            e = fails[0]
            self.assertEqual(e["run_id"], rid)  # 贯穿主键·正则面
            self.assertRegex(e["run_id"], r"shift-W\d+-\d{8}T\d{6}Z")
            self.assertEqual(e["stage"], "plan.json")  # 段位+触发源
            self.assertEqual(e["trigger"], "stage_artifact_fail")
            self.assertIn(e["routing"], ("候 COS", "候 CEO"))  # 分级二值·终裁归 COS
            self.assertIn("plan.json", e["evidence"])  # 证据指针（禁零锚条目）
            self.assertEqual(e["state"], "open")  # 默认 open·流转 COS 后置 routed

    def test_score_absent_engine_marks_j7(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "score.json").write_text(
                json.dumps({"verdict": "fail", "engine_state": "engine_absent",
                            "reasons": ["score_engine module absent"]}),
                encoding="utf-8",
            )
            fails, _ = scan_stage_artifacts(run)
            self.assertTrue(all("J7" in r for r in fails[0]["reasons"]))
            self.assertEqual(fails[0]["trigger"], "J7_score_engine_absent")

    def test_unreadable_artifact_is_upgrade_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "verify.json").write_text("{ broken", encoding="utf-8")
            fails, _ = scan_stage_artifacts(run)
            self.assertEqual(len(fails), 1)
            self.assertTrue(any("unreadable" in r for r in fails[0]["reasons"]))
            self.assertEqual(fails[0]["trigger"], "artifact_unreadable")


class StructureGateTest(unittest.TestCase):
    """精化二护栏机械面：upgrade_list_state 显式二值禁静默缺省。"""

    GOOD = {
        "close_version": "1.0.0", "run_id": "r", "from_week": "W46",
        "to_week": "W47", "upgrade_list_state": "extracted",
        "upgrade_list": [], "run_state": "ok",
        "notify_target": "COS", "verdict": "pass",
        "check_time": "2026-11-15T15:50:00+00:00",
    }

    def test_good_passes(self) -> None:
        self.assertEqual(_structure_gate(dict(self.GOOD)), [])

    def test_missing_state_key_rejected(self) -> None:
        bad = dict(self.GOOD)
        del bad["upgrade_list_state"]
        errors = _structure_gate(bad)
        self.assertTrue(any("upgrade_list_state" in e for e in errors))

    def test_silent_default_value_rejected(self) -> None:
        """state 值非显式二值（None/空/别词）=拦。"""
        for bad_val in (None, "", "auto", "skipped"):
            bad = dict(self.GOOD)
            bad["upgrade_list_state"] = bad_val
            errors = _structure_gate(bad)
            self.assertTrue(
                any("禁静默缺省" in e for e in errors), f"state={bad_val!r} 未拦"
            )

    def test_notify_target_must_be_cos(self) -> None:
        bad = dict(self.GOOD)
        bad["notify_target"] = "BOD"
        errors = _structure_gate(bad)
        self.assertTrue(any("notify_target" in e for e in errors))


class RunCloseTest(unittest.TestCase):
    def test_run_close_full_pass_empty_upgrade_list(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, c = run_close(_args(run_dir=td))
            self.assertEqual(code, 0)
            self.assertEqual(c["upgrade_list_state"], "extracted")
            self.assertEqual(c["upgrade_list"], [])
            self.assertEqual(c["notify_target"], "COS")

    def test_main_writes_close_json(self) -> None:
        from runtime.cognition.close_skill import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            code = main([
                "--run-dir", str(run), "--run-id", "r2",
                "--from-week", "W46", "--to-week", "W47",
            ])
            self.assertEqual(code, 0)
            c = json.loads((run / "close.json").read_text(encoding="utf-8"))
            self.assertIn("upgrade_list_state", c)  # 精化二：键必须显式在
            self.assertIn(c["upgrade_list_state"], ("extracted", "not_extracted"))


if __name__ == "__main__":
    unittest.main()
