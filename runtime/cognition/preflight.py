"""FADE-001 要点②: trigger 段 preflight 薄壳入口（cto-phase1-tech-plan.md §二 终裁）。

四断言 + 算周双闸（γ 主闸；γ 二道闸=weekly_plane_shift.py validate 步旁挂对表断言）：

  1. 算周双闸 γ 主闸  — 触发日必须周日（明天=周一边界断言）+ 三值重算比对
     （week-math 同族语义 python 侧重算·非调 TS——TriRMC command-handler 每拍
     用 computeWeekShiftTokens 展开占位符，本模块同机同时钟重算比对）。
  2. hostname 断言    — socket.gethostname() 对配置常数比对（防 job 误落他机）。
  3. 无进行中 git 操作 — MERGE_HEAD / rebase-merge / rebase-apply 探针 +
     git status --porcelain 对迁移面路径（docs/workflow/operating-records）非空即拦
     （其余路径脏不拦——迁移面残留才是不硬跑的理由）。
  4. 8710 healthz    — 载体 daemon 活性探针（ok!=true 即拦）。
  5. 分叉预检（现役抽取）— weekly_plane_shift._preflight_bare_sync 原样复用
     （import 复用·不复制代码——单点真源防两处分叉）。

退出码语义表（bash 消费面约定·与现役兼容）：
  0 = 全过 → 继续（交棒迁移器）
  2 = 断言族拦（hostname / 工作区脏 / healthz / 算周）→ 本拍不执行
  3 = 分叉拦（现役语义原样）→ 本拍不执行·双址 blocking 告警（现役链承担）
  4 = 保留（现役 notify_failures 语义·本模块零外发——告警由 bash 链尾
      shift_notify_fail 现役链承担，防双重告警）

输出：单份 JSON 到 stdout（bash 重定向落 $RUN_DIR/preflight.json）——
verdict / exit_code / reasons / assertions 五读数 / preflight_version（pull 前
版本知情面）/ check_time。全程无凭据值面回显（D-46）。

调用形（payload 终形）：
  cd /srv/fleet/TriCompany && python3 -m runtime.cognition.preflight \\
      --from W46 --to W47 --start-date 2026-11-16
"""

from __future__ import annotations

import argparse
import json as _json
import os
import socket
import subprocess
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from runtime.cognition.weekly_plane_shift import _preflight_bare_sync

PREFLIGHT_VERSION = "1.0.0"

# 河源执行机主机名（2026-11-13 α 窗活体实锚·Alibaba 实例名）。
# env 覆盖位=TRICO_PREFLIGHT_EXPECTED_HOST（部署面注入·dev 机用 --skip-hostname）。
DEFAULT_EXPECTED_HOST = "iZf8ziw57ydktu77fsld9yZ"
DEFAULT_DAEMON_URL = "http://127.0.0.1:8710/healthz"
MIGRATION_FACE = "docs/workflow/operating-records"


# ── week-math 同族语义（python 重算·对齐 TriRMC week-math.ts） ────────────


def _iso_week_of(d: date) -> int:
    """ISO 8601 周号（含周四规则=isocalendar 标准）。"""
    return d.isocalendar()[1]


def _last_iso_week_of_year(year: int) -> int:
    """该年最后一个 ISO 周（12-28 恒落在其中）。"""
    return date(year, 12, 28).isocalendar()[1]


def compute_week_shift_tokens(today: date) -> dict:
    """week-math 同族重算：toWeek=明天所在 ISO 周·startDate=该周周一·
    fromWeek=toWeek-1（跨年 wrap=上一年 12-28 的 ISO 周）。

    与 TriRMC command-handler 每拍展开语义同源（本机本地日历）——
    正常时三值必一致；错周只现于触发时点挪动（周一~周六），主闸即拦。
    """
    tomorrow = today + timedelta(days=1)
    monday = tomorrow - timedelta(days=tomorrow.isoweekday() - 1)
    to_week = _iso_week_of(monday)
    from_week = to_week - 1
    if from_week < 1:
        from_week = _last_iso_week_of_year(monday.year - 1)
    return {
        "from_week": f"W{from_week:02d}",
        "to_week": f"W{to_week:02d}",
        "start_date": monday.isoformat(),
    }


# ── 断言族（各返回 reading dict·ok+读数+失败 reason） ────────────────────


def check_week_math(
    today: date, from_week: str, to_week: str, start_date: str
) -> dict:
    computed = compute_week_shift_tokens(today)
    is_sunday = today.isoweekday() == 7
    expected = {"from_week": from_week, "to_week": to_week, "start_date": start_date}
    tokens_match = computed == expected
    reading = {
        "ok": is_sunday and tokens_match,
        "trigger_day_is_sunday": is_sunday,
        "computed": computed,
        "expected": expected,
    }
    if not is_sunday:
        reading["reason"] = (
            f"trigger day {today.isoformat()} is not Sunday "
            f"(tomorrow=Monday boundary violated — 时点挪动错周防线)"
        )
    elif not tokens_match:
        reading["reason"] = (
            f"week tokens mismatch: computed {computed} vs passed {expected}"
        )
    return reading


def check_hostname(expected_host: str | None) -> dict:
    actual = socket.gethostname()
    if not expected_host:
        return {
            "ok": True,
            "skipped": True,
            "actual": actual,
            "reason": "no expected-host configured（dev escape·部署面必配）",
        }
    reading = {"ok": actual == expected_host, "actual": actual, "expected": expected_host}
    if not reading["ok"]:
        reading["reason"] = (
            f"hostname mismatch: running on {actual!r}, expected {expected_host!r}"
            "（防 job 误落他机）"
        )
    return reading


