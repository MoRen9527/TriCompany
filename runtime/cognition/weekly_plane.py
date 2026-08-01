"""weekly_plane — ADE 周工作平面 CLI

标准化周经营记录的创建、迁移和闭合操作。
Agent 规划 → CLI 确定性执行 → ADE JSON 自检 → Agent 收口。

用法:
  python -m runtime.cognition.weekly_plane create --week W32 --start-date 2026-08-03
  python -m runtime.cognition.weekly_plane migrate --from W31 --to W32
  python -m runtime.cognition.weekly_plane close --week W31
"""

from __future__ import annotations

import argparse
import json as _json
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ── constants ──

WEEKLY_INDEX_OBJECT_TYPE = "WEEKLY_INDEX"
TREE_OP_OBJECT_TYPE = "TREE_OPERATING_PLAN"

REQUIRED_INDEX_FIELDS = [
    "dependsOn", "objectType", "objectId", "title",
    "ownerRole", "status", "summary", "metadata",
    "priority", "timebox", "createdAt", "relatedModules", "updatedAt",
    "activeTrees", "doneTreesThisWeek", "nextActions"
]

WEEK_PATTERN = r"^W\d{2}$"  # W01-W99

# ── ADE types ──

@dataclass
class ADEResult:
    status: str  # pass | fail | partial
    summary: dict
    changes: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    check_time: str = ""

    def to_ade_json(self) -> dict:
        return {
            "status": self.status,
            "summary": self.summary,
            "changes": self.changes,
            "errors": self.errors,
            "check_time": self.check_time or datetime.now(timezone.utc).isoformat(),
        }


# ── helpers ──

def _check_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return _json.load(fh)
    except Exception:
        return None


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        _json.dump(data, fh, indent=4, ensure_ascii=False)
    tmp.replace(path)


def _parse_week(week_str: str) -> tuple[int, int]:
    """Parse W32 -> (32,). Return (week_number,)."""
    import re
    m = re.match(r"^W(\d{2})$", week_str)
    if not m:
        raise ValueError(f"Invalid week format: {week_str}. Expected W01-W99.")
    return (int(m.group(1)),)


def _week_dir(operating_root: Path, week_str: str, start_date: str | None = None) -> Path:
    """Resolve week directory. Uses start_date for year if provided, else current year."""
    if start_date:
        year = datetime.fromisoformat(start_date).year
    else:
        year = datetime.now(timezone.utc).year
    return operating_root / f"{year}-{week_str}"


def _index_object_id(week_str: str, start_date: str) -> str:
    """Generate OP object ID matching convention: OP-YYYYMM-WXX-001."""
    dt = datetime.fromisoformat(start_date)
    return f"OP-{dt.year}{dt.month:02d}-{week_str}-001"


def _find_index_path(operating_root: Path, week_str: str) -> Path | None:
    """Find an existing weekly index file by week pattern. Searches for OP-*-{week}-*.json."""
    week_dir = _week_dir(operating_root, week_str)
    if not week_dir.exists():
        return None
    candidates = list(week_dir.glob(f"OP-*-{week_str}-*.json"))
    return candidates[0] if candidates else None


def _index_path(operating_root: Path, week_str: str, start_date: str = "") -> Path:
    """Get index path. Uses start_date for new files, searches existing files as fallback."""
    if start_date:
        return _week_dir(operating_root, week_str, start_date) / f"{_index_object_id(week_str, start_date)}.json"
    # Try to find existing file
    existing = _find_index_path(operating_root, week_str)
    if existing:
        return existing
    # Return a path that doesn't exist yet (for validation error reporting)
    return _week_dir(operating_root, week_str) / f"OP-{week_str}-NOT-FOUND.json"


# ── create ──

