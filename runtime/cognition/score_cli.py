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


# ── r12 批2 refine（CTO §三 影响面第 5 件·2026-11-23）：score_cli 输入扩读 exam.json ──
# 职责分离（ce26401a9）：段 3 产卷（objective/subjective）→ 本段消费 objective 侧。
# 判据形态受限三式（结构化 assertion 才可机判；自由文本=skipped 候值席，不造假判）：
#   path_exists:<rel-run-dir-path>
#   json_field:<file>::<dotted.path>::<op>:<value>   op ∈ eq|ne|exists|contains
#   regex:<file>::<pattern>
# 权重接法=候 CTO 裁（本段只产读数 exam_objective，不并入 total_score）。
_EXAM_CONSERVATIVE_NOTE = "non-mechanical assertion (candidate: value-seat manual judgment)"


def _load_exam(run_dir: Path) -> dict | None:
    p = run_dir / "exam.json"
    if not p.is_file():
        return None
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 卷坏不阻断跑分
        print(f"exam.json parse failed: {type(e).__name__}: {e}", flush=True)
        return None


def _judge_assertion(assertion: str, run_dir: Path) -> tuple[str, str]:
    """单条断言机判：返回 (pass|fail|skipped, detail)。异常=fail-open skipped。"""
    import re as _re
    a = (assertion or "").strip()
    try:
        if a.startswith("path_exists:"):
            p = run_dir / a.split(":", 1)[1].strip()
            return ("pass", str(p)) if p.exists() else ("fail", f"missing: {p}")
        m = _re.match(r"^(json_field|regex):([^:]+)::(.+)$", a)
        if not m:
            return ("skipped", _EXAM_CONSERVATIVE_NOTE)
        kind, fname, rest = m.group(1), m.group(2).strip(), m.group(3)
        fp = run_dir / fname
        if not fp.is_file():
            return ("fail", f"file missing: {fp}")
        text = fp.read_text(encoding="utf-8", errors="replace")
        if kind == "regex":
            return ("pass", rest) if _re.search(rest, text) else ("fail", f"regex no match: {rest}")
        mm = _re.match(r"^([^:]+)::(eq|ne|exists|contains):(.*)$", rest)
        if not mm:
            return ("skipped", _EXAM_CONSERVATIVE_NOTE)
        path_, op, want = mm.group(1), mm.group(2), mm.group(3)
        try:
            data = _json.loads(text)
        except Exception:
            return ("fail", f"file not json: {fp}")
        cur = data
        for seg in path_.strip(".").split("."):
            if isinstance(cur, dict) and seg in cur:
                cur = cur[seg]
            else:
                return ("fail", f"path absent: {path_}")
        if op == "exists":
            return ("pass", path_)
        if op == "eq":
            return ("pass", str(cur)) if str(cur) == want else ("fail", f"{cur!r} != {want!r}")
        if op == "ne":
            return ("pass", str(cur)) if str(cur) != want else ("fail", f"{cur!r} == {want!r}")
        # contains
        return ("pass", path_) if want in str(cur) else ("fail", f"{want!r} not in {cur!r}")
    except Exception as e:  # noqa: BLE001 — 判据面异常 fail-open
        return ("skipped", f"judge error: {type(e).__name__}: {e}")


def evaluate_exam_objective(exam: dict, run_dir: Path) -> dict:
    """objective 逐条机判→段卷（权重不并总分·候 CTO 裁）。"""
    items_out: list[dict] = []
    for it in (exam.get("objective") or []):
        if not isinstance(it, dict):
            continue
        res, detail = _judge_assertion(str(it.get("assertion") or ""), run_dir)
        items_out.append({"id": it.get("id"), "dimension": it.get("dimension"),
                          "assertion": it.get("assertion"), "result": res, "detail": detail})
    counts = {"pass": 0, "fail": 0, "skipped": 0}
    for r in items_out:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    return {"items": items_out, "counts": counts,
            "note": "readout only; weight integration pending CTO ruling (non-invasive)"}


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
        # r34 manifest 核（CTO 令）：engine 的 artifacts_manifest 提升到 score.json **顶层**（可查面）
        if isinstance(score_payload.get("artifacts_manifest"), dict):
            score["artifacts_manifest"] = score_payload["artifacts_manifest"]
    # r12 批2：exam 扩读（非侵入读数段·exam 缺席=零键；判据面异常不阻断本段）
    try:
        _exam = _load_exam(Path(args.run_dir))
        if _exam is not None:
            score["exam_objective"] = evaluate_exam_objective(_exam, Path(args.run_dir))
    except Exception as e:  # noqa: BLE001
        score["exam_objective"] = {"error": f"{type(e).__name__}: {e}",
                                   "note": "exam readout failed (fail-open, non-blocking)"}
    # c3 双修 A（CEO 批·CTO 施工令 2026-11-24 L168-175）：engine verdict 必须传染顶层——
    # 根因：顶层 verdict 仅由 CLI 级 reasons 判，engine_verdict=fail 时顶层仍 pass（SDE 转述「顶层=CLI 态」不准·实读为准）。
    _engine_fail = (isinstance(score.get("score"), dict)
                    and score["score"].get("verdict") == "fail")
    if reasons or _engine_fail:
        score["verdict"] = "fail"
        if reasons:
            score["reasons"] = reasons
        if _engine_fail:
            score.setdefault("reasons", [])
            if isinstance(score["reasons"], list):
                score["reasons"].append("engine verdict=fail（c3 传染面）")
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
        # CFO2（B4）：score 段 cost-log 行补 stage+不可用原因（本地判分无 LLM 调用）
        try:
            import datetime as _dtc
            with (run_dir / "cost-log.jsonl").open("a", encoding="utf-8") as _fh:
                _fh.write(json.dumps({"stage": "score",
                                      "started": _dtc.datetime.now(_dtc.timezone.utc).isoformat(),
                                      "tokens_in": None, "tokens_out": None,
                                      "unavailable_reason": "local-judgement（engine 本地判分·无 LLM 调用）"},
                                     ensure_ascii=False) + chr(10))
        except Exception:
            pass
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"score.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
