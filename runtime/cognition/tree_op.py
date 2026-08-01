"""tree_op — ADE Tree 操作 CLI

标准化执行树的创建和验证。
Agent 规划 → CLI 确定性执行 → ADE JSON 自检 → Agent 收口。

用法:
  python -m runtime.cognition.tree_op create --tree-id X --title "..." --parent-week W31 --priority P0 --nodes '[...]'
  python -m runtime.cognition.tree_op validate --tree-id X
"""

from __future__ import annotations

import argparse
import json as _json
import re
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ── constants ──

VALID_TREE_STATUSES = {"active", "done", "escalated"}
VALID_NODE_STATUSES = {"pending", "in_progress", "done", "escalated"}
VALID_AGENTS = {
    "CEOChiefOfStaff", "ChiefProductOfficer", "ChiefTechnologyOfficer",
    "ChiefHumanResourcesOfficer", "ChiefAdministrativeOfficer",
    "ChiefMarketingOfficer", "ChiefOperatingOfficer", "ChiefFinancialOfficer",
    "FullStackDeveloper", "TestEngineer", "RAndDTrainer",
    "CustomerSuccessOfficer", "DeploymentEngineer",
    "BusinessStrategy", "CompanyGovernanceRegistry",
    "TriMetaverseBusinessStrategyRegistry", "TriMetaverseProductRegistry", "TriMetaverseCodeRegistry",
}

REQUIRED_TREE_FIELDS = [
    "nodes", "objectType", "objectId", "title", "ownerRole",
    "treeId", "status", "priority", "summary",
    "metadata", "createdAt", "relatedModules", "updatedAt",
    "parentWeekPlan",
]

REQUIRED_NODE_FIELDS = ["nodeId", "agent", "status", "action"]

# ── ADE types ──

@dataclass
class ADEResult:
    status: str
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


def _tree_dir(operating_root: Path, week_str: str, tree_id: str) -> Path:
    return operating_root / f"trees/{tree_id}"


def _tree_path(operating_root: Path, week_str: str, tree_id: str) -> Path:
    return _tree_dir(operating_root, week_str, tree_id) / "tree-op.json"


# ── create ──

