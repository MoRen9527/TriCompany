"""orchestrate_tick — TriMMC 7×24 编排工作循环（M2，2026-08-25）

设计依据：trimmc-orchestration-design.md v0.2 §三/§六/§七/§八；CEO 成本裁决
（月度上限 1000 元，超限自动降级为仅影子+人工触发）。

单次 tick 职责（由 trimc cron 每 30 分钟调用）：
  1. 三重门待办评估：扫描 operating-records 各周 trees/*/tree-op.json，
     仅收 status=active 且 domainRouting=server-executable 且存在 pending
     节点且无未到期时间门的树（P1 准入门的确定性实现）
  2. 待办集指纹：变化才动作（P2 边沿触发）
  3. 成本护栏：读月度台账，超 1000 元上限则拒绝 spawn 并一次性发降级通知
  4. spawn 编排会话（fleet 身份 headless CC，锚定 ceo-chief-of-staff 渲染位，
     brief v2 模板含 F1 修正：收口必须置 tree.status=done）
  5. 会话结束：解析 usage 记成本台账、更新 SessionRegistry、边沿触发通知

通知通道现状：邮件（notify canonical）可用；trilc push 因 NAT 方向缺陷
（Q-F，服务器无法主动连本地）挂 M3 pull-as-push 方案，本版只走邮件。

用法：
  python3.8 -m runtime.cognition.orchestrate_tick [--dry-run] [--once]
cron 安装（trimc）：每 30 分钟错峰 "13,43 * * * *"，runAs fleet。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path("/srv/fleet/TriMetaverse")
PLANE = REPO / "docs/workflow/operating-records"
SHADOW = Path("/srv/fleet/shadow-plane")
LEDGER_PATH = SHADOW / "cost-ledger.json"
REGISTRY_PATH = SHADOW / "session-registry.json"
FINGERPRINT_PATH = SHADOW / "tick-fingerprint.txt"
CONFIG_PATH = Path.home() / ".trimetaverse" / "orchestration.json"

# 价格表（权威源 api-docs.deepseek.com/quick_start/pricing，2026-08-25 取数，
# USD per 1M tokens，[off-peak, peak]）；价格变动须重取数并更新 as-of。
PRICES = {
    "deepseek-v4-flash": {"in_hit": [0.007, 0.014], "in_miss": [0.22, 0.44], "out": [0.66, 1.32]},
    "deepseek-v4-pro": {"in_hit": [0.022, 0.044], "in_miss": [0.66, 1.32], "out": [1.98, 3.96]},
}
# 峰值时段（UTC，周一至周五）：01:00-04:00、06:00-10:00
PEAK_UTC = [(1, 4), (6, 10)]


def _load_config() -> dict:
    cfg = {
        "budget_cny_monthly": 1000.0,
        "usd_cny": 7.2,
        "daily_token_cap": 1500000000,
        "default_model": "deepseek-v4-flash",
        "session_timeout_s": 560,
        "tick_max_sessions": 1,
    }
    try:
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def _apply_price_overrides(cfg: dict) -> None:
    """cfg['prices_override'] 形如 {model: {in_hit:[lo,hi], in_miss:[...], out:[...]}}，
    覆盖内置 PRICES（模型切档后计价准确性，2026-08-25 ox-alpha 需求）。"""
    ov = cfg.get("prices_override")
    if isinstance(ov, dict):
        PRICES.update(ov)
        cfg["default_model"] = cfg.get("default_model", "deepseek-v4-flash")


LOCK_PATH = SHADOW / "orchestrator.lock"


def _pid_alive(pid) -> bool:
    """探测进程存活（0 信号=仅探测）。"""
    try:
        os.kill(int(pid), 0)
        return True
    except (ProcessLookupError, TypeError, ValueError):
        return False
    except PermissionError:
        return True  # 进程存在但非本用户所有（保守视为活）


def _lock_stale_or_absent(cfg: dict) -> bool:
    """运行锁陈旧判定（fade-rehearsal-001 审查 P0-1 修正版）。四通道：
    ① 锁龄 > 2×timeout（僵尸兜底）② 锁内 pid 已死（spawn 后锁内补记 pid）
    ③ 台账反查该树 spawn pid 已死 ④ 无 pid 可查且锁龄 > 300s（短阈值判死，
    **禁止默认拒斥**——原版查无条目即判活，孤儿锁滞留最长 80 分钟）。
    陈旧即删除锁文件并返回 True。"""
    SHORT_STALE_S = 300
    try:
        d = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return True  # 锁缺失/损坏=可获取
    age = datetime.now(timezone.utc).timestamp() - d.get("ts", 0)
    if age > cfg["session_timeout_s"] * 2:
        LOCK_PATH.unlink()
        return True
    if d.get("pid"):
        if not _pid_alive(d["pid"]):
            LOCK_PATH.unlink()
            return True
        return False
    tree_id = d.get("tree", "")
    for t in reversed(load_registry().get("ticks", [])):
        if t.get("tree") == tree_id and t.get("pid"):
            if not _pid_alive(t["pid"]):
                LOCK_PATH.unlink()
                return True
            return False
    if age > SHORT_STALE_S:
        LOCK_PATH.unlink()
        return True
    return False


def _tokens_today(ledger: dict) -> int:
    today = date.today().isoformat()
    return sum(s.get("total_tokens", 0) for s in ledger.get("sessions", []) if s.get("ts", "").startswith(today))


def _is_peak(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    h = now.hour
    return any(a <= h < b for a, b in PEAK_UTC)


def _session_cost_usd(model: str, in_hit: int, in_miss: int, out: int, peak: bool) -> float:
    p = PRICES.get(model, PRICES["deepseek-v4-flash"])
    i = 1 if peak else 0
    return (in_hit / 1e6) * p["in_hit"][i] + (in_miss / 1e6) * p["in_miss"][i] + (out / 1e6) * p["out"][i]


def _load_ledger() -> dict:
    try:
        d = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        if d.get("month") == date.today().strftime("%Y-%m"):
            return d
    except Exception:
        pass
    return {"month": date.today().strftime("%Y-%m"), "sessions": [], "totals": {"cost_usd": 0.0, "cost_cny": 0.0}}


def _save_ledger(d: dict) -> None:
    SHADOW.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def budget_check(cfg: dict, ledger: dict) -> tuple[bool, str]:
    """True=允许 spawn。双门：每日 token 上限（CEO 08-25：免费模型按量控制 15 亿/日）+ 月度金额兜底。"""
    tok = _tokens_today(ledger)
    cap = int(cfg["daily_token_cap"])
    if tok >= cap:
        return False, "今日 token %.0f 已超上限 %.0f——自动降级：仅影子试跑+人工触发" % (tok, cap)
    spent_cny = ledger["totals"].get("cost_cny", 0.0)
    if spent_cny >= cfg["budget_cny_monthly"]:
        return False, "月度成本 %.2f 元已超上限 %.0f 元——自动降级：仅影子试跑+人工触发" % (spent_cny, cfg["budget_cny_monthly"])
    return True, "今日 token %.0f/%.0f｜月度 %.2f 元" % (tok, cap, spent_cny)


TIME_GATE_RE = re.compile(r"(≥?\s*\d+\s*(周|天|小时)|时间门)")


def evaluate_backlog() -> tuple[list[dict], str]:
    """三重门确定性评估：返回可执行树清单与指纹。"""
    actionable = []
    today = date.today()
    for week_dir in sorted(PLANE.glob("2026-W*")):
        for tree_file in sorted(week_dir.glob("trees/*/tree-op.json")):
            try:
                d = json.loads(tree_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            # 门 1 状态门：仅 active（frozen/pending/blocked 不入队）
            if d.get("status") != "active":
                continue
            # 门 2 域路由门：显式服务器域授权（缺省不授权——安全默认）
            if d.get("domainRouting") != "server-executable":
                continue
            # 门 2b 面路由门（2026-08-26）：face=r-face 的树归 TriRMC（heyuan），
            # TriMMC 只取 m-face；缺省 face 视为 m-face（向后兼容存量树）
            if d.get("face", "m-face") != "m-face":
                continue
            pending = [n for n in d.get("nodes", []) if n.get("status") == "pending"]
            if not pending:
                continue
            # 门 3 可执行门：节点 action 含时间门语义则视为未到期，不入队
            gated = [n["nodeId"] for n in pending if TIME_GATE_RE.search(n.get("action", ""))]
            if len(gated) == len(pending):
                continue
            actionable.append({
                "treeId": d.get("treeId", tree_file.parent.name),
                "path": str(tree_file),
                "pendingNodes": [n["nodeId"] for n in pending],
                "gatedNodes": gated,
            })
    fp_src = json.dumps(sorted((a["treeId"], tuple(a["pendingNodes"])) for a in actionable), sort_keys=True)
    fp = hashlib.sha256(fp_src.encode()).hexdigest()[:16]
    return actionable, fp


BRIEF_V2 = """# 编排会话任务简报（tick {tick_id}，≤30 行交接纪律）

