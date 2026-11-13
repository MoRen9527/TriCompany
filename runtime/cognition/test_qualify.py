"""qualify.py 单测 — FADE-001 阶段 2（unittest stdlib·零新依赖）。

覆盖（联审 B 件五案对表·五断言五案全覆盖）：
  - check_identity 匹配/错身份注入/skip escape。
  - check_run_dir 可写/probe 不可写注入。
  - check_git_identity 真仓在位/GIT_CONFIG 隔离注入（无 config 仓）。
  - check_alert_credentials config 在位/凭据位隔离（缺文件+env 清）/env 回退/坏 json 兜底。
  - check_disk_free mock 充足/不足/阈值 env 覆盖。
  - run_qualify 端到端退出码（0 全过 / 2 资格拦）。

跑法：cd TriCompany && python -m unittest runtime.cognition.test_qualify -v
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from runtime.cognition.qualify import (
    build_parser,
    check_alert_credentials,
    check_disk_free,
    check_git_identity,
    check_identity,
    check_run_dir,
    run_qualify,
)


def _git(*args: str, cwd: Path | None = None) -> None:
    cmd = ["git", *args]
    if cwd is not None:
        cmd = ["git", "-C", str(cwd), *args]
    import subprocess

    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)


def _git_env_repo(repo: Path, with_identity: bool = True) -> None:
    """真 git 仓最小形（dev 分支+首提交·身份可选=断言 3 隔离注入位）。"""
    repo.mkdir(parents=True, exist_ok=True)
    _git("init", "-b", "dev", cwd=repo)
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    if with_identity:
        _git("config", "user.name", "test", cwd=repo)
        _git("config", "user.email", "test@example.com", cwd=repo)
        _git("commit", "-m", "seed", cwd=repo)
    else:
        # 单次 -c 身份 commit（不落 repo config——check_git_identity 读生效层级
        # local>global>system·repo 无 local 才是隔离注入位）
        _git("-c", "user.name=seed", "-c", "user.email=seed@example.com",
             "commit", "-m", "seed", cwd=repo)


def _write_notify_config(path: Path, host: str | None = "smtp.example", pwd: str | None = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"smtp": {}}
    if host is not None:
        body["smtp"]["host"] = host
    if pwd is not None:
        body["smtp"]["pass"] = pwd
    path.write_text(json.dumps(body), encoding="utf-8")


class IdentityTest(unittest.TestCase):
    def test_match_self_ok(self):
        r = check_identity(getpass.getuser())
        self.assertTrue(r["ok"])

    def test_mismatch_blocked(self):
        """B 件案 1——错身份注入（演练第一拍 root 形）。"""
        r = check_identity("definitely-not-this-user")
        self.assertFalse(r["ok"])
        self.assertIn("mismatch", r["reason"])

    def test_skip_escape(self):
        r = check_identity(None)
        self.assertTrue(r["ok"])
        self.assertTrue(r["skipped"])


class RunDirTest(unittest.TestCase):
    def test_writable_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = check_run_dir(Path(tmp) / "run-x")
            self.assertTrue(r["ok"])

    def test_probe_write_blocked(self):
        """B 件案 2——probe 写失败注入。"""
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(Path, "write_text", side_effect=OSError(13, "denied")):
                r = check_run_dir(Path(tmp) / "run-y")
            self.assertFalse(r["ok"])
            self.assertIn("not writable", r["reason"])


class GitIdentityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="qualify-git-"))

    def test_configured_ok(self):
        repo = self.tmp / "repo"
        _git_env_repo(repo, with_identity=True)
        r = check_git_identity(repo)
        self.assertTrue(r["ok"])
        self.assertTrue(r["has_name"] and r["has_email"])

    def test_unconfigured_blocked(self):
        """B 件案 3——GIT_CONFIG 隔离注入（全层级隔离=无身份形）。

        git config 生效层级 local>global>system——测试宿主有全局身份，
        单靠 repo 无 local 不构成隔离；正形=GIT_CONFIG_GLOBAL/SYSTEM 双指空
        文件（全层级无身份·生产语义=迁移 commit 身份取自生效层级）。
        """
        repo = self.tmp / "bare-config"
        _git_env_repo(repo, with_identity=False)
        empty = self.tmp / "empty-gitconfig"
        empty.write_text("", encoding="utf-8")
        with mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(empty), "GIT_CONFIG_SYSTEM": str(empty),
        }):
            r = check_git_identity(repo)
        self.assertFalse(r["ok"])
        self.assertIn("not fully configured", r["reason"])


class AlertCredentialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="qualify-notify-"))
        # 环境隔离：清 NOTIFY/WEEKLY_SHIFT 键（测试进程内 dict 级）
        env_patcher = mock.patch.dict(
            os.environ,
            {k: "" for k in list(os.environ)
             if k.startswith(("NOTIFY_SMTP_", "WEEKLY_SHIFT_SMTP_"))},
            clear=False,
        )
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

    def test_config_file_ok(self):
        cfg = self.tmp / "notify.json"
        _write_notify_config(cfg)
        r = check_alert_credentials(cfg)
        self.assertTrue(r["ok"])
        self.assertTrue(r["config_found"])

    def test_missing_all_blocked(self):
        """B 件案 4——凭据位隔离（缺文件+env 清）。"""
        r = check_alert_credentials(self.tmp / "absent.json")
        self.assertFalse(r["ok"])
        self.assertIn("not resolvable", r["reason"])

    def test_env_fallback_ok(self):
        with mock.patch.dict(os.environ, {"NOTIFY_SMTP_HOST": "h", "NOTIFY_SMTP_PASS": "p"}):
            r = check_alert_credentials(self.tmp / "absent.json")
        self.assertTrue(r["ok"])
        self.assertFalse(r["config_found"])

    def test_bad_json_env_fallback_ok(self):
        bad = self.tmp / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with mock.patch.dict(os.environ, {"WEEKLY_SHIFT_SMTP_HOST": "h", "NOTIFY_SMTP_PASS": "p"}):
            r = check_alert_credentials(bad)
        self.assertTrue(r["ok"])

    def test_host_only_blocked(self):
        cfg = self.tmp / "partial.json"
        _write_notify_config(cfg, pwd=None)
        r = check_alert_credentials(cfg)
        self.assertFalse(r["ok"])
        self.assertFalse(r["has_pass"])


class DiskFreeTest(unittest.TestCase):
    def test_sufficient_ok(self):
        with mock.patch("runtime.cognition.qualify.shutil.disk_usage",
                        return_value=SimpleNamespace(total=0, used=0, free=2 * 1024**3)):
            r = check_disk_free(Path("/"), 500)
        self.assertTrue(r["ok"])
        self.assertEqual(r["free_mb"], 2048)

    def test_insufficient_blocked(self):
        """B 件案 5——mock 余量不足。"""
        with mock.patch("runtime.cognition.qualify.shutil.disk_usage",
                        return_value=SimpleNamespace(total=0, used=0, free=100 * 1024**2)):
            r = check_disk_free(Path("/"), 500)
        self.assertFalse(r["ok"])
        self.assertIn("low disk", r["reason"])

    def test_env_threshold_override(self):
        with mock.patch("runtime.cognition.qualify.shutil.disk_usage",
                        return_value=SimpleNamespace(total=0, used=0, free=1000 * 1024**2)):
            with mock.patch.dict(os.environ, {"TRICO_QUALIFY_MIN_FREE_MB": "10000"}):
                code, out = run_qualify(make_args(repo="/", run_dir=tempfile.mkdtemp(),
                                                  skip_identity=True, notify_config="absent-probe.json"))
                # 阈值覆盖只影响 disk_free 断言——此处直接查断言读数
                df = out["assertions"]["disk_free"]
        self.assertEqual(df["min_free_mb"], 10000)
        self.assertFalse(df["ok"])


def make_args(**over):
    base = dict(
        run_dir="/nonexistent-qualify-run", repo="/nonexistent",
        expected_user=getpass.getuser(), skip_identity=False,
        notify_config=None, min_free_mb=None,
    )
    base.update(over)
    return argparse.Namespace(**base)


class RunQualifyExitCodesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="qualify-e2e-"))
        self.repo = self.tmp / "repo"
        _git_env_repo(self.repo, with_identity=True)
        self.run_dir = self.tmp / "run"
        self.run_dir.mkdir()
        self.notify_cfg = self.tmp / "notify.json"
        _write_notify_config(self.notify_cfg)
        env_patcher = mock.patch.dict(
            os.environ,
            {k: "" for k in list(os.environ)
             if k.startswith(("NOTIFY_SMTP_", "WEEKLY_SHIFT_SMTP_", "TRICO_QUALIFY_"))},
            clear=False,
        )
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

    def test_exit_0_all_pass(self):
        code, out = run_qualify(make_args(
            repo=str(self.repo), run_dir=str(self.run_dir),
            expected_user=getpass.getuser(), notify_config=str(self.notify_cfg),
        ))
        self.assertEqual(code, 0)
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["reasons"], [])
        self.assertTrue(out["qualify_version"])
        for name in ("identity", "run_dir", "git_identity", "alert_credentials", "disk_free"):
            self.assertTrue(out["assertions"][name]["ok"], name)

    def test_exit_2_identity_blocked(self):
        code, out = run_qualify(make_args(
            repo=str(self.repo), run_dir=str(self.run_dir),
            expected_user="root-wrong", notify_config=str(self.notify_cfg),
        ))
        self.assertEqual(code, 2)
        self.assertTrue(any(r.startswith("identity") for r in out["reasons"]))

    def test_exit_2_credentials_blocked(self):
        code, out = run_qualify(make_args(
            repo=str(self.repo), run_dir=str(self.run_dir),
            expected_user=getpass.getuser(),
            notify_config=str(self.tmp / "absent.json"),
        ))
        self.assertEqual(code, 2)
        self.assertTrue(any(r.startswith("alert_credentials") for r in out["reasons"]))

    def test_argparse_defaults(self):
        args = build_parser().parse_args(["--run-dir", "x"])
        self.assertEqual(args.expected_user, os.environ.get("TRICO_QUALIFY_EXPECTED_USER", "fleet"))
        self.assertIsNone(args.min_free_mb)


if __name__ == "__main__":
    unittest.main()
