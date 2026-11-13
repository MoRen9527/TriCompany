"""FADE-001 阶段 4: DCE 确定执行段序编排骨架（fsd-ten-stage-tech-collab §三阶段 4 行·G1 框架过审形）。

业务面切片第四段——迁移本体确定性执行。**骨架边界（今晚树零生产触铁律）**：
本模块=段序编排逻辑面（步骤表+rc_guard+每步读数落卷）——**生产面命令只在
--dry-run（默认）下渲染打印不执行**；--execute 为部署树生产 wiring 保留位
（payload vB→十阶段形 PATCH=周日首拍前置授权窗·本树零调用）。

段序（CPO 件 §二阶段 4 行预演形判读）：pull→迁移器→commit→push 分段落卷。
  pull     — TMV 工作区 fast-forward 对齐（rc_guard）
  migrate  — 迁移器真身（weekly_plane_shift 十段一体现役·骨架期=调 plan_scope 交棒形——
             生产形候部署树 CTO 对表）
  commit   — 迁移产物暂存+提交（共享 index 纪律·统一 add+commit）
  push     — 双通道推+ls-remote 验真（断通道降级如实注记）

每步产物=dce.json steps[]（step/rc/readings）挂 run id（段产物文件族外延·
dce.json=段 4 产物落卷位——PM §二文件族表未列段 4 产物·本名候 CTO 对表注记）。

退出码（同族）：0=全步绿（dry-run 下=渲染面绿非执行面绿·如实标注）；
  2=某步 rc_guard 拦（停段·dce.json 带 failed_step）。
"""

from __future__ import annotations

import argparse
import sys
import json as _json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DCE_VERSION = "1.0.0"

# 零外溢对表三处（PM §一 段 4 行产品语义必填·aca95877c 零外溢判据原样）——
# 骨架态=判据位+口径声明落卷（生产形=真值对表·候部署树授权窗实走）
OVERFLOW_CHECKS: list[dict] = [
    {
        "check": "week_dir_structure",
        "basis": "W 目录结构与改造前同形（aca95877c 零外溢判据①）",
    },
    {
        "check": "carry_over_semantics",
        "basis": "carry-over 语义与改造前同形（aca95877c 零外溢判据②）",
    },
    {
        "check": "commit_message_shape",
        "basis": "commit 消息形与改造前同形（aca95877c 零外溢判据③）",
    },
]

# 段序步骤表（cmd=模板·str.format 渲染·execute 面候部署树授权窗）
DCE_STEPS: list[dict] = [
    {
        "step": "pull",
        "cmd_tmpl": "git -C {tmv_root} pull --ff-only",
        "rc_guard": True,
        "note": "工作区对齐（并行窗互踩防线：ff-only 拒 diverge）",
    },
    {
        "step": "migrate",
        # 全名消歧（CTO 审面勘正在案）：weekly_plane_shift.py=CLI 入口（main L346/γ 闸）
        # ≠ weekly_plane.py=库函数面（migrate_weekly_plane·对表域实装）——引用带全名
        "cmd_tmpl": "python3 -m runtime.cognition.weekly_plane_shift --plan-file {plan_file}",
        "rc_guard": True,
        "note": "迁移器 CLI 真身交棒形（生产形候部署树 CTO 对表）",
    },
    {
        "step": "commit",
        "cmd_tmpl": "git -C {tmv_root} add -A && git -C {tmv_root} commit -m 'shift {run_id}'",
        "rc_guard": True,
        "note": "迁移产物落卷（统一 add+commit·共享 index 纪律）",
    },
    {
        "step": "push",
        "cmd_tmpl": "git -C {tmv_root} push origin dev",
        "rc_guard": False,
        "note": "双通道推（断通道降级如实注·验真=ls-remote 候部署树 wiring）",
    },
]


def render_steps(tmv_root: str, plan_file: str, run_id: str) -> list[dict]:
    """步骤表渲染（模板→命令串·零执行——dry-run 面）。"""
    ctx = {"tmv_root": tmv_root, "plan_file": plan_file, "run_id": run_id}
    return [
        {
            "step": s["step"],
            "cmd": s["cmd_tmpl"].format(**ctx),
            "rc_guard": s["rc_guard"],
            "note": s["note"],
        }
        for s in DCE_STEPS
    ]


def run_dce(args: argparse.Namespace) -> tuple[int, dict]:
    """执行段序（dry-run=渲染面·execute=真跑·rc_guard 拦停段）。"""
    steps = render_steps(args.tmv_root, args.plan_file, args.run_id)
    step_results: list[dict] = []
    exit_code = 0
    failed_step: str | None = None

    for s in steps:
        entry: dict = {"step": s["step"], "cmd": s["cmd"]}
        if args.dry_run:
            entry.update({"rc": None, "mode": "dry_run"})
            step_results.append(entry)
            continue
        try:
            proc = subprocess.run(
                s["cmd"], shell=True, capture_output=True, text=True, timeout=args.step_timeout
            )
            entry.update({"rc": proc.returncode, "mode": "execute",
                          "stderr_tail": proc.stderr[-500:] if proc.stderr else ""})
        except Exception as e:  # noqa: BLE001 — 执行异常=rc 非 0 同拦
            entry.update({"rc": 1, "mode": "execute",
                          "stderr_tail": f"{type(e).__name__}: {e}"})
        if s["rc_guard"] and entry.get("rc") != 0:
            exit_code = 2
            failed_step = s["step"]
            step_results.append(entry)
            break  # rc_guard 拦=停段（后续步骤零执行）
        step_results.append(entry)

    dce: dict = {
        "dce_version": DCE_VERSION,
        "run_id": args.run_id,
        "mode": "dry_run" if args.dry_run else "execute",
        "steps": step_results,
        "overflow_checks": [
            {**c, "checked": False, "note": "骨架态=口径位声明·生产形真值对表候部署树授权窗"}
            for c in OVERFLOW_CHECKS
        ],
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    if failed_step:
        dce["verdict"] = "fail"
        dce["failed_step"] = failed_step
    else:
        dce["verdict"] = "pass"
    return exit_code, dce


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 4 DCE 段序编排（骨架·dry-run 面）")
    p.add_argument("--tmv-root", required=True, help="TriMetaverse 工作区根")
    p.add_argument("--plan-file", required=True, help="阶段 3 plan.json 交棒")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", default="")
    p.add_argument(
        "--execute", action="store_true",
        help="真跑（部署树生产 wiring 保留位·今晚树零调用=默认 dry-run）",
    )
    p.add_argument("--step-timeout", type=int, default=120)
    # dry_run 与 --execute 互斥：execute 显式时 dry_run=False
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    args.dry_run = not args.execute  # 默认 dry-run（零生产触·execute 显式才真跑）
    exit_code, dce = run_dce(args)
    out = _json.dumps(dce, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "dce.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"dce.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # 非 UTF-8 宿主输出面兜底（GBK 炸 ⊂ 实锚）
    except Exception:  # noqa: BLE001 — 老宿主无 reconfigure 时维持默认
        pass
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