你是本次 tick 的编排实例（锚定渲染位 ceo-chief-of-staff）。cwd=/srv/fleet/TriMetaverse。

## 任务
执行树 {tree_path} 端到端：按节点派工 fresh 子实例（agent 字段指定角色），一次一个节点禁复用；
先写后报（子实例先落盘再报告，带路径+行数）。

## 铁律
- **状态先行+原子即提交**：开工先落 state/log 骨架并 commit；此后每完成一个原子动作立即单独 commit（会话随时可能被回收，只认已 commit 的进度）
- **命令一律裸形式**：你已在目标仓 cwd 内，禁止 `cd X && cmd` 组合（审批按命令前缀整串匹配，cd 开头必拒）；跨仓操作用 `git -C <路径> …`

## 红线（违反即停）
1. 只写该树目录内与任务明示的目标路径；operating-records 其他文件与 .shift-ade.json 只读
2. git 仅限 add <明确路径>/commit/push origin dev；禁 force/rebase
3. 事实障碍如实标注 blocked 并停，不臆造完成
4. **收口必做**：全部节点 done 后，把树文件顶层 "status" 置为 "done"，再提交（F1 修正）

## 完成定义
节点全 done+顶层 status=done+收口 commit 已 push+/srv/fleet/shadow-plane/session-registry.json 追加本 tick 台账

