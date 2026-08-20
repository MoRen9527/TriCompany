"""source_publish_check — TriCompany publish and project document DCE CLI.

B1 ✅ argument parsing, sync scope contract, structured JSON output framework.
B2 ✅ four-way diff engine (hash / git / codegraph / JSON semantic).
B3 ✅ --sync mode for executing out_of_sync file copies with live-entry protection.
B4 ✅ integration closeout — validation suite 13/13 green (2026-07-24), CLI contract verified.
B6 ✅ manifest-driven project truth document sync with planner candidate validation.

CLI entry: python -m runtime.cognition.source_publish_check --check --format json
Project docs: python -m runtime.cognition.source_publish_check --project-docs
Tests: python -m unittest runtime.cognition.source_publish_check_validation -v
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
# Paths that must never be overwritten during sync. .claude/agents/ is the
# Claude Code host face (ADE-B): the claude host itself is exempted via its
# protected_prefix, every other host (copilot) must never write it.
PROTECTED_TARGET_PATTERNS: tuple[str, ...] = (
    ".github/agents/",          # live entry agents
    ".github/binding-profiles/",  # binding profiles
    ".claude/agents/",          # ADE-B: Claude Code host face live entry agents
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
# Sole sanctioned live-entry landing zone for --publish-agents. Entries whose
# target lands anywhere else inside PROTECTED_TARGET_PATTERNS (binding
# profiles) or matching EMPLOYEE_KIT_SUFFIXES are rejected before any write
# (ADE phase-0 fix 2: whitelist ∩ protected zone = ∅ hard check).
AGENT_PUBLISH_LIVE_ENTRY_PREFIX: str = ".github/agents/"

# -- employee five-piece kit suffixes (extra safety net) ----------------------
EMPLOYEE_KIT_SUFFIXES: tuple[str, ...] = (
    ".soul.md",
    ".memory.md",
    ".colleagues.md",
    ".social.md",
    ".body.md",
)

# -- ADE-B multi-host render registry (CEO 2026-08-19 定调, §三 ADE-B) ----------
# 多宿主统一渲染模型：源单份 + 每宿主渲染模板 → 渲染产物。live entry 是宿主
# 发现面的派生加载壳（非字节副本），宿主附加段经 manifest 元数据
# (renderTemplate / extraSections) 回归源侧，禁止 live 成为第二语义真源。
# 未来支持任何宿主 = 注册表新增一个条目（模板+目标根+白名单），管线零改动。
# frontmatter 形状映射说明（CTO 定案 2026-08-20 批次 1）：
#   - copilot 面：源 frontmatter 原样（name/description/tools/user-invocable，
#     小写工具名），字节级保留，零回归。
#   - claude 面：输出字段顺序 name/description/tools/user-invocable；tools
#     按 tool_name_map 小写→PascalCase 映射（Claude Code 工具名）；映射/剔除
#     双态——未映射的源工具名从 claude 面剔除（剔除清单进 publish-agents 报告
#     scope_specific，审计可见非静默），映射值必须 ∈ CLAUDE_HOST_TOOL_ALLOWLIST
#     （映射到白名单外 = error 不落盘）。名字绑定（员工工作名）不注入
#     frontmatter（维持现状形状：frontmatter name = 源侧岗位名，员工名在正文）。
#   - 现有 .claude/agents/ 手工产物缺 user-invocable 字段；渲染将以
#     include_user_invocable=True 补齐（与任务书定案形状一致，标注为与现状
#     手工产物的差异，已 CTO 终审确认）。
@dataclass(frozen=True)
class HostRenderSpec:
    """Single host render template registration (ADE-B)."""

    host_id: str                  # "copilot" | "claude"
    live_root_marker: str         # manifest target 中可识别的宿主面根（如 ".github/agents"）
    target_root: str              # 渲染目标根（host=copilot 时 == live_root_marker）
    target_suffix: str            # 目标文件后缀（".agent.md" | ".md"）
    frontmatter_fields: tuple[str, ...]  # 输出 frontmatter 字段顺序
    include_user_invocable: bool  # 是否输出 user-invocable 字段
    tool_name_map: dict[str, str]  # 小写工具名 → 宿主工具名（PascalCase）
    protected_prefix: str         # sanctioned landing zone（保护检查豁免前缀）
    default_extra_section: str = ""  # 宿主默认附加段（定案 1：claude 面派生身份标记）


# claude 面派生身份标记（定案 1，CTO 2026-08-20）：渲染产物正文尾附加，
# 声明其由统一发布管线渲染生成；禁人工编辑，岗位职责修订走源侧合同。
CLAUDE_DERIVED_MARKER: str = (
    "本文件由统一发布管线渲染生成（--host=claude），禁人工编辑；岗位职责修订走源侧合同。"
)

# claude 面工具硬白名单（定案 2，CTO 2026-08-20）：渲染产物 tools 集必须 ⊆ 白名单。
# 映射值必须 ∈ 白名单（映射到白名单外 = error 不落盘）；未映射源工具从
# claude 面剔除，剔除清单进 publish-agents 报告 scope_specific（审计可见非静默）。
CLAUDE_HOST_TOOL_ALLOWLIST: frozenset[str] = frozenset({
    "Read", "Glob", "Grep", "Edit", "Write", "Bash",
    "WebFetch", "WebSearch", "NotebookEdit", "Task", "CodeSearch",
})


HOST_RENDER_REGISTRY: dict[str, HostRenderSpec] = {
    "copilot": HostRenderSpec(
        host_id="copilot",
        live_root_marker=".github/agents/",
        target_root=".github/agents/",
        target_suffix=".agent.md",
        frontmatter_fields=("name", "description", "tools", "user-invocable"),
        include_user_invocable=True,
        tool_name_map={},  # copilot 面原样保留源工具名
        protected_prefix=".github/agents/",
    ),
    "claude": HostRenderSpec(
        host_id="claude",
        live_root_marker=".github/agents/",
        target_root=".claude/agents/",
        target_suffix=".md",
        frontmatter_fields=("name", "description", "tools", "user-invocable"),
        include_user_invocable=True,
        tool_name_map={
            "read": "Read",
            "write": "Write",
            "edit": "Edit",
            "search": "Glob",
            "grep": "Grep",
            "glob": "Glob",
            "bash": "Bash",
            "web_fetch": "WebFetch",
            "web_search": "WebSearch",
            "notebook_edit": "NotebookEdit",
            "task": "Task",
            "code_search": "CodeSearch",
        },
        protected_prefix=".claude/agents/",
        default_extra_section=CLAUDE_DERIVED_MARKER,
    ),
}

# 默认宿主（未传 --host 时兼容现状：发布到 Copilot-host 面）。
DEFAULT_HOST_ID: str = "copilot"
# manifest liveEntries 渲染元数据键（缺省 = 当前复制/附加段行为，向后兼容旧
# manifest）。renderTemplate 当前仅支持 "host-default"（= 宿主注册表默认模板），
# 为 per-entry 模板覆盖预留扩展位。
RENDER_TEMPLATE_KEY: str = "renderTemplate"
RENDER_TEMPLATE_HOST_DEFAULT: str = "host-default"
EXTRA_SECTIONS_KEY: str = "extraSections"


# -- ADE unified report contract (ADE consolidation phase 1) -------------------
# All three CLI scopes (sync / project-docs / publish-agents) serialize to the
# same top-level envelope so Score / Close CLI can consume all domains with a
# single parser and a single validation schema:
#
#   {protocol, version, scope, run_id, mode, check_time, status,
#    summary{total,changed,skipped,errors}, items[], scope_specific{}}
#
# Scope-specific fields (plan_owner, close_owner, candidate, original counts,
# sync execution detail, ...) live in scope_specific; the shared summary keeps
# the invariant total == changed + skipped + errors.
ADE_PROTOCOL: str = "ade-report"
ADE_VERSION: str = "1.0"
ADE_SCOPES: tuple[str, ...] = ("sync", "project-docs", "publish-agents")

# Unified action vocabulary. Every report item's action must be a member of
# ADE_ACTIONS, and of its scope's allowed subset (ADE_ACTIONS_PER_SCOPE).
# planned_* items express write intent without performing it (dry-run);
# mode ("dry-run" | "execute") tells consumers whether writes happened.
ADE_ACTIONS: frozenset[str] = frozenset({
    "created",            # target written (new file)
    "updated",            # target written (overwritten)
    "planned_create",     # would create (dry-run intent; project-docs)
    "planned_update",     # would update (dry-run intent; project-docs / sync)
    "in_sync",            # already current, no change needed
    "skipped_identical",  # content identical, no write
    "skipped_dry_run",    # would write but dry-run
    "skipped_disabled",   # entry disabled in manifest
    "skipped_protected",  # sync: protected target skipped during execute
    "requires_candidate", # semantic candidate required (published-summary)
    "gap",                # sync scope item missing/unresolvable on support side
    "closed",             # close scope: terminal audit record written (Close CLI)
    "derived_identical",  # publish-agents render: live == render(source+template)
    "derived_drift",      # publish-agents render: live != render(source+template)
    "error",              # failed; see item.error for the error code
})

ADE_ACTIONS_PER_SCOPE: dict[str, frozenset[str]] = {
    "sync": frozenset({
        "updated", "planned_update", "in_sync",
        "skipped_protected", "gap", "error",
    }),
    "project-docs": frozenset({
        "created", "updated", "planned_create", "planned_update",
        "in_sync", "skipped_disabled", "requires_candidate", "error",
    }),
    "publish-agents": frozenset({
        "created", "updated", "skipped_identical", "skipped_dry_run",
        "derived_identical", "derived_drift", "error",
    }),
    # ADE phase 2: close is a lifecycle scope, not a business domain scope —
    # it stays out of ADE_SCOPES (spec §2.2 business scopes) but reuses the
    # envelope contract for the terminal-gate report.
    "close": frozenset({"closed", "error"}),
}

# -- ADE phase 2: lifecycle skeleton (runId / Close CLI / Score CLI) ----------
# Explicit run ids must be single tokens, filesystem-safe and parseable
# (used as close audit record file names); the timestamp-derived default
# (`ade-{scope}-{ts}`) always matches this pattern.
ADE_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

# Terminal states (spec §8.3): Close CLI accepts exactly these verdicts.
ADE_CLOSE_VERDICTS: tuple[str, ...] = ("APPROVED", "FROZEN", "ESCALATED", "RETRY")
# Lifecycle scopes that reuse the envelope contract but are not business
# domains (spec §2.2 three business scopes stay untouched).
ADE_LIFECYCLE_SCOPES: tuple[str, ...] = ("close",)

# Close CLI terminal audit record states (spec §2.5 终态门): CLOSED is the
# only terminal write; every validation failure lands in CLOSE_REJECTED and
# must never be silent (non-zero rc + machine-readable state).
ADE_CLOSE_STATE_CLOSED: str = "CLOSED"
ADE_CLOSE_STATE_REJECTED: str = "CLOSE_REJECTED"
# Per-run terminal audit record file name suffix.
ADE_CLOSE_RECORD_SUFFIX: str = ".close-ade.json"
# Default runtime records directory under --source-root (close audit records).
ADE_DEFAULT_DATA_DIR: str = ".ade"

# Score CLI defaults (spec §2.6 / 试卷模板 §二): threshold falls back to the
# paper's declared threshold, then to this default (80/100).
ADE_SCORE_DEFAULT_THRESHOLD: float = 80.0


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
    target_hash: str = ""  # before-write hash ("" when target missing)
    after_hash: str = ""   # after-write hash (audit; "" for skipped/error items)
    error: str = ""
    # 定案 2：claude 面渲染时被剔除的未映射源工具名（审计可见，非静默）。
    dropped_tools: list[str] = field(default_factory=list)


@dataclass
class AgentPublishSummary:
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped_identical: int = 0
    skipped_dry_run: int = 0
    derived_identical: int = 0  # ADE-B render: live == render(source+template)
    derived_drift: int = 0      # ADE-B render: live != render(source+template)
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


@dataclass
class ProjectDocSyncItem:
    """Single manifest-driven project document sync result."""

    entry_id: str
    source: str
    target: str
    sync_mode: str
    action: str
    source_hash: str = ""
    target_hash: str = ""
    after_hash: str = ""
    candidate: str = ""
    reason: str = ""
    error: str = ""


@dataclass
class ProjectDocSyncSummary:
    total: int = 0
    changed: int = 0
    planned: int = 0
    in_sync: int = 0
    needs_plan: int = 0
    skipped: int = 0
    errors: int = 0


@dataclass
class ProjectDocSyncReport:
    """ADE report for manifest-driven project truth document sync."""

    check_time: str
    manifest: str
    workspace_root: str
    plan_owner: str = ""
    close_owner: str = ""
    dry_run: bool = True
    status: str = "pass"
    items: list[ProjectDocSyncItem] = field(default_factory=list)
    summary: ProjectDocSyncSummary = field(default_factory=ProjectDocSyncSummary)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_path(raw: str | Path) -> Path:
    """Resolve and return an absolute, normalised Path."""
    return Path(raw).resolve()


def _make_run_id(scope: str) -> str:
    """Return a timestamp-derived run id for *scope*.

    The id is derived from the execution timestamp (``ade-{scope}-{ts}``,
    ts = UTC ``YYYYMMDDTHHMMSSffffff``). It is a *timestamp-derived* id, not
    a deterministic one: every invocation derives a fresh id from the current
    time, so back-to-back runs are identifiable and collisions are
    practically impossible (identical ids require two calls within the same
    microsecond). Use ``--run-id`` when a caller-controlled id is needed
    (ADE phase 2: explicit id wins over this derivation).
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"ade-{scope}-{ts}"


