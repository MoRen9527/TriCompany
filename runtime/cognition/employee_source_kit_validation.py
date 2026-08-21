from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_source_kit import (
    FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS,
    EmployeeSourceKitDefinition,
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
            self.assertTrue(validation.is_valid, [issue.message for issue in validation.issues])

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