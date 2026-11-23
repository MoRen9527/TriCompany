"""preflight.py 单测 — FADE-001 要点②（unittest stdlib·零新依赖）。

覆盖：
  - compute_week_shift_tokens 金值案（周日/跨年 wrap/中间周幂等窗）。
  - check_week_math 触发日边界 + 三值比对。
  - check_hostname 匹配/不匹配/dev escape。
  - check_git_hygiene 真 git 仓四态（干净/非迁移面脏/迁移面脏/MERGE_HEAD）。
  - check_healthz 本地真端点（ok:true / ok:false / 连接拒）。
  - run_preflight 端到端退出码表（0/2/3——3=真 bare 仓分叉造形·DEM-009 注入式
    拦截同款精神）。

跑法：cd TriCompany && python -m unittest runtime.cognition.test_preflight -v
"""

from __future__ import annotations

import argparse
import json
import tempfile
from unittest import mock
import os
import subprocess
import threading
import unittest
from datetime import date, datetime, timezone
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from runtime.cognition.preflight import (
    build_parser,
    check_git_hygiene,
    check_healthz,
    check_hostname,
    check_week_math,
    compute_week_shift_tokens,
    run_preflight,
)


def _git(*args: str, cwd: Path | None = None) -> None:
    cmd = ["git", *args]
    if cwd is not None:
        cmd = ["git", "-C", str(cwd), *args]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)


def _git_env_repo(repo: Path) -> None:
    """真 git 仓最小形（dev 分支 + 用户身份 + 首提交）。"""
    repo.mkdir(parents=True, exist_ok=True)
    _git("init", "-b", "dev", cwd=repo)
    _git("config", "user.name", "test")
    _git("config", "user.email", "test@example.com")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-m", "seed", cwd=repo)


class HealthzServer:
    """本地真 healthz 端点（payload 可配）。"""

    def __init__(self, body: dict, status: int = 200):
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                payload = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):  # 静默
                pass

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/healthz"

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def make_args(**over):
    base = dict(
        from_week="W46", to_week="W47", start_date="2026-11-16",
        repo="/nonexistent", daemon_url="http://127.0.0.1:9/healthz",
        expected_host="iZf8ziw57ydktu77fsld9yZ", skip_hostname=True, no_diverge=True,
        diverge_remote="sg-bare",
    )
    base.update(over)
    return argparse.Namespace(**base)



class Dp030RulingThreeBindTest(unittest.TestCase):
    """DP-030 六案：新件认/旧件拒/二次消费拒/跨 run 拒/缺 signed_at 拒（护栏停）/自指排除留痕。"""

    def _mk(self, td, name="shift-W46-r", ruling=None, age=0.0):
        rd = Path(td) / name
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
        (rd / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
        if ruling is not None:
            (rd / "ceo-ruling.json").write_text(json.dumps(ruling), encoding="utf-8")
        return rd

    def _bind(self, name="shift-W46-r", **over):
        doc = {"decision": "continue", "ruling_ref": "n", "run_id": name,
               "round_count": 1, "signed_at": "2026-11-23T00:00:00Z"}
        doc.update(over)
        return doc

    def test_new_three_bind_accepted_and_marked(self):
        with tempfile.TemporaryDirectory() as td:
            rd = self._mk(td, ruling=self._bind())
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc), current_run_dir=str(Path(td) / "shift-W46-next"))
            self.assertTrue(r["ok"])
            self.assertEqual(r["state"], "continue")
            self.assertTrue((rd / ".ceo-ruling-consumed.json").is_file())   # 消费戳落卷

    def test_legacy_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            self._mk(td, ruling={"decision": "continue", "signed_at": "2026-11-18T00:00:00Z"})
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertIn("作废需重签", r["detail"])

    def test_second_consumption_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            self._mk(td, ruling=self._bind())
            nxt = str(Path(td) / "shift-W46-next")
            r1 = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc), current_run_dir=nxt)
            self.assertTrue(r1["ok"])
            r2 = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc), current_run_dir=nxt + "2")
            self.assertFalse(r2["ok"])
            self.assertIn("已消费", r2["detail"])

    def test_cross_run_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            self._mk(td, ruling=self._bind(run_id="shift-W46-other"))
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertIn("跨 run", r["detail"])

    def test_missing_signed_at_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            doc = self._bind()
            doc.pop("signed_at")
            self._mk(td, ruling=doc)
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertIn("作废需重签", r["detail"])

    def test_self_run_dir_explicitly_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            self._mk(td, name="shift-W46-prev", ruling=self._bind("shift-W46-prev"))
            cur = Path(td) / "shift-W46-cur"
            cur.mkdir()
            (cur / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (cur / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc), current_run_dir=str(cur))
            self.assertEqual(r["prev_run_dir"], "shift-W46-prev")   # 自身显式排除·prev=真正上轮
            self.assertTrue(r["ok"])


