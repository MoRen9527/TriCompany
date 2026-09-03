# -*- coding: utf-8 -*-
"""LG-025 M0d 回填验证：sourceFiles pre-pass + definition 组装驱动（2026-09-03）。

M0d commit② 返工（R1-R5）三件套永久断言（COS 第二方法固化，回归锚）：
  ① 值形态前缀断言——真源 manifest sourceFiles 78 键逐键 TriCompany/source-agents/ 前缀；
  ② 契约投影对表断言——sourceFiles == contract.paths 投影逐键（含 CSO/DE 合并式）；
  ③ 存在性 error 断言——所指文件缺失/不可解析 → source_files_not_found 前置拦截。
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.source_publish_check import (
    SOURCE_FILES_REQUIRED_KEYS,
    SOURCE_FILES_VALUE_PREFIX,
    _source_files_preflight,
    run_agent_publish,
)

_TRI_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_REL = "source-agents/registries/trimetaverse-live-agent-publish-manifest.json"
_MANIFEST_PATH = _TRI_REPO_ROOT / _MANIFEST_REL
# contract paths 块文本解析（投影正身=contract.yaml 原文，非二次真源）
_PATHS_BLOCK_RE = re.compile(r"^paths:\n((?:  [a-z_]+: .+\n)+)", re.MULTILINE)
_MERGED_SEAT_IDS = ("customer-success-officer", "deployment-engineer")


def _load_role_agent_entries() -> list[dict]:
    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    return [
        entry for entry in manifest.get("liveEntries", [])
        if entry.get("kind") == "role-agent" and entry.get("sourceFiles")
    ]


def _employee_id_of(entry: dict) -> str:
    """从 liveEntries[].source 提取席位 id（TriCompany/source-agents/<id>/<id>.agent.md）。"""
    return entry["source"].split("/")[2]


def _contract_paths(employee_id: str) -> dict[str, str]:
    contract_text = (
        _TRI_REPO_ROOT / "source-agents" / employee_id / f"{employee_id}.contract.yaml"
    ).read_text(encoding="utf-8-sig")
    match = _PATHS_BLOCK_RE.search(contract_text)
    assert match, f"paths 块解析失败: {employee_id}"
    paths: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        paths[key.strip()] = value.strip()
    return paths


class Lg025M0dBackfillValidation(unittest.TestCase):
    # ── preflight 单元合同（R1-R5 版两参签名）────────────────────────────

    def test_preflight_missing_source_files_block(self):
        entry = {"kind": "role-agent"}
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                _source_files_preflight(entry, Path(tmp)),
                "source_files_missing:sourceFiles",
            )

    def test_preflight_missing_key_reported(self):
        """缺键报告：前五键合法（前缀形态+实存文件）逐键通过后，缺 social 键报
        source_files_missing:social。单病 fixture——键值带病（无效路径或缺文件）
        会让 R4/R5 在更早键位抢报，掩盖缺键断言。"""
        entry = {"kind": "role-agent", "sourceFiles": {
            "soul": f"{SOURCE_FILES_VALUE_PREFIX}x/soul.agent.md",
            "agent_body": f"{SOURCE_FILES_VALUE_PREFIX}x/agent-body.agent.md",
            "agent_frontmatter": f"{SOURCE_FILES_VALUE_PREFIX}x/agent-frontmatter.agent.md",
            "memory": f"{SOURCE_FILES_VALUE_PREFIX}x/memory.agent.md",
            "colleagues": f"{SOURCE_FILES_VALUE_PREFIX}x/colleagues.agent.md",
        }}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for key in ("soul", "agent_body", "agent_frontmatter", "memory", "colleagues"):
                kit_file = root / "source-agents" / "x" / f"{key.replace('_', '-')}.agent.md"
                kit_file.parent.mkdir(parents=True, exist_ok=True)
                kit_file.write_text("kit stub\n", encoding="utf-8")
            self.assertEqual(
                _source_files_preflight(entry, root),
                "source_files_missing:social",
            )

    def test_preflight_non_prefix_value_rejected(self):
        """R4：值不带仓库前缀形态 → source_files_not_found:<key>（内部自洽假绿根因消解）。"""
        entry = {"kind": "role-agent", "sourceFiles": {
            k: f"x/{k}.agent.md" for k in SOURCE_FILES_REQUIRED_KEYS
        }}
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                _source_files_preflight(entry, Path(tmp)),
                "source_files_not_found:soul",
            )

    def test_preflight_missing_file_rejected(self):
        """R5：前缀形态但 resolve 不到实存文件 → source_files_not_found:<key>。"""
        entry = {"kind": "role-agent", "sourceFiles": {
            k: f"{SOURCE_FILES_VALUE_PREFIX}x/{k}.agent.md" for k in SOURCE_FILES_REQUIRED_KEYS
        }}
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                _source_files_preflight(entry, Path(tmp)),
                "source_files_not_found:soul",
            )

    def test_preflight_complete_passes_and_registry_exempt(self):
        """六键前缀形态+实存文件 → 通过；registry 族豁免（不在 kit 契约域）。

        种件基座=source_root/source-agents/<id>/（R5 只剥 TriCompany/ 仓前缀，
        与 _resolve_agent_source_path 同约定——前窗错剥整前缀致 20 fail 根因）。
        """
        entry = {"kind": "role-agent", "sourceFiles": {
            k: f"{SOURCE_FILES_VALUE_PREFIX}x/{k}.agent.md" for k in SOURCE_FILES_REQUIRED_KEYS
        }}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for key in SOURCE_FILES_REQUIRED_KEYS:
                kit_file = root / "source-agents" / "x" / f"{key}.agent.md"
                kit_file.parent.mkdir(parents=True, exist_ok=True)
                kit_file.write_text("kit stub\n", encoding="utf-8")
            self.assertEqual(_source_files_preflight(entry, root), "")
        self.assertEqual(
            _source_files_preflight({"kind": "module-registry-agent"}, _TRI_REPO_ROOT), "",
        )

    # ── 三件套永久断言（返工 R1-R5 回归锚，COS 第二方法固化）──────────────

    def test_1_manifest_value_prefix_form(self):
        """①值形态：真源 manifest role-agent sourceFiles 全键仓库前缀形态（78 键=13 席×6）。"""
        entries = _load_role_agent_entries()
        self.assertEqual(len(entries), 13, "role-agent sourceFiles 席位数漂移")
        key_count = 0
        for entry in entries:
            for key, value in entry["sourceFiles"].items():
                key_count += 1
                self.assertIsInstance(value, str, f"{entry.get('source')}:{key} 值非字符串")
                self.assertTrue(
                    value.startswith(SOURCE_FILES_VALUE_PREFIX),
                    f"{entry.get('source')}:{key} 值非前缀形态: {value}",
                )
        self.assertEqual(key_count, 78, "sourceFiles 键总数漂移（78=13 席×6 键）")

    def test_2_manifest_matches_contract_paths_projection(self):
        """②契约投影：sourceFiles == TriCompany/source-agents/ + contract.paths 逐键；
        CSO/DE 合并席 colleagues/social 同指 colleagues-social.agent.md 显式断言。"""
        entries = _load_role_agent_entries()
        self.assertTrue(entries, "真源 manifest 无 role-agent sourceFiles 条目")
        for entry in entries:
            employee_id = _employee_id_of(entry)
            expected = {
                key: f"{SOURCE_FILES_VALUE_PREFIX}{value}"
                for key, value in _contract_paths(employee_id).items()
            }
            self.assertEqual(
                entry["sourceFiles"], expected,
                f"{employee_id} sourceFiles 与 contract.paths 投影不一致",
            )
        for seat in _MERGED_SEAT_IDS:
            entry = next(e for e in entries if _employee_id_of(e) == seat)
            merged = f"{SOURCE_FILES_VALUE_PREFIX}{seat}/colleagues-social.agent.md"
            self.assertEqual(entry["sourceFiles"]["colleagues"], merged, f"{seat} 合并投影缺失")
            self.assertEqual(entry["sourceFiles"]["social"], merged, f"{seat} 合并投影缺失")

    def test_3_missing_referenced_file_is_preflight_error(self):
        """③存在性：run_agent_publish 前置拦截——sourceFiles 所指文件缺失 →
        error item（source_files_not_found:*），不进渲染不落盘。"""
        entry = {
            "status": "current-copilot-host-live",
            "source": "TriCompany/source-agents/ceo/ceo.agent.md",
            "target": "TriMetaverse/.github/agents/ceo.agent.md",
            "kind": "role-agent",
            "sourceFiles": {
                key: f"{SOURCE_FILES_VALUE_PREFIX}ceo/{key}.agent.md"
                for key in SOURCE_FILES_REQUIRED_KEYS
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "TriCompany"
            (source_root / "source-agents" / "registries").mkdir(parents=True)
            (source_root / _MANIFEST_REL).write_text(
                json.dumps({"manifestId": "test-v0.1", "liveEntries": [entry]}),
                encoding="utf-8",
            )
            support_root = root / "support"
            support_root.mkdir()
            report = run_agent_publish(source_root, support_root, dry_run=True)
        self.assertEqual(report.summary.errors, 1)
        self.assertEqual(report.items[0].action, "error")
        self.assertEqual(report.items[0].error, "source_files_not_found:soul")

    def test_4_truth_surface_referenced_files_exist(self):
        """真值面存在性：manifest sourceFiles 所指 78 件在 TriCompany 仓根实存
        （R5 对真实表面的静态镜像——dry-run rc=0 的前提锚；剥 TriCompany/ 仓前缀，
        与 _resolve_agent_source_path 同约定）。"""
        for entry in _load_role_agent_entries():
            for key, value in entry["sourceFiles"].items():
                path = _TRI_REPO_ROOT / value[len("TriCompany/"):]
                self.assertTrue(
                    path.is_file(),
                    f"{entry.get('source')}:{key} 所指文件缺失: {path}",
                )

    def test_definition_assembly_drives_source_files(self):
        """补强①：组装段驱动 sourceFiles（fd8db82 双源先例——再生不丢键）；
        返工后规则生成=R1 前缀形态+R2 合并投影+R3 frontmatter 正映射。"""
        import inspect
        from runtime.cognition import host_object_generation as hog
        src = inspect.getsource(hog)
        self.assertIn('"sourceFiles"', src)
        self.assertIn('agent_frontmatter', src)
        self.assertIn('customer-success-officer', src)  # 合并席双键同指规则在位
        self.assertIn('SOURCE_FILES_VALUE_PREFIX', src)  # R1 前缀形态规则生成
        self.assertIn('_rule_generated_source_files', src)  # 规则生成函数在位


if __name__ == "__main__":
    unittest.main()
