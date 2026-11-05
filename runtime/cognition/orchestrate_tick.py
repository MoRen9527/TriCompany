"""orchestrate_tick — TriMMC 7×24 编排工作循环（M2 正身·形二席组形改造 2026-11-05）

形态定谳：CEO 2026-11-05 17:04:22（两域服务域编排统一=M 面本地域同款席组形·
非 headless CC）→CTO 形二方案卷 cto-form2-unification-plan.md（TMV 2427a0f3f）
→COO 派工单 v1.0（TMV 938b8036a）。本版=形二 sg 侧改造正身。

单次 tick 职责（由 trimc cron 每 30 分钟调用·13,43 * * * * runAs fleet）：
  1. 三重门待办评估：扫描 operating-records 各周 trees/*/tree-op.json，
     仅收 status=active 且 domainRouting=server-executable 且存在 pending
     节点且无未到期时间门的树（P1 准入门的确定性实现）
  2. 待办集指纹：变化才动作（P2 边沿触发）
  3. 成本护栏：读月度台账，超上限则拒绝派单并一次性发降级通知
  4. 派单 duty-cos（形二席组形）：POST trimmc :8712/internal/v1/notify
     （source=bod 白名单合规·target=m-duty-cos）+ 必跟 tmux send-keys 唤醒
     （normal notify 只落箱不唤醒 idle 值席——信到箱≠信到人现行纪律正形）；
     非 headless CC spawn（M2 原形随形态定谳退役）
  5. 派单审计：registry ticks 行（rc=dispatched）+ ledger 派单事件行
     （事件 ts+任务书指针+message_id+tmux 拾取）——成本面走 CFO 既有 token
     实测协议口径（perf 线），本循环不再解析 usage 记账（防双记账）

幂等语义（形二）：spawn 会话超时语义退役（人在环无超时）——派单幂等键=
树指纹边沿（同指纹不重派）+rc=dispatched 30 分钟冷却窗（现形 last.rc 判定
自然保留）+O_EXCL 派单锁（防同窗双发·派单毕即释放）。

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
import urllib.request
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path("/srv/fleet/TriMetaverse")
PLANE = REPO / "docs/workflow/operating-records"
SHADOW = Path("/srv/fleet/shadow-plane")
LEDGER_PATH = SHADOW / "cost-ledger.json"
REGISTRY_PATH = SHADOW / "session-registry.json"
FINGERPRINT_PATH = SHADOW / "tick-fingerprint.txt"
CONFIG_PATH = Path.home() / ".trimetaverse" / "orchestration.json"

# 形二派单面（CTO 方案卷 §二）：sg trimmc 8712 notify 现役端点。
NOTIFY_URL = "http://127.0.0.1:8712/internal/v1/notify"
NOTIFY_BODY_MAX_BYTES = 4096  # 与 TriMMC outbox 硬门对齐（413 拒收线）
DISPATCH_COOLDOWN_S = 1800  # 成功派单冷却窗（30min·微批件三·冷却判据显式化常量）
SOURCE_SEAT = "bod"  # SOURCE_SEAT_WHITELIST 在列；CEO 令语义=bod 通知 duty-cos
TARGET_SEAT_DEFAULT = "m-duty-cos"
TARGET_DAEMON = "trimmc"  # TARGET_SEAT_ROSTER['m-duty-cos'].daemon
TOKEN_ENV_FALLBACK = Path("/srv/fleet/TriMMC/docker/.env")  # fleet 600 副本（先例 duty-urge-patrol 同源·10-21 轮换窗双写）

# 价格表（权威源 api-docs.deepseek.com/quick_start/pricing，2026-08-25 取数，
# USD per 1M tokens，[off-peak, peak]）；形二 headless 退役后存量收割器仍在
# （存量 log 幂等清账），新派单不再产生 usage 面。价格变动须重取数并更新 as-of。
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
    ① 锁龄 > 2×timeout（僵尸兜底）② 锁内 pid 已死（spawn 后锁内补记 pid——
    形二派单锁无 pid，走④）③ 台账反查该树 spawn pid 已死 ④ 无 pid 可查且
    锁龄 > 300s（短阈值判死，**禁止默认拒斥**）。
    陈旧即删除锁文件并返回 True。形二锁职能=派单窗互斥（秒级），派毕即释。"""
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
    """True=允许派单。双门：每日 token 上限（CEO 08-25：免费模型按量控制 15 亿/日）+ 月度金额兜底。
    形二注：读数源=存量 usage 台账（历史数据）+CFO perf 线口径承接新成本面——
    护栏语义保留（超限即拒派），读数滞后性如实存在（值席会话成本不在本台账）。"""
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