def _resolve_run_id(explicit_run_id: str | None, scope: str) -> str:
    """Resolve the envelope run id: explicit ``--run-id`` wins, timestamp
    fallback otherwise (ADE phase 2 work package 1).

    *explicit_run_id* must already be validated (non-empty, matches
    ADE_RUN_ID_PATTERN) by the caller; here it is only trimmed.
    """
    if explicit_run_id:
        return explicit_run_id.strip()
    return _make_run_id(scope)


def _validate_run_id(run_id: str) -> str:
    """Return an error code for an invalid explicit run id, or "" when valid.

    A valid run id is a single filesystem-safe token (used as close audit
    record file name) that callers can parse back — see ADE_RUN_ID_PATTERN.
    """
    if not run_id.strip():
        return "run_id_missing"
    if not ADE_RUN_ID_PATTERN.match(run_id.strip()):
        return "run_id_invalid"
    return ""


def _is_drive_relative_path(raw: str) -> bool:
    """Return True for Windows drive-relative paths like ``C:foo``.

    ``Path("C:foo").is_absolute()`` is False on Windows (drive but no root),
    so the static layers cannot flag such paths; they resolve relative to the
    drive's current directory, not to the workspace. The resolution layer
    rejects them outright (error code ``drive_relative_path_not_allowed``).
    """
    return bool(re.match(r"^[A-Za-z]:[^/\\]", raw))


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
) -> tuple[Path | None, str]:
    """Resolve an agent target path relative to support_root.

    Strips 'TriMetaverse/' prefix if present. Prevents workspace escapes —
    mirrors _resolve_project_doc_path: absolute paths are rejected outright
    and any path resolving outside support_root (e.g. parent-dir traversal)
    is rejected with an explicit error code.
    Returns (resolved absolute Path | None, error code "" when ok).
    """
    if not entry_target:
        return None, "path_missing"
    normalized = entry_target
    if normalized.startswith("TriMetaverse/"):
        normalized = normalized[len("TriMetaverse/"):]
    # Windows drive-relative paths ("C:foo") pass is_absolute() but resolve
    # against the drive's current directory, not the workspace — reject them
    # explicitly at the resolution layer (ADE phase 1 observation item).
    if _is_drive_relative_path(normalized):
        return None, "drive_relative_path_not_allowed"
    path = Path(normalized)
    if path.is_absolute():
        return None, "absolute_path_not_allowed"
    resolved_root = support_root.resolve()
    resolved_path = (resolved_root / path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return None, "outside_workspace"
    return resolved_path, ""


def _is_agent_publish_target_protected(
    entry_target: str, host_id: str = DEFAULT_HOST_ID
) -> bool:
    """Return True if a manifest whitelist target falls inside a forbidden zone.

    Reverse guard for the whitelist (ADE phase-0 fix 2): live entry publishing
    is the *only* sanctioned writer to the host's landing zone, so that prefix
    is exempted from the shared PROTECTED_TARGET_PATTERNS. Every other
    protected pattern (binding profiles) and the employee five-piece kit
    suffixes remain hard forbidden even when a contaminated manifest lists
    them — such entries must be rejected, never silently skipped.

    ADE-B multi-host: the sanctioned landing zone is host-specific
    (copilot → AGENT_PUBLISH_LIVE_ENTRY_PREFIX, claude → .claude/agents/,
    from HOST_RENDER_REGISTRY[host_id].protected_prefix). The static check
    runs against the *final write target* (after host target derivation).
    """
    spec = HOST_RENDER_REGISTRY[host_id]
    rp = entry_target.replace("\\", "/")
    if rp.startswith("TriMetaverse/"):
        rp = rp[len("TriMetaverse/"):]
    # Path-escape forms (absolute paths, root-relative "/x" forms — which are
    # not Windows-absolute but resolve ambiguously, parent-dir traversal) are
    # always protected: a contaminated whitelist must never write outside
    # support_root. The resolved-path guard in _resolve_agent_target_path
    # stays as a second layer for anything this static check misses.
    escape_path = Path(rp)
    if (
        escape_path.is_absolute()
        or rp.startswith("/")
        or ".." in escape_path.parts
    ):
        return True
    # Employee five-piece kit suffixes are forbidden everywhere, including
    # inside the live-entry landing zone.
    for suffix in EMPLOYEE_KIT_SUFFIXES:
        if rp.endswith(suffix):
            return True
    # Binding profiles are forbidden in every host layout (".github/
    # binding-profiles" via _is_protected_target, plus any other
    # "binding-profiles" directory a contaminated manifest could name —
    # the ADE-B claude face has no sanctioned binding-profiles writer).
    # No leading slash: also covers the bare top-level form
    # "TriMetaverse/binding-profiles/…" after prefix stripping.
    if "binding-profiles/" in rp:
        return True
    if rp.startswith(spec.protected_prefix):
        return False
    # Flip logic (CTO 定案): anything outside the sanctioned landing zone is
    # protected. PROTECTED_TARGET_PATTERNS prefix matching alone would miss
    # sibling-variant directories (.github/agents-backup, .claude/agents.bak,
    # bare agents/, other modules' .github/agents, docs/…) — the whitelist's
    # only sanctioned writer is the exact host prefix, everything else is a
    # forbidden write (error code stays protected_target_rejected).
    return True


# ---------------------------------------------------------------------------
# ADE-B: multi-host render pipeline (CEO 2026-08-19 定调)
# 源 + 宿主模板 → 渲染产物；派生一致校验（render hash == live hash）替代
# 纯字节复制。缺省（无 renderTemplate/extraSections 元数据 + host=copilot）
# = 当前复制行为，向后兼容旧 manifest。
# ---------------------------------------------------------------------------


def _is_render_entry(entry: dict[str, Any], host_id: str) -> bool:
    """Return True when *entry* is a render-surface entry.

    A render-surface entry derives its live payload from source + host
    template (frontmatter shape mapping + extraSections). Copy-surface
    entries (no render metadata + host=copilot) keep byte-copy behaviour
    for backward compatibility with legacy manifests.
    """
    if host_id != DEFAULT_HOST_ID:
        return True  # any non-copilot host always renders (shape mapping)
    has_render_metadata = bool(
        entry.get(RENDER_TEMPLATE_KEY) or entry.get(EXTRA_SECTIONS_KEY)
    )
    return has_render_metadata


def _derive_host_target(
    entry_target: str, host_id: str = DEFAULT_HOST_ID
) -> tuple[str, str]:
    """Derive the final write target for *host_id* from the manifest target.

    The manifest target is the single target source of truth (copilot-face
    layout, e.g. ``TriMetaverse/.github/agents/ceo.agent.md``). For another
    host the live root marker (``.github/agents``) is swapped to the host's
    target root (``.claude/agents``) and the suffix ``.agent.md`` → ``.md``.

    Returns (derived_target, error_code); error_code is "" on success.
    """
    spec = HOST_RENDER_REGISTRY[host_id]
    if host_id == DEFAULT_HOST_ID:
        return entry_target, ""
    rp = entry_target.replace("\\", "/")
    if spec.live_root_marker not in rp:
        return "", f"host_target_not_derivable:{spec.live_root_marker}"
    derived = rp.replace(spec.live_root_marker, spec.target_root)
    if derived.endswith(".agent.md"):
        derived = derived[: -len(".agent.md")] + spec.target_suffix
    return derived, ""


def _split_frontmatter(text: str) -> tuple[str, str, str]:
    """Split *text* into (frontmatter_block, body, suffix_newline).

    Frontmatter is the leading YAML block between ``---`` lines (the shape
    used by agent sources). When *text* has no leading ``---`` block the
    frontmatter block is "" and the whole text is body. The trailing newline
    convention of the source is preserved for byte-stable rendering.
    """
    if not text.startswith("---\n"):
        return "", text, ""
    first_end = text.find("\n---", 3)
    if first_end == -1:
        return "", text, ""
    block = text[: first_end + 5]  # includes closing "---" and its newline
    body = text[first_end + 5 :]  # skip "\n---\n"
    if body.endswith("\n"):
        return block, body.rstrip("\n"), "\n"
    return block, body, ""


def _render_frontmatter_for_host(
    frontmatter_block: str, spec: HostRenderSpec
) -> tuple[str, str, list[str]]:
    """Apply the host frontmatter shape mapping to *frontmatter_block*.

    Returns (rendered_frontmatter, error_code, dropped_tools); error_code is
    "" on success and dropped_tools lists claude-face-removed source tools.

    copilot: byte-identical passthrough (zero-regression guarantee).
    claude:  field order per spec.frontmatter_fields, tools mapped via
    spec.tool_name_map (lower → PascalCase), user-invocable emitted per
    spec.include_user_invocable. 映射/剔除双态（定案 2）：未映射的源工具名
    从 claude 面剔除（dropped_tools 报告，审计可见非静默）；映射值必须 ∈
    CLAUDE_HOST_TOOL_ALLOWLIST，映射到白名单外 = error（不落盘）。
    """
    if spec.host_id == DEFAULT_HOST_ID:
        return frontmatter_block, "", []
    fields: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        line = line.strip()
        if not line or line == "---":
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        fields[key] = value.strip()
    out_lines = ["---"]
    dropped: list[str] = []
    for field in spec.frontmatter_fields:
        if field not in fields:
            continue
        value = fields[field]
        if field == "tools":
            names: list[str] = []
            for raw in value.strip("[]").split(","):
                n = raw.strip()
                if not n:
                    continue
                mapped = spec.tool_name_map.get(n.lower())
                if mapped is None:
                    # 未映射 → 剔除（定案 2：映射/剔除双态；清单进报告审计）
                    dropped.append(n)
                    continue
                if mapped not in CLAUDE_HOST_TOOL_ALLOWLIST:
                    # 映射到白名单外 → error 不落盘（硬白名单）
                    return "", f"tool_not_in_allowlist:{mapped}", []
                names.append(mapped)
            value = f"[{', '.join(names)}]"
        out_lines.append(f"{field}: {value}")
    out_lines.append("---")
    return "\n".join(out_lines) + "\n", "", dropped


def _render_agent_payload(
    source_text: str, entry: dict[str, Any], host_id: str
) -> tuple[str, str, list[str]]:
    """Render the live payload: source + host template → render output.

    Returns (rendered_text, error_code, dropped_tools); error_code is "" on
    success and dropped_tools lists claude-face-removed source tools.

    Rendering rules:
      - copy-surface entries (no render metadata + host=copilot): byte
        passthrough of the source (backward compatible with legacy manifests).
      - render-surface entries: frontmatter shape mapping per the host
        template + source body + manifest ``extraSections`` (host additional
        sections template; absent = current behaviour) + host default extra
        section (定案 1: claude 面派生身份标记). extraSections is an opaque
        markdown string appended to the body — no parsing, no second semantic
        source.
      - renderTemplate must be absent or "host-default"; any other value is
        rejected (unsupported_render_template) to keep the registry the only
        template source of truth.

    Tool names (定案 2): unmapped source tools are dropped from the claude
    face (reported via dropped_tools); mapped values must belong to
    CLAUDE_HOST_TOOL_ALLOWLIST or the render errors out (no write).
    """
    template_raw = entry.get(RENDER_TEMPLATE_KEY)
    if template_raw is not None and template_raw != RENDER_TEMPLATE_HOST_DEFAULT:
        return "", f"unsupported_render_template:{template_raw}", []
    if not _is_render_entry(entry, host_id):
        return source_text, "", []
    # 渲染面专用 CRLF 归一（CTO 裁决 2026-08-20 方案 A）：渲染产物统一 LF。
    # 归一在 copy-surface 透传分支之后——复制面字节保留，零回归。
    source_text = source_text.replace("\r\n", "\n")

    spec = HOST_RENDER_REGISTRY[host_id]
    frontmatter_block, body, _ = _split_frontmatter(source_text)
    rendered_frontmatter, fm_error, dropped = _render_frontmatter_for_host(
        frontmatter_block, spec,
    )
    if fm_error:
        return "", fm_error, []
    # Render output always ends with exactly one "\n" (byte-stable hash).
    body = body.rstrip("\n")
    extra_sections = entry.get(EXTRA_SECTIONS_KEY) or ""
    if extra_sections:
        body = body + "\n\n" + str(extra_sections).rstrip("\n")
    # 定案 1：宿主默认附加段（claude 面派生身份标记）尾附于正文
    if spec.default_extra_section:
        body = body + "\n\n" + spec.default_extra_section
    if not rendered_frontmatter:
        return body + "\n", "", dropped
    return rendered_frontmatter + body + "\n", "", dropped


def _publish_single_agent(
    source_file: Path,
    target_file: Path,
    entry: dict[str, Any],
    *,
    dry_run: bool = True,
    host_id: str = DEFAULT_HOST_ID,
) -> AgentPublishItem:
    """Publish (or dry-run) a single agent live entry.

    ADE-B: the payload is *rendered* (source + host template) unless the
    entry is a copy-surface entry (no render metadata + host=copilot, byte
    passthrough for backward compatibility).

    - Computes SHA-256 of the source file (copy surface) or of the rendered
      payload (render surface).
    - If target doesn't exist: would create (or mark skipped_dry_run /
      derived_drift on the render surface).
    - If target exists and hash matches: skipped_identical (copy surface) /
      derived_identical (render surface — 派生一致校验).
    - If target exists and hash differs: would update (or mark
      skipped_dry_run / derived_drift on the render surface).

    Returns an AgentPublishItem describing the result.
    """
    render_entry = _is_render_entry(entry, host_id)
    dropped_tools: list[str] = []
    try:
        if render_entry:
            rendered_text, render_error, dropped_tools = _render_agent_payload(
                source_file.read_text(encoding="utf-8-sig"), entry, host_id
            )
            if render_error:
                return AgentPublishItem(
                    source=entry.get("source", ""),
                    target=entry.get("target", ""),
                    kind=entry.get("kind", ""),
                    manifest_status=entry.get("status", ""),
                    action="error",
                    source_hash="",
                    target_hash="",
                    error=render_error,
                    dropped_tools=dropped_tools,
                )
            source_hash = hashlib.sha256(
                rendered_text.encode("utf-8")
            ).hexdigest()
        else:
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
    identical_action = "derived_identical" if render_entry else "skipped_identical"
    drift_action = "derived_drift" if render_entry else "skipped_dry_run"

    def _write_payload() -> tuple[str, str]:
        """Write the payload; returns (after_hash, ""), or ("", error)."""
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if render_entry:
            target_file.write_bytes(rendered_text.encode("utf-8"))
        else:
            shutil.copy2(source_file, target_file)
        try:
            return _file_sha256(target_file), ""
        except OSError:
            return "", ""

    # Determine action
    if not target_exists:
        if dry_run:
            return AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=kind,
                manifest_status=manifest_status,
                action=drift_action,
                source_hash=source_hash,
                target_hash="",
                dropped_tools=dropped_tools,
            )
        # Write the agent file
        try:
            after_hash, _ = _write_payload()
            return AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=kind,
                manifest_status=manifest_status,
                action="created",
                source_hash=source_hash,
                target_hash="",
                after_hash=after_hash,
                dropped_tools=dropped_tools,
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
                dropped_tools=dropped_tools,
            )

    # Target exists — compare hashes
    if source_hash == target_hash:
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action=identical_action,
            source_hash=source_hash,
            target_hash=target_hash,
            dropped_tools=dropped_tools,
        )

    # Hash differs
    if dry_run:
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action=drift_action,
            source_hash=source_hash,
            target_hash=target_hash,
            dropped_tools=dropped_tools,
        )

    # Execute the update
    try:
        after_hash, _ = _write_payload()
        return AgentPublishItem(
            source=entry.get("source", ""),
            target=entry.get("target", ""),
            kind=kind,
            manifest_status=manifest_status,
            action="updated",
            source_hash=source_hash,
            target_hash=target_hash,
            after_hash=after_hash,
            dropped_tools=dropped_tools,
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
            dropped_tools=dropped_tools,
        )


