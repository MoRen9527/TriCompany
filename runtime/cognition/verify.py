"""FADE-001 阶段 5: verify cli 迁移验证段（fsd-ten-stage-tech-collab §三路线框架·CTO 裁②同族退出码形）。

业务面切片第五段——判「迁完验迁对」。以 plan.json（阶段 3 产物）为基准面：
  γ 归位    — toWeek 断言（start_date isocalendar 推算 == --to-week·二道闸数学面归位——
              现役 γ 闸在 weekly_plane_shift.py L424-434·十阶段后独立成段）
  index 面  — 新周 index active 断言（to_week OP index 可得+JSON 可解析+activeTrees 键在
              ——结构面·预演形判据 CPO 件 §二阶段 5 行）
  对表面    — plan.migrate vs to_week index 清单逐项验证（生产形·--strict 开关；
              预演形默认 off——迁移器未真跑时对表必炸，--strict 留首拍实走路径）

预演形最小判据（COS 裁决 B）：本段产物落卷即验——verify.json 落 run dir。

退出码（preflight/qualify/plan_scope 同族）：0 全过 → 交棒 score 段；
  2 = 验证拦（plan 缺失/毒化/γ 不符/index 缺/--strict 对表赤字）→ 本拍停·告警面。

输出：verify.json 到 $RUN_DIR（main 层落卷·哑卷防线 exit 2 同族）：
  verify_version / run_id / from_week / to_week / checks[] / verdict / reasons / check_time

调用形（payload 接入点·候部署窗·今晚零生产触）：
  cd /srv/fleet/TriCompany && python3 -m runtime.cognition.verify \\
      --plan-file "$RUN_DIR/plan.json" --from-week W46 --to-week W47 \\
      --start-date "$NEW_WEEK_START" --run-dir "$RUN_DIR" \\
      --operating-root /srv/fleet/TriMetaverse/docs/workflow/operating-records
"""

from __future__ import annotations

import argparse
import sys
import json as _json
from datetime import date, datetime, timezone
from pathlib import Path

VERIFY_VERSION = "1.0.0"


def _load_plan(plan_path: Path) -> tuple[dict | None, str | None]:
    """plan.json 载入（替身禁令：缺/坏=err 不造空 dict 替身）。"""
    if not plan_path.is_file():
        return None, f"plan.json not found: {plan_path}（NOT_FOUND·不造替身）"
    try:
        data = _json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return None, f"plan.json unreadable: {type(e).__name__}: {e}"
    if not isinstance(data, dict):
        return None, "plan.json not a dict"
    return data, None


def check_plan_baseline(plan: dict) -> tuple[bool, list[str]]:
    """断言 A：plan 基准面——verdict=pass+counts 与清单实长一致（毒化拦·轻量复验）。"""
    reasons: list[str] = []
    if plan.get("verdict") != "pass":
        reasons.append(
            f"plan verdict={plan.get('verdict')!r} 非 pass（毒化 plan 不接棒）"
        )
    counts = plan.get("counts")
    if isinstance(counts, dict):
        for key in ("migrate", "keep", "carry_over"):
            if counts.get(key) != len(plan.get(key, [])):
                reasons.append(f"plan counts.{key} != len({key})（结构毒化拦）")
    else:
        reasons.append("plan counts not a dict")
    return (not reasons), reasons


def check_gamma(to_week: str, start_date: str | None) -> tuple[bool, list[str]]:
    """断言 B：γ 归位——start_date isocalendar 周号推算 == to_week（数学面二道闸）。

    start_date 缺省=本断言跳过（payload 必传·缺省时如实注记 skip 不拦）。
    """
    if not start_date:
        return True, ["gamma_skip(no start_date)"]
    try:
        iso = date.fromisoformat(start_date).isocalendar()
        expected = f"W{iso[1]:02d}"
    except ValueError as e:
        return False, [f"gamma_start_date_unparsable: {e}"]
    if expected != to_week:
        return False, [
            f"gamma_mismatch: start_date({start_date}) iso week={expected} != to_week({to_week})"
        ]
    return True, []


