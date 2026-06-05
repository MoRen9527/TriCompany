from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.cognition.knowledge_workspace import (
    KnowledgeWorkspace,
    audit_workspace,
    employee_workspace,
    org_shared_workspace,
    role_workspace,
)


HOST_OBJECT_MANIFEST_NAME = "host-object-manifest.json"
SOURCE_HOST_BINDING_PROFILE_DIR = Path(".github") / "binding-profiles"
SOURCE_HOST_OBJECT_MANIFEST_REFERENCE = "TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json"
SUPPORT_ROOT_REFERENCE = "TriCompany-copilot-host-assets"
SUPPORT_HOST_OBJECT_MANIFEST_REFERENCE = f"{SUPPORT_ROOT_REFERENCE}/{HOST_OBJECT_MANIFEST_NAME}"
SOURCE_AGENT_KIT_REFERENCE_ROOT = "TriCompany/.github/source-agents"
HOST_OBJECT_GOVERNED_BY = (
    SOURCE_HOST_OBJECT_MANIFEST_REFERENCE,
    "TriMetaverse/docs/workflow/tricompany-copilot-host-assets-governance.md",
    "TriMetaverse/docs/workflow/tricompany-copilot-host-assets-migration-matrix.md",
    "TriCompany/docs/workflow/host-object-publish-flow.md",
)
RD_TRAINER_OBJECT_SET_ID = "rd-trainer-knowledge-workspace-v0.1"
CEO_CHIEF_OF_STAFF_OBJECT_SET_ID = "ceo-chief-of-staff-knowledge-workspace-v0.1"
CHIEF_PRODUCT_OFFICER_OBJECT_SET_ID = "chief-product-officer-knowledge-workspace-v0.1"
CHIEF_TECHNOLOGY_OFFICER_OBJECT_SET_ID = "chief-technology-officer-knowledge-workspace-v0.1"
CHIEF_MARKETING_OFFICER_OBJECT_SET_ID = "chief-marketing-officer-knowledge-workspace-v0.1"
CHIEF_OPERATING_OFFICER_OBJECT_SET_ID = "chief-operating-officer-knowledge-workspace-v0.1"
CHIEF_FINANCIAL_OFFICER_OBJECT_SET_ID = "chief-financial-officer-knowledge-workspace-v0.1"
CHIEF_HUMAN_RESOURCES_OFFICER_OBJECT_SET_ID = "chief-human-resources-officer-knowledge-workspace-v0.1"
CHIEF_ADMINISTRATIVE_OFFICER_OBJECT_SET_ID = "chief-administrative-officer-knowledge-workspace-v0.1"
RD_TRAINER_GENERATED_AT = "2026-04-29T00:00:00+08:00"
CONSUMPTION_DATA_BOUNDARY_NOTE = (
    "Source .github/source-agents/<employee-id>/*.memory.md, *.colleagues.md, and *.social.md files are layer contracts only, not employee consumption records; "
    "concrete employee consumption records belong in the employee wiki or runtime cognition state."
)


def source_agent_kit_refs(employee_id: str) -> tuple[str, ...]:
    return tuple(
        f"{SOURCE_AGENT_KIT_REFERENCE_ROOT}/{employee_id}/{employee_id}.{suffix}.md"
        for suffix in ("agent", "soul", "memory", "colleagues", "social")
    )


@dataclass(frozen=True)
class HostObjectSetDefinition:
    object_set_id: str
    role_id: str
    employee_id: str
    owner_role: str
    source_refs: tuple[str, ...]
    role_description: str
    employee_description: str
    generator: str
    live_entry_status: str
    host_stage: str
    notes: tuple[str, ...]
    employee_display_name: str | None = None
    live_entry_ref: str | None = None
    generated_at: str = RD_TRAINER_GENERATED_AT
    status: str = "generated-staging"
    legacy_support_objects: tuple[Mapping[str, str], ...] = ()
    replaces_object_set_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeneratedHostObjectSet:
    object_set_id: str
    support_root: Path
    role_workspace: KnowledgeWorkspace
    employee_workspace: KnowledgeWorkspace
    org_shared_workspace: KnowledgeWorkspace
    audit_workspace: KnowledgeWorkspace
    manifest_path: Path


