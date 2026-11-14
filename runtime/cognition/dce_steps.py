"""FADE-001 阶段 4: DCE 确定执行段序编排骨架（fsd-ten-stage-tech-collab §三阶段 4 行·G1 框架过审形）。

业务面切片第四段——迁移本体确定性执行。**骨架边界（今晚树零生产触铁律）**：
本模块=段序编排逻辑面（步骤表+rc_guard+每步读数落卷）——**生产面命令只在
--dry-run（默认）下渲染打印不执行**；--execute 为部署树生产 wiring 保留位
（payload vB→十阶段形 PATCH=周日首拍前置授权窗·本树零调用）。

段序（CPO 件 §二阶段 4 行预演形判读）：pull→迁移器→commit→push 分段落卷。
  pull     — TMV 工作区 fast-forward 对齐（rc_guard）
  migrate  — 迁移器 CLI 真身（weekly_plane_shift·参数面=其 argparse 实锚 L348-352
             --from/--to/--start-date/--operating-root/--sync——**生产形精化勘正
             （部署树窗 2026-11-13）**：G3 骨架形 `--plan-file` 系参数面错位
             （weekly_plane_shift argparse 不识该参数·--execute 必 SystemExit(2)
             拦停段·G4 集成案走 dry-run 渲染面故未暴露）——本形照 argparse 实锚
             修正·--plan-file 保留为 CLI 交棒锚记录位（值随 dce.json 落卷）
             ——**发现 7 锚位勘正（2026-11-14·CTO 裁 A）**：cmd 加 `cd {tc_root}`
             前缀自锚（python -m 解析面 sys.path[0]=cwd 需 TC 仓根——cd tmv_root
             必 ModuleNotFoundError 活体实证+payload 现役链双证·主卷原「cd
             {tmv_root}」系锚位笔误·锚位随操作对象走=各锚各的真源）
  commit   — 迁移产物暂存+提交（**生产形精化**：add 精确 pathspec
             docs/workflow/operating-records 禁 -A 全仓面——W47 残留/仓内未跟踪
             件零卷入（SDE 实采实锚 13:35:07Z）+zero-diff 防线（vB 原形）+commit
             消息=vB 识别式原形 `ops: weekly plane shift W<X>->W<Y> run=$RUN_ID`
             （SDE §二回滚识别式锚·grep RUN_ID 精确识别））
  push     — sg-bare 通道推（**生产形精化**：vB 原形通道面 sg-bare HEAD:dev+
             断通道 fetch/merge 重试面——非骨架形 origin dev（河源 TMV remote
             真值=sg-bare·V4 产物三面读数锚面）·rc_guard=False 断通道降级如实注）

每步产物=dce.json steps[]（step/rc/readings）挂 run id（段产物文件族外延·
dce.json=段 4 产物落卷位——PM §二文件族表未列段 4 产物·本名候 CTO 对表注记）。

退出码（同族）：0=全步绿（dry-run 下=渲染面绿非执行面绿·如实标注）；
  2=某步 rc_guard 拦（停段·dce.json 带 failed_step）——verdict 读数路由面
  （发现 21/22·2026-11-14）：fail=修复链 / halt_pending_ruling=rc=3 候裁态
  （路由 COS 裁决链·停段行为与 exit 码两态一致）。
"""

from __future__ import annotations

import argparse
import sys
import json as _json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DCE_VERSION = "1.0.0"