def create_tree_op(
    operating_root: Path,
    tree_id: str,
    *,
    title: str,
    parent_week: str,
    owner_role: str = "CEOChiefOfStaff",
    priority: str = "P0",
    summary: str = "",
    object_id: str | None = None,
    nodes: list[dict] | None = None,
    dry_run: bool = True,
) -> ADEResult:
    """Create a new tree-op.json."""
    check_time = _check_time()
    errors: list[dict] = []

    # Validate tree_id
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,63}$", tree_id):
        errors.append({"item": "tree_id", "reason": f"invalid format: {tree_id}"})
        return ADEResult(status="fail", summary={"created": False, "errors": 1},
            errors=errors, check_time=check_time)

    # Validate parent_week
    if not re.match(r"^W\d{2}$", parent_week):
        errors.append({"item": "parent_week", "reason": f"invalid week format: {parent_week}"})
        return ADEResult(status="fail", summary={"created": False, "errors": 1},
            errors=errors, check_time=check_time)

    # Validate priority
    if priority not in ("P0", "P1", "P2"):
        errors.append({"item": "priority", "reason": f"invalid: {priority}"})
        return ADEResult(status="fail", summary={"created": False, "errors": 1},
            errors=errors, check_time=check_time)

    # Determine paths
    week_num = int(parent_week[1:])
    year = datetime.now(timezone.utc).year
    week_dir = operating_root / f"{year}-{parent_week}"
    tree_dir = week_dir / "trees" / tree_id
    tree_path = tree_dir / "tree-op.json"

    if tree_path.exists():
        errors.append({"item": str(tree_path), "reason": "already_exists"})
        return ADEResult(status="fail", summary={"created": False, "errors": 1},
            errors=errors, check_time=check_time)

    if object_id is None:
        object_id = f"TREE-OP-{tree_id}"

    # Default root node
    if nodes is None:
        nodes = [{
            "nodeId": f"{tree_id}-0",
            "agent": "CEOChiefOfStaff",
            "status": "done",
            "action": f"启动路由：{title}",
            "next_agent": None,
        }]

    # Validate all nodes
    node_ids = set()
    for i, node in enumerate(nodes):
        for field in REQUIRED_NODE_FIELDS:
            if field not in node:
                errors.append({"item": f"node[{i}].{field}", "reason": "missing_required_field"})
        if node.get("status") not in VALID_NODE_STATUSES:
            errors.append({"item": f"node[{i}].status", "reason": f"invalid: {node.get('status')}"})
        if node.get("agent") not in VALID_AGENTS:
            errors.append({"item": f"node[{i}].agent", "reason": f"unknown agent: {node.get('agent')}"})
        node_ids.add(node.get("nodeId", ""))

    # Validate dependsOn references
    for i, node in enumerate(nodes):
        for dep in node.get("dependsOn", []):
            if dep not in node_ids:
                errors.append({"item": f"node[{i}].dependsOn", "reason": f"references unknown node: {dep}"})

    if errors:
        return ADEResult(status="fail", summary={"created": False, "errors": len(errors)},
            errors=errors, check_time=check_time)

    tree_op = {
        "nodes": nodes,
        "relatedDocuments": [],
        "objectType": "TREE_OPERATING_PLAN",
        "parentWeekPlan": f"OP-{year}{week_num:02d}-{parent_week}-001",
        "objectId": object_id,
        "title": title,
        "ownerRole": owner_role,
        "treeId": tree_id,
        "status": "active",
        "priority": priority,
        "summary": summary or title,
        "metadata": {
            "updatedBy": owner_role,
            "lastUpdated": check_time,
            "version": "1.0.0",
            "note": f"v1.0.0: 开树。根节点 {tree_id}-0 done。",
        },
        "createdAt": check_time,
        "relatedModules": ["TriMetaverse", "TriCompany"],
        "updatedAt": check_time,
    }

    if dry_run:
        return ADEResult(status="pass",
            summary={"created": False, "dry_run": True, "tree_id": tree_id, "path": str(tree_path)},
            changes=[{"action": "would_create", "target": str(tree_path)}],
            check_time=check_time)

    _save_json(tree_path, tree_op)
    return ADEResult(status="pass",
        summary={"created": True, "tree_id": tree_id, "nodes": len(nodes)},
        changes=[{"action": "created", "target": str(tree_path), "nodes": len(nodes)}],
        check_time=check_time)


# ── validate ──

def validate_tree_op(tree_path: Path) -> ADEResult:
    """Validate a tree-op.json for protocol compliance."""
    check_time = _check_time()
    errors: list[dict] = []

    data = _load_json(tree_path)
    if not data:
        return ADEResult(status="fail", summary={"valid": False},
            errors=[{"item": str(tree_path), "reason": "invalid_json_or_missing"}],
            check_time=check_time)

    # Required tree fields
    for field in REQUIRED_TREE_FIELDS:
        if field not in data:
            errors.append({"item": field, "reason": "missing_required_field"})

    # Tree status
    if data.get("status") not in VALID_TREE_STATUSES:
        errors.append({"item": "status", "reason": f"invalid tree status: {data.get('status')}"})

    # objectType
    if data.get("objectType") != "TREE_OPERATING_PLAN":
        errors.append({"item": "objectType", "reason": "expected TREE_OPERATING_PLAN"})

    # Validate nodes
    nodes = data.get("nodes", [])
    if not nodes:
        errors.append({"item": "nodes", "reason": "empty_node_list"})
    else:
        node_ids = set()
        for i, node in enumerate(nodes):
            for field in REQUIRED_NODE_FIELDS:
                if field not in node:
                    errors.append({"item": f"node[{i}].{field}", "reason": "missing_required_field"})
            # Status
            if node.get("status") not in VALID_NODE_STATUSES:
                errors.append({"item": f"node[{i}].status", "reason": f"invalid: {node.get('status')}"})
            # Agent
            if node.get("agent") not in VALID_AGENTS:
                errors.append({"item": f"node[{i}].agent", "reason": f"unknown: {node.get('agent')}"})
            node_ids.add(node.get("nodeId", ""))

        # dependsOn references
        for i, node in enumerate(nodes):
            for dep in node.get("dependsOn", []):
                if dep not in node_ids:
                    errors.append({"item": f"node[{i}].dependsOn.{dep}", "reason": "references_unknown_node"})

        # Check no duplicate nodeIds
        if len(node_ids) != len(nodes):
            errors.append({"item": "nodes", "reason": f"duplicate nodeIds: {len(nodes)} nodes but {len(node_ids)} unique"})

    status = "pass" if len(errors) == 0 else "fail"
    return ADEResult(status=status,
        summary={"valid": len(errors) == 0, "nodes": len(nodes), "errors": len(errors)},
        errors=errors, check_time=check_time)


