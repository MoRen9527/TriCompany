from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence


VALIDATION_ID = "chief-of-staff-legacy-path-shadow-gate-v0.1"
GENERATED_AT = "2026-04-29T00:00:00+08:00"
LEGACY_PATH = "knowledge/chief-of-staff"
TARGET_EMPLOYEE_PATH = "knowledge/employees/ceo-chief-of-staff"
LEGACY_MANIFEST_PATH = "TriCompany-copilot-host-assets/knowledge/chief-of-staff"
EXPECTED_COMPATIBILITY_STATUS = "deprecated-legacy-path"
REQUIRED_AREAS = ("wiki", "workbench", "audit")
REQUIRED_WORKBENCH_FILES = (
    "index.html",
    "snapshot.json",
    "approval-report/snapshot.json",
    "approval-report/summary.md",
)
WORKBENCH_TEXT_SUFFIXES = (".html", ".json", ".md")
LEGACY_TEXT_PATTERNS = (
    "knowledge/chief-of-staff",
    "TriCompany-copilot-host-assets/knowledge/chief-of-staff",
)


def default_workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_support_root(workspace_root: Path | None = None) -> Path:
    workspace = workspace_root or default_workspace_root()
    return workspace / "TriMetaverse" / "TriCompany-copilot-host-assets"


def build_shadow_gate_report(
    *,
    workspace_root: Path | None = None,
    support_root: Path | None = None,
) -> dict[str, object]:
    workspace = workspace_root or default_workspace_root()
    support = support_root or default_support_root(workspace)
    legacy_root = support / LEGACY_PATH
    employee_root = support / TARGET_EMPLOYEE_PATH

    blockers: list[dict[str, object]] = []
    _check_required_directory(blockers, legacy_root, "legacy support object set must remain available during shadow validation")
    _check_required_directory(blockers, employee_root, "employee workspace must exist before formal takeover")
    _check_workspace_areas(blockers, legacy_root=legacy_root, employee_root=employee_root)
    _check_required_workbench_files(blockers, employee_root)
    _check_workbench_legacy_references(blockers, employee_root)
    _check_manifest_statuses(blockers, workspace=workspace, support=support)
    _check_anchor_index(blockers, workspace=workspace)

    status = "shadow-gate-ready-for-formal-takeover" if not blockers else "blocked-before-formal-takeover"
    return {
        "validationId": VALIDATION_ID,
        "generatedAt": GENERATED_AT,
        "status": status,
        "sourceTruthStage": "TriCompany/runtime/cognition plus TriCompany/.github/manifests",
        "shadowTestStage": "legacy path retained while employee workspace is populated and validated in parallel",
        "formalTakeoverStage": "active runtime and governance anchors point to employee workspace; legacy path is deprecated compatibility only",
        "legacyPath": LEGACY_PATH,
        "targetEmployeePath": TARGET_EMPLOYEE_PATH,
        "blockerCount": len(blockers),
        "blockers": blockers,
        "nextActions": _next_actions(blocked=bool(blockers)),
    }


def _check_required_directory(blockers: list[dict[str, object]], path: Path, reason: str) -> None:
    if path.is_dir():
        return
    blockers.append(
        {
            "category": "missing-directory",
            "path": path.as_posix(),
            "reason": reason,
        }
    )


def _check_workspace_areas(blockers: list[dict[str, object]], *, legacy_root: Path, employee_root: Path) -> None:
    for area in REQUIRED_AREAS:
        legacy_area = legacy_root / area
        employee_area = employee_root / area
        _check_required_directory(blockers, legacy_area, f"legacy {area} area must remain available during shadow validation")
        _check_required_directory(blockers, employee_area, f"employee {area} area must exist before formal takeover")
        if not legacy_area.is_dir() or not employee_area.is_dir():
            continue
        legacy_files = _relative_file_set(legacy_area)
        employee_files = _relative_file_set(employee_area)
        missing = sorted(legacy_files - employee_files)
        if area in {"wiki", "workbench"} and missing:
            blockers.append(
                {
                    "category": "shadow-parity-missing-files",
                    "area": area,
                    "path": employee_area.as_posix(),
                    "missingFiles": missing,
                    "reason": "employee workspace must contain legacy wiki/workbench objects before formal takeover",
                }
            )
        if area == "audit" and len(employee_files) < len(legacy_files):
            blockers.append(
                {
                    "category": "shadow-parity-audit-count",
                    "area": area,
                    "path": employee_area.as_posix(),
                    "legacyFileCount": len(legacy_files),
                    "employeeFileCount": len(employee_files),
                    "reason": "employee audit area must preserve at least the legacy audit history before formal takeover",
                }
            )


