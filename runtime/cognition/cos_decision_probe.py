"""cos-score 落卷探测探针（D3 层 2 互补件·ceo_ruling_probe.py 同构仿形）。

轮询面互补件（③主形=preflight 族轮间门为判决判定·本探针只管「判决落卷即知」
知会面）：tick 宿调本探针——上轮 run_dir cos-score.json 在场（state=evolve|hold）
且未登记知会→_notify_blocking 知会值席（round-state 推进面·候选轮层 2 门消费）
→知会登记防重（.done 标记·幂等）；缺席（awaiting-decision）→静默 exit 0（轮询
面常态·缺席催办=cos_decision_gate 72h 面承·本探针零重复）。

判定单值源=cos_decision_gate.check_cos_decision（零重复实现·同源防判定漂移）。
知会登记位=TRICO_COS_PROBE_STATE_DIR（缺省 /var/lib/trirmc/cos-decision-probe）。
零密值零敏感面（D-46）·never raises（探测面零阻 tick 本体——payload 调用尾
|| true 同款）。

退出码：0=常态（知会发/静默/登记过）；2=探测面异常（如实 exit 面审计·零阻 tick）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

RUNS_ROOT_DEFAULT = "/var/lib/trirmc/cron/runs"
STATE_DIR_DEFAULT = "/var/lib/trirmc/cos-decision-probe"


def main() -> int:
    from runtime.cognition.cos_decision_gate import check_cos_decision

    runs_root = os.environ.get("TRICO_PREV_RUNS_ROOT", RUNS_ROOT_DEFAULT)
    state_dir = Path(os.environ.get("TRICO_COS_PROBE_STATE_DIR", STATE_DIR_DEFAULT))
    try:
        reading = check_cos_decision(runs_root)
    except Exception as e:  # noqa: BLE001 — 探测面零炸 tick（never raises 承面）
        print(f"[cos-decision-probe] probe failed: {type(e).__name__}: {e}"[:200],
              file=__import__("sys").stderr, flush=True)
        return 2
    state = reading.get("state")
    prev = reading.get("prev_run_dir")
    if state not in ("evolve", "hold") or not prev:
        return 0  # awaiting-decision/skip=静默（轮询面常态·催办面=cos-gate 72h 承）
    state_dir.mkdir(parents=True, exist_ok=True)
    done_mark = state_dir / f"{prev}.notified"
    if done_mark.is_file():
        return 0  # 已知会（防重·幂等）
    try:
        from runtime.cognition.weekly_plane_shift import _notify_blocking
        to = [x.strip() for x in (os.environ.get(
            "TRICO_RULING_ESCALATE_TO", "").split(",")) if x.strip()]
        failures = _notify_blocking(
            subject=f"[probe] cos-score 落卷知会（{prev}·state={state}）",
            body=f"上轮 run={prev} cos-score.json 在场（eviction_decision={state}"
                 f"·rationale={reading.get('rationale')}·双分数="
                 f"{reading.get('scores')}）——round-state 推进面知会："
                 "候选轮层 2 门消费（evolve=迭代放行候选·hold=判止候选——"
                 "与层 1 ceo-ruling AND 门并读）",
            to=to, context_id=f"cos-decision-probe-{prev}",
        )
        done_mark.write_text(json.dumps({
            "notified_at_state": state, "failures": failures,
        }, ensure_ascii=False), encoding="utf-8")
        print(f"[cos-decision-probe] {prev} state={state} 知会毕 "
              f"(failures={len(failures)})", flush=True)
    except Exception as e:  # noqa: BLE001 — 知会面零炸 tick
        print(f"[cos-decision-probe] notify failed: {type(e).__name__}: {e}"[:200],
              file=__import__("sys").stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
