from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

# 兼容两种启动方式，常见的CLI入口兼容层。直接跑文件时，Python的包上下文可能不完整，需要把 repository root 加入 sys.path；如果作为模块跑，则正常解析包路径。
# 1. 作为模块：`python -m runtime.cognition.employee_source_kit ...`
# 2. 直接运行：`python runtime/cognition/employee_source_kit.py ...`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.knowledge_workspace import normalize_workspace_id


SOURCE_KIT_SUFFIXES = ("agent", "soul", "memory", "colleagues", "social")
COGNITIVE_LAYER_SUFFIXES = ("memory", "colleagues", "social")
SOURCE_AGENT_KIT_DIR = Path(".github") / "source-agents"
# 手工组件化员工目录（角色定义载体），与模板生成区 .github/source-agents/ 分开。
# 组件化员工（contract.yaml 形状）的编辑真源是 source-agents/<id>/agent-body.agent.md，
# 渲染真源是 source-agents/<id>/<id>.agent.md（合成文件）。
SOURCE_AGENTS_COMPONENT_DIR = Path("source-agents")
FORBIDDEN_HOST_BINDING_MARKERS = (
    "当前 live 入口位于",
    "TriMetaverse/.github/agents/",
    "TriCompany/.github/agents/",
    "当前 support 落点为",
    "当前 support 员工记录：",
    "TriCompany-copilot-host-assets/knowledge/employees/",
    ".tricompany-cognition/employee/",
)
FORBIDDEN_CONSUMPTION_MARKERS = (
    "## 阶段记忆记录",
    "## 工作关系人物档案",
    "## 工作事项记录",
    "## 社交人物档案",
    "## 社交事项记录",
    "## 运行同步摘录",
    "记录时间：",
    "最近整理时间：",
    "命名确认",
    "社交场景首选称呼",
)

# ── 内容归属校验：误植句模式清单（FADE 质量审核 2 问题 2 / CEO 2026-08-21 走查，CTO 定案）──
# 白名单式：以下句子是 employee source kit 模板的**角色无关通用纪律句**（骨架固定
# 句），纪律应由工程纪律文档承载，角色定义（agent-body 组件 / <id>.agent.md 合成
# 文件）只含角色职责。它们在角色定义中出现 = 模板段落误植（fade-quality-lessons.md
# 案例 2：CFO/CMO/COO 三员工源侧维护句模板误植）。
# 入册条件：该句在现役 14 个 agent-body 组件与合成文件中零出现（防误伤现役文件）；
# 角色化改写版（如"不把宿主 binding 或试运行上岗状态写成 TriMC 正式宿主切换"）
# 不匹配本清单原文，不构成误植。
FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS = (
    # agent 模板骨架句（_render_agent）
    "你维护的是 TriCompany 源侧岗位 / 员工定义",
    "把阶段性上下文、协作连续性和社交连续性留在宿主 employee workspace 或 runtime cognition state",
    "把稳定结论回写到对应 product、engineering、workflow、registry 或 training 真源",
    "先说明事实来源，再给出判断",
    "明确区分已落地、草案中、待验证、待初始化",
    "稳定结论回写源码真源；运行消费数据留在 support employee workspace 或 runtime cognition state",
    # soul 模板骨架句（_render_soul）
    "禁止把运行态消费记录写进源码侧认知层文件",
    "禁止把当前 Copilot-host 阶段写成 TriMC 正式宿主切换",
    "禁止把未验证能力写成已完成",
    "中文、自然、直接",
)


@dataclass(frozen=True)
class EmployeeSourceKitDefinition:
    employee_id: str
    agent_name: str
    role_title: str
    description: str
    role_scope: str
    display_name: str | None = None
    responsibilities: tuple[str, ...] = ()
    input_sources: tuple[str, ...] = ()
    voice_traits: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeneratedEmployeeSourceKit:
    employee_id: str
    files: Mapping[str, Path]


@dataclass(frozen=True)
class SourceKitValidationIssue:
    path: Path
    message: str