def _check_required_workbench_files(blockers: list[dict[str, object]], employee_root: Path) -> None:
    workbench_root = employee_root / "workbench"
    for relative_path in REQUIRED_WORKBENCH_FILES:
        path = workbench_root / relative_path
        if path.is_file():
            continue
        blockers.append(
            {
                "category": "missing-current-workbench-artifact",
                "path": path.as_posix(),
                "reason": "employee workbench must expose the current governed artifacts before formal takeover",
            }
        )


def _check_workbench_legacy_references(blockers: list[dict[str, object]], employee_root: Path) -> None:
    workbench_root = employee_root / "workbench"
    if not workbench_root.is_dir():
        return
    for path in _iter_workbench_text_files(workbench_root):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not any(pattern in line for pattern in LEGACY_TEXT_PATTERNS):
                continue
            blockers.append(
                {
                    "category": "employee-workbench-legacy-reference",
                    "path": path.as_posix(),
                    "line": line_number,
                    "excerpt": line.strip(),
                    "reason": "current employee workbench artifacts must not point active views back to the legacy path",
                }
            )


def _check_manifest_statuses(blockers: list[dict[str, object]], *, workspace: Path, support: Path) -> None:
    manifests = (
        workspace / "TriCompany" / ".github" / "manifests" / "tricompany-host-object-generation-manifest.json",
        support / "host-object-manifest.json",
    )
    for manifest_path in manifests:
        if not manifest_path.is_file():
            blockers.append(
                {
                    "category": "missing-manifest",
                    "path": manifest_path.as_posix(),
                    "reason": "source and support manifests must both record the legacy compatibility status",
                }
            )
            continue
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        status = _legacy_compatibility_status(payload)
        if status != EXPECTED_COMPATIBILITY_STATUS:
            blockers.append(
                {
                    "category": "manifest-status-not-deprecated",
                    "path": manifest_path.as_posix(),
                    "actualStatus": status or "missing",
                    "expectedStatus": EXPECTED_COMPATIBILITY_STATUS,
                    "reason": "formal takeover requires both manifests to mark the legacy path as deprecated compatibility",
                }
            )


def _check_anchor_index(blockers: list[dict[str, object]], *, workspace: Path) -> None:
    anchor_index = workspace / "TriMetaverse" / "docs" / "workflow" / "tricompany-copilot-host-assets-anchor-index.json"
    if not anchor_index.is_file():
        blockers.append(
            {
                "category": "missing-anchor-index",
                "path": anchor_index.as_posix(),
                "reason": "central governance anchor index must exist before formal takeover",
            }
        )
        return
    text = anchor_index.read_text(encoding="utf-8")
    if any(pattern in text for pattern in LEGACY_TEXT_PATTERNS):
        blockers.append(
            {
                "category": "anchor-index-legacy-reference",
                "path": anchor_index.as_posix(),
                "reason": "central governance anchors must not point to the legacy path after shadow validation",
            }
        )
    if TARGET_EMPLOYEE_PATH not in text:
        blockers.append(
            {
                "category": "anchor-index-missing-employee-path",
                "path": anchor_index.as_posix(),
                "reason": "central governance anchors must point to the employee workspace before formal takeover",
            }
        )


def _legacy_compatibility_status(manifest: dict[str, object]) -> str | None:
    object_sets = manifest.get("objectSets")
    if not isinstance(object_sets, list):
        return None
    for object_set in object_sets:
        if not isinstance(object_set, dict):
            continue
        support_objects = object_set.get("supportObjects")
        if not isinstance(support_objects, list):
            continue
        for item in support_objects:
            if not isinstance(item, dict):
                continue
            if item.get("path") == LEGACY_MANIFEST_PATH:
                return str(item.get("compatibilityStatus") or "")
    return None


def _relative_file_set(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _iter_workbench_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and any(path.name.endswith(suffix) for suffix in WORKBENCH_TEXT_SUFFIXES):
            yield path


def _next_actions(*, blocked: bool) -> list[str]:
    if blocked:
        return [
            "Keep the legacy path preserved and do not advance deprecation labels further.",
            "Populate or regenerate the employee workspace until wiki/workbench/audit parity is available.",
            "Rerun this shadow gate before treating the employee workspace as the active support object path.",
        ]
    return [
        "Keep legacy support objects retained as deprecated compatibility for at least one post-deprecation validation cycle.",
        "Use the employee workspace as the active support object path for current workbench, audit, and governance anchors.",
        "Do not archive or delete the legacy path until a separate archive/delete review passes.",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate chief-of-staff legacy path shadow gate.")
    parser.add_argument("--workspace-root", type=Path, default=default_workspace_root())
    parser.add_argument("--support-root", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)

    report = build_shadow_gate_report(workspace_root=args.workspace_root, support_root=args.support_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.require_ready and report["status"] != "shadow-gate-ready-for-formal-takeover":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())