## 输出
总结：各节点结果+commit hash+台账路径证据。
"""


def load_registry() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"ticks": []}


def save_registry(r: dict) -> None:
    SHADOW.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


def notify(subject: str, body: str) -> str:
    try:
        from runtime.cognition.notify import send_notification
        r = send_notification(subject=subject, body=body, to=[],
                              context_id="orchestrate-tick", trigger_mode="cron")
        return str(r.get("status"))
    except Exception as e:
        return "failed:%s" % e


def _sync_worktree() -> bool:
    """P1-1（fade-rehearsal-001 审查）：tick 入口同步工作树——数据面自愈，
    cron tick 也能看到新 push 的树（原版仅 hook 单点同步，pull 失败即结构性盲）。
    失败不阻断 tick（以当前视图继续），仅留痕。"""
    try:
        r1 = subprocess.run(["git", "fetch", "origin", "dev"], cwd=str(REPO),
                            capture_output=True, timeout=60)
        r2 = subprocess.run(["git", "rebase", "origin/dev"], cwd=str(REPO),
                            capture_output=True, timeout=120)
        ok_sync = r1.returncode == 0 and r2.returncode == 0
        if not ok_sync:
            print("worktree sync degraded (fetch rc=%s rebase rc=%s)"
                  % (r1.returncode, r2.returncode))
        return ok_sync
    except Exception as e:
        print("worktree sync error: %s" % e)
        return False


def _harvest_usage(ledger: dict) -> int:
    """P1-3（fade-rehearsal-001 审查）：收割已结束会话的 usage 入账——
    解析 orchestrator-session-*.log 尾部 CC result JSON 的 usage 字段，
    追加台账并去重（harvested 文件名清单）。返回本轮新增 token 数。
    修复原版 _save_ledger 零调用、预算双门读数恒零的问题。"""
    added = 0
    harvested = set(ledger.get("harvested", []))
    if not SHADOW.exists():
        return 0
    for log_file in sorted(SHADOW.glob("orchestrator-session-*.log")):
        name = log_file.name
        if name in harvested:
            continue
        try:
            text = log_file.read_text(encoding="utf-8", errors="replace").strip()
            if '"type":"result"' not in text:
                continue  # 会话未结束（无 result 行）
            idx = text.rfind("\n{")
            obj = json.loads(text[idx + 1:] if idx >= 0 else text)
            u = obj.get("usage") or {}
            total = int(u.get("input_tokens", 0)) + int(u.get("cache_read_input_tokens", 0)) \
                + int(u.get("cache_creation_input_tokens", 0)) + int(u.get("output_tokens", 0))
            model = (obj.get("modelUsage") or {}) and next(iter(obj.get("modelUsage", {})), "") or ""
            ledger.setdefault("sessions", []).append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_log": name, "total_tokens": total,
                "model": model, "source": "harvest"})
            ledger["harvested"] = list(harvested | {name})
            harvested.add(name)
            added += total
        except Exception:
            continue
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只评估门与预算，不 spawn 不写状态")
    ap.add_argument("--trigger", default="cron", choices=["cron", "hook", "manual"],
                    help="触发来源（P1-6：台账留痕，区分 hook 快通道/cron 慢通道/手工）")
    args = ap.parse_args()
    cfg = _load_config()
    _apply_price_overrides(cfg)
    now = datetime.now(timezone.utc)
    if not args.dry_run:
        _sync_worktree()

    actionable, fp = evaluate_backlog()
    prev_fp = FINGERPRINT_PATH.read_text(encoding="utf-8").strip() if FINGERPRINT_PATH.exists() else ""
    ledger = _load_ledger()
    if not args.dry_run:
        added = _harvest_usage(ledger)
        if added:
            _save_ledger(ledger)
    ok, budget_msg = budget_check(cfg, ledger)

    print(json.dumps({"tick": now.isoformat(), "actionable": [a["treeId"] for a in actionable],
                      "fingerprint": fp, "changed": fp != prev_fp,
                      "budget": budget_msg}, ensure_ascii=False))

    if args.dry_run:
        return 0
    if not actionable:
        if fp != prev_fp and prev_fp:  # 非零→零边沿：清零通知一次
            notify("[TriMMC] 编排待办清零", "当前无服务器域可执行树（指纹 %s）。" % fp)
        FINGERPRINT_PATH.write_text(fp, encoding="utf-8")
        return 0
    if fp == prev_fp:
        # 战役续跑模式：指纹未变但上一 tick 已完成且当前无运行中会话 → 继续推进长战役
        reg_now = load_registry()
        ticks = reg_now.get("ticks", [])
        last = ticks[-1] if ticks else None
        last_age_s = time.time() - last.get("ts_epoch", 0) if last else 1e9
        eligible = (last and (last.get("rc") == 0 or last_age_s > 1800) and _lock_stale_or_absent(cfg))
        if not (actionable and last and eligible):
            return 0
        notify_skip = True
    else:
        notify_skip = False
    if not ok:
        notify("[TriMMC][E3] 编排降级", budget_msg)
        return 1

    # 活动锁护栏：上一会话仍在运行则本轮不 spawn（防指纹写入失败时的
    # spawn 风暴——2026-08-26 NameError 事故的纵深防御）
    if not _lock_stale_or_absent(cfg):
        print("live session running, skip spawn")
        return 0

    tree = actionable[0]
    SHADOW.mkdir(parents=True, exist_ok=True)
    # P1-2：O_EXCL 原子锁申请——判定与写入之间的竞态窗口闭合（双通道并发
    # 只有一方能创建成功；失败方若见活锁即退出，陈旧锁被清除后重试一次）
    lock_claimed = False
    for _ in range(2):
        try:
            fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            payload = json.dumps({"ts": datetime.now(timezone.utc).timestamp(),
                                  "tree": tree["treeId"]})
            os.write(fd, payload.encode("utf-8"))
            os.close(fd)
            lock_claimed = True
            break
        except FileExistsError:
            if _lock_stale_or_absent(cfg):
                continue  # 陈旧锁已清除，重试申请
            print("live session running, skip spawn")
            return 0
    if not lock_claimed:
        print("lock contention, skip spawn")
        return 0
    brief = BRIEF_V2.format(tick_id=now.strftime("%Y%m%dT%H%M%SZ"), tree_path=tree["path"])
    brief_path = SHADOW / ("brief-%s.md" % now.strftime("%Y%m%dT%H%M%SZ"))
    brief_path.write_text(brief, encoding="utf-8")

    cmd = ["claude", "-p",
           "读取 %s 并严格执行其全部指令。" % brief_path,
           # P1-4：显式钉模型——防 HOME 配置漂移（141800Z 会话 ox-alpha 404 秒死事故）
           "--model", cfg.get("default_model", "glm-5.3"),
           # 执行通道扩展（2026-08-27 p0fix1 blocked 复盘）：代码修复树需要
           # 构建/测试/仓库整备命令；此前仅 git 写三件+mkdir/ls，npm/tsc 全被挡
           "--allowedTools", "Read", "Glob", "Grep", "Write", "Edit",
           "Bash(git add:*)", "Bash(git commit:*)", "Bash(git push:*)",
           "Bash(git fetch:*)", "Bash(git rebase:*)", "Bash(git checkout:*)",
           "Bash(git branch:*)", "Bash(git merge:*)", "Bash(git cherry-pick:*)",
           "Bash(git status:*)", "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)",
           "Bash(git -C:*)", "Bash(git pull:*)", "Bash(git restore:*)",
           "Bash(npm test:*)", "Bash(npm run:*)", "Bash(npm install:*)", "Bash(npm ci:*)",
           "Bash(npx tsc:*)", "Bash(node:*)", "Bash(python3:*)", "Bash(python3.8:*)",
           "Bash(mkdir:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)",
           "Bash(wc:*)", "Bash(grep:*)", "Bash(find:*)", "Bash(cp:*)", "Bash(mv:*)",
           "Bash(touch:*)", "Bash(diff:*)", "Task",
           "--output-format", "json"]
    env = dict(os.environ, HOME="/home/fleet")
    # spawn cwd 按树路由（2026-08-27 p0fix1 复盘二）：代码树的 tree.repo 字段
    # 给出工作仓路径——会话在仓内直接用裸命令（git status 等），杜绝
    # 「cd X && git …」复合前缀被权限引擎整串拒的形式性问题（D-11）
    repo_field = str(tree.get("repo", "") or "")
    m_repo = re.match(r"(/\S+)", repo_field)
    spawn_cwd = REPO
    if m_repo and Path(m_repo.group(1)).exists():
        spawn_cwd = Path(m_repo.group(1))
    elif repo_field:
        print("tree.repo unparseable/missing (%r), fallback cwd=%s" % (repo_field[:60], spawn_cwd))
    try:
        # 异步发射：Popen 不阻塞——CC 会话独立运行，下轮 tick 检查进度
        # （修复：同步等待导致 trimc 600s timeout 杀死长任务，连续 52 次）
        log_path = SHADOW / ("orchestrator-session-%s.log" % now.strftime("%Y%m%dT%H%M%SZ"))
        log_fh = open(log_path, "w")
        proc = subprocess.Popen(cmd, cwd=str(spawn_cwd), env=env,
                                stdout=log_fh, stderr=subprocess.STDOUT)
        log_fh.close()
        print("spawned detached PID=%d tree=%s" % (proc.pid, tree["treeId"]))
    except Exception as e:
        try:
            LOCK_PATH.unlink()
        except Exception:
            pass
        notify("[TriMMC][N3] 编排会话发射失败", "tick %s 树 %s: %s" % (now.isoformat(), tree["treeId"], str(e)[:200]))
        return 1

    # 异步模式：发射后立即返回，不等待 CC 会话完成
    # 进度追踪由下一轮 tick 通过 git/tree status 判断
    # P0-1①：锁内补记 spawn pid——下轮 tick 走精确存活判定（进程死即释放）
    try:
        LOCK_PATH.write_text(json.dumps({"ts": datetime.now(timezone.utc).timestamp(),
                                         "tree": tree["treeId"], "pid": proc.pid}))
    except Exception:
        pass
    reg = load_registry()
    reg.setdefault("ticks", []).append({"tick": now.isoformat(), "ts_epoch": time.time(),
                                        "tree": tree["treeId"], "rc": "spawned",
                                        "pid": proc.pid, "trigger": args.trigger})
    save_registry(reg)
    FINGERPRINT_PATH.write_text(fp, encoding="utf-8")
    print("async spawn OK pid=%d" % proc.pid)
    return 0

if __name__ == "__main__":
    sys.exit(main())