def create_weekly_plane(
    operating_root: Path,
    week_str: str,
    *,
    start_date: str,
    previous_week: str | None = None,
    dry_run: bool = True,
) -> ADEResult:
    """Create a new weekly operating index."""
    check_time = _check_time()
    changes: list[dict] = []
    errors: list[dict] = []

    # Validate week format
    try:
        week_num, year = _parse_week(week_str)
    except ValueError as e:
        return ADEResult(status="fail", summary={"created": False},
            errors=[{"item": week_str, "reason": str(e)}], check_time=check_time)

    # Check if already exists
    target_path = _index_path(operating_root, week_str, start_date)
    existing = _find_index_path(operating_root, week_str)
    if existing:
        errors.append({"item": str(existing), "reason": "already_exists"})
        return ADEResult(status="fail",
            summary={"created": False, "errors": 1},
            errors=errors, check_time=check_time)

    # Calculate timebox
    from datetime import date, timedelta
    start = date.fromisoformat(start_date)
    end = start + timedelta(days=6)  # Sunday

    # Build index
    object_id = _index_object_id(week_str, start_date)
    prev_ref = None
    if previous_week:
        prev_ref = f"docs/workflow/operating-records/{year}-{previous_week}/{_index_object_id(previous_week)}.json"

    index = {
        "dependsOn": [f"OP-{year}{week_num-1:02d}-{previous_week or 'W' + str(week_num-1).zfill(2)}-001"] if previous_week else [],
        "objectType": WEEKLY_INDEX_OBJECT_TYPE,
        "objectId": object_id,
        "title": f"TriMetaverse {week_str} 周经营维护索引",
        "ownerRole": "CEOChiefOfStaff",
        "status": "active",
        "summary": f"{week_str} 周经营维护。任务从上周迁移，新任务待规划。",
        "metadata": {
            "updatedBy": "CEOChiefOfStaff",
            "version": "1.0.0",
            "lastUpdated": check_time,
            "workflowTags": ["每周维护", "CEO 总助维护面", "经营维护计划单"],
            "latestActiveWeek": True,
            "phase": "ceo-copilot-host-coordination",
        },
        "priority": "high",
        "timebox": {
            "scope": "weekly",
            "label": f"{year}-{week_str} 当前周维护面",
            "startAt": f"{start.isoformat()}T00:00:00+08:00",
            "endAt": f"{end.isoformat()}T23:59:59+08:00",
        },
        "createdAt": check_time,
        "relatedModules": ["TriMetaverse", "TriCompany", "TriLC", "TriMC"],
        "updatedAt": check_time,
        "activeTrees": [],
        "doneTreesFromPreviousWeek": [],
        "doneTreesThisWeek": [],
        "nextActions": [],
    }

    if dry_run:
        return ADEResult(status="pass",
            summary={"created": False, "dry_run": True, "path": str(target_path)},
            changes=[{"action": "would_create", "target": str(target_path)}],
            check_time=check_time)

    # Write
    _save_json(target_path, index)
    changes.append({"action": "created", "target": str(target_path), "object_id": object_id})

    return ADEResult(status="pass",
        summary={"created": True, "dry_run": False, "object_id": object_id},
        changes=changes, check_time=check_time)


# ── migrate ──