@dataclass(frozen=True)
class SourceKitValidationResult:
    employee_id: str
    issues: tuple[SourceKitValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


def source_kit_paths(source_root: str | Path, employee_id: str) -> dict[str, Path]:
    normalized_employee_id = normalize_workspace_id(employee_id)
    source_kit_root = Path(source_root) / SOURCE_AGENT_KIT_DIR / normalized_employee_id
    return {
        suffix: source_kit_root / f"{normalized_employee_id}.{suffix}.md"
        for suffix in SOURCE_KIT_SUFFIXES
    }


def role_definition_paths(source_root: str | Path, employee_id: str) -> tuple[Path, ...]:
    """组件化员工角色定义文件（内容归属校验对象）。

    编辑真源 agent-body.agent.md（contract.yaml paths.agent_body）与渲染真源
    <id>.agent.md（合成文件，发布管线的 source 侧）。两者都可能被模板段落误植；
    校验只覆盖这两个载体，不覆盖 .github/source-agents/ 模板生成区（骨架句在
    那里是模板的正常内容，不属于误植）。
    """
    normalized_employee_id = normalize_workspace_id(employee_id)
    component_root = Path(source_root) / SOURCE_AGENTS_COMPONENT_DIR / normalized_employee_id
    return (
        component_root / "agent-body.agent.md",
        component_root / f"{normalized_employee_id}.agent.md",
    )


def host_binding_profile_reference(employee_id: str) -> str:
    normalized_employee_id = normalize_workspace_id(employee_id)
    return f"TriCompany/.github/binding-profiles/{normalized_employee_id}.json"


def generate_employee_source_kit(
    source_root: str | Path,
    definition: EmployeeSourceKitDefinition,
    *,
    overwrite: bool = False,
) -> GeneratedEmployeeSourceKit:
    employee_id = normalize_workspace_id(definition.employee_id)
    normalized_definition = EmployeeSourceKitDefinition(
        employee_id=employee_id,
        agent_name=definition.agent_name,
        role_title=definition.role_title,
        description=definition.description,
        role_scope=definition.role_scope,
        display_name=definition.display_name,
        responsibilities=definition.responsibilities,
        input_sources=definition.input_sources,
        voice_traits=definition.voice_traits,
    )
    paths = source_kit_paths(source_root, employee_id)
    existing_paths = [path for path in paths.values() if path.exists()]
    if existing_paths and not overwrite:
        existing = ", ".join(path.as_posix() for path in existing_paths)
        raise FileExistsError(f"Refusing to overwrite existing employee source kit files: {existing}")

    rendered = _render_source_kit(normalized_definition)
    for suffix, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered[suffix], encoding="utf-8")
    return GeneratedEmployeeSourceKit(employee_id=employee_id, files=paths)


def check_content_attribution(source_root: str | Path, employee_id: str) -> SourceKitValidationResult:
    """内容归属校验：检测角色定义文件中的模板通用纪律句误植（FADE 加固 B 项）。

    白名单式清单 FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS：这些句是 employee source
    kit 模板的骨架固定句（所有角色相同、与具体岗位无关），应由工程纪律承载，
    不应出现在角色定义（agent-body 组件 / <id>.agent.md 合成文件）中。出现即
    误植，说明维护时把模板段落复制进了角色定义（fade-quality-lessons 案例 2）。
    """
    normalized_employee_id = normalize_workspace_id(employee_id)
    issues: list[SourceKitValidationIssue] = []
    for path in role_definition_paths(source_root, normalized_employee_id):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS:
            if marker in text:
                issues.append(
                    SourceKitValidationIssue(
                        path=path,
                        message=f"contains template discipline sentence (content attribution): {marker}",
                    )
                )
    return SourceKitValidationResult(employee_id=normalized_employee_id, issues=tuple(issues))


