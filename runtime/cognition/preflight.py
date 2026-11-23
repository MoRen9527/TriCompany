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
    today: date,
    from_week: str,
    to_week: str,
    start_date: str,
    loop_window: bool = False,
) -> dict:
    # REGR week_math 双场景形（BOD 裁 b+c 混合·2026-11-16）：
    # ①loop 进化轮（--loop-window 标记携带）→ 周日硬门豁免（法源=CEO 23:55 令
    #   「进化循环不限周日·W47 续跑」），run_dir 归属周按实际时点注记防混；
    # ②真实周迁移（cron 23:50 周日）→ 周日门照旧（防线语义零改动，缺标记即硬门）。
    computed = compute_week_shift_tokens(today)
    is_sunday = today.isoweekday() == 7
    expected = {"from_week": from_week, "to_week": to_week, "start_date": start_date}
    tokens_match = computed == expected
    if loop_window:
        reading = {
            "ok": tokens_match,
            "mode": "loop-window",
            "sunday_gate": "exempted(loop)",
            "sunday_gate_note": "real cron Sunday gate unchanged",
            "run_dir_week_note": f"loop-run 实际时点 {today.isoformat()}（归属周按此时点注记防混）",
            "trigger_day_is_sunday": is_sunday,
            "computed": computed,
            "expected": expected,
        }
        if not tokens_match:
            reading["reason"] = (
                f"week tokens mismatch: computed {computed} vs passed {expected}"
            )
        return reading
    reading = {
        "ok": is_sunday and tokens_match,
        "mode": "cron-sunday",
        "sunday_gate": "enforced",
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


# ── 等待语义轮间门（notice-202·CTO 荐案③主形·2026-11-18） ──────────────────

_ESCALATE_AFTER_H = 72  # 3 天无裁决→升级催办（BOD 缺位缓存协议形·挂起保持不自行推进）


def check_ceo_ruling(runs_root: str | None, now_ts: datetime | None = None,
                      current_run_dir: str | None = None) -> dict:
    """轮间裁决门（等待语义·轮间分离形）——读上轮 run_dir/ceo-ruling.json 三态。

    裁决真值源=签批件落卷（CTO 卷 c 段共同前提）：run_dir/ceo-ruling.json
    {decision: continue|terminate, ruling_ref, signed_at}——值席经 BOD 通道
    落卷·sha 留痕（值席运行义务·本席零代笔）。

    三态分支（notice-202 定谳）：
      absent    → awaiting-ruling skip（ok=False·exit 4——cron 下窗自然再探=
                  轮间轮询·候裁不超时 fail-closed 无裁决不进下轮）；
                  上轮 run 时点距今 >72h→升级催办 notify（_notify_blocking
                  never-raises·零炸段——BOD 缺位缓存协议形）
      continue  → ok=True（本轮照跑·carry_over 承接）
      terminate → ok=False·state=terminated（exit 5——job 停用面=值席执行
                  cron disable·preflight 如实落卷）
      skip 形   → runs_root 缺/目录缺/无已跑轮=gate skip 注 ok=True（可选 gate
                  向后兼容——旧宿主/单测面零波及）

    上轮 run_dir 解析：runs_root 下含 preflight.json 的 run_dir 中 mtime 最新
    （本轮自身 run_dir 除外——payload 建目录在 preflight 前·其内无 preflight
    产物=自然排除）。
    """
    reading: dict = {"ok": True, "state": "skip", "detail": ""}
    if not runs_root:
        reading["detail"] = "no runs_root（可选 gate 缺省 skip·向后兼容）"
        return reading
    root = Path(runs_root)
    if not root.is_dir():
        reading["detail"] = f"runs_root not found: {root}（skip 注）"
        return reading
    # DP-030（§六 A·SDE 新发现）：prev 解析**显式排除本轮自身 run_dir**（旧形靠空壳瞬间
    # 自然排除——轮 3+ 若前轮件仍在=自指误判风险）。
    _self_name = Path(current_run_dir).name if current_run_dir else None
    candidates = []
    for d in root.iterdir():
        if _self_name and d.name == _self_name:
            continue
        pf = d / "preflight.json"
        close = d / "close.json"
        if (d.is_dir() and pf.is_file() and pf.stat().st_size > 0
                and close.is_file()):
            # 空壳排除（ns4 首拍实锚 2026-11-18·F2 面）：shell stdout 重定向在
            # preflight 进程启动瞬间即创建空 pf——零字节 pf=本轮自身进程壳——
            # size>0 过滤。
            # 残拍排除（ns4 第二拍实锚·F3 面）：awaiting 拍=pf 落卷后链停（零
            # close.json）——非完整轮非裁决对象轮；下拍读它=残拍链滚雪球（每
            # 误判拍又成下拍 prev）。close.json 在=链毕完整轮=「上轮」语义
            # 正身（真跑轮七段全毕必落 close）。
            try:
                # 排序/时点基准=pf mtime（上轮跑完时点·目录 mtime=子项增删面不作为候裁时长基准）
                candidates.append((pf.stat().st_mtime, d))
            except OSError:
                continue
    if not candidates:
        reading["detail"] = "no previous run（首拍/空 runs·skip 注）"
        return reading
    candidates.sort()
    prev_dir = candidates[-1][1]
    reading["prev_run_dir"] = prev_dir.name
    ruling_path = prev_dir / "ceo-ruling.json"
    if not ruling_path.is_file():
        reading["state"] = "awaiting-ruling"
        reading["ok"] = False
        age_h = None
        if now_ts is None:
            now_ts = datetime.now(timezone.utc)
        try:
            mtime = datetime.fromtimestamp(candidates[-1][0], tz=timezone.utc)
            age_h = round((now_ts - mtime).total_seconds() / 3600, 1)
        except (OSError, ValueError, OverflowError):
            pass
        reading["prev_run_age_h"] = age_h
        reading["detail"] = (
            f"ceo-ruling.json absent in {prev_dir.name}（awaiting-ruling·"
            "候裁不超时 fail-closed 无裁决不进下轮·cron 下窗再探）"
        )
        if age_h is not None and age_h > _ESCALATE_AFTER_H:
            reading["escalated"] = True
            reading["detail"] += f"·{age_h}h>72h 升级催办 notify（挂起保持不自行推进）"
            try:
                from runtime.cognition.weekly_plane_shift import _notify_blocking
                to = [x.strip() for x in (os.environ.get(
                    "TRICO_RULING_ESCALATE_TO", "").split(",")) if x.strip()]
                failures = _notify_blocking(
                    subject="[preflight] ceo-ruling 候裁超 3 天升级催办",
                    body=f"上轮 run={prev_dir.name} ceo-ruling.json 缺席 "
                         f"{age_h}h（>72h）——轮间门 awaiting-ruling 挂起保持"
                         "·候 CEO 裁决落卷（值席经 BOD 通道·sha 留痕）",
                    to=to, context_id=f"ruling-escalate-{prev_dir.name}",
                )
                reading["escalate_notify_failures"] = failures
            except Exception as e:  # noqa: BLE001 — 催办面零炸段
                reading["escalate_notify_failures"] = [
                    {"status": "escalate_path_failed", "error": str(e)[:200]}]
        return reading
    try:
        ruling = _json.loads(ruling_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 签批件坏=保守拦（不硬跑）
        reading["state"] = "awaiting-ruling"
        reading["ok"] = False
        reading["detail"] = f"ceo-ruling.json unparsable: {e}（保守拦·候值席勘正）"
        return reading
    decision = str(ruling.get("decision", "")).strip().lower()
    reading["ruling_ref"] = ruling.get("ruling_ref")
    reading["signed_at"] = ruling.get("signed_at")
    # ── DP-030 七件（主修面·CTO 2026-11-23）：三绑 + 一纸一轮 + 旧件拒 ──
    _rid = str(ruling.get("run_id") or "")
    _rc = ruling.get("round_count")
    _sig = ruling.get("signed_at")
    if not _rid or _rc is None or not _sig:
        # ⑤ 旧件（无 run_id/round_count/signed_at）→ absent 不认（旧 continue 作废需重签）
        reading["state"] = "awaiting-ruling"
        reading["ok"] = False
        reading["detail"] = ("旧 ruling 件缺 run_id/round_count/signed_at——旧 continue 作废需重签"
                            "（DP-030 三绑·resume4 件/ignite 件均作废）")
        return reading
    if _rid != prev_dir.name:
        # ① 跨 run 件拒（件须属上轮 run_dir 正身）
        reading["state"] = "awaiting-ruling"
        reading["ok"] = False
        reading["detail"] = (f"跨 run 件拒：件 run_id={_rid!r} ≠ prev={prev_dir.name!r}"
                            "（DP-030 三绑）")
        return reading
    _consumed_marker = prev_dir / ".ceo-ruling-consumed.json"
    if _consumed_marker.is_file():
        # ② 一纸一轮：已消费=absent fail-closed（绝不放行）
        reading["state"] = "awaiting-ruling"
        reading["ok"] = False
        reading["detail"] = (f"已消费件拒：{prev_dir.name} 的 ruling 已被消费"
                            f"（{_consumed_marker.name}·一纸一轮·DP-030）")
        return reading
    if decision == "continue":
        reading["state"] = "continue"
        reading["ok"] = True
        reading["detail"] = f"ruling=continue（{prev_dir.name}·本轮照跑 carry_over 承接）"
        try:
            _consumed_marker.write_text(_json.dumps({
                "consumed_by": _self_name,
                "consumed_at": datetime.now(timezone.utc).isoformat(),
                "ruling_run_id": _rid, "round_count": _rc, "signed_at": _sig,
            }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        except OSError as _e:  # 写戳失败=保守拦（一纸一轮不可降级）
            reading["state"] = "awaiting-ruling"
            reading["ok"] = False
            reading["detail"] = f"消费戳写入失败（保守拦·DP-030）: {_e}"
            return reading
        return reading
    if decision == "terminate":
        reading["state"] = "terminated"
        reading["ok"] = False
        reading["detail"] = (
            f"ruling=terminate（{prev_dir.name}·exit 5——job 停用面=值席执行 "
            "cron disable·preflight 落 terminated 态）"
        )
        return reading
    reading["state"] = "awaiting-ruling"
    reading["ok"] = False
    reading["detail"] = f"decision={decision!r} 非二值域（保守拦·候值席勘正）"
    return reading


def check_model_supply(agent_url: str, timeout_s: int = 90) -> dict:
    """供给探针断言（notice-219 修 C·A2-2 供给面同构·A 线第三项并轨归一形）。

    一发活体探针：零 override POST 8710 agent（maxTurns=1·单 turn 单答）——
    loop_end reason=done 且 content_delta 流=供给绿；其余（error/异常/超时/
    无 token）=供给红（断言族语义·红=如实·零炸段 never raises）。
    单值源=在役 8710 agent 面（与 trimodel/轮间门无交叉——判定面独立）。
    """
    reading: dict = {"ok": False, "state": "unknown", "detail": ""}
    token = os.environ.get("TRIRMC_INTERNAL_TOKEN", "")
    if not token:
        reading["state"] = "skip-no-token"
        reading["ok"] = True  # 无 token 宿主（dev/单测面）=skip 非红——断言域内在役宿主才判
        reading["detail"] = "TRIRMC_INTERNAL_TOKEN absent（非在役宿主·skip 注）"
        return reading
    body = _json.dumps({
        "messages": [{"role": "user", "content": "reply with the single word ok"}],
        "maxTurns": 1,
    }).encode("utf-8")
    req = urllib.request.Request(
        agent_url, data=body, method="POST",
        headers={"Content-Type": "application/json", "x-internal-token": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            doc = _json.loads(resp.read().decode("utf-8"))
        events = doc.get("events", []) if isinstance(doc, dict) else []
        end_reasons = [e.get("reason") for e in events if e.get("type") == "loop_end"]
        delta_len = sum(len(e.get("delta") or "") for e in events if e.get("type") == "content_delta")
        models = [e.get("model") for e in events if e.get("type") == "loop_start"]
        reading["model"] = models[0] if models else None
        reading["delta_len"] = delta_len
        if end_reasons and end_reasons[-1] == "done" and delta_len > 0:
            reading["ok"] = True
            reading["state"] = "supply-green"
            reading["detail"] = f"供给绿（model={reading['model']}·delta_len={delta_len}）"
        else:
            reading["state"] = "supply-red"
            reading["detail"] = (
                f"供给红（loop_end={end_reasons[-1] if end_reasons else 'none'}·"
                f"delta_len={delta_len}·model={reading['model']}）——供给面败·断言族红"
            )
    except Exception as err:  # noqa: BLE001 — 探针面零炸段（fail-closed 红非炸）
        reading["state"] = "supply-red"
        reading["detail"] = f"供给红（探针异常: {str(err)[:160]}）——断言族红"
    return reading


# ── 主入口 ─────────────────────────────────────────────────────


def run_preflight(args: argparse.Namespace, today: date | None = None) -> tuple[int, dict]:
    """执行全部断言并返回 (exit_code, output dict)。today 可注入（单测）。"""
    today = today or date.today()
    repo = Path(args.repo)

    # loop-window 接缝（REGR 双场景形承载·2026-11-16）：CLI 旗标不在 run 面通道
    # （runJob payload 禁改只透传 force）→ env/marker 双读一次性消费形：
    #   LOOP_WINDOW=1 env 或 <marker-dir>/loop-window.marker 在 → 本轮豁免周日门；
    #   marker 读即删（one-shot）——真实周日 cron 轮无 marker 无 env=周日门原样（防线保）。
    # marker 目录 env=TRICO_LOOP_MARKER_DIR（B 案·CTO 02:05 确认·2026-11-16）：
    #   原读 TRIMC_CONFIG_DIR 系 TriRMC daemon 自身消费键（cron store/log 域语义·同名
    #   撞车——unit 注入实测分叉实锚 2026-11-16），TRICO_ 前缀分域护栏
    #   （同域先例 TRICO_PREFLIGHT_EXPECTED_HOST）；兜底 /var/lib/trimc 语义维持。
    loop_window = bool(getattr(args, "loop_window", False))
    loop_source = "cli" if loop_window else None
    marker_path = Path(os.environ.get("TRICO_LOOP_MARKER_DIR", "/var/lib/trimc")) / "loop-window.marker"
    if not loop_window and os.environ.get("LOOP_WINDOW") == "1":
        loop_window = True
        loop_source = "env"
    if not loop_window and marker_path.exists():
        loop_window = True
        loop_source = "marker"
        try:
            marker_path.unlink()  # one-shot 消费：防信号残留污染真实周日门
        except OSError:
            pass  # 删失败不阻判定（读时已定；残留由下轮再消费，幂等无害）

    readings = {
        "week_math": check_week_math(
            today,
            args.from_week,
            args.to_week,
            args.start_date,
            loop_window=loop_window,
        ),
        "hostname": check_hostname(None if args.skip_hostname else args.expected_host),
        "git_hygiene": check_git_hygiene(repo),
        "healthz": check_healthz(args.daemon_url),
        "diverge": (
            {"ok": True, "skipped": True}
            if args.no_diverge
            else check_diverge(repo, remote=args.diverge_remote)
        ),
        # 等待语义轮间门（notice-202·可选 gate·payload 零改形——CLI 缺省+env 可覆）
        "ceo_ruling": (
            {"ok": True, "state": "skip", "detail": "no-diverge escape 形（dev/test）"}
            if args.no_diverge
            else check_ceo_ruling(getattr(args, 'prev_runs_root', None), current_run_dir=(getattr(args, 'run_dir', '') or None))
        ),
        # 供给探针断言（notice-219 修 C·A2-2 供给面同构·A 线第三项并轨归一形）——
        # 一发活体探针（8710 零 override·maxTurns=1）·供给红=断言红（断言族 exit 2）；
        # TRICO_SUPPLY_PROBE=off 跳过（向后兼容/省调用面·缺省 on）。
        "model_supply": (
            {"ok": True, "state": "skip", "detail": "no-diverge escape 形（dev/test）"}
            if args.no_diverge
            else check_model_supply(
                os.environ.get("TRICO_SUPPLY_AGENT_URL", "http://127.0.0.1:8710/internal/v1/agent"),
                timeout_s=int(os.environ.get("TRICO_SUPPLY_PROBE_TIMEOUT_S", "90")),
            )
        ),
    }

    if loop_source:
        readings["week_math"]["loop_source"] = loop_source
    reasons = []
    for name, r in readings.items():
        if not r.get("ok"):
            reasons.append(f"{name}: {r.get('reason') or r.get('detail', 'failed')}")

    # 退出码优先级：diverge 3（现役）＞ruling 4/5（等待语义轮间门）＞断言族 2
    # ——裁决门先决语义（无裁决不进下轮·terminate 即停）。
    if not readings["diverge"].get("ok"):
        exit_code = 3
    elif readings["ceo_ruling"].get("state") == "terminated":
        exit_code = 5
    elif not readings["ceo_ruling"].get("ok"):
        exit_code = 4
    elif reasons:
        exit_code = 2
    else:
        exit_code = 0

    _VERDICT_BY_EXIT = {4: "awaiting-ruling", 5: "terminated"}
    out = {
        "preflight_version": PREFLIGHT_VERSION,
        "verdict": _VERDICT_BY_EXIT.get(
            exit_code, "pass" if exit_code == 0 else "fail"
        ),
        "exit_code": exit_code,
        "reasons": reasons,
        "assertions": readings,
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    return exit_code, out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 trigger preflight（要点②·薄壳）")
    p.add_argument("--run-dir", default="", help="本轮 run 目录（DP-030 prev 自指显式排除用）")
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
        "--loop-window",
        action="store_true",
        help="loop 进化轮标记：周日门豁免（week_math 双场景形①；真实 cron 迁移禁带此旗——防线语义保持）",
    )
    p.add_argument(
        "--diverge-remote",
        default="origin",
        help="分叉预检 fetch 的 remote 名（默认 origin=TriCompany 检出实名；TriMetaverse 检出显式传 sg-bare）",
    )
    p.add_argument(
        "--prev-runs-root",
        default=os.environ.get("TRICO_PREV_RUNS_ROOT", "/var/lib/trirmc/cron/runs"),
        help="等待语义轮间门·上轮 run 目录根（缺省河源现役位·env "
             "TRICO_PREV_RUNS_ROOT 可覆——payload 零改形；置空串=gate skip）",
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
