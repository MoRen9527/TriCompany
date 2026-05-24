from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


WorkspaceKind = Literal["role", "employee", "org", "audit"]

_CAPITAL_BOUNDARY_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
_DASH_PATTERN = re.compile(r"-+")
_VALID_WORKSPACE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def repository_root(workspace_root: str | Path | None = None) -> Path:
    if workspace_root is not None:
        return Path(workspace_root)
    return Path(__file__).resolve().parents[2]


def normalize_workspace_id(raw_identifier: str) -> str:
    prepared = _CAPITAL_BOUNDARY_PATTERN.sub("-", raw_identifier.strip())
    prepared = prepared.replace("_", "-").replace(" ", "-").lower()
    prepared = _DASH_PATTERN.sub("-", prepared).strip("-")
    if not _VALID_WORKSPACE_ID_PATTERN.fullmatch(prepared):
        raise ValueError(f"Invalid workspace identifier: {raw_identifier!r}")
    return prepared


def knowledge_root(workspace_root: str | Path | None = None) -> Path:
    return repository_root(workspace_root) / "knowledge"


@dataclass(frozen=True)
class KnowledgeWorkspace:
    kind: WorkspaceKind
    identifier: str
    root: Path

    @property
    def inbox_root(self) -> Path:
        return self.root / "inbox"

    @property
    def wiki_root(self) -> Path:
        return self.root / "wiki"

    @property
    def audit_root(self) -> Path:
        return self.root / "audit"

    @property
    def workbench_root(self) -> Path:
        return self.root / "workbench"

    def ensure_directories(self) -> None:
        for directory in (self.inbox_root, self.wiki_root, self.audit_root, self.workbench_root):
            directory.mkdir(parents=True, exist_ok=True)


def role_workspace(role_id: str, workspace_root: str | Path | None = None) -> KnowledgeWorkspace:
    normalized_role_id = normalize_workspace_id(role_id)
    return KnowledgeWorkspace(
        kind="role",
        identifier=normalized_role_id,
        root=knowledge_root(workspace_root) / "roles" / normalized_role_id,
    )


def employee_workspace(employee_id: str, workspace_root: str | Path | None = None) -> KnowledgeWorkspace:
    normalized_employee_id = normalize_workspace_id(employee_id)
    return KnowledgeWorkspace(
        kind="employee",
        identifier=normalized_employee_id,
        root=knowledge_root(workspace_root) / "employees" / normalized_employee_id,
    )


def org_shared_workspace(workspace_root: str | Path | None = None) -> KnowledgeWorkspace:
    return KnowledgeWorkspace(
        kind="org",
        identifier="shared",
        root=knowledge_root(workspace_root) / "org" / "shared",
    )


def audit_workspace(workspace_root: str | Path | None = None) -> KnowledgeWorkspace:
    return KnowledgeWorkspace(
        kind="audit",
        identifier="audit",
        root=knowledge_root(workspace_root) / "audit",
    )


def employee_recall_workspace_order(
    *,
    employee_id: str,
    role_id: str,
    workspace_root: str | Path | None = None,
) -> tuple[KnowledgeWorkspace, KnowledgeWorkspace, KnowledgeWorkspace, KnowledgeWorkspace]:
    return (
        employee_workspace(employee_id, workspace_root),
        role_workspace(role_id, workspace_root),
        org_shared_workspace(workspace_root),
        audit_workspace(workspace_root),
    )
