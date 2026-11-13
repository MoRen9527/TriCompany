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
import subprocess
import threading
import unittest
from datetime import date
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
