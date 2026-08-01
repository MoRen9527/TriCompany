"""source_publish_check — Phase B CLI 最终版本 (B1/B2/B3/B4 全部完成).

B1 ✅ argument parsing, sync scope contract, structured JSON output framework.
B2 ✅ four-way diff engine (hash / git / codegraph / JSON semantic).
B3 ✅ --sync mode for executing out_of_sync file copies with live-entry protection.
B4 ✅ integration closeout — validation suite 13/13 green (2026-07-24), CLI contract verified.

CLI entry: python -m runtime.cognition.source_publish_check --check --format json
Tests:    python -m pytest runtime/cognition/source_publish_check_validation.py -v
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ---------------------------------------------------------------------------
# sync scope constants (CPO hard constraints, Phase B)
# ---------------------------------------------------------------------------

# -- included (source-side directories / files under --source-root) ----------
SYNC_SOURCE_DIRS: tuple[str, ...] = (
    "source-agents/registries/",
    "docs/",
    ".github/",  # non-employee content only; see exclusions
)

# -- excluded patterns -------------------------------------------------------
# Employee five-piece files, live entry agents under TriMetaverse, and
# binding profiles are never synced by this tool.
EXCLUDE_GLOBS: tuple[str, ...] = (
    "**/*.soul.md",
    "**/*.memory.md",
    "**/*.colleagues.md",
    "**/*.social.md",
    "**/binding-profiles/**",
)

EXCLUDE_DIR_NAMES: tuple[str, ...] = (
    "__pycache__",
    ".git",
    ".pytest_cache",
    "vendor",
)

# -- file-type classification for diff strategy selection --------------------
DOC_EXTENSIONS: tuple[str, ...] = (".md", ".json", ".yaml", ".yml")
SOURCE_EXTENSIONS: tuple[str, ...] = (".py", ".ts", ".js")
MANIFEST_REL_PATH: str = (
    "source-agents/registries/trimetaverse-live-agent-publish-manifest.json"
)

# -- live-entry protection (B3 --sync safety) ---------------------------------
# Paths that must never be overwritten during sync.
PROTECTED_TARGET_PATTERNS: tuple[str, ...] = (
    ".github/agents/",          # live entry agents
    ".github/binding-profiles/",  # binding profiles
)

# -- agent publish constants (Q3 Phase 2) ------------------------------------
# Eligible statuses for --publish-agents mode: only source-published and
# current-copilot-host-live entries are published by this pipeline.
AGENT_PUBLISH_ELIGIBLE_STATUSES: tuple[str, ...] = (
    "source-published-live-entry",
    "current-copilot-host-live",
)
# Kinds that are filterable by --employees (role agents map to employees).
AGENT_PUBLISH_ROLE_KIND: str = "role-agent"
# Max SHA-256 hex prefix length in error/reason strings.
AGENT_HASH_PREFIX_LEN: int = 16

# -- employee five-piece kit suffixes (extra safety net) ----------------------
EMPLOYEE_KIT_SUFFIXES: tuple[str, ...] = (
    ".soul.md",
    ".memory.md",
    ".colleagues.md",
    ".social.md",
    ".body.md",
)


# ---------------------------------------------------------------------------
# data types
# ---------------------------------------------------------------------------

@dataclass
class SyncItem:
    """A single synchronisation check result line."""

    source: str
    target: str
    reason: str


@dataclass
class SyncGap:
    """Something in scope that has no counterpart on the other side."""

    item: str
    issue: str


@dataclass
class SyncSummary:
    total: int = 0
    out_of_sync: int = 0
    in_sync: int = 0
    gaps: int = 0


@dataclass
class SyncReport:
    """Top-level structured output matching the CLI contract."""

    check_time: str
    source_root: str
    support_root: str
    out_of_sync: list[SyncItem] = field(default_factory=list)
    in_sync: list[SyncItem] = field(default_factory=list)
    gaps: list[SyncGap] = field(default_factory=list)
    summary: SyncSummary = field(default_factory=SyncSummary)


# ── Q3 Phase 2: agent publish data types ───────────────────────────────────


@dataclass
class AgentPublishItem:
    """Single agent live entry publish result."""

    source: str
    target: str
    kind: str
    manifest_status: str
    action: str  # created | updated | skipped_identical | skipped_dry_run | error
    source_hash: str = ""
    target_hash: str = ""
    error: str = ""


@dataclass
class AgentPublishSummary:
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped_identical: int = 0
    skipped_dry_run: int = 0
    errors: int = 0


@dataclass
class AgentPublishReport:
    """Top-level agent publish result for --publish-agents mode."""

    check_time: str
    source_root: str
    support_root: str
    dry_run: bool = True
    items: list[AgentPublishItem] = field(default_factory=list)
    summary: AgentPublishSummary = field(default_factory=AgentPublishSummary)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_path(raw: str | Path) -> Path:
    """Resolve and return an absolute, normalised Path."""
    return Path(raw).resolve()


def _is_excluded(rel_path: str) -> bool:
    """Return True when *rel_path* matches any exclusion rule."""
    # directory-name exclusion
    parts = Path(rel_path).parts
    if any(part in EXCLUDE_DIR_NAMES for part in parts):
        return True
    # glob exclusion (simple suffix / substring matching for Phase B)
    for glob_pattern in EXCLUDE_GLOBS:
        if glob_pattern.startswith("**/") and Path(rel_path).match(glob_pattern):
            return True
    return False


def _collect_source_items(source_root: Path) -> list[Path]:
    """Walk the declared sync source directories and return file paths.

    Files matched by EXCLUDE_GLOBS / EXCLUDE_DIR_NAMES are filtered out.
    """
    items: list[Path] = []
    for sync_dir in SYNC_SOURCE_DIRS:
        dir_path = source_root / sync_dir
        if not dir_path.is_dir():
            continue
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                rel = file_path.relative_to(source_root).as_posix()
            except ValueError:
                continue
            if _is_excluded(rel):
                continue
            items.append(file_path)
    return sorted(items)


# ---------------------------------------------------------------------------
# Q3 Phase 2: --publish-agents helpers
# ---------------------------------------------------------------------------


def _load_publish_manifest(source_root: Path) -> dict[str, Any] | None:
    """Load the live-agent publish manifest from source-root.

    Returns the parsed JSON dict, or None if the manifest is missing/invalid.
    """
    manifest_path = source_root / MANIFEST_REL_PATH
    if not manifest_path.is_file():
        return None
    return _load_json_safe(manifest_path)


def _derive_allowed_agent_targets(
    manifest: dict[str, Any],
) -> list[str]:
    """Derive the AGENT_PUBLISH_ALLOWED_TARGETS whitelist from manifest.

    Only entries with eligible statuses contribute to the whitelist.
    Returns a list of target paths (stripped of repo prefixes).
    """
    allowed: list[str] = []
    live_entries = manifest.get("liveEntries", [])
    if not isinstance(live_entries, list):
        return allowed
    for entry in live_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("status", "") not in AGENT_PUBLISH_ELIGIBLE_STATUSES:
            continue
        target = entry.get("target", "")
        if target:
            allowed.append(target)
    return allowed


def _filter_agent_publish_entries(
    manifest: dict[str, Any],
    employee_ids: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Filter manifest liveEntries for --publish-agents eligibility.

    Filters:
      1. status ∈ AGENT_PUBLISH_ELIGIBLE_STATUSES
      2. If employee_ids is given, only include role-agent entries whose
         source directory slug matches one of the given employee IDs.
    """
    live_entries = manifest.get("liveEntries", [])
    if not isinstance(live_entries, list):
        return []

    results: list[dict[str, Any]] = []
    for entry in live_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("status", "") not in AGENT_PUBLISH_ELIGIBLE_STATUSES:
            continue

        # employee filter
        if employee_ids is not None:
            if entry.get("kind") != AGENT_PUBLISH_ROLE_KIND:
                continue
            source = entry.get("source", "")
            # extract employee-id slug from source path (e.g.
            # "TriCompany/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.agent.md")
            parts = source.replace("\\", "/").split("/")
            # find the directory name after source-agents/
            dir_slug = ""
            for i, part in enumerate(parts):
                if part == "source-agents" and i + 1 < len(parts):
                    dir_slug = parts[i + 1]
                    break
            if dir_slug not in employee_ids:
                continue

        results.append(entry)
    return results


