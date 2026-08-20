"""
B5: source_publish_check validation tests.

Test framework for the source_publish_check CLI (B1).
Designed to run independently — unit tests for comparison logic
execute now; integration tests auto-skip until B1 skeleton lands.

Coverage:
  TC1  --help executable
  TC2  No-args usage output
  TC3  --check produces valid JSON
  TC4  --format json produces parseable JSON
  TC5  out_of_sync detection
  TC6  all-in-sync clean report
  TC7  exclusion rules (employee five-piece kit, live entry, binding profiles)
    AP   agent live entry dry-run, execute, filtering, and safety
    PD   project document copy/summary, candidate, audit, and path safety
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ── module discovery ──────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(_REPO_ROOT))

# Try to import the actual CLI module; used to decide skip behaviour.
_MODULE_PATH = _REPO_ROOT / "runtime" / "cognition" / "source_publish_check.py"
_HAS_CLI_MODULE = _MODULE_PATH.exists()

# ── exclusion helpers (CPO hard constraints) ──────────────────────────────────

# Paths / patterns that must NOT appear in the sync scope.
EXCLUDED_PATTERNS: Set[str] = {
    ".github/binding-profiles",
    ".github/agents",
    ".tricompany-cognition/employee",
    ".tricompany-cognition/org/audit",
    ".tricompany-cognition/org/shared",
    # employee five-piece kit suffixes
    "memory.md",
    "colleagues.md",
    "social.md",
    "soul.md",
    "body.md",
    # live entry markers
    "live-entry",
    "binding-profiles",
}


def _is_excluded(relative_path: str) -> bool:
    """Return True when *relative_path* falls inside an excluded scope."""
    rp = relative_path.replace("\\", "/")
    for pattern in EXCLUDED_PATTERNS:
        if pattern.replace("\\", "/") in rp:
            return True
    return False


# ── file-comparison primitives (unit-testable without CLI) ────────────────────


def _file_sha256(file_path: Path) -> str:
    """SHA-256 hex digest of *file_path*."""
    h = hashlib.sha256()
    h.update(file_path.read_bytes())
    return h.hexdigest()


def _tree_manifest(tree_root: Path) -> Dict[str, str]:
    """
    Walk *tree_root*, returning {relative_path: sha256}.
    Excluded paths are omitted.
    """
    manifest: Dict[str, str] = {}
    for fpath in tree_root.rglob("*"):
        if not fpath.is_file():
            continue
        rel = str(fpath.relative_to(tree_root)).replace("\\", "/")
        if _is_excluded(rel):
            continue
        manifest[rel] = _file_sha256(fpath)
    return manifest


def compare_trees(
    source_root: Path, support_root: Path
) -> Dict[str, Any]:
    """
    Simulate the core comparison logic of source_publish_check.

    Returns a dict matching the CLI JSON contract:
      {check_time, source_root, support_root,
       out_of_sync, in_sync, gaps, summary}
    """
    from datetime import datetime, timezone

    source_manifest = _tree_manifest(source_root)
    support_manifest = _tree_manifest(support_root)

    out_of_sync: List[str] = []
    in_sync: List[str] = []
    gaps: List[str] = []

    # Files that exist in both trees — compare hashes; files in source only = gap
    all_files = set(source_manifest.keys()) | set(support_manifest.keys())

    for rel in sorted(all_files):
        in_source = rel in source_manifest
        in_support = rel in support_manifest

        if in_source and in_support:
            if source_manifest[rel] == support_manifest[rel]:
                in_sync.append(rel)
            else:
                out_of_sync.append(rel)
        elif in_source and not in_support:
            gaps.append(rel)
        # support-only files are ignored (not in sync scope per CPO)

    return {
        "check_time": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "support_root": str(support_root),
        "out_of_sync": out_of_sync,
        "in_sync": in_sync,
        "gaps": gaps,
        "summary": {
            "total": len(out_of_sync) + len(in_sync) + len(gaps),
            "out_of_sync": len(out_of_sync),
            "in_sync": len(in_sync),
            "gaps": len(gaps),
        },
    }


# ── fixture builder ───────────────────────────────────────────────────────────


class TreeFixture:
    """Build temporary source / support tree fixtures for testing."""

    def __init__(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)

    def cleanup(self) -> None:
        self._td.cleanup()

    def write(self, relative_path: str, content: str) -> Path:
        fp = self.root / relative_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        return fp

    def subdir(self, name: str) -> "TreeFixture":
        """Return a fixture rooted at a subdirectory."""
        sub = TreeFixture.__new__(TreeFixture)
        sub._td = self._td  # share lifecycle
        sub.root = self.root / name
        sub.root.mkdir(parents=True, exist_ok=True)
        return sub


# ── tests ─────────────────────────────────────────────────────────────────────


def _cli_base_args(source_root: str, support_root: str) -> List[str]:
    return [
        sys.executable,
        "-m",
        "runtime.cognition.source_publish_check",
        "--source-root",
        source_root,
        "--support-root",
        support_root,
    ]


# ──────────────────────────── comparison logic ────────────────────────────────


class ComparisonLogicTests(unittest.TestCase):
    """Unit tests for tree comparison: no CLI dependency."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    # ── TC6: all-in-sync ──────────────────────────────────────────────────────

    def test_all_in_sync_reports_clean(self) -> None:
        """TC6: identical source and support trees → clean report."""
        content = "# Registry\n"
        self.source.write("docs/registry/code-state.md", content)
        self.support.write("docs/registry/code-state.md", content)

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["total"], 1)
        self.assertEqual(result["summary"]["in_sync"], 1)
        self.assertEqual(result["summary"]["out_of_sync"], 0)
        self.assertEqual(result["summary"]["gaps"], 0)
        self.assertEqual(result["in_sync"], ["docs/registry/code-state.md"])
        self.assertEqual(result["out_of_sync"], [])
        self.assertEqual(result["gaps"], [])

    # ── TC5: out_of_sync detection ────────────────────────────────────────────

    def test_out_of_sync_detected_when_content_differs(self) -> None:
        """TC5: file present in both trees but content differs → out_of_sync."""
        self.source.write("docs/registry/code-state.md", "v1")
        self.support.write("docs/registry/code-state.md", "v2")

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["out_of_sync"], 1)
        self.assertEqual(result["summary"]["in_sync"], 0)
        self.assertEqual(result["out_of_sync"], ["docs/registry/code-state.md"])

    def test_out_of_sync_multiple_files(self) -> None:
        """Multiple out_of_sync files reported correctly."""
        self.source.write("docs/a.md", "A1")
        self.support.write("docs/a.md", "A2")
        self.source.write("docs/b.md", "B1")
        self.support.write("docs/b.md", "B2")
        # one in-sync to confirm mixed
        self.source.write("docs/c.md", "same")
        self.support.write("docs/c.md", "same")

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["total"], 3)
        self.assertEqual(result["summary"]["out_of_sync"], 2)
        self.assertEqual(result["summary"]["in_sync"], 1)
        self.assertEqual(sorted(result["out_of_sync"]), ["docs/a.md", "docs/b.md"])

    # ── TC7: exclusion rules ──────────────────────────────────────────────────

    def test_binding_profiles_excluded(self) -> None:
        """TC7: .github/binding-profiles/* is excluded from sync."""
        self.source.write(".github/binding-profiles/test-engineer.json", "bp")
        self.support.write(".github/binding-profiles/test-engineer.json", "bp")
        self.source.write("docs/registry/code-state.md", "ok")
        self.support.write("docs/registry/code-state.md", "ok")

        result = compare_trees(self.source.root, self.support.root)
        # binding-profiles excluded; only docs/registry/code-state.md counted
        self.assertEqual(result["summary"]["total"], 1)
        self.assertNotIn(
            ".github/binding-profiles/test-engineer.json", result["in_sync"]
        )

    def test_employee_five_piece_kit_excluded(self) -> None:
        """TC7: employee memory/colleagues/social/soul/body excluded."""
        for kit_file in [
            "employee/memory.md",
            "employee/colleagues.md",
            "employee/social.md",
            "employee/soul.md",
            "employee/body.md",
        ]:
            self.source.write(kit_file, "kit")
            self.support.write(kit_file, "kit")
        self.source.write("docs/readme.md", "ok")
        self.support.write("docs/readme.md", "ok")

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["total"], 1, "Only docs/readme.md counted")
        self.assertEqual(result["in_sync"], ["docs/readme.md"])

    def test_employee_private_cognition_excluded(self) -> None:
        """TC7: .tricompany-cognition/employee/* excluded."""
        self.source.write(".tricompany-cognition/employee/ceo-chief-of-staff.md", "e")
        self.support.write(".tricompany-cognition/employee/ceo-chief-of-staff.md", "e")
        self.source.write("docs/registry/code-state.md", "ok")
        self.support.write("docs/registry/code-state.md", "ok")

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["total"], 1)

    # ── gaps ──────────────────────────────────────────────────────────────────

    def test_gaps_reported_for_source_only_files(self) -> None:
        """Files only in source tree → gaps."""
        self.source.write("docs/new-file.md", "new")
        # not in support

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["gaps"], 1)
        self.assertEqual(result["gaps"], ["docs/new-file.md"])

    # ── JSON contract validity ────────────────────────────────────────────────

    def test_result_matches_cli_json_contract(self) -> None:
        """Result dict has all required keys with expected types."""
        self.source.write("docs/x.md", "x")
        self.support.write("docs/x.md", "x")
        result = compare_trees(self.source.root, self.support.root)

        required_keys = {
            "check_time",
            "source_root",
            "support_root",
            "out_of_sync",
            "in_sync",
            "gaps",
            "summary",
        }
        self.assertTrue(required_keys.issubset(set(result.keys())))

        self.assertIsInstance(result["check_time"], str)
        self.assertIsInstance(result["source_root"], str)
        self.assertIsInstance(result["support_root"], str)
        self.assertIsInstance(result["out_of_sync"], list)
        self.assertIsInstance(result["in_sync"], list)
        self.assertIsInstance(result["gaps"], list)
        self.assertIsInstance(result["summary"], dict)

        summary = result["summary"]
        for key in ("total", "out_of_sync", "in_sync", "gaps"):
            self.assertIsInstance(summary[key], int)

    # ── registries included ───────────────────────────────────────────────────

    def test_source_agents_registries_in_scope(self) -> None:
        """Registries under source-agents/registries ARE in sync scope."""
        content = "registry content"
        self.source.write(
            "source-agents/registries/TriCompanyCodeRegistry.agent.md",
            content,
        )
        self.support.write(
            "source-agents/registries/TriCompanyCodeRegistry.agent.md",
            content,
        )

        result = compare_trees(self.source.root, self.support.root)
        self.assertEqual(result["summary"]["total"], 1)
        self.assertEqual(result["summary"]["in_sync"], 1)


