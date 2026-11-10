"""P1 改点 A/B validation — preflight divergence gate + dual-address blocking notify.

CTO 任务书 TMV fa69fcd9d（2026-11-10 勘修窗）单测四类判据门：
  ① 0/0 已齐 → 放行  ② 纯 behind (0,N) → 放行  ③ 分叉 (N,M>0) → 拦
  ④ fetch 失败 → 拦（不硬跑未知态）
外加：ahead 形（left>0 单侧）·blocking 重试语义·a2 防覆盖轮转·收件人谱解析。
"""

from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition import weekly_plane_shift as wps


def _fake_run_factory(counts: str, tops: list[str] | None = None):
    """Build a subprocess.run stand-in keyed on the git subcommand."""
    tops = tops or ["aaaa000", "bbbb111"]

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return types.SimpleNamespace(returncode=0)
        if cmd[:2] == ["git", "rev-parse"]:
            return types.SimpleNamespace(returncode=0, stdout="\n".join(tops))
        if cmd[:2] == ["git", "rev-list"]:
            return types.SimpleNamespace(returncode=0, stdout=counts)
        raise AssertionError(f"unexpected cmd in fake_run: {cmd}")

    return fake_run


class PreflightDivergeVerdictValidationTest(unittest.TestCase):
    """任务书四类判据 + ahead 形（纯函数面）。"""

    def test_case1_synced_0_0_passes(self) -> None:
        self.assertEqual(wps._diverge_verdict(0, 0), "synced")

    def test_case2_pure_behind_passes(self) -> None:
        self.assertEqual(wps._diverge_verdict(0, 84), "behind")

    def test_case3_diverged_blocks(self) -> None:
        verdict = wps._diverge_verdict(2, 3)
        self.assertEqual(verdict, "diverged")
        self.assertGreater(2, 0)  # left>0 = 拦截判据（病灶形）

    def test_case3b_ahead_blocks(self) -> None:
        verdict = wps._diverge_verdict(1, 0)
        self.assertEqual(verdict, "ahead")

    def test_parse_left_right_count_tab_and_space(self) -> None:
        self.assertEqual(wps._parse_left_right_count("0\t84"), (0, 84))
        self.assertEqual(wps._parse_left_right_count("2 3\n"), (2, 3))
        with self.assertRaises(ValueError):
            wps._parse_left_right_count("garbage")