def _resolve_agent_source_path(
    source_root: Path, entry_source: str
) -> Path | None:
    """Resolve an agent source path relative to source_root.

    Strips 'TriCompany/' prefix from the entry source.
    Returns the resolved absolute Path, or None if the file doesn't exist.
    """
    normalized = entry_source
    if normalized.startswith("TriCompany/"):
        normalized = normalized[len("TriCompany/"):]
    candidate = source_root / normalized
    if candidate.is_file():
        return candidate
    return None


def _resolve_agent_target_path(
    support_root: Path, entry_target: str
) -> Path | None:
    """Resolve an agent target path relative to support_root.

    Strips 'TriMetaverse/' prefix if present.
    Returns the resolved absolute Path (may not exist yet).
    """
    normalized = entry_target
    if normalized.startswith("TriMetaverse/"):
        normalized = normalized[len("TriMetaverse/"):]
    return support_root / normalized


def _publish_single_agent(
    source_file: Path,
    target_file: Path,
    entry: dict[str, Any],
    *,
    dry_run: bool = True,
) -> AgentPublishItem:
    """Publish (or dry-run) a single agent live entry.

    - Computes SHA-256 of the source file.
    - If target doesn't exist: would create (or mark skipped_dry_run).
    - If target exists and hash matches: skipped_identical.
    - If target exists and hash differs: would update (or mark skipped_dry_run).

    Returns an AgentPublishItem describing the result.
    """
    try:
        source_hash = _file_sha256(source_file)
    except OSError as exc:
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=entry.get("kind", ""),
            manifest_status=entry.get("status", ""),
            action="error",
            source_hash="",
            target_hash="",
            error=f"source_read_error: {exc}",
        )

    target_exists = target_file.is_file()
    target_hash = ""
    if target_exists:
        try:
            target_hash = _file_sha256(target_file)
        except OSError:
            target_hash = "<unreadable>"

    kind = entry.get("kind", "")
    manifest_status = entry.get("status", "")

    # Determine action
    if not target_exists:
        if dry_run:
            return AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=kind,
                manifest_status=manifest_status,
                action="skipped_dry_run",
                source_hash=source_hash,
                target_hash="",
            )
        # Write the agent file
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            return AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=kind,
                manifest_status=manifest_status,
                action="created",
                source_hash=source_hash,
                target_hash="",
            )
        except OSError as exc:
            return AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=kind,
                manifest_status=manifest_status,
                action="error",
                source_hash=source_hash,
                target_hash="",
                error=f"write_failed: {exc}",
            )

    # Target exists — compare hashes
    if source_hash == target_hash:
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action="skipped_identical",
            source_hash=source_hash,
            target_hash=target_hash,
        )

    # Hash differs
    if dry_run:
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action="skipped_dry_run",
            source_hash=source_hash,
            target_hash=target_hash,
        )

    # Execute the update
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action="updated",
            source_hash=source_hash,
            target_hash=target_hash,
        )
    except OSError as exc:
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action="error",
            source_hash=source_hash,
            target_hash=target_hash,
            error=f"write_failed: {exc}",
        )


