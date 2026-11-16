"""loop 联审召集面（V2-1·trigger convene_mode 字段扩展+召集件模板化+dimB 初判器）。

三件合一（COO 工单 §六 v2 表·FSD 车道）：
  ① convene_mode 字段扩展——触发面 convene_mode 读形（manual 缺省 fail-safe：
     新旧互兼容零行为漂移·CTO §二兜底采认；auto=召集自动化臂·由触发链显式
     置 loop-convene.json 声明）
  ② 召集件模板化——七席召集件模板渲染（α 轻形：单卷通用+席角 checklist 引用；
     产出=信箱 dispatch payload 形，控制面拾取发送·本骨架零直接投递）
  ③ dimB 初判器——dimB（collection 形）机判初判卷生成器：自 run_dir score.json
     机判可验族自动出初判草卷（judge=机判初判·候值席确认转正），值席采集域
     （A/F/H）不在初判器域（值席采集窗面·职责分层）

隔离纪律（CTO 机理定谳）：本面只读 run 段产物、只写召集件到 staging 面——
零 marker touch、零 run POST、零 schedule 触（触发链现役通道零触）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

CONVENE_MODE_DEFAULT = "manual"  # fail-safe 缺省（新旧互兼容零行为漂移·CTO §二）
VALID_MODES = ("manual", "auto")
SEATS = ("COS", "COO", "CAO", "CPO", "CTO", "CHO", "CFO")

# 席角 checklist 引用（STE α 轻形·视角指引层非独立计分——文案引用锚）
SEAT_CHECKLIST_REFS = {
    "CPO": "产品/划界语义：锚文判读+keep 活产品面+carry_over 三标注",
    "CTO": "技术/降级链完备：迁移批次技术风险+trap/RC_guard 闭合+降级链终态",
    "CAO": "治理/留痕可审计：rationale 可追溯+判卷纪律+改窗制度面",
    "COO": "经营/节奏取舍：23:50 硬时钟+窗口冲突如实列+止损分支",
    "COS": "汇总/终判全览：分歧面收敛+终判 rationale+分差触发复核",
}


def read_convene_mode(trigger_dir: Path) -> tuple[str, str | None]:
    """①convene_mode 字段扩展读形：trigger 面 loop-convene.json convene_mode 读。

    缺文件/缺键/非法值 → (CONVENE_MODE_DEFAULT, None)（fail-safe manual·零行为
    漂移）；合法 auto → ("auto", None)。返回 (mode, warn)。
    """
    path = Path(trigger_dir) / "loop-convene.json"
    if not path.is_file():
        return CONVENE_MODE_DEFAULT, None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as err:
        return CONVENE_MODE_DEFAULT, "loop-convene.json unreadable: {}".format(err)
    mode = doc.get("convene_mode")
    if mode not in VALID_MODES:
        return CONVENE_MODE_DEFAULT, "convene_mode invalid: {!r} → fail-safe manual".format(mode)
    return mode, None


def build_convene_letters(run_id: str, round_no: int, verdict: str,
                          scores_summary: Optional[Dict[str, Any]] = None,
                          seats: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """②召集件模板化：七席召集件模板渲染（信箱 dispatch payload 形）。

    模板面：title/body 从 run 上下文+verdict+席角 checklist 引用渲染——控制面
    拾取发送（本骨架零直接投递·零 POST）。
    """
    seats = list(seats or SEATS)
    letters: List[Dict[str, Any]] = []
    for seat in seats:
        checklist = SEAT_CHECKLIST_REFS.get(seat, "通用视角：判据对表+rationale 必附")
        letters.append({
            "target_daemon": "trimmc",
            "target_seat": seat,
            "urgent": "normal",
            "title": "[loop-{round}] 联审召集·{run_id}（verdict={verdict}）".format(
                round=round_no, run_id=run_id, verdict=verdict),
            "body": (
                "FADE-001 loop 第 {round} 轮联审召集（V2-1 召集件模板形·α 轻形）。\n"
                "run_id={run_id}\nverdict={verdict}\n分数面摘要={summary}\n"
                "席角判卷关注点：{checklist}\n"
                "判卷纪律：rationale 必附（禁裸分）+evidence_ref 可复核锚。"
            ).format(round=round_no, run_id=run_id, verdict=verdict,
                     summary=json.dumps(scores_summary, ensure_ascii=False),
                     checklist=checklist),
        })
    return letters


def dimb_initial_judge(run_dir: Path, judge_seat: str = "machine-initial") -> Dict[str, Any]:
    """③dimB 初判器：机判可验族初判草卷生成（collection 形·候值席确认转正）。

    判据源=run_dir/score.json checks 面（机判可验族 B/C/D/E/G 逐族 ok/weight/
    detail 实值）——初判 rationale=机判实值引用（非语义判·语义判=值席采集窗/
    联审面）；A/F/H=值席采集域不在初判器域（职责分层）。
    """
    score_path = Path(run_dir) / "score.json"
    if not score_path.is_file():
        return {"verdict": "pending", "note": "score.json absent（初判器域无源）", "entries": []}
    try:
        score = json.loads(score_path.read_text(encoding="utf-8"))
    except Exception as err:
        return {"verdict": "pending", "note": "score.json unreadable: {}".format(err), "entries": []}
    entries: List[Dict[str, Any]] = []
    for chk in score.get("checks", []):
        cid = chk.get("id")
        if not cid:
            continue
        entries.append({
            "family_id": cid,
            "verdict": "pass" if chk.get("ok") else "fail",
            "rationale": "机判初判：ok={} weight={} detail={}".format(
                chk.get("ok"), chk.get("weight"), json.dumps(chk.get("detail", {}), ensure_ascii=False)[:120]),
            "evidence_ref": str(score_path),
        })
    return {
        "score_version": "dimB-initial-1.0",
        "verdict": score.get("verdict", "unknown"),
        "run_id": run_dir.name,
        "judge": judge_seat,
        "entries": entries,
        "note": "初判草卷（候值席确认转正）",
    }


def main(argv=None) -> int:  # pragma: no cover — CLI 面薄壳
    parser = argparse.ArgumentParser(description="loop 联审召集面（V2-1）")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--trigger-dir", default=None, help="触发面目录（loop-convene.json 读形·缺省=run-dir）")
    parser.add_argument("--dry", action="store_true", help="dry 预演：渲染零写")
    args = parser.parse_args(argv)
    rd = Path(args.run_dir)
    mode, warn = read_convene_mode(Path(args.trigger_dir or args.run_dir))
    score_path = rd / "score.json"
    summary = {}
    if score_path.is_file():
        try:
            summary = json.loads(score_path.read_text(encoding="utf-8")).get("summary", {})
        except Exception:
            summary = {}
    letters = build_convene_letters(rd.name, 0, "pending", summary)
    init = dimb_initial_judge(rd)
    out = {"convene_mode": mode, "warn": warn, "letters": letters,
           "dimb_initial": init, "dry": bool(args.dry)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
