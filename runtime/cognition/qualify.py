"""FADE-001 要点②·阶段 2: Agent qualify 载体资格段（cto-phase2-qualify-tech-plan.md §二）。

五资格断言（执行侧资格面·触发闸 preflight 放行后、迁移器接棒前——判「这个执行
环境有没有资格跑迁移」，与「这一拍该不该跑」（preflight 语义）分层）：

  1. 执行身份     — getpass.getuser() 对期望值比对（默认 fleet·env 覆盖
                    TRICO_QUALIFY_EXPECTED_USER·--skip-identity 为 dev escape）
                    ——演练段第一拍 root 身份错位实锚=本段存在价值实证
                    （非 fleet 身份跑=dubious ownership 前兆+notify 读不到
                    →告警链全 render_only 静默死形态）。
  2. run dir 可写 — RUN_DIR probe 写+删（落卷面不可写=全链读数哑卷）。
  3. git 身份在位 — git config user.name/user.email 非空（迁移 commit 身份；
                    值面零回显只判 nonempty）。
  4. 告警凭据在位 — notify config（~/.trimetaverse/notify.json 的
                    smtp.host/smtp.pass）或 env 回退（NOTIFY_SMTP_* /
                    WEEKLY_SHIFT_SMTP_*·与 runtime.cognition.notify 同
                    precedence）nonempty（bool 面·D-46 零回显）——告警链
                    资格前验：凭据缺失=拦截时告警发不出=静默死
                    （P1 部署段凭据后置装配教训反推·把「告警可发」变成
                    run 前资格）。
  5. 磁头余量     — repo 所在卷剩余 ≥ MIN_FREE_MB（默认 500·联审 A 件：
                    实测锚随施工毕报供读数·env 覆盖 TRICO_QUALIFY_MIN_FREE_MB
                    可后调）。

边界（P1 已落面不复检）：8710 healthz 已前移触发段（preflight 断言 4·触发侧
切片）——本模块零重复探针（单点探针防双告警）。

退出码（与 preflight 同族·bash 消费面一致）：
  0 = 五断言全过 → 继续（交棒迁移器）
  2 = 任一资格拦 → 本拍不执行（qualify.json 落卷·trap 告警承担外发）

输出：单份 JSON 到 stdout（bash 重定向落 $RUN_DIR/qualify.json）——
verdict / exit_code / assertions 五读数 / qualify_version / check_time。

调用形（payload vB 三序）：
  python3 -m runtime.cognition.qualify --run-dir $RUN_DIR

发现 28 勘修知情注记（2026-11-14 γ 施工·CEO 13:59:49 裁令·本席零行为改动）：
本件=G 系链供形件（五断言读数被段 6 score_engine G 族消费面邻接）——同链段 5
verify strict 对表域经发现 28 勘修改「旧周 trees/ 目录存在性」（原地封存语义·
原形=to 周 OP index 并集与迁移执行域零机械联动·首拍空壳 index 必炸——CTO
review 卷 §二段 5 处置 d 定谳）。本件五断言面（identity/run_dir/git_identity/
alert_credentials/disk_free）零触零改动·注记纯链路面一致知情（check 产物键名
migrate_vs_index 保持=score_engine._judge_g 消费面契约）。
"""

from __future__ import annotations

import argparse
import json as _json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:  # getpass 在奇异宿主缺 os.environ 登录名时才可能炸——保守 import
    import getpass
except ImportError:  # pragma: no cover
    getpass = None  # type: ignore[assignment]

QUALIFY_VERSION = "1.0.0"

DEFAULT_EXPECTED_USER = "fleet"
DEFAULT_MIN_FREE_MB = 500
DEFAULT_DAEMON_INDEPENDENT = True  # 资格面全本地静态可验·零网络探针（边界声明）


# ── 断言族（各返回 reading dict·ok+读数+失败 reason） ────────────────────


def check_identity(expected_user: str | None) -> dict:
    """执行身份断言——非 fleet 身份=属主错位前兆（演练第一拍实锚）。"""
    try:
        actual = getpass.getuser() if getpass is not None else ""
    except Exception as e:  # noqa: BLE001 — 取不到身份同拦
        return {"ok": False, "reason": f"getuser failed: {type(e).__name__}: {e}"}
    if not expected_user:
        return {
            "ok": True,
            "skipped": True,
            "actual": actual,
            "reason": "no expected-user configured（dev escape·部署面必配）",
        }
    reading = {"ok": actual == expected_user, "actual": actual, "expected": expected_user}
    if not reading["ok"]:
        reading["reason"] = (
            f"identity mismatch: running as {actual!r}, expected {expected_user!r}"
            "（属主错位前兆·dubious ownership/notify 读不到族）"
        )
    return reading


def check_run_dir(run_dir: Path) -> dict:
    """run dir 可写断言——probe 写+删（落卷面不可写=全链读数哑卷）。"""
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        probe = run_dir / ".qualify-probe"
        probe.write_text("probe\n", encoding="utf-8")
        probe.unlink()
        return {"ok": True, "run_dir": str(run_dir)}
    except Exception as e:  # noqa: BLE001 — mkdir/touch/unlink 任一败同拦
        return {
            "ok": False,
            "run_dir": str(run_dir),
            "reason": f"run dir not writable: {type(e).__name__}: {e}",
        }