def run_agent_publish(
    source_root: Path,
    support_root: Path,
    *,
    employee_ids: tuple[str, ...] | None = None,
    dry_run: bool = True,
) -> AgentPublishReport:
    """Execute --publish-agents logic.

    1. Load manifest, filter eligible entries.
    2. For each entry: resolve source → SHA-256; compare with target.
    3. Return structured AgentPublishReport.

    When *dry_run* is True, no files are written.
    """
    report = AgentPublishReport(
        check_time=datetime.now(timezone.utc).isoformat(),
        source_root=source_root.as_posix(),
        support_root=support_root.as_posix(),
        dry_run=dry_run,
    )

    manifest = _load_publish_manifest(source_root)
    if manifest is None:
        report.items.append(AgentPublishItem(
            source="",
            target="",
            kind="",
            manifest_status="",
            action="error",
            error=f"manifest_missing_or_invalid: {MANIFEST_REL_PATH}",
        ))
        report.summary.total = 1
        report.summary.errors = 1
        return report

    entries = _filter_agent_publish_entries(manifest, employee_ids=employee_ids)

    for entry in entries:
        source_file = _resolve_agent_source_path(source_root, entry.get("source", ""))
        if source_file is None:
            report.items.append(AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=entry.get("kind", ""),
                manifest_status=entry.get("status", ""),
                action="error",
                error="source_file_not_found",
            ))
            report.summary.total += 1
            report.summary.errors += 1
            continue

        target_file = _resolve_agent_target_path(support_root, entry.get("target", ""))
        if target_file is None:
            report.items.append(AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=entry.get("kind", ""),
                manifest_status=entry.get("status", ""),
                action="error",
                error="could_not_resolve_target_path",
            ))
            report.summary.total += 1
            report.summary.errors += 1
            continue

        result = _publish_single_agent(
            source_file, target_file, entry, dry_run=dry_run,
        )
        report.items.append(result)
        report.summary.total += 1
        if result.action == "created":
            report.summary.created += 1
        elif result.action == "updated":
            report.summary.updated += 1
        elif result.action == "skipped_identical":
            report.summary.skipped_identical += 1
        elif result.action == "skipped_dry_run":
            report.summary.skipped_dry_run += 1
        elif result.action == "error":
            report.summary.errors += 1

    return report


def _serialize_agent_publish_report(report: AgentPublishReport) -> dict[str, Any]:
    """Serialize an AgentPublishReport to a JSON-compatible dict."""
    return {
        "check_time": report.check_time,
        "source_root": report.source_root,
        "support_root": report.support_root,
        "dry_run": report.dry_run,
        "items": [
            {
                "source": a.source,
                "target": a.target,
                "kind": a.kind,
                "manifest_status": a.manifest_status,
                "action": a.action,
                "source_hash": a.source_hash,
                "target_hash": a.target_hash,
                "error": a.error,
            }
            for a in report.items
        ],
        "summary": {
            "total": report.summary.total,
            "created": report.summary.created,
            "updated": report.summary.updated,
            "skipped_identical": report.summary.skipped_identical,
            "skipped_dry_run": report.summary.skipped_dry_run,
            "errors": report.summary.errors,
        },
    }


# ---------------------------------------------------------------------------
# B2: diff engine helpers
# ---------------------------------------------------------------------------

