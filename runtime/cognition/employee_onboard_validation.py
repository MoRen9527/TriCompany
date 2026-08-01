"""employee_onboard_validation — pytest validation suite for employee_onboard CLI.

Validates the 11-step onboarding pipeline against the ADE specification.
Run: python -m pytest runtime/cognition/employee_onboard_validation.py -v
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime.cognition.employee_onboard import (
    STAGE_LABELS,
    OnboardReport,
    StageResult,
    stage_1_check,
    stage_2_check,
    stage_3_check,
    stage_7_check,
    stage_9_check,
    stage_11_check,
    run_onboard_pipeline,
    _parse_stages,
    _normalize_path,
)


# ── ADE output contract tests ─────────────────────────────────────────────

class TestADEOutputContract:
    """Verify every stage function returns ADE-compliant JSON structures."""

    def test_stage_result_ade_format(self):
        """StageResult.to_ade_json() must contain all required ADE fields."""
        sr = StageResult(
            stage=1,
            label="Test",
            status="pass",
            summary={"total": 5, "passed": 5, "errors": 0},
            changes=[{"action": "test", "target": "/tmp/test", "hash": "abc123"}],
            errors=[],
            check_time="2026-08-01T00:00:00Z",
        )
        result = sr.to_ade_json()

        assert "status" in result
        assert result["status"] in ("pass", "fail", "partial")
        assert "summary" in result
        assert isinstance(result["summary"], dict)
        assert "total" in result["summary"]
        assert "passed" in result["summary"]
        assert "errors" in result["summary"]
        assert "changes" in result
        assert isinstance(result["changes"], list)
        assert "errors" in result
        assert isinstance(result["errors"], list)
        assert "check_time" in result

    def test_onboard_report_ade_format(self):
        """OnboardReport.to_ade_json() must contain all required ADE fields."""
        stages = [
            StageResult(
                stage=1,
                label=STAGE_LABELS[1],
                status="pass",
                summary={"total": 1, "passed": 1, "errors": 0},
                changes=[],
                errors=[],
                check_time="2026-08-01T00:00:00Z",
            ),
            StageResult(
                stage=2,
                label=STAGE_LABELS[2],
                status="pass",
                summary={"total": 1, "passed": 1, "errors": 0},
                changes=[],
                errors=[],
                check_time="2026-08-01T00:00:00Z",
            ),
        ]
        report = OnboardReport(
            employee_id="test-employee",
            stages=stages,
            check_time="2026-08-01T00:00:00Z",
        )
        result = report.to_ade_json()

        assert result["employee_id"] == "test-employee"
        assert "status" in result
        assert result["status"] in ("pass", "fail", "partial")
        assert result["status"] == "pass"
        assert result["summary"]["total_stages"] == 2
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 0
        assert "stages" in result
        assert len(result["stages"]) == 2

    def test_overall_status_pass_when_all_pass(self):
        sr_pass = StageResult(
            stage=1, label="T", status="pass",
            summary={"total": 1, "passed": 1, "errors": 0},
            changes=[], errors=[],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        report = OnboardReport(
            employee_id="test",
            stages=[sr_pass, sr_pass],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        assert report.overall_status == "pass"

    def test_overall_status_fail_when_any_fails(self):
        sr_pass = StageResult(
            stage=1, label="T", status="pass",
            summary={"total": 1, "passed": 1, "errors": 0},
            changes=[], errors=[],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        sr_fail = StageResult(
            stage=2, label="T", status="fail",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[], errors=[{"item": "x", "reason": "test"}],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        report = OnboardReport(
            employee_id="test",
            stages=[sr_pass, sr_fail],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        assert report.overall_status == "fail"

    def test_overall_status_partial_when_partial_present(self):
        sr_pass = StageResult(
            stage=1, label="T", status="pass",
            summary={"total": 1, "passed": 1, "errors": 0},
            changes=[], errors=[],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        sr_partial = StageResult(
            stage=2, label="T", status="partial",
            summary={"total": 1, "passed": 0, "errors": 1},
            changes=[], errors=[{"item": "x", "reason": "test"}],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        report = OnboardReport(
            employee_id="test",
            stages=[sr_pass, sr_partial],
            check_time=datetime.now(timezone.utc).isoformat(),
        )
        assert report.overall_status == "partial"


# ── Stage parser tests ────────────────────────────────────────────────────

class TestStageParser:
    def test_parse_single_stage(self):
        assert _parse_stages("3") == (3,)

    def test_parse_multiple_stages(self):
        assert _parse_stages("1,3,5") == (1, 3, 5)

    def test_parse_range(self):
        assert _parse_stages("1-5") == (1, 2, 3, 4, 5)

    def test_parse_mixed(self):
        result = _parse_stages("1-3,7,9-11")
        assert result == (1, 2, 3, 7, 9, 10, 11)

    def test_parse_clamps_out_of_range(self):
        result = _parse_stages("0,5,12")
        assert result == (5,)

    def test_parse_sorts_and_deduplicates(self):
        result = _parse_stages("5,3,5,1-3")
        assert result == (1, 2, 3, 5)

    def test_parse_empty_yields_empty(self):
        assert _parse_stages("") == ()

    def test_parse_invalid_yields_empty(self):
        assert _parse_stages("abc,xyz") == ()


# ── Stage function tests (with fixture) ───────────────────────────────────

class TestStage1FivePieceKit:
    def test_missing_employee_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        result = stage_1_check(source_root, "nonexistent-employee")
        assert result.status == "fail"
        assert result.stage == 1
        assert result.label == STAGE_LABELS[1]

    def test_stage_result_has_ade_fields(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        result = stage_1_check(source_root, "nonexistent-employee")
        ade = result.to_ade_json()
        assert "status" in ade
        assert "summary" in ade
        assert "changes" in ade
        assert "errors" in ade
        assert "check_time" in ade
        assert ade["stage"] == 1


class TestStage2ContractYaml:
    def test_missing_contract_yaml_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        result = stage_2_check(source_root, "nonexistent-employee")
        assert result.status == "fail"
        assert result.stage == 2

    def test_valid_contract_yaml_passes(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        registry_dir = source_root / "docs" / "registry"
        registry_dir.mkdir(parents=True)
        contract_path = registry_dir / "test-employee.contract.yaml"
        contract_path.write_text(
            "contract:\n"
            "  agent_id: test-employee\n"
            "  family: Role\n"
            "paths:\n"
            "  soul: source-agents/test-employee/test-employee.soul.md\n"
            "  agent_body: source-agents/test-employee/test-employee.agent.md\n"
            "decision_rights:\n"
            "  approve:\n"
            "    - code_review\n"
            "  freeze:\n"
            "    - breaking_changes\n"
            "  escalate:\n"
            "    - architecture\n"
        )
        result = stage_2_check(source_root, "test-employee")
        assert result.status == "pass"

    def test_contract_missing_decision_rights_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        registry_dir = source_root / "docs" / "registry"
        registry_dir.mkdir(parents=True)
        contract_path = registry_dir / "test-employee.contract.yaml"
        contract_path.write_text(
            "contract:\n"
            "  agent_id: test-employee\n"
            "paths:\n"
            "  soul: source-agents/test-employee/test-employee.soul.md\n"
        )
        result = stage_2_check(source_root, "test-employee")
        assert result.status == "fail"


class TestStage3BindingProfile:
    def test_missing_binding_profile_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        result = stage_3_check(source_root, "nonexistent-employee")
        assert result.status == "fail"
        assert result.stage == 3

    def test_valid_binding_profile_passes(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        bp_dir = source_root / ".github" / "binding-profiles"
        bp_dir.mkdir(parents=True)
        bp_path = bp_dir / "test-employee.json"
        bp_path.write_text(json.dumps({
            "employee_id": "test-employee",
            "role_title": "Test Role",
            "binding_timestamp": "2026-08-01T00:00:00Z",
            "source_kit_path": "source-agents/test-employee/",
        }))
        result = stage_3_check(source_root, "test-employee")
        assert result.status == "pass"

    def test_incomplete_binding_profile_yields_partial(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        bp_dir = source_root / ".github" / "binding-profiles"
        bp_dir.mkdir(parents=True)
        bp_path = bp_dir / "test-employee.json"
        bp_path.write_text(json.dumps({
            "employee_id": "test-employee",
        }))
        result = stage_3_check(source_root, "test-employee")
        assert result.status == "partial"


class TestStage7Manifest:
    def test_missing_manifest_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        result = stage_7_check(source_root, "nonexistent-employee")
        assert result.status == "fail"

    def test_employee_not_in_manifest_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        manifest_dir = source_root / "source-agents" / "registries"
        manifest_dir.mkdir(parents=True)
        manifest_path = manifest_dir / "trimetaverse-live-agent-publish-manifest.json"
        manifest_path.write_text(json.dumps({
            "liveEntries": [
                {
                    "source": "TriCompany/source-agents/other-employee/other-employee.agent.md",
                    "target": "TriMetaverse/.github/agents/other-employee.agent.md",
                    "kind": "role-agent",
                    "status": "source-published-live-entry",
                },
            ],
        }))
        result = stage_7_check(source_root, "test-employee")
        assert result.status == "fail"

    def test_employee_in_manifest_passes(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        manifest_dir = source_root / "source-agents" / "registries"
        manifest_dir.mkdir(parents=True)
        manifest_path = manifest_dir / "trimetaverse-live-agent-publish-manifest.json"
        manifest_path.write_text(json.dumps({
            "liveEntries": [
                {
                    "source": "TriCompany/source-agents/test-employee/test-employee.agent.md",
                    "target": "TriMetaverse/.github/agents/test-employee.agent.md",
                    "kind": "role-agent",
                    "status": "source-published-live-entry",
                },
            ],
        }))
        result = stage_7_check(source_root, "test-employee")
        assert result.status == "pass"


class TestStage9Roster:
    def test_missing_roster_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        result = stage_9_check(source_root, "nonexistent-employee")
        assert result.status == "fail"

    def test_employee_not_in_roster_yields_fail(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        roster_dir = source_root / "docs" / "registry"
        roster_dir.mkdir(parents=True)
        roster_path = roster_dir / "employee-roster.json"
        roster_path.write_text(json.dumps({
            "version": "1.0.0",
            "employees": [
                {"id": "other-employee", "displayName": "X", "role": "X", "status": "live"},
            ],
        }))
        result = stage_9_check(source_root, "test-employee")
        assert result.status == "fail"

    def test_employee_in_roster_passes(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        roster_dir = source_root / "docs" / "registry"
        roster_dir.mkdir(parents=True)
        roster_path = roster_dir / "employee-roster.json"
        roster_path.write_text(json.dumps({
            "version": "1.0.0",
            "employees": [
                {"id": "test-employee", "displayName": "Test", "role": "Tester", "status": "live"},
            ],
        }))
        result = stage_9_check(source_root, "test-employee")
        assert result.status == "pass"


# ── Stage 11 cross-validation tests ──────────────────────────────────────

class TestStage11CrossValidation:
    def test_all_pass_yields_pass(self):
        stages = [
            StageResult(
                stage=i, label=STAGE_LABELS[i], status="pass",
                summary={"total": 1, "passed": 1, "errors": 0},
                changes=[], errors=[],
                check_time=datetime.now(timezone.utc).isoformat(),
            )
            for i in range(1, 11)
        ]
        result = stage_11_check(stages)
        assert result.status == "pass"
        assert result.summary["passed"] == 10

    def test_any_fail_yields_fail(self):
        stages = [
            StageResult(
                stage=i, label=STAGE_LABELS[i], status="pass" if i != 5 else "fail",
                summary={"total": 1, "passed": 0 if i == 5 else 1, "errors": 1 if i == 5 else 0},
                changes=[], errors=[{"item": "x", "reason": "test"}] if i == 5 else [],
                check_time=datetime.now(timezone.utc).isoformat(),
            )
            for i in range(1, 11)
        ]
        result = stage_11_check(stages)
        assert result.status == "fail"

    def test_partial_yields_partial(self):
        stages = [
            StageResult(
                stage=i, label=STAGE_LABELS[i], status="pass" if i != 3 else "partial",
                summary={"total": 1, "passed": 0 if i == 3 else 1, "errors": 1 if i == 3 else 0},
                changes=[], errors=[{"item": "x", "reason": "test"}] if i == 3 else [],
                check_time=datetime.now(timezone.utc).isoformat(),
            )
            for i in range(1, 11)
        ]
        result = stage_11_check(stages)
        assert result.status == "partial"


# ── Pipeline integration tests ────────────────────────────────────────────

class TestPipelineIntegration:
    def test_run_onboard_pipeline_returns_report(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        # Create absolute minimal fixture for stage 9
        roster_dir = source_root / "docs" / "registry"
        roster_dir.mkdir(parents=True)
        roster_path = roster_dir / "employee-roster.json"
        roster_path.write_text(json.dumps({
            "version": "1.0.0",
            "employees": [
                {"id": "test-employee", "displayName": "T", "role": "T", "status": "live"},
            ],
        }))

        report = run_onboard_pipeline(
            source_root=source_root,
            employee_id="test-employee",
            stages=(9,),
            sync=False,
        )
        assert isinstance(report, OnboardReport)
        assert report.employee_id == "test-employee"
        assert len(report.stages) == 1

    def test_run_all_stages_on_empty_root(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        report = run_onboard_pipeline(
            source_root=source_root,
            employee_id="nonexistent-employee",
            stages=None,  # All stages
            sync=False,
        )
        assert isinstance(report, OnboardReport)
        assert report.overall_status == "fail"
        assert len(report.stages) == 11  # All 11 including cross-validation

    def test_pipeline_respects_stage_filtering(self, tmp_path: Path):
        source_root = tmp_path / "TriCompany"
        source_root.mkdir()
        report = run_onboard_pipeline(
            source_root=source_root,
            employee_id="nonexistent-employee",
            stages=(1, 3, 5),
            sync=False,
        )
        # Should only run stages 1, 3, 5
        stage_numbers = [s.stage for s in report.stages]
        assert 1 in stage_numbers
        assert 3 in stage_numbers
        assert 5 in stage_numbers
        assert 2 not in stage_numbers
        assert 11 not in stage_numbers  # Not included unless explicitly requested