def check_git_hygiene(repo: Path) -> dict:
    """无进行中 git 操作 + 迁移面工作区干净（其余路径脏不拦）。"""
    git_dir = repo / ".git"
    if git_dir.is_file():  # worktree 形：.git 为文件指向真 gitdir
        line = git_dir.read_text(encoding="utf-8").strip()
        git_dir = Path(line.split(":", 1)[1].strip()) if line.startswith("gitdir:") else git_dir
    in_progress = []
    for marker in ("MERGE_HEAD",):
        if (git_dir / marker).exists():
            in_progress.append(marker)
    for d in ("rebase-merge", "rebase-apply"):
        if (git_dir / d).is_dir():
            in_progress.append(d + "/")

    dirty = []
    git_err = None
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            git_err = (out.stderr or "").strip()[:200]
        else:
            for line in out.stdout.splitlines():
                path_part = line[3:].strip().strip('"')
                if MIGRATION_FACE in path_part:
                    dirty.append(line)
    except Exception as e:  # noqa: BLE001 — 探针异常同拦
        git_err = f"{type(e).__name__}: {e}"

    ok = not in_progress and not dirty and git_err is None
    reading = {
        "ok": ok,
        "in_progress_ops": in_progress,
        "migration_face_dirty": dirty,
    }
    if git_err is not None:
        reading["ok"] = False
        reading["reason"] = f"git status failed: {git_err}"
    elif in_progress:
        reading["reason"] = f"git operation in progress: {in_progress}（不硬跑）"
    elif dirty:
        reading["reason"] = (
            f"migration face dirty ({len(dirty)} entries — 可能上一轮残留): {dirty[:5]}"
        )
    return reading


def check_healthz(url: str, timeout_s: float = 5.0) -> dict:
    """载体 daemon（TriRMC 8710）活性探针——CEO 勘正 L5 载体资格前移触发段。"""
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            body = _json.loads(resp.read().decode("utf-8"))
        ok = isinstance(body, dict) and body.get("ok") is True
        cron = body.get("cron") if isinstance(body, dict) else None
        reading = {
            "ok": ok,
            "url": url,
            "service": body.get("service") if isinstance(body, dict) else None,
            "cron_enabled": cron.get("enabled") if isinstance(cron, dict) else None,
        }
        if not ok:
            reading["reason"] = f"healthz ok!=true: {body!r}"
        return reading
    except Exception as e:  # noqa: BLE001 — 连接拒/超时/非 JSON 同拦
        return {"ok": False, "url": url, "reason": f"{type(e).__name__}: {e}"}


def check_diverge(repo: Path, remote: str = "sg-bare", branch: str = "dev") -> dict:
    """分叉预检——现役 _preflight_bare_sync 原样复用（异常同拦·现役语义）。"""
    try:
        ok, detail, readback = _preflight_bare_sync(repo, remote=remote, branch=branch)
    except Exception as e:  # noqa: BLE001 — 现役拦截段同语义：异常同拦
        return {"ok": False, "reason": f"preflight_bare_sync raised {type(e).__name__}: {e}"}
    reading = {"ok": bool(ok), "detail": detail}
    if isinstance(readback, dict):
        reading["readback"] = readback
    if not ok:
        reading["reason"] = f"diverged from {remote}/{branch}（候裁不硬跑）: {detail}"
    return reading


# ── 主入口 ─────────────────────────────────────────────────────


def run_preflight(args: argparse.Namespace, today: date | None = None) -> tuple[int, dict]:
    """执行全部断言并返回 (exit_code, output dict)。today 可注入（单测）。"""
    today = today or date.today()
    repo = Path(args.repo)

    readings = {
        "week_math": check_week_math(today, args.from_week, args.to_week, args.start_date),
        "hostname": check_hostname(None if args.skip_hostname else args.expected_host),
        "git_hygiene": check_git_hygiene(repo),
        "healthz": check_healthz(args.daemon_url),
        "diverge": (
            {"ok": True, "skipped": True}
            if args.no_diverge
            else check_diverge(repo, remote=args.diverge_remote)
        ),
    }

    reasons = []
    for name, r in readings.items():
        if not r.get("ok"):
            reasons.append(f"{name}: {r.get('reason', 'failed')}")

    # 分叉拦优先于断言族（现役语义原样——3 比 2 更 actionable）
    if not readings["diverge"].get("ok"):
        exit_code = 3
    elif reasons:
        exit_code = 2
    else:
        exit_code = 0

    out = {
        "preflight_version": PREFLIGHT_VERSION,
        "verdict": "pass" if exit_code == 0 else "fail",
        "exit_code": exit_code,
        "reasons": reasons,
        "assertions": readings,
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    return exit_code, out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 trigger preflight（要点②·薄壳）")
    p.add_argument("--from", dest="from_week", required=True)
    p.add_argument("--to", dest="to_week", required=True)
    p.add_argument("--start-date", required=True, help="New week start date YYYY-MM-DD")
    p.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--daemon-url", default=DEFAULT_DAEMON_URL)
    p.add_argument(
        "--expected-host",
        default=os.environ.get("TRICO_PREFLIGHT_EXPECTED_HOST", DEFAULT_EXPECTED_HOST),
    )
    p.add_argument("--skip-hostname", action="store_true", help="dev escape: 跳过 hostname 断言")
    p.add_argument("--no-diverge", action="store_true", help="dev/test escape: 跳过分叉预检")
    p.add_argument(
        "--diverge-remote",
        default="origin",
        help="分叉预检 fetch 的 remote 名（默认 origin=TriCompany 检出实名；TriMetaverse 检出显式传 sg-bare）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    exit_code, out = run_preflight(args)
    print(_json.dumps(out, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