class PreflightBareSyncValidationTest(unittest.TestCase):
    """编排函数面（mock git）——四类判据端到端 + fetch 失败路径。"""

    def test_pass_when_synced_or_behind(self) -> None:
        for counts, expect_left, expect_right in (("0\t0", 0, 0), ("0\t84", 0, 84)):
            with patch.object(wps.subprocess, "run", _fake_run_factory(counts)):
                ok, detail, readback = wps._preflight_bare_sync(Path("/tmp/repo"))
            self.assertTrue(ok, detail)
            self.assertEqual((readback["left"], readback["right"]), (expect_left, expect_right))
            self.assertIn("preflight ok", detail)

    def test_blocks_on_diverged_with_readback(self) -> None:
        with patch.object(wps.subprocess, "run", _fake_run_factory("2\t3")):
            ok, detail, readback = wps._preflight_bare_sync(Path("/tmp/repo"))
        self.assertFalse(ok)
        self.assertIn("候裁不硬跑", detail)
        self.assertEqual(readback["verdict"], "diverged")
        self.assertEqual(readback["local_top"], "aaaa000")
        self.assertEqual(readback["bare_top"], "bbbb111")

    def test_case4_fetch_failure_blocks(self) -> None:
        def boom(cmd, **kwargs):
            raise OSError("network unreachable")

        with patch.object(wps.subprocess, "run", boom):
            ok, detail, readback = wps._preflight_bare_sync(Path("/tmp/repo"))
        self.assertFalse(ok)
        self.assertIn("preflight fetch/count failed", detail)
        self.assertIn("network unreachable", readback["error"])

    def test_find_repo_root_walks_up(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            (root / ".git").mkdir(parents=True)
            deep = root / "docs" / "workflow" / "operating-records"
            deep.mkdir(parents=True)
            self.assertEqual(wps._find_repo_root(deep), root)
            self.assertIsNone(wps._find_repo_root(Path(td) / "nowhere"))


class NotifyDualAddressBlockingValidationTest(unittest.TestCase):
    """改点 B：收件人谱 + blocking 重试语义。"""

    def test_notify_to_dual_env_wins(self) -> None:
        with patch.dict("os.environ", {
            "WEEKLY_SHIFT_NOTIFY_TO": "m-duty-cos, bod",
            "WEEKLY_SHIFT_SMTP_TO": "legacy@x",
        }, clear=False):
            self.assertEqual(wps._resolve_notify_to(), ["m-duty-cos", "bod"])

    def test_notify_to_legacy_fallback(self) -> None:
        with patch.dict("os.environ", {"WEEKLY_SHIFT_SMTP_TO": "legacy@x"}, clear=False):
            self.assertEqual(wps._resolve_notify_to(), ["legacy@x"])

    def test_notify_to_empty_falls_to_config_default(self) -> None:
        env = {k: "" for k in ("WEEKLY_SHIFT_NOTIFY_TO", "WEEKLY_SHIFT_SMTP_TO")}
        with patch.dict("os.environ", env, clear=False):
            self.assertEqual(wps._resolve_notify_to(), [])

    def _patch_send(self, results):
        mod = types.SimpleNamespace(
            send_notification=lambda **kw: results.pop(0)
        )
        return patch.dict("sys.modules", {"runtime.cognition.notify": mod})

    def test_blocking_first_try_success_empty_failures(self) -> None:
        with self._patch_send([{"status": "sent"}]):
            failures = wps._notify_blocking("s", "b", ["a@x"], "ctx")
        self.assertEqual(failures, [])

    def test_blocking_retry_then_success_is_empty(self) -> None:
        with self._patch_send([{"status": "email_failed", "error": "e1"}, {"status": "sent"}]):
            failures = wps._notify_blocking("s", "b", ["a@x"], "ctx")
        self.assertEqual(failures, [])  # 重试成功=非 blocking（可观测的是终态）

    def test_blocking_both_fail_returns_records(self) -> None:
        with self._patch_send([
            {"status": "email_failed", "error": "e1"},
            {"status": "render_only"},
        ]):
            failures = wps._notify_blocking("s", "b", ["a@x"], "ctx")
        self.assertEqual(len(failures), 2)
        self.assertEqual([f["attempt"] for f in failures], [1, 2])
        self.assertEqual(failures[1]["status"], "render_only")

    def test_blocking_import_failure_observable(self) -> None:
        with patch.dict("sys.modules", {"runtime.cognition.notify": None}):
            failures = wps._notify_blocking("s", "b", ["a@x"], "ctx")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["status"], "import_failed")

    def test_notify_shift_returns_failures(self) -> None:
        ade = {"from_week": "W46", "to_week": "W47", "status": "fail", "start_date": "2026-11-16"}
        mod = types.SimpleNamespace(
            send_notification=lambda **kw: {"status": "email_failed", "error": "down"}
        )
        with patch.dict("sys.modules", {"runtime.cognition.notify": mod}):
            failures = wps._notify_shift(ade)
        self.assertEqual(len(failures), 2)


class ShiftAdeRotationValidationTest(unittest.TestCase):
    """CTO 裁定 a2：单级轮转防覆盖。"""

    def test_rotation_single_level(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "2026-W46" / ".shift-ade.json"
            wps._write_shift_ade_rotating(out, {"round": 1})
            wps._write_shift_ade_rotating(out, {"round": 2})
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), {"round": 2})
            self.assertEqual(
                json.loads(out.with_name(".shift-ade.prev.json").read_text(encoding="utf-8")),
                {"round": 1},
            )
            wps._write_shift_ade_rotating(out, {"round": 3})  # 单级：prev 被第 2 轮覆盖
            self.assertEqual(
                json.loads(out.with_name(".shift-ade.prev.json").read_text(encoding="utf-8")),
                {"round": 2},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