DISPATCH_NOTICE = """[形二编排派单] tick {tick_id}

任务书指针：{tree_path}
树 ID：{tree_id}（{n_pending} 节点 pending{gated_note}）

接令语（CEO 形态定谳 2026-11-05 17:04:22）：你是 duty-cos 值席——按 D-27 树协议
拆树派工（duty-coo 协作·席组班组一气呵成·SendMessage 结构化通道），非 headless。
毕报回链=树节点收口（照 D-15）+顶层 status=done 收口 commit。

指纹：{fp}｜触发：{trigger}｜派单幂等键=本指纹（同指纹不重派）。
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
    形二注：headless spawn 退役后本收割器仅对存量 orchestrator-session-*.log
    幂等清账（harvested 集合恒跳过·零开销），保留至存量清毕窗口移除。"""
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
            try:
                reg = load_registry()
                stamp_digits = re.sub(r"\D", "", name)  # 20260827T104205Z -> 20260827104205
                subtype = obj.get("subtype")
                derived = 0 if subtype == "success" else 1
                for t in reversed(reg.get("ticks", [])):
                    tick_digits = re.sub(r"\D", "", str(t.get("tick", "")))[:14]
                    if stamp_digits[:14] == tick_digits and t.get("rc") in ("spawned", 1, "1"):
                        t["rc"] = derived
                        t["rc_source"] = "harvest-close-cli"
                        save_registry(reg)
                        break
            except Exception:
                pass
        except Exception:
            continue
    return added