class DivergeRemoteDefaultTest(unittest.TestCase):
    def test_argparse_default_origin(self):
        """argparse 默认 diverge_remote=origin（TriCompany 检出实名·FADE-001 演练实锚勘定
        —— sg-bare 系 TriMetaverse 检出实名，preflight --repo 默认 TriCompany 根）。"""
        args = build_parser().parse_args(
            ["--from", "W46", "--to", "W47", "--start-date", "2026-11-16"]
        )
        self.assertEqual(args.diverge_remote, "origin")


class ComputeWeekShiftTokensTest(unittest.TestCase):
    def test_sunday_golden(self):
        # 2026-11-15 周日 → 明天 11-16 周一 → to W47 / from W46 / start 2026-11-16
        self.assertEqual(
            compute_week_shift_tokens(date(2026, 11, 15)),
            {"from_week": "W46", "to_week": "W47", "start_date": "2026-11-16"},
        )

    def test_cross_year_wrap(self):
        # 2027-01-03 周日 → 明天 01-04 周一 = 2027 W01 → fromWeek=0 → wrap 上一年
        # 12-28 → 2026 最后 ISO 周 = W53
        self.assertEqual(
            compute_week_shift_tokens(date(2027, 1, 3)),
            {"from_week": "W53", "to_week": "W01", "start_date": "2027-01-04"},
        )

    def test_midweek_idempotent_window(self):
        # 中间周（2026-11-18 周三）→ 明天周四仍在 W47 窗 → 与周日跑同值
        self.assertEqual(
            compute_week_shift_tokens(date(2026, 11, 18)),
            {"from_week": "W46", "to_week": "W47", "start_date": "2026-11-16"},
        )


