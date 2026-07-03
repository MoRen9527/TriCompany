from __future__ import annotations

import argparse
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
        for suffix, path in result.files.items():
            print(f"{suffix}={path.as_posix()}")
        if not validation.is_valid:
            for issue in validation.issues:
                print(f"validation_error={issue.path.as_posix()}: {issue.message}", file=sys.stderr)
            return 1
        print(f"validated_employee_source_kit={result.employee_id}")
        return 0

    validation = validate_employee_source_kit(args.source_root, args.employee_id)
    if not validation.is_valid:
        for issue in validation.issues:
            print(f"validation_error={issue.path.as_posix()}: {issue.message}", file=sys.stderr)
        return 1
    print(f"validated_employee_source_kit={validation.employee_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())