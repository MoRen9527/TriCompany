from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.host_object_generation import (
    DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE,
    DECLARED_HOST_OBJECT_SETS,
    HOST_ENTRY_LIVE_MANIFEST_STATUSES,
    canonical_employee_id,
    derive_host_entry_status,
    render_host_binding_profile,
    write_host_binding_profiles,
)
from runtime.cognition.knowledge_workspace import normalize_workspace_id
from runtime.cognition.source_publish_check import (
    DEFAULT_HOST_ID,
    HOST_RENDER_REGISTRY,
    _derive_host_target,
)


# ── binding profile 三源一致性校验（FADE-ASSESS-004）───────────────────────
#
# 定案：binding profile = 发布绑定关系的派生记录。
# - 语义真源收敛 contract（source-agents/<id>/<id>.contract.yaml）
# - 绑定事实收敛 manifest（source-agents/registries/trimetaverse-live-agent-publish-manifest.json）
# - 禁人工编辑，由生成管线重建
# - 不可替代部分 = liveEntry.identityRule 与 notes（本模块不校验）
#
# hostEntries 多宿主承载（FADE 质量审核 3 问题 3 / CEO 2026-08-20 走查，CTO 定案）：
# - liveEntry 保留 copilot 唯一承载位（现状语义零变化、既有消费方零改动）
# - hostEntries 只承载非 copilot 宿主（claude 起步），由生成管线从 manifest +
#   HOST_RENDER_REGISTRY 派生；缺省/空 = 旧 profile 兼容
# - 校验：B1-B3 对每条目同构扩展（B2 多宿主版 = path == derive(manifest.target, host)），
#   新增 B4 host 枚举 / B5 copilot 拒绝 / B6 派生一致；C 组不动
#
# 分级约定：
# - error：三源事实冲突或真源缺失，生成路径必须拒绝写入
# - warn：派生字段/落后状态/语义等级差异，不阻塞写入但必须可见

Severity = Literal["error", "warn"]

MANIFEST_REL_PATH = "source-agents/registries/trimetaverse-live-agent-publish-manifest.json"
CONTRACT_REL_DIR = "source-agents"
BINDING_PROFILE_REL_DIR = ".github/binding-profiles"
SUPPORT_ROOT_REFERENCE = "TriCompany-copilot-host-assets"
LIVE_ENTRY_ROOT_REFERENCE = "TriMetaverse/.github/agents"
STANDARD_WORKSPACE_KINDS = (
    "role-knowledge-workspace",
    "employee-knowledge-workspace",
    "org-shared-knowledge-workspace",
    "audit-knowledge-workspace",
)

# liveEntry.status → 允许的 manifest status 集合（语义等价映射）
LIVE_STATUS_TO_MANIFEST_STATUSES = {
    "current-copilot-host-live": frozenset({"current-copilot-host-live", "source-published-live-entry"}),
    "live-entry-existing-not-changed": frozenset({"current-copilot-host-live", "source-published-live-entry"}),
    "source-declared-staging": frozenset(),
    "not-published": frozenset(),
}

# hostEntries.status → 允许的 manifest status（LIVE_STATUS_TO_MANIFEST_STATUSES 同构扩展）：
# "current-host-live"（宿主中性 live）与 liveEntry "current-copilot-host-live" 共享同一
# 语义等价集；host 中性 staging / not-published 键沿用原表。live 家族与渲染侧
# HOST_ENTRY_LIVE_MANIFEST_STATUSES 必须一致（防双表漂移，导入时硬校验）。
HOST_ENTRY_STATUS_TO_MANIFEST_STATUSES: dict[str, frozenset[str]] = {
    **LIVE_STATUS_TO_MANIFEST_STATUSES,
    "current-host-live": LIVE_STATUS_TO_MANIFEST_STATUSES["current-copilot-host-live"],
}
if HOST_ENTRY_LIVE_MANIFEST_STATUSES != LIVE_STATUS_TO_MANIFEST_STATUSES["current-copilot-host-live"]:
    raise RuntimeError("HOST_ENTRY_LIVE_MANIFEST_STATUSES 与 LIVE_STATUS_TO_MANIFEST_STATUSES live 家族不一致")

# 生成器实际使用的 status 值（用于 G1 落后检测）
STAGING_PROFILE_STATUSES = ("generated-staging", "source-declared-staging")