class CheckWeekMathTest(unittest.TestCase):
    def test_sunday_and_tokens_match(self):
        r = check_week_math(date(2026, 11, 15), "W46", "W47", "2026-11-16")
        self.assertTrue(r["ok"])
        self.assertTrue(r["trigger_day_is_sunday"])
        self.assertNotIn("reason", r)

    def test_non_sunday_blocked(self):
        r = check_week_math(date(2026, 11, 16), "W46", "W47", "2026-11-16")  # 周一
        self.assertFalse(r["ok"])
        self.assertFalse(r["trigger_day_is_sunday"])

    def test_loop_window_waives_sunday_gate(self):
        # 双场景形①：--loop-window 标记 → 周日门豁免（法源=CEO 23:55 令进化循环不限周日）
        r = check_week_math(date(2026, 11, 16), "W46", "W47", "2026-11-16", loop_window=True)  # 周一
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "loop-window")
        self.assertEqual(r["sunday_gate"], "exempted(loop)")  # CTO 裁 A+词面对表·验收锚②逐字形
        self.assertEqual(r["sunday_gate_note"], "real cron Sunday gate unchanged")  # 防混语义保载他键
        self.assertIn("2026-11-16", r["run_dir_week_note"])  # 归属周按实际时点注记防混

    def test_loop_window_tokens_mismatch_still_fails(self):
        r = check_week_math(date(2026, 11, 16), "W45", "W47", "2026-11-16", loop_window=True)
        self.assertFalse(r["ok"])
        self.assertIn("tokens mismatch", r.get("reason", ""))

    def test_cron_reading_has_sunday_gate_enforced(self):
        # CTO 裁 A 增量小补：现役 cron 形 reading 统一增键 sunday_gate:"enforced"
        # （加法非破坏·两形词面成对 enforced/exempted·读数面可溯）。
        r = check_week_math(date(2026, 11, 15), "W46", "W47", "2026-11-16")  # 周日绿案
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "cron-sunday")
        self.assertEqual(r["sunday_gate"], "enforced")

    def test_cron_wording_enforced_even_when_blocked(self):
        # 词面钉副案：周一 cron 拒案 reading 同带 sunday_gate:"enforced"
        # （键为形态标注·非通过断言——拒案读数可溯同键）。
        r = check_week_math(date(2026, 11, 16), "W46", "W47", "2026-11-16")  # 周一拒案
        self.assertFalse(r["ok"])
        self.assertEqual(r["sunday_gate"], "enforced")

    def test_loop_window_seam_marker_env_none(self):
        # 接缝三态（run_preflight 层）：marker 一次性消费/env 形/双无周日门原样。
        # sandbox=TRICO_LOOP_MARKER_DIR 指临时位（零生产面触碰·B 案 env 名契约）。
        import os
        import tempfile
        from runtime.cognition.preflight import run_preflight

        old_cfg = os.environ.get("TRICO_LOOP_MARKER_DIR")
        old_lw = os.environ.pop("LOOP_WINDOW", None)
        tmp_cfg = tempfile.mkdtemp(prefix="trico-seam-")
        os.environ["TRICO_LOOP_MARKER_DIR"] = tmp_cfg
        marker = os.path.join(tmp_cfg, "loop-window.marker")
        try:
            args = argparse.Namespace(
                repo=".", from_week="W46", to_week="W47", start_date="2026-11-16",
                daemon_url="http://127.0.0.1:1", skip_hostname=True,
                no_diverge=True, diverge_remote="origin", loop_window=False,
                expected_host=None,
            )
            # 态1 marker 形：文件在→豁免+读即删
            open(marker, "w").close()
            code, out = run_preflight(args, today=date(2026, 11, 16))
            wm = out["assertions"]["week_math"]
            self.assertTrue(wm["ok"]); self.assertEqual(wm["mode"], "loop-window")
            self.assertEqual(wm["loop_source"], "marker")
            self.assertFalse(os.path.exists(marker))  # one-shot 消费实证
            # 态2 env 形：LOOP_WINDOW=1→豁免（无 marker）
            os.environ["LOOP_WINDOW"] = "1"
            code, out = run_preflight(args, today=date(2026, 11, 16))
            wm = out["assertions"]["week_math"]
            self.assertTrue(wm["ok"]); self.assertEqual(wm["loop_source"], "env")
            # 态3 双无：周一无标记无 env→周日门原样拒
            del os.environ["LOOP_WINDOW"]
            code, out = run_preflight(args, today=date(2026, 11, 16))
            wm = out["assertions"]["week_math"]
            self.assertFalse(wm["ok"]); self.assertEqual(wm["mode"], "cron-sunday")
            # ①失败②不发断言（r112③·注入序依赖门槛）：豁免面失败=非零退出——
            # 触发链信号形（非零=①未过→②trigger 不发·防序失误面）。
            self.assertNotEqual(code, 0, "周日门拒=非零退出（②不发信号形）")
        finally:
            if old_lw is None:
                os.environ.pop("LOOP_WINDOW", None)
            else:
                os.environ["LOOP_WINDOW"] = old_lw
            if old_cfg is None:
                os.environ.pop("TRIMC_CONFIG_DIR", None)
            else:
                os.environ["TRIMC_CONFIG_DIR"] = old_cfg
            import shutil
            shutil.rmtree(tmp_cfg, ignore_errors=True)

    def test_marker_env_name_contract_no_legacy_read(self):
        # env 名契约钉（B 案·CTO 02:05 确认 TRICO_LOOP_MARKER_DIR·2026-11-16）：
        # 旧名 TRIMC_CONFIG_DIR 系 TriRMC daemon 自身消费键（cron store/log 域·同名
        # 撞车 unit 注入实测分叉实锚 2026-11-16）——preflight marker 路径禁回读旧名。
        # 诱饵形：旧名位放 marker·新名指空目录 → marker 零消费 → 周日门原样拒。
        import os
        import shutil
        import tempfile
        from runtime.cognition.preflight import run_preflight

        old_new = os.environ.pop("TRICO_LOOP_MARKER_DIR", None)
        old_legacy = os.environ.pop("TRIMC_CONFIG_DIR", None)
        tmp_new = tempfile.mkdtemp(prefix="trico-new-empty-")
        tmp_legacy = tempfile.mkdtemp(prefix="trico-legacy-bait-")
        os.environ["TRICO_LOOP_MARKER_DIR"] = tmp_new  # 新名·空目录（无 marker）
        os.environ["TRIMC_CONFIG_DIR"] = tmp_legacy  # 旧名诱饵位·放 marker
        open(os.path.join(tmp_legacy, "loop-window.marker"), "w").close()
        try:
            args = argparse.Namespace(
                repo=".", from_week="W46", to_week="W47", start_date="2026-11-16",
                daemon_url="http://127.0.0.1:1", skip_hostname=True,
                no_diverge=True, diverge_remote="origin", loop_window=False,
                expected_host=None,
            )
            code, out = run_preflight(args, today=date(2026, 11, 16))  # 周一
            wm = out["assertions"]["week_math"]
            self.assertFalse(wm["ok"])  # 旧名诱饵未被消费 → 周日门原样拒
            self.assertNotIn("loop_source", wm)  # 无豁免源=旧名零消费直证
        finally:
            if old_new is not None:
                os.environ["TRICO_LOOP_MARKER_DIR"] = old_new
            if old_legacy is None:
                os.environ.pop("TRIMC_CONFIG_DIR", None)
            else:
                os.environ["TRIMC_CONFIG_DIR"] = old_legacy
            shutil.rmtree(tmp_new, ignore_errors=True)
            shutil.rmtree(tmp_legacy, ignore_errors=True)

    def test_cron_mode_keeps_sunday_gate(self):
        # 双场景形②：无标记（真实 cron）→ 周日门原样（非周日仍拒）
        r = check_week_math(date(2026, 11, 16), "W46", "W47", "2026-11-16")
        self.assertFalse(r["ok"])
        self.assertEqual(r.get("mode"), "cron-sunday")
        self.assertIn("not Sunday", r["reason"])

    def test_token_mismatch_blocked(self):
        r = check_week_math(date(2026, 11, 15), "W45", "W47", "2026-11-16")  # from 错
        self.assertFalse(r["ok"])
        self.assertIn("mismatch", r["reason"])


