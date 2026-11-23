"""chain_runner — 十段链参数化执行器（notice-223 款二·S2 件·§六A 段级重跑承载）。

段序程序化（§四·198 四要点同族）：段 N+1 前置断言＝段 N 落卷真值（硬串行禁
跳段）＋装配=程序面 agent 只判读＋产出回管道落卷。

段序（十段·notice-207 件①硬序承录面）：
  1 preflight → 2 qualify → 3 plan → 4 dce → 5 verify → 6 score_cli
  → 7 score_skill_spawn（硬序段·score_cli 后 close_skill 前）
  → 8 score_rubric → 9 close_skill → 10 close_cli
  （联审尾段=joint_review_trigger best-effort 非链内·§三 队列归位承）

--resume-stage N（§六A 段级重跑承载）：段 N 起（前置真值断言复用·同 run_dir
断点续段非全链重跑——重跑指令=点火指令族·断点参数携带）。

每段=独立 CLI 子进程（段隔离·段报错停 fail-closed 款三——rc≠0=停链冒泡）。
退出码：0 全过／2 段 fail（停链·failed_stage 面）／3 前置断言红（跳段拒）。
"""
from __future__ import annotations

import argparse
import json as _json
import os
import subprocess
import sys
import time
from pathlib import Path

TC_ROOT = Path(__file__).resolve().parents[2]

# 段序表（§四·硬串行禁跳段）：段名 → (模块 argv 模板, 产物卷, 前置断言键)
STAGES = [
    ("preflight", "preflight.json"),
    ("qualify", "qualify.json"),
    ("plan", "plan.json"),
    ("dce", "dce.json"),
    ("verify", "verify.json"),
    ("score_cli", "score.json"),
    ("score_skill_spawn", "score-skill.json"),
    ("score_rubric", "rubric_report.json"),
    ("close_skill", "close.json"),
    ("close_cli", "manifest.json"),
]


def _stage_argv(name: str, run_dir: Path, run_id: str,
                from_week: str, to_week: str, start_date: str) -> list[str]:
    """段 CLI argv 面（参数化形·每段独立子进程）。"""
    rd, rid = str(run_dir), run_id
    common = ["--run-dir", rd, "--run-id", rid]
    if name == "preflight":
        return [sys.executable, "-m", "runtime.cognition.preflight",
                "--from", from_week, "--to", to_week, "--start-date", start_date,
                "--repo", str(TC_ROOT), "--prev-runs-root",
                os.environ.get("TRICO_PREV_RUNS_ROOT",
                               "/srv/fleet/TriRMC/fade001-runs"),
                "--no-diverge", "--skip-hostname", "--loop-window"]
    if name == "qualify":
        return [sys.executable, "-m", "runtime.cognition.qualify"] + common
    if name == "plan":
        return [sys.executable, "-m", "runtime.cognition.plan_scope"] + common + [
            "--from-week", from_week, "--to-week", to_week,
            "--start-date", start_date,
            "--operating-root",
            "/srv/fleet/TriMetaverse/docs/workflow/operating-records"]
    if name == "dce":
        return [sys.executable, "-m", "runtime.cognition.dce_steps",
                "--tmv-root", "/srv/fleet/TriMetaverse",
                "--plan-file", f"{rd}/plan.json"] + common + [
            "--from-week", from_week, "--to-week", to_week,
            "--start-date", start_date,
            "--operating-root",
            "/srv/fleet/TriMetaverse/docs/workflow/operating-records",
            "--execute"]
    if name == "verify":
        return [sys.executable, "-m", "runtime.cognition.verify",
                "--plan-file", f"{rd}/plan.json"] + common + [
            "--from-week", from_week, "--to-week", to_week,
            "--start-date", start_date,
            "--operating-root",
            "/srv/fleet/TriMetaverse/docs/workflow/operating-records",
            "--strict"]
    if name == "score_cli":
        return [sys.executable, "-m", "runtime.cognition.score_cli"] + common + [
            "--from-week", from_week, "--to-week", to_week]
    if name == "score_skill_spawn":
        return [sys.executable, "-m", "runtime.cognition.score_skill_spawn"] + common
    if name == "score_rubric":
        return [sys.executable, "-m", "runtime.cognition.score_rubric",
                "--rubric-file", str(TC_ROOT / "runtime/cognition/rubric-firstshoot.json"),
                "--out", f"{rd}/rubric_report.json"] + common
    if name == "close_skill":
        return [sys.executable, "-m", "runtime.cognition.close_skill"] + common + [
            "--from-week", from_week, "--to-week", to_week]
    if name == "close_cli":
        return [sys.executable, "-m", "runtime.cognition.close_cli"] + common + [
            "--from-week", from_week, "--to-week", to_week]
    raise ValueError(f"未知段: {name}")


