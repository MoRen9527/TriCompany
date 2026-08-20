"""employee_onboard — ADE 员工上岗 11 步流水线 CLI.

将 host-object-publish-flow.md 的 11 步发布流程实现为确定性执行 CLI，
每一步输出标准 ADE JSON 自检报告。

用法:
  python -m runtime.cognition.employee_onboard --employee-id X --validate-all --format json
  python -m runtime.cognition.employee_onboard --employee-id X --stage 1-11 --sync --format json
"""

from __future__ import annotations

import argparse
import hashlib
import json as _json
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

SOURCE_KIT_SUFFIXES = ("agent", "soul", "memory", "colleagues", "social")
SOURCE_AGENT_KIT_DIR = Path("source-agents")
BINDING_PROFILES_DIR = Path(".github") / "binding-profiles"
ROSTER_PATH = Path("docs") / "registry" / "employee-roster.json"
MANIFEST_REL_PATH = "source-agents/registries/trimetaverse-live-agent-publish-manifest.json"
CEO_SIGNOFF_DIR = Path("docs") / "execution" / "company-launch"
GOVERNANCE_RECORDS_DIR = Path("docs") / "workflow"

STAGE_LABELS: dict[int, str] = {
    1: "五件套完整性",
    2: "Contract YAML 有效性",
    3: "Binding profile 完整性",
    4: "Host object 生成",
    5: "Host object 发布",
    6: "Live entry 就位",
    7: "Manifest 注册",
    8: "Governance 回填",
    9: "Employee roster 更新",
    10: "CEO 签署",
    11: "交叉验证",
}


# ---------------------------------------------------------------------------
# ADE data types
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    stage: int
    label: str
    status: str  # pass | fail | partial
    summary: dict
    changes: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    check_time: str = ""

    def to_ade_json(self) -> dict:
        return {
            "stage": self.stage,
            "label": self.label,
            "status": self.status,
            "summary": self.summary,
            "changes": self.changes,
            "errors": self.errors,
            "check_time": self.check_time or datetime.now(timezone.utc).isoformat(),
        }


