"""FADE-001 阶段 3: plan skill 迁移范围预审段（fsd-ten-stage-tech-collab-20261113 §二·CTO 裁① APPROVE）。

业务面切片第三段（与 preflight「该不该跑」/qualify「有没有资格跑」零重叠探针零复检）——
判「迁什么不迁什么」。语义锚（CPO 件 C）：「这是一周的记录，还是这一周的活——
记录随周封存·活随人带走」。

三分类（机械判据·§二.8 实盘勘定修正版）：
  migrate    — 在途树（活随人带走）→清单候选面。预演形=零动手候审；
               生产形=清单驱动 OP index 元数据层搬家（文件树本体原地封存——
               现役 migrate_weekly_plane 动作域=index 层·weekly_plane.py L231-311 白盒实锚）。
  keep       — 全 close/记录面（记录随周封存·原地留档）——degrade 链终态=保守 keep。
  carry_over — unresolved-items §1 现役区 CARRY 行（两形正则·带状态去向）。

判据要点（§二.8 四发现实锚）：
  1. 全集 S={from_week}/trees/ 全条目（目录+散文件混装形）——OP index 与实盘脱节是
     现势常态（W46 activeTrees=0 vs 实盘 20+），index 只作旁证对表层（index_drift 读数）。
  2. 目录 degrade 链：tree-op.json status → authorization.json expiry → 默认 keep
     （漏迁毒于误封存——verify 对表+carry_over 面+生产形候审三兜底）。
  3. CARRY id 两形：`CARRY-YYYYMMDD-NNN`（日期形·实盘 CARRY-20260728-004）|
     `CARRY-NNN`（纯数字形·现役 shift_carry_over L103 域）——现役纯数字正则对日期形
     漏匹配（缺陷候选已登记候 CTO 裁），本模块判据面兼容两形。
  4. 散文件（.md 单件）默认 keep 原地封存。

双向枚举断言（STE 锚②·CPO 三标准之一；表述勘正 2026-11-14 review 日·发现 32
  CTO 裁词照录）：**M∪K=S（trees 域双向断言·零遗漏 ∧ 两两交=∅ 零重叠）∧ C 独立解析
  （unresolved-items 域·带状态去向·不进 S 断言）**——S 定义=trees/ 全条目（判据要点 1），
  CARRY 行域=unresolved-items 文件不同域不在 S 内（原稿「∪C=S」字面永假=表述含混；
  实现面 bidirectional_check 一向如此·本勘正仅 docstring 零行为）。违即 exit 2 拦。
  替身禁令（STE 锚⑤·S51 三向）：目录缺失/不可读/结构门毒化=
  exit 2 FAIL-EXPECTED——禁造替身清单（空 keep 全集形=最毒替身·双向断言会假绿）。

退出码（preflight/qualify 同族）：0 全过 → 交棒（DCE 照单执行）；
  2 = 范围拦（双向断言违/扫描败/结构门毒化）→ 本拍不执行（plan.json 带 verdict=fail 落卷）。

输出：单份 JSON 到 stdout（bash 重定向落 $RUN_DIR/plan.json·CPO 对接点②命名族）——
plan_version / run_id / from_week / to_week / migrate[] / keep[] / carry_over[] /
counts / bidirectional_ok / index_drift / other_unresolved_count / check_time。

调用形（payload vC 接入点·候部署窗·今晚零生产触）：
  cd /srv/fleet/TriCompany && python3 -m runtime.cognition.plan_scope \\
      --from-week W46 --to-week W47 --run-dir "$RUN_DIR" \\
      --operating-root /srv/fleet/TriMetaverse/docs/workflow/operating-records
"""

from __future__ import annotations

import argparse
import json as _json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path

PLAN_VERSION = "1.0.0"

# CARRY id 两形（§二.8③·日期形实盘在役+纯数字形现役域）
_CARRY_ID_RE = re.compile(r"^\s*\|\s*`(CARRY-\d{8}-\d+|CARRY-\d+)`\s*\|")
# 树内未过期授权=在途标记（authorization.json expiry 面秒级 epoch 或 ISO）
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
# tree-op.json status → keep 终态集（其余非空值=在途 migrate）
_KEEP_STATUS = {"done", "closed", "retired", "cancelled"}


# ── 分类器（degrade 链·§二.8④） ──────────────────────────────────────────