# ─────────────────────── integration tests (CLI) ──────────────────────────────


@unittest.skipUnless(_HAS_CLI_MODULE, "source_publish_check.py not yet implemented")
class CLIIntegrationTests(unittest.TestCase):
    """End-to-end tests that invoke the actual CLI process."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _run_cli(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        args = _cli_base_args(str(self.source.root), str(self.support.root))
        args.extend(extra_args)
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
        )

    # ── TC1: --help ───────────────────────────────────────────────────────────

    def test_help_executable(self) -> None:
        """TC1: --help exits 0 and prints usage."""
        proc = self._run_cli("--help")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        self.assertIn("usage", (proc.stdout + proc.stderr).lower())

    # ── TC2: no-args ──────────────────────────────────────────────────────────

    def test_no_args_outputs_valid_json(self) -> None:
        """TC2: running with zero arguments uses defaults and outputs valid JSON."""
        proc = subprocess.run(
            [sys.executable, "-m", "runtime.cognition.source_publish_check"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
        )
        # Exit 0 is acceptable: --source-root and --support-root have defaults
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"No-args stdout is not valid JSON: {exc}")
        self.assertEqual(data["protocol"], "ade-report")
        self.assertEqual(data["scope"], "sync")
        self.assertIn("summary", data)
        self.assertIn("source_root", data["scope_specific"])

    # ── TC3: --check JSON ─────────────────────────────────────────────────────

    def test_check_outputs_valid_json(self) -> None:
        """TC3: --check produces valid JSON on stdout."""
        self.source.write("docs/a.md", "content-a")
        self.support.write("docs/a.md", "content-a")

        proc = self._run_cli("--check")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"stdout is not valid JSON: {exc}")

        # Unified ADE envelope contract keys
        for key in (
            "protocol",
            "version",
            "scope",
            "run_id",
            "mode",
            "check_time",
            "status",
            "summary",
            "items",
            "scope_specific",
        ):
            self.assertIn(key, data, f"Missing key: {key}")

    # ── TC4: --format json ────────────────────────────────────────────────────

    def test_format_json_outputs_parseable_json(self) -> None:
        """TC4: --format json produces valid, parseable JSON."""
        self.source.write("docs/a.md", "content-a")
        self.support.write("docs/a.md", "content-a")

        proc = self._run_cli("--check", "--format", "json")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"stdout not parseable: {exc}")
        self.assertIsInstance(data, dict)


# ── Q3 Phase 2: agent publish tests ──────────────────────────────────────────


class AgentPublishUnitTests(unittest.TestCase):
    """Unit tests for agent publish core logic (no CLI dependency)."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _make_minimal_manifest(self, entries: list) -> str:
        """Build a minimal publish manifest JSON string."""
        import json
        return json.dumps({
            "manifestId": "test-v0.1",
            "date": "2026-07-24",
            "liveEntries": entries,
        })

    def _write_manifest(self, entries: list) -> None:
        """Write a minimal manifest to the source fixture."""
        self.source.write(
            "source-agents/registries/trimetaverse-live-agent-publish-manifest.json",
            self._make_minimal_manifest(entries),
        )

    def _write_agent_source(self, rel_dir: str, agent_id: str, content: str = "agent content v1") -> None:
        """Write a source agent file."""
        self.source.write(f"source-agents/{rel_dir}/{agent_id}.agent.md", content)

    def _write_agent_target(self, target_rel: str, content: str = "old content") -> None:
        """Write a target agent file on the support side."""
        self.support.write(target_rel, content)

    # ── TC-AP1: manifest filter (eligible statuses) ──────────────────────────

    def test_filter_eligible_statuses(self) -> None:
        """TC-AP1: Only source-published-live-entry and current-copilot-host-live pass filter."""
        from runtime.cognition.source_publish_check import (
            _filter_agent_publish_entries,
            _load_publish_manifest,
        )
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
            {"status": "source-published-live-entry", "source": "TriCompany/source-agents/registries/reg.agent.md", "target": "TriMetaverse/.github/agents/reg.agent.md", "kind": "registry-or-governance-agent"},
            {"status": "migrated-module-local-live-entry", "source": "TriDev/.github/agents/dev.agent.md", "target": "TriDev/.github/agents/dev.agent.md", "kind": "module-registry-agent"},
            {"status": "module-local-live-entry", "source": "TriCompany/source-agents/registries/foo.agent.md", "target": "TriCompany/.github/agents/foo.agent.md", "kind": "module-orchestrator-agent"},
        ]
        manifest = {"liveEntries": entries}
        filtered = _filter_agent_publish_entries(manifest)
        self.assertEqual(len(filtered), 2)
        for f in filtered:
            self.assertIn(f["status"], ("current-copilot-host-live", "source-published-live-entry"))

    # ── TC-AP2: --employees filter ───────────────────────────────────────────

    def test_employees_filter_only_role_agents(self) -> None:
        """TC-AP2: --employees filter selects only role-agent kind."""
        from runtime.cognition.source_publish_check import _filter_agent_publish_entries
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriM/.github/agents/ceo.agent.md", "kind": "role-agent"},
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/cto/cto.agent.md", "target": "TriM/.github/agents/cto.agent.md", "kind": "role-agent"},
            {"status": "source-published-live-entry", "source": "TriCompany/source-agents/registries/reg.agent.md", "target": "TriM/.github/agents/reg.agent.md", "kind": "registry-or-governance-agent"},
        ]
        manifest = {"liveEntries": entries}
        filtered = _filter_agent_publish_entries(manifest, employee_ids=("ceo",))
        self.assertEqual(len(filtered), 1)
        self.assertIn("ceo", filtered[0]["source"])

    def test_employees_filter_multiple(self) -> None:
        """TC-AP2: --employees filter supports multiple IDs."""
        from runtime.cognition.source_publish_check import _filter_agent_publish_entries
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriM/.github/agents/ceo.agent.md", "kind": "role-agent"},
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/cto/cto.agent.md", "target": "TriM/.github/agents/cto.agent.md", "kind": "role-agent"},
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/cfo/cfo.agent.md", "target": "TriM/.github/agents/cfo.agent.md", "kind": "role-agent"},
        ]
        manifest = {"liveEntries": entries}
        filtered = _filter_agent_publish_entries(manifest, employee_ids=("ceo", "cfo"))
        self.assertEqual(len(filtered), 2)

    # ── TC-AP3: source path resolution ──────────────────────────────────────

    def test_source_path_resolution_strips_prefix(self) -> None:
        """TC-AP3: Source path with TriCompany/ prefix resolves correctly."""
        from runtime.cognition.source_publish_check import _resolve_agent_source_path
        self._write_agent_source("ceo", "ceo")
        path = _resolve_agent_source_path(
            self.source.root,
            "TriCompany/source-agents/ceo/ceo.agent.md",
        )
        self.assertIsNotNone(path)
        self.assertTrue(path.is_file())

    def test_source_path_resolution_file_not_found(self) -> None:
        """TC-AP3: Non-existent source returns None."""
        from runtime.cognition.source_publish_check import _resolve_agent_source_path
        path = _resolve_agent_source_path(
            self.source.root,
            "TriCompany/source-agents/ghost/ghost.agent.md",
        )
        self.assertIsNone(path)

    # ── TC-AP4: target path resolution ──────────────────────────────────────

    def test_target_path_resolution_strips_prefix(self) -> None:
        """TC-AP4: Target path with TriMetaverse/ prefix resolves correctly."""
        from runtime.cognition.source_publish_check import _resolve_agent_target_path
        path, err = _resolve_agent_target_path(
            self.support.root,
            "TriMetaverse/.github/agents/ceo.agent.md",
        )
        self.assertEqual(err, "")
        self.assertEqual(
            path,
            (self.support.root / ".github" / "agents" / "ceo.agent.md").resolve(),
        )

    def test_target_path_resolution_escape_rejected(self) -> None:
        """TC-AP4: Parent-dir traversal resolving outside support_root is rejected."""
        from runtime.cognition.source_publish_check import _resolve_agent_target_path
        path, err = _resolve_agent_target_path(
            self.support.root,
            "TriMetaverse/../escaped-outside.md",
        )
        self.assertIsNone(path)
        self.assertEqual(err, "outside_workspace")

    def test_target_path_resolution_absolute_rejected(self) -> None:
        """TC-AP4: Absolute target paths are rejected outright."""
        from runtime.cognition.source_publish_check import _resolve_agent_target_path
        # os.path.abspath gives a drive/root absolute path on every platform
        # (C:\\... on Windows, /... on POSIX) — is_absolute() is guaranteed.
        absolute_target = os.path.abspath("absolute-evil.agent.md")
        path, err = _resolve_agent_target_path(
            self.support.root,
            absolute_target,
        )
        self.assertIsNone(path)
        self.assertEqual(err, "absolute_path_not_allowed")

    def test_target_path_resolution_missing_rejected(self) -> None:
        """TC-AP4: Empty target strings are rejected."""
        from runtime.cognition.source_publish_check import _resolve_agent_target_path
        path, err = _resolve_agent_target_path(self.support.root, "")
        self.assertIsNone(path)
        self.assertEqual(err, "path_missing")

    # ── TC-AP5: _publish_single_agent creates when target missing (dry-run) ──

    def test_publish_single_agent_create_dry_run(self) -> None:
        """TC-AP5: When target is missing and dry_run=True, action=skipped_dry_run."""
        from runtime.cognition.source_publish_check import _publish_single_agent
        self._write_agent_source("ceo", "ceo", "new content")
        source_file = self.source.root / "source-agents" / "ceo" / "ceo.agent.md"
        target_file = self.support.root / ".github" / "agents" / "ceo.agent.md"

        result = _publish_single_agent(
            source_file, target_file,
            {"source": "TriCompany/source-agents/ceo/ceo.agent.md",
             "target": "TriMetaverse/.github/agents/ceo.agent.md",
             "kind": "role-agent", "status": "current-copilot-host-live"},
            dry_run=True,
        )
        self.assertEqual(result.action, "skipped_dry_run")
        self.assertFalse(target_file.exists(), "dry-run must not create file")

    # ── TC-AP6: _publish_single_agent identical skips ────────────────────────

    def test_publish_single_agent_identical_skips(self) -> None:
        """TC-AP6: When source and target are identical, action=skipped_identical."""
        from runtime.cognition.source_publish_check import _publish_single_agent
        content = "same content"
        self._write_agent_source("ceo", "ceo", content)
        self._write_agent_target(".github/agents/ceo.agent.md", content)

        source_file = self.source.root / "source-agents" / "ceo" / "ceo.agent.md"
        target_file = self.support.root / ".github" / "agents" / "ceo.agent.md"

        result = _publish_single_agent(
            source_file, target_file,
            {"source": "TriCompany/source-agents/ceo/ceo.agent.md",
             "target": "TriMetaverse/.github/agents/ceo.agent.md",
             "kind": "role-agent", "status": "current-copilot-host-live"},
            dry_run=True,
        )
        self.assertEqual(result.action, "skipped_identical")

    # ── TC-AP7: _publish_single_agent update dry-run ─────────────────────────

    def test_publish_single_agent_update_dry_run(self) -> None:
        """TC-AP7: When hashes differ and dry_run=True, action=skipped_dry_run."""
        from runtime.cognition.source_publish_check import _publish_single_agent
        self._write_agent_source("ceo", "ceo", "new content")
        self._write_agent_target(".github/agents/ceo.agent.md", "old content")

        source_file = self.source.root / "source-agents" / "ceo" / "ceo.agent.md"
        target_file = self.support.root / ".github" / "agents" / "ceo.agent.md"

        result = _publish_single_agent(
            source_file, target_file,
            {"source": "TriCompany/source-agents/ceo/ceo.agent.md",
             "target": "TriMetaverse/.github/agents/ceo.agent.md",
             "kind": "role-agent", "status": "current-copilot-host-live"},
            dry_run=True,
        )
        self.assertEqual(result.action, "skipped_dry_run")
        # verify target was NOT overwritten
        self.assertEqual(target_file.read_text(encoding="utf-8"), "old content")

    # ── TC-AP8: _publish_single_agent actually creates (execute mode) ────────

    def test_publish_single_agent_create_execute(self) -> None:
        """TC-AP8: When target missing and dry_run=False, file is created."""
        from runtime.cognition.source_publish_check import _publish_single_agent
        content = "brand new agent"
        self._write_agent_source("ceo", "ceo", content)
        source_file = self.source.root / "source-agents" / "ceo" / "ceo.agent.md"
        target_file = self.support.root / ".github" / "agents" / "ceo.agent.md"

        result = _publish_single_agent(
            source_file, target_file,
            {"source": "TriCompany/source-agents/ceo/ceo.agent.md",
             "target": "TriMetaverse/.github/agents/ceo.agent.md",
             "kind": "role-agent", "status": "current-copilot-host-live"},
            dry_run=False,
        )
        self.assertEqual(result.action, "created")
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(encoding="utf-8"), content)

    # ── TC-AP9: _publish_single_agent actually updates (execute mode) ────────

    def test_publish_single_agent_update_execute(self) -> None:
        """TC-AP9: When hashes differ and dry_run=False, file is updated."""
        from runtime.cognition.source_publish_check import _publish_single_agent
        new_content = "updated content"
        old_content = "old content"
        self._write_agent_source("ceo", "ceo", new_content)
        self._write_agent_target(".github/agents/ceo.agent.md", old_content)

        source_file = self.source.root / "source-agents" / "ceo" / "ceo.agent.md"
        target_file = self.support.root / ".github" / "agents" / "ceo.agent.md"

        result = _publish_single_agent(
            source_file, target_file,
            {"source": "TriCompany/source-agents/ceo/ceo.agent.md",
             "target": "TriMetaverse/.github/agents/ceo.agent.md",
             "kind": "role-agent", "status": "current-copilot-host-live"},
            dry_run=False,
        )
        self.assertEqual(result.action, "updated")
        self.assertEqual(target_file.read_text(encoding="utf-8"), new_content)

    # ── TC-AP10: run_agent_publish returns correct structure ─────────────────

    def test_run_agent_publish_structure(self) -> None:
        """TC-AP10: run_agent_publish returns AgentPublishReport with expected fields."""
        from runtime.cognition.source_publish_check import run_agent_publish
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "test content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=True)
        self.assertEqual(report.summary.total, 1)
        self.assertEqual(report.summary.skipped_dry_run, 1)
        self.assertTrue(report.dry_run)

    # ── TC-AP11: manifest missing produces error ─────────────────────────────

    def test_run_agent_publish_missing_manifest(self) -> None:
        """TC-AP11: When manifest is missing, report has 1 error."""
        from runtime.cognition.source_publish_check import run_agent_publish
        report = run_agent_publish(self.source.root, self.support.root, dry_run=True)
        self.assertEqual(report.summary.total, 1)
        self.assertEqual(report.summary.errors, 1)

    # ── TC-AP12: allowed targets derived from manifest ───────────────────────

    def test_derive_allowed_agent_targets(self) -> None:
        """TC-AP12: Only eligible status entries contribute to allowed targets."""
        from runtime.cognition.source_publish_check import _derive_allowed_agent_targets
        entries = [
            {"status": "current-copilot-host-live", "target": "TriMetaverse/.github/agents/a.agent.md", "kind": "role-agent"},
            {"status": "source-published-live-entry", "target": "TriMetaverse/.github/agents/b.agent.md", "kind": "registry-or-governance-agent"},
            {"status": "migrated-module-local-live-entry", "target": "TriDev/.github/agents/c.agent.md", "kind": "module-registry-agent"},
        ]
        manifest = {"liveEntries": entries}
        allowed = _derive_allowed_agent_targets(manifest)
        self.assertEqual(len(allowed), 2)
        self.assertIn("TriMetaverse/.github/agents/a.agent.md", allowed)
        self.assertIn("TriMetaverse/.github/agents/b.agent.md", allowed)
        self.assertNotIn("TriDev/.github/agents/c.agent.md", allowed)

    # ── TC-AP13: source not found produces error ─────────────────────────────

    def test_run_agent_publish_source_not_found(self) -> None:
        """TC-AP13: Entry with missing source file produces error item."""
        from runtime.cognition.source_publish_check import run_agent_publish
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ghost/ghost.agent.md", "target": "TriMetaverse/.github/agents/ghost.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        # do NOT write the source file

        report = run_agent_publish(self.source.root, self.support.root, dry_run=True)
        self.assertEqual(report.summary.total, 1)
        self.assertEqual(report.summary.errors, 1)
        self.assertEqual(report.items[0].action, "error")
        self.assertIn("source_file_not_found", report.items[0].error)

    # ── TC-AP14: whitelist ∩ protected zone = ∅ hard check (ADE fix 2) ──────

    def test_whitelist_target_in_binding_profiles_zone_is_rejected(self) -> None:
        """TC-AP14: Manifest target inside .github/binding-profiles/ rejects the
        whole run even in execute mode — nothing is written, nothing skipped."""
        from runtime.cognition.source_publish_check import run_agent_publish
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/binding-profiles/evil.json", "kind": "role-agent"},
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=False)
        self.assertEqual(report.summary.errors, 1)
        self.assertEqual(report.summary.created, 0)
        self.assertEqual(report.summary.updated, 0)
        self.assertEqual(report.items[0].action, "error")
        self.assertEqual(report.items[0].error, "protected_target_rejected")
        self.assertFalse(
            (self.support.root / ".github" / "binding-profiles" / "evil.json").exists(),
            "execute mode must not write protected targets",
        )
        self.assertFalse(
            (self.support.root / ".github" / "agents" / "ceo.agent.md").exists(),
            "whole run rejected: even the legitimate entry must not be written",
        )

    def test_whitelist_target_with_employee_kit_suffix_is_rejected(self) -> None:
        """TC-AP14: A whitelist target ending in an employee kit suffix is a
        protected-zone violation even inside the live-entry landing zone."""
        from runtime.cognition.source_publish_check import run_agent_publish
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.soul.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=False)
        self.assertEqual(report.summary.errors, 1)
        self.assertEqual(report.items[0].error, "protected_target_rejected")
        self.assertFalse(
            (self.support.root / ".github" / "agents" / "ceo.soul.md").exists()
        )

    def test_live_entry_landing_zone_is_still_allowed(self) -> None:
        """TC-AP14: Legitimate .github/agents/ targets pass the reverse check."""
        from runtime.cognition.source_publish_check import run_agent_publish
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=False)
        self.assertEqual(report.summary.errors, 0)
        self.assertEqual(report.summary.created, 1)
        self.assertTrue(
            (self.support.root / ".github" / "agents" / "ceo.agent.md").is_file()
        )

    def test_escape_target_rejected_in_execute_mode(self) -> None:
        """TC-AP14: Parent-dir escape target rejects the whole run in execute
        mode — nothing escapes support_root, nothing gets written at all."""
        from runtime.cognition.source_publish_check import run_agent_publish
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/../escaped-outside.md", "kind": "role-agent"},
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=False)
        self.assertEqual(report.summary.errors, 1)
        self.assertEqual(report.summary.created, 0)
        self.assertEqual(report.items[0].action, "error")
        self.assertEqual(report.items[0].error, "protected_target_rejected")
        self.assertFalse(
            (self.support.root.parent / "escaped-outside.md").exists(),
            "execute mode must not write outside support_root",
        )
        self.assertFalse(
            (self.support.root / ".github" / "agents" / "ceo.agent.md").exists(),
            "whole run rejected: the legitimate entry must not be written either",
        )

    def test_absolute_path_target_rejected_in_execute_mode(self) -> None:
        """TC-AP14: An absolute-path manifest target rejects the whole run."""
        from runtime.cognition.source_publish_check import run_agent_publish
        absolute_target = os.path.abspath("absolute-evil.agent.md")
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": absolute_target, "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=False)
        self.assertEqual(report.summary.errors, 1)
        self.assertEqual(report.items[0].error, "protected_target_rejected")
        self.assertFalse(Path(absolute_target).exists(), "absolute target must not be written")

    # ── TC-AP15: audit trail (before/after + timestamp) ─────────────────────

    def test_agent_publish_audit_changes_before_after(self) -> None:
        """TC-AP15: Serialized report carries changes audit with before/after
        hashes; skipped/error items are not part of the changes list."""
        import hashlib
        from runtime.cognition.source_publish_check import (
            _serialize_agent_publish_report,
            run_agent_publish,
        )
        content = "audited content"
        old_content = "old content"
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", content)
        self._write_agent_target(".github/agents/ceo.agent.md", old_content)

        report = run_agent_publish(self.source.root, self.support.root, dry_run=False)
        serialized = _serialize_agent_publish_report(report)
        changed_items = [
            item for item in serialized["items"] if item["action"] == "updated"
        ]
        self.assertEqual(len(changed_items), 1)
        change = changed_items[0]
        self.assertEqual(change["action"], "updated")
        self.assertEqual(change["before_hash"], hashlib.sha256(old_content.encode()).hexdigest())
        self.assertEqual(change["after_hash"], hashlib.sha256(content.encode()).hexdigest())
        # timestamp lives at envelope level (same contract as check_time)
        self.assertIn("check_time", serialized)

    def test_agent_publish_dry_run_has_empty_audit_changes(self) -> None:
        """TC-AP15: Dry-run writes nothing, so the audit changes list is empty."""
        from runtime.cognition.source_publish_check import (
            _serialize_agent_publish_report,
            run_agent_publish,
        )
        entries = [
            {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
        ]
        self._write_manifest(entries)
        self._write_agent_source("ceo", "ceo", "content")

        report = run_agent_publish(self.source.root, self.support.root, dry_run=True)
        serialized = _serialize_agent_publish_report(report)
        self.assertEqual(
            [
                item for item in serialized["items"]
                if item["action"] in ("created", "updated")
            ],
            [],
        )
        self.assertTrue(serialized["scope_specific"]["dry_run"])


@unittest.skipUnless(_HAS_CLI_MODULE, "source_publish_check.py not yet implemented")
class AgentPublishCLITests(unittest.TestCase):
    """CLI integration tests for --publish-agents mode."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()
        self._write_manifest_with_agent()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _write_manifest_with_agent(self) -> None:
        """Write a minimal manifest with one role-agent entry and the source file."""
        import json
        manifest = {
            "manifestId": "test-v0.1",
            "liveEntries": [
                {"status": "current-copilot-host-live", "source": "TriCompany/source-agents/ceo/ceo.agent.md", "target": "TriMetaverse/.github/agents/ceo.agent.md", "kind": "role-agent"},
            ],
        }
        self.source.write(
            "source-agents/registries/trimetaverse-live-agent-publish-manifest.json",
            json.dumps(manifest),
        )
        self.source.write("source-agents/ceo/ceo.agent.md", "test agent content")

    def _run_cli(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable, "-m", "runtime.cognition.source_publish_check",
            "--source-root", str(self.source.root),
            "--support-root", str(self.support.root),
        ]
        args.extend(extra_args)
        return subprocess.run(
            args, capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=30,
        )

    # ── TC-AP-CLI1: --publish-agents dry-run outputs valid JSON ─────────────

    def test_publish_agents_dry_run_json(self) -> None:
        """TC-AP-CLI1: --publish-agents dry-run produces valid JSON with agent_publish."""
        proc = self._run_cli("--publish-agents")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["scope"], "publish-agents")
        self.assertTrue(data["scope_specific"]["dry_run"])
        self.assertIn("summary", data)
        self.assertIn("items", data)

    # ── TC-AP-CLI2: --publish-agents --employees filter ─────────────────────

    def test_publish_agents_employees_filter(self) -> None:
        """TC-AP-CLI2: --employees filter reduces entries."""
        proc = self._run_cli("--publish-agents", "--employees", "ceo")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["scope"], "publish-agents")
        # Our fixture has only "ceo" — should find 1 entry
        self.assertGreaterEqual(data["summary"]["total"], 1)

    # ── TC-AP-CLI3: --agent-execute requires --publish-agents ───────────────

    def test_agent_execute_requires_publish_agents(self) -> None:
        """TC-AP-CLI3: --agent-execute without --publish-agents exits with error."""
        proc = self._run_cli("--agent-execute")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("error", (proc.stdout + proc.stderr).lower())

    # ── TC-AP-CLI4: --check --publish-agents combined ────────────────────────

    def test_check_and_publish_agents_combined(self) -> None:
        """TC-AP-CLI4: --check and --publish-agents can run together."""
        proc = self._run_cli("--check", "--publish-agents")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        # Combined runs emit a reports container with one envelope per scope
        self.assertEqual(data["protocol"], "ade-report")
        reports = data.get("reports")
        self.assertIsNotNone(reports, "combined run must emit a reports container")
        self.assertEqual(
            {r["scope"] for r in reports},
            {"sync", "publish-agents"},
        )

    # ── TC-AP-CLI5: --publish-agents --help shows new args ──────────────────

    def test_publish_agents_in_help(self) -> None:
        """TC-AP-CLI5: --help mentions publish-agents and agent-execute."""
        proc = self._run_cli("--help")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        combined = proc.stdout + proc.stderr
        self.assertIn("publish-agents", combined.lower())
        self.assertIn("agent-execute", combined.lower())


class ProjectDocumentSyncTests(unittest.TestCase):
    """Manifest-driven project truth document ADE tests."""

    def setUp(self) -> None:
        self.workspace = TreeFixture()
        self.manifest_path = self.workspace.write(
            "TriCompany/.github/manifests/project-source-doc-sync-manifest.json",
            "{}",
        )

    def tearDown(self) -> None:
        self.workspace.cleanup()

    def _write_manifest(self, entries: list[dict[str, Any]]) -> None:
        self.manifest_path.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0",
                    "planOwner": "CEOChiefOfStaff",
                    "closeOwner": "CEOChiefOfStaff",
                    "entries": entries,
                }
            ),
            encoding="utf-8",
        )

    def test_published_copy_is_dry_run_then_executes(self) -> None:
        from runtime.cognition.source_publish_check import run_project_doc_sync

        source = self.workspace.write("TriCompany/docs/source.md", "new source")
        target = self.workspace.write("TriMetaverse/docs/source.md", "old target")
        self._write_manifest([
            {
                "id": "copy-doc",
                "source": "TriCompany/docs/source.md",
                "target": "TriMetaverse/docs/source.md",
                "syncMode": "published-copy",
            }
        ])

        dry_report = run_project_doc_sync(
            self.manifest_path, self.workspace.root, execute=False
        )
        self.assertEqual(dry_report.items[0].action, "planned_update")
        self.assertEqual(target.read_text(encoding="utf-8"), "old target")

        execute_report = run_project_doc_sync(
            self.manifest_path, self.workspace.root, execute=True
        )
        self.assertEqual(execute_report.items[0].action, "updated")
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            source.read_text(encoding="utf-8"),
        )

    def test_published_summary_with_current_revision_is_in_sync(self) -> None:
        from runtime.cognition.source_publish_check import run_project_doc_sync

        source = self.workspace.write("TriCompany/tricompany.md", "source charter")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        self.workspace.write(
            "TriMetaverse/tricompany.md",
            "\n".join(
                [
                    "# Central summary",
                    "",
                    "## 文档同步元信息",
                    "",
                    "- sourceOfTruth: TriCompany/tricompany.md",
                    "- syncMode: published-summary",
                    f"- sourceRevision: sha256:{source_hash}",
                    "- lastSyncedAt: 2026-08-07",
                ]
            ),
        )
        self._write_manifest([
            {
                "id": "summary-doc",
                "source": "TriCompany/tricompany.md",
                "target": "TriMetaverse/tricompany.md",
                "syncMode": "published-summary",
            }
        ])

        report = run_project_doc_sync(
            self.manifest_path, self.workspace.root, execute=False
        )
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.items[0].action, "in_sync")

    def test_stale_summary_requires_agent_candidate(self) -> None:
        from runtime.cognition.source_publish_check import run_project_doc_sync

        self.workspace.write("TriCompany/tricompany.md", "changed charter")
        target = self.workspace.write(
            "TriMetaverse/tricompany.md",
            "\n".join(
                [
                    "# Old summary",
                    "",
                    "## 文档同步元信息",
                    "",
                    "- sourceOfTruth: TriCompany/tricompany.md",
                    "- syncMode: published-summary",
                    "- sourceRevision: sha256:old",
                    "- lastSyncedAt: 2026-08-01",
                ]
            ),
        )
        self._write_manifest([
            {
                "id": "summary-doc",
                "source": "TriCompany/tricompany.md",
                "target": "TriMetaverse/tricompany.md",
                "syncMode": "published-summary",
            }
        ])

        report = run_project_doc_sync(
            self.manifest_path, self.workspace.root, execute=True
        )
        self.assertEqual(report.status, "partial")
        self.assertEqual(report.items[0].action, "requires_candidate")
        self.assertIn("Old summary", target.read_text(encoding="utf-8"))

    def test_valid_summary_candidate_is_executed(self) -> None:
        from runtime.cognition.source_publish_check import (
            _serialize_project_doc_sync_report,
            run_project_doc_sync,
        )

        source = self.workspace.write("TriCompany/tricompany.md", "changed charter")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        target = self.workspace.write("TriMetaverse/tricompany.md", "old summary")
        candidate = self.workspace.write(
            "TriCompany/.ade/candidates/tricompany.md",
            "\n".join(
                [
                    "# Reviewed summary",
                    "",
                    "## 文档同步元信息",
                    "",
                    "- sourceOfTruth: TriCompany/tricompany.md",
                    "- syncMode: published-summary",
                    f"- sourceRevision: sha256:{source_hash}",
                    "- lastSyncedAt: 2026-08-07",
                ]
            ),
        )
        self._write_manifest([
            {
                "id": "summary-doc",
                "source": "TriCompany/tricompany.md",
                "target": "TriMetaverse/tricompany.md",
                "syncMode": "published-summary",
            }
        ])

        report = run_project_doc_sync(
            self.manifest_path,
            self.workspace.root,
            execute=True,
            candidate_overrides={"summary-doc": str(candidate)},
        )
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.items[0].action, "updated")
        self.assertEqual(target.read_text(encoding="utf-8"), candidate.read_text(encoding="utf-8"))
        serialized = _serialize_project_doc_sync_report(report)
        changed_items = [
            item for item in serialized["items"]
            if item["action"] in ("created", "updated")
        ]
        self.assertEqual(
            changed_items[0]["after_hash"],
            hashlib.sha256(candidate.read_bytes()).hexdigest(),
        )

    def test_target_path_cannot_escape_workspace(self) -> None:
        from runtime.cognition.source_publish_check import run_project_doc_sync

        self.workspace.write("TriCompany/docs/source.md", "source")
        self._write_manifest([
            {
                "id": "escape",
                "source": "TriCompany/docs/source.md",
                "target": "../outside.md",
                "syncMode": "published-copy",
            }
        ])

        report = run_project_doc_sync(
            self.manifest_path, self.workspace.root, execute=True
        )
        self.assertEqual(report.status, "fail")
        self.assertEqual(report.items[0].action, "error")
        self.assertIn("outside_workspace", report.items[0].error)

    def test_protected_target_is_rejected(self) -> None:
        from runtime.cognition.source_publish_check import run_project_doc_sync

        self.workspace.write("TriCompany/docs/source.md", "source")
        self._write_manifest([
            {
                "id": "protected",
                "source": "TriCompany/docs/source.md",
                "target": "TriMetaverse/.github/agents/unsafe.agent.md",
                "syncMode": "published-copy",
            }
        ])

        report = run_project_doc_sync(
            self.manifest_path, self.workspace.root, execute=True
        )
        self.assertEqual(report.status, "fail")
        self.assertEqual(report.items[0].action, "error")
        self.assertIn("protected_target", report.items[0].error)

    def test_unknown_entry_filter_is_not_silent_success(self) -> None:
        from runtime.cognition.source_publish_check import run_project_doc_sync

        self.workspace.write("TriCompany/docs/source.md", "source")
        self._write_manifest([
            {
                "id": "known",
                "source": "TriCompany/docs/source.md",
                "target": "TriMetaverse/docs/source.md",
                "syncMode": "published-copy",
            }
        ])

        report = run_project_doc_sync(
            self.manifest_path,
            self.workspace.root,
            execute=False,
            entry_ids=("missing",),
        )
        self.assertEqual(report.status, "fail")
        self.assertEqual(report.items[0].action, "error")
        self.assertIn("entry_id_not_found", report.items[0].error)


@unittest.skipUnless(_HAS_CLI_MODULE, "source_publish_check.py not yet implemented")
class ProjectDocumentSyncCLITests(unittest.TestCase):
    """CLI contract tests for the project document ADE mode."""

    def setUp(self) -> None:
        self.workspace = TreeFixture()
        self.source_root = self.workspace.root / "TriCompany"
        self.target_root = self.workspace.root / "TriMetaverse"
        self.workspace.write("TriCompany/docs/source.md", "new source")
        self.workspace.write("TriMetaverse/docs/source.md", "old target")
        self.workspace.write(
            "TriCompany/.github/manifests/project-source-doc-sync-manifest.json",
            json.dumps(
                {
                    "schemaVersion": "1.0",
                    "planOwner": "CEOChiefOfStaff",
                    "closeOwner": "CEOChiefOfStaff",
                    "entries": [
                        {
                            "id": "copy-doc",
                            "source": "TriCompany/docs/source.md",
                            "target": "TriMetaverse/docs/source.md",
                            "syncMode": "published-copy",
                        }
                    ],
                }
            ),
        )

    def tearDown(self) -> None:
        self.workspace.cleanup()

    def _run_cli(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            "-m",
            "runtime.cognition.source_publish_check",
            "--source-root",
            str(self.source_root),
            "--support-root",
            str(self.target_root),
            "--workspace-root",
            str(self.workspace.root),
        ]
        args.extend(extra_args)
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
        )

    def test_project_docs_dry_run_and_execute(self) -> None:
        dry_run = self._run_cli("--project-docs")
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        dry_data = json.loads(dry_run.stdout)
        self.assertEqual(dry_data["scope"], "project-docs")
        self.assertTrue(dry_data["scope_specific"]["dry_run"])
        self.assertEqual(dry_data["scope_specific"]["plan_owner"], "CEOChiefOfStaff")
        self.assertEqual(dry_data["scope_specific"]["close_owner"], "CEOChiefOfStaff")
        self.assertEqual(dry_data["items"][0]["action"], "planned_update")
        self.assertEqual(
            (self.target_root / "docs" / "source.md").read_text(encoding="utf-8"),
            "old target",
        )

        execute = self._run_cli("--project-docs", "--project-docs-execute")
        self.assertEqual(execute.returncode, 0, execute.stderr)
        execute_data = json.loads(execute.stdout)
        self.assertFalse(execute_data["scope_specific"]["dry_run"])
        self.assertEqual(execute_data["items"][0]["action"], "updated")
        self.assertEqual(
            (self.target_root / "docs" / "source.md").read_text(encoding="utf-8"),
            "new source",
        )

    def test_project_docs_execute_requires_mode(self) -> None:
        proc = self._run_cli("--project-docs-execute")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("requires --project-docs", (proc.stdout + proc.stderr).lower())

    def test_help_lists_project_document_options(self) -> None:
        proc = self._run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        combined = (proc.stdout + proc.stderr).lower()
        self.assertIn("project-docs", combined)
        self.assertIn("project-doc-candidate", combined)


# ── ADE phase 1: unified envelope contract tests ──────────────────────────────


class EnvelopeContractTests(unittest.TestCase):
    """ADE phase 1: all three scopes share one envelope contract."""

    REQUIRED_KEYS = (
        "protocol", "version", "scope", "run_id", "mode",
        "check_time", "status", "summary", "items", "scope_specific",
    )
    SUMMARY_KEYS = ("total", "changed", "skipped", "errors")
    ITEM_KEYS = (
        "action", "source", "target", "before_hash", "after_hash",
        "scope_key", "error",
    )

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _assert_envelope_shape(self, env: Dict[str, Any]) -> None:
        """Assert the unified envelope contract on *env*."""
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, env, f"envelope missing {key}")
        self.assertEqual(env["protocol"], "ade-report")
        self.assertEqual(env["version"], "1.0")
        self.assertIn(env["scope"], ("sync", "project-docs", "publish-agents"))
        self.assertRegex(
            env["run_id"],
            rf"^ade-{env['scope']}-\d{{8}}T\d{{12}}$",
            "run_id must be deterministic: ade-{scope}-{timestamp}",
        )
        self.assertIn(env["mode"], ("dry-run", "execute"))
        self.assertIn(env["status"], ("pass", "fail", "partial"))
        for key in self.SUMMARY_KEYS:
            self.assertIsInstance(env["summary"][key], int)
        self.assertEqual(
            env["summary"]["total"],
            env["summary"]["changed"] + env["summary"]["skipped"]
            + env["summary"]["errors"],
            "invariant total == changed + skipped + errors",
        )
        self.assertEqual(
            env["summary"]["total"], len(env["items"]),
            "total must equal the number of items",
        )
        from runtime.cognition.source_publish_check import (
            ADE_ACTIONS, ADE_ACTIONS_PER_SCOPE,
        )
        for item in env["items"]:
            for key in self.ITEM_KEYS:
                self.assertIn(key, item, f"item missing {key}")
            self.assertIn(
                item["action"], ADE_ACTIONS,
                f"action {item['action']!r} not in unified vocabulary",
            )
            self.assertIn(
                item["action"], ADE_ACTIONS_PER_SCOPE[env["scope"]],
                f"action {item['action']!r} not allowed for scope {env['scope']}",
            )

    def test_action_vocabulary_is_contractual(self) -> None:
        """ADE phase 1: unified action vocabulary constants are consistent."""
        from runtime.cognition.source_publish_check import (
            ADE_ACTIONS, ADE_ACTIONS_PER_SCOPE, ADE_SCOPES,
        )
        self.assertEqual(set(ADE_SCOPES), {"sync", "project-docs", "publish-agents"})
        for scope in ADE_SCOPES:
            self.assertTrue(
                ADE_ACTIONS_PER_SCOPE[scope].issubset(ADE_ACTIONS),
                f"{scope} allowed actions must be a subset of the vocabulary",
            )
            self.assertIn(
                "error", ADE_ACTIONS_PER_SCOPE[scope],
                "every scope must allow the error action",
            )

    def test_run_id_deterministic_and_scope_scoped(self) -> None:
        """ADE phase 1: run_id is deterministic (timestamp + scope)."""
        from runtime.cognition.source_publish_check import _make_run_id
        run_id = _make_run_id("sync")
        self.assertTrue(run_id.startswith("ade-sync-"))
        self.assertNotIn(":", run_id, "run_id must be filesystem-safe")
        # timestamp part: YYYYMMDD + T + HHMMSS + 6-digit microseconds = 21 chars
        self.assertEqual(len(run_id.split("-")[-1]), 21)

    def test_sync_envelope_contract(self) -> None:
        """--check emits a sync envelope with planned_update/gap items."""
        self.source.write("docs/a.md", "v1")
        self.support.write("docs/a.md", "v2")
        self.source.write("docs/b.md", "only-source")

        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--check"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        env = json.loads(proc.stdout)
        self.assertEqual(env["scope"], "sync")
        self.assertEqual(env["mode"], "dry-run")
        self.assertEqual(env["status"], "pass")
        self._assert_envelope_shape(env)
        actions = {item["action"] for item in env["items"]}
        self.assertEqual(actions, {"planned_update", "gap"})

    def test_sync_execute_outcomes_and_fail_status(self) -> None:
        """--sync execution outcomes split items and errors flip status."""
        from runtime.cognition.source_publish_check import (
            SyncGap, SyncItem, SyncReport, SyncSummary,
            _serialize_sync_report,
        )
        report = SyncReport(
            check_time="2026-08-20T00:00:00+00:00",
            source_root="/src",
            support_root="/dst",
            out_of_sync=[
                SyncItem(source="docs/a.md", target="docs/a.md", reason="hash_mismatch"),
                SyncItem(source="docs/b.md", target="docs/b.md", reason="hash_mismatch"),
                SyncItem(source="docs/c.md", target="docs/c.md", reason="hash_mismatch"),
            ],
            in_sync=[SyncItem(source="docs/ok.md", target="docs/ok.md", reason="hash_match")],
            gaps=[SyncGap(item="docs/new.md", issue="missing_on_support")],
            summary=SyncSummary(total=5, out_of_sync=3, in_sync=1, gaps=1),
        )
        sync_result = {
            "synced": ["docs/a.md"],
            "skipped": ["protected_target: docs/c.md (hash_mismatch)"],
            "errors": ["copy_failed: docs/b.md → docs/b.md — boom"],
        }
        env = _serialize_sync_report(report, sync_result=sync_result)
        self.assertEqual(env["status"], "fail")
        self.assertEqual(env["mode"], "execute")
        by_action = {item["scope_key"]: item["action"] for item in env["items"]}
        self.assertEqual(by_action["docs/a.md"], "updated")
        self.assertEqual(by_action["docs/b.md"], "error")
        self.assertEqual(by_action["docs/c.md"], "skipped_protected")
        self.assertEqual(
            env["summary"],
            {"total": 5, "changed": 1, "skipped": 3, "errors": 1},
        )
        self._assert_envelope_shape(env)

    def test_publish_agents_envelope_contract_and_rc(self) -> None:
        """--publish-agents errors>0 → fail envelope and non-zero exit."""
        # no manifest in the fixture → 1 error item
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--publish-agents"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=30,
        )
        env = json.loads(proc.stdout)
        self.assertEqual(env["scope"], "publish-agents")
        self.assertEqual(env["status"], "fail")
        self.assertNotEqual(proc.returncode, 0, "errors>0 must exit non-zero")
        self._assert_envelope_shape(env)
        self.assertEqual(env["items"][0]["action"], "error")
        self.assertIn("manifest_missing_or_invalid", env["items"][0]["error"])

    def test_project_docs_envelope_contract(self) -> None:
        """project-docs envelope carries plan_owner in scope_specific."""
        from runtime.cognition.source_publish_check import (
            _serialize_project_doc_sync_report, run_project_doc_sync,
        )
        workspace = TreeFixture()
        try:
            workspace.write("TriCompany/docs/source.md", "new source")
            workspace.write("TriMetaverse/docs/source.md", "old target")
            manifest = workspace.write(
                "TriCompany/.github/manifests/project-source-doc-sync-manifest.json",
                json.dumps({
                    "schemaVersion": "1.0",
                    "planOwner": "CEOChiefOfStaff",
                    "closeOwner": "CEOChiefOfStaff",
                    "entries": [{
                        "id": "copy-doc",
                        "source": "TriCompany/docs/source.md",
                        "target": "TriMetaverse/docs/source.md",
                        "syncMode": "published-copy",
                    }],
                }),
            )
            report = run_project_doc_sync(manifest, workspace.root, execute=False)
            env = _serialize_project_doc_sync_report(report)
            self.assertEqual(env["scope"], "project-docs")
            self.assertEqual(env["scope_specific"]["plan_owner"], "CEOChiefOfStaff")
            self.assertEqual(env["scope_specific"]["close_owner"], "CEOChiefOfStaff")
            self.assertEqual(env["items"][0]["action"], "planned_update")
            self._assert_envelope_shape(env)
        finally:
            workspace.cleanup()

    @unittest.skipUnless(os.name == "nt", "Windows drive-relative path semantics")
    def test_drive_relative_target_rejected_at_resolution(self) -> None:
        """ADE phase 1: 'C:foo' style targets are rejected by the resolvers.

        Static layers cannot flag drive-relative paths (is_absolute() is
        False for them on Windows); the resolution layer must refuse them.
        """
        from runtime.cognition.source_publish_check import (
            _resolve_agent_target_path, _resolve_project_doc_path,
        )
        path, err = _resolve_agent_target_path(self.support.root, "C:foo")
        self.assertIsNone(path)
        self.assertEqual(err, "drive_relative_path_not_allowed")
        path, err = _resolve_project_doc_path(self.support.root, "C:foo")
        self.assertIsNone(path)
        self.assertEqual(err, "drive_relative_path_not_allowed")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