def check_git_identity(repo: Path) -> dict:
    """git commit 身份在位断言——值面零回显只判 nonempty（D-46 同族）。"""
    try:
        name = subprocess.run(
            ["git", "-C", str(repo), "config", "user.name"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        email = subprocess.run(
            ["git", "-C", str(repo), "config", "user.email"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
    except Exception as e:  # noqa: BLE001 — git 缺席/超时同拦
        return {"ok": False, "reason": f"git config probe failed: {type(e).__name__}: {e}"}
    reading = {"ok": bool(name) and bool(email), "has_name": bool(name), "has_email": bool(email)}
    if not reading["ok"]:
        reading["reason"] = "git user.name/user.email not fully configured（迁移 commit 段必败前兆）"
    return reading


def check_alert_credentials(config_path: Path | None = None) -> dict:
    """告警凭据在位断言——notify.py 同 precedence（config > NOTIFY_SMTP_* >
    WEEKLY_SHIFT_SMTP_*）·bool 面 zero-echo（D-46）。

    凭据缺失=拦截时告警发不出=静默死——把「告警可发」变成 run 前资格。
    """
    p = config_path or _default_notify_config()
    cfg: dict = {}
    if p.is_file():
        try:
            loaded = _json.loads(p.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg = loaded
        except Exception:  # noqa: BLE001 — 坏 config=视为无 config·env 回退兜底
            cfg = {}
    smtp = cfg.get("smtp", {}) if isinstance(cfg.get("smtp", {}), dict) else {}

    def _has(*candidates: str | None) -> bool:
        return any(c and str(c).strip() for c in candidates)

    has_host = _has(smtp.get("host"), os.environ.get("NOTIFY_SMTP_HOST"),
                    os.environ.get("WEEKLY_SHIFT_SMTP_HOST"))
    has_pass = _has(smtp.get("pass"), os.environ.get("NOTIFY_SMTP_PASS"),
                    os.environ.get("WEEKLY_SHIFT_SMTP_PASS"))
    ok = has_host and has_pass
    reading = {"ok": ok, "has_host": has_host, "has_pass": has_pass, "config_found": p.is_file()}
    if not ok:
        reading["reason"] = (
            "alert credentials not resolvable（config smtp.host/pass 或 "
            "NOTIFY_SMTP_HOST/PASS env·缺=拦截时告警发不出=静默死）"
        )
    return reading


def check_disk_free(path: Path, min_free_mb: int) -> dict:
    """磁头余量断言——迁移 tee 落盘+git 对象写中途满盘=半提交态·拦。"""
    try:
        usage = shutil.disk_usage(path)
        free_mb = int(usage.free // (1024 * 1024))
        reading = {"ok": free_mb >= min_free_mb, "free_mb": free_mb, "min_free_mb": min_free_mb}
        if not reading["ok"]:
            reading["reason"] = f"low disk: {free_mb}MB free < {min_free_mb}MB required"
        return reading
    except Exception as e:  # noqa: BLE001 — 卷不可探同拦
        return {"ok": False, "path": str(path), "reason": f"{type(e).__name__}: {e}"}


# ── 主入口 ─────────────────────────────────────────────────────


def _default_notify_config() -> Path:
    env_path = os.environ.get("NOTIFY_CONFIG")
    if env_path:
        return Path(env_path)
    home = Path.home()
    return home / ".trimetaverse" / "notify.json"


def run_qualify(args: argparse.Namespace) -> tuple[int, dict]:
    """执行全部资格断言并返回 (exit_code, output dict)。"""
    repo = Path(args.repo)
    run_dir = Path(args.run_dir)

    readings = {
        "identity": check_identity(None if args.skip_identity else args.expected_user),
        "run_dir": check_run_dir(run_dir),
        "git_identity": check_git_identity(repo),
        "alert_credentials": check_alert_credentials(
            Path(args.notify_config) if args.notify_config else None
        ),
        "disk_free": check_disk_free(
            repo, args.min_free_mb
            if args.min_free_mb is not None
            else int(os.environ.get("TRICO_QUALIFY_MIN_FREE_MB", DEFAULT_MIN_FREE_MB))
        ),
    }

    reasons = []
    for name, r in readings.items():
        if not r.get("ok"):
            reasons.append(f"{name}: {r.get('reason', 'failed')}")

    exit_code = 2 if reasons else 0
    out = {
        "qualify_version": QUALIFY_VERSION,
        "verdict": "pass" if exit_code == 0 else "fail",
        "exit_code": exit_code,
        "reasons": reasons,
        "assertions": readings,
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    return exit_code, out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 2 载体资格段（五断言·薄壳）")
    p.add_argument("--run-dir", required=True, help="本拍 run 目录（payload 铸形段传入）")
    p.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument(
        "--expected-user",
        default=os.environ.get("TRICO_QUALIFY_EXPECTED_USER", DEFAULT_EXPECTED_USER),
    )
    p.add_argument("--skip-identity", action="store_true", help="dev escape: 跳过身份断言")
    p.add_argument("--notify-config", default=None, help="notify config 路径覆盖（单测用）")
    p.add_argument("--min-free-mb", type=int, default=None, help="磁盘余量阈值覆盖（默认 env/500）")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    exit_code, out = run_qualify(args)
    print(_json.dumps(out, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