def _parse_expiry(value: str) -> datetime | None:
    """authorization expiry 面解析（ISO 8601 或 epoch 毫秒·解析败=None=视为在途保守拦）。"""
    v = value.strip()
    if v.isdigit():
        try:
            return datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    if _ISO_TS_RE.match(v):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def classify_dir(tree: Path, now: datetime) -> tuple[str, list[str]]:
    """目录分类 degrade 链：tree-op.json status → authorization expiry → keep。"""
    # 1) tree-op.json status 面（若有）
    top = tree / "tree-op.json"
    if top.is_file():
        try:
            data = _json.loads(top.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 坏 tree-op=结构信号丢失→降级继续链（不炸不替）
            data = None
        if isinstance(data, dict):
            status = str(data.get("status", "")).strip().lower()
            if status in _KEEP_STATUS:
                return "keep", ["tree_op_status:" + status]
            if status:
                return "migrate", ["tree_op_status:" + status]
    # 2) authorization.json expiry 面（若有·未过期=在途活授权）
    auth = tree / "authorization.json"
    if auth.is_file():
        try:
            adata = _json.loads(auth.read_text(encoding="utf-8"))
            expiry_raw = str(
                (adata.get("expiry") if isinstance(adata, dict) else None) or ""
            )
        except Exception:  # noqa: BLE001 — 坏 authorization=同降级
            expiry_raw = ""
        if expiry_raw:
            exp = _parse_expiry(expiry_raw)
            if exp is None or exp > now:
                # 解析败=保守在途（过期判断不可得时不放行）
                return "migrate", ["authorization_active_or_unparsable"]
            return "keep", ["authorization_expired"]
    # 3) 默认 keep（保守·漏迁毒于误封存——verify 对表+carry_over+候审三兜底）
    return "keep", ["no_active_markers_default_keep"]


def scan_trees(week_dir: Path, now: datetime) -> tuple[dict[str, list[str]] | None, str | None]:
    """全集扫描（目录+散文件两类）——返回 {name: (category 附 reason)} 或 (None, err)。

    替身禁令：week_dir 缺失/不可读=FAIL-EXPECTED（返回 err 非空清单替身）。
    """
    if not week_dir.is_dir():
        return None, f"trees dir not found: {week_dir}（NOT_FOUND·不造替身）"
    entries: dict[str, list[str]] = {}
    try:
        children = sorted(week_dir.iterdir(), key=lambda p: p.name)
    except Exception as e:  # noqa: BLE001 — 扫描异常同拦
        return None, f"trees dir unreadable: {type(e).__name__}: {e}（不造替身）"
    for child in children:
        name = child.name
        if child.is_dir():
            cat, reasons = classify_dir(child, now)
        else:
            cat, reasons = "keep", ["scatter_file_archive"]
        entries[name] = [cat] + reasons  # [category, *reason_codes]
    return entries, None


# ── carry_over 解析（两形正则·状态去向面） ────────────────────────────────


def parse_carry_rows(unresolved_path: Path) -> tuple[list[dict], int, str | None]:
    """unresolved-items §1 现役区 CARRY 行解析（两形）——返回 (rows, other_count, err)。

    other_count=非 CARRY 前缀的 unresolved 行数（REGR-/BUG- 等·读数如实面不进清单——
    与现役 shift_carry_over bump 域同域）。文件缺失=合法空集（carry 面缺失是迁移器
    carry_over 步的域·非 plan 拦点）。
    """
    if not unresolved_path.is_file():
        return [], 0, None  # 合法空集+读数面
    try:
        text = unresolved_path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 读败=扫描异常族（替身禁令）
        return [], 0, f"unresolved-items unreadable: {type(e).__name__}: {e}"
    rows: list[dict] = []
    other = 0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        m = _CARRY_ID_RE.match(line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            carry_id = m.group(1)
            # 状态去向面（行内词面归类·CPO 三标准之三 carry_over 带状态去向）
            joined = " ".join(cells)
            if "frozen" in joined.lower() or "冻结" in joined:
                status_to = "frozen"
            elif "已修" in joined or "销账" in joined:
                status_to = "closed"
            else:
                status_to = "pending_review"
            rows.append({
                "carry_id": carry_id,
                "cells": cells[:6],  # 截断防超长行进卷
                "status_to": status_to,
            })
        elif re.match(r"^\s*\|\s*`?[A-Z]{3,}-", line):
            other += 1
    return rows, other, None


# ── 双向枚举断言（STE 锚②） ───────────────────────────────────────────────


def bidirectional_check(
    entries: dict[str, list[str]], migrate: list[str], keep: list[str]
) -> tuple[bool, list[str]]:
    """M∪K=S（零遗漏）∧ M∩K=∅（零重叠）——违例明细返回（替身禁令配套）。"""
    violations: list[str] = []
    mset, kset = set(migrate), set(keep)
    covered = mset | kset
    all_names = set(entries.keys())
    uncovered = sorted(all_names - covered)
    if uncovered:
        violations.append(f"uncovered(漏): {uncovered}")
    overlap = sorted(mset & kset)
    if overlap:
        violations.append(f"overlap(重): {overlap}")
    phantom = sorted(covered - all_names)
    if phantom:
        violations.append(f"phantom(清单外幽灵): {phantom}")
    return (not violations), violations


# ── index 旁证对表层（§二.8①·index_drift 读数） ──────────────────────────


def index_drift(week_dir: Path, migrate_count: int) -> dict:
    """OP index activeTrees/doneTrees vs 实盘 migrate 数对表——旁证读数·读败不拦。"""
    drift: dict = {}
    try:
        ops = sorted(week_dir.glob("OP-*.json"))
        if not ops:
            return {"note": "no OP index found（旁证缺位·不拦）"}
        # 妆容劫持防族规（PM §四/STE §三.4）：取最新禁字典序——mtime 序正形
        latest = max(ops, key=lambda p: p.stat().st_mtime)
        data = _json.loads(latest.read_text(encoding="utf-8"))
        drift["index_file"] = latest.name
        drift["index_activeTrees"] = len(data.get("activeTrees", []))
        drift["index_doneTreesThisWeek"] = len(data.get("doneTreesThisWeek", []))
        drift["plan_migrate"] = migrate_count
        drift["note"] = (
            "index 与实盘脱节为现势常态（W46 实锚 activeTrees=0 vs 实盘 20+）——"
            "旁证读数非分类基准"
        )
    except Exception as e:  # noqa: BLE001 — 旁证层读败如实注记不拦
        drift["error"] = f"{type(e).__name__}: {e}"
    return drift


# ── 结构门（STE 锚①·schema 断言·写前自校验——毒化拦不写假卷） ─────────────


def _structure_gate(plan: dict) -> list[str]:
    errors: list[str] = []
    for key in (
        "plan_version", "run_id", "from_week", "to_week",
        "migrate", "keep", "carry_over", "counts",
        "bidirectional_ok", "check_time",
    ):
        if key not in plan:
            errors.append(f"missing required key: {key}")
    counts = plan.get("counts")
    if isinstance(counts, dict):
        if counts.get("migrate") != len(plan.get("migrate", [])):
            errors.append("counts.migrate != len(migrate)（结构毒化拦）")
        if counts.get("keep") != len(plan.get("keep", [])):
            errors.append("counts.keep != len(keep)（结构毒化拦）")
        if counts.get("carry_over") != len(plan.get("carry_over", [])):
            errors.append("counts.carry_over != len(carry_over)（结构毒化拦）")
    else:
        errors.append("counts not a dict")
    if plan.get("bidirectional_ok") is not True and plan.get("verdict") != "fail":
        errors.append("bidirectional_ok!=true 且非 fail verdict（矛盾态拦）")
    return errors


# ── 周目录名解析（实盘形={ISO 年}-W{nn}·2026-W46——§二.8 实锚弹外补） ─────


def _resolve_week_dir(operating_root: Path, week_token: str, start_date: str | None) -> tuple[Path | None, str | None]:
    """实盘周目录名带年段（`2026-W46`）——start_date ISO 年推算·缺省 glob fallback。

    fallback 多命中=err（fail-closed·不猜）。
    """
    if start_date:
        try:
            year = date.fromisoformat(start_date).isocalendar()[0]
            candidate = operating_root / f"{year}-{week_token}"
            if candidate.is_dir():
                return candidate, None
        except ValueError:
            pass
    hits = sorted(operating_root.glob(f"*-{week_token}"))
    if len(hits) == 1:
        return hits[0], None
    if len(hits) > 1:
        return None, f"week dir ambiguous for {week_token}: {[h.name for h in hits]}"
    return None, None


# ── 主入口 ─────────────────────────────────────────────────────


def run_plan(args: argparse.Namespace, now: datetime | None = None) -> tuple[int, dict]:
    """执行范围预审并返回 (exit_code, plan dict)。now 可注入（单测）。"""
    now = now or datetime.now(timezone.utc)
    operating_root = Path(args.operating_root)
    from_dir, week_err = _resolve_week_dir(operating_root, args.from_week, args.start_date)
    trees_dir = from_dir / "trees" if from_dir is not None else operating_root / "__unresolved__" / "trees"

    errors: list[str] = []
    scan: dict[str, list[str]] | None = None
    scan_err: str | None = None
    if week_err:
        errors.append(week_err)
    else:
        scan, scan_err = scan_trees(trees_dir, now)

    unresolved: Path | None = None
    if from_dir is not None:
        if args.op_id:
            unresolved = from_dir / f"{args.op_id}.unresolved-items.md"
        else:
            unresolved = _find_unresolved(from_dir)
    if unresolved is not None:
        carry_rows, other_count, carry_err = parse_carry_rows(unresolved)
    else:
        carry_rows, other_count, carry_err = [], 0, None

    if scan_err:
        errors.append(scan_err)
    if carry_err:
        errors.append(carry_err)

    migrate: list[dict] = []
    keep: list[dict] = []
    if scan is not None:
        for name, tags in scan.items():
            cat, reasons = tags[0], tags[1:]
            # 发现 4（CTO 派工 2026-11-14·八项之 4）：kind=is_dir 实值——散文件
            # 标 file 不再恒 dir（读数面失真修复·双向断言按 entry 名不受影响）。
            kind = "dir" if (trees_dir / name).is_dir() else "file"
            item = {"entry": name, "kind": kind, "reason_codes": reasons}
            if cat == "migrate":
                migrate.append(item)
            else:
                keep.append(item)

    # 双向断言（扫描成功才判——扫描败时 errors 已拦）
    bidir_ok = True
    violations: list[str] = []
    if scan is not None and not errors:
        bidir_ok, violations = bidirectional_check(
            scan, [m["entry"] for m in migrate], [k["entry"] for k in keep]
        )
        if not bidir_ok:
            errors.extend(violations)

    plan: dict = {
        "plan_version": PLAN_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "migrate": migrate,
        "keep": keep,
        "carry_over": carry_rows,
        "counts": {
            "migrate": len(migrate),
            "keep": len(keep),
            "carry_over": len(carry_rows),
        },
        "bidirectional_ok": bidir_ok,
        "violations": violations,
        "other_unresolved_count": other_count,
        "index_drift": index_drift(from_dir, len(migrate)) if from_dir is not None else {"note": "week dir unresolved（旁证缺位·不拦）"},
        "check_time": now.isoformat(),
    }
    if errors:
        plan["verdict"] = "fail"
        plan["reasons"] = errors
        exit_code = 2
    else:
        gate_errors = _structure_gate(plan)
        if gate_errors:
            plan["verdict"] = "fail"
            plan["reasons"] = gate_errors
            exit_code = 2
        else:
            plan["verdict"] = "pass"
            exit_code = 0
    return exit_code, plan


def _find_unresolved(from_dir: Path) -> Path | None:
    """OP id 未显式传时 glob unresolved-items 件（单一命中用之·多/零命中返回 None）。"""
    hits = sorted(from_dir.glob("OP-*.unresolved-items.md"))
    return hits[0] if len(hits) == 1 else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 3 迁移范围预审（plan skill·薄壳）")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--run-dir", required=True, help="本拍 run 目录（plan.json 落卷位·payload 传入）")
    p.add_argument("--run-id", default="", help="run id（payload 铸形段传入·空=留白面）")
    p.add_argument("--operating-root", default="docs/workflow/operating-records")
    p.add_argument("--start-date", default=None, help="New week start date YYYY-MM-DD（周目录年段推算·payload 模板变量现成）")
    p.add_argument("--op-id", default=None, help="OP index id（缺省=自动 glob 单一命中）")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, plan = run_plan(args)
    out = _json.dumps(plan, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "plan.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 落卷败=哑卷防线（同 qualify run dir 语义）
        print(f"plan.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
