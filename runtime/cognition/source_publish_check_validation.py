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


def _write_agent_manifest(source: TreeFixture, support: TreeFixture) -> None:
    """Write a publish manifest with one eligible role-agent + its source file.

    Needed by combined-run tests: --publish-agents on an empty fixture emits
    manifest_missing_or_invalid → errors>0 → non-zero rc, which would mask
    the assertions under test.
    """
    import json as _json
    source.write(
        "source-agents/registries/trimetaverse-live-agent-publish-manifest.json",
        _json.dumps({
            "manifestId": "test-v0.1",
            "liveEntries": [
                {"status": "current-copilot-host-live",
                 "source": "TriCompany/source-agents/ceo/ceo.agent.md",
                 "target": "TriMetaverse/.github/agents/ceo.agent.md",
                 "kind": "role-agent"},
            ],
        }),
    )
    source.write("source-agents/ceo/ceo.agent.md", "test agent content")


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
            encoding="utf-8",
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
            encoding="utf-8",
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
            args, capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
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
            encoding="utf-8",
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
        # Business-domain scopes (spec §2.2) plus the ADE phase 2 lifecycle
        # scope "close" (Close CLI terminal-gate report).
        self.assertIn(env["scope"], ("sync", "project-docs", "publish-agents", "close"))
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
            ADE_ACTIONS, ADE_ACTIONS_PER_SCOPE, ADE_LIFECYCLE_SCOPES, ADE_SCOPES,
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
        # ADE phase 2: lifecycle scopes reuse the envelope but stay out of the
        # business-domain scope set; their allowed actions are contractual too.
        self.assertEqual(set(ADE_LIFECYCLE_SCOPES), {"close"})
        self.assertIn("closed", ADE_ACTIONS)
        for scope in ADE_LIFECYCLE_SCOPES:
            self.assertTrue(
                ADE_ACTIONS_PER_SCOPE[scope].issubset(ADE_ACTIONS),
                f"{scope} allowed actions must be a subset of the vocabulary",
            )
            self.assertIn(
                "error", ADE_ACTIONS_PER_SCOPE[scope],
                "every scope must allow the error action",
            )

    def test_run_id_timestamp_derived_unique_and_scope_scoped(self) -> None:
        """ADE phase 2: run_id is timestamp-derived, NOT deterministic.

        Every invocation derives a fresh id from the current time (UTC
        timestamp with microseconds); the explicit --run-id overrides this
        derivation (see RunIdExplicitTests). Collisions would require two
        calls within the same microsecond — the contract is the shape, not
        a repeatable value.
        """
        from runtime.cognition.source_publish_check import _make_run_id
        run_id = _make_run_id("sync")
        self.assertTrue(run_id.startswith("ade-sync-"))
        self.assertNotIn(":", run_id, "run_id must be filesystem-safe")
        # timestamp part: YYYYMMDD + T + HHMMSS + 6-digit microseconds = 21 chars
        self.assertEqual(len(run_id.split("-")[-1]), 21)
        # scope scoping: different scopes get different prefixes
        self.assertTrue(_make_run_id("publish-agents").startswith("ade-publish-agents-"))

    def test_sync_envelope_contract(self) -> None:
        """--check emits a sync envelope with planned_update/gap items."""
        self.source.write("docs/a.md", "v1")
        self.support.write("docs/a.md", "v2")
        self.source.write("docs/b.md", "only-source")

        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--check"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
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
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
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


