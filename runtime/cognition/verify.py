"""FADE-001 阶段 5: verify cli 迁移验证段（fsd-ten-stage-tech-collab §三路线框架·CTO 裁②同族退出码形）。

业务面切片第五段——判「迁完验迁对」。以 plan.json（阶段 3 产物）为基准面：
  γ 归位    — toWeek 断言（start_date isocalendar 推算 == --to-week·二道闸数学面归位——
              现役 γ 闸在 weekly_plane_shift.py L424-434·十阶段后独立成段）
  index 面  — 新周 index active 断言（to_week OP index 可得+JSON 可解析+activeTrees 键在
              ——结构面·预演形判据 CPO 件 §二阶段 5 行）
  对表面    — plan.migrate vs 旧周 trees/ 目录存在性逐项验证（生产形·--strict 开
              关；预演形默认 off——--strict 留首拍实走路径。发现 28 勘修形：
              原判据域=to 周 OP index（done∪active 并集）与迁移执行域（OP index
              元数据层·activeTrees 清空不搬家·weekly_plane.py L282-293 实锚）零
              机械联动→首拍对表全 missing 必炸；迁移现役实形=旧周树原地封存
              （「活随人带走」周内开工面）→对表域改旧周 trees/ 存在性。CTO
              review 卷 §二段 5 处置 d·CEO 11-14 13:59:49 裁令 γ 施工）

预演形最小判据（COS 裁决 B）：本段产物落卷即验——verify.json 落 run dir。

退出码（preflight/qualify/plan_scope 同族）：0 全过 → 交棒 score 段；
  2 = 验证拦（plan 缺失/毒化/γ 不符/index 缺/--strict 对表赤字）→ 本拍停·告警面。

输出：verify.json 到 $RUN_DIR（main 层落卷·哑卷防线 exit 2 同族）：
  verify_version / run_id / from_week / to_week / checks[]
  （plan_baseline/gamma_week/new_week_index[/migrate_vs_index·strict 形]
    +1.1.0 WP5 对账红闸 reconciliation——counts↔readings 差额>0 即红） /
  verdict / reasons / check_time

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

VERIFY_VERSION = "1.2.0"  # WP5 对账红闸施工升版（2026-11-18·minor：checks 增
#   reconciliation 检查项——counts↔readings 差额>0 即红·注入即红锚；
#   notice-185 施工序·拆解任务书获批面）


def check_reconciliation(plan: dict) -> tuple[bool, list[str]]:
    """WP5 对账红闸（2026-11-18·拆解任务书 WP5 面）：counts↔readings 差额>0
    即红——check_plan_baseline 族同构形（轻量复验·毒化拦不接棒）。

    对账函数单值源=plan_scope.reconcile_counts_readings（WP2 铸面·verify
    复用零重复实现——两段同源对账防判定漂移）。1.0.0/1.1.0 旧形 plan
    （agent_readings 缺位）=对账域缺位如实注 skip 不红（向后兼容容忍族）。
    """
    from runtime.cognition.plan_scope import reconcile_counts_readings
    return reconcile_counts_readings(plan)


_FC_PATTERNS = (
    ("truncation", r"max.?tokens|truncat|16384"),
    ("tool_explore", r"tool.?call|工具调用|rate.?limit|429|503"),
    ("argv", r"unrecognized arguments|invalid choice|argv"),
    ("timeout", r"ETIMEDOUT|timed out|timeout|超时"),
)


def classify_failure(text: str) -> list[str]:
    """R10-COO-01：失败归族（单一源·供 run_verify 与白盒直测）。"""
    import re as _re
    classes = [name for name, pat in _FC_PATTERNS if _re.search(pat, text or "", _re.I)]
    return classes


def check_plan_structure(plan: dict) -> tuple[bool, list[str]]:
    """DP-20261123-015 全量质量门（CTO 裁③终点拦截·门不豁免哲学）：
    spawn 形与 CLI 形门等值——调 plan_scope._structure_gate 全集（顶层键/bidirectional_ok/
    counts 结构/readings 三件套/disposition 五态）。错误如实投影（上限 50 防爆卷），零静默。"""
    from runtime.cognition.plan_scope import _structure_gate
    errs = _structure_gate(plan)
    return (not errs), errs[:50]


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


def check_migrate_against_from_week_trees(
    plan: dict, operating_root: Path, from_week: str
) -> tuple[bool, list[str], list[dict]]:
    """断言 D（生产形·--strict·发现 28 勘修形）：plan.migrate vs 旧周 trees/
    目录存在性逐项对表。

    发现 28 定谳（CTO review 卷 §二段 5·处置倾向 d）：段 3 判据域（trees/ 文件
    系统层）与段 4 迁移执行域（OP index 元数据层·done 树搬家·activeTrees 清空
    不搬家·weekly_plane.py L282-293 白盒实锚）零机械联动——迁移现役实形=旧周
    树**原地封存**（不物理搬家·「活随人带走」=周内开工面落点）→对表域改
    「旧周 trees/ 目录存在性」；done 条目对表域维持 to 周 index（断言 C
    new_week_index 承载·本函数零触）。原 to 周 index 并集对表形退役（判据本体
    逐项验证+items 读数+deficit fail-closed 拦截机制原样保留·零删改）。

    逐项读数（PM §一 段 5 行必填）：items=[{entry, status: landed|missing}...]——
    landed=全集−missing 消费侧可推导·strict 面出列（非 strict=对表跳过如实不出列）。
    存在性判据=Path.exists()（kind 面不判——散文件树容忍·发现 4 kind 错标债在
    plan_scope 域不在本函数）。
    赤字=exit 2 带 deficit 明细。
    """
    migrate_entries = [m.get("entry") for m in plan.get("migrate", [])]
    hits = sorted(operating_root.glob(f"*-{from_week}"))
    if len(hits) == 0:
        return False, [
            f"strict: from_week dir not found: *-{from_week}（NOT_FOUND·不造替身）"
        ], []
    if len(hits) > 1:
        return False, [
            f"strict: from_week dir ambiguous for {from_week}: {[h.name for h in hits]}"
        ], []
    trees_dir = hits[0] / "trees"
    if not trees_dir.is_dir():
        return False, [
            f"strict: from_week trees/ dir not found: {hits[0].name}/trees（NOT_FOUND）"
        ], []
    items = [
        {"entry": e, "status": "landed" if (trees_dir / e).exists() else "missing"}
        for e in migrate_entries
        if e
    ]
    deficit = sorted(i["entry"] for i in items if i["status"] == "missing")
    if deficit:
        return False, [
            f"strict: migrate entries absent from from_week trees/: {deficit}"
            "（原地封存语义·发现 28 勘修形）"
        ], items
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
        checks.append({"check": "reconciliation",
                       "ok": False,
                       "reasons": ["plan_baseline failed·对账红闸不可用（WP5·基准面缺失）"]})
        checks.append({"check": "plan_structure_full", "ok": False,
                       "reasons": ["plan load failed·全量质量门不可用（DP-015）"]})
    else:
        ok, reasons = check_plan_baseline(plan)  # type: ignore[arg-type]
        checks.append({"check": "plan_baseline", "ok": ok, "reasons": reasons})
        errors.extend(reasons)
        # WP5 对账红闸（差额>0 即红·注入即红锚——plan_baseline 后追加）
        # v8 item1（CEO 批）：run_id 强制对表——plan.run_id 必须等于 --run-id（隔离主键·对不上即 fail）
        _plan_rid = plan.get("run_id") if isinstance(plan, dict) else None
        _rid_ok = bool(args.run_id) and _plan_rid == args.run_id
        checks.append({"check": "run_id_match", "ok": _rid_ok,
                       "reasons": [] if _rid_ok else
                       [f"plan.run_id={_plan_rid!r} != --run-id={args.run_id!r}（v8 item1 隔离主键）"]})
        if not _rid_ok:
            errors.append(f"run_id 对表败（v8 item1）：plan={_plan_rid!r} vs arg={args.run_id!r}")
        ok_r, reasons_r = check_reconciliation(plan)  # type: ignore[arg-type]
        checks.append({"check": "reconciliation", "ok": ok_r,
                       "reasons": reasons_r})
        errors.extend(reasons_r if not ok_r else [])
        # DP-20261123-015 全量质量门（终点拦截·spawn/CLI 两形门等值——flip 隐性代价修）
        ok_s, reasons_s = check_plan_structure(plan)  # type: ignore[arg-type]
        checks.append({"check": "plan_structure_full", "ok": ok_s,
                       "reasons": reasons_s})
        errors.extend(reasons_s if not ok_s else [])

    # v8 item1：--strict 必填（不传=显式 fail·防静默轻跑）；生产链 argv 已随行传 --strict
    if not args.strict:
        errors.append("--strict 必填缺失（v8 item1·verify 强制严格形）")
        checks.append({"check": "strict_required", "ok": False,
                       "reasons": ["--strict 必填缺失（v8 item1）"]})
    else:
        checks.append({"check": "strict_required", "ok": True, "reasons": []})
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

    if args.strict and not errors:
        # 发现 28 勘修形：对表域=旧周 trees/ 目录存在性（from_week 解析在对表
        # 函数内）——to 周 index 断言（上方 new_week_index）独立拦·不再是对表
        # 前置（结构性失败已使 errors 非空不触发本段）。
        ok2, reasons2, items = check_migrate_against_from_week_trees(
            plan, operating_root, args.from_week  # type: ignore[arg-type]
        )
        # check 键名 "migrate_vs_index" 保持=消费面契约（score_engine._judge_g
        # L249 按名索引 items·发现 28 勘修只换对表域零换键名·键名历史包袱如实
        # 注·候名面勘正窗）。
        entry = {"check": "migrate_vs_index", "ok": ok2, "reasons": reasons2}
        if items:
            entry["items"] = items  # 逐项读数（PM §一 段 5 行·landed/missing 二值）
        checks.append(entry)
        errors.extend(reasons2)

    # R10-COO-01（CEO 批讫 2026-11-23 19:51:38）：失败归族（failure_class）——
    # 红因自动归类供 COS 判据与修复轮分派；pass 轮=空表。
    _fc_pool = " ".join([str(r) for r in errors]
                        + [str(ch.get("reasons")) for ch in checks])
    failure_class = classify_failure(_fc_pool)
    if errors and not failure_class:
        failure_class = ["unclassified"]

    verify: dict = {
        "verify_version": VERIFY_VERSION,
        "failure_class": failure_class,
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
    p.add_argument("--run-id", required=True, help="v8 item1：必填（与 plan.run_id 对表·隔离主键）")
    p.add_argument("--operating-root", default="docs/workflow/operating-records")
    p.add_argument(
        "--strict", action="store_true",
        help="生产形对表（plan.migrate vs 旧周 trees/ 存在性逐项·发现 28 勘修形·首拍实走路径）",
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
