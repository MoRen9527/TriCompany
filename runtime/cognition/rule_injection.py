"""rule_injection — TriCade Phase 3 experiment-to-production rule injection CLI.

ACT1: Rule injection pipeline for crystallizing experiment conclusions into
production governance artifacts.

CLI entry:
    python -m runtime.cognition.rule_injection check --scope {module}
    python -m runtime.cognition.rule_injection sync --scope {module}
    python -m runtime.cognition.rule_injection rollback --scope {module}

Injection targets (by scope):
    doc-governance    → TriCompany/docs/{domain}/{standard}.md
    ade-protocol      → .github/agents/*.agent.md
    employee-contract → TriCompany/source-agents/{role}/
    position-def      → .github/instructions/*.instructions.md
    project-template  → .github/prompts/*.prompt.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

EXPERIMENT_MARKER_RE = re.compile(
    r"<!--\s*experiment:\s*(\S+)\s+status:\s*(\S+)\s+since:\s*(\d{4}-\d{2}-\d{2})\s*-->"
)

EXPERIMENT_DIR = "docs/experiments"

BACKUP_DIR = ".rule-injection-backups"

# Mapping from scope to injection target directories
SCOPE_TARGET_MAP: dict[str, list[str]] = {
    "doc-governance": ["docs/"],
    "ade-protocol": [".github/agents/"],
    "employee-contract": ["source-agents/"],
    "position-def": [".github/instructions/"],
    "project-template": [".github/prompts/"],
}

SCOPE_FILE_PATTERNS: dict[str, list[str]] = {
    "doc-governance": ["**/*.md"],
    "ade-protocol": ["**/*.agent.md"],
    "employee-contract": ["**/*.agent.md", "**/*.instructions.md"],
    "position-def": ["**/*.instructions.md"],
    "project-template": ["**/*.prompt.md"],
}

# Extensions eligible for rule injection
ELIGIBLE_EXTENSIONS: tuple[str, ...] = (".md", ".json", ".yaml", ".yml")

DOC_NAMESPACE_MAP: dict[str, str] = {
    "doc-governance": "workflow",
    "ade-protocol": "workflow",
    "employee-contract": "workflow",
    "position-def": "workflow",
    "project-template": "workflow",
}


# ---------------------------------------------------------------------------
# data types
# ---------------------------------------------------------------------------

@dataclass
class ExperimentEntry:
    """Parsed experiment marker from a file header."""
    topic: str
    status: str
    since: str
    file_path: str


@dataclass
class RuleDiff:
    """A detected difference between source (experiment) and target (production)."""
    scope: str
    experiment_topic: str
    source_file: str
    target_file: str
    source_hash: str = ""
    target_hash: str = ""
    target_exists: bool = True
    diff_type: str = "unknown"  # new_rule | modified | missing_target
    description: str = ""


@dataclass
class InjectionResult:
    """Result of a single rule injection operation."""
    scope: str
    source_file: str
    target_file: str
    action: str = ""  # created | updated | skipped_identical | error
    source_hash: str = ""
    target_hash: str = ""
    error: str = ""
    backup_path: str = ""


@dataclass
class CheckReport:
    """Structured check output (ADE JSON format)."""
    check_time: str
    scope: str
    root: str
    diffs: list[RuleDiff] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=lambda: {
        "total": 0, "new_rules": 0, "modified": 0, "missing_targets": 0,
    })


@dataclass
class SyncReport:
    """Structured sync output (ADE JSON format)."""
    sync_time: str
    scope: str
    root: str
    results: list[InjectionResult] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=lambda: {
        "total": 0, "created": 0, "updated": 0, "skipped_identical": 0, "errors": 0,
    })


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_path(raw: str | Path) -> Path:
    return Path(raw).resolve()


def _file_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    h.update(file_path.read_bytes())
    return h.hexdigest()


def _find_experiment_files(root: Path) -> list[Path]:
    """Find all experiment summary documents."""
    exp_dir = root / EXPERIMENT_DIR
    if not exp_dir.is_dir():
        return []
    return sorted(exp_dir.rglob("*.md"))


def _parse_experiment_markers(root: Path, scope: str) -> list[ExperimentEntry]:
    """Scan all files in scope for experiment markers."""
    entries: list[ExperimentEntry] = []
    targets = SCOPE_TARGET_MAP.get(scope, [])
    if not targets:
        return entries

    for target_dir in targets:
        dir_path = root / target_dir
        if not dir_path.is_dir():
            continue
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in ELIGIBLE_EXTENSIONS:
                continue
            # Skip backup dir
            if BACKUP_DIR in file_path.parts:
                continue
            try:
                text = file_path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError):
                continue
            # Check first 10 lines for experiment markers
            lines = text.split("\n")[:10]
            for line in lines:
                m = EXPERIMENT_MARKER_RE.search(line)
                if m:
                    entries.append(ExperimentEntry(
                        topic=m.group(1),
                        status=m.group(2),
                        since=m.group(3),
                        file_path=str(file_path.relative_to(root).as_posix()),
                    ))
                    break
    return entries


def _load_json_safe(file_path: Path) -> dict[str, Any] | None:
    try:
        with open(file_path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

def _read_file_head(file_path: Path, lines: int = 10) -> str:
    """Read the first N lines of a file."""
    try:
        with open(file_path, "r", encoding="utf-8-sig") as fh:
            return "".join(fh.readline() for _ in range(lines))
    except (OSError, UnicodeDecodeError):
        return ""


def run_check(root: Path, scope: str) -> CheckReport:
    """Detect rule differences between experiment markers and target production files.

    For each file in the scope that carries an experiment marker with status
    'ready-for-injection', compare it against potential injection targets to
    identify new rules, modifications, or missing targets.
    """
    report = CheckReport(
        check_time=datetime.now(timezone.utc).isoformat(),
        scope=scope,
        root=root.as_posix(),
    )

    markers = _parse_experiment_markers(root, scope)

    for entry in markers:
        if entry.status != "ready-for-injection":
            continue

        source_file = root / entry.file_path
        if not source_file.is_file():
            report.diffs.append(RuleDiff(
                scope=scope,
                experiment_topic=entry.topic,
                source_file=entry.file_path,
                target_file="",
                target_exists=False,
                diff_type="missing_target",
                description=f"source file not found: {entry.file_path}",
            ))
            report.summary["missing_targets"] += 1
            report.summary["total"] += 1
            continue

        source_hash = _file_sha256(source_file)

        # Derive target file paths based on experiment topic
        exp_doc = root / EXPERIMENT_DIR / f"{entry.topic}.md"
        if exp_doc.is_file():
            exp_data = _load_json_safe(exp_doc)
            # Check if experiment doc defines explicit targets
            targets_text = _read_file_head(exp_doc, 50)

        # For the check phase, we compare the source file against itself
        # in the target namespace for hash differences — the actual target
        # mapping is resolved during sync based on experiment summary docs.
        # Here we flag:
        # 1. Files marked ready-for-injection with no matching target (new_rule)
        # 2. Files with hash differences vs last known injected state

        # Derive potential target path
        namespace = DOC_NAMESPACE_MAP.get(scope, "workflow")
        target_rel = f"docs/{namespace}/{Path(entry.file_path).name}"
        target_file = root / target_rel

        if not target_file.is_file():
            report.diffs.append(RuleDiff(
                scope=scope,
                experiment_topic=entry.topic,
                source_file=entry.file_path,
                target_file=target_rel,
                source_hash=source_hash[:16],
                target_hash="",
                target_exists=False,
                diff_type="new_rule",
                description=f"ready-for-injection rule has no matching target at {target_rel}",
            ))
            report.summary["new_rules"] += 1
            report.summary["total"] += 1
            continue

        target_hash = _file_sha256(target_file)
        if source_hash != target_hash:
            report.diffs.append(RuleDiff(
                scope=scope,
                experiment_topic=entry.topic,
                source_file=entry.file_path,
                target_file=target_rel,
                source_hash=source_hash[:16],
                target_hash=target_hash[:16],
                target_exists=True,
                diff_type="modified",
                description=f"hash mismatch: source={source_hash[:12]} target={target_hash[:12]}",
            ))
            report.summary["modified"] += 1
            report.summary["total"] += 1

    return report


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------

def run_sync(root: Path, scope: str, dry_run: bool = False) -> SyncReport:
    """Execute rule injection for files marked ready-for-injection.

    Creates backups before overwriting target files. In dry_run mode,
    only reports what would happen without making changes.
    """
    report = SyncReport(
        sync_time=datetime.now(timezone.utc).isoformat(),
        scope=scope,
        root=root.as_posix(),
    )

    markers = _parse_experiment_markers(root, scope)
    backup_root = root / BACKUP_DIR

    for entry in markers:
        if entry.status != "ready-for-injection":
            continue

        source_file = root / entry.file_path
        if not source_file.is_file():
            report.results.append(InjectionResult(
                scope=scope,
                source_file=entry.file_path,
                target_file="",
                action="error",
                error=f"source file not found: {entry.file_path}",
            ))
            report.summary["errors"] += 1
            report.summary["total"] += 1
            continue

        source_hash = _file_sha256(source_file)
        namespace = DOC_NAMESPACE_MAP.get(scope, "workflow")
        target_rel = f"docs/{namespace}/{Path(entry.file_path).name}"
        target_file = root / target_rel

        # Check if target already exists and has identical content
        if target_file.is_file():
            target_hash = _file_sha256(target_file)
            if source_hash == target_hash:
                report.results.append(InjectionResult(
                    scope=scope,
                    source_file=entry.file_path,
                    target_file=target_rel,
                    action="skipped_identical",
                    source_hash=source_hash[:16],
                    target_hash=target_hash[:16],
                ))
                report.summary["skipped_identical"] += 1
                report.summary["total"] += 1
                continue

        if dry_run:
            action = "created" if not target_file.is_file() else "updated"
            report.results.append(InjectionResult(
                scope=scope,
                source_file=entry.file_path,
                target_file=target_rel,
                action=f"would_{action}",
                source_hash=source_hash[:16],
                target_hash=target_file.is_file() and _file_sha256(target_file)[:16] or "",
            ))
            report.summary["total"] += 1
            continue

        # Execute injection: back up target if it exists, then copy source
        try:
            # Create backup
            if target_file.is_file():
                backup_path = backup_root / target_rel
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target_file, backup_path)

            # Ensure target directory exists
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy source to target
            shutil.copy2(source_file, target_file)

            target_hash = _file_sha256(target_file)
            action = "created" if not target_file.is_file() else "updated"
            # Re-check to avoid edge case
            was_existing = _file_sha256(backup_root / target_rel) if (backup_root / target_rel).is_file() else ""
            actual_action = "updated" if was_existing else "created"

            report.results.append(InjectionResult(
                scope=scope,
                source_file=entry.file_path,
                target_file=target_rel,
                action=actual_action,
                source_hash=source_hash[:16],
                target_hash=target_hash[:16],
                backup_path=str((backup_root / target_rel).relative_to(root).as_posix()) if (backup_root / target_rel).is_file() else "",
            ))
            if actual_action == "created":
                report.summary["created"] += 1
            else:
                report.summary["updated"] += 1
            report.summary["total"] += 1

        except OSError as exc:
            report.results.append(InjectionResult(
                scope=scope,
                source_file=entry.file_path,
                target_file=target_rel,
                action="error",
                error=f"injection_failed: {exc}",
            ))
            report.summary["errors"] += 1
            report.summary["total"] += 1

    return report


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------

def run_rollback(root: Path, scope: str) -> dict[str, Any]:
    """Rollback the last injection for a given scope.

    Restores files from .rule-injection-backups/ to their original locations.
    """
    backup_root = root / BACKUP_DIR
    if not backup_root.is_dir():
        return {"ok": False, "error": "no backups found", "scope": scope}

    restored: list[str] = []
    failed: list[str] = []

    namespace = DOC_NAMESPACE_MAP.get(scope, "workflow")
    scope_backup_dir = backup_root / "docs" / namespace
    if not scope_backup_dir.is_dir():
        return {"ok": False, "error": f"no backups for scope '{scope}'", "scope": scope}

    for backup_file in scope_backup_dir.rglob("*"):
        if not backup_file.is_file():
            continue
        try:
            rel = backup_file.relative_to(backup_root).as_posix()
        except ValueError:
            continue
        target_file = root / rel
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, target_file)
            restored.append(rel)
        except OSError as exc:
            failed.append(f"{rel}: {exc}")

    return {
        "ok": True,
        "rollback_time": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "root": root.as_posix(),
        "restored": restored,
        "failed": failed,
        "summary": {
            "total": len(restored) + len(failed),
            "restored": len(restored),
            "failed_count": len(failed),
        },
    }


# ---------------------------------------------------------------------------
# serialization
# ---------------------------------------------------------------------------

def _serialize_check_report(report: CheckReport) -> dict[str, Any]:
    return {
        "check_time": report.check_time,
        "scope": report.scope,
        "root": report.root,
        "diffs": [
            {
                "scope": d.scope,
                "experiment_topic": d.experiment_topic,
                "source_file": d.source_file,
                "target_file": d.target_file,
                "source_hash": d.source_hash,
                "target_hash": d.target_hash,
                "target_exists": d.target_exists,
                "diff_type": d.diff_type,
                "description": d.description,
            }
            for d in report.diffs
        ],
        "summary": report.summary,
    }


def _serialize_sync_report(report: SyncReport) -> dict[str, Any]:
    return {
        "sync_time": report.sync_time,
        "scope": report.scope,
        "root": report.root,
        "results": [
            {
                "scope": r.scope,
                "source_file": r.source_file,
                "target_file": r.target_file,
                "action": r.action,
                "source_hash": r.source_hash,
                "target_hash": r.target_hash,
                "error": r.error,
                "backup_path": r.backup_path,
            }
            for r in report.results
        ],
        "summary": report.summary,
    }


def _print_check_summary(report: CheckReport) -> None:
    lines = [
        "",
        "=" * 60,
        f"  Rule Injection Check — scope: {report.scope}",
        "=" * 60,
        f"  Total diffs:       {report.summary['total']}",
        f"  New rules:         {report.summary['new_rules']}",
        f"  Modified:          {report.summary['modified']}",
        f"  Missing targets:   {report.summary['missing_targets']}",
        "-" * 60,
    ]
    for d in report.diffs:
        icon = {
            "new_rule": "[NEW]",
            "modified": "[MODIFIED]",
            "missing_target": "[MISSING]",
        }.get(d.diff_type, "[?]")
        lines.append(f"  {icon} {d.source_file} → {d.target_file or '(no target)'}")
        if d.description:
            lines.append(f"      {d.description}")
    lines.append("=" * 60)
    lines.append("")
    print("\n".join(lines), file=sys.stderr)


def _print_sync_summary(report: SyncReport) -> None:
    lines = [
        "",
        "=" * 60,
        f"  Rule Injection Sync — scope: {report.scope}",
        "=" * 60,
        f"  Created:           {report.summary['created']}",
        f"  Updated:           {report.summary['updated']}",
        f"  Skipped (same):    {report.summary['skipped_identical']}",
        f"  Errors:            {report.summary['errors']}",
        "-" * 60,
    ]
    for r in report.results:
        icon = {
            "created": "[CREATED]",
            "updated": "[UPDATED]",
            "skipped_identical": "[SKIPPED]",
            "error": "[ERROR]",
        }.get(r.action, "[?]")
        lines.append(f"  {icon} {r.source_file} → {r.target_file}")
        if r.error:
            lines.append(f"      error: {r.error}")
        if r.backup_path:
            lines.append(f"      backup: {r.backup_path}")
    lines.append("=" * 60)
    lines.append("")
    print("\n".join(lines), file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rule_injection",
        description="TriCade Phase 3 rule injection pipeline — crystallize experiment conclusions into production governance artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check
    check_parser = subparsers.add_parser("check", help="Detect rule differences between experiments and production targets.")
    check_parser.add_argument("--scope", required=True, help="Injection scope (doc-governance | ade-protocol | employee-contract | position-def | project-template)")
    check_parser.add_argument("--root", default=".", help="TriCompany root directory (default: current directory).")
    check_parser.add_argument("--format", choices=("json",), default="json", help="Output format.")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Execute rule injection for ready-for-injection files.")
    sync_parser.add_argument("--scope", required=True, help="Injection scope.")
    sync_parser.add_argument("--root", default=".", help="TriCompany root directory.")
    sync_parser.add_argument("--dry-run", action="store_true", default=False, help="Preview without writing files.")
    sync_parser.add_argument("--format", choices=("json",), default="json", help="Output format.")

    # rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback the last injection for a scope.")
    rollback_parser.add_argument("--scope", required=True, help="Injection scope.")
    rollback_parser.add_argument("--root", default=".", help="TriCompany root directory.")
    rollback_parser.add_argument("--format", choices=("json",), default="json", help="Output format.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    root = _normalize_path(args.root)
    scope = args.scope

    if scope not in SCOPE_TARGET_MAP:
        print(
            f"error: unknown scope '{scope}'. Valid scopes: {', '.join(sorted(SCOPE_TARGET_MAP.keys()))}",
            file=sys.stderr,
        )
        return 1

    if args.command == "check":
        report = run_check(root, scope)
        _print_check_summary(report)
        json.dump(_serialize_check_report(report), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    elif args.command == "sync":
        report = run_sync(root, scope, dry_run=args.dry_run)
        _print_sync_summary(report)
        json.dump(_serialize_sync_report(report), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    elif args.command == "rollback":
        result = run_rollback(root, scope)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0 if result.get("ok") else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