def generate_rd_trainer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=RD_TRAINER_HOST_OBJECT_SET)


def generate_project_trainer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_rd_trainer_host_objects(support_root)


def generate_ceo_chief_of_staff_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET)


def generate_chief_product_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_PRODUCT_OFFICER_HOST_OBJECT_SET)


def generate_chief_technology_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_TECHNOLOGY_OFFICER_HOST_OBJECT_SET)


def generate_chief_marketing_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_MARKETING_OFFICER_HOST_OBJECT_SET)


def generate_chief_operating_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_OPERATING_OFFICER_HOST_OBJECT_SET)


def generate_chief_financial_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_FINANCIAL_OFFICER_HOST_OBJECT_SET)


def generate_chief_human_resources_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_HUMAN_RESOURCES_OFFICER_HOST_OBJECT_SET)


def generate_chief_administrative_officer_host_objects(support_root: str | Path) -> GeneratedHostObjectSet:
    return generate_host_object_set(support_root=support_root, definition=CHIEF_ADMINISTRATIVE_OFFICER_HOST_OBJECT_SET)


def generate_all_declared_employee_host_objects(support_root: str | Path) -> tuple[GeneratedHostObjectSet, ...]:
    return tuple(generate_host_object_set(support_root=support_root, definition=definition) for definition in DECLARED_HOST_OBJECT_SETS)


RD_TRAINER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=RD_TRAINER_OBJECT_SET_ID,
    role_id="rd-trainer",
    employee_id="rd-trainer",
    owner_role="RAndDTrainer",
    source_refs=(
        "TriCompany/docs/workflow/rd-trainer-role.md",
        *source_agent_kit_refs("rd-trainer"),
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
        "TriCompany/docs/training/README.md",
        "TriCompany/docs/training/ipd-usage-guide.md",
    ),
    role_description="Role-level reusable training knowledge for RAndDTrainer.",
    employee_description="Employee-instance working knowledge for the current RAndDTrainer.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee rd-trainer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "RAndDTrainer is enabled as a current Copilot-host live employee in the current phase.",
        "The live discovery entry is TriMetaverse/.github/agents/rd-trainer.agent.md; the source kit remains under TriCompany/.github/source-agents/rd-trainer.",
        "The legacy project-trainer id is retained only as a compatibility alias and is replaced in support manifests by rd-trainer.",
        "RAndDTrainer runtime cognition state is created only after a live/runtime write, not during support payload generation.",
    ),
    employee_display_name="小吴",
    live_entry_ref="TriMetaverse/.github/agents/rd-trainer.agent.md",
    replaces_object_set_ids=("project-trainer-knowledge-workspace-v0.1",),
)


CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CEO_CHIEF_OF_STAFF_OBJECT_SET_ID,
    role_id="ceo-chief-of-staff",
    employee_id="ceo-chief-of-staff",
    owner_role="CEOChiefOfStaff",
    source_refs=(
        *source_agent_kit_refs("ceo-chief-of-staff"),
        "TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md",
        "TriCompany/docs/workflow/chief-of-staff-llm-wiki-object-spec.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
    ),
    role_description="Role-level reusable coordination knowledge for the CEOChiefOfStaff role.",
    employee_description="Employee-instance working knowledge for the current ceo-chief-of-staff live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee ceo-chief-of-staff",
    live_entry_status="live-entry-existing-not-changed",
    host_stage="current-copilot-host-live",
    notes=(
        "The existing TriMetaverse/.github ceo-chief-of-staff live entry is the active live agent; no second live agent file is published for this migration.",
        "This object set binds that live entry to the role/employee workspace model without changing the live .github entry identity.",
        "The retired knowledge/chief-of-staff compatibility path is no longer published; the current support payload lives only under the ceo-chief-of-staff role/employee workspaces.",
        "The existing .tricompany-cognition/employee/ceo-chief-of-staff.md file remains runtime-state, not support payload source truth.",
    ),
    live_entry_ref="TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md",
)