def migrate_weekly_plane(
    operating_root: Path,
    from_week: str,
    to_week: str,
    *,
    dry_run: bool = True,
) -> ADEResult:
    """Migrate done trees from previous week to new week, retire previous week."""
    check_time = _check_time()
    changes: list[dict] = []
    errors: list[dict] = []

    from_path = _index_path(operating_root, from_week)
    to_path = _index_path(operating_root, to_week)

    # Validate
    if not from_path.exists():
        errors.append({"item": str(from_path), "reason": "source_index_not_found"})
        return ADEResult(status="fail", summary={"migrated": False, "errors": 1},
            errors=errors, check_time=check_time)

    if not to_path.exists():
        errors.append({"item": str(to_path), "reason": "target_index_not_found"})
        return ADEResult(status="fail", summary={"migrated": False, "errors": 1},
            errors=errors, check_time=check_time)

    from_data = _load_json(from_path)
    to_data = _load_json(to_path)

    if not from_data or not to_data:
        errors.append({"item": "parse", "reason": "invalid_json"})
        return ADEResult(status="fail", summary={"migrated": False, "errors": 1},
            errors=errors, check_time=check_time)

    # Collect done trees from source week
    done_trees = list(from_data.get("doneTreesThisWeek", []))
    previous_done = list(from_data.get("doneTreesFromPreviousWeek", []))

    if dry_run:
        return ADEResult(status="pass",
            summary={"migrated": False, "dry_run": True,
                "from_week": from_week, "to_week": to_week,
                "trees_to_migrate": len(done_trees)},
            changes=[{"action": "would_migrate", "trees": [t.get("treeId") for t in done_trees]}],
            check_time=check_time)

    # Move trees: from_week doneTreesThisWeek → to_week doneTreesFromPreviousWeek
    to_data["doneTreesFromPreviousWeek"] = previous_done + done_trees
    to_data["metadata"]["previousWeekRef"] = f"docs/workflow/operating-records/{from_path.parent.name}/{from_path.name}"

    # Retire source week
    from_data["status"] = "closed"
    from_data["activeTrees"] = []
    from_data["metadata"]["latestActiveWeek"] = False
    from_data["metadata"]["nextWeekRef"] = f"docs/workflow/operating-records/{to_path.parent.name}/{to_path.name}"
    from_data["metadata"]["lastUpdated"] = check_time

    _save_json(from_path, from_data)
    _save_json(to_path, to_data)

    changes.append({"action": "retired", "target": str(from_path), "week": from_week})
    changes.append({"action": "migrated", "target": str(to_path), "trees": len(done_trees)})

    return ADEResult(status="pass",
        summary={"migrated": True, "from_week": from_week, "to_week": to_week,
            "trees_migrated": len(done_trees)},
        changes=changes, check_time=check_time)


# ── close ──

def close_weekly_plane(
    operating_root: Path,
    week_str: str,
    *,
    dry_run: bool = True,
) -> ADEResult:
    """Close the current week (retire index, mark latestActiveWeek=false)."""
    check_time = _check_time()
    errors: list[dict] = []

    target_path = _index_path(operating_root, week_str)
    if not target_path.exists():
        errors.append({"item": str(target_path), "reason": "index_not_found"})
        return ADEResult(status="fail", summary={"closed": False},
            errors=errors, check_time=check_time)

    data = _load_json(target_path)
    if not data:
        errors.append({"item": str(target_path), "reason": "invalid_json"})
        return ADEResult(status="fail", summary={"closed": False},
            errors=errors, check_time=check_time)

    # Validate no active trees remain
    active = data.get("activeTrees", [])
    if active:
        errors.append({"item": "activeTrees",
            "reason": f"{len(active)} active tree(s) remain: {[t.get('treeId') for t in active]}"})
        return ADEResult(status="fail", summary={"closed": False, "active_trees": len(active)},
            errors=errors, check_time=check_time)

    if dry_run:
        return ADEResult(status="pass",
            summary={"closed": False, "dry_run": True, "week": week_str},
            check_time=check_time)

    data["status"] = "closed"
    data["activeTrees"] = []
    data["metadata"]["latestActiveWeek"] = False
    data["metadata"]["lastUpdated"] = check_time
    data["updatedAt"] = check_time

    _save_json(target_path, data)

    return ADEResult(status="pass",
        summary={"closed": True, "week": week_str},
        changes=[{"action": "closed", "target": str(target_path), "week": week_str}],
        check_time=check_time)


# ── validate ──

def validate_index(path: Path) -> ADEResult:
    """Validate a weekly index JSON for completeness."""
    check_time = _check_time()
    errors: list[dict] = []

    data = _load_json(path)
    if not data:
        return ADEResult(status="fail", summary={"valid": False},
            errors=[{"item": str(path), "reason": "invalid_json_or_missing"}],
            check_time=check_time)

    # Check required fields
    for field in REQUIRED_INDEX_FIELDS:
        if field not in data:
            errors.append({"item": field, "reason": "missing_required_field"})

    # Check objectType
    if data.get("objectType") != WEEKLY_INDEX_OBJECT_TYPE:
        errors.append({"item": "objectType", "reason": f"expected {WEEKLY_INDEX_OBJECT_TYPE}, got {data.get('objectType')}"})

    # Check status
    if data.get("status") not in ("active", "closed"):
        errors.append({"item": "status", "reason": f"invalid status: {data.get('status')}"})

    # Check no empty trees have wrong status
    for tree in data.get("doneTreesThisWeek", []):
        if tree.get("status") != "done":
            errors.append({"item": f"doneTree.{tree.get('treeId')}", "reason": "status_not_done"})

    status = "pass" if len(errors) == 0 else "fail"
    return ADEResult(status=status,
        summary={"valid": len(errors) == 0, "total_checks": len(REQUIRED_INDEX_FIELDS), "errors": len(errors)},
        errors=errors, check_time=check_time)