class RunIdExplicitTests(unittest.TestCase):
    """ADE phase 2 work package 1: explicit --run-id wins, timestamp fallback."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    def test_explicit_run_id_overrides_default_in_envelope(self) -> None:
        """--run-id propagates into the emitted envelope."""
        self.source.write("docs/a.md", "v1")
        self.support.write("docs/a.md", "v1")
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--check", "--run-id", "custom-run-42"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        env = json.loads(proc.stdout)
        self.assertEqual(env["run_id"], "custom-run-42")
        # explicit id is NOT the timestamp-derived shape
        self.assertNotRegex(env["run_id"], r"^ade-")

    def test_explicit_run_id_propagates_to_combined_container(self) -> None:
        """Combined runs: every report and the container carry the run id."""
        self.source.write("docs/a.md", "v1")
        self.support.write("docs/a.md", "v1")
        _write_agent_manifest(self.source, self.support)
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--check", "--publish-agents", "--run-id", "combined-001"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["run_id"], "combined-001")
        for report in data["reports"]:
            self.assertEqual(report["run_id"], "combined-001")

    def test_publish_agents_explicit_run_id_in_envelope(self) -> None:
        """FADE-002 回填：--publish-agents 单 scope 显式 --run-id 直达 envelope."""
        _write_agent_manifest(self.source, self.support)
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--publish-agents", "--run-id", "pub-manifest-007"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        env = json.loads(proc.stdout)
        self.assertEqual(env["scope"], "publish-agents")
        self.assertEqual(
            env["run_id"], "pub-manifest-007",
            "manifest 面 envelope 必须承载显式 --run-id（覆盖时间戳派生）",
        )
        self.assertNotRegex(env["run_id"], r"^ade-")

    def test_project_docs_explicit_run_id_in_envelope(self) -> None:
        """FADE-002 回填：--project-docs 单 scope 显式 --run-id 直达 envelope."""
        self.source.write("TriCompany/docs/source.md", "new source")
        self.source.write("TriMetaverse/docs/source.md", "old target")
        self.source.write(
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
        proc = subprocess.run(
            [
                sys.executable, "-m", "runtime.cognition.source_publish_check",
                "--source-root", str(self.source.root / "TriCompany"),
                "--support-root", str(self.source.root / "TriMetaverse"),
                "--workspace-root", str(self.source.root),
                "--project-docs", "--run-id", "proj-manifest-007",
            ],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        env = json.loads(proc.stdout)
        self.assertEqual(env["scope"], "project-docs")
        self.assertEqual(
            env["run_id"], "proj-manifest-007",
            "project-docs manifest 面 envelope 必须承载显式 --run-id",
        )
        self.assertNotRegex(env["run_id"], r"^ade-")

    def test_timestamp_fallback_when_no_run_id(self) -> None:
        """Without --run-id every envelope carries its own scope-scoped id."""
        self.source.write("docs/a.md", "v1")
        self.support.write("docs/a.md", "v1")
        _write_agent_manifest(self.source, self.support)
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--check", "--publish-agents"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertNotIn("run_id", data, "container must not synthesize a run id")
        by_scope = {r["scope"]: r["run_id"] for r in data["reports"]}
        self.assertRegex(by_scope["sync"], r"^ade-sync-\d{8}T\d{12}$")
        self.assertRegex(
            by_scope["publish-agents"], r"^ade-publish-agents-\d{8}T\d{12}$",
        )

    def test_invalid_run_id_rejected_at_cli(self) -> None:
        """Non-token run ids (path separators, leading dot) are rejected."""
        for bad in ("bad/run-id", "bad\\run", ".hidden", "with space"):
            proc = subprocess.run(
                _cli_base_args(str(self.source.root), str(self.support.root))
                + ["--check", "--run-id", bad],
                capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
            )
            self.assertNotEqual(proc.returncode, 0, f"run id {bad!r} must fail")
            self.assertIn("run-id", proc.stderr)

    def test_validate_run_id_unit(self) -> None:
        """_validate_run_id: empty / bad shape rejected, tokens accepted."""
        from runtime.cognition.source_publish_check import _validate_run_id
        self.assertEqual(_validate_run_id(""), "run_id_missing")
        self.assertEqual(_validate_run_id("   "), "run_id_missing")
        self.assertEqual(_validate_run_id("a/b"), "run_id_invalid")
        self.assertEqual(_validate_run_id("a b"), "run_id_invalid")
        self.assertEqual(_validate_run_id("ade-sync-20260820T000000000000"), "")
        self.assertEqual(_validate_run_id("custom.run_1-2"), "")


class CombinedContainerAggregationTests(unittest.TestCase):
    """ADE phase 2 work package 2: combined-run container aggregation."""

    def _envelope(self, scope: str, errors: int, status: str) -> Dict[str, Any]:
        return {
            "protocol": "ade-report", "version": "1.0", "scope": scope,
            "run_id": f"ade-{scope}-20260820T000000000000",
            "mode": "dry-run", "check_time": "2026-08-20T00:00:00+00:00",
            "status": status,
            "summary": {"total": 3, "changed": 0, "skipped": 3 - errors, "errors": errors},
            "items": [], "scope_specific": {},
        }

    def test_container_fail_when_any_report_has_errors(self) -> None:
        """任一域 errors>0 → 容器 status=fail（聚合规则提案）。"""
        from runtime.cognition.source_publish_check import _serialize_combined_container
        container = _serialize_combined_container([
            self._envelope("sync", 0, "pass"),
            self._envelope("publish-agents", 2, "fail"),
        ])
        self.assertEqual(container["status"], "fail")
        self.assertEqual(
            container["summary"],
            {"total": 6, "changed": 0, "skipped": 4, "errors": 2},
        )

    def test_container_partial_when_no_errors_but_partial_present(self) -> None:
        """无 errors 但任一域 partial → partial。"""
        from runtime.cognition.source_publish_check import _serialize_combined_container
        container = _serialize_combined_container([
            self._envelope("sync", 0, "pass"),
            self._envelope("project-docs", 0, "partial"),
        ])
        self.assertEqual(container["status"], "partial")

    def test_container_pass_when_all_clean(self) -> None:
        """全域 pass 且无 errors → pass。"""
        from runtime.cognition.source_publish_check import _serialize_combined_container
        container = _serialize_combined_container([
            self._envelope("sync", 0, "pass"),
            self._envelope("publish-agents", 0, "pass"),
        ])
        self.assertEqual(container["status"], "pass")
        self.assertEqual(container["summary"]["errors"], 0)

    def test_container_invariant_preserved(self) -> None:
        """逐 envelope 守恒（total == changed + skipped + errors）⇒ 容器守恒。"""
        from runtime.cognition.source_publish_check import _serialize_combined_container
        container = _serialize_combined_container([
            self._envelope("sync", 0, "pass"),
            self._envelope("publish-agents", 1, "fail"),
            self._envelope("project-docs", 0, "partial"),
        ])
        summary = container["summary"]
        self.assertEqual(
            summary["total"],
            summary["changed"] + summary["skipped"] + summary["errors"],
        )

    def test_container_run_id_only_when_explicit(self) -> None:
        """显式 --run-id 时容器携带；缺省不合成容器级 id。"""
        from runtime.cognition.source_publish_check import _serialize_combined_container
        container = _serialize_combined_container(
            [self._envelope("sync", 0, "pass")], run_id="explicit-1",
        )
        self.assertEqual(container["run_id"], "explicit-1")
        no_id = _serialize_combined_container([self._envelope("sync", 0, "pass")])
        self.assertNotIn("run_id", no_id)

    def test_combined_cli_emits_aggregated_container(self) -> None:
        """CLI 组合运行输出带 status/summary 聚合的容器。"""
        self.source = TreeFixture()
        self.support = TreeFixture()
        try:
            _write_agent_manifest(self.source, self.support)
            proc = subprocess.run(
                _cli_base_args(str(self.source.root), str(self.support.root))
                + ["--check", "--publish-agents"],
                capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
            )
            self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
            data = json.loads(proc.stdout)
            self.assertEqual(data["protocol"], "ade-report")
            self.assertIn("status", data)
            self.assertIn("summary", data)
            self.assertIn("check_time", data)
            self.assertEqual(len(data["reports"]), 2)
            summary = data["summary"]
            self.assertEqual(
                summary["total"],
                summary["changed"] + summary["skipped"] + summary["errors"],
            )
        finally:
            self.source.cleanup()


class AdeEnvelopeHelperTests(unittest.TestCase):
    """ADE phase 2 work package 3: shared consumer-side envelope helpers."""

    def test_parse_cli_output_invalid_json_is_none(self) -> None:
        from runtime.cognition.ade_envelope import parse_cli_output
        self.assertIsNone(parse_cli_output("not json {"))
        self.assertIsNone(parse_cli_output("[1, 2]"))
        self.assertIsNone(parse_cli_output(""))
        self.assertIsNotNone(parse_cli_output('{"protocol": "ade-report"}'))

    def test_find_scope_envelope_bare(self) -> None:
        from runtime.cognition.ade_envelope import find_scope_envelope
        data = {"protocol": "ade-report", "scope": "publish-agents", "summary": {}}
        env = find_scope_envelope(data, "publish-agents")
        self.assertIsNotNone(env)
        self.assertEqual(env["scope"], "publish-agents")

    def test_find_scope_envelope_reports_container(self) -> None:
        from runtime.cognition.ade_envelope import find_scope_envelope
        data = {
            "protocol": "ade-report", "version": "1.0",
            "reports": [
                {"protocol": "ade-report", "scope": "sync"},
                {"protocol": "ade-report", "scope": "publish-agents"},
            ],
        }
        env = find_scope_envelope(data, "publish-agents")
        self.assertIsNotNone(env)
        self.assertEqual(env["scope"], "publish-agents")

    def test_find_scope_envelope_malformed_container_defensive(self) -> None:
        """reports 非 list / 非 dict 条目 → None，绝不抛异常。"""
        from runtime.cognition.ade_envelope import find_scope_envelope
        self.assertIsNone(find_scope_envelope(
            {"protocol": "ade-report", "reports": "not-a-list"}, "publish-agents",
        ))
        self.assertIsNone(find_scope_envelope(
            {"protocol": "ade-report", "reports": ["nope", 3]}, "publish-agents",
        ))
        self.assertIsNone(find_scope_envelope(
            {"reports": [{"scope": "publish-agents"}]}, "publish-agents",
        ), "non-ade entries in the container must not match")

    def test_find_scope_envelope_wrong_scope_is_none(self) -> None:
        from runtime.cognition.ade_envelope import find_scope_envelope
        data = {"protocol": "ade-report", "scope": "sync"}
        self.assertIsNone(find_scope_envelope(data, "publish-agents"))
        self.assertIsNone(find_scope_envelope(data, "close"))

    def test_extract_scope_envelope_roundtrip(self) -> None:
        from runtime.cognition.ade_envelope import extract_scope_envelope
        import json as _json
        env = extract_scope_envelope(
            _json.dumps({"protocol": "ade-report", "scope": "publish-agents"}),
            "publish-agents",
        )
        self.assertIsNotNone(env)
        self.assertIsNone(extract_scope_envelope("{bad", "publish-agents"))

    def test_envelope_error_items_filters_errors(self) -> None:
        from runtime.cognition.ade_envelope import envelope_error_items
        env = {
            "items": [
                {"action": "created", "error": ""},
                {"action": "error", "source": "a", "error": "boom"},
                {"action": "error", "source": "b", "error": "bang"},
                {"action": "in_sync", "error": ""},
            ],
        }
        errors = envelope_error_items(env)
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0]["error"], "boom")
        self.assertEqual(envelope_error_items({"items": "nope"}), [])


class CloseCliTests(unittest.TestCase):
    """ADE phase 2 work package 4: Close CLI (spec §2.5 终态门)."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()
        self.source.write("evidence.md", "evidence artifact")

    def tearDown(self) -> None:
        self.source.cleanup()

    def _run_close(self, data_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--close", "--ade-data-dir", str(data_dir), *extra],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )

    def test_close_approved_writes_audit_record_and_envelope(self) -> None:
        """校验通过 → 写终态审计记录 + CLOSED envelope + rc 0。"""
        from runtime.cognition.source_publish_check import ADE_CLOSE_RECORD_SUFFIX
        data_dir = TreeFixture()
        try:
            proc = self._run_close(
                data_dir.root,
                "--run-id", "ade-sync-20260820T000000000000",
                "--verdict", "APPROVED",
                "--evidence-ref", "evidence.md",
                "--source-revision", "abc123def",
            )
            self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
            env = json.loads(proc.stdout)
            self.assertEqual(env["scope"], "close")
            self.assertEqual(env["status"], "pass")
            self.assertEqual(env["scope_specific"]["state"], "CLOSED")
            self.assertEqual(env["scope_specific"]["verdict"], "APPROVED")
            self.assertEqual(env["items"][0]["action"], "closed")
            record = data_dir.root / (
                f"ade-sync-20260820T000000000000{ADE_CLOSE_RECORD_SUFFIX}"
            )
            self.assertTrue(record.is_file())
            payload = json.loads(record.read_text(encoding="utf-8"))
            self.assertEqual(
                set(payload),
                {"run_id", "verdict", "evidence", "source_revision", "check_time"},
            )
            self.assertEqual(payload["run_id"], "ade-sync-20260820T000000000000")
            self.assertEqual(payload["verdict"], "APPROVED")
            self.assertEqual(payload["evidence"], "evidence.md")
            self.assertEqual(payload["source_revision"], "abc123def")
        finally:
            data_dir.cleanup()

    def test_close_envelope_contract_and_invariant(self) -> None:
        """close envelope 复用统一合同且守恒不变量成立。"""
        data_dir = TreeFixture()
        try:
            proc = self._run_close(
                data_dir.root,
                "--run-id", "close-run-1",
                "--verdict", "FROZEN",
                "--evidence-ref", "evidence.md",
                "--source-revision", "rev-1",
            )
            self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
            env = json.loads(proc.stdout)
            for key in ("protocol", "version", "scope", "run_id", "mode",
                        "check_time", "status", "summary", "items", "scope_specific"):
                self.assertIn(key, env)
            self.assertEqual(env["protocol"], "ade-report")
            self.assertEqual(env["run_id"], "close-run-1")
            self.assertEqual(
                env["summary"]["total"],
                env["summary"]["changed"] + env["summary"]["skipped"]
                + env["summary"]["errors"],
            )
            self.assertEqual(env["summary"], {"total": 1, "changed": 1, "skipped": 0, "errors": 0})
        finally:
            data_dir.cleanup()

    def test_close_rejected_missing_run_id(self) -> None:
        """run_id 缺失 → CLOSE_REJECTED + 非零 rc + 无审计记录（不得静默）。"""
        data_dir = TreeFixture()
        try:
            proc = self._run_close(
                data_dir.root,
                "--verdict", "APPROVED",
                "--evidence-ref", "evidence.md",
                "--source-revision", "rev-1",
            )
            self.assertNotEqual(proc.returncode, 0)
            env = json.loads(proc.stdout)
            self.assertEqual(env["status"], "fail")
            self.assertEqual(env["scope_specific"]["state"], "CLOSE_REJECTED")
            self.assertIn("run_id_missing", env["items"][0]["error"])
            self.assertFalse(
                list(data_dir.root.glob("*.close-ade.json")),
                "rejected close must not write a terminal audit record",
            )
        finally:
            data_dir.cleanup()

    def test_close_rejected_invalid_run_id_and_unresolvable_evidence(self) -> None:
        """非法 run_id / 不可解析 evidence / 空 revision → 逐项 error code。"""
        data_dir = TreeFixture()
        try:
            proc = self._run_close(
                data_dir.root,
                "--run-id", "bad/run id",
                "--verdict", "RETRY",
                "--evidence-ref", "no-such-file.md",
                "--source-revision", "  ",
            )
            self.assertNotEqual(proc.returncode, 0)
            env = json.loads(proc.stdout)
            self.assertEqual(env["scope_specific"]["state"], "CLOSE_REJECTED")
            error = env["items"][0]["error"]
            self.assertIn("run_id_invalid", error)
            self.assertIn("evidence_ref_unresolvable", error)
            self.assertIn("source_revision_missing", error)
        finally:
            data_dir.cleanup()

    def test_close_rejects_double_close(self) -> None:
        """同一 run 二次 close → run_already_closed（状态转换校验）。"""
        data_dir = TreeFixture()
        try:
            first = self._run_close(
                data_dir.root,
                "--run-id", "once-only",
                "--verdict", "APPROVED",
                "--evidence-ref", "evidence.md",
                "--source-revision", "rev-1",
            )
            self.assertEqual(first.returncode, 0, f"stderr: {first.stderr}")
            second = self._run_close(
                data_dir.root,
                "--run-id", "once-only",
                "--verdict", "APPROVED",
                "--evidence-ref", "evidence.md",
                "--source-revision", "rev-1",
            )
            self.assertNotEqual(second.returncode, 0)
            env = json.loads(second.stdout)
            self.assertEqual(env["scope_specific"]["state"], "CLOSE_REJECTED")
            self.assertIn("run_already_closed", env["items"][0]["error"])
        finally:
            data_dir.cleanup()

    def test_close_verdict_invalid_rejected_by_validation(self) -> None:
        """verdict 非法值在 _validate_close_inputs 层被拒绝。"""
        from runtime.cognition.source_publish_check import _validate_close_inputs
        errors = _validate_close_inputs(
            run_id="run-1", verdict="MAYBE", evidence_ref="evidence.md",
            source_revision="rev-1", source_root=self.source.root,
        )
        self.assertIn("verdict_invalid", errors)

    def test_close_evidence_url_resolvable(self) -> None:
        """http(s)/file URL evidence 视为可解析。"""
        from runtime.cognition.source_publish_check import _evidence_ref_resolvable
        self.assertTrue(_evidence_ref_resolvable("https://example.com/x.md", self.source.root))
        self.assertTrue(_evidence_ref_resolvable("file:///tmp/x.md", self.source.root))
        self.assertFalse(_evidence_ref_resolvable("no-such-file.md", self.source.root))
        self.assertFalse(_evidence_ref_resolvable("", self.source.root))


class ScoreCliTests(unittest.TestCase):
    """ADE phase 2 work package 5: Score CLI (spec §2.6 / 试卷模板 §三)."""

    PAPER = {
        "items": [
            {"id": "dry-run-gate", "label": "dry-run gate", "weight": 40, "max": 40,
             "required": True, "verify_method": "assert no writes"},
            {"id": "structured-report", "label": "structured report", "weight": 30,
             "max": 30, "required": True, "verify_method": "parse JSON"},
            {"id": "terminal-close", "label": "terminal close", "weight": 30,
             "max": 30, "required": True, "verify_method": "audit record"},
        ],
        # total max = 100, threshold 80 per 试卷模板 §二 default
        "threshold": 80,
    }

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _full_report(self) -> Dict[str, Any]:
        """Envelope with evidence for all three paper items (scope_key match)."""
        return {
            "protocol": "ade-report", "version": "1.0", "scope": "publish-agents",
            "run_id": "ade-publish-agents-20260820T000000000000",
            "mode": "dry-run", "check_time": "2026-08-20T00:00:00+00:00",
            "status": "pass",
            "summary": {"total": 3, "changed": 0, "skipped": 3, "errors": 0},
            "items": [
                {"action": "skipped_dry_run", "source": "a", "target": "b",
                 "before_hash": "", "after_hash": "", "scope_key": "dry-run-gate", "error": ""},
                {"action": "skipped_dry_run", "source": "c", "target": "d",
                 "before_hash": "", "after_hash": "", "scope_key": "structured-report", "error": ""},
                {"action": "skipped_dry_run", "source": "e", "target": "f",
                 "before_hash": "", "after_hash": "", "scope_key": "terminal-close", "error": ""},
            ],
            "scope_specific": {},
        }

    def _quality(self, **scores: float) -> Dict[str, Any]:
        """Build quality-scores payload; kwargs use '_' where ids use '-'."""
        return {"items": [
            {"id": item_id.replace("_", "-"), "score": score}
            for item_id, score in scores.items()
        ]}

    # ── 模板 §三 合同断言 ──────────────────────────────────────────────────

    def test_score_contract_shape(self) -> None:
        """评分输出合同字段齐全（status/items/total/required_all_passed/verdict/scored_at）。"""
        from runtime.cognition.source_publish_check import score_assessment
        contract = score_assessment(
            self.PAPER, self._full_report(),
            quality_scores=self._quality(dry_run_gate=40, structured_report=30, terminal_close=30),
        )
        self.assertEqual(
            set(contract),
            {"status", "items", "total", "required_all_passed", "verdict", "scored_at"},
        )
        self.assertEqual(set(contract["total"]), {"score", "max", "threshold"})
        for item in contract["items"]:
            self.assertEqual(
                set(item),
                {"id", "label", "weight", "score", "max", "evidence_ref",
                 "required", "omission", "quality_score"},
            )
        self.assertEqual(contract["total"], {"score": 100.0, "max": 100.0, "threshold": 80.0})

    def test_score_verdict_iff_required_all_passed_and_threshold(self) -> None:
        """合同断言：verdict PASS ⇔ required_all_passed ∧ score >= threshold。"""
        from runtime.cognition.source_publish_check import score_assessment

        # 全覆盖 + 质量满分 → PASS
        full = score_assessment(
            self.PAPER, self._full_report(),
            quality_scores=self._quality(dry_run_gate=40, structured_report=30, terminal_close=30),
        )
        self.assertTrue(full["required_all_passed"])
        self.assertEqual(full["verdict"], "PASS")
        self.assertEqual(full["status"], "pass")

        # 必选项遗漏 → required_all_passed False → FAIL（分数无关）
        partial_report = self._full_report()
        partial_report["items"] = partial_report["items"][:2]  # terminal-close 无证据
        omitted = score_assessment(
            self.PAPER, partial_report,
            quality_scores=self._quality(dry_run_gate=10, structured_report=10),
        )
        self.assertFalse(omitted["required_all_passed"])
        self.assertEqual(omitted["verdict"], "FAIL")
        self.assertEqual(omitted["status"], "fail")

        # 必选项全过但总分不达标 → FAIL（status partial）
        low_quality = score_assessment(
            self.PAPER, self._full_report(),
            quality_scores=self._quality(dry_run_gate=2, structured_report=2, terminal_close=2),
        )
        self.assertTrue(low_quality["required_all_passed"])
        self.assertEqual(low_quality["total"]["score"], 6.0)
        self.assertLess(low_quality["total"]["score"], low_quality["total"]["threshold"])
        self.assertEqual(low_quality["verdict"], "FAIL")
        self.assertEqual(low_quality["status"], "partial")

        # 非必选项遗漏 + 必选项全过 + 分数达标 → PASS
        relaxed_paper = {
            "items": [
                {"id": "dry-run-gate", "label": "dry-run gate", "weight": 50, "max": 50,
                 "required": True, "verify_method": "x"},
                {"id": "nice-to-have", "label": "nice to have", "weight": 50, "max": 50,
                 "required": False, "verify_method": "x"},
            ],
            "threshold": 50,
        }
        relaxed_report = {
            "protocol": "ade-report", "version": "1.0", "scope": "sync",
            "run_id": "r", "mode": "dry-run", "check_time": "t", "status": "pass",
            "summary": {"total": 1, "changed": 0, "skipped": 1, "errors": 0},
            "items": [{"action": "in_sync", "source": "", "target": "",
                       "before_hash": "", "after_hash": "", "scope_key": "dry-run-gate", "error": ""}],
            "scope_specific": {},
        }
        relaxed = score_assessment(
            relaxed_paper, relaxed_report,
            quality_scores=self._quality(dry_run_gate=50),
        )
        self.assertTrue(relaxed["required_all_passed"])
        self.assertEqual(relaxed["items"][1]["omission"], True)
        self.assertEqual(relaxed["items"][1]["score"], 0.0)
        self.assertEqual(relaxed["total"]["score"], 50.0)
        self.assertEqual(relaxed["verdict"], "PASS")

    def test_score_omission_zero_score_rule(self) -> None:
        """omission=true → 0 分，且 evidence_ref 为空。"""
        from runtime.cognition.source_publish_check import score_assessment
        report = self._full_report()
        report["items"] = report["items"][:1]
        contract = score_assessment(
            self.PAPER, report,
            quality_scores=self._quality(dry_run_gate=10, structured_report=10),
        )
        for item in contract["items"]:
            if item["id"] in ("structured-report", "terminal-close"):
                self.assertTrue(item["omission"])
                self.assertEqual(item["score"], 0.0)
                self.assertEqual(item["evidence_ref"], "")
                self.assertIsNone(item["quality_score"])
        self.assertEqual(contract["items"][0]["score"], 10.0)

    def test_score_quality_merge_rules(self) -> None:
        """质量合并：有质量分用质量分；无质量分保留 max（覆盖检查不扣分）。"""
        from runtime.cognition.source_publish_check import score_assessment
        contract = score_assessment(
            self.PAPER, self._full_report(),
            quality_scores=self._quality(dry_run_gate=7, structured_report=8),
        )
        by_id = {item["id"]: item for item in contract["items"]}
        self.assertEqual(by_id["dry-run-gate"]["score"], 7.0)
        self.assertEqual(by_id["structured-report"]["score"], 8.0)
        self.assertEqual(by_id["dry-run-gate"]["quality_score"], 7.0)
        self.assertEqual(by_id["structured-report"]["quality_score"], 8.0)
        # 未提供质量分的已覆盖项：保留 max，quality_score=null 显式标记
        self.assertEqual(by_id["terminal-close"]["score"], 30.0)
        self.assertIsNone(by_id["terminal-close"]["quality_score"])

    def test_score_quality_score_out_of_range_rejected(self) -> None:
        """质量分越界（> max 或 < 0）→ 输入错误合同 + FAIL。"""
        from runtime.cognition.source_publish_check import run_score
        contract = run_score(
            paper=self.PAPER, report=self._full_report(),
            quality_scores=self._quality(dry_run_gate=99),
        )
        self.assertEqual(contract["verdict"], "FAIL")
        self.assertEqual(contract["status"], "fail")
        self.assertIn("quality_score_out_of_range", contract.get("error", ""))

    def test_score_evidence_suffix_and_scope_specific_matching(self) -> None:
        """证据匹配：source/target 后缀匹配 + scope_specific 键匹配。"""
        from runtime.cognition.source_publish_check import score_assessment
        report = {
            "protocol": "ade-report", "version": "1.0", "scope": "sync",
            "run_id": "r", "mode": "dry-run", "check_time": "t", "status": "pass",
            "summary": {"total": 2, "changed": 0, "skipped": 2, "errors": 0},
            "items": [
                {"action": "in_sync", "source": "TriCompany/docs/dry-run-gate.md",
                 "target": "", "before_hash": "", "after_hash": "",
                 "scope_key": "docs/dry-run-gate.md", "error": ""},
            ],
            "scope_specific": {"terminal-close": "docs/execution/close-record.json"},
        }
        contract = score_assessment(
            self.PAPER, report,
            quality_scores=self._quality(dry_run_gate=10, structured_report=10, terminal_close=10),
        )
        by_id = {item["id"]: item for item in contract["items"]}
        self.assertFalse(by_id["dry-run-gate"]["omission"])
        # first match wins: scope_key "docs/dry-run-gate.md" (stem match) before source
        self.assertEqual(by_id["dry-run-gate"]["evidence_ref"], "docs/dry-run-gate.md")
        self.assertFalse(by_id["terminal-close"]["omission"])
        self.assertEqual(by_id["terminal-close"]["evidence_ref"], "scope_specific.terminal-close")
        self.assertTrue(by_id["structured-report"]["omission"])

    def test_score_declared_evidence_ref_strict(self) -> None:
        """试卷项声明 evidence_ref 时严格匹配：找不到即 omission。"""
        from runtime.cognition.source_publish_check import score_assessment
        paper = {
            "items": [
                {"id": "copy-doc", "label": "copy doc", "weight": 10, "max": 10,
                 "required": True, "evidence_ref": "TriCompany/docs/source.md",
                 "verify_method": "x"},
            ],
            "threshold": 80,
        }
        matched = score_assessment(
            paper, self._full_report(),
            quality_scores=self._quality(copy_doc=10),
        )
        # scope_key 是 "dry-run-gate" 等，不匹配声明的 evidence_ref → omission
        self.assertTrue(matched["items"][0]["omission"])
        report = {
            "protocol": "ade-report", "version": "1.0", "scope": "project-docs",
            "run_id": "r", "mode": "dry-run", "check_time": "t", "status": "pass",
            "summary": {"total": 1, "changed": 0, "skipped": 1, "errors": 0},
            "items": [{"action": "planned_update", "source": "TriCompany/docs/source.md",
                       "target": "TriMetaverse/docs/source.md", "before_hash": "",
                       "after_hash": "", "scope_key": "copy-doc", "error": ""}],
            "scope_specific": {},
        }
        matched2 = score_assessment(
            paper, report, quality_scores=self._quality(copy_doc=10),
        )
        self.assertFalse(matched2["items"][0]["omission"])
        self.assertEqual(matched2["items"][0]["evidence_ref"], "TriCompany/docs/source.md")

    def test_score_container_report_evidence_across_envelopes(self) -> None:
        """组合容器报告：证据可跨 envelope 指认。"""
        from runtime.cognition.source_publish_check import score_assessment
        container = {
            "protocol": "ade-report", "version": "1.0",
            "reports": [
                self._full_report(),
                {
                    "protocol": "ade-report", "version": "1.0", "scope": "sync",
                    "run_id": "r2", "mode": "dry-run", "check_time": "t",
                    "status": "pass",
                    "summary": {"total": 1, "changed": 0, "skipped": 1, "errors": 0},
                    "items": [{"action": "in_sync", "source": "", "target": "",
                               "before_hash": "", "after_hash": "",
                               "scope_key": "structured-report", "error": ""}],
                    "scope_specific": {},
                },
            ],
        }
        contract = score_assessment(
            self.PAPER, container, quality_scores=self._quality(),
        )
        by_id = {item["id"]: item for item in contract["items"]}
        self.assertFalse(by_id["structured-report"]["omission"])

    def test_score_threshold_from_paper_and_override(self) -> None:
        """阈值优先级：--score-threshold > paper.threshold > 默认 80。"""
        from runtime.cognition.source_publish_check import score_assessment
        paper_no_threshold = {"items": self.PAPER["items"]}
        contract = score_assessment(
            paper_no_threshold, self._full_report(), quality_scores=self._quality(),
        )
        self.assertEqual(contract["total"]["threshold"], 80.0)
        override = score_assessment(
            self.PAPER, self._full_report(), quality_scores=self._quality(),
            threshold=30.0,
        )
        self.assertEqual(override["total"]["threshold"], 30.0)
        self.assertEqual(override["verdict"], "PASS")

    def test_score_invalid_paper_rejected(self) -> None:
        """试卷 items 为空 / 容器无 envelope → error 合同 + FAIL。"""
        from runtime.cognition.source_publish_check import run_score
        self.assertEqual(
            run_score(paper={"items": []}, report=self._full_report())["error"],
            "paper_items_must_be_nonempty_list",
        )
        self.assertEqual(
            run_score(paper=self.PAPER, report={"reports": []})["error"],
            "report_has_no_envelope",
        )
        # 裸 envelope 但无 items：合法退化报告 → 全 omission → FAIL（无 error 字段）
        degenerate = run_score(
            paper=self.PAPER, report={"protocol": "ade-report", "scope": "sync"},
        )
        self.assertEqual(degenerate["verdict"], "FAIL")
        self.assertNotIn("error", degenerate)

    def test_score_cli_roundtrip_and_rc(self) -> None:
        """CLI 全链路：paper/report/quality 文件 → 合同 JSON，rc 随 verdict。"""
        paper = self.source.write("paper.json", json.dumps(self.PAPER))
        report = self.source.write("report.json", json.dumps(self._full_report()))
        quality = self.source.write(
            "quality.json",
            json.dumps(self._quality(dry_run_gate=40, structured_report=30, terminal_close=30)),
        )
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--score", "--score-paper", str(paper), "--score-report", str(report),
               "--score-quality-scores", str(quality)],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        contract = json.loads(proc.stdout)
        self.assertEqual(contract["verdict"], "PASS")
        self.assertEqual(contract["status"], "pass")
        # FAIL 时 rc 非零
        failing_report = self.source.write("report-fail.json", json.dumps({"reports": []}))
        proc2 = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--score", "--score-paper", str(paper), "--score-report", str(failing_report)],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertNotEqual(proc2.returncode, 0)
        contract2 = json.loads(proc2.stdout)
        self.assertEqual(contract2["verdict"], "FAIL")

    def test_score_missing_input_files_rejected(self) -> None:
        """score 输入文件缺失 → error 字段 + 非零 rc。"""
        proc = subprocess.run(
            _cli_base_args(str(self.source.root), str(self.support.root))
            + ["--score", "--score-paper", "no-paper.json", "--score-report", "no-report.json"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT), timeout=30,
        )
        self.assertNotEqual(proc.returncode, 0)
        contract = json.loads(proc.stdout)
        self.assertEqual(contract["verdict"], "FAIL")
        self.assertIn("paper_missing_or_invalid", contract.get("error", ""))
        self.assertIn("report_missing_or_invalid", contract.get("error", ""))