CHIEF_PRODUCT_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_PRODUCT_OFFICER_OBJECT_SET_ID,
    role_id="ChiefProductOfficer",
    employee_id="chief-product-officer",
    owner_role="ChiefProductOfficer",
    source_refs=(
        *source_agent_kit_refs("chief-product-officer"),
        "TriCompany/docs/product/PROJECT.md",
        "TriCompany/docs/product/REQUIREMENTS.md",
        "TriCompany/docs/product/ROADMAP.md",
        "TriCompany/docs/product/STATE.md",
        "TriCompany/docs/registry/product-state.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
    ),
    role_description="Role-level reusable product judgment knowledge for the ChiefProductOfficer role.",
    employee_description="Employee-instance working knowledge for the current chief-product-officer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-product-officer",
    live_entry_status="live-entry-existing-not-changed",
    host_stage="current-copilot-host-live",
    notes=(
        "The existing TriMetaverse/.github chief-product-officer live entry is the active live agent for the current Copilot-host; no second live agent file is published.",
        "This object set binds that live entry to the role/employee workspace model without changing the live .github entry identity.",
        "This onboarding means current Copilot-host live enablement and TriCompany source-side handoff, not a TriMC formal host switch.",
    ),
    employee_display_name="小乔",
    live_entry_ref="TriMetaverse/.github/agents/chief-product-officer.agent.md",
)


CHIEF_TECHNOLOGY_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_TECHNOLOGY_OFFICER_OBJECT_SET_ID,
    role_id="ChiefTechnologyOfficer",
    employee_id="chief-technology-officer",
    owner_role="ChiefTechnologyOfficer",
    source_refs=(
        *source_agent_kit_refs("chief-technology-officer"),
        "TriCompany/docs/engineering/DESIGN.md",
        "TriCompany/docs/engineering/ROADMAP.md",
        "TriCompany/docs/engineering/STATE.md",
        "TriCompany/docs/engineering/metacognition-architecture.md",
        "TriCompany/docs/registry/code-state.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
    ),
    role_description="Role-level reusable engineering delivery knowledge for the ChiefTechnologyOfficer role.",
    employee_description="Employee-instance working knowledge for the current chief-technology-officer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-technology-officer",
    live_entry_status="live-entry-existing-not-changed",
    host_stage="current-copilot-host-live",
    notes=(
        "The existing TriMetaverse/.github chief-technology-officer live entry is the active live agent for the current Copilot-host; no second live agent file is published.",
        "This object set binds that live entry to the role/employee workspace model without changing the live .github entry identity.",
        "This onboarding means current Copilot-host live enablement and TriCompany source-side handoff, not a TriMC formal host switch.",
    ),
    employee_display_name="小狄",
    live_entry_ref="TriMetaverse/.github/agents/chief-technology-officer.agent.md",
)


CHIEF_MARKETING_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_MARKETING_OFFICER_OBJECT_SET_ID,
    role_id="ChiefMarketingOfficer",
    employee_id="chief-marketing-officer",
    owner_role="ChiefMarketingOfficer",
    source_refs=(
        "TriCompany/docs/workflow/chief-marketing-officer-role.md",
        *source_agent_kit_refs("chief-marketing-officer"),
        "TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md",
        "TriCompany/docs/workflow/host-object-publish-flow.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
        "TriMetaverse/cyber-company.md",
    ),
    role_description="Role-level reusable market intelligence, competitor research, trend tracking and product-input knowledge for the ChiefMarketingOfficer role.",
    employee_description="Employee-instance working knowledge for the current chief-marketing-officer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-marketing-officer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "ChiefMarketingOfficer is enabled as an independent live host agent in the current Copilot-host phase.",
        "The live discovery entry is TriMetaverse/.github/agents/chief-marketing-officer.agent.md.",
        "CMO owns market research, competitor intelligence, trend and hotspot capture, and structured product inputs for CPO; this does not imply TriMC formal host switch.",
        "Current enablement does not imply automated internet crawling, production market-data pipelines, or scheduled research jobs are already implemented.",
    ),
    live_entry_ref="TriMetaverse/.github/agents/chief-marketing-officer.agent.md",
)


