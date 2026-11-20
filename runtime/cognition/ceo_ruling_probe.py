"""ceo-ruling 在场探测探针（notice-202·CTO 荐案①探测机制·rmc-orchestrate-tick 宿）。

轮询面互补件（③主形=preflight 轮间门为裁决判定·本探针只管「裁决落卷即知」知会面）：
  tick（17/47 分）宿调本探针——上轮 run_dir ceo-ruling.json 在场（state=
  continue|terminate）且未登记知会→_notify_blocking 知会值席（round-state
  推进面·候选轮轮间门消费）→知会登记防重（.done 标记·幂等）；
  缺席（awaiting）→静默 exit 0（轮询面常态·缺席催办=preflight gate 72h 面承·
  本探针零重复）。

判定单值源=preflight.check_ceo_ruling（零重复实现·同源防判定漂移）。
知会登记位=TRICO_RULING_PROBE_STATE_DIR（缺省 /var/lib/trirmc/ceo-ruling-probe）。
零密值零敏感面（D-46）·never raises（探测面零阻 tick 本体——payload 调用尾 || true）。

退出码：0=常态（知会发/静默/登记过）；2=探测面异常（如实 exit 面审计·零阻 tick）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

RUNS_ROOT_DEFAULT = "/var/lib/trirmc/cron/runs"
STATE_DIR_DEFAULT = "/var/lib/trirmc/ceo-ruling-probe"


def main() -> int:
    from runtime.cognition.preflight import check_ceo_ruling

    runs_root = os.environ.get("TRICO_PREV_RUNS_ROOT", RUNS_ROOT_DEFAULT)
    state_dir = Path(os.environ.get("TRICO_RULING_PROBE_STATE_DIR", STATE_DIR_DEFAULT))
    reading = check_ceo_ruling(runs_root)
    state = reading.get("state")
    prev = reading.get("prev_run_dir")
    if state not in ("continue", "terminate") or not prev:
        return 0  # awaiting/skip=静默（轮询面常态·催办面=preflight gate 承）
    state_dir.mkdir(parents=True, exist_ok=True)
    done_mark = state_dir / f"{prev}.notified"
    if done_mark.is_file():
        return 0  # 已知会（防重·幂等）
    try:
        from runtime.cognition.weekly_plane_shift import _notify_blocking
        to = [x.strip() for x in (os.environ.get(
            "TRICO_RULING_ESCALATE_TO", "").split(",")) if x.strip()]
        failures = _notify_blocking(
            subject=f"[probe] ceo-ruling 落卷知会（{prev}·state={state}）",
            body=f"上轮 run={prev} ceo-ruling.json 在场（decision={state}"
                 f"·ruling_ref={reading.get('ruling_ref')}·signed_at="
                 f"{reading.get('signed_at')}）——round-state 推进面知会："
                 "候选轮轮间门消费（continue=下轮照跑/terminate=job 停用面值席执行）",
            to=to, context_id=f"ruling-probe-{prev}",
        )
        done_mark.write_text(json.dumps({
            "notified_at_state": state, "failures": failures,
        }, ensure_ascii=False), encoding="utf-8")
        print(f"[ruling-probe] {prev} state={state} 知会毕 "
              f"(failures={len(failures)})", flush=True)
    except Exception as e:  # noqa: BLE001 — 知会面零炸 tick
        print(f"[ruling-probe] notify failed: {type(e).__name__}: {e}"[:200],
              file=__import__("sys").stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