def _trimmc_token() -> str:
    """notify 门 token 读源（fail-closed 同构）：①进程 env（TriMMC cron 子进程
    继承 daemon env——cron 拍形态正源）②回退 /srv/fleet/TriMMC/docker/.env
    fleet 600 副本提取（先例 duty-urge-patrol.py 同源·manual/sudo 形态兜底；
    KEY=VAL 形按首个 = 切值段）③两者皆无=空串（调用方 fail-closed 不派单·
    留痕降级）。注：unit drop-in override.conf=600 root 不可读——通道废弃
    （实测 2026-11-05 首拍 fail-closed 触发归因）。token 值面零打印（D-46）。"""
    tok = (os.environ.get("TRIMC_INTERNAL_TOKEN") or "").strip()
    if tok:
        return tok
    try:
        for line in TOKEN_ENV_FALLBACK.read_text(encoding="utf-8").splitlines():
            if line.startswith("TRIMC_INTERNAL_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def _duty_tmux_target() -> tuple[list[str], str]:
    """唤醒目标构造：与 daemon duty-consumer 同源 env 键（TRIMC_NOTIFY_DUTY_TMUX
    /TRIMC_NOTIFY_DUTY_TMUX_SOCK）——cron 子进程继承 daemon env；缺省回退
    m-duty-cos+默认 socket（fleet uid default=/tmp/tmux-<uid>/default·13 席在役形）。"""
    sock = (os.environ.get("TRIMC_NOTIFY_DUTY_TMUX_SOCK") or "").strip()
    seat = (os.environ.get("TRIMC_NOTIFY_DUTY_TMUX") or TARGET_SEAT_DEFAULT).strip()
    sock_args = ["-S", sock] if sock else []
    return sock_args, seat


def _tmux_wake(seat: str, summary: str, timeout_s: float = 12.0, tree_token: str = "") -> dict:
    """tmux send-keys 唤醒（现行纪律正形）：信体单行摘要→独立补发 Enter
    （bracketed paste 吞 Enter 坑）→capture-pane 验拾取（对话流增量=接令实锚）。
    返回 {delivered: bool, probe: str}——失败不抛（notify 信箱通道已在·此为
    快通道；False 留痕供审计+人工兜底）。"""
    sock_args, _ = _duty_tmux_target()
    deadline = time.time() + timeout_s
    probe = ""
    try:
        subprocess.run(["tmux"] + sock_args + ["send-keys", "-t", seat, summary],
                       capture_output=True, timeout=10)
        time.sleep(1.5)
        subprocess.run(["tmux"] + sock_args + ["send-keys", "-t", seat, "Enter"],
                       capture_output=True, timeout=10)  # 独立补发 Enter
        while time.time() < deadline:
            time.sleep(1.5)
            cap = subprocess.run(["tmux"] + sock_args + ["capture-pane", "-t", seat, "-p"],
                                 capture_output=True, timeout=10)
            probe = cap.stdout.decode("utf-8", "replace")[-600:]
            # 拾取判据：摘要关键词（编排派单/树 ID 前段）出现在 pane 近尾
            if "编排派单" in probe or (tree_token and tree_token in probe):
                return {"delivered": True, "probe": probe[-200:]}
            subprocess.run(["tmux"] + sock_args + ["send-keys", "-t", seat, "Enter"],
                           capture_output=True, timeout=10)  # 二次补发
        return {"delivered": False, "probe": probe[-200:]}
    except Exception as e:
        return {"delivered": False, "probe": "tmux error: %s" % e}


def _notify_duty_cos(tree: dict, cfg: dict, now: datetime, fp: str, trigger: str) -> dict:
    """形二 step4：notify 落箱（慢通道·信箱持久）+tmux send-keys 唤醒（快通道·
    立即拾取验证）双保险。返回 {ok, message_id, tmux_delivered, error}。"""
    tree_token = str(tree.get("treeId", ""))[:24]  # 拾取判据辅助（参数传值·微批件一·global 形退役）
    tick_id = now.strftime("%Y%m%dT%H%M%SZ")
    gated_note = "（另有 %d 节点时间门未到期）" % len(tree.get("gatedNodes", [])) if tree.get("gatedNodes") else ""
    body = DISPATCH_NOTICE.format(tick_id=tick_id, tree_path=tree["path"],
                                  tree_id=tree["treeId"], n_pending=len(tree["pendingNodes"]),
                                  gated_note=gated_note, fp=fp, trigger=trigger)
    if len(body.encode("utf-8")) > NOTIFY_BODY_MAX_BYTES:
        body = body.encode("utf-8")[:NOTIFY_BODY_MAX_BYTES].decode("utf-8", "ignore")  # 字节安全截断（微批件二·字符切可超字节门·CJK 3B/字）
    summary = "[编排派单 %s] 树 %s（%d 节点 pending）候接令拆树派工——详情见信箱(bod→%s)或读树 %s" % (
        tick_id, tree["treeId"], len(tree["pendingNodes"]), TARGET_SEAT_DEFAULT, tree["path"])

    token = _trimmc_token()
    if not token:
        return {"ok": False, "message_id": "", "tmux_delivered": False,
                "error": "no token (fail-closed: env+unit drop-in 皆无)"}
    payload = json.dumps({
        "source_seat": SOURCE_SEAT,
        "target_daemon": TARGET_DAEMON,
        "target_seat": TARGET_SEAT_DEFAULT,
        "urgent": "normal",
        "title": "[形二编排派单] 树 %s（%d 节点 pending）候接令" % (tree["treeId"], len(tree["pendingNodes"])),
        "body": body,
    }).encode()
    req = urllib.request.Request(NOTIFY_URL, data=payload,
                                 headers={"content-type": "application/json",
                                          "X-Internal-Token": token},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            out = json.loads(resp.read().decode("utf-8", "replace"))
        if not out.get("ok"):
            return {"ok": False, "message_id": "", "tmux_delivered": False,
                    "error": "notify rejected: %s" % json.dumps(out, ensure_ascii=False)[:300]}
        message_id = str(out.get("message", {}).get("message_id", "") or out.get("message_id", ""))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        return {"ok": False, "message_id": "", "tmux_delivered": False,
                "error": "HTTP %d: %s" % (e.code, detail)}
    except Exception as e:
        return {"ok": False, "message_id": "", "tmux_delivered": False,
                "error": "notify error: %s" % e}
    wake = _tmux_wake(TARGET_SEAT_DEFAULT, summary, tree_token=tree_token)
    return {"ok": True, "message_id": message_id,
            "tmux_delivered": wake["delivered"], "error": "" if wake["delivered"] else "tmux probe no pickup"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只评估门与预算，不派单不写状态")
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
        # 战役续跑模式（形二幂等）：指纹未变+冷却窗外+锁空闲 → 重派推进长战役
        # （duty-cos 侧有同树施工中的接令纪律，重派=提醒形）。冷却判据显式化
        # （微批件三·CTO 裁定正形 rc=="dispatched" and age<1800）：旧形 rc==0
        # 系字符串与整数比较恒 False 死分支勘正——失败（dispatch-failed）下拍
        # 即重试（fail-closed 失败不写指纹·不进本分支重派面）
        reg_now = load_registry()
        ticks = reg_now.get("ticks", [])
        last = ticks[-1] if ticks else None
        last_age_s = time.time() - last.get("ts_epoch", 0) if last else 1e9
        cooldown_active = (bool(last) and last.get("rc") == "dispatched"
                           and last_age_s < DISPATCH_COOLDOWN_S)
        eligible = (bool(last) and not cooldown_active and _lock_stale_or_absent(cfg))
        if not (actionable and last and eligible):
            return 0
        notify_skip = True
    else:
        notify_skip = False
    if not ok:
        notify("[TriMMC][E3] 编排降级", budget_msg)
        return 1

    # 派单锁护栏（O_EXCL 原子申请·防双通道并发双派——判定与写入竞态闭合）
    tree = actionable[0]
    SHADOW.mkdir(parents=True, exist_ok=True)
    lock_claimed = False
    for _ in range(2):
        try:
            fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            payload = json.dumps({"ts": datetime.now(timezone.utc).timestamp(),
                                  "tree": tree["treeId"], "mode": "form2-dispatch"})
            os.write(fd, payload.encode("utf-8"))
            os.close(fd)
            lock_claimed = True
            break
        except FileExistsError:
            if _lock_stale_or_absent(cfg):
                continue  # 陈旧锁已清除，重试申请
            print("live dispatch window, skip")
            return 0
    if not lock_claimed:
        print("lock contention, skip dispatch")
        return 0

    # ── 形二 step4：notify duty-cos + tmux 唤醒（spawn headless CC 段退役）──
    disp = _notify_duty_cos(tree, cfg, now, fp, args.trigger)

    # 派单毕即释锁（锁职能=派单窗互斥秒级；幂等由指纹+冷却窗承担）
    try:
        LOCK_PATH.unlink()
    except Exception:
        pass

    # ── 形二 step5：派单审计行（防双记账——成本面走 CFO perf 线口径）──
    reg = load_registry()
    reg.setdefault("ticks", []).append({
        "tick": now.isoformat(), "ts_epoch": time.time(),
        "tree": tree["treeId"], "treePath": tree["path"],
        "pendingNodes": tree["pendingNodes"],
        "rc": "dispatched" if disp["ok"] else "dispatch-failed",
        "message_id": disp["message_id"],
        "tmux_delivered": disp["tmux_delivered"],
        "dispatch_error": disp["error"][:200],
        "trigger": args.trigger, "mode": "form2"})
    save_registry(reg)
    ledger.setdefault("dispatches", []).append({
        "ts": now.isoformat(), "tree": tree["treeId"], "treePath": tree["path"],
        "message_id": disp["message_id"], "notify_ok": disp["ok"],
        "tmux_delivered": disp["tmux_delivered"], "trigger": args.trigger})
    _save_ledger(ledger)
    if disp["ok"]:
        FINGERPRINT_PATH.write_text(fp, encoding="utf-8")  # 派单成功才写指纹（失败下轮重试）
        print("form2 dispatch OK tree=%s mid=%s tmux=%s"
              % (tree["treeId"], disp["message_id"] or "-", disp["tmux_delivered"]))
        return 0
    print("form2 dispatch FAILED tree=%s: %s" % (tree["treeId"], disp["error"][:200]))
    return 1

if __name__ == "__main__":
    sys.exit(main())
