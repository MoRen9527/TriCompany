"""FADE-001 阶段 9: close cli run 终态落卷段骨架（fsd-ten-stage-tech-collab §三路线框架）。

业务面切片第九段——判「每个 run 有终点」。run 终态三态字段落 manifest.json
（manifest 既有形推广·CPO 件②段产物命名族）：
  ok     — 七段产物全在且 verdict 全 pass（发现 12 扩 dce.json 段 4 产物·CTO 派工 2026-11-14）
  failed — 七段产物全在但存在 fail 段（死有名字=哪段死·reasons 在各段卷内）
  stale  — 段产物缺件（run 未走完即断=悬空 run 面·生产形零容忍断言连跑 4 周读数候窗）

manifest 层=终点记录非闸：不拦链不告警（告警面在前段+段 10 结论动作）——
如实汇总落卷即本职。CLI 命名族候 G2 对表（本件名 close_cli.py 候定谳·与 close_skill 分立）。

WP7 收口自洽注记（2026-11-18·拆解任务书获批面）：**manifest=run_state 单值源
本尊**——summarize_stages/derive_run_state 为全链唯一三态判权威；close_skill
侧（1.1.0 起）run_state 改 manifest 引用形（close 不自判 stale——双源双时点
矛盾消除面），本件行为零变（单值源生成侧原样）。

退出码：0=manifest 落卷成功（任何 run_state 都是合法落卷）；2=落卷败（哑卷防线）。
"""

from __future__ import annotations

import argparse
import json as _json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_VERSION = "1.0.0"
# 七段产物序（阶段 1-8 产物面·dce.json=段 4 产物发现 12 扩·arrival/cron 面不入此对表域）
_STAGE_ORDER = (
    "preflight.json", "qualify.json", "plan.json", "dce.json", "verify.json",
    "score.json", "close.json",
)


def summarize_stages(run_dir: Path) -> dict:
    """七段产物 verdict 汇总——返回 {stage_name: verdict_or_absent}。"""
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


def assert_close_contract(run_dir: Path, manifest_time: str) -> dict:
    """notice-208 断言族（件④·2026-11-19·七席 I3 相抵面口径统一）——close
    skill 产物三面机械验（收口末段 close_cli 终位·先 skill 后 CLI 勘正承）。

    ①时点断言：close.check_time ≤ manifest_time（写序产物 vs 定稿态口径分立
      承认——pending_manifest 形=合法序·非拦面）
    ②hash 断言：close.evidence[].hash 全 sha256_16 算法形（裸 hash 拒钉维持
      ·r1 缺陷③防复发核）
    ③run_state 口径断言：run_state_source ∈ {manifest, pending}（单值源强制
      ·polluted/malformed=毒化面如实）；manifest_late 枚举形候 CAO 值面随批。
    close.json 缺=skip 注（向后兼容·旧拍零波及）。never raises（断言面零阻
    manifest 落卷——断言读数入 manifest.close_contract 审计行）。
    """
    reading: dict = {"checks": [], "ok": True}
    close_path = run_dir / "close.json"
    if not close_path.is_file():
        reading["checks"].append({"check": "close_presence",
                                  "ok": True,
                                  "note": "close.json 缺（skip 注·旧拍兼容）"})
        return reading
    try:
        close = _json.loads(close_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        reading["ok"] = False
        reading["checks"].append({"check": "close_parse", "ok": False,
                                  "note": f"close.json unparsable: {e}"})
        return reading
    # ①时点断言（写序 vs 定稿态口径分立承认）
    ct = str(close.get("check_time", ""))
    ok_time = bool(ct) and (ct <= manifest_time)
    reading["checks"].append({"check": "time_order", "ok": ok_time,
                              "close_check_time": ct,
                              "manifest_check_time": manifest_time,
                              "note": "写序产物 vs 定稿态口径分立承认（pending_manifest 形=合法序）"})
    # ②hash 断言（sha256_16 算法形全载·裸 hash 拒钉）
    ev = close.get("evidence")
    if isinstance(ev, list) and ev:
        bad = [e.get("stage_artifact") for e in ev if isinstance(e, dict)
               and not str(e.get("hash", "")).startswith("sha256_16:")]
        ok_hash = not bad
        reading["checks"].append({"check": "evidence_hash_algo", "ok": ok_hash,
                                  "naked_hash_items": bad,
                                  "note": "sha256_16 算法形全载（裸 hash 拒钉维持·r1 缺陷③防复发核）"})
    # ③run_state 口径断言（单值源 source 强制）
    source = close.get("run_state_source")
    ok_source = source in ("manifest", "pending")
    reading["checks"].append({"check": "run_state_source", "ok": ok_source,
                              "run_state_source": source,
                              "manifest_late_enum": "候 CAO 值面随批（候勘接入位）"})
    reading["ok"] = all(c["ok"] for c in reading["checks"])
    return reading


def run_manifest(args: argparse.Namespace) -> tuple[int, dict]:
    """落 run 终态 manifest 并返回 (exit_code, manifest dict)。"""
    stages = summarize_stages(Path(args.run_dir))
    now_iso = datetime.now(timezone.utc).isoformat()
    close_contract = assert_close_contract(Path(args.run_dir), now_iso)
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "stages": stages,
        "run_state": derive_run_state(stages),
        "close_contract": close_contract,  # notice-208 断言族审计行（件④）
        "check_time": now_iso,
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