class CheckHostnameTest(unittest.TestCase):
    def test_match(self):
        import socket
        r = check_hostname(socket.gethostname())
        self.assertTrue(r["ok"])

    def test_mismatch(self):
        r = check_hostname("definitely-not-this-host")
        self.assertFalse(r["ok"])
        self.assertIn("mismatch", r["reason"])

    def test_skip_escape(self):
        r = check_hostname(None)
        self.assertTrue(r["ok"])
        self.assertTrue(r["skipped"])


class CheckGitHygieneTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="preflight-git-"))
        self.repo = self.tmp / "repo"
        _git_env_repo(self.repo)

    def test_clean_ok(self):
        self.assertTrue(check_git_hygiene(self.repo)["ok"])

    def test_non_migration_face_dirty_ok(self):
        (self.repo / "scratch.txt").write_text("x", encoding="utf-8")
        r = check_git_hygiene(self.repo)
        self.assertTrue(r["ok"])  # 非迁移面脏不拦

    def test_migration_face_dirty_blocked(self):
        wk = self.repo / "docs" / "workflow" / "operating-records" / "W46"
        wk.mkdir(parents=True)
        (wk / "leftover.md").write_text("residue\n", encoding="utf-8")
        r = check_git_hygiene(self.repo)
        self.assertFalse(r["ok"])
        self.assertEqual(len(r["migration_face_dirty"]), 1)

    def test_merge_head_blocked(self):
        _git("checkout", "-b", "other", cwd=self.repo)
        (self.repo / "f.txt").write_text("x", encoding="utf-8")
        _git("add", "-A", cwd=self.repo)
        _git("commit", "-m", "other", cwd=self.repo)
        (self.repo / ".git" / "MERGE_HEAD").write_text(
            "0" * 40 + "\n", encoding="utf-8"
        )
        r = check_git_hygiene(self.repo)
        self.assertFalse(r["ok"])
        self.assertIn("MERGE_HEAD", r["in_progress_ops"])


