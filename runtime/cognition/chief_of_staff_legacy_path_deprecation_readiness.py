from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


VALIDATION_ID = "chief-of-staff-legacy-path-deprecation-readiness-v0.1"
GENERATED_AT = "2026-04-29T00:00:00+08:00"
LEGACY_PATH = "knowledge/chief-of-staff"
TARGET_EMPLOYEE_PATH = "knowledge/employees/ceo-chief-of-staff"
LEGACY_PATH_PATTERNS = (
    "knowledge/chief-of-staff",
    "TriCompany-copilot-host-assets/knowledge/chief-of-staff",
    '"knowledge" / "chief-of-staff"',
)
TEXT_SUFFIXES = (".json", ".md", ".py", ".prompt", ".agent", ".instructions")
SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "node_modules"}
EXCLUDED_FILE_NAMES = {
    "chief_of_staff_legacy_path_deprecation_readiness.py",
    "chief_of_staff_legacy_path_deprecation_validation.py",
    "chief-of-staff-legacy-path-deprecation-readiness.md",
}
NON_BLOCKING_RUNTIME_COMPATIBILITY_FILE_REASONS = {
    "host_object_generation.py": "source generator intentionally keeps the legacy support object set until manifest deprecation is applied",
    "rd_trainer_host_object_generation_validation.py": "host object generation validation intentionally asserts legacy compatibility preservation",
    "chief_of_staff_legacy_path_shadow_gate.py": "shadow gate intentionally references the legacy path to prove it is retained only as deprecated compatibility",
    "chief_of_staff_legacy_path_shadow_gate_validation.py": "shadow gate validation intentionally seeds legacy path fixtures and stale-reference blockers",
    "README.md": "runtime README documents compatibility status and is not an active runtime consumer",
}


@dataclass(frozen=True)
class LegacyPathScanRoot:
    root: Path
    category: str
    blocking: bool
    reason: str


def default_workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_default_scan_roots(workspace_root: Path | None = None) -> tuple[LegacyPathScanRoot, ...]:
    workspace = workspace_root or default_workspace_root()
    tri_company_root = workspace / "TriCompany"
    tri_metaverse_root = workspace / "TriMetaverse"
    support_root = tri_metaverse_root / "TriCompany-copilot-host-assets"

    roots: list[LegacyPathScanRoot] = [
        LegacyPathScanRoot(
            root=tri_company_root / "runtime" / "cognition",
            category="runtime-source",
            blocking=True,
            reason="source runtime still references the legacy chief-of-staff knowledge path",
        ),
        LegacyPathScanRoot(
            root=support_root / "runtime" / "cognition",
            category="runtime-support-published-copy",
            blocking=True,
            reason="support runtime copy still references the legacy chief-of-staff knowledge path",
        ),
        LegacyPathScanRoot(
            root=tri_metaverse_root / "docs" / "workflow" / "tricompany-copilot-host-assets-anchor-index.json",
            category="governance-anchor-index",
            blocking=True,
            reason="central governance anchors still point at legacy chief-of-staff workbench or audit objects",
        ),
    ]

    for live_subdir in ("agents", "prompts", "instructions", "hooks"):
        roots.append(
            LegacyPathScanRoot(
                root=tri_metaverse_root / ".github" / live_subdir,
                category=f"live-entry-{live_subdir}",
                blocking=True,
                reason="live host assets must not hard-code the legacy chief-of-staff knowledge path before deprecation",
            )
        )

    roots.extend(
        [
            LegacyPathScanRoot(
                root=support_root / "host-object-manifest.json",
                category="support-host-object-manifest",
                blocking=False,
                reason="manifest references are expected until the legacy object set is formally deprecated",
            ),
            LegacyPathScanRoot(
                root=tri_company_root / ".github" / "manifests" / "tricompany-host-object-generation-manifest.json",
                category="source-host-object-generation-manifest",
                blocking=False,
                reason="source manifest references are expected until the legacy object set is formally deprecated",
            ),
            LegacyPathScanRoot(
                root=tri_metaverse_root / "docs" / "workflow" / "tricompany-copilot-host-assets-governance.md",
                category="governance-doc",
                blocking=False,
                reason="governance prose documents the current compatibility boundary and must be updated after runtime migration",
            ),
            LegacyPathScanRoot(
                root=tri_metaverse_root / "docs" / "workflow" / "tricompany-copilot-host-assets-migration-matrix.md",
                category="migration-matrix",
                blocking=False,
                reason="migration matrix tracks the transition state and is not itself an active runtime dependency",
            ),
        ]
    )
    return tuple(root for root in roots if root.root.exists())


