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
        "default_model": "deepseek-v4-flash",
        "session_timeout_s": 560,
        "tick_max_sessions": 1,
    }
    try:
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


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
    """True=允许 spawn。超限返回 False 与降级说明。"""
    spent_cny = ledger["totals"].get("cost_cny", 0.0)
    if spent_cny >= cfg["budget_cny_monthly"]:
        return False, "月度成本 %.2f 元已超上限 %.0f 元——自动降级：仅影子试跑+人工触发（CEO Q-C 裁决）" % (spent_cny, cfg["budget_cny_monthly"])
    return True, "月度成本 %.2f/%.0f 元" % (spent_cny, cfg["budget_cny_monthly"])


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只评估门与预算，不 spawn 不写状态")
    args = ap.parse_args()
    cfg = _load_config()
    now = datetime.now(timezone.utc)

    actionable, fp = evaluate_backlog()
    prev_fp = FINGERPRINT_PATH.read_text(encoding="utf-8").strip() if FINGERPRINT_PATH.exists() else ""
    ledger = _load_ledger()
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
        return 0  # 指纹未变：上一 tick 已处理或在跑，静默
    if not ok:
        notify("[TriMMC][E3] 编排降级", budget_msg)
        return 1

    tree = actionable[0]
    brief = BRIEF_V2.format(tick_id=now.strftime("%Y%m%dT%H%M%SZ"), tree_path=tree["path"])
    SHADOW.mkdir(parents=True, exist_ok=True)
    brief_path = SHADOW / ("brief-%s.md" % now.strftime("%Y%m%dT%H%M%SZ"))
    brief_path.write_text(brief, encoding="utf-8")

    cmd = ["claude", "-p",
           "读取 %s 并严格执行其全部指令。" % brief_path,
           "--allowedTools", "Read", "Glob", "Grep", "Write", "Edit",
           "Bash(git add:*)", "Bash(git commit:*)", "Bash(git push:*)",
           "Bash(git status:*)", "Bash(git log:*)", "Bash(mkdir:*)", "Bash(ls:*)", "Task",
           "--output-format", "json"]
    env = dict(os.environ, HOME="/home/fleet")
    try:
        # 本脚本经 trimc cron 以 fleet 身份执行（runAs），子进程自然继承，无需再降级
        proc = subprocess.run(cmd, cwd=str(REPO), env=env,
                              timeout=cfg["session_timeout_s"],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except subprocess.TimeoutExpired:
        notify("[TriMMC][N3] 编排会话超时", "tick %s 树 %s 会话超时被回收（%ss）。" % (now.isoformat(), tree["treeId"], cfg["session_timeout_s"]))
        return 1

    out = proc.stdout or ""
    usage = {}
    try:
        j = json.loads(out.strip().splitlines()[-1])
        usage = j.get("usage", {}) or {}
        u = usage
        cost = _session_cost_usd(cfg["default_model"],
                                 int(u.get("cache_read_input_tokens", 0)),
                                 int(u.get("input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0)),
                                 int(u.get("output_tokens", 0)), _is_peak(now))
    except Exception:
        cost = 0.0
    ledger["sessions"].append({"ts": now.isoformat(), "tree": tree["treeId"], "model": cfg["default_model"],
                               "usage": usage, "cost_usd": round(cost, 4),
                               "cost_cny": round(cost * cfg["usd_cny"], 4), "peak": _is_peak(now)})
    ledger["totals"]["cost_usd"] = round(ledger["totals"].get("cost_usd", 0.0) + cost, 4)
    ledger["totals"]["cost_cny"] = round(ledger["totals"]["cost_usd"] * cfg["usd_cny"], 4)
    _save_ledger(ledger)

    reg = load_registry()
    reg.setdefault("ticks", []).append({"tick": now.isoformat(), "tree": tree["treeId"],
                                        "rc": proc.returncode, "cost_cny": round(cost * cfg["usd_cny"], 4)})
    save_registry(reg)
    FINGERPRINT_PATH.write_text(fp, encoding="utf-8")

    notify("[TriMMC][N1] 编排开工", "tick %s 开始执行树 %s（待办节点 %s）。会话 rc=%s，本次成本 %.4f 元。\n%s"
           % (now.isoformat(), tree["treeId"], tree["pendingNodes"], proc.returncode,
              cost * cfg["usd_cny"], out[-600:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
