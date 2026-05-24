from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_source_kit import (
    EmployeeSourceKitDefinition,
    generate_employee_source_kit,
    host_binding_profile_reference,
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