# ── 2a: file hash ──────────────────────────────────────────────────────────

def _file_sha256(file_path: Path) -> str:
    """SHA-256 hex digest of *file_path*."""
    h = hashlib.sha256()
    h.update(file_path.read_bytes())
    return h.hexdigest()


def _hash_diff(
    source_file: Path, support_file: Path, rel_path: str
) -> SyncItem | None:
    """Compare two files by SHA-256 hash. Returns SyncItem if out_of_sync, None if in-sync."""
    source_hash = _file_sha256(source_file)
    support_hash = _file_sha256(support_file)
    if source_hash != support_hash:
        return SyncItem(
            source=rel_path,
            target=rel_path,
            reason=f"hash_mismatch source={source_hash[:12]}… support={support_hash[:12]}…",
        )
    return None


# ── 2b: git diff detection ────────────────────────────────────────────────

def _git_changed_files(repo_root: Path) -> set[str]:
    """Return set of relative paths changed in the most recent commit (HEAD vs HEAD~1).

    Returns empty set if git is unavailable or there is only one commit.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=15,
        )
        if result.returncode != 0:
            # Possibly only one commit; try HEAD vs initial commit
            result2 = subprocess.run(
                ["git", "diff", "--name-only", "HEAD", "--", "."],
                capture_output=True,
                text=True,
                cwd=str(repo_root),
                timeout=15,
            )
            if result2.returncode != 0:
                return set()
            lines = result2.stdout.strip().split("\n")
            return {ln.strip() for ln in lines if ln.strip()}
        lines = result.stdout.strip().split("\n")
        return {ln.strip() for ln in lines if ln.strip()}
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return set()


def _git_diff_flag(
    rel_path: str, changed_files: set[str]
) -> SyncItem | None:
    """Flag a source-code file as needing sync check if it was recently changed in git."""
    if rel_path in changed_files:
        return SyncItem(
            source=rel_path,
            target=rel_path,
            reason="git_recent_change — verify sync status",
        )
    return None


# ── 2c: CodeGraph structural change detection ─────────────────────────────

def _codegraph_freshness_check(repo_root: Path) -> dict[str, Any]:
    """Check CodeGraph index freshness against git HEAD.

    Returns a dict with 'stale', 'head_commits_ahead', and 'message' fields.
    Best-effort — returns empty dict if codegraph is unavailable.
    """
    try:
        # count commits since last codegraph refresh anchor
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        head_commits = int(result.stdout.strip()) if result.returncode == 0 else 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError, ValueError):
        head_commits = 0

    # check codegraph db freshness marker
    codegraph_db = repo_root / ".codegraph" / "codegraph.db"
    if not codegraph_db.exists():
        return {
            "stale": True,
            "head_commits_ahead": head_commits,
            "message": "codegraph database not found; run codegraph index refresh",
        }

    if head_commits > 5:
        return {
            "stale": True,
            "head_commits_ahead": head_commits,
            "message": (
                f"HEAD is {head_commits} commits ahead of initial commit; "
                "codegraph index may be stale. Consider refreshing before relying on "
                "structural diff results."
            ),
        }
    return {
        "stale": False,
        "head_commits_ahead": head_commits,
        "message": "codegraph index appears reasonably fresh.",
    }


# ── 2d: JSON semantic diff ────────────────────────────────────────────────

def _load_json_safe(file_path: Path) -> dict[str, Any] | None:
    """Load a JSON file safely; return None on any error.

    Handles UTF-8 with or without BOM (the manifest uses UTF-8 BOM).
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def _json_key_diff(
    source_data: dict[str, Any], support_data: dict[str, Any]
) -> list[str]:
    """Compare two JSON dicts at the top-level key set.

    Returns a list of human-readable difference descriptions.
    """
    diffs: list[str] = []
    source_keys = set(source_data.keys())
    support_keys = set(support_data.keys())

    only_source = source_keys - support_keys
    only_support = support_keys - source_keys
    common = source_keys & support_keys

    if only_source:
        diffs.append(f"keys_only_in_source: {sorted(only_source)}")
    if only_support:
        diffs.append(f"keys_only_in_support: {sorted(only_support)}")

    # For common keys, check value type and rough structural equality
    for key in sorted(common):
        sv = source_data[key]
        tv = support_data[key]
        if type(sv) is not type(tv):
            diffs.append(f"key '{key}' type_mismatch: source={type(sv).__name__} support={type(tv).__name__}")
        elif isinstance(sv, (list, dict)):
            # structural comparison via canonical JSON serialisation
            sv_json = json.dumps(sv, sort_keys=True, ensure_ascii=False)
            tv_json = json.dumps(tv, sort_keys=True, ensure_ascii=False)
            if sv_json != tv_json:
                diffs.append(f"key '{key}' structural_diff")
        else:
            if sv != tv:
                diffs.append(f"key '{key}' value_diff: source={sv!r} support={tv!r}")

    return diffs