CHIEF_OPERATING_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_OPERATING_OFFICER_OBJECT_SET_ID,
    role_id="ChiefOperatingOfficer",
    employee_id="chief-operating-officer",
    owner_role="ChiefOperatingOfficer",
    source_refs=(
        "TriCompany/docs/workflow/chief-operating-officer-role.md",
        *source_agent_kit_refs("chief-operating-officer"),
        "TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md",
        "TriCompany/docs/workflow/host-object-publish-flow.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
        "TriMetaverse/cyber-company.md",
    ),
    role_description="Role-level reusable operating cadence, rollout planning, cross-functional execution and recovery-loop knowledge for the ChiefOperatingOfficer role.",
    employee_description="Employee-instance working knowledge for the current chief-operating-officer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-operating-officer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "ChiefOperatingOfficer is enabled as an independent live host agent in the current Copilot-host phase.",
        "The live discovery entry is TriMetaverse/.github/agents/chief-operating-officer.agent.md.",
        "COO owns operating cadence, rollout planning, cross-functional execution windows and recovery loops for CMO/CPO/CFO/CTO/TriDev collaboration; this does not imply TriMC formal host switch.",
        "Current enablement does not imply production dashboards, automated scheduling, automated rollout, automated rollback or a complete authorization matrix are already implemented.",
    ),
    live_entry_ref="TriMetaverse/.github/agents/chief-operating-officer.agent.md",
)


CHIEF_FINANCIAL_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_FINANCIAL_OFFICER_OBJECT_SET_ID,
    role_id="ChiefFinancialOfficer",
    employee_id="chief-financial-officer",
    owner_role="ChiefFinancialOfficer",
    source_refs=(
        "TriCompany/docs/workflow/chief-financial-officer-role.md",
        *source_agent_kit_refs("chief-financial-officer"),
        "TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md",
        "TriCompany/docs/workflow/host-object-publish-flow.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
        "TriMetaverse/cyber-company.md",
    ),
    role_description="Role-level reusable budget guardrail, cost control, profitability check and financial-risk knowledge for the ChiefFinancialOfficer role.",
    employee_description="Employee-instance working knowledge for the current chief-financial-officer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-financial-officer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "ChiefFinancialOfficer is enabled as an independent live host agent in the current Copilot-host phase.",
        "The live discovery entry is TriMetaverse/.github/agents/chief-financial-officer.agent.md.",
        "CFO owns budget guardrails, cost controls, profitability checks, pricing assumptions and financial risk review for CMO/CPO/COO/CTO/TriDev collaboration; this does not imply TriMC formal host switch.",
        "Current enablement does not imply production ledgers, automated settlement, on-chain budgets, on-chain revenue sharing or a complete finance authorization matrix are already implemented.",
    ),
    live_entry_ref="TriMetaverse/.github/agents/chief-financial-officer.agent.md",
)


CHIEF_HUMAN_RESOURCES_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_HUMAN_RESOURCES_OFFICER_OBJECT_SET_ID,
    role_id="ChiefHumanResourcesOfficer",
    employee_id="chief-human-resources-officer",
    owner_role="ChiefHumanResourcesOfficer",
    source_refs=(
        "TriCompany/docs/workflow/chief-human-resources-officer-role.md",
        *source_agent_kit_refs("chief-human-resources-officer"),
        "TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md",
        "TriCompany/docs/workflow/host-object-publish-flow.md",
        "TriCompany/docs/workflow/cyber-company-secretariat.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
    ),
    role_description="Role-level reusable organization and handoff governance knowledge for the ChiefHumanResourcesOfficer role.",
    employee_description="Employee-instance working knowledge for the source-side chief-human-resources-officer employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-human-resources-officer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "ChiefHumanResourcesOfficer is enabled as an independent live host agent in the current Copilot-host phase.",
        "The live discovery entry is TriMetaverse/.github/agents/chief-human-resources-officer.agent.md.",
        "CHO owns staffing governance, role enablement and handoff completion tracking; this does not imply TriMC formal host switch.",
    ),
    live_entry_ref="TriMetaverse/.github/agents/chief-human-resources-officer.agent.md",
)


