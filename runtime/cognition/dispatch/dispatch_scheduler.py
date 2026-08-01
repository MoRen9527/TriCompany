"""dispatch_scheduler — CTO quality gate scheduler (Phase D).

B1 (W30): shell + four-gate no-op quality check table.
B2 (next week): wire real data sources (pytest, tsc, codegraph, source_publish_check).

This module provides a structured quality gate that the CTO runs as part of the
weekly operating review cycle (per operating-review-cycle.md).

Usage:
    python -m runtime.cognition.dispatch.dispatch_scheduler          # no-op gate
    python -m runtime.cognition.dispatch.dispatch_scheduler --help   # usage
    python -m runtime.cognition.dispatch.dispatch_scheduler --ci     # CI mode (B2)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


# ---------------------------------------------------------------------------
# data types
# ---------------------------------------------------------------------------


class GateStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class GateResult:
    """Result of a single quality gate check."""

    gate: str
    status: GateStatus
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class QualityGateReport:
    """Aggregated quality gate report for the CTO operating review."""

    check_time: str
    gates: list[GateResult] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    @property
    def overall(self) -> GateStatus:
        """Overall gate status: FAIL if any gate failed, WARN if any warned, else PASS."""
        statuses = [g.status for g in self.gates]
        if GateStatus.FAIL in statuses:
            return GateStatus.FAIL
        if GateStatus.WARN in statuses:
            return GateStatus.WARN
        return GateStatus.PASS


# ---------------------------------------------------------------------------
# B1: individual gate checks (no-op / placeholder)
# ---------------------------------------------------------------------------


def _check_tests() -> GateResult:
    """Gate 1: test suite pass rate across all active modules.

    B1 (no-op): returns PASS with placeholder data.
    B2: wires pytest (TriCompany) + npm test (TriMC, TriModel).
    """
    return GateResult(
        gate="tests",
        status=GateStatus.PASS,
        data={
            "phase": "B1-noop",
            "tri_company_pytest": {"status": "not_checked", "total": 0, "passed": 0},
            "trimc_npm_test": {"status": "not_checked", "total": 0, "passed": 0},
            "trimodel_npm_test": {"status": "not_checked", "total": 0, "passed": 0},
        },
        message="B1 no-op: test gate not yet wired. B2 will run pytest + npm test.",
    )


def _check_pipelines() -> GateResult:
    """Gate 2: publish pipeline + TypeScript type-check integrity.

    B1 (no-op): returns PASS with placeholder data.
    B2: wires CTO-002 publish + tsc --noEmit.
    """
    return GateResult(
        gate="pipelines",
        status=GateStatus.PASS,
        data={
            "phase": "B1-noop",
            "cto002_publish": {"status": "not_checked", "host_objects": 0},
            "trimc_tsc": {"status": "not_checked", "errors": 0},
        },
        message="B1 no-op: pipeline gate not yet wired. B2 will run publish + tsc --noEmit.",
    )


def _check_codegraph() -> GateResult:
    """Gate 3: CodeGraph index freshness vs git HEAD.

    B1 (no-op): returns PASS with placeholder data.
    B2: wires codegraph_status + .codegraph/codegraph.db timestamp.
    """
    return GateResult(
        gate="codegraph",
        status=GateStatus.PASS,
        data={
            "phase": "B1-noop",
            "index_exists": False,
            "commits_behind": 0,
            "stale": False,
        },
        message="B1 no-op: codegraph gate not yet wired. B2 will check codegraph_status.",
    )


def _check_registry_drift() -> GateResult:
    """Gate 4: source → support registry synchronisation status.

    B1 (no-op): returns PASS with placeholder data.
    B2: wires source_publish_check --check --format json.
    """
    return GateResult(
        gate="registry_drift",
        status=GateStatus.PASS,
        data={
            "phase": "B1-noop",
            "out_of_sync": 0,
            "in_sync": 0,
            "gaps": 0,
        },
        message="B1 no-op: registry drift gate not yet wired. B2 will run source_publish_check.",
    )


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


def run_quality_gate() -> QualityGateReport:
    """Run all four quality gates and return an aggregated report.

    B1: all gates return no-op PASS results.
    B2: each gate wired to real data sources.

    Returns a QualityGateReport suitable for JSON serialisation and consumption
    by the CTO operating review cycle.
    """
    gates: list[GateResult] = [
        _check_tests(),
        _check_pipelines(),
        _check_codegraph(),
        _check_registry_drift(),
    ]

    summary = {
        "total": len(gates),
        "pass": sum(1 for g in gates if g.status == GateStatus.PASS),
        "fail": sum(1 for g in gates if g.status == GateStatus.FAIL),
        "warn": sum(1 for g in gates if g.status == GateStatus.WARN),
    }

    return QualityGateReport(
        check_time=datetime.now(timezone.utc).isoformat(),
        gates=gates,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# serialisation
# ---------------------------------------------------------------------------


def _report_to_dict(report: QualityGateReport) -> dict[str, Any]:
    """Convert a QualityGateReport to a JSON-serialisable dict."""
    return {
        "check_time": report.check_time,
        "overall": report.overall.value,
        "gates": [
            {
                "gate": g.gate,
                "status": g.status.value,
                "message": g.message,
                "data": g.data,
            }
            for g in report.gates
        ],
        "summary": report.summary,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dispatch_scheduler",
        description=(
            "Phase D: CTO quality gate scheduler. "
            "Runs four engineering quality gates (tests, pipelines, codegraph, "
            "registry drift) and produces a structured report for the CTO "
            "operating review cycle."
        ),
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        default=False,
        help="CI mode: exit non-zero on FAIL (B2, placeholder for now).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write JSON report to file (B2).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    report = run_quality_gate()
    output = _report_to_dict(report)

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    if args.ci and report.overall == GateStatus.FAIL:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