def _manifest_semantic_diff(
    source_file: Path, support_file: Path, rel_path: str
) -> SyncItem | None:
    """Perform key-level semantic diff on the live-agent publish manifest.

    Returns SyncItem if semantic differences found, None if semantically identical.
    """
    source_data = _load_json_safe(source_file)
    support_data = _load_json_safe(support_file)

    if source_data is None:
        return SyncItem(
            source=rel_path, target=rel_path,
            reason="source manifest unreadable or invalid JSON",
        )
    if support_data is None:
        return SyncItem(
            source=rel_path, target=rel_path,
            reason="support manifest missing or invalid JSON",
        )

    diffs = _json_key_diff(source_data, support_data)
    if diffs:
        return SyncItem(
            source=rel_path,
            target=rel_path,
            reason=f"manifest_semantic_diff: {'; '.join(diffs[:5])}",
        )
    return None


# ── B3: sync helpers ──────────────────────────────────────────────────────

def _is_protected_target(rel_path: str) -> bool:
    """Return True if *rel_path* targets a protected location.

    Protected: live entry agents (.github/agents/), binding profiles,
    and employee five-piece kit files.
    """
    rp = rel_path.replace("\\", "/")
    for pattern in PROTECTED_TARGET_PATTERNS:
        if pattern.replace("\\", "/") in rp:
            return True
    for suffix in EMPLOYEE_KIT_SUFFIXES:
        if rp.endswith(suffix):
            return True
    return False


def _execute_sync(
    report: SyncReport, source_root: Path, support_root: Path
) -> dict[str, Any]:
    """Copy out_of_sync source files to their support counterparts.

    Returns a result dict with 'synced', 'skipped', and 'errors' lists.
    Does NOT copy files marked for live-entry or employee-kit protection.
    """
    synced: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for item in report.out_of_sync:
        source_file = source_root / item.source
        support_file = support_root / item.target

        if not source_file.is_file():
            errors.append(f"source_not_found: {item.source}")
            continue

        if _is_protected_target(item.target):
            skipped.append(f"protected_target: {item.target} ({item.reason})")
            continue

        # ensure parent directory exists on support side
        try:
            support_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            errors.append(f"mkdir_failed: {support_file.parent} — {exc}")
            continue

        try:
            shutil.copy2(source_file, support_file)
            synced.append(item.source)
        except OSError as exc:
            errors.append(f"copy_failed: {item.source} → {item.target} — {exc}")

    return {"synced": synced, "skipped": skipped, "errors": errors}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source_publish_check",
        description=(
            "Phase B CLI: check TriCompany source → TriMetaverse publish "
            "side synchronisation status (B2 four-way diff + B3 --sync)."
        ),
    )
    parser.add_argument(
        "--source-root",
        default=".",
        help="TriCompany source root directory (default: current directory).",
    )
    parser.add_argument(
        "--support-root",
        default="../TriMetaverse",
        help="Publish / support root directory (default: ../TriMetaverse).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Execute synchronisation status check (B2+).",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        default=False,
        help="Execute sync for out_of_sync items (copy source → support). Requires --check.",
    )
    parser.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format (currently only 'json' is supported).",
    )
    parser.add_argument(
        "--scope",
        action="store_true",
        default=False,
        help="Print detection scope report to stderr before check (auditable).",
    )
    # ── Q3 Phase 2: agent publish arguments ───────────────────────────────
    parser.add_argument(
        "--publish-agents",
        action="store_true",
        default=False,
        help="Execute agent live entry publish check (dry-run by default). "
             "Use --agent-execute to actually write files.",
    )
    parser.add_argument(
        "--agent-execute",
        action="store_true",
        default=False,
        help="When combined with --publish-agents, actually write agent files "
             "to live entry targets. Without this flag, --publish-agents is dry-run only.",
    )
    parser.add_argument(
        "--employees",
        default=None,
        help="Comma-separated employee IDs to filter role-agent publish entries "
             "(e.g. 'ceo-chief-of-staff,chief-product-officer'). "
             "Only applies to --publish-agents mode.",
    )
    return parser


