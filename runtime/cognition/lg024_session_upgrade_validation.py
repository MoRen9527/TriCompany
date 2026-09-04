# -*- coding: utf-8 -*-
"""LG-024 批 0 样板验证：session 面合同升格组合管线（2026-09-02，CTO 派工令）。

五断言 + 正签件 diff 交叉验证（第二方法）。纪律：dry-run/临时输出路径，
不覆盖现役正签件、不触 .claude/hub/ 手作件（只读对拍）。
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.host_object_generation import (
    CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET,
    generate_ceo_chief_of_staff_host_objects,
)
from runtime.cognition.source_publish_check import (
    CLAUDE_SESSION_DERIVED_MARKER,
    SESSION_BODY_SECTION_HEADER,
    HOST_RENDER_REGISTRY,
    _compose_session_payload,
    _extract_m001_public_section,
    _load_session_body_payload,
    _publish_single_agent,
    _render_agent_payload,
    _split_frontmatter,
)

_TRI_REPO_ROOT = Path(__file__).resolve().parents[2]
_TRIMETAVERSE_ROOT = _TRI_REPO_ROOT.parent / "TriMetaverse"
_SIGNED_PIECE = (
    _TRIMETAVERSE_ROOT / ".claude" / "hub" / "ceo-chief-of-staff.session.md"
)
_SOURCE_AGENT_MD = (
    _TRI_REPO_ROOT / "source-agents" / "ceo-chief-of-staff" / "ceo-chief-of-staff.agent.md"
)
_SESSION_BODY_MD = (
    _TRI_REPO_ROOT / "source-agents" / "ceo-chief-of-staff" / "session-body.agent.md"
)

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def _rendered_session_text() -> str:
    """组合公式直调：源侧合成件 + sessionBody 片段 → claude-session 产物文本。

    M-001 终裁①：全席公共段（D-04 真源投影）随组合公式注入（与主链
    run_agent_publish 同构——public_section 抽取对齐，防测试通道与执行通道
    结构漂移）。"""
    spec = HOST_RENDER_REGISTRY["claude-session"]
    entry = {
        "sessionBody": CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET.session_body_ref,
        "renderTemplate": "host-default",
    }
    source_text = _SOURCE_AGENT_MD.read_text(encoding="utf-8-sig")
    fragment_text, err = _load_session_body_payload(_TRI_REPO_ROOT, entry)
    assert not err, f"sessionBody 片段加载失败: {err}"
    public_section, m001_err = _extract_m001_public_section(_TRI_REPO_ROOT)
    assert not m001_err, f"M-001 公共段抽取失败: {m001_err}"
    composed = _compose_session_payload(
        source_text, fragment_text, spec, public_section=public_section
    )
    rendered, render_err, _ = _render_agent_payload(composed, entry, "claude-session")
    assert not render_err, f"渲染失败: {render_err}"
    return rendered


class Lg024SessionUpgradeValidation(unittest.TestCase):
    """批 0 样板：ceo 席 session 面合同升格组合管线五断言。"""

    def test_1_golden_section_set_complete(self):
        """golden 节集基线：源侧 ^## 节清单逐一在位（零剥离）+ 补充段节。"""
        rendered = _rendered_session_text()
        source_text = _SOURCE_AGENT_MD.read_text(encoding="utf-8-sig")
        _, source_body, _ = _split_frontmatter(source_text)
        source_sections = set(_SECTION_RE.findall(source_body))
        rendered_sections = set(_SECTION_RE.findall(rendered))
        missing = source_sections - rendered_sections
        self.assertEqual(missing, set(), f"治理节缺失: {missing}")
        self.assertIn("会话面补充（session-body）", rendered_sections)

    def test_2_no_frontmatter(self):
        """产物首行 ≠ ---（frontmatter 不入会话合同）。"""
        rendered = _rendered_session_text()
        first_line = rendered.split("\n", 1)[0].strip()
        self.assertNotEqual(first_line, "---")
        self.assertNotIn("tools:", rendered.split("\n\n", 1)[0])

    def test_3_session_body_section_in_place(self):
        """sessionBody 在位：分隔段头存在+片段非空行逐行在位。"""
        rendered = _rendered_session_text()
        self.assertIn(SESSION_BODY_SECTION_HEADER, rendered)
        fragment_lines = [
            line.strip()
            for line in _SESSION_BODY_MD.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
        for line in fragment_lines:
            self.assertIn(line, rendered, f"片段行缺失: {line[:60]}")

    def test_4_render_idempotent_byte_stable(self):
        """渲染幂等：连续两次渲染字节一致（组合管线无时间戳注入）。"""
        self.assertEqual(_rendered_session_text(), _rendered_session_text())

    def test_5_pipeline_dry_run_no_write(self):
        """管线层 dry-run：不落盘、action ∈ 预期集、无 error。"""
        with tempfile.TemporaryDirectory() as tmp:
            generated = generate_ceo_chief_of_staff_host_objects(tmp)
            manifest = generated.manifest_path.read_text(encoding="utf-8-sig")
            self.assertIn('"sessionBody"', manifest)
            self.assertIn('"liveEntries"', manifest)
            entry = {
                "target": CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET.live_entry_ref,
                "source": "TriCompany/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.agent.md",
                "kind": "role-agent",
                "status": "current-copilot-host-live",
                "sessionBody": CEO_CHIEF_OF_STAFF_HOST_OBJECT_SET.session_body_ref,
                "renderTemplate": "host-default",
            }
            item = _publish_single_agent(
                _SOURCE_AGENT_MD,
                Path(tmp) / "unused.session.md",
                entry,
                dry_run=True,
                host_id="claude-session",
                source_root=_TRI_REPO_ROOT,
            )
            self.assertEqual(item.error, "", f"dry-run error: {item.error}")
            self.assertIn(item.action, {"skipped_dry_run", "derived_drift", "would_create"})
            self.assertFalse((Path(tmp) / "unused.session.md").exists(), "dry-run 不得写盘")

    def test_6_signed_piece_diff_is_upgrade_increment(self):
        """正签件对拍（第二方法，f669ec1a 后语义）：正签件已随批 0 升格替换
        （f669ec1a：1884487b 首件 17→151 行，增量交叉验证当轮已过）——本用例
        常驻化为 drift=0 幂等再确证：现役正签件 == 组合公式再渲染产物。"""
        self.assertTrue(_SIGNED_PIECE.is_file(), f"正签件缺失: {_SIGNED_PIECE}")
        rendered = _rendered_session_text()
        signed = _SIGNED_PIECE.read_text(encoding="utf-8-sig")
        self.assertEqual(
            rendered.strip(),
            signed.strip(),
            "正签件与组合公式渲染 drift≠0（源侧或管线漂移，须勘）",
        )
        self.assertIn(CLAUDE_SESSION_DERIVED_MARKER, rendered)


if __name__ == "__main__":
    unittest.main()