def run_agent_publish(
    source_root: Path,
    support_root: Path,
    *,
    employee_ids: tuple[str, ...] | None = None,
    dry_run: bool = True,
    host_id: str = DEFAULT_HOST_ID,
) -> AgentPublishReport:
    """Execute --publish-agents logic.

    1. Load manifest; reject the whole run when any whitelist target falls
       inside a protected zone (whitelist ∩ protected zone = ∅ hard check).
       ADE-B: the check runs against the *final write target* (after host
       target derivation) so a contaminated manifest can never write a
       non-sanctioned host location either.
    2. Filter eligible entries.
    3. For each entry: resolve source → render (source + host template) →
       SHA-256; compare with target (派生一致校验).
    4. Return structured AgentPublishReport.

    When *dry_run* is True, no files are written.
    """
    if host_id not in HOST_RENDER_REGISTRY:
        raise ValueError(f"unsupported_host:{host_id}")
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

    # ── ADE phase-0 fix 2 + ADE-B: whitelist ∩ protected zone = ∅ ─────────
    # A contaminated manifest must never be executed against a protected
    # target. When any whitelist target (final write target after host
    # derivation) falls inside a forbidden zone the whole run is rejected
    # with explicit error items — never silently skipped, never partially
    # executed. Derivation failures (target not mappable to the host face)
    # are rejected the same way.
    final_targets: list[str] = []
    derivation_errors: list[str] = []
    for target in _derive_allowed_agent_targets(manifest):
        derived, derive_error = _derive_host_target(target, host_id)
        if derive_error:
            derivation_errors.append(f"{target}: {derive_error}")
            continue
        final_targets.append(derived)
    violating_targets = [
        target
        for target in final_targets
        if _is_agent_publish_target_protected(target, host_id)
    ]
    if violating_targets or derivation_errors:
        for target in sorted(violating_targets):
            report.items.append(AgentPublishItem(
                source="",
                target=target,
                kind="",
                manifest_status="",
                action="error",
                error="protected_target_rejected",
            ))
        for target_error in sorted(derivation_errors):
            report.items.append(AgentPublishItem(
                source="",
                target=target_error.split(": ", 1)[0],
                kind="",
                manifest_status="",
                action="error",
                error=target_error.split(": ", 1)[1],
            ))
        report.summary.total += len(violating_targets) + len(derivation_errors)
        report.summary.errors += len(violating_targets) + len(derivation_errors)
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

        final_target, derive_error = _derive_host_target(
            entry.get("target", ""), host_id
        )
        if derive_error:
            report.items.append(AgentPublishItem(
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                kind=entry.get("kind", ""),
                manifest_status=entry.get("status", ""),
                action="error",
                error=derive_error,
            ))
            report.summary.total += 1
            report.summary.errors += 1
            continue
        target_file, target_error = _resolve_agent_target_path(
            support_root, final_target
        )
        if target_error:
            report.items.append(AgentPublishItem(
                source=entry.get("source", ""),
                target=final_target,
                kind=entry.get("kind", ""),
                manifest_status=entry.get("status", ""),
                action="error",
                error=target_error,
            ))
            report.summary.total += 1
            report.summary.errors += 1
            continue

        result = _publish_single_agent(
            source_file,
            target_file,
            entry,
            dry_run=dry_run,
            host_id=host_id,
        )
        # ADE-B: the report target is the final write target (host-derived),
        # so consumers read the true write surface, not the copilot-face
        # manifest value.
        if result.target == entry.get("target", ""):
            result.target = final_target
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
        elif result.action == "derived_identical":
            report.summary.derived_identical += 1
        elif result.action == "derived_drift":
            report.summary.derived_drift += 1
        elif result.action == "error":
            report.summary.errors += 1

    return report