# ── CLI ──

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ADE Tree 操作 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python -m runtime.cognition.tree_op create --tree-id my-task --title "My Task" --parent-week W31 --priority P0
          python -m runtime.cognition.tree_op validate --tree-id my-task
        """),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create new tree-op.json")
    p_create.add_argument("--tree-id", required=True, help="Tree identifier (kebab-case)")
    p_create.add_argument("--title", required=True, help="Tree title")
    p_create.add_argument("--parent-week", required=True, help="Parent week (e.g. W31)")
    p_create.add_argument("--priority", default="P0", choices=["P0", "P1", "P2"])
    p_create.add_argument("--owner", default="CEOChiefOfStaff", help="Owner role")
    p_create.add_argument("--summary", default="", help="Tree summary")
    p_create.add_argument("--nodes", default=None, help="JSON array of nodes (inline or @filepath)")
    p_create.add_argument("--operating-root", default="docs/workflow/operating-records", help="Operating records root")
    p_create.add_argument("--sync", action="store_true", default=False, help="Execute writes (default: dry-run)")
    p_create.add_argument("--format", default="json", choices=["json", "text"])

    # validate
    p_val = sub.add_parser("validate", help="Validate tree-op.json")
    p_val.add_argument("--tree-id", required=True, help="Tree identifier")
    p_val.add_argument("--week", default="W31", help="Week for path resolution")
    p_val.add_argument("--operating-root", default="docs/workflow/operating-records", help="Operating records root")
    p_val.add_argument("--format", default="json", choices=["json", "text"])

    args = parser.parse_args()
    op_root = Path(args.operating_root)
    # Smart default: check TriMetaverse sibling if not found relative to CWD
    if not op_root.exists():
        alt = Path("..") / "TriMetaverse" / args.operating_root
        if alt.exists():
            op_root = alt

    if args.command == "create":
        # Parse nodes if provided
        nodes = None
        if args.nodes:
            raw = args.nodes.strip()
            if raw.startswith("@"):
                # Read from file
                nodes_path = Path(raw[1:])
                if nodes_path.exists():
                    nodes = _load_json(nodes_path)
                else:
                    print(_json.dumps({"status": "fail", "errors": [{"item": raw, "reason": "node_file_not_found"}]}))
                    sys.exit(1)
            else:
                nodes = _json.loads(raw)

        result = create_tree_op(
            op_root, args.tree_id,
            title=args.title, parent_week=args.parent_week,
            owner_role=args.owner, priority=args.priority,
            summary=args.summary, nodes=nodes,
            dry_run=not args.sync,
        )
    elif args.command == "validate":
        tree_path = _tree_path(op_root, args.week, args.tree_id)
        if not tree_path.exists():
            # Try without week subdirectory
            alt = op_root / f"trees/{args.tree_id}/tree-op.json"
            if alt.exists():
                tree_path = alt
            else:
                result = ADEResult(status="fail",
                    summary={"valid": False, "errors": 1},
                    errors=[{"item": str(tree_path), "reason": "tree_not_found"}])
                print(_json.dumps(result.to_ade_json(), indent=2, ensure_ascii=False))
                sys.exit(1)
                return  # unreachable
        result = validate_tree_op(tree_path)
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
