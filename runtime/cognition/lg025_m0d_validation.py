# -*- coding: utf-8 -*-
"""LG-025 M0d 回填验证：sourceFiles pre-pass + definition 组装驱动（2026-09-03）。"""

from __future__ import annotations

import unittest

from runtime.cognition.source_publish_check import _source_files_preflight


class Lg025M0dBackfillValidation(unittest.TestCase):
    def test_preflight_missing_source_files_block(self):
        entry = {"kind": "role-agent"}
        self.assertEqual(_source_files_preflight(entry), "source_files_missing:sourceFiles")

    def test_preflight_missing_key_reported(self):
        entry = {"kind": "role-agent", "sourceFiles": {
            "soul": "x/soul.agent.md", "agent_body": "x/agent-body.agent.md",
            "agent_frontmatter": "x/agent-frontmatter.agent.md",
            "memory": "x/memory.agent.md", "colleagues": "x/colleagues.agent.md",
        }}
        self.assertEqual(_source_files_preflight(entry), "source_files_missing:social")

    def test_preflight_complete_passes_and_registry_exempt(self):
        full = {"kind": "role-agent", "sourceFiles": {
            k: f"x/{k}.agent.md" for k in ("soul", "agent_body", "agent_frontmatter", "memory", "colleagues", "social")
        }}
        self.assertEqual(_source_files_preflight(full), "")
        self.assertEqual(_source_files_preflight({"kind": "module-registry-agent"}), "")

    def test_definition_assembly_drives_source_files(self):
        """补强①：组装段驱动 sourceFiles（fd8db82 双源先例——再生不丢键）。"""
        import inspect
        from runtime.cognition import host_object_generation as hog
        src = inspect.getsource(hog)
        self.assertIn('"sourceFiles"', src)
        self.assertIn('agent_frontmatter', src)
        self.assertIn('customer-success-officer', src)  # 合并席双键同指规则在位


if __name__ == "__main__":
    unittest.main()