CHIEF_ADMINISTRATIVE_OFFICER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=CHIEF_ADMINISTRATIVE_OFFICER_OBJECT_SET_ID,
    role_id="ChiefAdministrativeOfficer",
    employee_id="chief-administrative-officer",
    owner_role="ChiefAdministrativeOfficer",
    source_refs=(
        "TriCompany/docs/workflow/chief-administrative-officer-role.md",
        *source_agent_kit_refs("chief-administrative-officer"),
        "TriCompany/docs/workflow/cyber-company-secretariat.md",
        "TriCompany/docs/workflow/host-object-publish-flow.md",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
        "TriMetaverse/docs/registry/company-governance-state.md",
    ),
    role_description="Role-level reusable administration, secretariat and governance documentation knowledge for the ChiefAdministrativeOfficer role.",
    employee_description="Employee-instance working knowledge for the current chief-administrative-officer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee chief-administrative-officer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "ChiefAdministrativeOfficer is enabled as an independent live host agent in the current Copilot-host phase.",
        "The live discovery entry is TriMetaverse/.github/agents/chief-administrative-officer.agent.md.",
        "CAO owns administration, secretariat mechanism, meeting governance and governance documentation ownership; this does not imply TriMC formal host switch.",
    ),
    live_entry_ref="TriMetaverse/.github/agents/chief-administrative-officer.agent.md",
)


DECLARED_HOST_OBJECT_SETS = (
    RD_TRAINER_HOST_OBJECT_SET,
    CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET,
    CHIEF_PRODUCT_OFFICER_HOST_OBJECT_SET,
    CHIEF_TECHNOLOGY_OFFICER_HOST_OBJECT_SET,
    CHIEF_MARKETING_OFFICER_HOST_OBJECT_SET,
    CHIEF_OPERATING_OFFICER_HOST_OBJECT_SET,
    CHIEF_FINANCIAL_OFFICER_HOST_OBJECT_SET,
    CHIEF_HUMAN_RESOURCES_OFFICER_HOST_OBJECT_SET,
    CHIEF_ADMINISTRATIVE_OFFICER_HOST_OBJECT_SET,
)

LEGACY_EMPLOYEE_ID_ALIASES = {
    "project-trainer": "rd-trainer",
}

DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE = {definition.employee_id: definition for definition in DECLARED_HOST_OBJECT_SETS}
DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE.update(
    {
        legacy_employee_id: DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE[canonical_employee_id]
        for legacy_employee_id, canonical_employee_id in LEGACY_EMPLOYEE_ID_ALIASES.items()
    }
)


def canonical_employee_id(employee_id: str) -> str:
    return LEGACY_EMPLOYEE_ID_ALIASES.get(employee_id, employee_id)


def host_binding_profile_reference(employee_id: str) -> str:
    return f"TriCompany/.github/binding-profiles/{employee_id}.json"


def host_binding_profile_path(source_root: str | Path, employee_id: str) -> Path:
    return Path(source_root) / SOURCE_HOST_BINDING_PROFILE_DIR / f"{employee_id}.json"


def write_host_binding_profiles(
    source_root: str | Path,
    *,
    employee_ids: Iterable[str] | None = None,
) -> tuple[Path, ...]:
    definitions = DECLARED_HOST_OBJECT_SETS if employee_ids is None else tuple(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE[employee_id] for employee_id in employee_ids)
    return tuple(_write_host_binding_profile(source_root=source_root, definition=definition) for definition in definitions)