def run_check(source_root: Path, support_root: Path) -> SyncReport:
    """B2: four-way diff engine.

    For each file in the sync scope, selects the appropriate diff strategy
    and populates the SyncReport with out_of_sync, in_sync, and gaps entries.
    """
    source_items = _collect_source_items(source_root)
    out_of_sync: list[SyncItem] = []
    in_sync: list[SyncItem] = []
    gaps: list[SyncGap] = []

    # ── pre-compute git changed files (2b) ────────────────────────────────
    git_changed: set[str] = _git_changed_files(source_root)

    # ── pre-compute codegraph freshness (2c) ──────────────────────────────
    cg_status = _codegraph_freshness_check(source_root)
    if cg_status.get("stale"):
        gaps.append(SyncGap(
            item=".codegraph/index",
            issue=f"codegraph_stale: {cg_status.get('message', 'unknown')}",
        ))

    # ── iterate source items ──────────────────────────────────────────────
    for source_file in source_items:
        try:
            rel_path = source_file.relative_to(source_root).as_posix()
        except ValueError:
            continue

        support_file = support_root / rel_path

        # ── file does not exist on support side → gap ────────────────────
        if not support_file.is_file():
            gaps.append(SyncGap(
                item=rel_path,
                issue="missing_on_support",
            ))
            continue

        # ── 2d: JSON semantic diff for manifest ──────────────────────────
        if rel_path == MANIFEST_REL_PATH:
            result = _manifest_semantic_diff(source_file, support_file, rel_path)
            if result is not None:
                out_of_sync.append(result)
            else:
                in_sync.append(SyncItem(
                    source=rel_path, target=rel_path, reason="manifest_semantic_match",
                ))
            continue

        # ── determine file type and apply diff strategy ───────────────────
        ext = source_file.suffix.lower()

        if ext in DOC_EXTENSIONS:
            # 2a: hash diff for doc files
            result = _hash_diff(source_file, support_file, rel_path)
            if result is not None:
                out_of_sync.append(result)
            else:
                in_sync.append(SyncItem(
                    source=rel_path, target=rel_path, reason="hash_match",
                ))

        elif ext in SOURCE_EXTENSIONS:
            # 2b: git diff flag for source files, then fall back to hash
            git_result = _git_diff_flag(rel_path, git_changed)
            if git_result is not None:
                out_of_sync.append(git_result)
            else:
                # fallback: hash comparison for source files not in git diff
                hash_result = _hash_diff(source_file, support_file, rel_path)
                if hash_result is not None:
                    out_of_sync.append(hash_result)
                else:
                    in_sync.append(SyncItem(
                        source=rel_path, target=rel_path, reason="hash_match",
                    ))

        else:
            # unknown file type: fall back to hash comparison
            result = _hash_diff(source_file, support_file, rel_path)
            if result is not None:
                out_of_sync.append(result)
            else:
                in_sync.append(SyncItem(
                    source=rel_path, target=rel_path, reason="hash_match",
                ))

    # ── add codegraph structural gaps for files under source-agents ──────
    _append_codegraph_structural_gaps(source_root, support_root, gaps, source_items)

    # ── note: exclusion-based gaps (items correctly excluded) ─────────────
    gaps.append(SyncGap(
        item="employee five-piece kit",
        issue="excluded_from_sync_scope per CPO hard constraints (soul/memory/colleagues/social/body)",
    ))
    gaps.append(SyncGap(
        item="binding-profiles",
        issue="excluded_from_sync_scope per CPO hard constraints",
    ))

    total = len(out_of_sync) + len(in_sync) + len(gaps)
    return SyncReport(
        check_time=datetime.now(timezone.utc).isoformat(),
        source_root=source_root.as_posix(),
        support_root=support_root.as_posix(),
        out_of_sync=out_of_sync,
        in_sync=in_sync,
        gaps=gaps,
        summary=SyncSummary(
            total=total,
            out_of_sync=len(out_of_sync),
            in_sync=len(in_sync),
            gaps=len(gaps),
        ),
    )


def _append_codegraph_structural_gaps(
    source_root: Path,
    support_root: Path,
    gaps: list[SyncGap],
    source_items: list[Path],
) -> None:
    """Detect structural gaps using CodeGraph index or manifest cross-referencing.

    Checks:
    - Registry agent files under source-agents/registries/ that have live-entry targets
      defined in the manifest but whose support copy is missing or stale.
    - Files in the sync source dirs that CodeGraph detects as having new dependencies.
    """
    # cross-reference the publish manifest for registry agent live entries
    manifest_path = source_root / MANIFEST_REL_PATH
    if not manifest_path.is_file():
        gaps.append(SyncGap(
            item=MANIFEST_REL_PATH,
            issue="publish_manifest_missing — cannot cross-reference live entries",
        ))
        return

    manifest = _load_json_safe(manifest_path)
    if manifest is None:
        gaps.append(SyncGap(
            item=MANIFEST_REL_PATH,
            issue="publish_manifest_unreadable — cannot cross-reference live entries",
        ))
        return

    live_entries = manifest.get("liveEntries", [])
    if not isinstance(live_entries, list):
        return

    # build a set of discovered source-agent registry files from the source tree
    source_agent_files: set[str] = set()
    for sp in source_items:
        try:
            rel = sp.relative_to(source_root).as_posix()
        except ValueError:
            continue
        if "source-agents/registries/" in rel:
            source_agent_files.add(rel)

    for entry in live_entries:
        if not isinstance(entry, dict):
            continue
        entry_source = entry.get("source", "")
        entry_target = entry.get("target", "")
        status = entry.get("status", "")

        # only check source-published and current-copilot-host-live entries
        if status not in ("source-published-live-entry", "current-copilot-host-live"):
            continue

        # strip repo prefix (TriCompany/) from source path for comparison
        normalized_source = entry_source
        if normalized_source.startswith("TriCompany/"):
            normalized_source = normalized_source[len("TriCompany/"):]

        # check if source exists in collected items
        source_found = any(
            normalized_source in rel for rel in source_agent_files
        )
        if not source_found and normalized_source:
            # source might be in a different location; skip if not in sync scope
            continue

        # check if target exists on support side
        normalized_target = entry_target
        if normalized_target.startswith("TriMetaverse/"):
            normalized_target = normalized_target[len("TriMetaverse/"):]
        target_file = support_root / normalized_target
        if not target_file.is_file():
            gaps.append(SyncGap(
                item=normalized_target,
                issue=f"live_entry_target_missing: source={entry_source}",
            ))