# ── ADE-B: multi-host render tests (CEO 2026-08-19 定调) ──────────────────────


class AgentPublishRenderTests(unittest.TestCase):
    """ADE-B multi-host render unit tests (source + host template → render).

    Covers: --host=claude frontmatter shape mapping, extraSections render
    metadata, target derivation, derived-consistency check (derived_identical /
    derived_drift), escape protection on both hosts, Chinese content, and
    legacy-manifest byte-copy compatibility.
    """

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _write_manifest(self, entries: list) -> None:
        self.source.write(
            "source-agents/registries/trimetaverse-live-agent-publish-manifest.json",
            json.dumps({"manifestId": "test-v0.1", "liveEntries": entries}),
        )

    def _write_agent_source(
        self, content: str = "---\nname: CEOChiefOfStaff\n"
        "description: \"desc\"\n"
        "tools: [read, search, edit]\n"
        "user-invocable: true\n"
        "---\n你是 TriCompany 的 CEO 总助。\n"
    ) -> None:
        self.source.write("source-agents/ceo/ceo.agent.md", content)

    def _render_entry(self, **extra: Any) -> dict:
        entry: dict[str, Any] = {
            "status": "current-copilot-host-live",
            "source": "TriCompany/source-agents/ceo/ceo.agent.md",
            "target": "TriMetaverse/.github/agents/ceo.agent.md",
            "kind": "role-agent",
        }
        entry.update(extra)
        return entry

    # ── frontmatter shape mapping ──────────────────────────────────────────

    def test_claude_frontmatter_shape(self) -> None:
        """claude 渲染 frontmatter：name/description/tools/user-invocable，tools PascalCase。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        self._write_agent_source()
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(), "claude",
        )
        self.assertEqual(err, "")
        head = rendered.splitlines()
        self.assertEqual(head[0], "---")
        self.assertIn("name: CEOChiefOfStaff", head)
        self.assertIn('description: "desc"', head)
        self.assertIn("tools: [Read, Glob, Edit]", head)
        self.assertIn("user-invocable: true", head)
        self.assertEqual(head[-1], "你是 TriCompany 的 CEO 总助。")
        self.assertFalse(rendered.endswith(".agent.md"))

    def test_claude_tools_unknown_kept(self) -> None:
        """未映射工具名原样保留（保守不编造）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        self._write_agent_source(
            "---\nname: X\ntools: [read, mytool]\nuser-invocable: true\n---\nbody\n"
        )
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(), "claude",
        )
        self.assertEqual(err, "")
        self.assertIn("tools: [Read, mytool]", rendered)

    def test_copilot_frontmatter_byte_preserved(self) -> None:
        """copilot 渲染面（有元数据）frontmatter 字节级保留。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        self._write_agent_source()
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(extraSections="## 默认输出结构\n\n### 决策\n- 内容\n"), "copilot",
        )
        self.assertEqual(err, "")
        self.assertIn("tools: [read, search, edit]", rendered)
        self.assertIn("user-invocable: true", rendered)

    # ── CRLF / frontmatter split regression (CTO 裁决 2026-08-20) ─────────

    def test_crlf_source_renders_unified_lf(self) -> None:
        """CRLF 源渲染产物统一 LF（无 \\r），frontmatter 正确保留（渲染面 CRLF 归一）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        crlf_source = (
            "---\r\nname: CEOChiefOfStaff\r\n"
            "description: \"desc\"\r\n"
            "tools: [read, search, edit]\r\n"
            "user-invocable: true\r\n"
            "---\r\n你是 TriCompany 的 CEO 总助。\r\n"
        )
        rendered, err = _render_agent_payload(
            crlf_source, self._render_entry(renderTemplate="host-default"), "copilot",
        )
        self.assertEqual(err, "")
        self.assertNotIn("\r", rendered)
        head = rendered.splitlines()
        self.assertEqual(head[0], "---")
        self.assertIn("name: CEOChiefOfStaff", head)
        self.assertIn("tools: [read, search, edit]", head)
        self.assertIn("user-invocable: true", head)
        self.assertEqual(head[-1], "你是 TriCompany 的 CEO 总助。")

    def test_crlf_source_with_extra_sections_unified_lf(self) -> None:
        """CRLF 源 + extraSections → 渲染产物全 LF（附加段拼接处亦无 \\r）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        crlf_source = (
            "---\r\nname: CEOChiefOfStaff\r\n"
            "tools: [read, search, edit]\r\n"
            "user-invocable: true\r\n"
            "---\r\n你是 TriCompany 的 CEO 总助。\r\n"
        )
        rendered, err = _render_agent_payload(
            crlf_source,
            self._render_entry(extraSections="## 默认输出结构\n\n### 决策\n- 内容\n"),
            "copilot",
        )
        self.assertEqual(err, "")
        self.assertNotIn("\r", rendered)
        self.assertIn("## 默认输出结构", rendered)

    def test_split_frontmatter_closing_dashes_preserved(self) -> None:
        """off-by-one 回归：frontmatter block 含闭合 --- 及其行尾换行，body 无前导空行。"""
        from runtime.cognition.source_publish_check import _split_frontmatter
        block, body, nl = _split_frontmatter("---\nname: x\n---\nbody line\n")
        self.assertEqual(block, "---\nname: x\n---\n")
        self.assertEqual(body, "body line")
        self.assertEqual(nl, "\n")

    def test_render_frontmatter_body_no_blank_line(self) -> None:
        """渲染输出 frontmatter 与 body 直接相邻（闭合 --- 后无空行插入）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        rendered, err = _render_agent_payload(
            "---\nname: x\n---\nbody line\n", self._render_entry(), "copilot",
        )
        self.assertEqual(err, "")
        self.assertIn("---\nbody line\n", rendered)
        self.assertNotIn("---\n\nbody line", rendered)

    def test_render_trailing_single_newline(self) -> None:
        """渲染产物恒以单 \\n 结尾（不接受每文件保留尾部形态）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        for source_text in (
            "---\nname: x\n---\nbody line",      # 源无尾部换行
            "---\nname: x\n---\nbody line\n",    # 源单尾部换行
            "---\nname: x\n---\nbody line\n\n",  # 源多尾部换行
        ):
            rendered, err = _render_agent_payload(
                source_text, self._render_entry(renderTemplate="host-default"), "copilot",
            )
            self.assertEqual(err, "")
            self.assertTrue(rendered.endswith("\n"), source_text)
            self.assertFalse(rendered.endswith("\n\n"), source_text)

    # ── extraSections / backward compatibility ─────────────────────────────

    def test_extra_sections_rendered(self) -> None:
        """extraSections 元数据 → 渲染 = 源 + 附加段（附加段回归源侧模板化）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        self._write_agent_source()
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(extraSections="## 默认输出结构\n\n### 决策\n- APPROVE / FREEZE / ESCALATE\n"),
            "copilot",
        )
        self.assertEqual(err, "")
        self.assertIn("## 默认输出结构", rendered)
        self.assertIn("### 决策", rendered)
        self.assertIn("- APPROVE / FREEZE / ESCALATE", rendered)

    def test_no_render_metadata_byte_passthrough(self) -> None:
        """无渲染元数据 + host=copilot → 渲染 = 源字节（旧 manifest 向后兼容）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        source_text = "---\nname: X\ntools: [read]\nuser-invocable: true\n---\nbody\n"
        self._write_agent_source(source_text)
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(), "copilot",
        )
        self.assertEqual(err, "")
        self.assertEqual(rendered, source_text)

    def test_claude_renders_without_metadata(self) -> None:
        """host=claude 无元数据也走渲染面（frontmatter 形状映射必须）。"""
        from runtime.cognition.source_publish_check import _is_render_entry
        self.assertTrue(_is_render_entry(self._render_entry(), "claude"))
        self.assertFalse(_is_render_entry(self._render_entry(), "copilot"))

    def test_unsupported_render_template(self) -> None:
        """renderTemplate 未知值 → unsupported_render_template 错误。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        self._write_agent_source()
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(renderTemplate="v2-custom"), "copilot",
        )
        self.assertEqual(rendered, "")
        self.assertIn("unsupported_render_template", err)

    # ── target derivation ──────────────────────────────────────────────────

    def test_claude_target_derivation(self) -> None:
        """目标派生：.github/agents → .claude/agents、.agent.md → .md。"""
        from runtime.cognition.source_publish_check import _derive_host_target
        derived, err = _derive_host_target(
            "TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md", "claude"
        )
        self.assertEqual(err, "")
        self.assertEqual(derived, "TriMetaverse/.claude/agents/ceo-chief-of-staff.md")
        copilot_derived, copilot_err = _derive_host_target(
            "TriMetaverse/.github/agents/ceo.agent.md", "copilot"
        )
        self.assertEqual(copilot_err, "")
        self.assertEqual(copilot_derived, "TriMetaverse/.github/agents/ceo.agent.md")

    def test_derive_host_target_error(self) -> None:
        """目标不含宿主面根 → host_target_not_derivable。"""
        from runtime.cognition.source_publish_check import _derive_host_target
        derived, err = _derive_host_target("TriMetaverse/docs/ceo.md", "claude")
        self.assertEqual(derived, "")
        self.assertIn("host_target_not_derivable", err)

    # ── derived-consistency check ──────────────────────────────────────────

    def test_derived_identical_dry_run(self) -> None:
        """渲染产物 == live → derived_identical（派生一致）。"""
        from runtime.cognition.source_publish_check import _publish_single_agent
        self._write_agent_source()
        source_file = self.source.root.joinpath("source-agents/ceo/ceo.agent.md")
        entry = self._render_entry(extraSections="## 默认输出结构\n\n### 决策\n- 内容\n")
        target_rel = "TriMetaverse/.github/agents/ceo.agent.md"
        target_file = self.support.write(target_rel, "")
        # live = 源 + 附加段（write_bytes：字节稳定，避免 write_text 换行转换）
        rendered, _ = _render_agent_payload_for(source_file, entry, "copilot")
        target_file.write_bytes(rendered.encode("utf-8"))
        item = _publish_single_agent(
            source_file, target_file, entry, dry_run=True, host_id="copilot"
        )
        self.assertEqual(item.action, "derived_identical")

    def test_derived_drift_dry_run(self) -> None:
        """live 与渲染不一致 → derived_drift（派生漂移，dry-run 不写）。"""
        from runtime.cognition.source_publish_check import _publish_single_agent
        self._write_agent_source()
        source_file = self.source.root.joinpath("source-agents/ceo/ceo.agent.md")
        entry = self._render_entry(extraSections="## 默认输出结构\n\n### 决策\n- 内容\n")
        target_rel = "TriMetaverse/.github/agents/ceo.agent.md"
        self.support.write(target_rel, "stale live content\n")
        target_file = self.support.root / target_rel
        item = _publish_single_agent(
            source_file, target_file, entry, dry_run=True, host_id="copilot"
        )
        self.assertEqual(item.action, "derived_drift")
        self.assertEqual(
            self.support.root.joinpath(target_rel).read_text(encoding="utf-8"),
            "stale live content\n",
        )

    def test_derived_drift_execute_updates(self) -> None:
        """派生漂移 + execute → updated，写入渲染产物（after_hash == 渲染 hash）。"""
        from runtime.cognition.source_publish_check import _publish_single_agent
        self._write_agent_source()
        source_file = self.source.root.joinpath("source-agents/ceo/ceo.agent.md")
        entry = self._render_entry(extraSections="## 默认输出结构\n\n### 决策\n- 内容\n")
        target_rel = "TriMetaverse/.github/agents/ceo.agent.md"
        self.support.write(target_rel, "stale live content\n")
        target_file = self.support.root / target_rel
        item = _publish_single_agent(
            source_file, target_file, entry, dry_run=False, host_id="copilot"
        )
        self.assertEqual(item.action, "updated")
        self.assertEqual(item.after_hash, item.source_hash)
        rendered, _ = _render_agent_payload_for(source_file, entry, "copilot")
        self.assertEqual(
            target_file.read_text(encoding="utf-8"), rendered,
        )

    def test_copy_surface_skipped_identical_kept(self) -> None:
        """复制面（无元数据）保持 skipped_identical（旧 action 词零回归）。"""
        from runtime.cognition.source_publish_check import _publish_single_agent
        source_text = "---\nname: X\ntools: [read]\nuser-invocable: true\n---\nbody\n"
        self._write_agent_source(source_text)
        source_file = self.source.root.joinpath("source-agents/ceo/ceo.agent.md")
        entry = self._render_entry()
        target_rel = "TriMetaverse/.github/agents/ceo.agent.md"
        self.support.write(target_rel, source_text)
        target_file = self.support.root / target_rel
        item = _publish_single_agent(
            source_file, target_file, entry, dry_run=True, host_id="copilot"
        )
        self.assertEqual(item.action, "skipped_identical")

    # ── escape protection on both hosts ────────────────────────────────────

    def test_claude_sanctioned_zone_not_protected(self) -> None:
        """claude 面 landing zone（.claude/agents/）豁免。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        self.assertFalse(_is_agent_publish_target_protected(
            "TriMetaverse/.claude/agents/ceo.md", "claude"))

    def test_claude_escape_protection(self) -> None:
        """claude 面 escape/绝对路径/父目录 → 保护。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        for bad in (
            "TriMetaverse/.claude/agents/../../outside.md",
            "C:/evil/agents/ceo.md",
            "/abs/agents/ceo.md",
        ):
            self.assertTrue(
                _is_agent_publish_target_protected(bad, "claude"),
                f"expected protected: {bad}",
            )

    def test_claude_fivepiece_rejected(self) -> None:
        """claude 面五件套后缀仍禁（landing zone 内也不可写）。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        for suffix in (".soul.md", ".memory.md", ".colleagues.md", ".social.md", ".body.md"):
            self.assertTrue(_is_agent_publish_target_protected(
                f"TriMetaverse/.claude/agents/ceo{suffix}", "claude"))

    def test_claude_binding_profiles_rejected(self) -> None:
        """claude 面 binding-profiles 禁写（白名单∩禁区跨宿主成立）。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        self.assertTrue(_is_agent_publish_target_protected(
            "TriMetaverse/.claude/binding-profiles/ceo.json", "claude"))

    def test_bare_top_level_binding_profiles_rejected_both_hosts(self) -> None:
        """PATCH-1 回归：裸顶层 binding-profiles（无前导斜杠）双宿主皆禁。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        for host in ("copilot", "claude"):
            self.assertTrue(
                _is_agent_publish_target_protected(
                    "TriMetaverse/binding-profiles/ceo.json", host
                ),
                f"expected bare top-level binding-profiles protected for {host}",
            )

    def test_copilot_host_cannot_write_claude_face(self) -> None:
        """PATCH-2 回归：copilot 宿主禁写 claude 面（.claude/agents/）。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        self.assertTrue(_is_agent_publish_target_protected(
            "TriMetaverse/.claude/agents/ceo.md", "copilot"))

    def test_claude_host_cannot_write_copilot_face(self) -> None:
        """PATCH-2 对称：claude 宿主禁写 copilot 面（.github/agents/）。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        self.assertTrue(_is_agent_publish_target_protected(
            "TriMetaverse/.github/agents/ceo.agent.md", "claude"))

    def test_agents_backup_variant_not_derivable(self) -> None:
        """PATCH-3 回归：agents-backup 变体不派生（marker 带边界斜杠）。"""
        from runtime.cognition.source_publish_check import _derive_host_target
        derived, err = _derive_host_target(
            "TriMetaverse/.github/agents-backup/ceo.agent.md", "claude"
        )
        self.assertEqual(derived, "")
        self.assertIn("host_target_not_derivable", err)

    def test_flip_logic_variant_dirs_protected_both_hosts(self) -> None:
        """翻转逻辑回归：非豁免前缀一律保护（agents 变体目录全拒）。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        variants = (
            "TriMetaverse/.github/agents-backup/ceo.agent.md",
            "TriMetaverse/agents_backup/ceo.agent.md",
            "TriMetaverse/.github/agents.bak/ceo.agent.md",
            "TriMetaverse/.claude/agents-backup/ceo.md",
            "TriMetaverse/agents-backup/ceo.agent.md",
            "TriMetaverse/docs/x.md",
            "Triavatar/.github/agents/x.agent.md",
        )
        for host in ("copilot", "claude"):
            for variant in variants:
                self.assertTrue(
                    _is_agent_publish_target_protected(variant, host),
                    f"expected protected ({host}): {variant}",
                )

    def test_flip_logic_sanctioned_zones_exempt(self) -> None:
        """翻转逻辑豁免面：copilot→.github/agents/、claude→.claude/agents/。"""
        from runtime.cognition.source_publish_check import _is_agent_publish_target_protected
        self.assertFalse(_is_agent_publish_target_protected(
            "TriMetaverse/.github/agents/ceo.agent.md", "copilot"))
        self.assertFalse(_is_agent_publish_target_protected(
            "TriMetaverse/.claude/agents/ceo.md", "claude"))

    # ── Chinese content / action vocabulary ────────────────────────────────

    def test_chinese_content_rendered(self) -> None:
        """中文正文渲染往返一致（UTF-8 无 BOM、行尾 \n）。"""
        from runtime.cognition.source_publish_check import _render_agent_payload
        chinese_body = "你是赛博公司的全栈开发工程师。\n职责包括编码实现与自测。\n"
        self._write_agent_source(
            "---\nname: FullStackDeveloper\ndescription: \"中文描述：全栈开发\"\n"
            "tools: [read, edit]\nuser-invocable: true\n---\n" + chinese_body
        )
        rendered, err = _render_agent_payload(
            self.source.root.joinpath("source-agents/ceo/ceo.agent.md").read_text(encoding="utf-8"),
            self._render_entry(extraSections="## 默认输出结构\n\n### 实现方案\n- 实现思路\n"),
            "claude",
        )
        self.assertEqual(err, "")
        self.assertIn(chinese_body.rstrip("\n"), rendered)
        self.assertIn("中文描述：全栈开发", rendered)
        self.assertIn("### 实现方案", rendered)
        encoded = rendered.encode("utf-8")
        self.assertNotIn(b"\xef\xbb\xbf", encoded)  # no BOM
        self.assertNotIn(b"\r\n", encoded)  # stable \n newlines

    def test_ade_actions_include_derived(self) -> None:
        """derived_identical / derived_drift 进 ADE_ACTIONS 与 publish-agents 域子集。"""
        from runtime.cognition.source_publish_check import (
            ADE_ACTIONS, ADE_ACTIONS_PER_SCOPE,
        )
        self.assertIn("derived_identical", ADE_ACTIONS)
        self.assertIn("derived_drift", ADE_ACTIONS)
        self.assertIn(
            "derived_identical", ADE_ACTIONS_PER_SCOPE["publish-agents"],
        )
        self.assertIn(
            "derived_drift", ADE_ACTIONS_PER_SCOPE["publish-agents"],
        )


