"""duty_collection 自动采集生成器（notice-214 款一·③自动采集窗＋死信标注）。

A2-3 调度漏根修（七席意见修法共识「trigger 链排 T+10min 自动采集窗·首采禁靠
值席人手」）——采集生成器（T+10min 窗形）：
  tick 宿（17/47 分）调本探针——joint-review-trigger.json 落卷时点 +10min ≤
  now 且 collection-score.json 缺→**自动采集生成**（run_dir 段产物聚合→
  collection-score.json 对 score_engine._judge_collection 消费面契约：
  {score_version, run_id, entries[{family_id, verdict, rationale, evidence_ref}],
  check_time}）；窗未到/已落卷=静默 exit 0（幂等零重复）。

判据面：七段 verdict 全 pass→entry verdict=pass；任一缺/fail→fail（机器采集
客观面·禁部分分同制）。死信标注联动面：malformed 死信案（plan dead_letter）
不阻 collection 判（死信=标注态非阻断·notice-214 款一承）。

never raises（探测面零阻 tick 本体——payload 调用尾 || true）·零密值（D-46）。
"""
from __future__ import annotations

import json as _json
import os
from datetime import datetime, timezone
from pathlib import Path

COLLECTION_WINDOW_MIN = 10  # T+10min 自动采集窗（A2-3 修法面）
_RUN_STAGES = (
    "preflight.json", "qualify.json", "plan.json", "dce.json",
    "verify.json", "score.json", "close.json",
)


def _parse_ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def run(run_dir: Path, now: datetime | None = None) -> tuple[int, dict]:
    now = now or datetime.now(timezone.utc)
    out: dict = {"collector_version": "1.0.0", "run_id": "", "action": "skip"}
    trigger_path = run_dir / "joint-review-trigger.json"
    if not trigger_path.is_file():
        out["reason"] = "joint-review-trigger.json 缺（skip）"
        return 0, out
    try:
        trig = _json.loads(trigger_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        out["reason"] = f"trigger unparsable: {e}"
        return 0, out
    out["run_id"] = trig.get("loop_run_id", "")
    out_path = run_dir / "collection-score.json"
    if out_path.is_file():
        out["action"] = "already_collected（幂等零重复）"
        return 0, out
    t0 = _parse_ts(str(trig.get("trigger_time", "")))
    if t0 is None:
        out["reason"] = "trigger_time unparsable（skip）"
        return 0, out
    elapsed_min = (now - t0).total_seconds() / 60
    if elapsed_min < COLLECTION_WINDOW_MIN:
        out["reason"] = (f"T+{elapsed_min:.1f}min<{COLLECTION_WINDOW_MIN}min"
                         "（窗未到·下 tick 再探）")
        return 0, out
    # 窗到——自动采集生成（段产物聚合→entries）
    stages_ok, reasons = True, []
    for name in _RUN_STAGES:
        p = run_dir / name
        if not p.is_file():
            stages_ok = False
            reasons.append(f"{name} 缺")
            continue
        try:
            d = _json.loads(p.read_text(encoding="utf-8"))
            if d.get("verdict") not in ("pass", "awaiting-ruling"):
                stages_ok = False
                reasons.append(f"{name} verdict={d.get('verdict')}")
        except Exception as e:  # noqa: BLE001
            stages_ok = False
            reasons.append(f"{name} unparsable: {e}")
    verdict = "pass" if stages_ok else "fail"
    entry = {
        "family_id": "collection",
        "verdict": verdict,
        "rationale": ("自动采集（T+10min 窗·notice-214 款一③）——七段产物聚合"
                      f"{'全 pass' if stages_ok else '缺/红：' + '；'.join(reasons[:3])}"),
        "evidence_ref": "manifest.json#/run_state + 七段 verdict 面",
    }
    doc = {
        "score_version": "2.0.0-ns6-auto",
        "run_id": trig.get("loop_run_id", ""),
        "entries": [entry],
        "check_time": now.isoformat(),
        "collector": "duty_collection_auto（T+10min 窗自动采集形·A2-3 修法面）",
    }
    out_path.write_text(_json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    out["action"] = "collected"
    out["verdict"] = verdict
    return 0, out


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="duty_collection 自动采集生成器（T+10min 窗）")
    p.add_argument("--run-dir", required=True)
    a = p.parse_args(argv)
    code, out = run(Path(a.run_dir).resolve())
    print(_json.dumps(out, ensure_ascii=False))
    return code


if __name__ == "__main__":
    import sys
    sys.exit(main())