class CheckHealthzTest(unittest.TestCase):
    def tearDown(self):
        srv = getattr(self, "_srv", None)
        if srv is not None:
            srv.stop()

    def test_ok_true_passes(self):
        self._srv = HealthzServer({"ok": True, "service": "trirmc", "cron": {"enabled": True}})
        r = check_healthz(self._srv.url)
        self.assertTrue(r["ok"])
        self.assertEqual(r["service"], "trirmc")

    def test_ok_false_blocked(self):
        self._srv = HealthzServer({"ok": False})
        r = check_healthz(self._srv.url)
        self.assertFalse(r["ok"])
        self.assertIn("ok!=true", r["reason"])

    def test_connection_refused_blocked(self):
        r = check_healthz("http://127.0.0.1:9/healthz", timeout_s=1.0)
        self.assertFalse(r["ok"])
        self.assertIn("reason", r)


class RunPreflightExitCodesTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="preflight-e2e-"))
        self.repo = self.tmp / "repo"
        _git_env_repo(self.repo)
        self._servers = []

    def tearDown(self):
        for s in self._servers:
            s.stop()

    def _healthz_ok(self) -> str:
        s = HealthzServer({"ok": True, "service": "trirmc"})
        self._servers.append(s)
        return s.url

    def test_exit_0_all_pass(self):
        code, out = run_preflight(make_args(
            repo=str(self.repo), daemon_url=self._healthz_ok(),
            expected_host=None,  # hostname skip
        ), today=date(2026, 11, 15))  # 周日（真今天非周日·主闸工作证明）
        self.assertEqual(code, 0)
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["exit_code"], 0)
        self.assertEqual(out["reasons"], [])
        self.assertTrue(out["preflight_version"])

    def test_exit_2_wrong_tokens(self):
        code, out = run_preflight(make_args(
            from_week="W44",  # 错周 token
            repo=str(self.repo), daemon_url=self._healthz_ok(), expected_host=None,
        ))
        self.assertEqual(code, 2)
        self.assertTrue(any(r.startswith("week_math") for r in out["reasons"]))

    def test_exit_2_healthz_down(self):
        code, out = run_preflight(make_args(
            repo=str(self.repo), daemon_url="http://127.0.0.1:9/healthz", expected_host=None,
        ))
        self.assertEqual(code, 2)
        self.assertTrue(any(r.startswith("healthz") for r in out["reasons"]))

    def test_exit_3_real_divergence(self):
        """真 bare 仓分叉造形 → exit 3（现役 _preflight_bare_sync 语义原样）。"""
        bare = self.tmp / "bare.git"
        _git("init", "--bare", "-b", "dev", str(bare))
        _git("remote", "add", "sg-bare", str(bare), cwd=self.repo)
        _git("push", "sg-bare", "dev", cwd=self.repo)
        # bare 侧前进一笔（经第二 clone 模拟他机推送）
        clone2 = self.tmp / "clone2"
        _git("clone", str(bare), str(clone2))
        _git("config", "user.name", "other", cwd=clone2)
        _git("config", "user.email", "other@example.com", cwd=clone2)
        (clone2 / "remote.txt").write_text("from other\n", encoding="utf-8")
        _git("add", "-A", cwd=clone2)
        _git("commit", "-m", "remote advance", cwd=clone2)
        _git("push", "origin", "HEAD:dev", cwd=clone2)
        # 本地侧前进一笔（不 pull）→ 分叉
        (self.repo / "local.txt").write_text("local\n", encoding="utf-8")
        _git("add", "-A", cwd=self.repo)
        _git("commit", "-m", "local advance", cwd=self.repo)

        code, out = run_preflight(make_args(
            repo=str(self.repo), daemon_url=self._healthz_ok(), expected_host=None,
            no_diverge=False,
        ), today=date(2026, 11, 15))
        self.assertEqual(code, 3)
        self.assertTrue(any(r.startswith("diverge") for r in out["reasons"]))
        rb = out["assertions"]["diverge"].get("readback", {})
        self.assertEqual(rb.get("verdict"), "diverged")

    def test_exit_0_no_diverge_with_synced_bare(self):
        """本地与 bare 同步（left=0）→ 分叉门放行 → 全绿 exit 0。"""
        bare = self.tmp / "bare.git"
        _git("init", "--bare", "-b", "dev", str(bare))
        _git("remote", "add", "sg-bare", str(bare), cwd=self.repo)
        _git("push", "sg-bare", "dev", cwd=self.repo)
        code, out = run_preflight(make_args(
            repo=str(self.repo), daemon_url=self._healthz_ok(), expected_host=None,
            no_diverge=False,
        ), today=date(2026, 11, 15))
        self.assertEqual(code, 0)
        rb = out["assertions"]["diverge"].get("readback", {})
        self.assertEqual(rb.get("verdict"), "synced")