def _stage_artifact_ok(run_dir: Path, artifact: str) -> tuple[bool, str]:
    """段 N 落卷真值断言（前置断言复用面·§四）：产物在+可解析+verdict 面。"""
    p = run_dir / artifact
    if not p.is_file():
        return False, f"{artifact} 缺（前置真值断言红·跳段拒）"
    try:
        d = _json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return False, f"{artifact} unparsable: {e}"
    verdict = d.get("verdict")
    if verdict not in ("pass", "awaiting-ruling"):
        return False, f"{artifact} verdict={verdict!r}（前置真值红）"
    return True, f"{artifact} verdict={verdict}"


def run(args: argparse.Namespace) -> tuple[int, dict]:
    run_dir = Path(args.run_dir).resolve()
    stages = STAGES
    start = 0
    if args.resume_stage is not None:
        # §六A 段级重跑承载：段 N 起（前置真值断言复用——段 N-1 产物面先验）
        start = args.resume_stage
        if start < 1 or start > len(stages):
            return 3, {"resume_error": f"resume-stage={start} 越段序（1-{len(stages)}）"}
        if start > 1:
            prev_name, prev_art = stages[start - 2]
            ok, note = _stage_artifact_ok(run_dir, prev_art)
            if not ok:
                return 3, {"resume_error": f"段 {start} 前置断言红（{prev_name}）: {note}"}
        stages = stages[start - 1:]
    report: dict = {"chain_runner_version": "1.0.0", "run_id": args.run_id,
                    "run_dir": str(run_dir), "resume_stage": args.resume_stage,
                    "steps": [], "failed_stage": None}
    for name, artifact in stages:
        argv = _stage_argv(name, run_dir, args.run_id,
                           args.from_week, args.to_week, args.start_date)
        print(f"[chain] {name} …", flush=True)
        try:
            r = subprocess.run(argv, capture_output=True, text=True,
                               timeout=args.stage_timeout, cwd=str(TC_ROOT))
            rc, tail = r.returncode, (r.stderr or "")[-300:]
        except subprocess.TimeoutExpired:
            rc, tail = -1, f"stage timeout {args.stage_timeout}s"
        report["steps"].append({"stage": name, "rc": rc, "tail": tail})
        if rc != 0:
            report["failed_stage"] = name
            report["verdict"] = "fail"
            print(f"[chain] {name} rc={rc} 停链（fail-closed 款三）", flush=True)
            return 2, report
        ok, note = _stage_artifact_ok(run_dir, artifact)
        if not ok:
            report["failed_stage"] = name
            report["verdict"] = "fail"
            print(f"[chain] {name} 产物断言红: {note}", flush=True)
            return 2, report
    report["verdict"] = "pass"
    return 0, report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="chain_runner — 十段链参数化执行器（S2）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--from-week", default="W47")
    p.add_argument("--to-week", default="W48")
    p.add_argument("--start-date", default="2026-11-23")
    p.add_argument("--resume-stage", type=int, default=None,
                   help="§六A 段级重跑：段 N 起（前置真值断言复用·同 run_dir 断点续段）")
    p.add_argument("--stage-timeout", type=int, default=1800)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code, report = run(args)
    print(_json.dumps(report, ensure_ascii=False, indent=1)[:4000])
    return code


if __name__ == "__main__":
    sys.exit(main())