# ── 组件-合成文件同步校验（FADE 加固 D 项 / fade-quality-lessons 建议 3）──────
# 组件化员工（contract.yaml 形状）的双真源结构：
# - 编辑真源（组件）：source-agents/<id>/agent-body.agent.md（正文段落）、
#   soul.agent.md（认知分层约束等段落）、<id>.contract.yaml（身份事实）
# - 渲染真源（合成文件）：source-agents/<id>/<id>.agent.md
# 修改组件必须同步合成（或建立合成机制），否则发布链消费的是旧合成内容
# （"改组件不传导渲染"，fade-quality-lessons 案例 3 建议 3）。
# 校验语义（单向传导）：组件的每个 `## ` 段落必须完整出现在合成文件中，
# 缺失/不一致 = 漂移 → 提示重新合成/同步；合成文件独有的模板固定段落
# （渲染时补充、组件不承载）不算漂移，反向不检。
COMPONENT_AGENT_BODY_FILE = "agent-body.agent.md"
COMPONENT_SOUL_FILE = "soul.agent.md"
SECTION_HEADING_PREFIX = "## "


def component_role_definition_paths(source_root: str | Path, employee_id: str) -> dict[str, Path]:
    """组件化员工组件文件（编辑真源）：agent-body / soul / contract。"""
    normalized_employee_id = normalize_workspace_id(employee_id)
    component_root = Path(source_root) / SOURCE_AGENTS_COMPONENT_DIR / normalized_employee_id
    return {
        "agent-body": component_root / COMPONENT_AGENT_BODY_FILE,
        "soul": component_root / COMPONENT_SOUL_FILE,
        "contract": component_root / f"{normalized_employee_id}.contract.yaml",
    }