def _write_host_binding_profile(*, source_root: str | Path, definition: HostObjectSetDefinition) -> Path:
    profile_path = host_binding_profile_path(source_root, definition.employee_id)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(_render_host_binding_profile(definition), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return profile_path


def _render_host_binding_profile(definition: HostObjectSetDefinition) -> dict[str, Any]:
    support_root = Path(SUPPORT_ROOT_REFERENCE)
    role = role_workspace(definition.role_id, support_root)
    employee = employee_workspace(definition.employee_id, support_root)
    org = org_shared_workspace(support_root)
    audit = audit_workspace(support_root)
    live_entry = {
        "status": definition.live_entry_status,
        "path": definition.live_entry_ref,
        "identityRule": "reuse-existing-live-entry" if definition.live_entry_ref else "not-published",
    }
    profile: dict[str, Any] = {
        "bindingProfileId": f"{definition.employee_id}-host-binding-v0.1",
        "objectSetId": definition.object_set_id,
        "status": definition.status,
        "employeeId": definition.employee_id,
        "ownerRole": definition.owner_role,
        "hostStage": definition.host_stage,
        "sourceManifest": SOURCE_HOST_OBJECT_MANIFEST_REFERENCE,
        "supportManifest": SUPPORT_HOST_OBJECT_MANIFEST_REFERENCE,
        "liveEntry": live_entry,
        "supportObjects": _support_object_entries(
            role=role,
            employee=employee,
            org=org,
            audit=audit,
            legacy_support_objects=definition.legacy_support_objects,
        ),
        "runtimeNamespaces": _runtime_namespace_entries(employee.identifier),
        "notes": _notes_with_consumption_boundary(definition.notes),
        "governedBy": list(HOST_OBJECT_GOVERNED_BY),
    }
    if definition.employee_display_name:
        profile["employeeDisplayName"] = definition.employee_display_name
    return profile


def generate_role_employee_host_objects(
    *,
    support_root: str | Path,
    object_set_id: str,
    role_id: str,
    employee_id: str,
    owner_role: str,
    source_refs: Iterable[str],
    generated_at: str = RD_TRAINER_GENERATED_AT,
) -> GeneratedHostObjectSet:
    definition = HostObjectSetDefinition(
        object_set_id=object_set_id,
        role_id=role_id,
        employee_id=employee_id,
        owner_role=owner_role,
        source_refs=tuple(source_refs),
        role_description=f"Role-level reusable knowledge for {owner_role}.",
        employee_description=f"Employee-instance working knowledge for {employee_id}.",
        generator="python -m runtime.cognition.employee_host_object_generation",
        live_entry_status="not-published",
        host_stage="support-payload-generated-only",
        notes=("This manifest governs host-consumed object payloads, not source truth.",),
        generated_at=generated_at,
    )
    return generate_host_object_set(support_root=support_root, definition=definition)


def generate_host_object_set(
    *,
    support_root: str | Path,
    definition: HostObjectSetDefinition,
) -> GeneratedHostObjectSet:
    support_root_path = Path(support_root)
    role = role_workspace(definition.role_id, support_root_path)
    employee = employee_workspace(definition.employee_id, support_root_path)
    org = org_shared_workspace(support_root_path)
    audit = audit_workspace(support_root_path)
    for workspace in (role, employee, org, audit):
        workspace.ensure_directories()

    _write_workspace_readme(
        role,
        object_set_id=definition.object_set_id,
        owner_role=definition.owner_role,
        source_refs=definition.source_refs,
        generated_at=definition.generated_at,
        live_entry_status=definition.live_entry_status,
        description=definition.role_description,
    )
    _write_workspace_readme(
        employee,
        object_set_id=definition.object_set_id,
        owner_role=definition.owner_role,
        source_refs=definition.source_refs,
        generated_at=definition.generated_at,
        live_entry_status=definition.live_entry_status,
        description=definition.employee_description,
        employee_display_name=definition.employee_display_name,
    )
    _write_shared_workspace_readme(org, generated_at=definition.generated_at)
    _write_shared_workspace_readme(audit, generated_at=definition.generated_at)

    manifest_path = support_root_path / HOST_OBJECT_MANIFEST_NAME
    object_set: dict[str, Any] = {
        "objectSetId": definition.object_set_id,
        "status": definition.status,
        "ownerRole": definition.owner_role,
        "generatedAt": definition.generated_at,
        "generator": definition.generator,
        "sourceRefs": list(definition.source_refs),
        "bindingProfile": host_binding_profile_reference(definition.employee_id),
        "supportObjects": _support_object_entries(
            role=role,
            employee=employee,
            org=org,
            audit=audit,
            legacy_support_objects=definition.legacy_support_objects,
        ),
        "runtimeNamespaces": _runtime_namespace_entries(employee.identifier),
        "liveEntryStatus": definition.live_entry_status,
        "notes": _notes_with_consumption_boundary(definition.notes),
    }
    if definition.employee_display_name:
        object_set["employeeDisplayName"] = definition.employee_display_name

    _upsert_manifest(manifest_path, object_set=object_set, replaces_object_set_ids=definition.replaces_object_set_ids)
    return GeneratedHostObjectSet(
        object_set_id=definition.object_set_id,
        support_root=support_root_path,
        role_workspace=role,
        employee_workspace=employee,
        org_shared_workspace=org,
        audit_workspace=audit,
        manifest_path=manifest_path,
    )


def _write_workspace_readme(
    workspace: KnowledgeWorkspace,
    *,
    object_set_id: str,
    owner_role: str,
    source_refs: Iterable[str],
    generated_at: str,
    live_entry_status: str,
    description: str,
    employee_display_name: str | None = None,
) -> None:
    workspace.root.mkdir(parents=True, exist_ok=True)
    source_lines = "\n".join(f"- {source_ref}" for source_ref in source_refs)
    display_name_line = f"- employeeDisplayName: {employee_display_name}\n" if employee_display_name else ""
    content = (
        f"# {workspace.identifier} {workspace.kind.title()} Knowledge Workspace\n\n"
        f"- objectSetId: {object_set_id}\n"
        f"- workspaceKind: {workspace.kind}\n"
        f"- workspaceId: {workspace.identifier}\n"
        f"- ownerRole: {owner_role}\n"
        f"{display_name_line}"
        f"- generatedAt: {generated_at}\n"
        f"- syncMode: support-object-set\n"
        f"- liveEntryStatus: {live_entry_status}\n\n"
        f"{description}\n\n"
        "This directory is generated as current-host payload under `TriCompany-copilot-host-assets`. "
        "It is not source truth; source definitions remain in `TriCompany/`.\n\n"
        "Concrete employee consumption records belong in employee wiki pages such as "
        "`wiki/employee-consumption-records.md` or runtime cognition state; source cognitive layer files remain contracts only.\n\n"
        "## Directory Contract\n\n"
        "- inbox/: raw training or role/employee input material\n"
        "- wiki/: curated knowledge pages\n"
        "- audit/: generation, review, and source-tracking records\n"
        "- workbench/: rendered workspace snapshots\n\n"
        "## Source Refs\n\n"
        f"{source_lines}\n"
    )
    (workspace.root / "README.md").write_text(content, encoding="utf-8")


def _write_shared_workspace_readme(workspace: KnowledgeWorkspace, *, generated_at: str) -> None:
    workspace.root.mkdir(parents=True, exist_ok=True)
    title = "Org Shared" if workspace.kind == "org" else "Audit"
    description = (
        "Shared company knowledge workspace used by generated employee object sets."
        if workspace.kind == "org"
        else "Shared audit workspace used to track generated employee object sets and source boundaries."
    )
    content = (
        f"# {title} Knowledge Workspace\n\n"
        f"- workspaceKind: {workspace.kind}\n"
        f"- workspaceId: {workspace.identifier}\n"
        f"- generatedAt: {generated_at}\n"
        f"- syncMode: support-object-set\n"
        f"- liveEntryStatus: shared-support-object\n\n"
        f"{description}\n\n"
        "This directory is support payload under `TriCompany-copilot-host-assets`. "
        "Runtime markdown state remains under `TRICOMPANY_COGNITION_HOME` or `.tricompany-cognition` and is not generated here.\n\n"
        "## Directory Contract\n\n"
        "- inbox/: shared raw inputs awaiting promotion\n"
        "- wiki/: curated shared or audit pages\n"
        "- audit/: generation, review, and source-tracking records\n"
        "- workbench/: rendered workspace snapshots\n"
    )
    (workspace.root / "README.md").write_text(content, encoding="utf-8")


def _upsert_manifest(
    manifest_path: Path,
    *,
    object_set: dict[str, Any],
    replaces_object_set_ids: Iterable[str] = (),
) -> None:
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "manifestId": "tricompany-host-object-manifest-v0.1",
            "status": "staging",
            "sourceRepo": "TriCompany",
            "supportRoot": SUPPORT_ROOT_REFERENCE,
            "notDocsPublishedCopyManifest": True,
            "governedBy": list(HOST_OBJECT_GOVERNED_BY),
            "objectSets": [],
        }

    manifest["status"] = "staging"
    manifest["sourceRepo"] = "TriCompany"
    manifest["supportRoot"] = SUPPORT_ROOT_REFERENCE
    manifest["notDocsPublishedCopyManifest"] = True
    manifest["governedBy"] = list(HOST_OBJECT_GOVERNED_BY)

    replaced_object_set_ids = set(replaces_object_set_ids)
    object_sets = [
        existing
        for existing in manifest.get("objectSets", [])
        if existing.get("objectSetId") != object_set["objectSetId"]
        and existing.get("objectSetId") not in replaced_object_set_ids
    ]
    object_sets.append(object_set)
    manifest["objectSets"] = object_sets
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _notes_with_consumption_boundary(notes: Iterable[str]) -> list[str]:
    merged = list(notes)
    if CONSUMPTION_DATA_BOUNDARY_NOTE not in merged:
        merged.append(CONSUMPTION_DATA_BOUNDARY_NOTE)
    return merged