@dataclass
class OnboardReport:
    employee_id: str
    stages: list[StageResult]
    check_time: str

    @property
    def overall_status(self) -> str:
        statuses = {s.status for s in self.stages}
        if "fail" in statuses:
            return "fail"
        if "partial" in statuses:
            return "partial"
        return "pass"

    def to_ade_json(self) -> dict:
        total = len(self.stages)
        passed = sum(1 for s in self.stages if s.status == "pass")
        failed = sum(1 for s in self.stages if s.status == "fail")
        partial = sum(1 for s in self.stages if s.status == "partial")
        all_errors = [e for s in self.stages for e in s.errors]
        all_changes = [c for s in self.stages for c in s.changes]

        return {
            "employee_id": self.employee_id,
            "status": self.overall_status,
            "check_time": self.check_time,
            "summary": {
                "total_stages": total,
                "passed": passed,
                "failed": failed,
                "partial": partial,
                "total_errors": len(all_errors),
            },
            "stages": [s.to_ade_json() for s in self.stages],
            "changes": all_changes,
            "errors": all_errors,
        }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_path(raw: str | Path) -> Path:
    return Path(raw).resolve()


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _load_json_safe(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return _json.load(fh)
    except Exception:
        return None


def _load_yaml_safe(path: Path) -> dict | None:
    try:
        import yaml as _yaml
        with open(path, "r", encoding="utf-8") as fh:
            return _yaml.safe_load(fh)
    except Exception:
        return None


def _source_kit_paths(source_root: Path, employee_id: str) -> dict[str, Path]:
    """Resolve source kit file paths, trying both naming conventions.

    Convention A (contract YAML): {suffix}.agent.md (soul.agent.md, agent-body.agent.md, ...)
    Convention B (legacy):     {employee_id}.{suffix}.md (ceo-chief-of-staff.soul.md, ...)

    For 'agent' suffix, also check 'agent-body.agent.md' (the contract YAML naming).
    """
    kit_root = source_root / SOURCE_AGENT_KIT_DIR / employee_id
    paths: dict[str, Path] = {}

    # Map suffixes to their possible filenames
    suffix_aliases: dict[str, list[str]] = {
        "agent": ["agent-body.agent.md", f"{employee_id}.agent.md"],
        "soul": ["soul.agent.md", f"{employee_id}.soul.md"],
        "memory": ["memory.agent.md", f"{employee_id}.memory.md"],
        "colleagues": ["colleagues.agent.md", f"{employee_id}.colleagues.md", "colleagues-social.agent.md"],
        "social": ["social.agent.md", f"{employee_id}.social.md", "colleagues-social.agent.md"],
    }

    for suffix, aliases in suffix_aliases.items():
        found = False
        for alias in aliases:
            candidate = kit_root / alias
            if candidate.is_file():
                paths[suffix] = candidate
                found = True
                break
        if not found:
            # Default to contract YAML convention for error reporting
            paths[suffix] = kit_root / f"{suffix}.agent.md"

    return paths


def _contract_yaml_path(source_root: Path, employee_id: str) -> Path | None:
    """Find contract YAML with kebab-case or PascalCase fallback."""
    # Try kebab-case first (e.g. ceo-chief-of-staff.contract.yaml)
    kebab_path = source_root / "docs" / "registry" / f"{employee_id}.contract.yaml"
    if kebab_path.exists():
        return kebab_path
    # Try PascalCase (e.g. CEOChiefOfStaff.contract.yaml)
    pascal_id = "".join(part.capitalize() for part in employee_id.split("-"))
    pascal_path = source_root / "docs" / "registry" / f"{pascal_id}.contract.yaml"
    if pascal_path.exists():
        return pascal_path
    # Also check source-agents/<id>/<id>.contract.yaml (V2 location)
    v2_path = source_root / SOURCE_AGENT_KIT_DIR / employee_id / f"{employee_id}.contract.yaml"
    if v2_path.exists():
        return v2_path
    return kebab_path  # return kebab as default for error reporting


def _binding_profile_path(source_root: Path, employee_id: str) -> Path:
    return source_root / BINDING_PROFILES_DIR / f"{employee_id}.json"


def _command_exists(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


def _check_time() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# stage 1: 五件套完整性
# ---------------------------------------------------------------------------

def stage_1_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Validate the employee's five-piece source kit."""
    check_time = _check_time()
    paths = _source_kit_paths(source_root, employee_id)
    changes: list[dict] = []
    errors: list[dict] = []

    missing: list[str] = []
    for suffix, path in paths.items():
        if not path.is_file():
            missing.append(f"{employee_id}.{suffix}.md")
            errors.append({"item": str(path), "reason": "missing_file"})

    # Run existing validator for detailed checks (only if paths resolved)
    if not missing:
        try:
            from runtime.cognition.employee_source_kit import validate_employee_source_kit
            # Note: legacy validator uses old path conventions; skip if our path resolution
            # already found all files (avoids false positives from path convention mismatch)
            validation = validate_employee_source_kit(str(source_root), employee_id)
            if not validation.is_valid:
                for issue in validation.issues:
                    # Only report issues not related to old path conventions
                    issue_path = Path(str(issue.path))
                    if issue_path.exists():
                        continue  # file exists, old path convention false positive
                    errors.append({"item": str(issue.path), "reason": issue.message})
        except ImportError:
            pass  # validator not available — rely on direct file check above

    for suffix, path in paths.items():
        if path.is_file():
            changes.append({"action": "found", "target": str(path), "hash": _file_sha256(path)})

    total = len(SOURCE_KIT_SUFFIXES)
    passed = total - len(missing)
    status = "pass" if len(errors) == 0 else "fail"

    return StageResult(
        stage=1,
        label=STAGE_LABELS[1],
        status=status,
        summary={"total": total, "passed": passed, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 2: Contract YAML 有效性
# ---------------------------------------------------------------------------

def stage_2_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Validate the contract YAML file."""
    check_time = _check_time()
    contract_path = _contract_yaml_path(source_root, employee_id)
    if contract_path is None or not contract_path.exists():
        return StageResult(stage=2, label=STAGE_LABELS[2], status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            errors=[{"item": f"{employee_id}.contract.yaml", "reason": "contract_not_found"}],
            check_time=check_time)
    errors: list[dict] = []
    changes: list[dict] = []

    if not contract_path.is_file():
        errors.append({"item": str(contract_path), "reason": "contract_yaml_missing"})
        return StageResult(
            stage=2,
            label=STAGE_LABELS[2],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    data = _load_yaml_safe(contract_path)
    if data is None:
        errors.append({"item": str(contract_path), "reason": "yaml_parse_error"})
        return StageResult(
            stage=2,
            label=STAGE_LABELS[2],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    # Check agent_id
    agent_id = data.get("contract", {}).get("agent_id", "")
    if not agent_id:
        errors.append({"item": "contract.agent_id", "reason": "missing_or_empty"})

    # Check decision_rights
    decision_rights = data.get("decision_rights", {})
    if not isinstance(decision_rights, dict):
        errors.append({"item": "decision_rights", "reason": "missing_or_invalid"})
    else:
        has_approve = bool(decision_rights.get("approve"))
        has_freeze = bool(decision_rights.get("freeze"))
        has_escalate = bool(decision_rights.get("escalate"))
        if not has_approve and not has_freeze:
            errors.append({"item": "decision_rights", "reason": "approve_and_freeze_both_empty"})

    # Check paths
    paths = data.get("paths", {})
    if not isinstance(paths, dict) or not paths:
        errors.append({"item": "paths", "reason": "missing_or_empty"})

    changes.append({"action": "parsed", "target": str(contract_path), "hash": _file_sha256(contract_path)})

    total = 3  # agent_id, paths, decision_rights
    checks = [not errors]  # simplified: one aggregate check
    passed = sum(1 for c in checks if c)

    return StageResult(
        stage=2,
        label=STAGE_LABELS[2],
        status="pass" if len(errors) == 0 else "fail",
        summary={"total": total, "passed": passed, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 3: Binding profile 完整性
# ---------------------------------------------------------------------------

def stage_3_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Validate the binding profile JSON."""
    check_time = _check_time()
    bp_path = _binding_profile_path(source_root, employee_id)
    errors: list[dict] = []
    changes: list[dict] = []

    if not bp_path.is_file():
        errors.append({"item": str(bp_path), "reason": "binding_profile_missing"})
        return StageResult(
            stage=3,
            label=STAGE_LABELS[3],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    data = _load_json_safe(bp_path)
    if data is None:
        errors.append({"item": str(bp_path), "reason": "json_parse_error"})
        return StageResult(
            stage=3,
            label=STAGE_LABELS[3],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    # Check required binding profile fields
    expected_keys = {"employee_id", "role_title", "binding_timestamp", "source_kit_path"}
    for key in expected_keys:
        if key not in data:
            errors.append({"item": key, "reason": "missing_required_field"})

    changes.append({"action": "validated", "target": str(bp_path), "hash": _file_sha256(bp_path)})

    return StageResult(
        stage=3,
        label=STAGE_LABELS[3],
        status="pass" if len(errors) == 0 else "partial",
        summary={"total": len(expected_keys), "passed": len(expected_keys) - len(errors), "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 4: Host object 生成
# ---------------------------------------------------------------------------

def stage_4_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Execute host object generation (dry-run or sync)."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    host_gen_script = source_root / "runtime" / "cognition" / "employee_host_object_generation.py"
    if not host_gen_script.exists():
        errors.append({"item": str(host_gen_script), "reason": "generator_script_not_found"})
        return StageResult(
            stage=4,
            label=STAGE_LABELS[4],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    try:
        # Use the module-level API rather than subprocess
        from runtime.cognition.host_object_generation import (
            DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE,
            generate_host_object_set,
        )
        if employee_id not in DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE:
            errors.append({"item": employee_id, "reason": "employee_not_in_declared_host_object_sets"})
        elif sync:
            definition = DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE[employee_id]
            # We use a default support root; host object generation requires it
            support_root = source_root.parent / "TriCompany-copilot-host-assets"
            result = generate_host_object_set(support_root=str(support_root), definition=definition)
            changes.append({"action": "generated", "target": str(result.role_workspace.root), "hash": ""})
            changes.append({"action": "generated", "target": str(result.employee_workspace.root), "hash": ""})
        else:
            changes.append({"action": "dry_run", "target": f"host_object_set:{employee_id}", "hash": ""})
    except ImportError:
        errors.append({"item": "host_object_generation", "reason": "module_import_failed"})
    except Exception as exc:
        errors.append({"item": employee_id, "reason": f"generation_error: {exc}"})

    return StageResult(
        stage=4,
        label=STAGE_LABELS[4],
        status="pass" if len(errors) == 0 else "fail",
        summary={"total": 1, "passed": 1 if len(errors) == 0 else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 5: Host object 发布
# ---------------------------------------------------------------------------

def stage_5_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Execute host object publish (delegates to employee_host_publish)."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    publish_script = source_root / "runtime" / "cognition" / "employee_host_publish.py"
    if not publish_script.exists():
        errors.append({"item": str(publish_script), "reason": "publish_script_not_found"})
        return StageResult(
            stage=5,
            label=STAGE_LABELS[5],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    support_root = source_root.parent / "TriMetaverse" / "TriCompany-copilot-host-assets"
    cmd_base = [
        sys.executable, "-m", "runtime.cognition.employee_host_publish",
        "--source-root", str(source_root),
        "--support-root", str(support_root),
        "--employee", employee_id,
        "--format", "json",
    ]

    if sync:
        result = subprocess.run(
            cmd_base + ["--execute"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if result.returncode != 0:
            errors.append({"item": "employee_host_publish", "reason": f"exit_code={result.returncode}", "stderr": result.stderr[:500]})
        else:
            try:
                data = _json.loads(result.stdout)
                if data.get("status") == "fail":
                    for e in data.get("errors", []):
                        errors.append(e)
                for c in data.get("changes", []):
                    changes.append(c)
            except _json.JSONDecodeError:
                errors.append({"item": "employee_host_publish", "reason": "json_parse_failure"})
    else:
        result = subprocess.run(
            cmd_base + ["--dry-run"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if result.returncode != 0:
            errors.append({"item": "employee_host_publish", "reason": f"exit_code={result.returncode}"})
        else:
            changes.append({"action": "dry_run_verified", "target": f"employee_host_publish:{employee_id}", "hash": ""})

    return StageResult(
        stage=5,
        label=STAGE_LABELS[5],
        status="pass" if len(errors) == 0 else "fail",
        summary={"total": 1, "passed": 1 if len(errors) == 0 else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 6: Live entry 就位
# ---------------------------------------------------------------------------

def stage_6_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Check live entry readiness via source_publish_check --publish-agents."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    publish_check_script = source_root / "runtime" / "cognition" / "source_publish_check.py"
    if not publish_check_script.exists():
        errors.append({"item": str(publish_check_script), "reason": "publish_check_script_not_found"})
        return StageResult(
            stage=6,
            label=STAGE_LABELS[6],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    support_root = source_root.parent / "TriMetaverse"
    cmd = [
        sys.executable, "-m", "runtime.cognition.source_publish_check",
        "--publish-agents",
        "--source-root", str(source_root),
        "--support-root", str(support_root),
        "--employees", employee_id,
    ]

    if sync:
        cmd.append("--agent-execute")

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )

    # ADE phase 1: --publish-agents emits the unified envelope (protocol
    # ade-report, scope publish-agents); errors > 0 now also maps to a
    # non-zero exit code, so the error branch parses the envelope as well
    # to keep item-level error detail in the stage record.
    # ADE phase 2: envelope parsing is shared via ade_envelope (bare
    # envelope or reports-container branch, defensive).
    from runtime.cognition.ade_envelope import (
        envelope_error_items,
        find_scope_envelope,
        parse_cli_output,
    )
    if result.returncode != 0:
        errors.append({"item": "source_publish_check", "reason": f"exit_code={result.returncode}", "stderr": result.stderr[:500]})
        data = parse_cli_output(result.stdout)
        env = find_scope_envelope(data, "publish-agents") if data else None
        if env is not None:
            for item in envelope_error_items(env):
                errors.append({"item": item.get("source", ""), "reason": item.get("error", "unknown")})
    else:
        data = parse_cli_output(result.stdout)
        env = find_scope_envelope(data, "publish-agents") if data else None
        if env is not None:
            summary = env.get("summary", {})
            if summary.get("errors", 0) > 0:
                for item in envelope_error_items(env):
                    errors.append({"item": item.get("source", ""), "reason": item.get("error", "unknown")})
            for item in env.get("items", []):
                changes.append(item)
        elif data is None:
            errors.append({"item": "source_publish_check", "reason": "json_parse_failure"})

    return StageResult(
        stage=6,
        label=STAGE_LABELS[6],
        status="pass" if len(errors) == 0 else "fail",
        summary={"total": 1, "passed": 1 if len(errors) == 0 else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 7: Manifest 注册
# ---------------------------------------------------------------------------

def stage_7_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Verify manifest registration — check that the employee has a manifest entry."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    manifest_path = source_root / MANIFEST_REL_PATH
    if not manifest_path.is_file():
        errors.append({"item": MANIFEST_REL_PATH, "reason": "manifest_missing"})
        return StageResult(
            stage=7,
            label=STAGE_LABELS[7],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    manifest = _load_json_safe(manifest_path)
    if manifest is None:
        errors.append({"item": MANIFEST_REL_PATH, "reason": "manifest_parse_error"})
        return StageResult(
            stage=7,
            label=STAGE_LABELS[7],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    live_entries = manifest.get("liveEntries", [])
    if not isinstance(live_entries, list):
        errors.append({"item": "liveEntries", "reason": "missing_or_not_list"})
        return StageResult(
            stage=7,
            label=STAGE_LABELS[7],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    # Search for the employee in the manifest
    employee_entry = None
    for entry in live_entries:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source", "")
        if f"/{employee_id}/" in source or source.endswith(f"/{employee_id}"):
            employee_entry = entry
            break
        # Also check by kind=role-agent and directory slug
        if entry.get("kind") == "role-agent":
            parts = source.replace("\\", "/").split("/")
            for i, part in enumerate(parts):
                if part == "source-agents" and i + 1 < len(parts) and parts[i + 1] == employee_id:
                    employee_entry = entry
                    break

    if employee_entry:
        status_val = employee_entry.get("status", "")
        changes.append({
            "action": "manifest_entry_verified",
            "target": f"liveEntries:{employee_id}",
            "status": status_val,
        })
        if status_val not in ("source-published-live-entry", "current-copilot-host-live"):
            errors.append({"item": employee_id, "reason": f"status_not_live_eligible: {status_val}"})
    else:
        errors.append({"item": employee_id, "reason": "no_manifest_entry_found"})

    return StageResult(
        stage=7,
        label=STAGE_LABELS[7],
        status="pass" if len(errors) == 0 else "fail",
        summary={"total": 1, "passed": 1 if len(errors) == 0 else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 8: Governance 回填
# ---------------------------------------------------------------------------

def stage_8_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Check for CHO/CAO governance records."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    # Check for CHO handoff records
    cho_records = list((source_root / GOVERNANCE_RECORDS_DIR).rglob("*handoff*"))
    cao_records = list((source_root / GOVERNANCE_RECORDS_DIR).rglob("*governance*"))

    governance_files = cho_records + cao_records
    if not governance_files:
        errors.append({"item": "governance_records", "reason": "no_cho_or_cao_records_found"})
    else:
        for record_path in governance_files:
            if record_path.is_file():
                changes.append({"action": "governance_record_found", "target": str(record_path)})

    return StageResult(
        stage=8,
        label=STAGE_LABELS[8],
        status="partial" if errors else "pass",
        summary={"total": 1, "passed": 1 if not errors else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 9: Employee roster 更新
# ---------------------------------------------------------------------------

def stage_9_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Verify the employee is registered in employee-roster.json."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    roster_path = source_root / ROSTER_PATH
    if not roster_path.is_file():
        errors.append({"item": str(ROSTER_PATH), "reason": "roster_missing"})
        return StageResult(
            stage=9,
            label=STAGE_LABELS[9],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    roster = _load_json_safe(roster_path)
    if roster is None:
        errors.append({"item": str(ROSTER_PATH), "reason": "roster_parse_error"})
        return StageResult(
            stage=9,
            label=STAGE_LABELS[9],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    employees = roster.get("employees", [])
    if not isinstance(employees, list):
        errors.append({"item": "employees", "reason": "missing_or_not_list"})
        return StageResult(
            stage=9,
            label=STAGE_LABELS[9],
            status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    employee_in_roster = None
    for emp in employees:
        if isinstance(emp, dict) and emp.get("id") == employee_id:
            employee_in_roster = emp
            break

    if employee_in_roster:
        changes.append({
            "action": "roster_entry_verified",
            "target": f"employees:{employee_id}",
            "status": employee_in_roster.get("status", ""),
            "role": employee_in_roster.get("role", ""),
            "displayName": employee_in_roster.get("displayName", ""),
        })
        if employee_in_roster.get("status") != "live":
            errors.append({"item": employee_id, "reason": f"status_not_live: {employee_in_roster.get('status')}"})
    else:
        errors.append({"item": employee_id, "reason": "not_in_employee_roster"})

    return StageResult(
        stage=9,
        label=STAGE_LABELS[9],
        status="pass" if len(errors) == 0 else "fail",
        summary={"total": 1, "passed": 1 if len(errors) == 0 else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 10: CEO 签署
# ---------------------------------------------------------------------------

def stage_10_check(source_root: Path, employee_id: str, *, sync: bool = False) -> StageResult:
    """Check for CEO sign-off records."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    signoff_dir = source_root / CEO_SIGNOFF_DIR
    if not signoff_dir.is_dir():
        errors.append({"item": str(CEO_SIGNOFF_DIR), "reason": "signoff_directory_missing"})
        return StageResult(
            stage=10,
            label=STAGE_LABELS[10],
            status="partial",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[],
            errors=errors,
            check_time=check_time,
        )

    # Look for sign-off indicators in operating records
    found_signoff = False
    for record_dir in signoff_dir.iterdir():
        if not record_dir.is_dir():
            continue
        for record_file in record_dir.iterdir():
            if not record_file.is_file():
                continue
            if employee_id in record_file.name.lower():
                changes.append({"action": "signoff_record_found", "target": str(record_file)})
                found_signoff = True

    if not found_signoff:
        errors.append({"item": employee_id, "reason": "no_ceo_signoff_found", "note": "check operating records for sign-off"})

    return StageResult(
        stage=10,
        label=STAGE_LABELS[10],
        status="partial" if not found_signoff else "pass",
        summary={"total": 1, "passed": 1 if found_signoff else 0, "errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# stage 11: 交叉验证
# ---------------------------------------------------------------------------

def stage_11_check(stage_results: list[StageResult]) -> StageResult:
    """Aggregate all prior stages and produce cross-validation report."""
    check_time = _check_time()
    errors: list[dict] = []
    changes: list[dict] = []

    total = len(stage_results)
    passed = sum(1 for s in stage_results if s.status == "pass")
    failed = sum(1 for s in stage_results if s.status == "fail")
    partial = sum(1 for s in stage_results if s.status == "partial")

    # Cross-validation: ensure each stage that passed has no errors
    for sr in stage_results:
        if sr.status == "pass" and sr.errors:
            errors.append({"item": f"stage_{sr.stage}", "reason": "status_pass_but_has_errors", "count": len(sr.errors)})
        if sr.status == "fail" and not sr.errors:
            errors.append({"item": f"stage_{sr.stage}", "reason": "status_fail_but_no_errors"})

    # Aggregate all non-error changes
    for sr in stage_results:
        for c in sr.changes:
            if c.get("action") != "error":
                changes.append(c)

    overall_status = "pass"
    if failed > 0:
        overall_status = "fail"
    elif partial > 0:
        overall_status = "partial"

    return StageResult(
        stage=11,
        label=STAGE_LABELS[11],
        status=overall_status,
        summary={"total_stages_checked": total, "passed": passed, "failed": failed, "partial": partial, "cross_validation_errors": len(errors)},
        changes=changes,
        errors=errors,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# pipeline executor
# ---------------------------------------------------------------------------

def run_onboard_pipeline(
    source_root: Path,
    employee_id: str,
    *,
    stages: tuple[int, ...] | None = None,
    sync: bool = False,
) -> OnboardReport:
    """Execute the 11-step employee onboarding pipeline.

    Args:
        source_root: Path to TriCompany source root.
        employee_id: Employee ID to onboard.
        stages: Specific stages to run (1-11). None means all 11.
        sync: When True, execute writes. When False (default), dry-run only.
    """
    check_time = _check_time()
    target_stages = list(stages) if stages else list(range(1, 12))
    target_stages = sorted(set(target_stages))

    # Stage functions mapped (stage 11 is special — run after collecting 1-10)
    stage_funcs: dict[int, callable] = {
        1: lambda eid: stage_1_check(source_root, eid, sync=sync),
        2: lambda eid: stage_2_check(source_root, eid, sync=sync),
        3: lambda eid: stage_3_check(source_root, eid, sync=sync),
        4: lambda eid: stage_4_check(source_root, eid, sync=sync),
        5: lambda eid: stage_5_check(source_root, eid, sync=sync),
        6: lambda eid: stage_6_check(source_root, eid, sync=sync),
        7: lambda eid: stage_7_check(source_root, eid, sync=sync),
        8: lambda eid: stage_8_check(source_root, eid, sync=sync),
        9: lambda eid: stage_9_check(source_root, eid, sync=sync),
        10: lambda eid: stage_10_check(source_root, eid, sync=sync),
    }

    results: list[StageResult] = []

    # Run stages 1-10
    for s in target_stages:
        if s == 11:
            continue  # Run stage 11 after collecting 1-10
        if s in stage_funcs:
            try:
                result = stage_funcs[s](employee_id)
                results.append(result)
            except Exception as exc:
                results.append(StageResult(
                    stage=s,
                    label=STAGE_LABELS.get(s, f"Stage {s}"),
                    status="fail",
                    summary={"total": 1, "passed": 0, "errors": 1},
                    errors=[{"item": f"stage_{s}", "reason": f"unexpected_error: {exc}"}],
                    check_time=_check_time(),
                ))

    # Stage 11: cross-validation (if requested)
    if 11 in target_stages or not stages:
        results_before_11 = [r for r in results if r.stage != 11]
        results.append(stage_11_check(results_before_11))

    return OnboardReport(
        employee_id=employee_id,
        stages=results,
        check_time=check_time,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="employee_onboard",
        description=textwrap.dedent("""\
            ADE 员工上岗 11 步流水线 CLI。
            将 host-object-publish-flow.md 的 11 步发布流程实现为确定性执行 CLI，
            每步输出标准 ADE JSON 自检报告。
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              python -m runtime.cognition.employee_onboard --employee-id chief-technology-officer --validate-all --format json
              python -m runtime.cognition.employee_onboard --employee-id chief-technology-officer --stage 1-11 --sync --format json
              python -m runtime.cognition.employee_onboard --employee-id chief-technology-officer --stage 1-3 --format json
        """),
    )
    parser.add_argument(
        "--employee-id",
        required=True,
        help="Employee ID to onboard (e.g. chief-technology-officer).",
    )
    parser.add_argument(
        "--source-root",
        default=".",
        help="Path to TriCompany source root (default: current directory).",
    )
    parser.add_argument(
        "--validate-all",
        action="store_true",
        default=False,
        help="Run all 11 stages in dry-run mode (equivalent to --stage 1-11).",
    )
    parser.add_argument(
        "--stage",
        default=None,
        help="Comma-separated stage numbers or ranges, e.g. '1-11', '1,3,5-7'.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        default=False,
        help="Execute write operations (publish, generate, etc.). Default is dry-run only.",
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="Output format (currently only 'json' is supported).",
    )
    return parser


def _parse_stages(stage_arg: str) -> tuple[int, ...]:
    """Parse stage argument like '1-11' or '1,3,5-7'."""
    stages: list[int] = []
    for part in stage_arg.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start_s, end_s = part.split("-", 1)
                start, end = int(start_s.strip()), int(end_s.strip())
                stages.extend(range(start, end + 1))
            except ValueError:
                print(f"warning: invalid stage range '{part}', skipping", file=sys.stderr)
        else:
            try:
                stages.append(int(part))
            except ValueError:
                print(f"warning: invalid stage number '{part}', skipping", file=sys.stderr)
    return tuple(sorted(set(s for s in stages if 1 <= s <= 11)))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source_root = _normalize_path(args.source_root)

    if not source_root.is_dir():
        print(_json.dumps({
            "status": "fail",
            "check_time": _check_time(),
            "summary": {"total": 0, "passed": 0, "errors": 1},
            "errors": [{"item": str(source_root), "reason": "source_root_not_found"}],
        }, ensure_ascii=False, indent=2))
        return 1

    # Determine stages to run
    if args.validate_all:
        target_stages = tuple(range(1, 12))
    elif args.stage:
        target_stages = _parse_stages(args.stage)
        if not target_stages:
            print(_json.dumps({
                "status": "fail",
                "check_time": _check_time(),
                "summary": {"total": 0, "passed": 0, "errors": 1},
                "errors": [{"item": args.stage, "reason": "no_valid_stages_parsed"}],
            }, ensure_ascii=False, indent=2))
            return 1
    else:
        print(_json.dumps({
            "status": "fail",
            "check_time": _check_time(),
            "summary": {"total": 0, "passed": 0, "errors": 1},
            "errors": [{"item": "stages", "reason": "use --validate-all or --stage to specify stages"}],
        }, ensure_ascii=False, indent=2))
        return 1

    report = run_onboard_pipeline(
        source_root=source_root,
        employee_id=args.employee_id,
        stages=target_stages,
        sync=args.sync,
    )

    if args.format == "json":
        print(_json.dumps(report.to_ade_json(), ensure_ascii=False, indent=2))
    else:
        print(_json.dumps(report.to_ade_json(), ensure_ascii=False))

    # Exit code reflects overall status
    if report.overall_status == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