@dataclass(frozen=True)
class ConsistencyIssue:
    severity: Severity
    rule: str
    field: str
    message: str
    expected: str | None = None
    actual: str | None = None


@dataclass(frozen=True)
class ConsistencyReport:
    employee_id: str
    issues: tuple[ConsistencyIssue, ...]

    @property
    def is_consistent(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warn")


def _issue(
    severity: Severity,
    rule: str,
    field: str,
    message: str,
    *,
    expected: str | None = None,
    actual: str | None = None,
) -> ConsistencyIssue:
    return ConsistencyIssue(
        severity=severity,
        rule=rule,
        field=field,
        message=message,
        expected=expected,
        actual=actual,
    )


def _expected_live_entry_path(employee_id: str) -> str:
    return f"{LIVE_ENTRY_ROOT_REFERENCE}/{employee_id}.agent.md"


def _expected_employee_workspace_path(employee_id: str) -> str:
    return f"{SUPPORT_ROOT_REFERENCE}/knowledge/employees/{employee_id}"


def _expected_role_workspace_path(role_slug: str) -> str:
    return f"{SUPPORT_ROOT_REFERENCE}/knowledge/roles/{role_slug}"


def _contract_agent_id(contract: Mapping) -> str | None:
    value = contract.get("contract")
    if isinstance(value, Mapping):
        agent_id = value.get("agent_id")
        if isinstance(agent_id, str):
            return agent_id
    return None


def _contract_identity_role(contract: Mapping) -> str | None:
    identity = contract.get("identity")
    if isinstance(identity, Mapping):
        role = identity.get("role")
        if isinstance(role, str):
            return role
    return None


def find_manifest_entry(manifest: Mapping, employee_id: str) -> dict | None:
    """按派生 target（TriMetaverse/.github/agents/<id>.agent.md）匹配 liveEntries 条目。"""
    expected_target = _expected_live_entry_path(employee_id)
    for entry in manifest.get("liveEntries", []):
        if isinstance(entry, Mapping) and entry.get("target") == expected_target:
            return dict(entry)
    return None


def validate_binding_profile_consistency(
    binding: Mapping,
    contract: Mapping | None,
    manifest_entry: Mapping | None,
    *,
    manifest_status: str | None = None,
) -> ConsistencyReport:
    """对单个 binding profile 做三源一致性校验，返回结构化差异报告。

    Args:
        binding: binding profile JSON 对象。
        contract: contract YAML 解析结果（None 表示真源缺失，报 E1）。
        manifest_entry: 该员工的 liveEntries 条目（None 表示未发布或匹配失败）。
        manifest_status: manifest 顶层 status（None 表示 manifest 缺失，报 F1）。
    """
    issues: list[ConsistencyIssue] = []
    employee_id = binding.get("employeeId") if isinstance(binding.get("employeeId"), str) else ""

    # ── F1: manifest 真源缺失 ──────────────────────────────────────────────
    if manifest_status is None:
        issues.append(_issue("error", "F1", "manifest", "live-agent publish manifest 缺失，绑定事实真源不可用"))
    manifest_entry = manifest_entry if manifest_status is not None else None

    # ── E1: contract 真源缺失/无效 ─────────────────────────────────────────
    contract_agent_id = _contract_agent_id(contract) if contract is not None else None
    if contract is None or contract_agent_id is None:
        issues.append(_issue("error", "E1", "contract", "contract 缺失或缺少 contract.agent_id，语义真源不可用"))
        if not employee_id:
            issues.append(_issue("error", "A0", "employeeId", "binding.employeeId 缺失"))
        return ConsistencyReport(employee_id=employee_id, issues=tuple(issues))

    # ── A: employeeId 语义一致性 ───────────────────────────────────────────
    if not employee_id:
        issues.append(_issue("error", "A0", "employeeId", "binding.employeeId 缺失"))
    elif employee_id != contract_agent_id:
        issues.append(
            _issue(
                "error",
                "A1",
                "employeeId",
                "binding.employeeId 与 contract.agent_id 不一致",
                expected=contract_agent_id,
                actual=employee_id,
            )
        )
    else:
        binding_profile_id = binding.get("bindingProfileId")
        if not isinstance(binding_profile_id, str):
            issues.append(_issue("error", "A2", "bindingProfileId", "binding.bindingProfileId 缺失"))
        elif binding_profile_id != f"{employee_id}-host-binding-v0.1":
            issues.append(
                _issue(
                    "warn",
                    "A2",
                    "bindingProfileId",
                    "bindingProfileId 与 employeeId 派生规则不一致",
                    expected=f"{employee_id}-host-binding-v0.1",
                    actual=binding_profile_id,
                )
            )

    # ── B: liveEntry 一致性 ────────────────────────────────────────────────
    live_entry = binding.get("liveEntry")
    if not isinstance(live_entry, Mapping):
        issues.append(_issue("error", "B0", "liveEntry", "binding.liveEntry 缺失"))
    else:
        live_status = live_entry.get("status")
        if not isinstance(live_status, str):
            issues.append(_issue("error", "B0", "liveEntry.status", "binding.liveEntry.status 缺失"))
        else:
            expected_target = _expected_live_entry_path(employee_id)
            live_path = live_entry.get("path")
            if manifest_entry is not None:
                manifest_status_value = manifest_entry.get("status")
                allowed = LIVE_STATUS_TO_MANIFEST_STATUSES.get(live_status)
                if allowed is None:
                    issues.append(
                        _issue(
                            "error",
                            "B1",
                            "liveEntry.status",
                            f"未知 liveEntry.status 值 {live_status!r}，无法判定语义",
                            actual=live_status,
                        )
                    )
                elif manifest_status_value not in allowed:
                    issues.append(
                        _issue(
                            "error",
                            "B1",
                            "liveEntry.status",
                            "liveEntry.status 与 manifest 条目 status 语义不一致（漂移）",
                            expected=manifest_status_value,
                            actual=live_status,
                        )
                    )
                manifest_target = manifest_entry.get("target")
                if isinstance(manifest_target, str) and live_path != manifest_target:
                    issues.append(
                        _issue(
                            "error",
                            "B2",
                            "liveEntry.path",
                            "liveEntry.path 与 manifest 条目 target 不一致",
                            expected=manifest_target,
                            actual=live_path if isinstance(live_path, str) else None,
                        )
                    )
                manifest_source = manifest_entry.get("source")
                if isinstance(manifest_source, str) and f"/source-agents/{employee_id}/" not in manifest_source:
                    issues.append(
                        _issue(
                            "error",
                            "A3",
                            "manifest.source",
                            "manifest 条目 source 未指向该员工的 source-agents 目录",
                            expected=f"TriCompany/source-agents/{employee_id}/...",
                            actual=manifest_source,
                        )
                    )
            if isinstance(live_path, str) and live_path != expected_target:
                issues.append(
                    _issue(
                        "error",
                        "B3",
                        "liveEntry.path",
                        "liveEntry.path 与 employeeId 派生规则不一致",
                        expected=expected_target,
                        actual=live_path,
                    )
                )

    # ── B-HOST: hostEntries 多宿主承载（FADE 质量审核 3 问题 3 / CEO 2026-08-20 走查，CTO 定案）──
    # liveEntry 保留 copilot 唯一承载位；hostEntries 只承载非 copilot 宿主（claude 起步）。
    # 缺省/空 = 旧 profile 兼容（既有消费方零改动）。B1-B3 对每条目同构扩展：
    #   B1  status 语义 vs manifest 条目 status（同 LIVE_STATUS_TO_MANIFEST_STATUSES 映射）
    #   B2  path == derive(manifest.target, host)（与渲染管线共用 _derive_host_target，派生闭环）
    #   B3  path == derive(employeeId 派生规则, host)
    # 新增：B4 host ∈ HOST_RENDER_REGISTRY 枚举（含重复拒绝）；B5 host=copilot 拒绝
    #      （双承载漂移）；B6 派生一致（status 必须等于生成管线从 manifest 派生值，禁人工编辑）。
    # C 组不动。
    host_entries = binding.get("hostEntries")
    if host_entries is None:
        pass  # 缺省 = 旧 profile 兼容
    elif not isinstance(host_entries, list):
        issues.append(_issue("error", "B0", "hostEntries", "binding.hostEntries 必须为数组"))
    else:
        seen_hosts: set[str] = set()
        for index, host_entry in enumerate(host_entries):
            entry_field = f"hostEntries[{index}]"
            if not isinstance(host_entry, Mapping):
                issues.append(_issue("error", "B0", entry_field, "hostEntries 条目必须为对象"))
                continue
            host = host_entry.get("host")
            entry_status = host_entry.get("status")
            entry_path = host_entry.get("path")
            if not isinstance(host, str) or not host:
                issues.append(_issue("error", "B0", f"{entry_field}.host", "hostEntries 条目缺少 host"))
                continue
            # B5：copilot 由 liveEntry 唯一承载，禁止出现在 hostEntries（防双承载漂移）
            if host == DEFAULT_HOST_ID:
                issues.append(
                    _issue(
                        "error",
                        "B5",
                        f"{entry_field}.host",
                        "hostEntries 禁止 host=copilot（copilot 由 liveEntry 唯一承载）",
                        expected="非 copilot 宿主",
                        actual=host,
                    )
                )
                continue
            # B4：host ∈ HOST_RENDER_REGISTRY 枚举校验（含重复 host 拒绝）
            if host not in HOST_RENDER_REGISTRY:
                issues.append(
                    _issue(
                        "error",
                        "B4",
                        f"{entry_field}.host",
                        f"未知宿主 {host!r}，不在 HOST_RENDER_REGISTRY 中",
                        expected=" | ".join(sorted(HOST_RENDER_REGISTRY)),
                        actual=host,
                    )
                )
                continue
            if host in seen_hosts:
                issues.append(
                    _issue(
                        "error",
                        "B4",
                        f"{entry_field}.host",
                        f"hostEntries 中存在重复 host {host!r}",
                        actual=host,
                    )
                )
            seen_hosts.add(host)
            if not isinstance(entry_status, str) or not entry_status:
                issues.append(_issue("error", "B0", f"{entry_field}.status", "hostEntries 条目缺少 status"))
            if not isinstance(entry_path, str) or not entry_path:
                issues.append(_issue("error", "B0", f"{entry_field}.path", "hostEntries 条目缺少 path"))
            if not isinstance(host_entry.get("identityRule"), str) or not host_entry.get("identityRule"):
                issues.append(_issue("error", "B0", f"{entry_field}.identityRule", "hostEntries 条目缺少 identityRule（绑定决策证据，按宿主注册表派生）"))
            # B1（多宿主版）：status 语义 vs manifest 条目 status（同 liveEntry B1 同构扩展）
            if isinstance(entry_status, str) and entry_status and manifest_entry is not None:
                allowed = HOST_ENTRY_STATUS_TO_MANIFEST_STATUSES.get(entry_status)
                if allowed is None:
                    issues.append(
                        _issue(
                            "error",
                            "B1",
                            f"{entry_field}.status",
                            f"未知 hostEntries.status 值 {entry_status!r}，无法判定语义",
                            actual=entry_status,
                        )
                    )
                elif manifest_entry.get("status") not in allowed:
                    issues.append(
                        _issue(
                            "error",
                            "B1",
                            f"{entry_field}.status",
                            "hostEntries.status 与 manifest 条目 status 语义不一致（漂移）",
                            expected=manifest_entry.get("status"),
                            actual=entry_status,
                        )
                    )
            # B2（多宿主版）：path == derive(manifest.target, host) 派生关系校验（渲染管线闭环）
            if isinstance(entry_path, str) and entry_path and manifest_entry is not None:
                manifest_target = manifest_entry.get("target")
                if isinstance(manifest_target, str):
                    derived_path, derive_error = _derive_host_target(manifest_target, host)
                    if derive_error or derived_path != entry_path:
                        issues.append(
                            _issue(
                                "error",
                                "B2",
                                f"{entry_field}.path",
                                "hostEntries.path 与 manifest target 的宿主派生不一致",
                                expected=derived_path if not derive_error else derive_error,
                                actual=entry_path,
                            )
                        )
            # B3（多宿主版）：path == derive(employeeId 派生规则, host)
            if isinstance(entry_path, str) and entry_path:
                expected_derived, derive_error = _derive_host_target(_expected_live_entry_path(employee_id), host)
                if not derive_error and entry_path != expected_derived:
                    issues.append(
                        _issue(
                            "error",
                            "B3",
                            f"{entry_field}.path",
                            "hostEntries.path 与 employeeId 宿主派生规则不一致",
                            expected=expected_derived,
                            actual=entry_path,
                        )
                    )
            # B6：派生一致（status 必须等于生成管线从 manifest 派生值，禁人工编辑）
            if isinstance(entry_status, str) and entry_status and manifest_entry is not None:
                derived_status = derive_host_entry_status(manifest_entry)
                if derived_status is None:
                    issues.append(
                        _issue(
                            "error",
                            "B6",
                            f"{entry_field}.status",
                            "hostEntries 条目存在但 manifest status 不在 live 家族（无法派生）",
                            actual=entry_status,
                        )
                    )
                elif entry_status != derived_status:
                    issues.append(
                        _issue(
                            "error",
                            "B6",
                            f"{entry_field}.status",
                            "hostEntries.status 与生成管线派生值不一致（禁人工编辑）",
                            expected=derived_status,
                            actual=entry_status,
                        )
                    )
        # B6：manifest 无条目但 hostEntries 非空 → 条目不可派生（整体拒绝）；
        # 空数组 = 旧 profile 兼容（与缺省等价，不产生条目级校验）。
        if manifest_entry is None and host_entries:
            issues.append(
                _issue("error", "B6", "hostEntries", "manifest 无条目但 hostEntries 非空——宿主条目只能由生成管线从 manifest 派生")
            )

    # ── C: hostStage 与 manifest status 三档 ───────────────────────────────
    host_stage = binding.get("hostStage")
    if not isinstance(host_stage, str):
        issues.append(_issue("error", "C0", "hostStage", "binding.hostStage 缺失"))
    elif manifest_entry is not None:
        manifest_status_value = manifest_entry.get("status")
        if host_stage != "current-copilot-host-live":
            severity: Severity = "error" if manifest_status_value == "current-copilot-host-live" else "warn"
            issues.append(
                _issue(
                    severity,
                    "C1" if severity == "error" else "C2",
                    "hostStage",
                    "manifest 已登记发布条目，hostStage 应声明当前宿主 live",
                    expected="current-copilot-host-live",
                    actual=host_stage,
                )
            )
    elif manifest_status is not None:
        profile_status = binding.get("status")
        if host_stage != "support-payload-generated-only":
            if profile_status == "source-declared-staging":
                issues.append(
                    _issue(
                        "warn",
                        "C3",
                        "hostStage",
                        "源侧声明阶段（source-declared-staging）但 manifest 无条目，hostStage 建议 support-payload-generated-only",
                        expected="support-payload-generated-only",
                        actual=host_stage,
                    )
                )
            else:
                issues.append(
                    _issue(
                        "error",
                        "C3",
                        "hostStage",
                        "manifest 无条目但 hostStage 未声明 support-payload-generated-only",
                        expected="support-payload-generated-only",
                        actual=host_stage,
                    )
                )

    # ── D: supportObjects 与 contract 语义 ─────────────────────────────────
    support_objects = binding.get("supportObjects")
    if not isinstance(support_objects, list):
        issues.append(_issue("error", "D0", "supportObjects", "binding.supportObjects 缺失"))
    else:
        by_kind = {entry.get("kind"): entry for entry in support_objects if isinstance(entry, Mapping) and isinstance(entry.get("kind"), str)}
        for kind in STANDARD_WORKSPACE_KINDS:
            if kind not in by_kind:
                issues.append(_issue("error", "D1", f"supportObjects.{kind}", f"缺少标准 support object：{kind}"))
        employee_obj = by_kind.get("employee-knowledge-workspace")
        if employee_obj is not None:
            workspace_id = employee_obj.get("workspaceId")
            if workspace_id != employee_id:
                issues.append(
                    _issue(
                        "error",
                        "D2",
                        "supportObjects.employee-knowledge-workspace.workspaceId",
                        "employee workspaceId 与 employeeId 不一致",
                        expected=employee_id,
                        actual=workspace_id,
                    )
                )
            obj_path = employee_obj.get("path")
            expected_employee_path = _expected_employee_workspace_path(employee_id)
            if obj_path != expected_employee_path:
                issues.append(
                    _issue(
                        "error",
                        "D3",
                        "supportObjects.employee-knowledge-workspace.path",
                        "employee workspace path 与 employeeId 派生规则不一致",
                        expected=expected_employee_path,
                        actual=obj_path,
                    )
                )
        role_obj = by_kind.get("role-knowledge-workspace")
        if role_obj is not None:
            role_slug_candidates = {normalize_workspace_id(contract_agent_id)}
            identity_role = _contract_identity_role(contract)
            if isinstance(identity_role, str):
                role_slug_candidates.add(normalize_workspace_id(identity_role))
            workspace_id = role_obj.get("workspaceId")
            if workspace_id not in role_slug_candidates:
                issues.append(
                    _issue(
                        "error",
                        "D4",
                        "supportObjects.role-knowledge-workspace.workspaceId",
                        "role workspaceId 与 contract 语义（agent_id/identity.role）不一致",
                        expected=" | ".join(sorted(role_slug_candidates)),
                        actual=workspace_id,
                    )
                )
            expected_role_path = _expected_role_workspace_path(str(workspace_id))
            if role_obj.get("path") != expected_role_path:
                issues.append(
                    _issue(
                        "warn",
                        "D4b",
                        "supportObjects.role-knowledge-workspace.path",
                        "role workspace path 与 workspaceId 派生规则不一致",
                        expected=expected_role_path,
                        actual=role_obj.get("path"),
                    )
                )
        org_obj = by_kind.get("org-shared-knowledge-workspace")
        if org_obj is not None and org_obj.get("path") != f"{SUPPORT_ROOT_REFERENCE}/knowledge/org/shared":
            issues.append(
                _issue(
                    "warn",
                    "D5",
                    "supportObjects.org-shared-knowledge-workspace.path",
                    "org-shared workspace path 与共享派生规则不一致",
                    expected=f"{SUPPORT_ROOT_REFERENCE}/knowledge/org/shared",
                    actual=org_obj.get("path"),
                )
            )
        audit_obj = by_kind.get("audit-knowledge-workspace")
        if audit_obj is not None and audit_obj.get("path") != f"{SUPPORT_ROOT_REFERENCE}/knowledge/audit":
            issues.append(
                _issue(
                    "warn",
                    "D6",
                    "supportObjects.audit-knowledge-workspace.path",
                    "audit workspace path 与共享派生规则不一致",
                    expected=f"{SUPPORT_ROOT_REFERENCE}/knowledge/audit",
                    actual=audit_obj.get("path"),
                )
            )

    # ── G: profile.status 落后检测（warn）─────────────────────────────────
    profile_status = binding.get("status")
    if isinstance(profile_status, str) and profile_status in STAGING_PROFILE_STATUSES and manifest_entry is not None:
        issues.append(
            _issue(
                "warn",
                "G1",
                "status",
                "profile 仍为生成/声明阶段状态，但 manifest 已登记发布条目——旧生成未随发布重建",
                expected="current-copilot-host-live 语义",
                actual=profile_status,
            )
        )

    return ConsistencyReport(employee_id=employee_id, issues=tuple(issues))


# ── 加载器 ────────────────────────────────────────────────────────────────

def _load_json_safe(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _load_yaml_safe(path: Path) -> dict | None:
    try:
        import yaml as _yaml

        with open(path, "r", encoding="utf-8") as fh:
            data = _yaml.safe_load(fh)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_manifest(source_root: str | Path) -> tuple[dict | None, str | None]:
    """加载 live-agent publish manifest。返回 (manifest, 顶层 status)。"""
    manifest = _load_json_safe(Path(source_root) / MANIFEST_REL_PATH)
    if manifest is None:
        return None, None
    status = manifest.get("status")
    return manifest, status if isinstance(status, str) else "unknown"


def load_contract(source_root: str | Path, employee_id: str) -> dict | None:
    """加载 source-agents/<id>/<id>.contract.yaml（V2 位置）。"""
    return _load_yaml_safe(Path(source_root) / CONTRACT_REL_DIR / employee_id / f"{employee_id}.contract.yaml")


def load_binding_profile(source_root: str | Path, employee_id: str) -> dict | None:
    return _load_json_safe(Path(source_root) / BINDING_PROFILE_REL_DIR / f"{employee_id}.json")


def validate_employee_binding(
    source_root: str | Path,
    employee_id: str,
    *,
    binding: Mapping | None = None,
) -> ConsistencyReport:
    """从 source root 加载三源并对单个员工做全链路校验。

    binding 可注入（生成路径渲染后的 profile 字典，避免依赖磁盘文件）。
    """
    manifest, manifest_status = load_manifest(source_root)
    contract = load_contract(source_root, canonical_employee_id(employee_id))
    if binding is None:
        binding = load_binding_profile(source_root, canonical_employee_id(employee_id))
    if not isinstance(binding, Mapping):
        return ConsistencyReport(
            employee_id=canonical_employee_id(employee_id),
            issues=(_issue("error", "B0", "binding", "binding profile 缺失或无法解析"),),
        )
    manifest_entry = None
    if manifest is not None:
        manifest_entry = find_manifest_entry(manifest, canonical_employee_id(employee_id))
    return validate_binding_profile_consistency(
        binding,
        contract,
        manifest_entry,
        manifest_status=manifest_status,
    )


def validate_all_bindings(
    source_root: str | Path,
    employee_ids: Iterable[str] | None = None,
) -> tuple[ConsistencyReport, ...]:
    """对全部（或指定）binding profiles 做三源一致性校验。"""
    if employee_ids is None:
        employee_ids = tuple(definition.employee_id for definition in DECLARED_HOST_OBJECT_SETS)
    return tuple(validate_employee_binding(source_root, employee_id) for employee_id in employee_ids)


def _render_report_text(report: ConsistencyReport) -> str:
    if not report.issues:
        return f"binding_profile={report.employee_id} consistent"
    lines = [f"binding_profile={report.employee_id} errors={report.error_count} warnings={report.warning_count}"]
    for issue in report.issues:
        detail = issue.message
        if issue.expected is not None or issue.actual is not None:
            detail = f"{detail} (expected={issue.expected!r}, actual={issue.actual!r})"
        lines.append(f"  [{issue.severity}] {issue.rule} {issue.field}: {detail}")
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────

EMPLOYEE_CHOICES = {
    "all": None,
    **{employee_id: (employee_id,) for employee_id in sorted(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE)},
}


def _resolve_target_ids(choice: str) -> tuple[str, ...]:
    if choice == "all":
        return tuple(definition.employee_id for definition in DECLARED_HOST_OBJECT_SETS)
    return tuple(dict.fromkeys(canonical_employee_id(employee_id) for employee_id in EMPLOYEE_CHOICES[choice]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Write or validate declared TriCompany employee host binding profiles.")
    parser.add_argument("--source-root", default=".", help="Path to the TriCompany source root.")
    parser.add_argument(
        "--employee",
        default="all",
        choices=sorted(EMPLOYEE_CHOICES),
        help="Employee binding profile to write or validate. Defaults to all declared employees.",
    )
    parser.add_argument(
        "--validate-binding",
        action="store_true",
        help="Validate binding profiles against contract and live-agent publish manifest without writing.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report for --validate-binding.")
    args = parser.parse_args()

    target_ids = _resolve_target_ids(args.employee)

    if args.validate_binding:
        reports = tuple(validate_employee_binding(args.source_root, employee_id) for employee_id in target_ids)
        if args.json:
            payload = {
                "sourceRoot": str(Path(args.source_root)),
                "profiles": [
                    {
                        "employeeId": report.employee_id,
                        "consistent": report.is_consistent,
                        "errors": report.error_count,
                        "warnings": report.warning_count,
                        "issues": [
                            {"severity": issue.severity, "rule": issue.rule, "field": issue.field, "message": issue.message, "expected": issue.expected, "actual": issue.actual}
                            for issue in report.issues
                        ],
                    }
                    for report in reports
                ],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for report in reports:
                print(_render_report_text(report))
        return 1 if any(not report.is_consistent for report in reports) else 0

    # 生成路径：先渲染校验（不落盘），error 级不一致 → 拒绝写入。
    # hostEntries 从 manifest 条目 + HOST_RENDER_REGISTRY 派生（禁人工编辑）；
    # manifest 缺失时保持旧 profile 形状（无 hostEntries，兼容）。
    manifest, _ = load_manifest(args.source_root)
    preflight_reports = []
    for employee_id in target_ids:
        definition = DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE[employee_id]
        manifest_entry = find_manifest_entry(manifest, employee_id) if manifest is not None else None
        rendered = render_host_binding_profile(definition, manifest_entry=manifest_entry)
        preflight_reports.append(validate_employee_binding(args.source_root, employee_id, binding=rendered))
    if any(not report.is_consistent for report in preflight_reports):
        for report in preflight_reports:
            if not report.is_consistent:
                print(_render_report_text(report), file=sys.stderr)
        print("binding_profile_write=refused inconsistent_with_contract_or_manifest", file=sys.stderr)
        return 1

    profile_paths = write_host_binding_profiles(args.source_root, employee_ids=target_ids, manifest=manifest)
    for profile_path in profile_paths:
        print(f"binding_profile={profile_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())