if __name__ == "__main__":
    unittest.main()


# ── 等待语义轮间门案族（notice-202·CTO 荐案③主形·2026-11-18 SDE 随卷） ──

from runtime.cognition.preflight import check_ceo_ruling


class CeoRulingGateTest(unittest.TestCase):
    """check_ceo_ruling 三态+skip+3 天催办案族（absent/continue/terminate/坏卷）。"""

    def _mk_runs(self, root: Path, run_name: str = "shift-W46-test",
                 with_preflight: bool = True,
                 ruling: dict | None = None,
                 age_days: float | None = None,
                 full_run: bool = True) -> Path:
        rd = root / run_name
        rd.mkdir(parents=True, exist_ok=True)
        if with_preflight:
            (rd / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
        if full_run:
            # F3 语义精化（2026-11-19·ns4 第二拍实锚）：「上轮」候选=链毕完整轮
            # （close.json 在）——案 fixture 随精化勘正（完整轮+裁决缺席态语义）。
            (rd / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
        if ruling is not None:
            # DP-030 三绑形：缺省补 run_id=目录名/round_count=1（旧件案显式用 _legacy=True 另造）
            doc = {"run_id": run_name, "round_count": 1,
                   "signed_at": "2026-11-18T00:00:00Z", **ruling}
            (rd / "ceo-ruling.json").write_text(json.dumps(doc), encoding="utf-8")
        if age_days is not None:
            import os as _os
            ts = time.time() - age_days * 86400
            _os.utime(rd / "preflight.json", (ts, ts))
        return rd

    def test_skip_when_no_runs_root(self) -> None:
        r = check_ceo_ruling(None)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "skip")

    def test_skip_when_root_missing(self) -> None:
        r = check_ceo_ruling("/tmp/definitely-not-here-8f3d21")
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "skip")

    def test_absent_awaiting_ruling(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), ruling=None)
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-ruling")
            self.assertIn("fail-closed", r["detail"])
            self.assertNotIn("escalated", r)

    def test_absent_over_72h_escalates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), age_days=4.0)
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-ruling")
            self.assertTrue(r.get("escalated"))
            self.assertGreater(r.get("prev_run_age_h", 0), 72)

    def test_continue_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), ruling={
                "decision": "continue", "ruling_ref": "notice-202",
                "signed_at": "2026-11-18T00:00:00Z"})
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertTrue(r["ok"])
            self.assertEqual(r["state"], "continue")
            self.assertEqual(r["ruling_ref"], "notice-202")

    def test_terminate_gate_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), ruling={
                "decision": "terminate", "ruling_ref": "X",
                "signed_at": "2026-11-18T00:00:00Z"})
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "terminated")

    def test_bad_decision_conservative_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), ruling={"decision": "maybe"})
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-ruling")

    def test_unparsable_ruling_conservative_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = self._mk_runs(Path(td))
            (rd / "ceo-ruling.json").write_text("{ broken", encoding="utf-8")
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-ruling")

    def test_latest_prev_run_selected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), run_name="shift-W46-old", ruling={
                "decision": "terminate", "ruling_ref": "old"})
            time.sleep(0.05)
            self._mk_runs(Path(td), run_name="shift-W46-new", ruling={
                "decision": "continue", "ruling_ref": "new"})
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertEqual(r["state"], "continue")  # mtime 最新=上轮
            self.assertEqual(r["prev_run_dir"], "shift-W46-new")

    def test_current_run_dir_naturally_excluded(self) -> None:
        """本轮 run_dir（无 preflight 产物·payload 前建空壳）自然排除钉。"""
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), ruling={
                "decision": "continue", "ruling_ref": "prev"})
            time.sleep(0.05)
            (Path(td) / "shift-W46-current").mkdir()  # 本轮空壳（零 preflight）
            r = check_ceo_ruling(td, now_ts=datetime.now(timezone.utc))
            self.assertEqual(r["state"], "continue")
            self.assertEqual(r["prev_run_dir"], "shift-W46-test")


