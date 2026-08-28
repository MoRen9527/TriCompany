#!/usr/bin/env python3
"""daily_progress_patrol.py — FADE-001 维护项②「每日工作进度」巡检兜底脚本（LG-011）。

设计锚（真源）：
- TriCompany/docs/engineering/fade-registry.md FADE-001 维护项②（节奏重设计 49287fc）：
  主=事件驱动（董事长助理增量即写），辅=定时巡检兜底（本脚本，TriMC cron 每 10 分钟）；
  单写者原则：巡检只补漏（append）不重写；机械门=自上次进度条目后新 commits>0；
  无变化=skip 不产空节；Score CLI 缺口随本脚本一并补齐（Verify=写入后回读自检）。
- TriMC/docs/ops/trimc-cron-plane-shift-runbook.md：服务器 python3.8（禁 3.10+ 语法）、
  runAs fleet、代码修改一律本地发起（本地 → 裸仓 → 舰队克隆）。
- TriMetaverse/docs/workflow/operating-records/<ISO 周>/daily-progress.md：三端持久
  （本地/sg-bare/GitHub）；push 纪律=sg-bare 必达，GitHub 失败不阻塞。

数据边界：`.fade/hub-snapshots/ledger-mirror.md` 为机器本地不入仓（TriMetaverse
.gitignore `.fade/`），服务器巡检不可读——故门限仅用 git commits（与登记册机械门
「自上次进度条目后新 commits>0」一致），registry 变化取 TriCompany 舰队克隆的
fade-registry.md（版本行 + 当日 registry 提交），均为确定性收集，无 LLM。
设计史：ledger-mirror mtime 门限分支曾入 49287fc 设计，2026-08-28 升档联审裁定
删除（未实现未接线的纸面设计=审计负债）——门限仅拓扑口径。

单写者/冲突口径（LG-011 委派令）：只在文件落后（存在新于文件最后触碰提交的
commits）时补写，不重写既有内容；与助理事件驱动写的冲突用 `pull --rebase` 重试
一次、再失败跳过本轮（下轮再补）。上轮 push 失败遗留的未推提交在下轮开头自愈
重推（recovery push），防止「文件已被自己触碰→门限闭合→永不重推」死锁。

审计：stdout 结构化 JSON envelope 由 trimc cron per-run 日志落盘
（/var/lib/trimc/cron/logs/<jobId>__<ISO>.log）——FADE §九.4「sync-log 或等效
审计日志」的等效载体。

用法：
    python3.8 -m runtime.cognition.daily_progress_patrol             # dry-run（默认）
    python3.8 -m runtime.cognition.daily_progress_patrol --sync      # 写入+commit+push
    python3.8 -m runtime.cognition.daily_progress_patrol --self-test # 内置验证套件

退出码：0=written/skip/would-write/pass；1=fail（errors 非空，cron 侧可见）。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

PROTOCOL = "daily-progress-patrol"
VERSION = "1.0"

TZ_CN = timezone(timedelta(hours=8))  # Asia/Shanghai（UTC+8，无夏令时）
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

GIT_REMOTE = "origin"
GIT_BRANCH = "dev"
COMMIT_NAME = "TriMC Scheduler"
COMMIT_EMAIL = "trimc-scheduler@fleet.local"
COMMITS_FMT = "%H%x1f%an%x1f%ct%x1f%h%x1f%s"

# ── Score 模式常量（2026-08-28 升档联审裁定·五约束） ────────────────────────
SCORE_PROTOCOL = "daily-progress-score"
SCORE_VERSION = "1.0"
TICK_SECONDS = 600            # cron */10
JOB_TIMEOUT_SECONDS = 180     # cron payload timeoutMs
T2_MAX_GAP = TICK_SECONDS + JOB_TIMEOUT_SECONDS  # 780s（裁定 T2 量化：tick+timeout 对齐）
SCORE_WEIGHTS = {"T1": 15, "T2": 15, "T4": 15, "T5": 10, "T6": 15, "T8": 10}  # 小计 80
SCORE_SKILL_EXTERNAL = {"T3": 10, "T7": 10}  # 事件及时性/治理对齐留 Score Skill（约束 1）
SCORE_THRESHOLD = 90
LOG_SCAN_CAP = 500

DEFAULT_TMV_REPO = "/srv/fleet/TriMetaverse"
DEFAULT_TCO_REPO = "/srv/fleet/TriCompany"
DEFAULT_REGISTRY_REL = "docs/engineering/fade-registry.md"

DAY_HEADING_RE = re.compile(r"^## \d{4}-\d{2}-\d{2}", re.M)
VERSION_LINE_RE = re.compile(r"^版本：(v[0-9][0-9A-Za-z.\-]*)")


def now_cn():
    """北京时间现值（人读轨：daily-progress 面向人，对齐 D-04 v4 北京时间口径）。"""
    return datetime.now(TZ_CN)


def week_relpath(day):
    """当前 ISO 周的 daily-progress.md 仓库相对路径（周平面目录约定）。"""
    iso_year, iso_week, _ = day.isocalendar()
    return "docs/workflow/operating-records/{}-W{:02d}/daily-progress.md".format(iso_year, iso_week)


def day_heading(day):
    return "## {}（{}）".format(day.strftime("%Y-%m-%d"), WEEKDAY_CN[day.weekday()])


def day_section_index(text, date_str):
    """当日节标题（按日期前缀匹配；星期标签变体/误标不触发重复建节）起始下标，无则 -1。"""
    m = re.search(r"^## {}（".format(re.escape(date_str)), text, re.M)
    return m.start() if m else -1


def git_env():
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"  # 服务器无凭据的 remote（github best-effort）必须快速失败禁挂起
    return env


def run_git(repo, args, timeout=90):
    proc = subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True,
        env=git_env(),
        timeout=timeout,
    )
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    return proc.returncode, out, err


def git_pull_rebase(repo, attempts=2, sleep_s=5.0):
    """pull --rebase origin dev；失败重试一次，再失败返回 False（跳过本轮，下轮再补）。"""
    out_all, err_all = "", ""
    for i in range(attempts):
        if i:
            time.sleep(sleep_s)
        rc, out, err = run_git(repo, ["pull", "--rebase", GIT_REMOTE, GIT_BRANCH])
        if rc == 0:
            return True, i + 1, out, err
        out_all += out
        err_all += err
    return False, attempts, out_all, err_all


def file_last_touch(repo, rel):
    """rel 最后一次被触碰的 commit：(epoch, full_hash, short_hash)；文件无提交史返回 (0, None, None)。"""
    rc, out, _ = run_git(repo, ["log", "-1", "--format=%ct%x1f%H%x1f%h", "--", rel])
    if rc != 0 or not out.strip():
        return 0, None, None
    line = out.strip().splitlines()[-1]
    parts = line.split("\x1f")
    if len(parts) != 3:
        return 0, None, None
    try:
        return int(parts[0]), parts[1], parts[2]
    except ValueError:
        return 0, None, None


def recent_commits(repo, cap=LOG_SCAN_CAP, path=None):
    """HEAD 历史（新→旧）解析为 [{hash,ct,short,subject}]；git 失败返回 None。"""
    args = ["log", "--format=" + COMMITS_FMT, "-n", str(cap)]
    if path:
        args += ["--", path]
    rc, out, _ = run_git(repo, args)
    if rc != 0:
        return None
    commits = []
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 5:
            continue
        try:
            ct = int(parts[2])
        except ValueError:
            continue
        commits.append(
            {
                "hash": parts[0],
                "author": parts[1],
                "ct": ct,
                "short": parts[3],
                "subject": " ".join(parts[4].split()),  # 控制字符/换行压平
            }
        )
    return commits


def commits_since(repo, base_full, cap=LOG_SCAN_CAP):
    """拓扑门限：文件最后触碰提交 base 之后到达 HEAD 的提交（新→旧）。

    比「时间戳严格大于」健壮：同秒连发/变基重写的提交不会因秒级相同被漏计
    （20:20 tick 实测缺陷：rebase 连发使 marker 与进度提交同秒，门限误闭合）。
    base 为 None（文件无提交史）→ 全部历史视为新增。
    """
    if not base_full:
        return recent_commits(repo, cap=cap)
    args = ["log", "--format=" + COMMITS_FMT, "-n", str(cap), "{}..HEAD".format(base_full)]
    rc, out, _ = run_git(repo, args)
    if rc != 0:
        return None
    commits = []
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 5:
            continue
        try:
            ct = int(parts[2])
        except ValueError:
            continue
        commits.append(
            {
                "hash": parts[0],
                "author": parts[1],
                "ct": ct,
                "short": parts[3],
                "subject": " ".join(parts[4].split()),
            }
        )
    return commits


def registry_snapshot(tco, registry_rel, day_start_epoch):
    """registry 粗粒度快照：当前版本行 + 当日 registry 提交；只读，失败降级不致命。"""
    snap = {"version": None, "today_commits": [], "error": None}
    reg_path = os.path.join(tco, *registry_rel.split("/"))
    try:
        with open(reg_path, "r", encoding="utf-8") as fh:
            for line in fh:
                m = VERSION_LINE_RE.match(line)
                if m:
                    snap["version"] = m.group(1)
                    break
    except OSError as exc:
        snap["error"] = "unreadable: {}".format(exc.__class__.__name__)
        return snap
    commits = recent_commits(tco, cap=100, path=registry_rel)
    if commits is None:
        snap["error"] = "git log failed"
        return snap
    snap["today_commits"] = [c for c in commits if c["ct"] >= day_start_epoch]
    return snap


def registry_line(registry):
    if registry["error"]:
        return "- registry：不可读（{}）".format(registry["error"])
    version = registry["version"] or "未知版本"
    today = registry["today_commits"]
    if not today:
        return "- registry：{}；今日 registry 提交无变化".format(version)
    shown = today[:5]
    txt = "；".join("{} {}".format(c["short"], c["subject"]) for c in shown)
    more = "（另 {} 条略）".format(len(today) - len(shown)) if len(today) > len(shown) else ""
    return "- registry：{}；今日 registry 提交 {} 条：{}{}".format(version, len(today), txt, more)


def build_increment(now, commits, since_short, registry, max_commits):
    lines = [
        "- 巡检兜底补写 @{} +08：自上次进度提交 {} 后新增 {} 条 commit：".format(
            now.strftime("%H:%M"), since_short, len(commits)
        )
    ]
    shown = commits[:max_commits]
    for c in shown:
        lines.append("  - {} {}".format(c["short"], c["subject"]))
    if len(commits) > len(shown):
        lines.append("  - …另有 {} 条略（全量见 git log）".format(len(commits) - len(shown)))
    lines.append(registry_line(registry))
    return "\n".join(lines) + "\n"


def build_day_section(now, commits, since_short, registry, max_commits, new_file):
    """当日节不存在时产出的整节（含标题）；new_file=True 时附文件头。"""
    parts = []
    if new_file:
        iso_year, iso_week, _ = now.isocalendar()
        parts.append(
            "# {}-W{:02d} 每日工作进度（仓库级粗粒度恢复兜底）\n\n"
            "> sourceOfTruth: 本文件（周平面维护项，FADE-001 承接）｜维护方：事件驱动主"
            "（董事长助理）+ 巡检兜底（daily-progress-watcher，本节即其自动补写）"
            "｜粒度：粗（日级战役/挂账/锚点）\n\n---\n\n".format(iso_year, iso_week)
        )
    parts.append("{}\n\n".format(day_heading(now)))
    parts.append(
        "**巡检兜底补写**（daily-progress-watcher 自动；粗粒度恢复锚，权威叙事见 "
        "ledger-mirror/董事会记事本——均机器本地不入仓）：\n"
    )
    parts.append(build_increment(now, commits, since_short, registry, max_commits))
    return "".join(parts)


def verify_day_section(file_path, date_str, must_contain):
    """写入后回读自检（Verify 段）：当日节存在且非空、本次追加内容在卷、锚点格式合规。"""
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return False, "file unreadable: {}".format(exc.__class__.__name__)
    idx = day_section_index(text, date_str)
    if idx < 0:
        return False, "day heading missing after write"
    line_end = text.find("\n", idx)
    tail = text[line_end:] if line_end >= 0 else ""
    if not tail.strip():
        return False, "day section empty"
    if must_contain.strip() not in text:
        return False, "appended block missing after write"
    if not DAY_HEADING_RE.search(text):
        return False, "heading format invalid"
    return True, ""


def git_commit_file(repo, rel, message):
    rc, _, err = run_git(repo, ["add", "--", rel])
    if rc != 0:
        return False, "git add failed: {}".format(err.strip()[:200])
    rc, out, err = run_git(
        repo,
        ["-c", "user.name={}".format(COMMIT_NAME), "-c", "user.email={}".format(COMMIT_EMAIL),
         "commit", "-m", message],
    )
    if rc != 0:
        return False, "git commit failed: {}".format((err or out).strip()[:200])
    return True, ""


def git_push(repo, remote, timeout=120):
    rc, out, err = run_git(repo, ["push", remote, "HEAD:refs/heads/{}".format(GIT_BRANCH)], timeout=timeout)
    return rc == 0, (err or out).strip()


def remote_exists(repo, name):
    rc, _, _ = run_git(repo, ["remote", "get-url", name])
    return rc == 0


def unpushed_count(repo):
    rc, out, _ = run_git(repo, ["rev-list", "--count", "{}/{}".format(GIT_REMOTE, GIT_BRANCH) + "..HEAD"])
    if rc != 0:
        return -1
    try:
        return int(out.strip())
    except ValueError:
        return -1


def make_envelope(status, details, errors, mode):
    return {
        "protocol": PROTOCOL,
        "version": VERSION,
        "mode": mode,
        "check_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "summary": {
            "new_commits": details.get("new_commits", 0),
            "errors": len(errors),
        },
        "details": details,
        "errors": errors,
    }


def patrol_once(tmv_repo, tco_repo, relpath, registry_rel, max_commits, do_write):
    """单轮巡检。do_write=False 为 dry-run（只读，不 pull 不写不推）。"""
    mode = "sync" if do_write else "dry-run"
    errors = []
    details = {}
    now = now_cn()
    day_start_epoch = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    file_path = os.path.join(tmv_repo, *relpath.split("/"))
    details["relpath"] = relpath

    if do_write:
        ok, attempts, _, err = git_pull_rebase(tmv_repo)
        details["tmv_pull"] = {"ok": ok, "attempts": attempts}
        if not ok:
            # 单写者冲突/瞬态故障口径：重试一次仍败 → 跳过本轮（下轮再补），不算 cron 失败
            details["tmv_pull"]["err_tail"] = err.strip()[-200:]
            return make_envelope("skip", details, errors, mode), None
        rc_tco, _, _ = run_git(tco_repo, ["pull", "--rebase", GIT_REMOTE, GIT_BRANCH])
        details["tco_pull"] = {"ok": rc_tco == 0}

        # 自愈：上轮 push 失败遗留的未推提交先重推（否则门限被自己触碰闭合，永不重推）
        n_unpushed = unpushed_count(tmv_repo)
        details["unpushed_before"] = n_unpushed
        if n_unpushed > 0:
            ok_push, msg_push = git_push(tmv_repo, GIT_REMOTE)
            details["recovery_push"] = {"ok": ok_push, "note": None if ok_push else msg_push[:200]}
            if not ok_push:
                errors.append("recovery push to {} failed: {}".format(GIT_REMOTE, msg_push[:200]))

    if os.path.exists(file_path):
        with open(file_path, "rb") as fh:
            pre_bytes = fh.read()
    else:
        pre_bytes = None
    touch_epoch, touch_full, touch_short = file_last_touch(tmv_repo, relpath)
    details["file_last_touch"] = {"epoch": touch_epoch, "short": touch_short}

    commits = commits_since(tmv_repo, touch_full)
    if commits is None:
        errors.append("git log failed on tmv repo")
        return make_envelope("fail", details, errors, mode), None
    details["new_commits"] = len(commits)
    if not commits:
        return make_envelope("skip", details, errors, mode), None

    registry = registry_snapshot(tco_repo, registry_rel, day_start_epoch)
    details["registry"] = {
        "version": registry["version"],
        "today_commits": len(registry["today_commits"]),
        "error": registry["error"],
    }

    since_short = touch_short if touch_short else "周初基线"
    text = pre_bytes.decode("utf-8", "replace") if pre_bytes is not None else ""
    has_day = day_section_index(text, now.strftime("%Y-%m-%d")) >= 0
    if has_day:
        block = build_increment(now, commits, since_short, registry, max_commits)
        new_file = False
    else:
        block = build_day_section(now, commits, since_short, registry, max_commits, new_file=pre_bytes is None)
        new_file = pre_bytes is None

    if not do_write:
        details["would_write_first_line"] = block.splitlines()[0]
        details["would_create_day_section"] = not has_day
        details["would_create_file"] = new_file
        return make_envelope("would-write", details, errors, mode), block

    # 写入（单写者原则：只 append/新建，不重写既有内容）
    if pre_bytes is not None and pre_bytes and not pre_bytes.endswith(b"\n"):
        block = "\n" + block
    if new_file:
        with open(file_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(block)
    else:
        with open(file_path, "a", encoding="utf-8", newline="") as fh:
            fh.write(block)

    def rollback():
        if pre_bytes is None:
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            with open(file_path, "wb") as fh:
                fh.write(pre_bytes)

    ok_v, msg_v = verify_day_section(file_path, now.strftime("%Y-%m-%d"), block)
    if not ok_v:
        rollback()
        errors.append("post-write verify failed (rolled back): {}".format(msg_v))
        return make_envelope("fail", details, errors, mode), None

    msg = "docs(plane): 巡检兜底补写 {}——{} 条 commit 粗粒度增量（daily-progress-watcher 自动；FADE-001 维护项②/LG-011）".format(
        now.strftime("%Y-%m-%d %H:%M"), len(commits)
    )
    ok_c, msg_c = git_commit_file(tmv_repo, relpath, msg)
    if not ok_c:
        rollback()
        errors.append("{} (rolled back)".format(msg_c))
        return make_envelope("fail", details, errors, mode), None

    ok_bare, msg_bare = git_push(tmv_repo, GIT_REMOTE)
    details["push_sg_bare"] = {"ok": ok_bare, "note": None if ok_bare else msg_bare[:200]}
    if not ok_bare:
        # sg-bare 必达：失败不伪造终态；commit 留在舰队克隆，下轮 recovery push 自愈
        errors.append("push sg-bare failed (commit kept, next round self-heals): {}".format(msg_bare[:200]))
        return make_envelope("fail", details, errors, mode), None

    if remote_exists(tmv_repo, "github"):
        ok_gh, msg_gh = git_push(tmv_repo, "github")
        details["push_github"] = {"ok": ok_gh, "note": None if ok_gh else msg_gh[:200]}
    else:
        details["push_github"] = {"ok": False, "note": "remote absent (best-effort end, non-blocking)"}

    return make_envelope("written", details, errors, mode), block


# ── Score 模式（--score；2026-08-28 升档联审裁定·五约束） ────────────────────
# 约束 1：T3 事件及时性/T7 治理对齐留 Score Skill（人工+双席抽验），CLI 禁自动化
# 约束 2：T5 网络降级=「不可验」非 FAIL
# 约束 3：scoreable run=含事件驱动写与巡检补写各≥1 次的自然日；skip-only 轮不可评
# 约束 4：首评期只观测不拦截（shadow）；试卷冻结+双门槛达标后 push 终态门接 score
# 约束 5：T8 性质注记=载体运行时健康项，非 run 产物项


def day_window(day):
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(start.timestamp()), int((start + timedelta(days=1)).timestamp())


def commits_in_window(repo, start, end, path=None):
    commits = recent_commits(repo, path=path)
    if commits is None:
        return None
    return [c for c in commits if start <= c["ct"] < end]


def check_score_t1(file_path, day):
    """T1（15）：当日节存在、星期标签格式合规、节非空。"""
    with open(file_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    date_str = day.strftime("%Y-%m-%d")
    idx = day_section_index(text, date_str)
    if idx < 0:
        return False, "day heading missing"
    line_end = text.find("\n", idx)
    heading = text[idx:line_end if line_end >= 0 else len(text)].strip()
    if not re.match(r"^## " + re.escape(date_str) + r"（周[一二三四五六日]）$", heading):
        return False, "weekday label format: " + heading
    body_start = (line_end + 1) if line_end >= 0 else len(text)
    rest = text[body_start:]
    nxt = re.search(r"^## ", rest, re.M)
    body = rest[:nxt.start()] if nxt else rest
    if not body.strip():
        return False, "empty day section"
    return True, "ok"


def check_score_t2(repo, day_start, day_end, rel):
    """T2（15）：巡检兜底及时性——触发（当日非 patrol 且不触文件的提交）到下一次文件
    触碰间隔 ≤T2_MAX_GAP（tick+timeout）。
    基线规则（shadow 观测期校准 2026-08-28）：仅计当日首次文件触碰之后的触发——
    文件建档前无兜底义务（首日建档前触发/部署日前历史触发由 Score Skill 注记）。"""
    all_day = commits_in_window(repo, day_start, day_end)
    file_all = recent_commits(repo, path=rel)
    if all_day is None or file_all is None:
        return None, None, None, None
    file_touch = set(c["hash"] for c in file_all)
    chrono = sorted((c["ct"], c["hash"], c["short"]) for c in file_all)
    baseline = min((c["ct"] for c in file_all), default=day_end)
    triggers = [c for c in all_day
                if c["author"] != COMMIT_NAME and c["hash"] not in file_touch
                and c["ct"] >= baseline]
    violations = []
    pending = 0
    checked = 0
    max_gap = 0
    for t in triggers:
        nxt = None
        for fc in chrono:
            if fc[0] >= t["ct"] and fc[1] != t["hash"]:
                nxt = fc
                break
        if nxt is None:
            pending += 1  # 触发后尚无补写（下一 tick 未到/跨日），计 pending 不计违规
            continue
        gap = nxt[0] - t["ct"]
        checked += 1
        max_gap = max(max_gap, gap)
        if gap > T2_MAX_GAP:
            violations.append({"trigger": t["short"], "backfill": nxt[2], "gap_s": gap})
    return violations, pending, checked, max_gap


def check_score_t4(repo, patrol_day, rel):
    """T4（15）：单写者纪律——patrol 身份提交补丁零删除行（append-only）。"""
    violations = []
    for c in patrol_day:
        rc, out, _ = run_git(repo, ["show", c["hash"], "--", rel])
        removed = [l for l in out.splitlines() if l.startswith("-") and not l.startswith("---")]
        if removed:
            violations.append({"commit": c["short"], "removed_lines": len(removed)})
    return violations


def check_score_t5(repo, ends):
    """T5（10）：三端持久对账；离线/失败=不可验非 FAIL（约束 2）。"""
    rc, out, _ = run_git(repo, ["rev-parse", "HEAD"])
    head = out.strip() if rc == 0 else None
    report = {}
    for name in ends:
        rc2, out2, err2 = run_git(repo, ["ls-remote", name, "refs/heads/{}".format(GIT_BRANCH)], timeout=60)
        if rc2 != 0:
            report[name] = {"verifiable": False, "note": (err2 or "unreachable")[:80]}
            continue
        tip = out2.split()[0] if out2.strip() else None
        report[name] = {
            "verifiable": True,
            "tip": tip[:12] if tip else None,
            "matches_head": (tip == head) if (tip and head) else None,
        }
    return head, report


PATROL_MSG_RE = re.compile(
    r"^docs\(plane\): 巡检兜底补写 \d{4}-\d{2}-\d{2} \d{2}:\d{2}——\d+ 条 commit 粗粒度增量"
    r"（daily-progress-watcher 自动；FADE-001 维护项②/LG-011）$"
)


def check_score_t6(file_path, patrol_day):
    """T6（15）：门限正确性——全文件日节零空节（skip 不产空节）+patrol 提交消息格式合规。"""
    with open(file_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    empty_days = []
    heads = list(re.finditer(r"^## \d{4}-\d{2}-\d{2}（周[一二三四五六日]）", text, re.M))
    for i, m in enumerate(heads):
        seg_end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        if not text[m.end():seg_end].strip():
            empty_days.append(m.group(0))
    bad_msgs = [c["short"] for c in patrol_day if not PATROL_MSG_RE.match(c["subject"])]
    return empty_days, bad_msgs


def check_score_t8(t8_runner=None):
    """T8（10）：载体运行时健康（性质注记：非 run 产物项，约束 5）——跑内置自测。"""
    if t8_runner is not None:
        return t8_runner()
    return _self_test_result()


def run_score(repo, day, rel, ends, t8_runner=None):
    """Score 模式：对指定日产出 shadow 评分 envelope（只观测不拦截，约束 4）。"""
    day_start, day_end = day_window(day)
    file_path = os.path.join(repo, *rel.split("/"))
    errors = []
    file_day = commits_in_window(repo, day_start, day_end, path=rel)
    if file_day is None:
        errors.append("git log failed on repo")
        file_day = []
    patrol_day = [c for c in file_day if c.get("author") == COMMIT_NAME]
    event_day = [c for c in file_day if c.get("author") != COMMIT_NAME]
    scoreable = bool(patrol_day) and bool(event_day)
    checks = {}
    subtotal = 0
    if scoreable and not errors:
        ok1, d1 = check_score_t1(file_path, day)
        checks["T1"] = {"ok": ok1, "weight": SCORE_WEIGHTS["T1"], "detail": d1}
        v2, pending, checked, max_gap = check_score_t2(repo, day_start, day_end, rel)
        if v2 is None:
            errors.append("git log failed on T2 collection")
            checks["T2"] = {"ok": False, "weight": SCORE_WEIGHTS["T2"], "violations": [], "error": "collection failed"}
        else:
            checks["T2"] = {"ok": not v2, "weight": SCORE_WEIGHTS["T2"], "violations": v2,
                            "pending_triggers": pending, "checked": checked,
                            "max_gap_s": max_gap, "threshold_s": T2_MAX_GAP}
        v4 = check_score_t4(repo, patrol_day, rel)
        checks["T4"] = {"ok": not v4, "weight": SCORE_WEIGHTS["T4"], "violations": v4,
                        "patrol_commits": len(patrol_day)}
        head, ends_report = check_score_t5(repo, ends)
        checks["T5"] = {"ok": True, "weight": SCORE_WEIGHTS["T5"], "head": (head or "")[:12],
                        "ends": ends_report,
                        "note": "离线/未收敛=不可验或收敛中，非 FAIL（约束 2；GitHub 容差≤24h 收敛）"}
        empty_days, bad_msgs = check_score_t6(file_path, patrol_day)
        checks["T6"] = {"ok": not empty_days and not bad_msgs, "weight": SCORE_WEIGHTS["T6"],
                        "empty_days": empty_days, "bad_msgs": bad_msgs}
        t8 = check_score_t8(t8_runner)
        checks["T8"] = {"ok": t8["status"] == "pass", "weight": SCORE_WEIGHTS["T8"],
                        "self_test": t8["summary"],
                        "note": "载体运行时健康项，非 run 产物项（约束 5）"}
        subtotal = sum(c["weight"] for c in checks.values() if c["ok"])
    status = "fail" if errors else ("not-scoreable" if not scoreable else "shadow")
    reason = None
    if not scoreable and not errors:
        reason = ("scoreable run=自然日含事件驱动写与巡检补写各≥1；skip-only/单类不可评（约束 3）"
                  "；当日 patrol={} event={}".format(len(patrol_day), len(event_day)))
    return {
        "protocol": SCORE_PROTOCOL,
        "version": SCORE_VERSION,
        "mode": "shadow-score",
        "check_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date": day.strftime("%Y-%m-%d"),
        "scoreable": scoreable,
        "status": status,
        "reason": reason,
        "summary": {
            "subtotal": subtotal,
            "subtotal_max": sum(SCORE_WEIGHTS.values()),
            "threshold": SCORE_THRESHOLD,
            "gate_wired": False,
            "errors": len(errors),
        },
        "score_skill_external": SCORE_SKILL_EXTERNAL,
        "day_commits": {"patrol": len(patrol_day), "event": len(event_day)},
        "checks": checks,
        "errors": errors,
    }


# ── 内置验证套件（--self-test；FADE §九.3 配套 validation） ──────────────────


def _init_sandbox(tmp):
    """沙箱：repo（工作仓，branch dev）+ bare（origin）+ tco（registry 仓）。"""
    bare = os.path.join(tmp, "bare.git")
    repo = os.path.join(tmp, "repo")
    tco = os.path.join(tmp, "tco")
    rc, _, _ = run_git(tmp, ["init", "--bare", os.path.relpath(bare, tmp)])
    assert rc == 0, "init bare failed"
    rc, _, _ = run_git(tmp, ["init", os.path.relpath(repo, tmp)])
    assert rc == 0, "init repo failed"
    rc, _, _ = run_git(repo, ["symbolic-ref", "HEAD", "refs/heads/{}".format(GIT_BRANCH)])
    assert rc == 0, "set branch failed"
    rc, _, _ = run_git(tmp, ["init", os.path.relpath(tco, tmp)])
    assert rc == 0, "init tco failed"
    rc, _, _ = run_git(repo, ["remote", "add", GIT_REMOTE, bare])
    assert rc == 0, "add remote failed"
    return repo, bare, tco


def _sandbox_commit(repo, rel_files, message):
    for rel, content in rel_files.items():
        abs_path = os.path.join(repo, *rel.split("/"))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        rc, _, err = run_git(repo, ["add", "--", rel])
        assert rc == 0, "add failed: " + err
    rc, out, err = run_git(
        repo,
        ["-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-m", message],
    )
    assert rc == 0, "commit failed: " + (err or out)


def _self_test_result():
    errors = []
    checks = []
    tmp = tempfile.mkdtemp(prefix="dpp-selftest-")
    try:
        repo, bare, tco = _init_sandbox(tmp)
        rel = week_relpath(now_cn())
        reg_rel = "docs/engineering/fade-registry.md"
        yesterday = now_cn() - timedelta(days=1)

        # 底料：昨日节 + registry v9.9
        _sandbox_commit(
            repo,
            {rel: "# 测试进度\n\n---\n\n{}\n\n**已完成**：底料\n".format(day_heading(yesterday))},
            "init daily progress (yesterday)",
        )
        _sandbox_commit(tco, {reg_rel: "版本：v9.9（测试）\n"}, "init registry")
        rc, _, err = run_git(repo, ["push", GIT_REMOTE, "HEAD:refs/heads/{}".format(GIT_BRANCH)])
        assert rc == 0, "initial push failed: " + err

        def expect(cond, name):
            checks.append({"name": name, "ok": bool(cond)})
            if not cond:
                errors.append("self-test check failed: {}".format(name))

        # Case A：门限闭合（无新 commits）→ skip，不产空节
        env_a, block_a = patrol_once(repo, tco, rel, reg_rel, 15, do_write=True)
        expect(env_a["status"] == "skip", "A: gate closed -> skip")
        expect(block_a is None, "A: no block produced")

        # Case B：marker commit（非进度文件）→ 门限开 → written + 当日节自动建 + registry 版本在卷
        _sandbox_commit(repo, {"NOTES.md": "marker\n"}, "marker commit for gate")
        env_b, block_b = patrol_once(repo, tco, rel, reg_rel, 15, do_write=True)
        expect(env_b["status"] == "written", "B: gate open -> written")
        expect(env_b["details"]["new_commits"] == 1, "B: one new commit counted")
        expect(env_b["details"]["push_sg_bare"]["ok"] is True, "B: sg-bare push ok")
        with open(os.path.join(repo, *rel.split("/")), "r", encoding="utf-8") as fh:
            written = fh.read()
        expect(day_heading(now_cn()) in written, "B: day section created")
        expect("marker commit for gate" in written, "B: commit subject in block")
        expect("v9.9" in written, "B: registry version in block")
        expect(unpushed_count(repo) == 0, "B: push complete (no unpushed)")

        # Case C：巡检自己触碰文件后门限闭合 → skip（无自激循环）
        env_c, _ = patrol_once(repo, tco, rel, reg_rel, 15, do_write=True)
        expect(env_c["status"] == "skip", "C: gate closed after own write")

        # Case D：当日节已存在时的二次增量 append（不重写既有内容）
        _sandbox_commit(repo, {"NOTES.md": "marker2\n"}, "marker commit 2")
        env_d, block_d = patrol_once(repo, tco, rel, reg_rel, 15, do_write=True)
        expect(env_d["status"] == "written", "D: second increment written")
        with open(os.path.join(repo, *rel.split("/")), "r", encoding="utf-8") as fh:
            written2 = fh.read()
        expect(written2.count(day_heading(now_cn())) == 1, "D: day heading not duplicated")
        expect("marker commit for gate" in written2 and "marker commit 2" in written2, "D: append-only preserved")

        # Case E：verify 单元（缺标题/空节/缺追加块 → False）
        probe = os.path.join(tmp, "probe.md")
        today_str = now_cn().strftime("%Y-%m-%d")
        with open(probe, "w", encoding="utf-8", newline="") as fh:
            fh.write("no heading here\n")
        ok1, _ = verify_day_section(probe, today_str, "x")
        expect(not ok1, "E1: verify rejects missing heading")
        with open(probe, "w", encoding="utf-8", newline="") as fh:
            fh.write("{}\n\n".format(day_heading(now_cn())))
        ok2, _ = verify_day_section(probe, today_str, "x")
        expect(not ok2, "E2: verify rejects empty section")

        # Case H：当日节日期前缀匹配容错（星期标签误标变体不重复建节）
        text_h = "## {}（周四）\n\n**已完成**：底料\n".format(today_str)
        expect(day_section_index(text_h, today_str) == 0, "H1: weekday-label variant recognized")
        expect(day_section_index(text_h, "1999-01-01") == -1, "H2: other date no match")

        # Case F：registry 快照版本行解析
        snap = registry_snapshot(tco, reg_rel, 0)
        expect(snap["version"] == "v9.9", "F: registry version parsed")

        # Case I：同秒提交边界（变基/连发实测缺陷回归）——拓扑门限不漏计
        env_same = git_env()
        env_same["GIT_COMMITTER_DATE"] = "2026-08-27 12:00:00 +0800"
        env_same["GIT_AUTHOR_DATE"] = "2026-08-27 12:00:00 +0800"
        for msg in ("same-second commit A", "same-second commit B"):
            proc = subprocess.run(
                ["git", "-C", repo, "commit", "--allow-empty", "-m", msg],
                capture_output=True, env=env_same,
            )
            assert proc.returncode == 0, "same-second commit failed"
        proc = subprocess.run(
            ["git", "-C", repo, "commit", "--allow-empty", "-m", "marker commit 3"],
            capture_output=True, env=git_env(),
        )
        assert proc.returncode == 0, "marker3 commit failed"
        touch_e, touch_f, _ = file_last_touch(repo, rel)
        late = commits_since(repo, touch_f)
        expect(late is not None and len(late) == 3, "I1: topo gate counts same-second commits")
        expect(any(c["subject"] == "same-second commit B" for c in (late or [])), "I2: same-second commit listed")

        # Case G：dry-run 只读（不写不推；I 造了 3 个未推提交，G 再造 1 个 marker → 门限开 4 条）
        _sandbox_commit(repo, {"NOTES.md": "marker3\n"}, "marker commit 3 (notes)")
        pre_unpushed = unpushed_count(repo)
        env_g, block_g = patrol_once(repo, tco, rel, reg_rel, 15, do_write=False)
        expect(env_g["status"] == "would-write", "G: dry-run reports would-write")
        expect(env_g["details"]["new_commits"] == 4, "G: four pending commits counted")
        expect(block_g is not None and "marker commit 3 (notes)" in block_g, "G: preview contains increment")
        expect(unpushed_count(repo) == pre_unpushed, "G: dry-run pushed nothing")

        # Case S：--score 沙箱（事件驱动写+巡检补写同日；T8 stub 防自测递归）
        def _commit_as(rel_files, message, name, email):
            for r, content in rel_files.items():
                ap = os.path.join(repo, *r.split("/"))
                os.makedirs(os.path.dirname(ap), exist_ok=True)
                with open(ap, "w", encoding="utf-8", newline="") as fh:
                    fh.write(content)
                rc2, _, err2 = run_git(repo, ["add", "--", r])
                assert rc2 == 0, "S add failed: " + err2
            env_c = git_env()
            env_c["GIT_AUTHOR_NAME"] = name
            env_c["GIT_COMMITTER_NAME"] = name
            env_c["GIT_AUTHOR_EMAIL"] = email
            env_c["GIT_COMMITTER_EMAIL"] = email
            proc2 = subprocess.run(
                ["git", "-C", repo, "commit", "-m", message],
                capture_output=True, env=env_c,
            )
            assert proc2.returncode == 0, "S commit failed: " + proc2.stderr.decode("utf-8", "replace")

        stamp_s = now_cn().strftime("%Y-%m-%d %H:%M")
        _commit_as({"NOTES2.md": "s marker\n"}, "s-case event marker", "ceo-test", "ceo@test")
        patrol_msg_s = ("docs(plane): 巡检兜底补写 {}——1 条 commit 粗粒度增量"
                        "（daily-progress-watcher 自动；FADE-001 维护项②/LG-011）").format(stamp_s)
        with open(os.path.join(repo, *rel.split("/")), "a", encoding="utf-8", newline="") as fh:
            fh.write("- s-case 巡检兜底补写行\n")
        rc_s1, _, _ = run_git(repo, ["add", "--", rel])
        assert rc_s1 == 0, "S patrol add failed"
        proc_s1 = subprocess.run(
            ["git", "-C", repo, "commit", "-m", patrol_msg_s],
            capture_output=True,
            env=dict(git_env(), GIT_AUTHOR_NAME=COMMIT_NAME, GIT_COMMITTER_NAME=COMMIT_NAME,
                     GIT_AUTHOR_EMAIL=COMMIT_EMAIL, GIT_COMMITTER_EMAIL=COMMIT_EMAIL),
        )
        assert proc_s1.returncode == 0, "S patrol commit failed"
        with open(os.path.join(repo, *rel.split("/")), "a", encoding="utf-8", newline="") as fh:
            fh.write("- s-case 事件驱动行\n")
        rc_s2, _, _ = run_git(repo, ["add", "--", rel])
        assert rc_s2 == 0, "S event add failed"
        proc_s2 = subprocess.run(
            ["git", "-C", repo, "commit", "-m", "docs(plane): s-case 事件驱动写（M-002）"],
            capture_output=True,
            env=dict(git_env(), GIT_AUTHOR_NAME="assistant-test", GIT_COMMITTER_NAME="assistant-test",
                     GIT_AUTHOR_EMAIL="a@test", GIT_COMMITTER_EMAIL="a@test"),
        )
        assert proc_s2.returncode == 0, "S event commit failed"
        t8_stub = {"status": "pass", "summary": {"checks": 24, "failed": 0}}
        env_s = run_score(repo, now_cn(), rel, [], t8_runner=lambda: t8_stub)
        expect(env_s["scoreable"] is True, "S1: scoreable (event+patrol both present)")
        expect(env_s["status"] == "shadow", "S2: shadow observe-only")
        expect(env_s["summary"]["subtotal"] == 80, "S3: subtotal 80/80 all CLI checks ok")
        expect(env_s["checks"]["T2"]["checked"] >= 1, "S4: T2 trigger checked")
        expect(env_s["checks"]["T4"]["ok"] is True, "S5: append-only holds")
        # T4 负例：patrol 身份删行提交
        del_path = os.path.join(repo, *rel.split("/"))
        with open(del_path, "r", encoding="utf-8") as fh:
            cur_text = fh.read()
        with open(del_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(cur_text.replace("- s-case 巡检兜底补写行\n", ""))
        rc_s3, _, _ = run_git(repo, ["add", "--", rel])
        assert rc_s3 == 0, "S del add failed"
        proc_s3 = subprocess.run(
            ["git", "-C", repo, "commit", "-m", "s-case deletion by patrol identity"],
            capture_output=True,
            env=dict(git_env(), GIT_AUTHOR_NAME=COMMIT_NAME, GIT_COMMITTER_NAME=COMMIT_NAME,
                     GIT_AUTHOR_EMAIL=COMMIT_EMAIL, GIT_COMMITTER_EMAIL=COMMIT_EMAIL),
        )
        assert proc_s3.returncode == 0, "S del commit failed"
        del_commit = [c for c in recent_commits(repo, path=rel) if c["author"] == COMMIT_NAME][0]
        v4_neg = check_score_t4(repo, [del_commit], rel)
        expect(len(v4_neg) == 1, "S6: T4 detects patrol deletion")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    result = {
        "protocol": PROTOCOL,
        "version": VERSION,
        "mode": "self-test",
        "check_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "pass" if not errors else "fail",
        "summary": {"checks": len(checks), "failed": len(errors)},
        "checks": checks,
        "errors": errors,
    }
    return result


def self_test(quiet=False):
    """运行内置验证套件；quiet=True 不打印（--score T8 复用入口）。"""
    result = _self_test_result()
    if not quiet:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["errors"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="daily_progress_patrol",
        description="FADE-001 维护项② 每日进度巡检兜底（LG-011）——确定性脚本，无 LLM。"
        " 默认 dry-run；--sync 才写入/commit/push；--self-test 跑内置验证套件。",
    )
    parser.add_argument("--sync", action="store_true", help="写入模式：append+commit+push（默认 dry-run）")
    parser.add_argument("--dry-run", action="store_true", help="显式 dry-run（默认即 dry-run）")
    parser.add_argument("--self-test", action="store_true", help="运行内置验证套件（沙箱 git 仓，不动真仓）")
    parser.add_argument("--tmv-repo", default=DEFAULT_TMV_REPO, help="TriMetaverse 舰队克隆路径")
    parser.add_argument("--tco-repo", default=DEFAULT_TCO_REPO, help="TriCompany 舰队克隆路径")
    parser.add_argument("--relpath", default=None, help="daily-progress.md 相对路径（默认按当前 ISO 周推算）")
    parser.add_argument("--registry-rel", default=DEFAULT_REGISTRY_REL, help="registry 文件相对路径（TriCompany 侧）")
    parser.add_argument("--max-commits", type=int, default=15, help="单次补写列出的 commit 上限")
    parser.add_argument("--score", action="store_true", help="Score 模式：对指定日产出 shadow 评分 envelope（只观测不拦截，约束 4）")
    parser.add_argument("--date", default=None, help="--score 评分日 YYYY-MM-DD（默认今天；限当前周）")
    parser.add_argument("--score-ends", default="sg-server,origin", help="--score 三端对账 remote 名（逗号分隔）")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    rel = args.relpath or week_relpath(now_cn())

    if args.score:
        day = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=TZ_CN) if args.date else now_cn()
        ends = [s.strip() for s in args.score_ends.split(",") if s.strip()]
        envelope = run_score(args.tmv_repo, day, rel, ends)
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
        return 1 if envelope["errors"] else 0
    result, _ = patrol_once(
        args.tmv_repo, args.tco_repo, rel, args.registry_rel, args.max_commits, do_write=args.sync
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
