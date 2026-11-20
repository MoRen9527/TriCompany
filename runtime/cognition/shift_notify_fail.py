"""shift_notify_fail — 周迁移链兜底告警（P1 改点 C·CTO 任务书 TMV fa69fcd9d）。

cron 链形（TriRMC 9c81c7ec PATCH 尾部追加）:
  (原 && 全链) || { E=$?; cd /srv/fleet/TriCompany && \
    python3 -m runtime.cognition.shift_notify_fail --chain-exit "$E"; }

链跑路径主防线（CTO 裁定②分工表述——与改点 A preflight 非冗余）：
覆盖链体任一段死（含 pull 段 exit 128 = 19.5h/45h 静默本体）→ SMTP 双址
blocking 告警「迁移链 exit N + 阶段探读数」。阶段探=两检出 HEAD/脏面只读
快照（零 token 读取·值面禁密）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

TC_REPO = "/srv/fleet/TriCompany"
TMV_REPO = "/srv/fleet/TriMetaverse"


def _stage_evidence() -> dict:
    ev: dict = {"check_time": datetime.now(timezone.utc).isoformat()}
    for name, repo in (("tmv", TMV_REPO), ("tc", TC_REPO)):
        try:
            head = subprocess.run(
                ["git", "-C", repo, "log", "-1", "--format=%h %cI %s"],
                capture_output=True, text=True, timeout=15).stdout.strip()
            dirty = subprocess.run(
                ["git", "-C", repo, "status", "--porcelain"],
                capture_output=True, text=True, timeout=15).stdout.splitlines()
            ev[name] = {"head": head[:160], "dirty_lines": len(dirty)}
        except Exception as e:
            ev[name] = {"error": str(e)[:200]}
    return ev


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="weekly shift chain fallback alerter (P1 C)")
    p.add_argument("--chain-exit", default="unknown", help="exit code of the failed chain")
    args = p.parse_args(argv)

    # F1 exit-code-aware 补丁（CTO 复验卷 cto-notice202-wait-semantics-reverify
    # -20261119 候批项·值席域裁批准·2026-11-19 SDE 落码）：
    #   exit 4（awaiting-ruling 挂起）=设计内态非链失败——静默 log 形（两形择一
    #   勘定=形 B）：零 SMTP（每窗双址误框噪音消除）·催办语义单值源=轮间门 gate
    #   72h 催办面（重叠错位消除）·观测面=stdout（cron journal 可读）。
    #   exit 5（terminated 停用）=一次性停用事件——SMTP 停用知会形（非链失败
    #   语义·distinct subject）。
    #   其余码=链失败语义照旧（P1 改点 C 原形零动）。
    if str(args.chain_exit) == "4":
        print("[shift_notify_fail] exit=4 awaiting-ruling 挂起（设计内态·静默 log"
              "——零 SMTP·催办语义=轮间门 gate 72h 催办面单值源·F1 补丁形 B）",
              flush=True)
        return 0
    if str(args.chain_exit) == "5":
        sys.path.insert(0, TC_REPO)
        from runtime.cognition.weekly_plane_shift import _notify_blocking, _resolve_notify_to
        ev = _stage_evidence()
        failures = _notify_blocking(
            subject=f"[TriCade] 周平面迁移 terminated 停用知会 exit=5 {ev['check_time'][:10]}",
            body=("链 exit 5=terminated（CEO 裁决 terminate·轮间门定谳）——job 停用面"
                  "=值席执行 cron disable（本知会=停用事件 SMTP 面·非链失败语义·F1 补丁）\n"
                  "阶段探读数:\n" + json.dumps(ev, ensure_ascii=False, indent=2)),
            to=_resolve_notify_to(),
            context_id="weekly-shift-terminated",
        )
        if failures:
            print(json.dumps({"alert": "failed", "notify_failures": failures,
                              "chain_exit": args.chain_exit, "evidence": ev},
                             ensure_ascii=False), file=sys.stderr)
            return 5
        print("[shift_notify_fail] terminated 停用知会 sent (dual-address blocking)")
        return 0

    sys.path.insert(0, TC_REPO)
    from runtime.cognition.weekly_plane_shift import _notify_blocking, _resolve_notify_to

    ev = _stage_evidence()
    failures = _notify_blocking(
        subject=f"[TriCade] 周平面迁移链失败告警 exit={args.chain_exit} {ev['check_time'][:10]}",
        body=("周迁移链非零退出（|| 兜底分支·P1 改点 C）\n链 exit 码: " + str(args.chain_exit)
              + "\n阶段探读数:\n" + json.dumps(ev, ensure_ascii=False, indent=2)),
        to=_resolve_notify_to(),
        context_id="weekly-shift-chain-fail",
    )
    if failures:
        print(json.dumps({"alert": "failed", "notify_failures": failures,
                          "chain_exit": args.chain_exit, "evidence": ev},
                         ensure_ascii=False), file=sys.stderr)
        return 5  # 兜底自身告警发不出 = 可观测（stderr 入 cron journal lastError 面）
    print("[shift_notify_fail] chain-fail alert sent (dual-address blocking)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
