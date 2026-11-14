"""FADE-001 阶段 8: close skill 复盘收口段骨架（fsd-ten-stage-tech-collab §三路线框架·CTO 裁②精化二）。

业务面切片第八段——判「复盘在收口时自动发生」。**漏报护栏（CTO 精化二·c5d6e636d 留痕）**：
  close.json **必载 upgrade_list_state 键**——显式二值禁静默缺省：
    "extracted"     — 升级提取流程实跑过（含空清单=合法态·零升级条目如实落）
    "not_extracted" — 骨架未提取（现役形）——**键必须显式落·禁静默缺省**
  缺键=结构门拦（替身禁令同族：静默缺省=最毒漏报形——收口面看着干净实则没跑）。

  COS 单址告警面：notify_target="COS" 显式落卷（升级条目非空时的告警路由载体——
  真实 notify 候 P1 SMTP 形接入·骨架只落路由字段）。

升级提取骨架逻辑（现役形=extracted 路径·轻量）：
  扫 run dir 段产物（preflight/qualify/plan/dce/verify/score 六件 JSON·发现 12
  扩 dce.json 段 4 产物——CTO 派工 2026-11-14）→
  verdict=fail 段提取升级条目 {stage, reasons} → score 段 engine_state=engine_absent
  → 升级级=J7 升级面（路径分立对表·精化一）。

退出码（同族）：0 close 卷落卷（含 not_extracted 显式态）；
  2 = 结构门毒化/段产物不可读（非缺件——缺件如实注记不拦）/落卷败。
"""

from __future__ import annotations

import argparse
import sys
import json as _json
from datetime import datetime, timezone
from pathlib import Path

CLOSE_VERSION = "1.0.0"
_STAGE_ARTIFACTS = (
    "preflight.json", "qualify.json", "plan.json", "dce.json",
    "verify.json", "score.json",
)
_UPGRADE_STATES = ("extracted", "not_extracted")


def scan_stage_artifacts(
    run_dir: Path, run_id: str = ""
) -> tuple[list[dict], list[str]]:
    """段产物扫描——返回 (fail_stages, notes)。缺件=如实 note 不拦（骨架容忍·禁造替身读数）。

    升级条目五字段 spec（PM §二·CPO 主稿 §六点名·D-39 分级承载面）：
      run_id / stage+trigger（触发源枚举）/ routing（候 COS|候 CEO 二值）/
      evidence（run id+段产物路径·禁零锚升级条目）/ state（open|routed 默认 open）。
    防蠕变划线：清单=提取与承载不做裁决（裁=COS 域）——routing=保守默认候 COS+
    判据注记·零裁决语义字段进 schema（禁自动降级/自动销项）。
    """
    fail_stages: list[dict] = []
    notes: list[str] = []
    for name in _STAGE_ARTIFACTS:
        p = run_dir / name
        if not p.is_file():
            notes.append(f"{name} absent（段产物缺件·如实注记）")
            continue
        try:
            data = _json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — 不可读=毒化族（升级面不可盲判）
            fail_stages.append(_mk_upgrade_entry(
                run_id, name, "artifact_unreadable", str(p),
                [f"unreadable: {type(e).__name__}: {e}（升级面不可读条目）"],
            ))
            continue
        if not isinstance(data, dict):
            continue
        if data.get("verdict") == "fail":
            reasons = data.get("reasons", [])
            trigger = "stage_artifact_fail"
            if name == "score.json" and data.get("engine_state") == "engine_absent":
                reasons = [f"J7 upgrade path: {r}" for r in reasons]
                trigger = "J7_score_engine_absent"
            fail_stages.append(_mk_upgrade_entry(run_id, name, trigger, str(p), reasons))
    return fail_stages, notes


def _mk_upgrade_entry(
    run_id: str, stage: str, trigger: str, evidence: str, reasons: list
) -> dict:
    """升级条目构造（五字段 spec·骨架提取面可及域：J7 缺席/段产物 fail/unreadable；
    J5 首拍 fallback 与告警面聚合=生产形候项·如实不在骨架枚举）。"""
    return {
        "run_id": run_id,
        "stage": stage,
        "trigger": trigger,
        "routing": "候 COS",  # D-39 对表承载：终裁归 COS 分诊（三类判据=候 CEO 面·骨架不做裁决）
        "evidence": evidence,  # run id 同卷+段产物路径指针（禁零锚升级条目）
        "state": "open",  # 流转 COS 后置 routed（骨架默认 open）
        "reasons": reasons,
    }


def _structure_gate(close: dict) -> list[str]:
    """结构门：upgrade_list_state 显式二值+必载键族（精化二漏报护栏的机械面）。"""
    errors: list[str] = []
    for key in ("close_version", "run_id", "upgrade_list_state", "upgrade_list",
                "run_state", "notify_target", "verdict", "check_time"):
        if key not in close:
            errors.append(f"missing required key: {key}")
    state = close.get("upgrade_list_state")
    if state not in _UPGRADE_STATES:
        errors.append(
            f"upgrade_list_state={state!r} 非显式二值（禁静默缺省·精化二护栏拦）"
        )
    if close.get("notify_target") != "COS":
        errors.append("notify_target!=COS（单址告警面字段违规）")
    return errors


def run_close(args: argparse.Namespace) -> tuple[int, dict]:
    """执行复盘收口并返回 (exit_code, close dict)。"""
    run_dir = Path(args.run_dir)
    fail_stages, notes = scan_stage_artifacts(run_dir, run_id=args.run_id)
    # run 终态字段（PM §二契约：close.json=升级清单提取+run 终态字段同卷）——
    # 复用 close_cli 汇总/三态判（零重复·两件同源一致）
    from runtime.cognition.close_cli import derive_run_state, summarize_stages

    stages = summarize_stages(run_dir)
    close: dict = {
        "close_version": CLOSE_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "upgrade_list_state": "extracted",
        "upgrade_list": fail_stages,
        "stage_artifact_notes": notes,
        "run_state": derive_run_state(stages),
        "notify_target": "COS",
        "verdict": "pass",  # 门前置占位（门拦则翻 fail——防自造缺键拦）
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    gate_errors = _structure_gate(close)
    if gate_errors:
        close["verdict"] = "fail"
        close["reasons"] = gate_errors
        exit_code = 2
    else:
        close["verdict"] = "pass"
        exit_code = 0
    return exit_code, close


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 8 复盘收口（close skill·骨架形）")
    p.add_argument("--run-dir", required=True, help="run 目录（close.json 落卷位+段产物扫描域）")
    p.add_argument("--run-id", default="")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, close = run_close(args)
    out = _json.dumps(close, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "close.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"close.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # 非 UTF-8 宿主输出面兜底（GBK 炸 ⊂ 实锚）
    except Exception:  # noqa: BLE001 — 老宿主无 reconfigure 时维持默认
        pass
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