def _serialize_agent_publish_report(
    report: AgentPublishReport,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Serialize an AgentPublishReport to the unified ADE envelope contract.

    Shared summary keeps total == changed + skipped + errors; scope-specific
    counts (created/updated/skipped_identical/skipped_dry_run) and the
    original before-write hash surface live in scope_specific.
    *run_id* is the explicit ``--run-id`` when given (ADE phase 2); it wins
    over the timestamp-derived default.
    """
    changed = report.summary.created + report.summary.updated
    # derived_* items are not writes: derived_identical = live already matches
    # the render output; derived_drift = render-surface drift found (dry-run
    # intent, mirrors planned_update in project-docs). Both count as skipped
    # so the ADE invariant total == changed + skipped + errors holds.
    skipped = (
        report.summary.skipped_identical
        + report.summary.skipped_dry_run
        + report.summary.derived_identical
        + report.summary.derived_drift
    )
    errors = report.summary.errors
    return {
        "protocol": ADE_PROTOCOL,
        "version": ADE_VERSION,
        "scope": "publish-agents",
        "run_id": _resolve_run_id(run_id, "publish-agents"),
        "mode": "execute" if not report.dry_run else "dry-run",
        "check_time": report.check_time,
        "status": "fail" if errors else "pass",
        "summary": {
            "total": report.summary.total,
            "changed": changed,
            "skipped": skipped,
            "errors": errors,
        },
        "items": [
            {
                "action": a.action,
                "source": a.source,
                "target": a.target,
                "before_hash": a.target_hash,
                "after_hash": a.after_hash,
                "scope_key": a.target,
                "error": a.error,
                # domain extensions (kept for audit detail)
                "kind": a.kind,
                "manifest_status": a.manifest_status,
                # 定案 2：claude 面渲染剔除的未映射源工具（按目标聚合见
                # scope_specific.tool_drops；审计可见非静默）
                "dropped_tools": a.dropped_tools,
            }
            for a in report.items
        ],
        "scope_specific": {
            "source_root": report.source_root,
            "support_root": report.support_root,
            "dry_run": report.dry_run,
            "counts": {
                "created": report.summary.created,
                "updated": report.summary.updated,
                "skipped_identical": report.summary.skipped_identical,
                "skipped_dry_run": report.summary.skipped_dry_run,
                "derived_identical": report.summary.derived_identical,
                "derived_drift": report.summary.derived_drift,
            },
            # 定案 2：剔除清单（目标 → 剔除工具名，排序去重；空则缺省键）
            "tool_drops": {
                a.target: sorted(set(a.dropped_tools))
                for a in report.items
                if a.dropped_tools
            },
        },
    }


def _resolve_project_doc_path(
    workspace_root: Path, raw_path: str
) -> tuple[Path | None, str]:
    """Resolve a manifest path while preventing workspace escapes."""
    if not raw_path:
        return None, "path_missing"
    # Windows drive-relative paths ("C:foo") are ambiguous: they resolve
    # against the drive's current directory, never the workspace — reject
    # them explicitly (ADE phase 1 observation item).
    if _is_drive_relative_path(raw_path):
        return None, "drive_relative_path_not_allowed"
    path = Path(raw_path)
    if path.is_absolute():
        return None, "absolute_path_not_allowed"
    resolved_root = workspace_root.resolve()
    resolved_path = (resolved_root / path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return None, "outside_workspace"
    return resolved_path, ""


def _read_document_sync_metadata(file_path: Path) -> dict[str, str]:
    """Read bullet metadata from a document's sync metadata section."""
    try:
        lines = file_path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return {}

    metadata: dict[str, str] = {}
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## 文档同步元信息":
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section or not stripped.startswith("- "):
            continue
        key_value = stripped[2:].split(":", 1)
        if len(key_value) != 2:
            continue
        key, value = key_value
        metadata[key.strip()] = value.strip()
    return metadata


def _summary_metadata_errors(
    candidate_path: Path,
    *,
    source_path: str,
    source_hash: str,
) -> list[str]:
    """Validate deterministic metadata required for a published summary."""
    metadata = _read_document_sync_metadata(candidate_path)
    expected = {
        "sourceOfTruth": source_path.replace("\\", "/"),
        "syncMode": "published-summary",
        "sourceRevision": f"sha256:{source_hash}",
    }
    errors = [
        f"{key}_mismatch"
        for key, value in expected.items()
        if metadata.get(key) != value
    ]
    if not metadata.get("lastSyncedAt"):
        errors.append("lastSyncedAt_missing")
    return errors


def _finalize_project_doc_report(report: ProjectDocSyncReport) -> None:
    """Populate summary counters and ADE status from item actions."""
    actions = [item.action for item in report.items]
    report.summary = ProjectDocSyncSummary(
        total=len(actions),
        changed=sum(action in ("created", "updated") for action in actions),
        planned=sum(
            action in ("planned_create", "planned_update") for action in actions
        ),
        in_sync=actions.count("in_sync"),
        needs_plan=actions.count("requires_candidate"),
        skipped=actions.count("skipped_disabled"),
        errors=actions.count("error"),
    )
    if report.summary.errors:
        report.status = "fail"
    elif report.summary.needs_plan:
        report.status = "partial"
    else:
        report.status = "pass"


def run_project_doc_sync(
    manifest_path: Path,
    workspace_root: Path,
    *,
    execute: bool = False,
    entry_ids: tuple[str, ...] | None = None,
    candidate_overrides: dict[str, str] | None = None,
) -> ProjectDocSyncReport:
    """Run the manifest-driven project truth document ADE execution layer.

    ``published-copy`` entries are copied byte-for-byte. ``published-summary``
    entries are never synthesized by the CLI; a planner-provided candidate is
    required when the target's ``sourceRevision`` is stale.
    """
    manifest_path = manifest_path.resolve()
    workspace_root = workspace_root.resolve()
    report = ProjectDocSyncReport(
        check_time=datetime.now(timezone.utc).isoformat(),
        manifest=manifest_path.as_posix(),
        workspace_root=workspace_root.as_posix(),
        dry_run=not execute,
    )
    manifest = _load_json_safe(manifest_path)
    if manifest is None:
        report.items.append(ProjectDocSyncItem(
            entry_id="manifest",
            source="",
            target="",
            sync_mode="",
            action="error",
            error="manifest_missing_or_invalid",
        ))
        _finalize_project_doc_report(report)
        return report

    report.plan_owner = str(manifest.get("planOwner", ""))
    report.close_owner = str(manifest.get("closeOwner", ""))
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        report.items.append(ProjectDocSyncItem(
            entry_id="manifest",
            source="",
            target="",
            sync_mode="",
            action="error",
            error="manifest_entries_must_be_array",
        ))
        _finalize_project_doc_report(report)
        return report

    candidates = candidate_overrides or {}
    selected_ids = set(entry_ids) if entry_ids is not None else None
    known_ids = {
        str(entry.get("id", ""))
        for entry in entries
        if isinstance(entry, dict) and entry.get("id")
    }
    if selected_ids is not None:
        for missing_id in sorted(selected_ids - known_ids):
            report.items.append(ProjectDocSyncItem(
                entry_id=missing_id,
                source="",
                target="",
                sync_mode="",
                action="error",
                error="entry_id_not_found",
            ))

    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            report.items.append(ProjectDocSyncItem(
                entry_id="",
                source="",
                target="",
                sync_mode="",
                action="error",
                error="manifest_entry_must_be_object",
            ))
            continue

        entry_id = str(raw_entry.get("id", ""))
        source_path = str(raw_entry.get("source", ""))
        target_path = str(raw_entry.get("target", ""))
        sync_mode = str(raw_entry.get("syncMode", ""))
        item_base = {
            "entry_id": entry_id,
            "source": source_path,
            "target": target_path,
            "sync_mode": sync_mode,
        }

        if selected_ids is not None and entry_id not in selected_ids:
            continue
        if raw_entry.get("enabled", True) is False:
            report.items.append(ProjectDocSyncItem(
                **item_base, action="skipped_disabled"
            ))
            continue
        if not entry_id:
            report.items.append(ProjectDocSyncItem(
                **item_base, action="error", error="entry_id_missing"
            ))
            continue
        if sync_mode not in ("published-copy", "published-summary"):
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                error=f"unsupported_sync_mode:{sync_mode}",
            ))
            continue
        if (
            Path(source_path).suffix.lower() not in DOC_EXTENSIONS
            or Path(target_path).suffix.lower() not in DOC_EXTENSIONS
        ):
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                error="non_document_path",
            ))
            continue
        if _is_protected_target(target_path):
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                error="protected_target",
            ))
            continue

        source_file, source_error = _resolve_project_doc_path(
            workspace_root, source_path
        )
        target_file, target_error = _resolve_project_doc_path(
            workspace_root, target_path
        )
        if source_error or target_error:
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                error=source_error or target_error,
            ))
            continue
        if source_file is None or not source_file.is_file():
            report.items.append(ProjectDocSyncItem(
                **item_base, action="error", error="source_file_not_found"
            ))
            continue
        if target_file is None:
            report.items.append(ProjectDocSyncItem(
                **item_base, action="error", error="target_path_unresolved"
            ))
            continue

        source_hash = _file_sha256(source_file)
        target_hash = _file_sha256(target_file) if target_file.is_file() else ""

        if sync_mode == "published-copy":
            if source_hash == target_hash:
                report.items.append(ProjectDocSyncItem(
                    **item_base,
                    action="in_sync",
                    source_hash=source_hash,
                    target_hash=target_hash,
                    reason="hash_match",
                ))
                continue
            planned_action = "planned_update" if target_hash else "planned_create"
            if not execute:
                report.items.append(ProjectDocSyncItem(
                    **item_base,
                    action=planned_action,
                    source_hash=source_hash,
                    target_hash=target_hash,
                    after_hash=source_hash,
                    reason="hash_mismatch" if target_hash else "target_missing",
                ))
                continue
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
            except OSError as exc:
                report.items.append(ProjectDocSyncItem(
                    **item_base,
                    action="error",
                    source_hash=source_hash,
                    target_hash=target_hash,
                    error=f"write_failed:{exc}",
                ))
                continue
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="updated" if target_hash else "created",
                source_hash=source_hash,
                target_hash=target_hash,
                after_hash=source_hash,
                reason="copied_source_to_target",
            ))
            continue

        if target_file.is_file() and not _summary_metadata_errors(
            target_file,
            source_path=source_path,
            source_hash=source_hash,
        ):
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="in_sync",
                source_hash=source_hash,
                target_hash=target_hash,
                reason="source_revision_match",
            ))
            continue

        candidate_raw = candidates.get(entry_id) or str(raw_entry.get("candidate", ""))
        if not candidate_raw:
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="requires_candidate",
                source_hash=source_hash,
                target_hash=target_hash,
                reason="planner_candidate_required_for_published_summary",
            ))
            continue

        candidate_path = Path(candidate_raw)
        if not candidate_path.is_absolute():
            candidate_path = workspace_root / candidate_path
        candidate_path = candidate_path.resolve()
        if not candidate_path.is_file():
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                source_hash=source_hash,
                target_hash=target_hash,
                candidate=candidate_path.as_posix(),
                error="candidate_file_not_found",
            ))
            continue
        metadata_errors = _summary_metadata_errors(
            candidate_path,
            source_path=source_path,
            source_hash=source_hash,
        )
        if metadata_errors:
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                source_hash=source_hash,
                target_hash=target_hash,
                candidate=candidate_path.as_posix(),
                error=f"candidate_metadata_invalid:{','.join(metadata_errors)}",
            ))
            continue

        candidate_hash = _file_sha256(candidate_path)
        if candidate_hash == target_hash:
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="in_sync",
                source_hash=source_hash,
                target_hash=target_hash,
                candidate=candidate_path.as_posix(),
                reason="candidate_hash_match",
            ))
            continue
        if not execute:
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="planned_update" if target_hash else "planned_create",
                source_hash=source_hash,
                target_hash=target_hash,
                after_hash=candidate_hash,
                candidate=candidate_path.as_posix(),
                reason="validated_summary_candidate",
            ))
            continue
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate_path, target_file)
        except OSError as exc:
            report.items.append(ProjectDocSyncItem(
                **item_base,
                action="error",
                source_hash=source_hash,
                target_hash=target_hash,
                candidate=candidate_path.as_posix(),
                error=f"write_failed:{exc}",
            ))
            continue
        report.items.append(ProjectDocSyncItem(
            **item_base,
            action="updated" if target_hash else "created",
            source_hash=source_hash,
            target_hash=target_hash,
            after_hash=candidate_hash,
            candidate=candidate_path.as_posix(),
            reason="validated_summary_candidate_published",
        ))

    _finalize_project_doc_report(report)
    return report