def build_readiness_report(
    *,
    scan_roots: Sequence[LegacyPathScanRoot] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    workspace = workspace_root or default_workspace_root()
    roots = tuple(scan_roots or build_default_scan_roots(workspace))
    findings = list(_collect_findings(roots=roots, workspace_root=workspace))
    blocking_findings = [finding for finding in findings if finding["blocking"]]
    non_blocking_findings = [finding for finding in findings if not finding["blocking"]]
    status = "blocked-by-active-legacy-path-dependencies" if blocking_findings else "ready-for-deprecation-label"

    return {
        "validationId": VALIDATION_ID,
        "generatedAt": GENERATED_AT,
        "status": status,
        "legacyPath": LEGACY_PATH,
        "targetEmployeePath": TARGET_EMPLOYEE_PATH,
        "blockingDependencyCount": len(blocking_findings),
        "nonBlockingReferenceCount": len(non_blocking_findings),
        "blockingDependencies": blocking_findings,
        "nonBlockingReferences": non_blocking_findings,
        "nextActions": _next_actions(blocking=bool(blocking_findings)),
    }


def _collect_findings(*, roots: Sequence[LegacyPathScanRoot], workspace_root: Path) -> Iterable[dict[str, object]]:
    for scan_root in roots:
        for path in _iter_text_files(scan_root.root):
            if path.name in EXCLUDED_FILE_NAMES:
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if not any(pattern in line for pattern in LEGACY_PATH_PATTERNS):
                    continue
                blocking = scan_root.blocking
                category = scan_root.category
                reason = scan_root.reason
                if scan_root.category.startswith("runtime-") and path.name in NON_BLOCKING_RUNTIME_COMPATIBILITY_FILE_REASONS:
                    blocking = False
                    category = "runtime-compatibility-record"
                    reason = NON_BLOCKING_RUNTIME_COMPATIBILITY_FILE_REASONS[path.name]
                yield {
                    "category": category,
                    "blocking": blocking,
                    "path": _relative_path(path, workspace_root),
                    "line": line_number,
                    "excerpt": line.strip(),
                    "reason": reason,
                }


def _iter_text_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if _is_text_path(root):
            yield root
        return
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and _is_text_path(path):
            yield path


def _is_text_path(path: Path) -> bool:
    return any(str(path).endswith(suffix) for suffix in TEXT_SUFFIXES)


def _relative_path(path: Path, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


def _next_actions(*, blocking: bool) -> list[str]:
    if blocking:
        return [
            f"Move runtime default delivery targets from {LEGACY_PATH}/audit to {TARGET_EMPLOYEE_PATH}/audit or an explicit configurable target.",
            f"Move workbench read/fallback paths from {LEGACY_PATH}/wiki and {LEGACY_PATH}/audit to the employee workspace after equivalent objects exist.",
            "Update central governance anchors after runtime and workbench consumers have switched.",
            "Rerun this readiness validation before changing manifest compatibilityStatus to deprecated.",
        ]
    return [
        "Confirm source and support manifests keep the legacy compatibilityStatus at deprecated-legacy-path.",
        "Mark the legacy support object set read-only and schedule archive/delete review.",
        "Keep the legacy directory until at least one post-deprecation validation cycle passes.",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate readiness to deprecate knowledge/chief-of-staff.")
    parser.add_argument("--workspace-root", type=Path, default=default_workspace_root())
    parser.add_argument("--require-ready", action="store_true", help="Return non-zero when active dependencies remain.")
    args = parser.parse_args(argv)

    report = build_readiness_report(workspace_root=args.workspace_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.require_ready and report["status"] != "ready-for-deprecation-label":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())