def check_new_week_index(
    operating_root: Path, to_week: str, year_hint: str | None
) -> tuple[bool, list[str], Path | None]:
    """断言 C：新周 index active 断言——to_week OP index 可得+可解析+activeTrees 键在。

    year_hint=to 周年段推算用（start_date ISO 年·缺省 glob fallback 唯一命中——
    与 plan_scope._resolve_week_dir 同形语义）。
    """
    week_dir: Path | None = None
    if year_hint:
        cand = operating_root / f"{year_hint}-{to_week}"
        if cand.is_dir():
            week_dir = cand
    if week_dir is None:
        hits = sorted(operating_root.glob(f"*-{to_week}"))
        if len(hits) == 1:
            week_dir = hits[0]
        elif len(hits) > 1:
            return False, [f"to_week dir ambiguous for {to_week}: {[h.name for h in hits]}"], None
    if week_dir is None:
        return False, [f"to_week dir not found: *-{to_week}（NOT_FOUND·不造替身）"], None
    ops = sorted(week_dir.glob("OP-*.json"))
    if not ops:
        return False, [f"to_week OP index not found in {week_dir.name}（NOT_FOUND）"], week_dir
    # 妆容劫持防族规（PM §四）：取最新禁字典序——mtime 序正形
    latest = max(ops, key=lambda p: p.stat().st_mtime)
    try:
        data = _json.loads(latest.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return False, [f"to_week OP index unreadable: {type(e).__name__}: {e}"], week_dir
    if not isinstance(data, dict) or "activeTrees" not in data:
        return False, ["to_week OP index missing activeTrees key（结构面拦）"], week_dir
    return True, [], week_dir


def check_migrate_against_index(
    plan: dict, to_week_dir: Path, to_week: str
) -> tuple[bool, list[str], list[dict]]:
    """断言 D（生产形·--strict）：plan.migrate entries vs to_week index 清单逐项对表。

    对表域=to 周 OP index 的 doneTreesFromPreviousWeek∪activeTrees（迁移器两落点并集——
    doneFromPrev=迁移器落点写实装·activeTrees=周内开工面落点（迁移器不写 to 周值·
    只建 key 兼容）——CTO 审面注一措辞精化·引用锚 weekly_plane.py L282-283/L208）。
    赤字=exit 2 带 deficit 明细。
    逐项读数（PM §一 段 5 行必填）：items=[{entry, status: landed|missing}...]——
    landed=全集−missing 消费侧可推导·strict 面出列（非 strict=对表跳过如实不出列）。
    """
    migrate_entries = [m.get("entry") for m in plan.get("migrate", [])]
    ops = sorted(to_week_dir.glob("OP-*.json"))
    if not ops:
        return False, ["strict: to_week OP index not found（NOT_FOUND）"], []
    # 妆容劫持防族规（PM §四）：mtime 序取最新
    latest = max(ops, key=lambda p: p.stat().st_mtime)
    try:
        data = _json.loads(latest.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return False, [
            f"strict: to_week OP index unreadable: {type(e).__name__}: {e}"
        ], []
    indexed = set()
    for key in ("doneTreesFromPreviousWeek", "activeTrees"):
        for item in data.get(key, []) or []:
            name = item.get("name") if isinstance(item, dict) else str(item)
            if name:
                indexed.add(name)
    items = [
        {"entry": e, "status": "landed" if e in indexed else "missing"}
        for e in migrate_entries
        if e
    ]
    deficit = sorted(i["entry"] for i in items if i["status"] == "missing")
    if deficit:
        return False, [f"strict: migrate entries absent from to_week index: {deficit}"], items
    return True, [], items


# ── 主入口 ─────────────────────────────────────────────────────


def run_verify(args: argparse.Namespace) -> tuple[int, dict]:
    """执行迁移验证并返回 (exit_code, verify dict)。"""
    plan_path = Path(args.plan_file)
    plan, err = _load_plan(plan_path)
    errors: list[str] = []
    checks: list[dict] = []
    if err:
        errors.append(err)
        checks.append({"check": "plan_baseline", "ok": False})
    else:
        ok, reasons = check_plan_baseline(plan)  # type: ignore[arg-type]
        checks.append({"check": "plan_baseline", "ok": ok, "reasons": reasons})
        errors.extend(reasons)

    ok, reasons = check_gamma(args.to_week, args.start_date)
    checks.append({"check": "gamma_week", "ok": ok, "reasons": reasons})
    errors.extend(r for r in reasons if not r.startswith("gamma_skip"))

    operating_root = Path(args.operating_root)
    year_hint = None
    if args.start_date:
        try:
            year_hint = str(date.fromisoformat(args.start_date).isocalendar()[0])
        except ValueError:
            year_hint = None
    ok, reasons, week_dir = check_new_week_index(operating_root, args.to_week, year_hint)
    checks.append({"check": "new_week_index", "ok": ok, "reasons": reasons})
    errors.extend(reasons)

    if args.strict and ok and week_dir is not None and not errors:
        ok2, reasons2, items = check_migrate_against_index(plan, week_dir, args.to_week)  # type: ignore[arg-type]
        entry = {"check": "migrate_vs_index", "ok": ok2, "reasons": reasons2}
        if items:
            entry["items"] = items  # 逐项读数（PM §一 段 5 行·landed/missing 二值）
        checks.append(entry)
        errors.extend(reasons2)

    verify: dict = {
        "verify_version": VERIFY_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "checks": checks,
        "strict_mode": bool(args.strict),
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    if errors:
        verify["verdict"] = "fail"
        verify["reasons"] = errors
        exit_code = 2
    else:
        verify["verdict"] = "pass"
        exit_code = 0
    return exit_code, verify


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 5 迁移验证（verify cli·薄壳）")
    p.add_argument("--plan-file", required=True, help="阶段 3 plan.json 路径（基准面）")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--start-date", default=None, help="New week start date（γ 推算+年段解析）")
    p.add_argument("--run-dir", required=True, help="run 目录（verify.json 落卷位）")
    p.add_argument("--run-id", default="")
    p.add_argument("--operating-root", default="docs/workflow/operating-records")
    p.add_argument(
        "--strict", action="store_true",
        help="生产形对表（plan.migrate vs to_week index 逐项·首拍实走路径）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, verify = run_verify(args)
    out = _json.dumps(verify, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "verify.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"verify.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # 非 UTF-8 宿主输出面兜底（GBK 炸 ⊂ 实锚）
    except Exception:  # noqa: BLE001 — 老宿主无 reconfigure 时维持默认
        pass
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
