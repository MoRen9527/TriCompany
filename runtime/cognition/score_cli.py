"""FADE-001 阶段 6: score cli 跑分段骨架（fsd-ten-stage-tech-collab §三路线框架·CTO 裁②精化一）。

业务面切片第六段——判「跑完有没有分」。**路径分立（CTO 精化一·9c-d6e636d 留痕）**：
  executed_ok      — score_engine 实跑成功 → exit 0·score.json 载读数
  executed_failed  — 引擎在·实跑抛异常/返回非零 → exit 2·非阻塞告警面（COS 单址）
  engine_absent    — score_engine 模块不存在 → exit 2·**J7 升级面仅限此路径**
                     （部署面缺件≠引擎坏了——升级路由判据面分立防误升）

骨架形边界（预演形·COS 裁决 B）：score_engine 实弹候 J5-J7 灰度前提对表
（现役评分形制=件⑥改卷制候窗）——本段骨架只立「三态路径分立+score.json 落卷」；
首拍默认态=engine_absent（engine 未部署）→ 升级面告警路由字段如实落卷。

退出码（preflight/qualify/plan_scope/verify 同族）：0 executed_ok → 交棒 close 段；
  2 = engine_absent/executed_failed/落卷败 → 告警面（级别看 engine_state 分立）。

输出：score.json 到 $RUN_DIR：
  score_version / run_id / engine_state / verdict / reasons / check_time
"""

from __future__ import annotations

import argparse
import json as _json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

SCORE_VERSION = "1.0.0"


def probe_score_engine() -> tuple[object | None, str]:
    """score_engine 探测——返回 (module|None, state)。缺席≠跑败（路径分立·精化一）。"""
    try:
        return import_module("runtime.cognition.score_engine"), "present"
    except ImportError:
        return None, "engine_absent"
    except Exception as e:  # noqa: BLE001 — import 期非缺席异常=装了坏了（非缺席路径）
        print(f"score_engine import error: {type(e).__name__}: {e}", flush=True)
        return None, "engine_broken_import"


def run_score(args: argparse.Namespace) -> tuple[int, dict]:
    """执行跑分并返回 (exit_code, score dict)。"""
    engine, import_state = probe_score_engine()
    reasons: list[str] = []
    score_payload: dict | None = None

    if import_state == "engine_absent":
        reasons.append("score_engine module absent（J7 升级面路径·部署面缺件）")
        engine_state = "engine_absent"
    elif import_state == "engine_broken_import":
        reasons.append("score_engine import failed（装了坏了·非缺席路径）")
        engine_state = "executed_failed"
    else:
        try:
            score_payload = engine.run_score(  # type: ignore[union-attr]
                run_id=args.run_id,
                run_dir=args.run_dir,
                from_week=args.from_week,
                to_week=args.to_week,
            )
            engine_state = "executed_ok"
            if not isinstance(score_payload, dict):
                reasons.append("score_engine returned non-dict（引擎契约面违规）")
                engine_state = "executed_failed"
        except Exception as e:  # noqa: BLE001 — 实跑败=非缺席路径（精化一分立面）
            reasons.append(f"score_engine run failed: {type(e).__name__}: {e}（非阻塞告警面·COS 单址）")
            engine_state = "executed_failed"

    score: dict = {
        "score_version": SCORE_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "engine_state": engine_state,
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    if score_payload is not None and engine_state == "executed_ok":
        score["score"] = score_payload
    if reasons:
        score["verdict"] = "fail"
        score["reasons"] = reasons
        exit_code = 2
    else:
        score["verdict"] = "pass"
        exit_code = 0
    return exit_code, score


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 6 跑分（score cli·骨架形）")
    p.add_argument("--run-dir", required=True, help="run 目录（score.json 落卷位）")
    p.add_argument("--run-id", default="")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, score = run_score(args)
    out = _json.dumps(score, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "score.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"score.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