# 发现 7（CTO 裁 A 2026-11-14·派工八项之 6）：migrate 锚位换真源自锚——migrate
# 操作对象=TriCompany 仓迁移器模块·锚 tc_root（pull/commit/push 操作 TMV 工作区
# 故锚 tmv_root·各锚各的真源）。python -m 解析面 sys.path[0]=cwd 需 TC 仓根
# （cd tmv_root 必 ModuleNotFoundError——活体实证+payload 现役链双证·主卷原
# 「cd {tmv_root}」系锚位笔误）。零新参自锚：部署位 parents[2]=TC 仓根（dev
# D:/Code/ai/TriCompany 与河源 /srv/fleet/TriCompany 两机同形）。
TC_ROOT = str(Path(__file__).resolve().parents[2])

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
        # 参数面=weekly_plane_shift argparse 实锚（L348-352·部署树窗生产形精化勘正）
        "cmd_tmpl": (
            "cd {tc_root} && "
            "python3 -m runtime.cognition.weekly_plane_shift "
            "--from {from_week} --to {to_week} --start-date {start_date} "
            "--operating-root {operating_root} --sync"
        ),
        "rc_guard": True,
        "note": "迁移器 CLI 真身（argparse 实锚参数面·--sync 迁移面·部署树窗精化形·cd tc_root 自锚=发现 7 裁 A）",
    },
    {
        "step": "commit",
        "cmd_tmpl": (
            "git -C {tmv_root} add docs/workflow/operating-records && "
            "(git -C {tmv_root} diff --cached --quiet || "
            "git -C {tmv_root} -c user.name=TriRMC-Scheduler -c user.email=trirmc@tri.company "
            "commit -m 'ops: weekly plane shift {from_week}->{to_week} run={run_id}')"
        ),
        "rc_guard": True,
        "note": "迁移产物落卷（精确 pathspec 禁 -A·zero-diff 防线+vB 识别式消息形·部署树窗精化形）",
    },
    {
        "step": "push",
        "cmd_tmpl": (
            "git -C {tmv_root} push sg-bare HEAD:dev || "
            "(git -C {tmv_root} fetch sg-bare dev && "
            "git -C {tmv_root} merge --no-edit FETCH_HEAD && "
            "git -C {tmv_root} push sg-bare HEAD:dev)"
        ),
        "rc_guard": False,
        "note": "sg-bare 通道推+vB 原形断通道 fetch/merge 重试面（降级如实注·部署树窗精化形）",
    },
]


def render_steps(
    tmv_root: str,
    plan_file: str,
    run_id: str,
    from_week: str = "",
    to_week: str = "",
    start_date: str = "",
    operating_root: str = "",
) -> list[dict]:
    """步骤表渲染（模板→命令串·零执行——dry-run 面）。"""
    ctx = {
        "tc_root": TC_ROOT,  # 发现 7 裁 A：migrate 前缀自锚（零新参）
        "tmv_root": tmv_root,
        "plan_file": plan_file,
        "run_id": run_id,
        "from_week": from_week,
        "to_week": to_week,
        "start_date": start_date,
        "operating_root": operating_root,
    }
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
    steps = render_steps(
        args.tmv_root,
        args.plan_file,
        args.run_id,
        from_week=getattr(args, "from_week", ""),
        to_week=getattr(args, "to_week", ""),
        start_date=getattr(args, "start_date", ""),
        operating_root=getattr(args, "operating_root", ""),
    )
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
            # 发现 21/22（CTO 裁 2026-11-14·派工八项之 3）：rc=3=候裁态特判——
            # verdict 记 halt_pending_ruling（读数定性保真：「失败」路由修复链·
            # 「候裁」路由 COS 裁决链·合并=处置路由丢失）。停段行为不变
            # （后续步骤零执行·零豁免零 escape·门不豁免哲学不破）·rc=4 维持
            # 布尔拦不特判（特判稀释读数）。
            if entry.get("rc") == 3:
                entry["halt_class"] = "pending_ruling"
                entry["halt_note"] = (
                    "rc=3 候裁态（weekly_plane_shift 裁决护栏位）——"
                    "verdict=halt_pending_ruling·路由 COS 裁决链非修复链"
                )
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
        if any(r.get("halt_class") == "pending_ruling" for r in step_results):
            dce["verdict"] = "halt_pending_ruling"  # 发现 21/22：候裁态读数路由
        else:
            dce["verdict"] = "fail"
        dce["failed_step"] = failed_step
    else:
        dce["verdict"] = "pass"
    return exit_code, dce


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 4 DCE 段序编排（骨架·dry-run 面）")
    p.add_argument("--tmv-root", required=True, help="TriMetaverse 工作区根")
    p.add_argument("--plan-file", required=True, help="阶段 3 plan.json 交棒锚（记录位·migrate 不再直传）")
    p.add_argument(
        "--from-week", default="", help="迁移周锚 from（weekly_plane_shift --from 透传·生产形必填）"
    )
    p.add_argument("--to-week", default="", help="迁移周锚 to（weekly_plane_shift --to 透传）")
    p.add_argument(
        "--start-date", default="", help="新周起始日（weekly_plane_shift --start-date 透传）"
    )
    p.add_argument(
        "--operating-root", default="",
        help="operating-records 根（weekly_plane_shift --operating-root 透传）",
    )
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
