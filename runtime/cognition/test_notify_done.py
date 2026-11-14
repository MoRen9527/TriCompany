"""FADE-001 阶段 10 notify_done 骨架单测（结论路由三态+PM 契约 run id 嵌入）。"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition.notify_done import (
    _notify_to_chain,
    route_conclusion,
    run_notify_done,
)


def _ns(run: Path, **kw) -> argparse.Namespace:
    base = dict(
        run_dir=str(run), run_id="shift-W46-test",
        from_week="W46", to_week="W47",
        notify_to="cos@example.com", dry_run_only=True,
    )
    base.update(kw)
    return argparse.Namespace(**base)


class RouteTest(unittest.TestCase):
    def test_three_states_routed(self) -> None:
        self.assertEqual(route_conclusion("ok")[0], "结论通知")
        self.assertEqual(route_conclusion("failed")[0], "失败告警")
        self.assertEqual(route_conclusion("stale")[0], "悬空 run 报告")

    def test_unknown_state_degrades_honestly(self) -> None:
        prefix, note = route_conclusion("bogus")
        self.assertIn("未知", prefix)
        self.assertIn("bogus", note)


class RunNotifyDoneTest(unittest.TestCase):
    def test_ok_route_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "manifest.json").write_text(
                json.dumps({"run_state": "ok"}), encoding="utf-8"
            )
            code, d = run_notify_done(_ns(run))
            self.assertEqual(code, 0)
            self.assertEqual(d["run_state"], "ok")
            self.assertIn("结论通知", d["route"]["subject_prefix"])

    def test_failed_route_run_id_in_subject(self) -> None:
        """PM 契约：告警文案必带 run id（subject 嵌入断言）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "manifest.json").write_text(
                json.dumps({"run_state": "failed"}), encoding="utf-8"
            )
            sent: dict = {}
            fake_notify = mock.MagicMock()

            def _capture(**kw) -> dict:
                sent.update(kw)
                return {"status": "render_only"}

            fake_notify.send_notification.side_effect = _capture
            from runtime.cognition import notify as notify_mod  # patch 前显式载（延迟 import 面）
            with mock.patch.object(
                notify_mod, "send_notification", fake_notify.send_notification
            ):
                code, d = run_notify_done(_ns(run, dry_run_only=False))
            self.assertEqual(code, 0)
            self.assertEqual(d["run_state"], "failed")
            self.assertIn("shift-W46-test", sent["subject"])
            self.assertEqual(sent["context_id"], "shift-W46-test")

    def test_no_manifest_is_unknown_degrade(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, d = run_notify_done(_ns(Path(td)))
            self.assertEqual(code, 0)
            self.assertEqual(d["run_state"], "unknown")

    def test_dry_run_only_no_send(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, d = run_notify_done(_ns(Path(td), dry_run_only=True))
            self.assertEqual(code, 0)
            self.assertEqual(d["notify_result"]["status"], "render_only")
            self.assertIn("dry_run_only", d["notify_result"]["note"])


class NotifyToChainTest(unittest.TestCase):
    """发现 27 对齐案（CTO 派工 2026-11-14·CEO 点名）：--notify-to 缺省链
    precedence 与迁移器 _resolve_notify_to env 双址谱同源对表。"""

    def test_cli_value_wins_over_env(self) -> None:
        """CLI 传参优先——env 双址在位时 CLI 值仍胜（precedence 首位）。"""
        with mock.patch.dict("os.environ", {
            "WEEKLY_SHIFT_NOTIFY_TO": "a@x,b@y",
        }):
            self.assertEqual(_notify_to_chain("cos@example.com"), ["cos@example.com"])

    def test_cli_comma_split_matches_migrator_form(self) -> None:
        """CLI 逗号分隔值走同款 strip/split 形（与迁移器谱一致）。"""
        with mock.patch.dict("os.environ", {"WEEKLY_SHIFT_NOTIFY_TO": "a@x"}):
            self.assertEqual(_notify_to_chain("a@x, b@y"), ["a@x", "b@y"])

    def test_empty_cli_falls_to_notify_to_env(self) -> None:
        """CLI 空 → WEEKLY_SHIFT_NOTIFY_TO（双址逗号分隔·precedence 次位）。"""
        with mock.patch.dict("os.environ", {
            "WEEKLY_SHIFT_NOTIFY_TO": "m-duty-cos, bod",
            "WEEKLY_SHIFT_SMTP_TO": "legacy@x",
        }):
            self.assertEqual(_notify_to_chain(""), ["m-duty-cos", "bod"])

    def test_notify_to_absent_falls_to_smtp_to_env(self) -> None:
        """NOTIFY_TO 缺/空 → WEEKLY_SHIFT_SMTP_TO（兼容面·precedence 末位）。"""
        with mock.patch.dict("os.environ", {"WEEKLY_SHIFT_SMTP_TO": "legacy@x"}):
            self.assertEqual(_notify_to_chain(""), ["legacy@x"])
        with mock.patch.dict(
            "os.environ", {"WEEKLY_SHIFT_NOTIFY_TO": "  , ", "WEEKLY_SHIFT_SMTP_TO": "legacy@x"}
        ):
            self.assertEqual(_notify_to_chain(""), ["legacy@x"])

    def test_all_empty_yields_empty_list_config_default(self) -> None:
        """均空 → []（send_notification 落 config default_to·迁移器谱终态同形）。"""
        with mock.patch.dict("os.environ", {
            "WEEKLY_SHIFT_NOTIFY_TO": "", "WEEKLY_SHIFT_SMTP_TO": "",
        }):
            self.assertEqual(_notify_to_chain(""), [])

    def test_run_send_path_consumes_chain(self) -> None:
        """集成案：send 路径 `to` 消费缺省链（CLI 空+env 双址→收双址）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "manifest.json").write_text(
                json.dumps({"run_state": "ok"}), encoding="utf-8"
            )
            sent: dict = {}

            def _capture(**kw) -> dict:
                sent.update(kw)
                return {"status": "render_only"}

            from runtime.cognition import notify as notify_mod  # patch 前显式载（延迟 import 面）
            with mock.patch.dict("os.environ", {
                "WEEKLY_SHIFT_NOTIFY_TO": "m-duty-cos, bod",
            }), mock.patch.object(
                notify_mod, "send_notification", _capture
            ):
                code, d = run_notify_done(_ns(run, notify_to="", dry_run_only=False))
            self.assertEqual(code, 0)
            self.assertEqual(sent["to"], ["m-duty-cos", "bod"])


class NotifyDoneWriteTest(unittest.TestCase):
    def test_main_writes_notify_done_json(self) -> None:
        from runtime.cognition.notify_done import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            code = main([
                "--run-dir", str(run), "--run-id", "r10",
                "--from-week", "W46", "--to-week", "W47",
                "--dry-run-only",
            ])
            self.assertEqual(code, 0)
            d = json.loads((run / "notify_done.json").read_text(encoding="utf-8"))
            self.assertEqual(d["run_id"], "r10")

    def test_unwritable_run_dir_is_exit2(self) -> None:
        from runtime.cognition.notify_done import main
        with tempfile.TemporaryDirectory() as td:
            blocker = Path(td) / "blocked"
            blocker.write_text("file not dir", encoding="utf-8")
            code = main([
                "--run-dir", str(blocker), "--run-id", "r",
                "--from-week", "W46", "--to-week", "W47",
            ])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
