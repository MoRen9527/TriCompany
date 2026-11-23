"""plan_enricher — DP-20261123-018 item1-4/6（charter-060521Z 施工批·CTO 认可泛化形）。

在 plan 落盘前由 plan_skill_spawn 调用（fail-open·零阻断）。职责：
 ① tree-facts collector：from 周 trees/ 实况六字段（path/file_count/total_bytes/tree_op_size/sha256_16/mtime）
 ② observed/confidence 逐 tree 注入 migrate/keep 项
 ③ index_assertions：当周实盘 backfill/loose 列表（动态周键名 `<week_slug>_*`）
 ④ families[].items[] owner/timebox/acceptance/depends_on（owner 映射源=charter·镜像防漂移）
 ⑤ staffing.raci（migrate/keep 项与当周顶层散件逐项 accountable 单席）
 ⑥ carry_over owner 拆 accountable 单席 + consulted 数组
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

# 映射源=charter-060521Z（A1A2/E1E2→COS·B1B2→COO·C1C2→CPO·D1D2→CAO/CTO·F1F3→CAO·F2→CPO due 2026-11-23）
# ⚠ 镜像件：charter 变更须同步本表（同「prompt 镜像校验器」族·CTO 2026-11-23）
FAMILY_ITEM_OWNER = {
    "A": "COS", "E": "COS", "B": "COO", "C": "CPO", "D": "CAO", "F": "CAO",
}
F2_OWNER = "CPO"
F2_DUE = "2026-11-23"
_DEFAULT_ACCEPTANCE = "counts 对账零差额 + verify 全量门（plan_structure_full）pass"
_DEFAULT_TIMEBOX = "本周（W 内）"


def _find_week_dir(operating_root: Path, week: str) -> Path | None:
    if not operating_root.is_dir():
        return None
    for d in sorted(operating_root.iterdir()):
        if d.is_dir() and d.name.endswith("-" + week):
            return d
    return None


def _week_slug(week: str) -> str:
    return (week or "").strip().lower()


def _tree_facts_for(tree_dir: Path) -> dict | None:
    if not tree_dir.is_dir():
        return None
    files = [f for f in tree_dir.rglob("*") if f.is_file()]
    total = sum(f.stat().st_size for f in files)
    op = tree_dir / "tree-op.json"
    h = hashlib.sha256()
    for f in sorted(files, key=lambda x: str(x)):
        h.update(str(f.relative_to(tree_dir)).encode("utf-8"))
        try:
            h.update(f.read_bytes())
        except OSError:
            continue
    mt = max([f.stat().st_mtime for f in files], default=tree_dir.stat().st_mtime)
    return {
        "path": str(tree_dir),
        "file_count": len(files),
        "total_bytes": total,
        "tree_op_size": op.stat().st_size if op.is_file() else None,
        "sha256_16": h.hexdigest()[:16],
        "mtime": datetime.fromtimestamp(mt, timezone.utc).isoformat(),
    }


def enrich_plan(plan: dict, run_dir: Path, tmv_root: str | None) -> dict:
    """原地增强 plan 并写 run_dir/tree-facts.json；返回读数 stats。调用面 fail-open 包裹。"""
    stats: dict = {"tree_facts": 0, "observed_injected": 0, "families_items": 0,
                   "raci_items": 0, "carry_over": 0, "backfill_ids": 0, "errors": []}
    if not tmv_root:
        stats["errors"].append("tmv_root absent - enrichment skipped")
        # 形一致：仍落空 tree-facts（消费面零 FileNotFound）
        (run_dir / "tree-facts.json").write_text(
            __import__("json").dumps(
                {"generated_at": datetime.now(timezone.utc).isoformat(),
                 "source_week": str(plan.get("from_week") or ""), "trees": {}},
                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return stats
    operating_root = Path(tmv_root) / "docs" / "workflow" / "operating-records"
    from_week = str(plan.get("from_week") or "")
    to_week = str(plan.get("to_week") or "")
    from_dir = _find_week_dir(operating_root, from_week) if from_week else None
    to_dir = _find_week_dir(operating_root, to_week) if to_week else None
    from_trees = (from_dir / "trees") if from_dir else None

    # ① tree-facts（from 周 trees 实况）
    tree_ids = [str(x.get("item_id")) for x in (plan.get("keep") or []) + (plan.get("migrate") or [])
                if isinstance(x, dict) and x.get("item_id")]
    facts: dict = {}
    if from_trees and from_trees.is_dir():
        for tid in dict.fromkeys(tree_ids):  # 去重保序
            tf = _tree_facts_for(from_trees / tid)
            if tf:
                facts[tid] = tf
    tf_doc = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "source_week": from_week, "trees": facts}
    (run_dir / "tree-facts.json").write_text(
        __import__("json").dumps(tf_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stats["tree_facts"] = len(facts)

    # ② observed/confidence 注入
    for section in ("keep", "migrate"):
        for item in plan.get(section) or []:
            if not isinstance(item, dict):
                continue
            tid = item.get("item_id")
            if tid in facts:
                item["observed"] = facts[tid]
                item["confidence"] = "high"
                stats["observed_injected"] += 1
            else:
                item.setdefault("confidence", "low")

    # ③ index_assertions：当周实盘（动态周键名）
    slug = _week_slug(to_week)
    ia = plan.setdefault("index_assertions", {})
    if not isinstance(ia, dict):
        ia = {}
        plan["index_assertions"] = ia
    backfill: list = []
    loose: list = []
    if to_dir and to_dir.is_dir():
        for d in sorted(to_dir.iterdir()):
            if d.is_dir() and d.name != "trees":
                pass  # 周目录下无子目录约定（trees 在 to_dir/trees）
        trees_dir = to_dir / "trees"
        if trees_dir.is_dir():
            backfill = sorted([p.name for p in trees_dir.iterdir() if p.is_dir()])
        loose = sorted([p.name for p in to_dir.iterdir() if p.is_file() and not p.name.startswith("OP-")])
    ia[f"{slug}_backfill_ids"] = backfill
    ia[f"{slug}_loose_files"] = loose
    ia[f"{slug}_expected_active_count"] = len(backfill)
    stats["backfill_ids"] = len(backfill)

    # ④ families[].items[] 四字段（owner 映射=charter 镜像）
    for fam in plan.get("families") or []:
        if not isinstance(fam, dict):
            continue
        for it in fam.get("items") or []:
            if not isinstance(it, dict):
                continue
            iid = str(it.get("item_id") or "")
            prefix = iid[:1].upper()
            owner = FAMILY_ITEM_OWNER.get(prefix)
            if iid == "F2":
                it["owner"] = F2_OWNER
                it["due"] = F2_DUE
            elif owner:
                it.setdefault("owner", owner)
            it.setdefault("timebox", _DEFAULT_TIMEBOX)
            it.setdefault("acceptance", _DEFAULT_ACCEPTANCE)
            it.setdefault("depends_on", [])
            stats["families_items"] += 1

    # ⑤ staffing.raci（migrate/keep 项 + 当周顶层散件）
    staffing = plan.setdefault("staffing", {})
    if not isinstance(staffing, dict):
        staffing = {}
        plan["staffing"] = staffing
    raci = staffing.setdefault("raci", {})
    if not isinstance(raci, dict):
        raci = {}
        staffing["raci"] = raci
    for section in ("keep", "migrate"):
        for item in plan.get(section) or []:
            if not isinstance(item, dict) or not item.get("item_id"):
                continue
            raci[str(item["item_id"])] = {"accountable": "COS", "responsible": "COS", "due": F2_DUE}
            stats["raci_items"] += 1
    for name in loose:
        raci[name] = {"accountable": "COS", "responsible": "COS", "due": F2_DUE}
        stats["raci_items"] += 1

    # ⑥ carry_over owner 拆解（accountable 单席 + consulted 数组）
    for co in plan.get("carry_over") or []:
        if not isinstance(co, dict):
            continue
        owner = co.get("owner") or "COS"
        co["accountable"] = owner if isinstance(owner, str) and owner else "COS"
        co.setdefault("consulted", ["COS"] if co["accountable"] != "COS" else [])
        stats["carry_over"] += 1

    return stats
