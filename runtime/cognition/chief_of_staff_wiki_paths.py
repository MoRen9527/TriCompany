from __future__ import annotations

from pathlib import Path


CEO_CHIEF_OF_STAFF_EMPLOYEE_ID = "ceo-chief-of-staff"
_SUPPORT_ROOT_NAME = "TriCompany-copilot-host-assets"


def workspace_root(workspace_root: str | Path | None = None) -> Path:
    if workspace_root is not None:
        return Path(workspace_root).resolve()
    return Path(__file__).resolve().parents[2]


def support_root(workspace_root_path: str | Path | None = None) -> Path:
    root = workspace_root(workspace_root_path)
    candidates = (
        root / _SUPPORT_ROOT_NAME,
        root / "TriMetaverse" / _SUPPORT_ROOT_NAME,
        root.parent / "TriMetaverse" / _SUPPORT_ROOT_NAME,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    if (root / ".github").exists() or (root / "runtime").exists():
        return candidates[-1]
    return root


def chief_of_staff_knowledge_root(workspace_root_path: str | Path | None = None) -> Path:
    return support_root(workspace_root_path) / "knowledge" / "employees" / CEO_CHIEF_OF_STAFF_EMPLOYEE_ID


def chief_of_staff_inbox_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_knowledge_root(workspace_root_path) / "inbox"


def chief_of_staff_wiki_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_knowledge_root(workspace_root_path) / "wiki"


def chief_of_staff_wiki_page_specs_path(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_wiki_root(workspace_root_path) / "page-specs.json"


def chief_of_staff_workbench_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_knowledge_root(workspace_root_path) / "workbench"


def chief_of_staff_ipd_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_workbench_root(workspace_root_path) / "ipd"


def chief_of_staff_ipd_cases_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_ipd_root(workspace_root_path) / "cases"


def chief_of_staff_ipd_case_root(
    case_id: str,
    workspace_root_path: str | Path | None = None,
) -> Path:
    return chief_of_staff_ipd_cases_root(workspace_root_path) / case_id


def chief_of_staff_approval_report_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_workbench_root(workspace_root_path) / "approval-report"


def chief_of_staff_audit_root(workspace_root_path: str | Path | None = None) -> Path:
    return chief_of_staff_knowledge_root(workspace_root_path) / "audit"


def chief_of_staff_schedule_root(workspace_root_path: str | Path | None = None) -> Path:
    return (
        support_root(workspace_root_path)
        / "docs"
        / "execution"
        / "hermes-copilot-host"
        / "phase-1"
        / "schedules"
    )