def _render_agent_payload_for(
    source_file: Path, entry: dict[str, Any], host_id: str
) -> tuple[str, str]:
    """Test helper: render *source_file* payload for *host_id*."""
    from runtime.cognition.source_publish_check import _render_agent_payload
    return _render_agent_payload(
        source_file.read_text(encoding="utf-8-sig"), entry, host_id,
    )


class AgentPublishHostCLITests(unittest.TestCase):
    """CLI integration tests for --host={copilot|claude}."""

    def setUp(self) -> None:
        self.source = TreeFixture()
        self.support = TreeFixture()
        self._write_manifest_with_agent()

    def tearDown(self) -> None:
        self.source.cleanup()

    def _write_manifest_with_agent(self) -> None:
        """Manifest with one render-metadata role-agent entry + source file."""
        source_text = (
            "---\nname: CEOChiefOfStaff\ndescription: \"desc\"\n"
            "tools: [read, search, edit]\nuser-invocable: true\n"
            "---\n你是 TriCompany 的 CEO 总助。\n"
        )
        manifest = {
            "manifestId": "test-v0.1",
            "liveEntries": [
                {
                    "status": "current-copilot-host-live",
                    "source": "TriCompany/source-agents/ceo/ceo.agent.md",
                    "target": "TriMetaverse/.github/agents/ceo.agent.md",
                    "kind": "role-agent",
                    "renderTemplate": "host-default",
                    "extraSections": "## 默认输出结构\n\n### 决策\n- APPROVE / FREEZE / ESCALATE\n",
                },
            ],
        }
        self.source.write(
            "source-agents/registries/trimetaverse-live-agent-publish-manifest.json",
            json.dumps(manifest),
        )
        self.source.write("source-agents/ceo/ceo.agent.md", source_text)

    def _run_cli(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable, "-m", "runtime.cognition.source_publish_check",
            "--source-root", str(self.source.root),
            "--support-root", str(self.support.root),
        ]
        args.extend(extra_args)
        return subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8",
            cwd=str(_REPO_ROOT), timeout=30,
        )

    def test_cli_host_default_copilot_compat(self) -> None:
        """默认 host=copilot：target 落 .github/agents/，派生语义（drift）。"""
        proc = self._run_cli("--publish-agents")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["scope"], "publish-agents")
        self.assertTrue(data["scope_specific"]["dry_run"])
        item = data["items"][0]
        self.assertEqual(item["action"], "derived_drift")
        self.assertIn(".github/agents/ceo.agent.md", item["target"])

    def test_cli_host_claude_dry_run_json(self) -> None:
        """--host=claude dry-run：目标派生 .claude/agents/ceo.md，派生漂移。"""
        proc = self._run_cli("--publish-agents", "--host", "claude")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["scope"], "publish-agents")
        item = data["items"][0]
        self.assertEqual(item["action"], "derived_drift")
        self.assertEqual(
            item["target"], "TriMetaverse/.claude/agents/ceo.md",
        )
        counts = data["scope_specific"]["counts"]
        self.assertEqual(counts["derived_drift"], 1)

    def test_cli_host_claude_execute_writes(self) -> None:
        """--host=claude --agent-execute：写 .claude/agents/ceo.md，形状断言。"""
        proc = self._run_cli("--publish-agents", "--host", "claude", "--agent-execute")
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        item = data["items"][0]
        self.assertEqual(item["action"], "created")
        # _resolve_agent_target_path strips the "TriMetaverse/" repo prefix —
        # the write lands at support_root/.claude/agents/ceo.md.
        written = self.support.root.joinpath(".claude/agents/ceo.md")
        self.assertTrue(written.is_file())
        content = written.read_text(encoding="utf-8")
        self.assertIn("name: CEOChiefOfStaff", content)
        self.assertIn("tools: [Read, Glob, Edit]", content)
        self.assertIn("user-invocable: true", content)
        self.assertIn("## 默认输出结构", content)
        self.assertIn("### 决策", content)
        # copilot face untouched
        self.assertFalse(
            self.support.root.joinpath(
                "TriMetaverse/.github/agents/ceo.agent.md"
            ).exists()
        )
        # re-run dry-run → derived_identical
        proc2 = self._run_cli("--publish-agents", "--host", "claude")
        data2 = json.loads(proc2.stdout)
        self.assertEqual(data2["items"][0]["action"], "derived_identical")

    def test_cli_host_invalid_choice_rejected(self) -> None:
        """--host 非法值 → argparse 拒绝（非零 rc）。"""
        proc = self._run_cli("--publish-agents", "--host", "trihost")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid choice", (proc.stdout + proc.stderr).lower())

    def test_cli_contaminated_variant_target_rejected_zero_write(self) -> None:
        """翻转逻辑 e2e：变体目录污染 manifest 整批拒绝、零写入。"""
        import json as _json
        contaminated = {
            "manifestId": "test-v0.1",
            "liveEntries": [
                {
                    "status": "current-copilot-host-live",
                    "source": "TriCompany/source-agents/ceo/ceo.agent.md",
                    "target": "TriMetaverse/.github/agents-backup/ceo.agent.md",
                    "kind": "role-agent",
                },
            ],
        }
        self.source.write(
            "source-agents/registries/trimetaverse-live-agent-publish-manifest.json",
            _json.dumps(contaminated),
        )
        # copilot 默认面 dry-run：整批拒绝 + 零写入（变体目录不落盘）
        proc = self._run_cli("--publish-agents")
        self.assertNotEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["scope"], "publish-agents")
        self.assertEqual(data["items"][0]["action"], "error")
        self.assertEqual(data["items"][0]["error"], "protected_target_rejected")
        written = list(self.support.root.rglob("*"))
        self.assertEqual(written, [], f"unexpected writes: {written}")
        # claude 面同样整批拒绝：变体目录无宿主面根 → 派生失败拒绝
        #（host_target_not_derivable，与 protected_target_rejected 拒绝效果等价）
        proc2 = self._run_cli("--publish-agents", "--host", "claude")
        self.assertNotEqual(proc2.returncode, 0)
        data2 = json.loads(proc2.stdout)
        self.assertEqual(data2["items"][0]["action"], "error")
        self.assertIn(
            "host_target_not_derivable", data2["items"][0]["error"],
        )


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