def _strip_frontmatter(text: str) -> str:
    """去掉 markdown 文件头部 `--- ... ---` frontmatter 块。"""
    if text.startswith("---\n"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def _split_sections(text: str) -> list[tuple[str, str]]:
    """按 `## ` 标题切分正文为 (标题行, 段落全文) 列表，跳过 frontmatter。

    段落全文从标题行开始到下一个 `## ` 标题前，strip 首尾空白后原样保留，
    用于与合成文件做子串匹配（组件段落必须逐字传导）。
    """
    body = _strip_frontmatter(text)
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith(SECTION_HEADING_PREFIX):
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line
            current_lines = [line]
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return sections


def _extract_frontmatter(text: str) -> str:
    """提取 markdown 头部 `--- ... ---` frontmatter 块原文（不含分隔行）。"""
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[4:end]


def _frontmatter_value(frontmatter: str, key: str) -> str | None:
    """从 frontmatter 提取单行字段值（去 YAML 双引号包裹）。"""
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            value = line[len(key) + 1 :].strip()
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value
    return None


def _contract_identity_value(text: str, key: str) -> str | None:
    """从 contract.yaml 提取 identity 段的单行字段值（两空格缩进，正则免 yaml 依赖）。"""
    match = re.search(rf"^  {re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    # 与 _frontmatter_value 同规则剥 YAML 双引号包裹（防带引号 vs 去引号误报漂移）
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value


def check_component_synthetic_sync(source_root: str | Path, employee_id: str) -> SourceKitValidationResult:
    """组件-合成文件同步校验：检测编辑真源（组件）到渲染真源（合成）的内容漂移。

    单向传导检查：
    1. agent-body.agent.md 的每个 `## ` 段落必须完整出现在合成文件 <id>.agent.md；
    2. soul.agent.md 的每个 `## ` 段落同样必须传导（如认知分层约束段）；
    3. contract.yaml identity 的 display_name / role 必须以反引号锚点出现在合成正文，
       合成 frontmatter 的 description 必须与 contract identity.description 一致。
    任一项不满足 → issue（组件修改未同步合成），提示重新合成/同步 <id>.agent.md。
    组件或合成文件缺失时按可检项继续：合成缺失直接报 missing（无法比对）。
    """
    normalized_employee_id = normalize_workspace_id(employee_id)
    components = component_role_definition_paths(source_root, normalized_employee_id)
    synthetic = role_definition_paths(source_root, normalized_employee_id)[1]
    issues: list[SourceKitValidationIssue] = []

    if not synthetic.is_file():
        issues.append(
            SourceKitValidationIssue(path=synthetic, message="missing synthetic agent file (component-synthetic sync)")
        )
        return SourceKitValidationResult(employee_id=normalized_employee_id, issues=tuple(issues))

    synthetic_text = synthetic.read_text(encoding="utf-8")
    synthetic_frontmatter = _extract_frontmatter(synthetic_text)

    for kind, path in (("agent-body", components["agent-body"]), ("soul", components["soul"])):
        if not path.is_file():
            continue
        component_text = path.read_text(encoding="utf-8")
        for title, section_text in _split_sections(component_text):
            if section_text not in synthetic_text:
                issues.append(
                    SourceKitValidationIssue(
                        path=synthetic,
                        message=(
                            f"component section not propagated to synthetic file ({kind} component {path.name}): {title} "
                            f"— 组件修改未同步合成，请重新合成/同步 {synthetic.name}"
                        ),
                    )
                )

    contract = components["contract"]
    if contract.is_file():
        contract_text = contract.read_text(encoding="utf-8")
        role = _contract_identity_value(contract_text, "role")
        display_name = _contract_identity_value(contract_text, "display_name")
        description = _contract_identity_value(contract_text, "description")
        if role and f"`{role}`" not in synthetic_text:
            issues.append(
                SourceKitValidationIssue(
                    path=synthetic,
                    message=f"contract identity role not propagated to synthetic file (contract {contract.name}): {role}",
                )
            )
        if display_name and f"你的工作名是 `{display_name}`" not in synthetic_text:
            issues.append(
                SourceKitValidationIssue(
                    path=synthetic,
                    message=f"contract identity display_name not propagated to synthetic file (contract {contract.name}): {display_name}",
                )
            )
        if description and _frontmatter_value(synthetic_frontmatter, "description") != description:
            issues.append(
                SourceKitValidationIssue(
                    path=synthetic,
                    message=f"contract identity description not propagated to synthetic frontmatter (contract {contract.name})",
                )
            )

    return SourceKitValidationResult(employee_id=normalized_employee_id, issues=tuple(issues))


def validate_employee_source_kit(source_root: str | Path, employee_id: str) -> SourceKitValidationResult:
    normalized_employee_id = normalize_workspace_id(employee_id)
    paths = source_kit_paths(source_root, normalized_employee_id)
    issues: list[SourceKitValidationIssue] = []

    for suffix, path in paths.items():
        if not path.is_file():
            issues.append(SourceKitValidationIssue(path=path, message="missing source kit file"))
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_CONSUMPTION_MARKERS:
            if marker in text:
                issues.append(SourceKitValidationIssue(path=path, message=f"contains consumption marker: {marker}"))
        for marker in FORBIDDEN_HOST_BINDING_MARKERS:
            if marker in text:
                issues.append(SourceKitValidationIssue(path=path, message=f"contains host binding marker: {marker}"))
        if suffix in COGNITIVE_LAYER_SUFFIXES:
            for required_marker in (
                "源侧认知层契约",
                "## 当前原则",
                "## 运行资产落点",
                "## 层契约",
                "TRICOMPANY_COGNITION_HOME",
            ):
                if required_marker not in text:
                    issues.append(SourceKitValidationIssue(path=path, message=f"missing required boundary marker: {required_marker}"))
        elif suffix == "agent":
            for required_marker in (
                "---",
                "name:",
                "description:",
                "tools:",
                "## 认知分层约束",
                "employee knowledge workspace",
                "runtime cognition state",
            ):
                if required_marker not in text:
                    issues.append(SourceKitValidationIssue(path=path, message=f"missing required agent marker: {required_marker}"))
        elif suffix == "soul":
            for required_marker in ("角色气质", "对话风格", "禁止退化"):
                if required_marker not in text:
                    issues.append(SourceKitValidationIssue(path=path, message=f"missing required soul marker: {required_marker}"))

    return SourceKitValidationResult(employee_id=normalized_employee_id, issues=tuple(issues))


def _render_source_kit(definition: EmployeeSourceKitDefinition) -> dict[str, str]:
    employee_id = normalize_workspace_id(definition.employee_id)
    binding_profile_reference = host_binding_profile_reference(employee_id)
    display_name_line = (
        f"在实际对话里，你的工作名是 `{definition.display_name}`。\n\n"
        if definition.display_name
        else "你尚未配置固定工作名；后续如确认稳定称呼，只把称呼声明写入身份层，具体事件写入宿主 employee workspace。\n\n"
    )
    soul_name = definition.display_name or "待命名"
    responsibilities = definition.responsibilities or (
        f"围绕 {definition.role_title} 的岗位职责完成判断、交付和协同。",
        "把稳定结论回写到对应 product、engineering、workflow、registry 或 training 真源。",
        "把阶段性上下文、协作连续性和社交连续性留在宿主 employee workspace 或 runtime cognition state。",
    )
    input_sources = definition.input_sources or (
        "CEO / 当前操作者的明确输入。",
        "CEOChiefOfStaff 的协调说明。",
        "TriCompany 源侧 docs、registry、workflow 与相关代码。",
        "TriMetaverse 中央层架构、workflow、registry 摘要与模块边界说明。",
    )
    voice_traits = definition.voice_traits or (
        "清楚、稳健、尊重事实边界。",
        "先说明来源和判断范围，再给出建议。",
        "不把计划、草案或 support-only 证据写成已完成事实。",
    )

    return {
        "agent": _render_agent(definition, display_name_line, responsibilities, input_sources, binding_profile_reference),
        "soul": _render_soul(definition, soul_name, voice_traits),
        "memory": _render_memory(definition, employee_id, binding_profile_reference),
        "colleagues": _render_colleagues(definition, employee_id, binding_profile_reference),
        "social": _render_social(definition, employee_id, binding_profile_reference),
    }


def _render_agent(
    definition: EmployeeSourceKitDefinition,
    display_name_line: str,
    responsibilities: Iterable[str],
    input_sources: Iterable[str],
    binding_profile_reference: str,
) -> str:
    return (
        "---\n"
        f"name: {definition.agent_name}\n"
        f"description: \"{_escape_yaml_double_quoted(definition.description)}\"\n"
        "tools: [read, search, edit]\n"
        "user-invocable: true\n"
        "---\n"
        f"你是 TriCompany 的 {definition.agent_name}，也就是{definition.role_title}。\n\n"
        f"{display_name_line}"
        f"你当前是源侧员工定义；当前 live 入口、support payload 与宿主阶段事实由 `{binding_profile_reference}` 承载，不在源侧五件套内固化。这不等于 TriMC 正式宿主切换。\n\n"
        "## 当前角色定位\n\n"
        f"- {definition.role_scope}\n"
        "- 你维护的是 TriCompany 源侧岗位 / 员工定义，不把当前 support runtime 记录写回源码层。\n"
        "- 你不替代 BusinessStrategy、CEOChiefOfStaff、CPO、CTO 或对应 registry 的正式裁决。\n\n"
        "## 认知分层约束\n\n"
        "- 你的身份气质由 soul 覆盖层定义。\n"
        "- 源侧 memory、colleagues、social 只定义认知层契约、写入边界和运行资产落点。\n"
        f"- 你的具体阶段记忆、工作关系和社交连续性由 employee knowledge workspace 与 runtime cognition state 承载；具体宿主绑定事实由 `{binding_profile_reference}` 承载。\n"
        "- 你应区分 role knowledge workspace 与 employee knowledge workspace：岗位知识用于沉淀可继承方法，员工知识用于保留当前员工实例的工作连续性。\n\n"
        "## 核心职责\n\n"
        f"{_numbered_lines(responsibilities)}\n"
        "## 当前输入来源\n\n"
        f"{_numbered_lines(input_sources)}\n"
        "## 输出原则\n\n"
        "- 先说明事实来源，再给出判断。\n"
        "- 明确区分已落地、草案中、待验证、待初始化。\n"
        "- 稳定结论回写源码真源；运行消费数据留在 support employee workspace 或 runtime cognition state。\n"
    )


def _render_soul(definition: EmployeeSourceKitDefinition, soul_name: str, voice_traits: Iterable[str]) -> str:
    return (
        f"# {definition.agent_name} 人格设定\n\n"
        f"名字：{soul_name}\n\n"
        "角色气质：\n\n"
        f"{_bullet_lines(voice_traits)}\n"
        "对话风格：\n\n"
        "- 中文、自然、直接。\n"
        "- 先给边界，再给判断，再给下一步。\n"
        "- 遇到事实不足时说待确认，不用气势替代证据。\n\n"
        "禁止退化：\n\n"
        "- 禁止把运行态消费记录写进源码侧认知层文件。\n"
        "- 禁止把当前 Copilot-host 阶段写成 TriMC 正式宿主切换。\n"
        "- 禁止把未验证能力写成已完成。\n"
    )


def _render_memory(
    definition: EmployeeSourceKitDefinition,
    employee_id: str,
    binding_profile_reference: str,
) -> str:
    return _render_layer_contract(
        title=f"# {definition.agent_name} 配套记忆",
        agent_name=definition.agent_name,
        employee_id=employee_id,
        binding_profile_reference=binding_profile_reference,
        layer_name="memory",
        layer_label="记忆",
        forbidden_examples="具体任务流水、称呼事件或运行同步摘录",
        stable_target="对应 product、engineering、workflow、registry、training 或 operating record 真源",
        contract_lines=(
            f"memory 层用于承载当前 {definition.agent_name} 员工实例的阶段性上下文、待复核判断和任务连续性。",
            "这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。",
            "稳定后可晋升到对应正式真源。",
        ),
    )


def _render_colleagues(
    definition: EmployeeSourceKitDefinition,
    employee_id: str,
    binding_profile_reference: str,
) -> str:
    return _render_layer_contract(
        title=f"# {definition.agent_name} 工作协作档案",
        agent_name=definition.agent_name,
        employee_id=employee_id,
        binding_profile_reference=binding_profile_reference,
        layer_name="colleagues",
        layer_label="工作协作档案",
        forbidden_examples="具体人物关系、称呼偏好或事项流水",
        stable_target="role workspace、workflow、agent 主档或对应 registry",
        contract_lines=(
            f"colleagues 层用于承载当前 {definition.agent_name} 员工实例在工作层面的协作关系、事项上下文和待确认信息。",
            "这些内容默认是 current-host consumption data，不属于源码侧岗位定义。",
            "可复用协作协议应晋升到 role workspace、workflow 或 agent 主档。",
        ),
    )


def _render_social(
    definition: EmployeeSourceKitDefinition,
    employee_id: str,
    binding_profile_reference: str,
) -> str:
    return _render_layer_contract(
        title=f"# {definition.agent_name} 社交档案",
        agent_name=definition.agent_name,
        employee_id=employee_id,
        binding_profile_reference=binding_profile_reference,
        layer_name="social",
        layer_label="社交档案",
        forbidden_examples="具体非正式称呼、互动偏好或轻社交流水",
        stable_target="colleagues、workflow 或正式协作规则",
        contract_lines=(
            f"social 层用于承载当前 {definition.agent_name} 员工实例的轻社交连续性、非正式互动偏好和闲聊层面的待确认信息。",
            "这些内容默认是 current-host consumption data，不属于源码侧岗位定义。",
            "如果某条社交偏好变成稳定协作要求，应经复核后晋升。",
        ),
    )


def _render_layer_contract(
    *,
    title: str,
    agent_name: str,
    employee_id: str,
    binding_profile_reference: str,
    layer_name: str,
    layer_label: str,
    forbidden_examples: str,
    stable_target: str,
    contract_lines: Iterable[str],
) -> str:
    return (
        f"{title}\n\n"
        f"本文件是 TriCompany 源侧认知层契约，只定义 {agent_name} {layer_name} 层的用途、写入边界和运行资产落点；不记录{forbidden_examples}。\n\n"
        "## 当前原则\n\n"
        f"- 源码侧只保留 {layer_label} 的通用规则和边界，不写运行消费数据。\n"
        f"- {agent_name} 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。\n"
        f"- 若某条内容经复核后成为稳定事实，应晋升到 {stable_target}。\n"
        f"- employee id 固定为 `{employee_id}`；该 id 只用于路径和 manifest，不代表 live 已启用。\n\n"
        "## 运行资产落点\n\n"
        f"- 宿主绑定说明：`{binding_profile_reference}`\n"
        "- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend\n\n"
        "## 层契约\n\n"
        f"{_bullet_lines(contract_lines)}"
    )


def _bullet_lines(lines: Iterable[str]) -> str:
    return "".join(f"- {line}\n" for line in lines)


def _numbered_lines(lines: Iterable[str]) -> str:
    return "".join(f"{index}. {line}\n" for index, line in enumerate(lines, start=1))


def _escape_yaml_double_quoted(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate TriCompany employee source five-piece kits.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a source-side employee five-piece kit.")
    generate_parser.add_argument("--source-root", default=".", help="Path to TriCompany source root. Defaults to current directory.")
    generate_parser.add_argument("--employee-id", required=True, help="Employee id used for source file names and support paths.")
    generate_parser.add_argument("--agent-name", required=True, help="Agent frontmatter name, e.g. ChiefProductOfficer.")
    generate_parser.add_argument("--role-title", required=True, help="Chinese role title used in body text.")
    generate_parser.add_argument("--description", required=True, help="Agent frontmatter description.")
    generate_parser.add_argument("--role-scope", required=True, help="One sentence describing this role's scope.")
    generate_parser.add_argument("--display-name", help="Optional employee working name.")
    generate_parser.add_argument("--responsibility", action="append", default=[], help="Core responsibility line. May be repeated.")
    generate_parser.add_argument("--input-source", action="append", default=[], help="Input source line. May be repeated.")
    generate_parser.add_argument("--voice-trait", action="append", default=[], help="Soul voice trait line. May be repeated.")
    generate_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing source kit files.")

    validate_parser = subparsers.add_parser("validate", help="Validate a source-side employee five-piece kit.")
    validate_parser.add_argument("--source-root", default=".", help="Path to TriCompany source root. Defaults to current directory.")
    validate_parser.add_argument("--employee-id", required=True, help="Employee id to validate.")

    sync_parser = subparsers.add_parser(
        "check-sync",
        help="Check component (agent-body/soul/contract) to synthetic (<id>.agent.md) propagation drift.",
    )
    sync_parser.add_argument("--source-root", default=".", help="Path to TriCompany source root. Defaults to current directory.")
    sync_parser.add_argument("--employee-id", required=True, help="Employee id to check component-synthetic sync.")

    args = parser.parse_args()
    if args.command == "generate":
        definition = EmployeeSourceKitDefinition(
            employee_id=args.employee_id,
            agent_name=args.agent_name,
            role_title=args.role_title,
            description=args.description,
            role_scope=args.role_scope,
            display_name=args.display_name,
            responsibilities=tuple(args.responsibility),
            input_sources=tuple(args.input_source),
            voice_traits=tuple(args.voice_trait),
        )
        result = generate_employee_source_kit(args.source_root, definition, overwrite=args.overwrite)
        validation = validate_employee_source_kit(args.source_root, result.employee_id)
        attribution = check_content_attribution(args.source_root, result.employee_id)
        for suffix, path in result.files.items():
            print(f"{suffix}={path.as_posix()}")
        if not validation.is_valid or not attribution.is_valid:
            for issue in list(validation.issues) + list(attribution.issues):
                print(f"validation_error={issue.path.as_posix()}: {issue.message}", file=sys.stderr)
            return 1
        print(f"validated_employee_source_kit={result.employee_id}")
        return 0

    if args.command == "check-sync":
        drift = check_component_synthetic_sync(args.source_root, args.employee_id)
        if not drift.is_valid:
            for issue in drift.issues:
                print(f"sync_drift={issue.path.as_posix()}: {issue.message}", file=sys.stderr)
            return 1
        print(f"component_synthetic_in_sync={drift.employee_id}")
        return 0

    validation = validate_employee_source_kit(args.source_root, args.employee_id)
    attribution = check_content_attribution(args.source_root, args.employee_id)
    combined_issues = list(validation.issues) + list(attribution.issues)
    if combined_issues:
        for issue in combined_issues:
            print(f"validation_error={issue.path.as_posix()}: {issue.message}", file=sys.stderr)
        return 1
    print(f"validated_employee_source_kit={validation.employee_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())