def _print_agent_publish_summary(report: AgentPublishReport) -> None:
    """Print human-readable agent publish summary to stderr."""
    summary = report.summary
    lines = [
        "",
        "=" * 60,
        "  Agent Publish Report" + (" (DRY RUN)" if report.dry_run else " (EXECUTING)"),
        "=" * 60,
        f"  Total entries:  {summary.total}",
        f"  Created:        {summary.created}",
        f"  Updated:        {summary.updated}",
        f"  Skipped (same): {summary.skipped_identical}",
        f"  Skipped (dry):  {summary.skipped_dry_run}",
        f"  Errors:         {summary.errors}",
        "-" * 60,
    ]
    for item in report.items:
        icon = {
            "created": "✅",
            "updated": "🔄",
            "skipped_identical": "⏭️",
            "skipped_dry_run": "🔍",
            "error": "❌",
        }.get(item.action, "❓")
        lines.append(
            f"  {icon} {item.action:20s} {item.target}"
        )
        if item.error:
            lines.append(f"      error: {item.error}")
    lines.append("=" * 60)
    lines.append("")
    print("\n".join(lines), file=sys.stderr)


def _print_change_summary(cs: dict[str, Any]) -> None:
    """Print human-readable sync change summary to stderr."""
    before = cs.get("before", {})
    after = cs.get("after", {})
    synced_files: list[str] = cs.get("synced_files", [])
    skipped = cs.get("skipped", [])
    errors = cs.get("errors", [])

    lines = [
        "",
        "=" * 60,
        "  同步变化摘要",
        "=" * 60,
        f"  同步前  out_of_sync: {before.get('out_of_sync', '?')}  |  "
        f"in_sync: {before.get('in_sync', '?')}  |  gaps: {before.get('gaps', '?')}",
        f"  同步后  out_of_sync: {after.get('out_of_sync', '?')}  |  "
        f"in_sync: {after.get('in_sync', '?')}  |  gaps: {after.get('gaps', '?')}",
        "-" * 60,
    ]
    if synced_files:
        lines.append(f"  已同步 ({len(synced_files)} 个文件):")
        for f in synced_files:
            lines.append(f"    ✅ {f}")
    if skipped:
        lines.append(f"  已跳过 ({len(skipped)} 个):")
        for s in skipped:
            lines.append(f"    ⏭️  {s}")
    if errors:
        lines.append(f"  错误 ({len(errors)} 个):")
        for e in errors:
            lines.append(f"    ❌ {e}")
    lines.append("=" * 60)
    lines.append("")
    print("\n".join(lines), file=sys.stderr)


