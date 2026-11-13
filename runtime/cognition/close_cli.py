"""FADE-001 阶段 9: close cli run 终态落卷段骨架（fsd-ten-stage-tech-collab §三路线框架）。

业务面切片第九段——判「每个 run 有终点」。run 终态三态字段落 manifest.json
（manifest 既有形推广·CPO 件②段产物命名族）：
  ok     — 六段产物全在且 verdict 全 pass
  failed — 六段产物全在但存在 fail 段（死有名字=哪段死·reasons 在各段卷内）
  stale  — 段产物缺件（run 未走完即断=悬空 run 面·生产形零容忍断言连跑 4 周读数候窗）

manifest 层=终点记录非闸：不拦链不告警（告警面在前段+段 10 结论动作）——
如实汇总落卷即本职。CLI 命名族候 G2 对表（本件名 close_cli.py 候定谳·与 close_skill 分立）。

退出码：0=manifest 落卷成功（任何 run_state 都是合法落卷）；2=落卷败（哑卷防线）。
"""

from __future__ import annotations

import argparse
import json as _json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_VERSION = "1.0.0"
# 六段产物序（阶段 1-8 产物面·arrival/cron 面不入此对表域）
_STAGE_ORDER = (
    "preflight.json", "qualify.json", "plan.json", "verify.json",
    "score.json", "close.json",
)


def summarize_stages(run_dir: Path) -> dict:
    """六段产物 verdict 汇总——返回 {stage_name: verdict_or_absent}。"""
    stages: dict[str, str] = {}
    for name in _STAGE_ORDER:
        p = run_dir / name
        if not p.is_file():
            stages[name] = "absent"
            continue
        try:
            data = _json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 不可读如实记（终点记录不抛不拦）
            stages[name] = "unreadable"
            continue
        stages[name] = str(data.get("verdict", "unknown")) if isinstance(data, dict) else "unknown"
    return stages


def derive_run_state(stages: dict[str, str]) -> str:
    """三态判：缺件/不可读=stale·有 fail=failed·全 pass=ok。"""
    values = set(stages.values())
    if "absent" in values or "unreadable" in values:
        return "stale"
    if "fail" in values:
        return "failed"
    return "ok"


def run_manifest(args: argparse.Namespace) -> tuple[int, dict]:
    """落 run 终态 manifest 并返回 (exit_code, manifest dict)。"""
    stages = summarize_stages(Path(args.run_dir))
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "stages": stages,
        "run_state": derive_run_state(stages),
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    return 0, manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 9 run 终态落卷（close cli·骨架形）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", default="")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, manifest = run_manifest(args)
    out = _json.dumps(manifest, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"manifest.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
