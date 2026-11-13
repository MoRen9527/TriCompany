"""FADE-001 阶段 9 close cli 骨架单测（run 终态三态·落卷面）。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.close_cli import derive_run_state, run_manifest

_ALL_PASS = {
    "preflight.json": {"verdict": "pass"},
    "qualify.json": {"verdict": "pass"},
    "plan.json": {"verdict": "pass"},
    "verify.json": {"verdict": "pass"},
    "score.json": {"verdict": "pass"},
    "close.json": {"verdict": "pass"},
}


def _write_run(run: Path, spec: dict) -> None:
    run.mkdir(parents=True, exist_ok=True)
    for name, body in spec.items():
        (run / name).write_text(json.dumps(body), encoding="utf-8")


class RunStateTest(unittest.TestCase):
    def test_ok_all_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            _write_run(run, _ALL_PASS)
            code, m = run_manifest(_ns(run))
            self.assertEqual(code, 0)
            self.assertEqual(m["run_state"], "ok")
            self.assertEqual(set(m["stages"].values()), {"pass"})

    def test_failed_has_fail_stage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            spec = dict(_ALL_PASS)
            spec["verify.json"] = {"verdict": "fail", "reasons": ["γ mismatch"]}
            _write_run(run, spec)
            code, m = run_manifest(_ns(run))
            self.assertEqual(code, 0)
            self.assertEqual(m["run_state"], "failed")
            self.assertEqual(m["stages"]["verify.json"], "fail")

    def test_stale_missing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            spec = {k: v for k, v in _ALL_PASS.items() if k != "score.json"}
            _write_run(run, spec)
            code, m = run_manifest(_ns(run))
            self.assertEqual(code, 0)
            self.assertEqual(m["run_state"], "stale")
            self.assertEqual(m["stages"]["score.json"], "absent")

    def test_stale_unreadable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            _write_run(run, _ALL_PASS)
            (run / "close.json").write_text("{ broken", encoding="utf-8")
            code, m = run_manifest(_ns(run))
            self.assertEqual(code, 0)
            self.assertEqual(m["run_state"], "stale")

    def test_derive_pure_function(self) -> None:
        self.assertEqual(derive_run_state({"a": "pass", "b": "pass"}), "ok")
        self.assertEqual(derive_run_state({"a": "pass", "b": "fail"}), "failed")
        self.assertEqual(derive_run_state({"a": "pass", "b": "absent"}), "stale")


class ManifestWriteTest(unittest.TestCase):
    def test_main_writes_manifest_json(self) -> None:
        from runtime.cognition.close_cli import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            _write_run(run, _ALL_PASS)
            code = main([
                "--run-dir", str(run), "--run-id", "shift-W46-test",
                "--from-week", "W46", "--to-week", "W47",
            ])
            self.assertEqual(code, 0)
            m = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(m["run_id"], "shift-W46-test")
            self.assertEqual(m["run_state"], "ok")

    def test_unwritable_run_dir_is_exit2(self) -> None:
        from runtime.cognition.close_cli import main
        with tempfile.TemporaryDirectory() as td:
            blocker = Path(td) / "blocked"
            blocker.write_text("file not dir", encoding="utf-8")
            code = main([
                "--run-dir", str(blocker), "--run-id", "r",
                "--from-week", "W46", "--to-week", "W47",
            ])
            self.assertEqual(code, 2)


def _ns(run: Path):
    import argparse
    return argparse.Namespace(
        run_dir=str(run), run_id="shift-W46-test",
        from_week="W46", to_week="W47",
    )


if __name__ == "__main__":
    unittest.main()