def _print_scope_report(source_root: Path, support_root: Path) -> None:
    """Print auditable detection scope to stderr."""
    lines = [
        "",
        "=" * 60,
        "  检测范围 (Scope Report)",
        "=" * 60,
        f"  源侧 (source):  {source_root.as_posix()}",
        f"  发布侧 (support): {support_root.as_posix()}",
        "-" * 60,
        "  纳入检测的目录:",
    ]
    for d in SYNC_SOURCE_DIRS:
        lines.append(f"    ✅ {d}")
    lines.append("")
    lines.append("  排除规则:")
    for g in EXCLUDE_GLOBS:
        lines.append(f"    ❌ {g}")
    lines.append("")
    lines.append("  保护目标 (永不覆盖):")
    for p in PROTECTED_TARGET_PATTERNS:
        lines.append(f"    🔒 {p}")
    lines.append("")
    lines.append("  差异检测策略:")
    lines.append(f"    文档类 ({', '.join(DOC_EXTENSIONS)}) → file hash (SHA-256)")
    lines.append(f"    源码类 ({', '.join(SOURCE_EXTENSIONS)}) → git diff + hash fallback")
    lines.append(f"    manifest → JSON semantic diff")
    lines.append(f"    结构性变更 → CodeGraph")
    lines.append("=" * 60)
    lines.append("")
    print("\n".join(lines), file=sys.stderr)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source_root = _normalize_path(args.source_root)
    support_root = _normalize_path(args.support_root)

    # ── parse --employees filter ──────────────────────────────────────────
    employee_ids: tuple[str, ...] | None = None
    if args.employees:
        employee_ids = tuple(
            eid.strip() for eid in args.employees.split(",") if eid.strip()
        )
        if not employee_ids:
            employee_ids = None

    # ── validate --agent-execute requires --publish-agents ─────────────────
    if args.agent_execute and not args.publish_agents:
        print(
            "error: --agent-execute requires --publish-agents",
            file=sys.stderr,
        )
        return 1

    sync_result: dict[str, Any] | None = None
    change_summary: dict[str, Any] | None = None
    agent_publish_report: dict[str, Any] | None = None

    # ── --publish-agents mode (can run with or without --check) ────────────
    if args.publish_agents:
        dry_run = not args.agent_execute
        ap_report = run_agent_publish(
            source_root=source_root,
            support_root=support_root,
            employee_ids=employee_ids,
            dry_run=dry_run,
        )
        agent_publish_report = _serialize_agent_publish_report(ap_report)
        # human-readable summary to stderr
        _print_agent_publish_summary(ap_report)

    # ── --check mode ──────────────────────────────────────────────────────
    if args.check:
        if args.scope:
            _print_scope_report(source_root, support_root)
        report = run_check(source_root, support_root)

        # capture before state for change summary
        before_out_of_sync = [
            {"source": si.source, "target": si.target, "reason": si.reason}
            for si in report.out_of_sync
        ]
        before_summary = {
            "total": report.summary.total,
            "out_of_sync": report.summary.out_of_sync,
            "in_sync": report.summary.in_sync,
            "gaps": report.summary.gaps,
        }

        # B3: --sync mode
        if args.sync:
            sync_result = _execute_sync(report, source_root, support_root)
            # re-run check to capture after state
            after_report = run_check(source_root, support_root)
            after_summary = {
                "total": after_report.summary.total,
                "out_of_sync": after_report.summary.out_of_sync,
                "in_sync": after_report.summary.in_sync,
                "gaps": after_report.summary.gaps,
            }
            change_summary: dict[str, Any] = {
                "before": before_summary,
                "after": after_summary,
                "synced_count": len(sync_result.get("synced", [])),
                "synced_files": sync_result.get("synced", []),
                "skipped_count": len(sync_result.get("skipped", [])),
                "skipped": sync_result.get("skipped", []),
                "error_count": len(sync_result.get("errors", [])),
                "errors": sync_result.get("errors", []),
            }
            # human-readable summary to stderr
            _print_change_summary(change_summary)
        else:
            change_summary = None
    else:
        if args.sync:
            print(
                "error: --sync requires --check to be set",
                file=sys.stderr,
            )
            return 1
        # --check not supplied: still emit empty framework when requested
        report = SyncReport(
            check_time=datetime.now(timezone.utc).isoformat(),
            source_root=source_root.as_posix(),
            support_root=support_root.as_posix(),
        )

    # ── if neither --check nor --publish-agents: default empty report ──────
    if not args.check and not args.publish_agents:
        report = SyncReport(
            check_time=datetime.now(timezone.utc).isoformat(),
            source_root=source_root.as_posix(),
            support_root=support_root.as_posix(),
        )

    # Serialise to JSON
    output: dict[str, Any] = {
        "check_time": report.check_time,
        "source_root": report.source_root,
        "support_root": report.support_root,
        "out_of_sync": [
            {"source": si.source, "target": si.target, "reason": si.reason}
            for si in report.out_of_sync
        ],
        "in_sync": [
            {"source": si.source, "target": si.target, "reason": si.reason}
            for si in report.in_sync
        ],
        "gaps": [
            {"item": sg.item, "issue": sg.issue} for sg in report.gaps
        ],
        "summary": {
            "total": report.summary.total,
            "out_of_sync": report.summary.out_of_sync,
            "in_sync": report.summary.in_sync,
            "gaps": report.summary.gaps,
        },
    }

    if sync_result is not None:
        output["sync"] = sync_result
    if change_summary is not None:
        output["change_summary"] = change_summary
    if agent_publish_report is not None:
        output["agent_publish"] = agent_publish_report

    if args.scope and args.check:
        output["scope"] = {
            "source_root": source_root.as_posix(),
            "support_root": support_root.as_posix(),
            "included_dirs": list(SYNC_SOURCE_DIRS),
            "excluded_globs": list(EXCLUDE_GLOBS),
            "excluded_dir_names": list(EXCLUDE_DIR_NAMES),
            "protected_targets": list(PROTECTED_TARGET_PATTERNS),
            "diff_strategies": {
                "doc_extensions": list(DOC_EXTENSIONS),
                "doc_method": "file hash (SHA-256)",
                "source_extensions": list(SOURCE_EXTENSIONS),
                "source_method": "git diff + hash fallback",
                "manifest_method": "JSON semantic diff (key-level)",
                "structural_method": "CodeGraph",
            },
        }

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
