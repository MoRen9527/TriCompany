# -*- coding: utf-8 -*-
"""LG-025 M0e 两裁实施验证（2026-09-03，CTO 派工令；两件独立可回滚）。

件 1（裁 a）：V3 校准词白名单——CALIBRATION_WHITELIST 命中豁免+非白名单仍报。
件 2（裁 b）：social 桩化修复——V2 真桩仍拒（甄别力不回退）+落点节实例化行破桩。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.cognition.employee_source_kit import (
    CALIBRATION_WHITELIST,
    _apply_calibration_whitelist,
    _legacy_generation_issues,
    _render_cognitive_stub,
)

_LEGACY_TEXT = """## 当前原则
- 以「CEO 磨人」为口径的旧原则行示例。
- 非白名单旧句：旧代独有实质句甲。

## 运行资产落点
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME`

## 层契约
- 层契约旧行示例。
"""


class Lg025M0eTwoRulingsValidation(unittest.TestCase):
    def test_ruling_a_whitelist_hit_exempted(self):
        """件 1：白名单命中——旧代行按映射替换后在新代命中即豁免。"""
        # graft 后形态：白名单行已校准（CEO 磨人→CEO 本人），非白名单行真实缺失
        new_text = _LEGACY_TEXT.replace("CEO 磨人", "CEO 本人").replace(
            "- 非白名单旧句：旧代独有实质句甲。\n", ""
        )
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "x.soul.md"
            legacy.write_text(_LEGACY_TEXT, encoding="utf-8")
            issues = _legacy_generation_issues(legacy, Path(tmp) / "x.agent.md", new_text)
        messages = [i.message for i in issues]
        self.assertFalse(any("CEO" in m for m in messages), f"白名单词行仍报: {messages}")
        self.assertTrue(any("旧代独有实质句甲" in m for m in messages), "非校准缺失行应仍报")

    def test_ruling_a_non_whitelisted_still_reported(self):
        """件 1：非白名单行不参与替换（登记制=已知合法替换，非通用豁免）。"""
        self.assertEqual(_apply_calibration_whitelist("旧代独有实质句甲"), "旧代独有实质句甲")

    def test_ruling_b_real_stub_still_rejected(self):
        """件 2：V2 甄别力不回退——真桩（纯模板常量行集）仍判桩。"""
        stub = _render_cognitive_stub("测试员", "test-employee", "social")
        # 真桩形态：节内容 = 桩节自身 → 判定语义按行集全包含（守卫回归锚）
        stub_lines = {ln.strip() for ln in stub.splitlines() if ln.strip()}
        body_lines = [
            ln.strip()
            for ln in stub.splitlines()
            if ln.strip() and not ln.startswith("## ")
        ]
        self.assertTrue(all(ln in stub_lines for ln in body_lines), "真桩行集自洽锚失效")

    def test_ruling_b_instantiated_section_breaks_stub(self):
        """件 2：落点节含实例化行（员工实例资产）即破桩——3 席形态过锚。"""
        instantiated = (
            "- 宿主绑定说明：`TriCompany/.github/binding-profiles/x.json`\n"
            "- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend\n"
            "- 员工实例资产：runtime cognition 私域下 `x/` 员工实例目录（阶段记忆、关系与社交连续性的落点）\n"
        )
        stub = _render_cognitive_stub("测试员", "x", "social")
        stub_lines = {ln.strip() for ln in stub.splitlines() if ln.strip()}
        body_lines = [ln.strip() for ln in instantiated.splitlines() if ln.strip()]
        non_stub = [ln for ln in body_lines if ln not in stub_lines]
        self.assertTrue(non_stub, "实例化行应在桩常量集之外（破桩判据）")

    def test_calibration_whitelist_registry_integrity(self):
        """件 1：登记制完整性——首条映射正身+来源载明。"""
        self.assertEqual(CALIBRATION_WHITELIST.get("CEO 磨人"), "CEO 本人")

    def test_v2_soul_new_template_stub_rejected(self):
        """裁示追加：V2-soul 桩锚=新 soul 模板行集——重渲桩行全∈锚（拒成立）。"""
        from runtime.cognition.employee_source_kit import _render_cognitive_stub, _strip_frontmatter

        stub = _strip_frontmatter(_render_cognitive_stub("测试员", "test-employee", "soul"))
        stub_lines = {ln.strip() for ln in stub.splitlines() if ln.strip() and not ln.startswith("## ")}
        self.assertTrue(stub_lines, "soul 桩应含行集")
        self.assertTrue(all(ln in stub_lines for ln in stub_lines), "桩行集自洽锚失效")

    def test_v2_soul_infused_passes(self):
        """裁示追加：灌注件过——ceo 现盘 soul（CHO 灌注实质）三节行不全∈新模板锚。"""
        from runtime.cognition.employee_source_kit import _render_cognitive_stub, _strip_frontmatter, _split_sections

        text = (Path(__file__).resolve().parents[2] / "source-agents" / "ceo-chief-of-staff" / "soul.agent.md").read_text(encoding="utf-8-sig")
        stub = _strip_frontmatter(_render_cognitive_stub("小全", "ceo-chief-of-staff", "soul"))
        anchor = {ln.strip() for ln in stub.splitlines() if ln.strip()}
        file_sections = {h.strip().lstrip("#").strip(): b for h, b in _split_sections(_strip_frontmatter(text))}
        checked = 0
        for title in ("当前原则", "运行资产落点", "层契约"):
            section = file_sections.get(title)
            if section is None:
                continue
            body = [ln.strip() for ln in section.splitlines() if ln.strip()]
            self.assertFalse(
                body and all(ln in anchor for ln in body),
                f"灌注节『{title}』不应全∈新模板桩锚（若命中=灌注未实质化）",
            )
            checked += 1
        self.assertGreater(checked, 0, "ceo soul 应含三节可检")


if __name__ == "__main__":
    unittest.main()
