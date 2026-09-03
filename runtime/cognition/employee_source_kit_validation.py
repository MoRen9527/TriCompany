from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_source_kit import (
    FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS,
    EmployeeSourceKitDefinition,
    _render_cognitive_stub,
    _split_sections,
    check_component_synthetic_sync,
    check_content_attribution,
    component_role_definition_paths,
    generate_employee_source_kit,
    host_binding_profile_reference,
    iter_component_employee_ids,
    role_definition_paths,
    validate_employee_source_kit,
)


class EmployeeSourceKitValidation(unittest.TestCase):
    def test_generates_and_validates_source_five_piece_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            generated = generate_employee_source_kit(source_root, _sample_definition())

            self.assertEqual(set(generated.files), {"agent", "soul", "memory", "colleagues", "social"})
            for path in generated.files.values():
                self.assertTrue(path.is_file())

            validation = validate_employee_source_kit(source_root, "customer-success-officer")
            # LG-025 M0e 硬线（D-15 联审裁）：generate 产物=纯模板桩，治理门必须拒收
            # （禁空心合规/禁模板桩）——本测试翻转为断言桩被检出（集成语义不变：
            # validate 能识别 generate 输出并逐条报 template-stub/empty-section）。
            self.assertFalse(validation.is_valid, [issue.message for issue in validation.issues])
            stub_or_empty = [
                issue.message
                for issue in validation.issues
                if "template-stub-section" in issue.message or "empty-section" in issue.message
            ]
            self.assertTrue(stub_or_empty, [issue.message for issue in validation.issues])

            agent_text = generated.files["agent"].read_text(encoding="utf-8")
            memory_text = generated.files["memory"].read_text(encoding="utf-8")
            self.assertIn("源侧认知层契约", memory_text)
            self.assertIn(host_binding_profile_reference("customer-success-officer"), memory_text)
            self.assertIn("TRICOMPANY_COGNITION_HOME", memory_text)
            self.assertNotIn("TriCompany-copilot-host-assets/knowledge/employees/customer-success-officer", memory_text)
            self.assertNotIn("live 状态为", agent_text)

    def test_refuses_to_overwrite_existing_source_kit_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            generate_employee_source_kit(source_root, _sample_definition())

            with self.assertRaises(FileExistsError):
                generate_employee_source_kit(source_root, _sample_definition())

    def test_detects_consumption_markers_in_source_cognitive_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            generated = generate_employee_source_kit(source_root, _sample_definition())
            memory_path = generated.files["memory"]
            memory_path.write_text(memory_path.read_text(encoding="utf-8") + "\n## 阶段记忆记录\n", encoding="utf-8")

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            self.assertFalse(validation.is_valid)
            self.assertTrue(any("contains consumption marker" in issue.message for issue in validation.issues))

    def test_detects_host_binding_support_path_in_source_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            generated = generate_employee_source_kit(source_root, _sample_definition())
            memory_path = generated.files["memory"]
            memory_path.write_text(
                memory_path.read_text(encoding="utf-8")
                + "\n- 当前 support 员工记录：`TriCompany-copilot-host-assets/knowledge/employees/customer-success-officer/wiki/employee-consumption-records.md`\n",
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            self.assertFalse(validation.is_valid)
            self.assertTrue(
                any("contains host binding marker: TriCompany-copilot-host-assets/knowledge/employees/" in issue.message for issue in validation.issues)
            )

    def test_detects_host_binding_live_entry_sentence_in_source_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            generated = generate_employee_source_kit(source_root, _sample_definition())
            agent_path = generated.files["agent"]
            agent_path.write_text(
                agent_path.read_text(encoding="utf-8")
                + "\n当前 live 入口位于 `TriMetaverse/.github/agents/customer-success-officer.agent.md`。\n",
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            self.assertFalse(validation.is_valid)
            self.assertTrue(any("contains host binding marker: 当前 live 入口位于" in issue.message for issue in validation.issues))

    def test_detects_missing_support_runtime_boundary_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            generated = generate_employee_source_kit(source_root, _sample_definition())
            social_path = generated.files["social"]
            social_path.write_text(
                social_path.read_text(encoding="utf-8").replace("TRICOMPANY_COGNITION_HOME", "TRICOMPANY_RUNTIME_HOME"),
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            self.assertFalse(validation.is_valid)
            self.assertTrue(any("TRICOMPANY_COGNITION_HOME" in issue.message for issue in validation.issues))


# ── 内容归属校验（FADE 加固 B 项 / fade-quality-lessons 案例 2）──────────────


def _write_role_definition(source_root: Path, employee_id: str, content: str, *, synthetic: bool = False) -> Path:
    """写入组件化角色定义文件（agent-body 组件或 <id>.agent.md 合成文件）。"""
    component_root = source_root / "source-agents" / employee_id
    component_root.mkdir(parents=True, exist_ok=True)
    path = component_root / ("agent-body.agent.md" if not synthetic else f"{employee_id}.agent.md")
    path.write_text(content, encoding="utf-8")
    return path


class ContentAttributionValidation(unittest.TestCase):
    def test_role_definition_paths_resolve_component_and_synthetic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            paths = role_definition_paths(source_root, "customer-success-officer")
            self.assertEqual(len(paths), 2)
            self.assertTrue(paths[0].as_posix().endswith("source-agents/customer-success-officer/agent-body.agent.md"))
            self.assertTrue(paths[1].as_posix().endswith("source-agents/customer-success-officer/customer-success-officer.agent.md"))

    def test_clean_role_definition_passes(self) -> None:
        """正例：角色定义纯净（只含角色职责）→ 无内容归属问题。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            _write_role_definition(
                source_root,
                "customer-success-officer",
                "---\nname: CustomerSuccessOfficer\n---\n"
                "## 当前角色定位\n\n- 你负责把试点客户反馈整理成可复核的产品、交付和运营输入。\n"
                "- 你不替代 CTO 做技术裁决，不替代 CPO 做产品取舍。\n",
            )
            _write_role_definition(
                source_root,
                "customer-success-officer",
                "---\nname: CustomerSuccessOfficer\n---\n"
                "## 当前角色定位\n\n- 你负责把试点客户反馈整理成可复核的产品、交付和运营输入。\n",
                synthetic=True,
            )

            attribution = check_content_attribution(source_root, "customer-success-officer")

            self.assertTrue(attribution.is_valid, [issue.message for issue in attribution.issues])

    def test_template_discipline_sentence_in_component_is_error(self) -> None:
        """反例：源侧维护句模板误植进 agent-body 组件 → error。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            _write_role_definition(
                source_root,
                "customer-success-officer",
                "---\nname: CustomerSuccessOfficer\n---\n"
                "## 当前角色定位\n\n"
                "- 你负责把试点客户反馈整理成可复核的产品、交付和运营输入。\n"
                "- 你维护的是 TriCompany 源侧岗位 / 员工定义，不把当前 support runtime 记录写回源码层。\n",
            )

            attribution = check_content_attribution(source_root, "customer-success-officer")

            self.assertFalse(attribution.is_valid)
            self.assertTrue(
                any(
                    "template discipline sentence" in issue.message
                    and "你维护的是 TriCompany 源侧岗位 / 员工定义" in issue.message
                    and "agent-body.agent.md" in issue.path.as_posix()
                    for issue in attribution.issues
                ),
                [issue.message for issue in attribution.issues],
            )

    def test_template_discipline_sentence_in_synthetic_is_error(self) -> None:
        """反例：soul 模板句误植进合成文件 <id>.agent.md → error。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            _write_role_definition(
                source_root,
                "customer-success-officer",
                "---\nname: CustomerSuccessOfficer\n---\n"
                "## 当前角色定位\n\n- 你负责客户成功运营。\n"
                "## 对话风格\n\n- 中文、自然、直接。\n",
                synthetic=True,
            )

            attribution = check_content_attribution(source_root, "customer-success-officer")

            self.assertFalse(attribution.is_valid)
            self.assertTrue(
                any(
                    "template discipline sentence" in issue.message
                    and "中文、自然、直接" in issue.message
                    and "customer-success-officer.agent.md" in issue.path.as_posix()
                    for issue in attribution.issues
                ),
                [issue.message for issue in attribution.issues],
            )

    def test_missing_role_definition_files_are_skipped(self) -> None:
        """无组件化文件（纯模板员工）→ 不报错（文件缺失跳过，非误植）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            attribution = check_content_attribution(source_root, "customer-success-officer")
            self.assertTrue(attribution.is_valid, [issue.message for issue in attribution.issues])

    def test_allowlist_is_role_agnostic_and_distinct_from_role_rewrites(self) -> None:
        """白名单约束：误植句清单必须非空；角色化改写版（如"不把宿主 binding 或
        试运行上岗状态写成 TriMC 正式宿主切换"）不属于清单原文（防误伤现役文件）。"""
        self.assertGreaterEqual(len(FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS), 5)
        self.assertNotIn(
            "不把宿主 binding 或试运行上岗状态写成 TriMC 正式宿主切换",
            FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS,
        )
        self.assertNotIn("你不替代 BusinessStrategy、CEOChiefOfStaff、CPO、CTO 或对应 registry 的正式裁决", FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS)


# ── 组件-合成文件同步校验（FADE 加固 D 项 / fade-quality-lessons 建议 3）────


def _write_component_fixture(
    source_root: Path,
    employee_id: str,
    *,
    synthetic: str | None = None,
    agent_body: str | None = None,
    soul: str | None = None,
    contract: str | None = None,
) -> dict[str, Path]:
    """写入组件化员工 fixture（组件 + 合成文件），返回写入路径。

    默认 fixture：合成文件 = agent-body 段落 + soul 段落拼接 + frontmatter，
    contract identity 与合成一致——各测试按需覆盖任一文件制造漂移。
    """
    component_root = source_root / "source-agents" / employee_id
    component_root.mkdir(parents=True, exist_ok=True)
    synthetic_path = component_root / f"{employee_id}.agent.md"
    body_path = component_root / "agent-body.agent.md"
    soul_path = component_root / "soul.agent.md"
    contract_path = component_root / f"{employee_id}.contract.yaml"

    default_body = (
        "---\n"
        f"name: CustomerSuccessOfficer\n"
        'description: "客户成功负责人，负责把试点客户反馈整理成可复核的输入。"\n'
        "tools: [read, search, edit]\n"
        "user-invocable: true\n"
        "---\n"
        "## 当前角色定位\n\n"
        "- 你负责把试点客户反馈整理成可复核的产品、交付和运营输入。\n"
        "- 你不替代 CTO 做技术裁决，不替代 CPO 做产品取舍。\n"
        "## 使命\n\n"
        "把试点客户反馈收敛成可复核、可执行的公司输入。\n"
    )
    default_soul = (
        "## 认知分层约束\n\n"
        "- 你的身份气质由 soul 覆盖层定义。\n"
        "- 源侧 memory、colleagues、social 只定义认知层契约、写入边界和运行资产落点。\n"
    )
    default_contract = (
        "# Agent Contract v3\n"
        "contract:\n"
        '  version: "3.0"\n'
        "  type: agent-contract\n"
        f"  agent_id: {employee_id}\n"
        "  family: Role\n"
        "identity:\n"
        "  display_name: 小成\n"
        "  role: CustomerSuccessOfficer\n"
        '  description: "客户成功负责人，负责把试点客户反馈整理成可复核的输入。"\n'
        "  user_invocable: true\n"
    )
    default_synthetic = (
        "---\n"
        "name: CustomerSuccessOfficer\n"
        'description: "客户成功负责人，负责把试点客户反馈整理成可复核的输入。"\n'
        "tools: [read, search, edit]\n"
        "user-invocable: true\n"
        "---\n"
        "你是 TriCompany 当前阶段已上岗的 `CustomerSuccessOfficer`，也就是赛博公司的客户成功负责人。\n\n"
        "在实际对话里，你的工作名是 `小成`。\n\n"
        "## 当前角色定位\n\n"
        "- 你负责把试点客户反馈整理成可复核的产品、交付和运营输入。\n"
        "- 你不替代 CTO 做技术裁决，不替代 CPO 做产品取舍。\n"
        "## 认知分层约束\n\n"
        "- 你的身份气质由 soul 覆盖层定义。\n"
        "- 源侧 memory、colleagues、social 只定义认知层契约、写入边界和运行资产落点。\n"
        "## 使命\n\n"
        "把试点客户反馈收敛成可复核、可执行的公司输入。\n"
    )

    if agent_body is not None:
        body_path.write_text(agent_body, encoding="utf-8")
    else:
        body_path.write_text(default_body, encoding="utf-8")
    if soul is not None:
        soul_path.write_text(soul, encoding="utf-8")
    else:
        soul_path.write_text(default_soul, encoding="utf-8")
    if contract is not None:
        contract_path.write_text(contract, encoding="utf-8")
    else:
        contract_path.write_text(default_contract, encoding="utf-8")
    if synthetic is not None:
        synthetic_path.write_text(synthetic, encoding="utf-8")
    else:
        synthetic_path.write_text(default_synthetic, encoding="utf-8")

    return {
        "synthetic": synthetic_path,
        "agent-body": body_path,
        "soul": soul_path,
        "contract": contract_path,
    }


class ComponentSyntheticSyncValidation(unittest.TestCase):
    def test_component_paths_resolve_components_and_contract(self) -> None:
        """组件路径解析：agent-body / soul / contract 三组件落位。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            paths = component_role_definition_paths(source_root, "customer-success-officer")
            self.assertEqual(set(paths), {"agent-body", "soul", "contract"})
            self.assertTrue(paths["agent-body"].as_posix().endswith("source-agents/customer-success-officer/agent-body.agent.md"))
            self.assertTrue(paths["soul"].as_posix().endswith("source-agents/customer-success-officer/soul.agent.md"))
            self.assertTrue(paths["contract"].as_posix().endswith("source-agents/customer-success-officer/customer-success-officer.contract.yaml"))

    def test_fully_synced_component_and_synthetic_passes(self) -> None:
        """正例：组件全部传导到合成（agent-body 段落 + soul 段落 + contract 身份一致）→ 无漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            _write_component_fixture(source_root, "customer-success-officer")

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertTrue(drift.is_valid, [issue.message for issue in drift.issues])

    def test_component_edit_without_synthetic_sync_is_drift(self) -> None:
        """反例（核心）：agent-body 组件新增段落未同步合成 → 检出漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            body = fixture["agent-body"].read_text(encoding="utf-8")
            fixture["agent-body"].write_text(
                body + "## 新增岗位段落\n\n- 这是一条只在组件里新增、未同步合成的职责。\n",
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any(
                    "component section not propagated to synthetic file" in issue.message
                    and "新增岗位段落" in issue.message
                    and "agent-body" in issue.message
                    for issue in drift.issues
                ),
                [issue.message for issue in drift.issues],
            )

    def test_component_edit_of_existing_section_without_sync_is_drift(self) -> None:
        """反例：agent-body 既有段落内容被改写未同步合成 → 检出漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            body = fixture["agent-body"].read_text(encoding="utf-8")
            fixture["agent-body"].write_text(
                body.replace(
                    "你不替代 CTO 做技术裁决，不替代 CPO 做产品取舍。",
                    "你不替代 CTO 做技术裁决，不替代 CPO 做产品取舍，不替代小柯做测试判断。",
                ),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any("component section not propagated to synthetic file" in issue.message for issue in drift.issues),
                [issue.message for issue in drift.issues],
            )

    def test_soul_component_section_missing_in_synthetic_is_drift(self) -> None:
        """反例：soul 组件段落（认知分层约束）未传导到合成 → 检出漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            synthetic = fixture["synthetic"].read_text(encoding="utf-8")
            fixture["synthetic"].write_text(
                synthetic.replace("## 认知分层约束\n\n- 你的身份气质由 soul 覆盖层定义。\n", ""),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any("soul component" in issue.message and "认知分层约束" in issue.message for issue in drift.issues),
                [issue.message for issue in drift.issues],
            )

    def test_contract_role_change_without_synthetic_sync_is_drift(self) -> None:
        """反例：contract identity.role 变更未同步合成正文 → 检出漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            contract = fixture["contract"].read_text(encoding="utf-8")
            fixture["contract"].write_text(
                contract.replace("role: CustomerSuccessOfficer", "role: CustomerExperienceOfficer"),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any("contract identity role not propagated" in issue.message for issue in drift.issues),
                [issue.message for issue in drift.issues],
            )

    def test_contract_description_semantics_differ_from_frontmatter_is_not_drift(self) -> None:
        """正例（语义修正）：现役约定 contract identity.description=职责长句、合成
        frontmatter description="适用场景："清单，两者本不同——不要求相等，非空即通过。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            contract = fixture["contract"].read_text(encoding="utf-8")
            fixture["contract"].write_text(
                contract.replace(
                    'description: "客户成功负责人，负责把试点客户反馈整理成可复核的输入。"',
                    'description: "客户成功负责人。负责把试点客户反馈整理成可复核的输入，并跟踪续费风险。"',
                ),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertTrue(drift.is_valid, [issue.message for issue in drift.issues])

    def test_contract_description_present_but_frontmatter_description_empty_is_error(self) -> None:
        """反例：contract 声明 description 但合成 frontmatter description 缺失 → 检出漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            synthetic = fixture["synthetic"].read_text(encoding="utf-8")
            fixture["synthetic"].write_text(
                synthetic.replace('description: "客户成功负责人，负责把试点客户反馈整理成可复核的输入。"', "description: "),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any("synthetic frontmatter description empty" in issue.message for issue in drift.issues),
                [issue.message for issue in drift.issues],
            )

    def test_multiline_contract_description_is_parsed_without_truncation(self) -> None:
        """正例（多行 YAML）：contract identity.description 用 YAML 续行（缩进折行）时，
        yaml.safe_load 完整解析，不因单行正则截断而漏检/误报。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            contract = fixture["contract"].read_text(encoding="utf-8")
            fixture["contract"].write_text(
                contract.replace(
                    '  description: "客户成功负责人，负责把试点客户反馈整理成可复核的输入。"\n',
                    "  description: 客户成功负责人。负责把试点客户反馈整理成可复核的输入，并跟踪\n"
                    "    续费风险与流失预警。\n",
                ),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertTrue(drift.is_valid, [issue.message for issue in drift.issues])

    def test_display_name_placeholder_is_skipped_when_contract_says_pending(self) -> None:
        """正例（待命名占位特判）：contract display_name=待命名 且合成无工作名锚点 → 不构成漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            contract = fixture["contract"].read_text(encoding="utf-8")
            fixture["contract"].write_text(
                contract.replace("display_name: 小成", "display_name: 待命名"),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertTrue(drift.is_valid, [issue.message for issue in drift.issues])

    def test_display_name_anchor_still_checked_when_not_placeholder(self) -> None:
        """反例（待命名特判不误伤）：非占位 display_name 未传导锚点 → 仍检出漂移。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            synthetic = fixture["synthetic"].read_text(encoding="utf-8")
            fixture["synthetic"].write_text(
                synthetic.replace("在实际对话里，你的工作名是 `小成`。", "在实际对话里，你的工作名是 `老成`。"),
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any("contract identity display_name not propagated" in issue.message for issue in drift.issues),
                [issue.message for issue in drift.issues],
            )

    def test_missing_synthetic_file_is_drift(self) -> None:
        """反例：合成文件缺失（组件已改、未合成）→ 检出 missing。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            fixture["synthetic"].unlink()

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any("missing synthetic agent file" in issue.message for issue in drift.issues),
                [issue.message for issue in drift.issues],
            )

    def test_synthetic_only_sections_are_not_drift(self) -> None:
        """合成文件独有的模板固定段落（渲染补充、组件不承载）→ 不构成漂移（反向不检）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_component_fixture(source_root, "customer-success-officer")
            synthetic = fixture["synthetic"].read_text(encoding="utf-8")
            fixture["synthetic"].write_text(
                synthetic + "## 输出原则\n\n- 先说明事实来源，再给出判断。\n",
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "customer-success-officer")

            self.assertTrue(drift.is_valid, [issue.message for issue in drift.issues])


class CognitiveLayerGateBoundaryValidation(unittest.TestCase):
    """LG-025 M0e validator 四断言边界补测（COS 派工单、经 CTO 认领 2026-09-03）。

    语义基准（CTO 残项③裁示）：generate 产物（模板桩）直 validate 必拒=设计行为
    非缺陷，V2 门=防桩上岗的核心治理价值；流程正解=generate→graft→validate 三序流。
    本组用例按三序流构造：generate 为基底、graft 目标件为目标内容、只对目标件的
    gate issue 断言（其余件的桩报告不在断言面内）。
    """

    # 精确边界行常量：V1 双线=非标题非空行 ≥2 且 strip 合计 ≥50 字符
    LINE_25 = "过" * 25
    LINE_24 = "过" * 24

    def _generated_component(self, source_root: Path) -> Path:
        """三序流第一序：generate 全套（模板桩基底）。"""
        generate_employee_source_kit(source_root, _sample_definition())
        return source_root / "source-agents" / "customer-success-officer"

    def _gate_text(self, principle: list[str], contract: list[str]) -> str:
        """构造过 V1/V4 门的三节 memory 源侧件（当前原则/层契约体可定制）。"""
        lines = [
            "<!-- 源侧认知层契约：M0e 边界补测 fixture。 -->",
            "## 当前原则",
            *principle,
            "## 运行资产落点",
            "认知层资产落点说明：TRICOMPANY_COGNITION_HOME 由当前 runtime cognition backend 承载与巡检。",
            "运行期读写以 employee knowledge workspace 为边界，source 侧只持契约与边界声明。",
            "## 层契约",
            *contract,
        ]
        return "\n".join(lines)

    def _memory_gate_messages(self, issues: list) -> list[str]:
        return [i.message for i in issues if i.path.name == "memory.agent.md"]

    # ── ① V1 阈值边界 ──

    def test_v1_exact_threshold_passes(self) -> None:
        """过线样本：恰 2 行且合计恰 50 字符（双线均踩线不越）→ 不报 empty-section。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            comp = self._generated_component(source_root)
            body = [self.LINE_25, self.LINE_25]
            self.assertEqual(sum(len(line) for line in body), 50)  # 边界自检
            (comp / "memory.agent.md").write_text(
                self._gate_text(principle=body, contract=[self.LINE_25, self.LINE_25]),
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            empties = [m for m in self._memory_gate_messages(validation.issues) if "empty-section" in m]
            self.assertEqual(empties, [], empties)

    def test_v1_off_by_one_on_both_axes_fails(self) -> None:
        """差一线 fail 样本：行线（1 行）与字符线（2 行恰 49 字）各触发 empty-section。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            comp = self._generated_component(source_root)
            # 行线：单行（哪怕超 50 字符）< 2 行下限
            (comp / "memory.agent.md").write_text(
                self._gate_text(principle=["单行长文本" + self.LINE_25], contract=[self.LINE_25, self.LINE_25]),
                encoding="utf-8",
            )
            validation = validate_employee_source_kit(source_root, "customer-success-officer")
            empties = [m for m in self._memory_gate_messages(validation.issues) if "empty-section" in m]
            self.assertTrue(any("## 当前原则" in m for m in empties), empties)

            # 字符线：2 行合计 49 字（差一线）→ 仍 fail
            comp2_dir = source_root / "source-agents" / "customer-success-officer"
            body = [self.LINE_25, self.LINE_24]
            self.assertEqual(sum(len(line) for line in body), 49)  # 边界自检
            (comp2_dir / "memory.agent.md").write_text(
                self._gate_text(principle=body, contract=[self.LINE_25, self.LINE_25]),
                encoding="utf-8",
            )
            validation2 = validate_employee_source_kit(source_root, "customer-success-officer")
            empties2 = [m for m in self._memory_gate_messages(validation2.issues) if "empty-section" in m]
            self.assertTrue(any("## 当前原则" in m for m in empties2), empties2)

    # ── ② V2 模板桩双分支 ──

    def test_v2_byte_identical_stub_is_rejected(self) -> None:
        """分支一（逐字节）：generate 产物（=重渲桩原样）直 validate → 三节全报 template-stub。

        正向断言面（语义基准）：generate 直 validate 必拒=设计行为，V2 门正确工作。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            self._generated_component(source_root)

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            stubs = [
                i.message
                for i in validation.issues
                if i.path.name == "memory.agent.md" and "template-stub-section" in i.message
            ]
            self.assertEqual(len(stubs), 3, stubs)  # 三节各一条

    def test_v2_stub_line_set_reordering_is_rejected(self) -> None:
        """分支二（行集包含）：当前原则节体取桩行倒序+重复一行——非逐字节相同但行全∈桩常量行集 → 仍报。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            comp = self._generated_component(source_root)
            stub = (comp / "memory.agent.md").read_text(encoding="utf-8")
            principle_stub = dict(_split_sections(stub))["## 当前原则"]
            stub_body = [
                line.strip()
                for line in principle_stub.splitlines()
                if line.strip() and not line.startswith("## ")
            ]
            variant = list(reversed(stub_body)) + [stub_body[0]]  # 行集不变、序列倒置+重复=非逐字节
            self.assertNotEqual(variant, stub_body)  # 非逐字节前置自检
            (comp / "memory.agent.md").write_text(
                self._gate_text(principle=variant, contract=[self.LINE_25, self.LINE_25]),
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            stubs = [
                m
                for m in self._memory_gate_messages(validation.issues)
                if "template-stub-section" in m
            ]
            self.assertTrue(
                len(stubs) >= 1 and any("## 当前原则" in m for m in stubs),
                stubs,
            )

    # ── ③ V3 旧代语义保真 ──

    def test_v3_legacy_unique_line_reported_as_missing(self) -> None:
        """tempdir 旧代件（三候选第三项）含三节：未 containment 的行报 legacy-line-missing。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            comp = self._generated_component(source_root)
            keep_a = "组长信箱督办岗以信件状态机门禁为唯一流转准绳，投递与升级全程留痕。"
            keep_b = "行为反馈与岗位判断按周沉淀入册，历史叙事冻结、技术真源可修留痕。"
            (comp / "memory.agent.md").write_text(
                self._gate_text(principle=[keep_a, self.LINE_25], contract=[keep_b, self.LINE_25]),
                encoding="utf-8",
            )
            legacy_root = source_root / ".github" / "source-agents" / "customer-success-officer"
            legacy_root.mkdir(parents=True)
            unique_line = "旧代独有保真行必须被核对是否存在缺失遗漏。"
            legacy_asset = "认知层资产落点说明：TRICOMPANY_COGNITION_HOME 由当前 runtime cognition backend 承载与巡检。"
            (legacy_root / "customer-success-officer.memory.md").write_text(
                "\n".join(
                    [
                        "## 当前原则",
                        keep_a,
                        unique_line,
                        "## 运行资产落点",
                        legacy_asset,
                        "## 层契约",
                        keep_b,
                    ]
                ),
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            missing = [i.message for i in validation.issues if "legacy-line-missing" in i.message]
            self.assertEqual(len(missing), 1, missing)
            self.assertIn(unique_line[:20], missing[0])

    # ── ④ 合并件堵截去重 ──

    def test_merged_file_double_key_gate_runs_once(self) -> None:
        """colleagues/social 双键同指一合并件：同一检查集按路径去重只跑一次（桩报 3 节而非 6）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            comp = self._generated_component(source_root)
            merged = comp / "colleagues-social.agent.md"
            merged.write_text((comp / "colleagues.agent.md").read_text(encoding="utf-8"), encoding="utf-8")
            (comp / "colleagues.agent.md").unlink()
            (comp / "social.agent.md").unlink()
            (comp / "customer-success-officer.contract.yaml").write_text(
                "identity:\n"
                "  role: CustomerSuccessOfficer\n"
                "paths:\n"
                "  colleagues: customer-success-officer/colleagues-social.agent.md\n"
                "  social: customer-success-officer/colleagues-social.agent.md\n",
                encoding="utf-8",
            )

            validation = validate_employee_source_kit(source_root, "customer-success-officer")

            stubs = [
                i.message
                for i in validation.issues
                if i.path == merged and "template-stub-section" in i.message
            ]
            self.assertEqual(len(stubs), 3, stubs)  # 去重正确=3；双报=6


class SyntheticPathOverrideAndEnumerationValidation(unittest.TestCase):
    """FADE-LEFTOVER-20260821-001 1b/1c（CTO 裁决）覆盖：

    - business-strategy（registry 类单文件区）的合成文件不在组件目录，经
      SYNTHETIC_PATH_OVERRIDES 映射到 registries/business-strategy.agent.md，
      该真漂移面从此被 D 校验保护；
    - 批量枚举只选含组件结构（agent-body.agent.md 或 *.contract.yaml）的目录，
      registries 单文件区与无组件目录排除（修批量误报 missing synthetic）。
    """

    def test_role_definition_paths_override_business_strategy_to_registries(self) -> None:
        """映射例外：business-strategy 合成文件路径落 registries 单文件区。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            body_path, synthetic_path = role_definition_paths(source_root, "business-strategy")
            self.assertTrue(body_path.as_posix().endswith("source-agents/business-strategy/agent-body.agent.md"))
            self.assertTrue(synthetic_path.as_posix().endswith("source-agents/registries/business-strategy.agent.md"))

    def test_sync_drift_detected_against_registries_synthetic_via_override(self) -> None:
        """映射例外生效：组件改动未同步 registries 版合成 → 漂移指向 registries 路径。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_business_strategy_fixture(source_root)

            drift = check_component_synthetic_sync(source_root, "business-strategy")

            self.assertTrue(drift.is_valid, [issue.message for issue in drift.issues])

            body = fixture["agent-body"].read_text(encoding="utf-8")
            fixture["agent-body"].write_text(
                body + "2. 把商业问题映射到正确模块并声明 TriTest 仅作兼容资料入口。\n",
                encoding="utf-8",
            )

            drift = check_component_synthetic_sync(source_root, "business-strategy")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any(
                    "registries/business-strategy.agent.md" in issue.path.as_posix()
                    and "component section not propagated" in issue.message
                    for issue in drift.issues
                ),
                [(issue.path.as_posix(), issue.message) for issue in drift.issues],
            )

    def test_missing_registries_synthetic_reported_via_override(self) -> None:
        """registries 版合成缺失 → missing 报告路径为映射后的 registries 路径。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            fixture = _write_business_strategy_fixture(source_root)
            fixture["synthetic"].unlink()

            drift = check_component_synthetic_sync(source_root, "business-strategy")

            self.assertFalse(drift.is_valid)
            self.assertTrue(
                any(
                    "missing synthetic" in issue.message
                    and "registries/business-strategy.agent.md" in issue.path.as_posix()
                    for issue in drift.issues
                ),
                [(issue.path.as_posix(), issue.message) for issue in drift.issues],
            )

    def test_iter_component_employee_ids_excludes_registries_and_non_component_dirs(self) -> None:
        """批量枚举：仅组件目录入选；registries 单文件区 / 无组件目录排除。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            agents_dir = source_root / "source-agents"
            cso_dir = agents_dir / "customer-success-officer"
            cso_dir.mkdir(parents=True)
            (cso_dir / "customer-success-officer.contract.yaml").write_text("identity: {}\n", encoding="utf-8")
            bs_dir = agents_dir / "business-strategy"
            bs_dir.mkdir()
            (bs_dir / "agent-body.agent.md").write_text("## 核心职责\n", encoding="utf-8")
            registries_dir = agents_dir / "registries"
            registries_dir.mkdir()
            (registries_dir / "business-strategy.agent.md").write_text("单文件区条目\n", encoding="utf-8")
            (agents_dir / "drafts").mkdir()

            employee_ids = iter_component_employee_ids(source_root)

            self.assertEqual(employee_ids, ["business-strategy", "customer-success-officer"])


def _write_business_strategy_fixture(source_root: Path) -> dict[str, Path]:
    """registry 类单文件区 fixture：组件目录（agent-body + contract）+ registries 合成。"""
    component_dir = source_root / "source-agents" / "business-strategy"
    registries_dir = source_root / "source-agents" / "registries"
    component_dir.mkdir(parents=True)
    registries_dir.mkdir(parents=True)
    body_path = component_dir / "agent-body.agent.md"
    contract_path = component_dir / "business-strategy.contract.yaml"
    synthetic_path = registries_dir / "business-strategy.agent.md"
    body_path.write_text("## 核心职责\n\n1. 解释长期商业模式与当前经营实验。\n", encoding="utf-8")
    contract_path.write_text(
        "identity:\n"
        "  role: BusinessStrategy\n"
        "  display_name: BusinessStrategy\n"
        "  description: 适用场景：总商业模式、模块边界。\n",
        encoding="utf-8",
    )
    synthetic_path.write_text(
        "---\n"
        "name: BusinessStrategy\n"
        'description: "适用场景：总商业模式、模块边界。"\n'
        "---\n"
        "你是 TriMetaverse 的中央 `Strategy Registry`。\n\n"
        "## 核心职责\n\n"
        "1. 解释长期商业模式与当前经营实验。\n",
        encoding="utf-8",
    )
    return {"agent-body": body_path, "contract": contract_path, "synthetic": synthetic_path}


def _sample_definition() -> EmployeeSourceKitDefinition:
    return EmployeeSourceKitDefinition(
        employee_id="customer-success-officer",
        agent_name="CustomerSuccessOfficer",
        role_title="客户成功负责人",
        description="适用场景：客户成功、试点跟进、用户反馈收集、续费风险识别。",
        role_scope="你负责把试点客户反馈整理成可复核的产品、交付和运营输入。",
        display_name="小成",
        responsibilities=(
            "跟进试点客户反馈并区分产品问题、交付问题和使用教育问题。",
            "把稳定客户事实回写到对应产品、运营或 registry 真源。",
        ),
        input_sources=(
            "CEO / 当前操作者的客户反馈。",
            "CPO、CTO 和 CEOChiefOfStaff 的交接说明。",
        ),
        voice_traits=(
            "耐心、具体、尊重客户原话。",
            "先区分事实、判断和待确认问题。",
        ),
    )


if __name__ == "__main__":
    unittest.main()