def _support_object_entries(
    *,
    role: KnowledgeWorkspace,
    employee: KnowledgeWorkspace,
    org: KnowledgeWorkspace,
    audit: KnowledgeWorkspace,
    legacy_support_objects: tuple[Mapping[str, str], ...],
) -> list[dict[str, str]]:
    return [
        {
            "kind": "role-knowledge-workspace",
            "workspaceId": role.identifier,
            "path": _support_relative_path(role.root),
            "tracking": "tracked",
        },
        {
            "kind": "employee-knowledge-workspace",
            "workspaceId": employee.identifier,
            "path": _support_relative_path(employee.root),
            "tracking": "tracked",
        },
        {
            "kind": "org-shared-knowledge-workspace",
            "workspaceId": org.identifier,
            "path": _support_relative_path(org.root),
            "tracking": "tracked",
        },
        {
            "kind": "audit-knowledge-workspace",
            "workspaceId": audit.identifier,
            "path": _support_relative_path(audit.root),
            "tracking": "tracked",
        },
        *[dict(item) for item in legacy_support_objects],
    ]


def _runtime_namespace_entries(employee_workspace_id: str) -> list[dict[str, str]]:
    return [
        {
            "kind": "employee-private-runtime-namespace",
            "namespace": f"employee/{employee_workspace_id}",
            "storage": "TRICOMPANY_COGNITION_HOME or .tricompany-cognition",
            "tracking": "runtime-state",
            "creationRule": "created on first cognition write, not by host object generation",
        },
        {
            "kind": "org-shared-runtime-namespace",
            "namespace": "org/shared",
            "storage": "TRICOMPANY_COGNITION_HOME or .tricompany-cognition",
            "tracking": "runtime-state",
            "creationRule": "shared across employees when runtime providers write shared memory",
        },
        {
            "kind": "org-audit-runtime-namespace",
            "namespace": "org/audit",
            "storage": "TRICOMPANY_COGNITION_HOME or .tricompany-cognition",
            "tracking": "runtime-state",
            "creationRule": "shared audit namespace created by runtime providers",
        },
    ]


def _support_relative_path(path: Path) -> str:
    parts = path.parts
    if "TriCompany-copilot-host-assets" in parts:
        start = parts.index("TriCompany-copilot-host-assets")
        return "/".join(parts[start:])
    return path.as_posix()