class CeoRulingGateEmptyShellTest(unittest.TestCase):
    """空壳排除钉（ns4 首拍实锚 2026-11-18·F2 面）：shell stdout 重定向提前
    创建的零字节 pf=本轮进程壳——gate 排除（size>0 过滤）·真跑轮恒非空。"""

    def test_empty_shell_pf_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # 上轮：真跑轮（非空 pf+close 毕形+continue 裁决）
            prev = root / "shift-W46-prev"
            prev.mkdir()
            (prev / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (prev / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (prev / "ceo-ruling.json").write_text(
                json.dumps({"decision": "continue", "ruling_ref": "n", "run_id": "shift-W46-prev", "round_count": 1, "signed_at": "2026-11-18T00:00:00Z"}),
                encoding="utf-8")
            # 本轮：shell 空壳（零字节 pf·gate 跑时点形）
            cur = root / "shift-W46-current"
            cur.mkdir()
            (cur / "preflight.json").write_text("", encoding="utf-8")
            r = check_ceo_ruling(str(root), now_ts=datetime.now(timezone.utc))
            self.assertTrue(r["ok"])
            self.assertEqual(r["state"], "continue")
            self.assertEqual(r["prev_run_dir"], "shift-W46-prev")


class CeoRulingGatePartialRunTest(unittest.TestCase):
    """残拍排除钉（ns4 第二拍实锚·F3 面）：awaiting 拍（pf 落卷后链停·零
    close.json）非完整轮——gate prev 候选排除（滚雪球根消·真轮=close 毕形）。"""

    def test_partial_run_excluded_full_run_selected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # 完整轮（链毕形·continue 裁决）
            full = root / "shift-W46-full"
            full.mkdir()
            (full / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (full / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (full / "ceo-ruling.json").write_text(
                json.dumps({"decision": "continue", "ruling_ref": "n", "run_id": "shift-W46-full", "round_count": 1, "signed_at": "2026-11-18T00:00:00Z"}),
                encoding="utf-8")
            # 残拍（awaiting 拍·pf+manifest 两件族零 close）
            part = root / "shift-W46-partial"
            part.mkdir()
            (part / "preflight.json").write_text(
                '{"verdict": "awaiting-ruling", "exit_code": 4}', encoding="utf-8")
            (part / "manifest.json").write_text('{"run_id": "x"}', encoding="utf-8")
            r = check_ceo_ruling(str(root), now_ts=datetime.now(timezone.utc))
            self.assertTrue(r["ok"])
            self.assertEqual(r["state"], "continue")
            self.assertEqual(r["prev_run_dir"], "shift-W46-full")

    def test_no_full_run_skips(self) -> None:
        """全残拍场（零完整轮）→skip 注（首拍/清场面·零误判）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            part = root / "shift-W46-partial"
            part.mkdir()
            (part / "preflight.json").write_text('{"verdict": "awaiting-ruling"}',
                                                 encoding="utf-8")
            r = check_ceo_ruling(str(root), now_ts=datetime.now(timezone.utc))
            self.assertTrue(r["ok"])
            self.assertEqual(r["state"], "skip")


class AgentSupplyCheckTest(unittest.TestCase):
    """②供给断言族案族（notice-214 款一·2026-11-19·CTO root-cause 衔接）。

    分层红绿直证（mock 形零真网络）：supply_ok 绿/supply_exhausted 红（ns4
    探针实锚同型）/call_failed 红/empty_output 保守红——fail-fast 拦截语义。
    """

    def _probe_with(self, events) -> dict:
        import tempfile
        from runtime.cognition.agent_supply_check import probe_agent_supply
        resp = {"ok": True, "turns": "completed", "events": events}
        with tempfile.TemporaryDirectory() as td:
            fp = Path(td) / "resp.json"
            fp.write_text(json.dumps(resp), encoding="utf-8")
            data = fp.read_bytes()  # 即时读（with 内·temp 退出即删面）

        class FakeResp:
            def read(self):
                return data

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with mock.patch(
            "runtime.cognition.agent_supply_check.urllib.request.urlopen",
            return_value=FakeResp(),
        ):
            with mock.patch(
                "runtime.cognition.agent_supply_check.urllib.request.Request",
            ):
                return probe_agent_supply(endpoint="http://probe", token="t")

    def test_supply_ok_green(self) -> None:
        events = [{"type": "content_delta", "delta": '{"supply": "ok"}'}]
        r = self._probe_with(events)
        self.assertTrue(r["ok"])
        self.assertEqual(r["layer"], "supply_ok")

    def test_supply_exhausted_red(self) -> None:
        events = [{"type": "error",
                   "message": "All fallback models exhausted for deepseek-v4-pro. Please try again later."}]
        r = self._probe_with(events)
        self.assertFalse(r["ok"])
        self.assertEqual(r["layer"], "supply_exhausted")

    def test_empty_output_conservative_red(self) -> None:
        r = self._probe_with([])
        self.assertFalse(r["ok"])
        self.assertEqual(r["layer"], "empty_output")


class ModelSupplyProbeTest(unittest.TestCase):
    """修 C 供给探针断言单测（notice-219·A2-2 同构·mock 面·零活体调用）。"""

    def _probe_with_events(self, events, token="tok"):
        from runtime.cognition import preflight as pf

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                import json as _j
                return _j.dumps({"ok": True, "events": events}).encode("utf-8")

        with mock.patch.object(pf.urllib.request, "urlopen", return_value=FakeResp()):
            with mock.patch.dict(os.environ, {"TRIRMC_INTERNAL_TOKEN": token}):
                return pf.check_model_supply("http://127.0.0.1:8710/internal/v1/agent")

    def test_supply_green_done_with_delta(self) -> None:
        events = [
            {"type": "loop_start", "model": "glm-5.3-flash"},
            {"type": "content_delta", "delta": "ok"},
            {"type": "loop_end", "reason": "done"},
        ]
        r = self._probe_with_events(events)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "supply-green")
        self.assertEqual(r["model"], "glm-5.3-flash")

    def test_supply_red_loop_error(self) -> None:
        events = [
            {"type": "loop_start", "model": "deepseek-v4-pro"},
            {"type": "error", "message": "All fallback models exhausted"},
            {"type": "loop_end", "reason": "error"},
        ]
        r = self._probe_with_events(events)
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "supply-red")

    def test_supply_red_zero_delta_not_green(self) -> None:
        events = [{"type": "loop_start", "model": "m"}, {"type": "loop_end", "reason": "done"}]
        r = self._probe_with_events(events)
        self.assertFalse(r["ok"])  # done 但零 delta=非绿（防零内容假绿）

    def test_probe_exception_fail_closed_red(self) -> None:
        from runtime.cognition import preflight as pf

        with mock.patch.object(pf.urllib.request, "urlopen", side_effect=OSError("conn refused")):
            with mock.patch.dict(os.environ, {"TRIRMC_INTERNAL_TOKEN": "tok"}):
                r = pf.check_model_supply("http://127.0.0.1:9/internal/v1/agent")
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "supply-red")

    def test_no_token_skip_not_red(self) -> None:
        from runtime.cognition import preflight as pf

        env = {k: v for k, v in os.environ.items() if k != "TRIRMC_INTERNAL_TOKEN"}
        with mock.patch.dict(os.environ, env, clear=True):
            r = pf.check_model_supply("http://127.0.0.1:8710/internal/v1/agent")
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "skip-no-token")