# ── CLI ──

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ADE 周工作平面 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python -m runtime.cognition.weekly_plane create --week W32 --start-date 2026-08-03
          python -m runtime.cognition.weekly_plane migrate --from W31 --to W32
          python -m runtime.cognition.weekly_plane close --week W31
          python -m runtime.cognition.weekly_plane validate --week W31
        """),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create new weekly index")
    p_create.add_argument("--week", required=True, help="Week identifier (e.g. W32)")
    p_create.add_argument("--start-date", required=True, help="Week start date (YYYY-MM-DD)")
    p_create.add_argument("--previous-week", help="Previous week identifier for dependsOn")
    p_create.add_argument("--operating-root", default="docs/workflow/operating-records", help="Operating records root")
    p_create.add_argument("--sync", action="store_true", default=False, help="Execute writes (default: dry-run)")
    p_create.add_argument("--format", default="json", choices=["json", "text"])

    # migrate
    p_migrate = sub.add_parser("migrate", help="Migrate trees from old week to new week")
    p_migrate.add_argument("--from", dest="from_week", required=True, help="Source week (e.g. W31)")
    p_migrate.add_argument("--to", dest="to_week", required=True, help="Target week (e.g. W32)")
    p_migrate.add_argument("--operating-root", default="docs/workflow/operating-records", help="Operating records root")
    p_migrate.add_argument("--sync", action="store_true", default=False, help="Execute writes (default: dry-run)")
    p_migrate.add_argument("--format", default="json", choices=["json", "text"])

    # close
    p_close = sub.add_parser("close", help="Close current week")
    p_close.add_argument("--week", required=True, help="Week identifier (e.g. W31)")
    p_close.add_argument("--operating-root", default="docs/workflow/operating-records", help="Operating records root")
    p_close.add_argument("--sync", action="store_true", default=False, help="Execute writes (default: dry-run)")
    p_close.add_argument("--format", default="json", choices=["json", "text"])

    # validate
    p_val = sub.add_parser("validate", help="Validate weekly index")
    p_val.add_argument("--week", required=True, help="Week identifier (e.g. W31)")
    p_val.add_argument("--operating-root", default="docs/workflow/operating-records", help="Operating records root")
    p_val.add_argument("--format", default="json", choices=["json", "text"])

    args = parser.parse_args()
    op_root = Path(args.operating_root)

    # Smart default: if operating-root doesn't exist relative to CWD, check TriMetaverse sibling
    if not op_root.exists():
        alt = Path("..") / "TriMetaverse" / args.operating_root
        if alt.exists():
            op_root = alt

    dry_run = not getattr(args, "sync", False)

    if args.command == "create":
        result = create_weekly_plane(op_root, args.week, start_date=args.start_date,
            previous_week=getattr(args, "previous_week", None), dry_run=dry_run)
    elif args.command == "migrate":
        result = migrate_weekly_plane(op_root, args.from_week, args.to_week, dry_run=dry_run)
    elif args.command == "close":
        result = close_weekly_plane(op_root, args.week, dry_run=dry_run)
    elif args.command == "validate":
        result = validate_index(_index_path(op_root, args.week))
    else:
        parser.print_help()
        sys.exit(1)

    if args.format == "json":
        print(_json.dumps(result.to_ade_json(), indent=2, ensure_ascii=False))
    else:
        print(f"status={result.status}")
        print(f"summary={result.summary}")
        for c in result.changes:
            print(f"  + {c.get('action')}: {c.get('target', '')}")
        for e in result.errors:
            print(f"  ! {e.get('item')}: {e.get('reason')}")

    sys.exit(0 if result.status == "pass" else 1)


if __name__ == "__main__":
    main()