def _serialize_project_doc_sync_report(
    report: ProjectDocSyncReport,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Serialize the project document ADE report to the unified envelope.

    status pass/fail/partial and plan_owner/close_owner (semantic-plan
    owners) move to scope_specific; planned_* actions stay on items so
    consumers can distinguish write intent from performed writes.
    *run_id* is the explicit ``--run-id`` when given (ADE phase 2).
    """
    changed = report.summary.changed
    errors = report.summary.errors
    return {
        "protocol": ADE_PROTOCOL,
        "version": ADE_VERSION,
        "scope": "project-docs",
        "run_id": _resolve_run_id(run_id, "project-docs"),
        "mode": "execute" if not report.dry_run else "dry-run",
        "check_time": report.check_time,
        "status": report.status,
        "summary": {
            "total": report.summary.total,
            "changed": changed,
            # invariant total == changed + skipped + errors; skipped covers
            # planned_* (dry-run intent), in_sync, needs_plan and disabled.
            "skipped": report.summary.total - changed - errors,
            "errors": errors,
        },
        "items": [
            {
                "action": item.action,
                "source": item.source,
                "target": item.target,
                "before_hash": item.target_hash,
                "after_hash": item.after_hash,
                "scope_key": item.entry_id,
                "error": item.error,
                # domain extensions (kept for audit detail)
                "entry_id": item.entry_id,
                "sync_mode": item.sync_mode,
                "candidate": item.candidate,
                "reason": item.reason,
            }
            for item in report.items
        ],
        "scope_specific": {
            "manifest": report.manifest,
            "workspace_root": report.workspace_root,
            "plan_owner": report.plan_owner,
            "close_owner": report.close_owner,
            "dry_run": report.dry_run,
            "counts": {
                "planned": report.summary.planned,
                "in_sync": report.summary.in_sync,
                "needs_plan": report.summary.needs_plan,
                "skipped_disabled": report.summary.skipped,
            },
        },
    }


def _classify_sync_outcomes(
    sync_result: dict[str, Any] | None,
    out_of_sync: list[SyncItem],
) -> dict[str, str]:
    """Map each out_of_sync item to its post-execute action.

    _execute_sync appends every out_of_sync item to exactly one of
    synced / skipped / errors, so each item maps to:
      - "updated"           → written successfully
      - "skipped_protected" → protected target, never written
      - "error"             → failed (source missing / copy / mkdir failure)
    Items that cannot be attributed to a specific outcome (rare mkdir
    failures without a source reference) map to "error"; the raw execution
    result stays in scope_specific.sync for audit.
    """
    if sync_result is None:
        return {}
    synced: set[str] = set(sync_result.get("synced", []))
    # protected-skip strings look like "protected_target: <target> (<reason>)"
    skipped_targets: set[str] = set()
    for skip in sync_result.get("skipped", []):
        if skip.startswith("protected_target: "):
            skipped_targets.add(skip.split(":", 1)[1].strip().split(" (", 1)[0])
    outcomes: dict[str, str] = {}
    for item in out_of_sync:
        if item.source in synced:
            outcomes[item.source] = "updated"
        elif item.target in skipped_targets:
            outcomes[item.source] = "skipped_protected"
        else:
            outcomes[item.source] = "error"
    return outcomes


def _serialize_sync_report(
    report: SyncReport,
    *,
    sync_result: dict[str, Any] | None = None,
    change_summary: dict[str, Any] | None = None,
    scope_report: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Serialize the --check / --sync report to the unified ADE envelope.

    - dry-run (--check only): out_of_sync items carry action planned_update
      (write intent, nothing written); skipped covers every non-written item.
    - execute (--check --sync): out_of_sync items are split by execution
      outcome (updated / skipped_protected / error); the raw execution
      result (synced/skipped/errors lists) stays in scope_specific.sync.
    *run_id* is the explicit ``--run-id`` when given (ADE phase 2).
    """
    executed = sync_result is not None
    outcomes = (
        _classify_sync_outcomes(sync_result, report.out_of_sync)
        if executed else {}
    )

    items: list[dict[str, Any]] = []
    for si in report.out_of_sync:
        action = outcomes.get(si.source, "planned_update")
        items.append({
            "action": action,
            "source": si.source,
            "target": si.target,
            "before_hash": "",
            "after_hash": "",
            "scope_key": si.source,
            "error": "",
            # domain extension (diff reason, kept for audit detail)
            "reason": si.reason,
        })
    for si in report.in_sync:
        items.append({
            "action": "in_sync",
            "source": si.source,
            "target": si.target,
            "before_hash": "",
            "after_hash": "",
            "scope_key": si.source,
            "error": "",
            "reason": si.reason,
        })
    for sg in report.gaps:
        items.append({
            "action": "gap",
            "source": "",
            "target": "",
            "before_hash": "",
            "after_hash": "",
            "scope_key": sg.item,
            "error": "",
            "reason": sg.issue,
        })

    errors = len(sync_result.get("errors", [])) if sync_result else 0
    changed = len(sync_result.get("synced", [])) if sync_result else 0
    if executed:
        protected_count = sum(
            1 for outcome in outcomes.values()
            if outcome == "skipped_protected"
        )
        skipped = len(report.in_sync) + len(report.gaps) + protected_count
    else:
        skipped = (
            len(report.out_of_sync) + len(report.in_sync) + len(report.gaps)
        )

    scope_specific: dict[str, Any] = {
        "source_root": report.source_root,
        "support_root": report.support_root,
        "counts": {
            "out_of_sync": report.summary.out_of_sync,
            "in_sync": report.summary.in_sync,
            "gaps": report.summary.gaps,
        },
    }
    if sync_result is not None:
        scope_specific["sync"] = sync_result
    if change_summary is not None:
        scope_specific["before"] = change_summary.get("before", {})
        scope_specific["after"] = change_summary.get("after", {})
    if scope_report is not None:
        scope_specific["scope_report"] = scope_report

    return {
        "protocol": ADE_PROTOCOL,
        "version": ADE_VERSION,
        "scope": "sync",
        "run_id": _resolve_run_id(run_id, "sync"),
        "mode": "execute" if executed else "dry-run",
        "check_time": report.check_time,
        "status": "fail" if errors else "pass",
        "summary": {
            "total": report.summary.total,
            "changed": changed,
            "skipped": skipped,
            "errors": errors,
        },
        "items": items,
        "scope_specific": scope_specific,
    }


def _serialize_combined_container(
    envelopes: list[dict[str, Any]],
    *,
    run_id: str | None = None,
    check_time: str | None = None,
) -> dict[str, Any]:
    """Aggregate multiple scope envelopes into a combined-run container.

    Shape proposal (ADE phase 2 work package 2, 终审判定):

    .. code-block:: json

        {
          "protocol": "ade-report", "version": "1.0",
          "run_id": "<explicit --run-id, present only when given>",
          "check_time": "<container creation time>",
          "status": "fail|partial|pass",
          "summary": {"total": N, "changed": N, "skipped": N, "errors": N},
          "reports": [envelope...]
        }

    Aggregation rules:
      - status: any report with errors > 0 → "fail"; else any report with
        status "partial" → "partial"; else "pass".
      - summary: total / changed / skipped / errors summed across reports.
        Per-envelope invariant (total == changed + skipped + errors) is
        preserved by the sum.
      - run_id: only present when an explicit --run-id was given (each
        report already carries its own run_id; no synthetic container id).
    """
    status = "pass"
    for env in envelopes:
        errors = env.get("summary", {}).get("errors", 0)
        if errors > 0:
            status = "fail"
            break
        if env.get("status") == "partial":
            status = "partial"
    summary = {
        key: sum(env.get("summary", {}).get(key, 0) for env in envelopes)
        for key in ("total", "changed", "skipped", "errors")
    }
    container: dict[str, Any] = {
        "protocol": ADE_PROTOCOL,
        "version": ADE_VERSION,
        "check_time": check_time or datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": summary,
        "reports": envelopes,
    }
    if run_id:
        container["run_id"] = run_id.strip()
    return container


# ---------------------------------------------------------------------------
# ADE phase 2: Close CLI (spec §2.5 终态门)
# ---------------------------------------------------------------------------

def _close_data_dir(ade_data_dir: str | None, source_root: Path) -> Path:
    """Resolve the ADE runtime records directory for close audit records."""
    if ade_data_dir:
        raw = Path(ade_data_dir)
        return raw if raw.is_absolute() else (source_root / raw)
    return source_root / ADE_DEFAULT_DATA_DIR


def _evidence_ref_resolvable(evidence_ref: str, source_root: Path) -> bool:
    """Return True when *evidence_ref* points at a resolvable artifact.

    Resolvable = an existing file (absolute path, or path relative to
    --source-root) or an http(s) / file URL.
    """
    if not evidence_ref:
        return False
    if evidence_ref.startswith(("http://", "https://", "file://")):
        return True
    candidate = Path(evidence_ref)
    if candidate.is_absolute():
        return candidate.is_file()
    return (source_root / candidate).is_file()


def _validate_close_inputs(
    *,
    run_id: str,
    verdict: str,
    evidence_ref: str,
    source_revision: str,
    source_root: Path,
) -> list[str]:
    """Validate Close CLI inputs (spec §2.5). Returns error codes, [] = ok.

    - verdict ∈ ADE_CLOSE_VERDICTS (terminal states, spec §8.3)
    - run_id non-empty and parseable (ADE_RUN_ID_PATTERN)
    - evidence-ref resolvable (existing file / URL)
    - source-revision non-empty single token
    """
    errors: list[str] = []
    run_id_error = _validate_run_id(run_id)
    if run_id_error:
        errors.append(run_id_error)
    if verdict not in ADE_CLOSE_VERDICTS:
        errors.append("verdict_invalid")
    if not evidence_ref.strip():
        errors.append("evidence_ref_missing")
    elif not _evidence_ref_resolvable(evidence_ref.strip(), source_root):
        errors.append("evidence_ref_unresolvable")
    revision = source_revision.strip()
    if not revision:
        errors.append("source_revision_missing")
    elif len(revision) > 128 or any(ch.isspace() for ch in revision):
        errors.append("source_revision_invalid")
    return errors


def _serialize_close_envelope(
    *,
    run_id: str,
    verdict: str,
    evidence_ref: str,
    source_revision: str,
    check_time: str,
    state: str,
    audit_record: str,
    errors: list[str],
) -> dict[str, Any]:
    """Serialize the Close CLI report to the unified envelope contract.

    scope is "close" (ADE_LIFECYCLE_SCOPES): reuses the envelope shape so
    Score / Close consumers parse it with the same schema, but stays out of
    the three business-domain scopes (spec §2.2).
    """
    accepted = state == ADE_CLOSE_STATE_CLOSED
    return {
        "protocol": ADE_PROTOCOL,
        "version": ADE_VERSION,
        "scope": "close",
        "run_id": run_id,
        "mode": "execute",
        "check_time": check_time,
        "status": "pass" if accepted else "fail",
        "summary": {
            "total": 1,
            "changed": 1 if accepted else 0,
            "skipped": 0,
            "errors": 0 if accepted else 1,
        },
        "items": [
            {
                "action": "closed" if accepted else "error",
                "source": "",
                "target": audit_record,
                "before_hash": "",
                "after_hash": "",
                "scope_key": run_id,
                "error": ";".join(errors),
            }
        ],
        "scope_specific": {
            "state": state,
            "verdict": verdict,
            "evidence_ref": evidence_ref,
            "source_revision": source_revision,
            "audit_record": audit_record,
        },
    }


def run_close(
    *,
    run_id: str,
    verdict: str,
    evidence_ref: str,
    source_revision: str,
    source_root: Path,
    ade_data_dir: str | None = None,
) -> dict[str, Any]:
    """Execute the Close CLI (spec §2.5 终态门).

    1. Validate verdict / run_id / evidence-ref / source-revision.
    2. On failure: return a CLOSE_REJECTED envelope (never silent, never a
       terminal write).
    3. On success: write the per-run terminal audit record
       ``<data_dir>/<run_id>.close-ade.json`` and return a CLOSED envelope.
       A run with an existing audit record is rejected (no double close —
       state transition validation).
    """
    check_time = datetime.now(timezone.utc).isoformat()
    errors = _validate_close_inputs(
        run_id=run_id,
        verdict=verdict,
        evidence_ref=evidence_ref,
        source_revision=source_revision,
        source_root=source_root,
    )
    if errors:
        return _serialize_close_envelope(
            run_id=run_id.strip(),
            verdict=verdict,
            evidence_ref=evidence_ref,
            source_revision=source_revision,
            check_time=check_time,
            state=ADE_CLOSE_STATE_REJECTED,
            audit_record="",
            errors=errors,
        )

    data_dir = _close_data_dir(ade_data_dir, source_root)
    audit_record = data_dir / f"{run_id.strip()}{ADE_CLOSE_RECORD_SUFFIX}"
    # State-transition guard: a run can only be closed once.
    if audit_record.is_file():
        return _serialize_close_envelope(
            run_id=run_id.strip(),
            verdict=verdict,
            evidence_ref=evidence_ref,
            source_revision=source_revision,
            check_time=check_time,
            state=ADE_CLOSE_STATE_REJECTED,
            audit_record=audit_record.as_posix(),
            errors=["run_already_closed"],
        )

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id.strip(),
            "verdict": verdict,
            "evidence": evidence_ref.strip(),
            "source_revision": source_revision.strip(),
            "check_time": check_time,
        }
        audit_record.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        return _serialize_close_envelope(
            run_id=run_id.strip(),
            verdict=verdict,
            evidence_ref=evidence_ref,
            source_revision=source_revision,
            check_time=check_time,
            state=ADE_CLOSE_STATE_REJECTED,
            audit_record="",
            errors=[f"audit_write_failed:{exc}"],
        )

    return _serialize_close_envelope(
        run_id=run_id.strip(),
        verdict=verdict,
        evidence_ref=evidence_ref,
        source_revision=source_revision,
        check_time=check_time,
        state=ADE_CLOSE_STATE_CLOSED,
        audit_record=audit_record.as_posix(),
        errors=[],
    )


