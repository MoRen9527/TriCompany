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
    "dce.json": {"verdict": "pass"},
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

    def test_stale_missing_dce_json(self) -> None:
        """发现 12 扩域案：dce.json（段 4 产物）缺=stale（十阶段形下 dce.json
        必在·缺即 run 未走完即断的悬空面）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            spec = {k: v for k, v in _ALL_PASS.items() if k != "dce.json"}
            _write_run(run, spec)
            code, m = run_manifest(_ns(run))
            self.assertEqual(code, 0)
            self.assertEqual(m["run_state"], "stale")
            self.assertEqual(m["stages"]["dce.json"], "absent")

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


class CloseContractAssertionTest(unittest.TestCase):
    """notice-208 件④断言族案族（2026-11-19·三面机械验·先 skill 后 CLI 终位承）。"""

    def _mk_run(self, root: Path, close: dict | None, verdict: str = "pass") -> Path:
        run = root / "run"
        run.mkdir(parents=True, exist_ok=True)
        for name in ("preflight.json", "qualify.json", "plan.json", "dce.json",
                     "verify.json", "score.json", "close.json"):
            content = {"verdict": verdict}
            if name == "close.json" and close is not None:
                content = close
            (run / name).write_text(json.dumps(content), encoding="utf-8")
        return run

    def test_time_order_and_hash_and_source_ok(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            run = self._mk_run(Path(td), close={
                "verdict": "pass", "run_state": "ok",
                "run_state_source": "manifest",
                "evidence": [{"stage_artifact": "plan.json", "present": True,
                              "hash": "sha256_16:0123456789abcdef"}],
                "check_time": "2026-11-19T00:00:00+00:00"})
            from runtime.cognition.close_cli import assert_close_contract
            r = assert_close_contract(run, "2026-11-19T01:00:00+00:00")
            self.assertTrue(r["ok"])
            checks = {c["check"]: c["ok"] for c in r["checks"]}
            self.assertTrue(all(checks.values()))

    def test_time_inversion_recd(self) -> None:
        """时点倒挂=红（close 时点晚于 manifest=写序违·口径相抵面直证）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            run = self._mk_run(Path(td), close={
                "verdict": "pass", "run_state": "ok",
                "run_state_source": "manifest",
                "check_time": "2026-11-19T09:00:00+00:00"})
            from runtime.cognition.close_cli import assert_close_contract
            r = assert_close_contract(run, "2026-11-19T01:00:00+00:00")
            checks = {c["check"]: c["ok"] for c in r["checks"]}
            self.assertFalse(checks["time_order"])

    def test_naked_hash_and_bad_source_red(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            run = self._mk_run(Path(td), close={
                "verdict": "pass", "run_state": "manifest_malformed",
                "run_state_source": "manifest_polluted",
                "evidence": [{"stage_artifact": "p", "present": True,
                              "hash": "deadbeefdeadbeef"}],
                "check_time": "2026-11-19T00:00:00+00:00"})
            from runtime.cognition.close_cli import assert_close_contract
            r = assert_close_contract(run, "2026-11-19T01:00:00+00:00")
            checks = {c["check"]: c["ok"] for c in r["checks"]}
            self.assertFalse(checks["evidence_hash_algo"])  # 裸 hash 拒
            self.assertFalse(checks["run_state_source"])  # polluted 非单值域