# ---------------------------------------------------------------------------
# ADE phase 2: Score CLI (spec §2.6 / 试卷模板 §三)
# ---------------------------------------------------------------------------

def _iter_report_envelopes(report_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize a score input report into a list of envelopes.

    Accepts a bare envelope or a combined-run reports container; malformed
    containers yield [] (defensive, mirrors ade_envelope.find_scope_envelope).
    """
    if report_data.get("protocol") == ADE_PROTOCOL and "scope" in report_data:
        return [report_data]
    reports = report_data.get("reports")
    if not isinstance(reports, list):
        return []
    return [
        r for r in reports
        if isinstance(r, dict) and r.get("protocol") == ADE_PROTOCOL
    ]


def _find_item_evidence(
    paper_item: dict[str, Any],
    envelopes: list[dict[str, Any]],
) -> str | None:
    """Locate evidence for *paper_item* inside the report envelopes.

    Coverage check (Score CLI, deterministic — spec §2.6). Probe values, in
    priority order:
      1. the paper item's declared ``evidence_ref`` (when present) — strict:
         it must be found or the item is omitted;
      2. the paper item ``id``;
      3. the paper item ``label``.

    A probe matches when, in any envelope:
      - an item's ``scope_key`` / ``source`` / ``target`` equals the probe,
        ends with ``/`` + probe (path suffix), or has a file stem equal to
        the probe (``docs/dry-run-gate.md`` matches id ``dry-run-gate``); or
      - ``scope_specific`` has a top-level key equal to the probe, or a
        top-level string value equal to it.

    Returns the evidence reference string (the matched report item's
    field value, or ``scope_specific.<key>``), or None when no evidence is
    found (→ omission = true, 0 分).
    """
    probes: list[str] = []
    declared = str(paper_item.get("evidence_ref") or "").strip()
    if declared:
        probes.append(declared)
    else:
        probes.append(str(paper_item.get("id") or ""))
        label = str(paper_item.get("label") or "")
        if label:
            probes.append(label)

    for env in envelopes:
        items = env.get("items")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                for field in ("scope_key", "source", "target"):
                    value = str(item.get(field) or "")
                    for probe in probes:
                        if not probe:
                            continue
                        if (
                            value == probe
                            or (probe and value.endswith("/" + probe))
                            or (probe and Path(value).stem == probe)
                        ):
                            return value
        scope_specific = env.get("scope_specific")
        if isinstance(scope_specific, dict):
            for key, value in scope_specific.items():
                for probe in probes:
                    if not probe:
                        continue
                    if key == probe:
                        return f"scope_specific.{key}"
                    if str(value) == probe:
                        return f"scope_specific.{key}"
    return None


def _normalize_quality_scores(quality_scores: dict[str, Any]) -> dict[str, float]:
    """Normalize --score-quality-scores into {item_id: score}.

    Accepted shapes (proposal, 终审判定):
      {"items": [{"id": "...", "score": 8}, ...]}   — primary, Skill-friendly
      {"<item id>": 8, ...}                          — plain map fallback
    """
    normalized: dict[str, float] = {}
    raw_items = quality_scores.get("items")
    if isinstance(raw_items, list):
        for entry in raw_items:
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("id") or "")
            score = entry.get("score")
            if entry_id and isinstance(score, (int, float)):
                normalized[entry_id] = float(score)
    else:
        for entry_id, score in quality_scores.items():
            if entry_id == "items":
                continue
            if isinstance(score, (int, float)):
                normalized[str(entry_id)] = float(score)
    return normalized


def score_assessment(
    paper: dict[str, Any],
    report: dict[str, Any],
    *,
    quality_scores: dict[str, Any] | None = None,
    threshold: float | None = None,
    scored_at: str | None = None,
) -> dict[str, Any]:
    """Run the Score CLI assessment (spec §2.6 / 试卷模板 §三).

    Deterministic part: coverage check per paper item (omission + required
    all-passed). Semantic part: quality scores merged in (Score Skill
    output). Double gate: verdict PASS ⇔ required_all_passed ∧
    total.score >= total.threshold.

    Raises ValueError on invalid paper / quality input (caller maps it to a
    fail contract + non-zero rc).
    """
    raw_items = paper.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("paper_items_must_be_nonempty_list")

    quality = _normalize_quality_scores(quality_scores or {})
    envelopes = _iter_report_envelopes(report)
    if not envelopes:
        raise ValueError("report_has_no_envelope")

    scored_items: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("paper_item_must_be_object")
        item_id = str(raw.get("id") or "")
        if not item_id:
            raise ValueError("paper_item_id_missing")
        max_score = raw.get("max")
        if not isinstance(max_score, (int, float)) or max_score <= 0:
            raise ValueError(f"paper_item_max_invalid:{item_id}")
        max_score = float(max_score)
        label = str(raw.get("label") or item_id)
        weight = raw.get("weight")
        if not isinstance(weight, (int, float)) or weight < 0:
            weight = max_score
        required = bool(raw.get("required", False))

        evidence_ref = _find_item_evidence(raw, envelopes)
        omission = evidence_ref is None
        quality_score: float | None = None
        if omission:
            score = 0.0
        else:
            quality_score = quality.get(item_id)
            if quality_score is not None:
                if quality_score < 0 or quality_score > max_score:
                    raise ValueError(f"quality_score_out_of_range:{item_id}")
                score = quality_score
            else:
                # Coverage-only mode: a covered item without a Score Skill
                # rating keeps its max (no basis to deduct). The raw quality
                # value stays visible as quality_score=null (proposal).
                score = max_score

        scored_items.append({
            "id": item_id,
            "label": label,
            "weight": float(weight),
            "score": score,
            "max": max_score,
            "evidence_ref": evidence_ref or "",
            "required": required,
            "omission": omission,
            "quality_score": quality_score,
        })

    required_items = [item for item in scored_items if item["required"]]
    required_all_passed = all(not item["omission"] for item in required_items)
    total_score = sum(item["score"] for item in scored_items)
    total_max = sum(item["max"] for item in scored_items)
    paper_threshold = paper.get("threshold")
    if threshold is None:
        threshold = (
            float(paper_threshold)
            if isinstance(paper_threshold, (int, float))
            else ADE_SCORE_DEFAULT_THRESHOLD
        )
    verdict = "PASS" if required_all_passed and total_score >= threshold else "FAIL"
    if verdict == "PASS":
        status = "pass"
    elif required_all_passed:
        status = "partial"  # coverage ok, quality below the line
    else:
        status = "fail"

    return {
        "status": status,
        "items": scored_items,
        "total": {
            "score": total_score,
            "max": total_max,
            "threshold": threshold,
        },
        "required_all_passed": required_all_passed,
        "verdict": verdict,
        "scored_at": scored_at or datetime.now(timezone.utc).isoformat(),
    }


def run_score(
    *,
    paper: dict[str, Any],
    report: dict[str, Any],
    quality_scores: dict[str, Any] | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Score CLI entry: map input errors to a fail contract + error field."""
    try:
        return score_assessment(
            paper,
            report,
            quality_scores=quality_scores,
            threshold=threshold,
        )
    except ValueError as exc:
        return {
            "status": "fail",
            "items": [],
            "total": {
                "score": 0.0,
                "max": 0.0,
                "threshold": float(threshold) if threshold is not None else ADE_SCORE_DEFAULT_THRESHOLD,
            },
            "required_all_passed": False,
            "verdict": "FAIL",
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
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

def _reconfigure_stdout_utf8() -> None:
    """Force UTF-8 on stdout before every JSON report exit.

    Console / pipe encoding follows the locale by default (GBK on zh-CN
    Windows), which corrupts ``ensure_ascii=False`` ADE reports for
    downstream parsers. ADE reports are machine contracts — they must
    always exit as UTF-8 regardless of the environment.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (rare); keep current encoding


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source_publish_check",
        description=(
            "TriCompany DCE CLI for source/support checks, agent live entry "
            "publishing, and manifest-driven project truth document sync."
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
        help="Execute sync for out_of_sync items (copy source -> support). Requires --check.",
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
        "--host",
        choices=tuple(HOST_RENDER_REGISTRY.keys()),
        default=DEFAULT_HOST_ID,
        help="ADE-B target host face for --publish-agents: 'copilot' publishes "
             "to .github/agents/ (default, current behaviour); 'claude' renders "
             "source + host template to .claude/agents/ (Claude Code face). "
             "Render metadata (renderTemplate/extraSections) on manifest "
             "liveEntries activates derived-consistency checks.",
    )
    parser.add_argument(
        "--employees",
        default=None,
        help="Comma-separated employee IDs to filter role-agent publish entries "
             "(e.g. 'ceo-chief-of-staff,chief-product-officer'). "
             "Only applies to --publish-agents mode.",
    )
    # ── project truth document ADE arguments ─────────────────────────────
    parser.add_argument(
        "--project-docs",
        action="store_true",
        default=False,
        help="Check manifest-driven project truth document sync (dry-run by default).",
    )
    parser.add_argument(
        "--project-docs-execute",
        action="store_true",
        default=False,
        help="When combined with --project-docs, execute validated document writes.",
    )
    parser.add_argument(
        "--project-docs-manifest",
        default=".github/manifests/project-source-doc-sync-manifest.json",
        help="Project document manifest path, absolute or relative to --source-root.",
    )
    parser.add_argument(
        "--workspace-root",
        default=None,
        help="Parent workspace containing project repositories. Defaults to --source-root parent.",
    )
    parser.add_argument(
        "--project-doc-ids",
        default=None,
        help="Comma-separated project document entry IDs to process.",
    )
    parser.add_argument(
        "--project-doc-candidate",
        action="append",
        default=[],
        metavar="ID=PATH",
        help="Planner-provided published-summary candidate. Repeat for multiple entries.",
    )
    # ── ADE phase 2: lifecycle skeleton (runId / Close CLI / Score CLI) ───
    parser.add_argument(
        "--run-id",
        default=None,
        help="Explicit ADE run id overriding the timestamp-derived default in "
             "every envelope emitted by this invocation. Single filesystem-safe "
             "token (letters, digits, '_', '.', '-'; max 128 chars).",
    )
    # Close CLI (spec §2.5 终态门)
    parser.add_argument(
        "--close",
        action="store_true",
        default=False,
        help="Close CLI: validate and persist the terminal state for --run-id. "
             "Writes the terminal audit record only after full validation; "
             "rejection emits CLOSE_REJECTED with a non-zero exit code.",
    )
    parser.add_argument(
        "--verdict",
        choices=ADE_CLOSE_VERDICTS,
        default=None,
        help="Close Skill terminal verdict (spec §8.3): "
             "APPROVED | FROZEN | ESCALATED | RETRY.",
    )
    parser.add_argument(
        "--evidence-ref",
        default=None,
        help="Close evidence reference: existing file path (absolute or "
             "relative to --source-root) or http(s)/file URL.",
    )
    parser.add_argument(
        "--source-revision",
        default=None,
        help="Source revision (e.g. git sha / tag) the close evidence was "
             "produced against. Non-empty single token.",
    )
    parser.add_argument(
        "--ade-data-dir",
        default=None,
        help="Directory for ADE runtime records (close terminal audit). "
             "Defaults to <source-root>/.ade/.",
    )
    # Score CLI (spec §2.6 / 试卷模板 §三)
    parser.add_argument(
        "--score",
        action="store_true",
        default=False,
        help="Score CLI: deterministic coverage check of a DCE/Verify report "
             "against an assessment paper test-set; emits the §三 评分合同.",
    )
    parser.add_argument(
        "--score-paper",
        default=None,
        metavar="PATH",
        help="Assessment paper JSON: {items:[{id,label,weight,max,required,"
             "verify_method,evidence_ref?}], threshold?}.",
    )
    parser.add_argument(
        "--score-report",
        default=None,
        metavar="PATH",
        help="DCE/Verify envelope JSON (bare envelope or combined reports "
             "container) to check coverage against.",
    )
    parser.add_argument(
        "--score-quality-scores",
        default=None,
        metavar="PATH",
        help="Score Skill quality scores JSON: {items:[{id,score}]} — "
             "semantic per-item ratings merged with the coverage check.",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=None,
        metavar="N",
        help="Total pass threshold override (default: paper threshold, "
             "then 80).",
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
        f"  Derived (ok):   {summary.derived_identical}",
        f"  Derived (drift): {summary.derived_drift}",
        f"  Errors:         {summary.errors}",
        "-" * 60,
    ]
    for item in report.items:
        icon = {
            "created": "✅",
            "updated": "🔄",
            "skipped_identical": "⏭️",
            "skipped_dry_run": "🔍",
            "derived_identical": "✅",
            "derived_drift": "⚠️",
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
    # Force UTF-8 before argparse touches stdout (--help / usage / errors can
    # exit before the JSON report exits; GBK default would corrupt --help
    # output and break UTF-8-consuming callers).
    _reconfigure_stdout_utf8()
    parser = build_parser()
    args = parser.parse_args()

    source_root = _normalize_path(args.source_root)
    support_root = _normalize_path(args.support_root)

    # ── ADE phase 2: explicit run id validation (wins over timestamp) ──────
    # Close mode skips the early rejection: run_close validates the id itself
    # and emits a full CLOSE_REJECTED envelope (spec §2.5, never silent).
    if args.run_id and not args.close:
        run_id_error = _validate_run_id(args.run_id)
        if run_id_error:
            print(f"error: invalid --run-id: {run_id_error}", file=sys.stderr)
            return 1
    explicit_run_id = args.run_id.strip() if args.run_id else None

    # ── ADE phase 2: Close CLI / Score CLI are exclusive lifecycle modes ───
    other_scopes = (
        args.check or args.sync or args.publish_agents or args.project_docs
    )
    if args.close and (other_scopes or args.score):
        print(
            "error: --close cannot be combined with other scope flags",
            file=sys.stderr,
        )
        return 1
    if args.score and (other_scopes or args.close):
        print(
            "error: --score cannot be combined with other scope flags",
            file=sys.stderr,
        )
        return 1

    # ── Close CLI (spec §2.5): validate → persist terminal state → report ──
    if args.close:
        env = run_close(
            run_id=args.run_id or "",
            verdict=args.verdict or "",
            evidence_ref=args.evidence_ref or "",
            source_revision=args.source_revision or "",
            source_root=source_root,
            ade_data_dir=args.ade_data_dir,
        )
        _reconfigure_stdout_utf8()
        json.dump(env, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0 if env["status"] == "pass" else 1

    # ── Score CLI (spec §2.6): coverage check + quality merge + 双门槛 ─────
    if args.score:
        paper = _load_json_safe(_normalize_path(args.score_paper)) if args.score_paper else None
        report = _load_json_safe(_normalize_path(args.score_report)) if args.score_report else None
        quality_scores = (
            _load_json_safe(_normalize_path(args.score_quality_scores))
            if args.score_quality_scores else None
        )
        input_errors: list[str] = []
        if paper is None:
            input_errors.append("paper_missing_or_invalid")
        if report is None:
            input_errors.append("report_missing_or_invalid")
        if args.score_quality_scores and quality_scores is None:
            input_errors.append("quality_scores_missing_or_invalid")
        if input_errors:
            contract = run_score(
                paper=paper or {"items": []},
                report=report or {"reports": []},
                quality_scores=quality_scores,
                threshold=args.score_threshold,
            )
            contract["error"] = ";".join(input_errors)
            _reconfigure_stdout_utf8()
            json.dump(contract, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
            return 1
        contract = run_score(
            paper=paper,
            report=report,
            quality_scores=quality_scores,
            threshold=args.score_threshold,
        )
        _reconfigure_stdout_utf8()
        json.dump(contract, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0 if contract.get("verdict") == "PASS" else 1

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
    if args.project_docs_execute and not args.project_docs:
        print(
            "error: --project-docs-execute requires --project-docs",
            file=sys.stderr,
        )
        return 1
    if args.project_doc_candidate and not args.project_docs:
        print(
            "error: --project-doc-candidate requires --project-docs",
            file=sys.stderr,
        )
        return 1

    sync_result: dict[str, Any] | None = None
    change_summary: dict[str, Any] | None = None
    # ADE phase 1: every scope serializes to one unified envelope; combined
    # runs (e.g. --check --publish-agents) collect them into a reports list.
    envelopes: list[dict[str, Any]] = []
    exit_code = 0

    # ── project truth document ADE mode ──────────────────────────────────
    if args.project_docs:
        workspace_root = _normalize_path(
            args.workspace_root if args.workspace_root else source_root.parent
        )
        project_manifest = Path(args.project_docs_manifest)
        if not project_manifest.is_absolute():
            project_manifest = source_root / project_manifest

        project_doc_ids: tuple[str, ...] | None = None
        if args.project_doc_ids:
            project_doc_ids = tuple(
                entry_id.strip()
                for entry_id in args.project_doc_ids.split(",")
                if entry_id.strip()
            ) or None

        candidate_overrides: dict[str, str] = {}
        for candidate_arg in args.project_doc_candidate:
            if "=" not in candidate_arg:
                print(
                    "error: --project-doc-candidate must use ID=PATH",
                    file=sys.stderr,
                )
                return 1
            entry_id, candidate_path = candidate_arg.split("=", 1)
            entry_id = entry_id.strip()
            candidate_path = candidate_path.strip()
            if not entry_id or not candidate_path:
                print(
                    "error: --project-doc-candidate must use non-empty ID=PATH",
                    file=sys.stderr,
                )
                return 1
            candidate_overrides[entry_id] = candidate_path

        pd_report = run_project_doc_sync(
            manifest_path=project_manifest,
            workspace_root=workspace_root,
            execute=args.project_docs_execute,
            entry_ids=project_doc_ids,
            candidate_overrides=candidate_overrides,
        )
        envelopes.append(_serialize_project_doc_sync_report(
            pd_report, run_id=explicit_run_id,
        ))
        if pd_report.status == "fail":
            exit_code = 1

    # ── --publish-agents mode (can run with or without --check) ────────────
    if args.publish_agents:
        dry_run = not args.agent_execute
        ap_report = run_agent_publish(
            source_root=source_root,
            support_root=support_root,
            employee_ids=employee_ids,
            dry_run=dry_run,
            host_id=args.host,
        )
        envelopes.append(_serialize_agent_publish_report(
            ap_report, run_id=explicit_run_id,
        ))
        # ADE phase 0 observation item: errors (incl. protected_target_rejected)
        # map to a non-zero exit code, aligned with project-docs.
        if ap_report.summary.errors > 0:
            exit_code = 1
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
            change_summary = {
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

        # ADE phase 1: sync scope envelope
        scope_report = None
        if args.scope:
            scope_report = {
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
        envelopes.append(_serialize_sync_report(
            report,
            sync_result=sync_result,
            change_summary=change_summary,
            scope_report=scope_report,
            run_id=explicit_run_id,
        ))
        # ADE phase 1 rc mapping: sync execute errors also exit non-zero.
        if sync_result and len(sync_result.get("errors", [])) > 0:
            exit_code = 1
    else:
        if args.sync:
            print(
                "error: --sync requires --check to be set",
                file=sys.stderr,
            )
            return 1

    # ── no scope ran: emit an empty sync envelope shell (backward-compatible) ─
    if not envelopes:
        report = SyncReport(
            check_time=datetime.now(timezone.utc).isoformat(),
            source_root=source_root.as_posix(),
            support_root=support_root.as_posix(),
        )
        envelopes.append(_serialize_sync_report(
            report, run_id=explicit_run_id,
        ))

    # Serialise to JSON: a single envelope for one scope, an aggregated
    # reports container for combined runs (e.g. --check --publish-agents).
    if len(envelopes) == 1:
        output: dict[str, Any] = envelopes[0]
    else:
        output = _serialize_combined_container(
            envelopes, run_id=explicit_run_id,
        )

    _reconfigure_stdout_utf8()
    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
