# -*- coding: utf-8 -*-
# LG-035 后续：validator D1c 退役豁免两案（CTO 裁修法 b，2026-09-15 22:5x 批）
# 既有 fixture（L267/L298）保留原样；本件追加：
#   a) 首部带 D1c 注记的 agent 件 → 零 issues（13 席红灯清零锚）
#   b) 注记头缺失+缺 tools → 仍报红（豁免窄性回归锚——防真缺陷借退役词逃门）
import io

p = 'runtime/cognition/employee_source_kit_validation.py'
s = io.open(p, encoding='utf-8').read()

NEW = r'''

# ── D1c 退役豁免（2026-09-15 CTO 裁修法 b；5973ae1 注记锚=窄性信号）──────────

_D1C_NOTE = "> 本件已退役出渲染链；真源=同目录 agent-body.agent.md（D1b manifest 已切源）。\n"


class RetiredCompositeExemptionValidation(unittest.TestCase):
    def test_retired_composite_agent_file_is_exempt(self) -> None:
        """a) 红灯清零锚：首部带 D1c 注记的 agent 件（缺 tools 等 marker）→ 零 issues。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            d = source_root / "source-agents" / "retired-probe"
            d.mkdir(parents=True)
            # 复合件现役形态：fm（无 tools）+ D1c 注记头 + 正文——缺 tools/认知分层
            # 等 marker 全不计（退役豁免早退）。
            (d / "retired-probe.agent.md").write_text(
                "---\n"
                "name: RetiredProbe\n"
                'description: "退役复合件探针。"\n'
                "user-invocable: true\n"
                "---\n"
                + _D1C_NOTE +
                "你是探针席。\n",
                encoding="utf-8",
            )
            issues = validate_employee_source_kit(source_root, "retired-probe")
            agent_file_issues = [i for i in issues if i.path.as_posix().endswith("retired-probe.agent.md")]
            self.assertEqual(agent_file_issues, [], [i.message for i in agent_file_issues])

    def test_non_retired_agent_missing_tools_still_flagged(self) -> None:
        """b) 窄性回归锚：注记头缺失+缺 tools → 仍报红（豁免不得借退役词逃门）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            d = source_root / "source-agents" / "live-probe"
            d.mkdir(parents=True)
            (d / "live-probe.agent.md").write_text(
                "---\n"
                "name: LiveProbe\n"
                'description: "未退役复合件探针（缺 tools）。"\n'
                "user-invocable: true\n"
                "---\n"
                "你是探针席。\n",
                encoding="utf-8",
            )
            issues = validate_employee_source_kit(source_root, "live-probe")
            agent_issues = [i for i in issues if i.path.as_posix().endswith("live-probe.agent.md")]
            self.assertTrue(
                any("missing required agent marker: tools:" in i.message for i in agent_issues),
                [i.message for i in agent_issues],
            )

    def test_retired_note_in_tail_is_not_exempt(self) -> None:
        """窄性补充：注记锚不在文件首部（尾部才出现）→ 不豁免（照常报红）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            d = source_root / "source-agents" / "tail-probe"
            d.mkdir(parents=True)
            (d / "tail-probe.agent.md").write_text(
                "---\n"
                "name: TailProbe\n"
                'description: "注记在尾部的探针。"\n'
                "user-invocable: true\n"
                "---\n"
                "你是探针席。\n"
                + _D1C_NOTE,
                encoding="utf-8",
            )
            issues = validate_employee_source_kit(source_root, "tail-probe")
            agent_issues = [i for i in issues if i.path.as_posix().endswith("tail-probe.agent.md")]
            self.assertTrue(
                any("missing required agent marker: tools:" in i.message for i in agent_issues),
                [i.message for i in agent_issues],
            )


if __name__ == "__main__":
    unittest.main()
'''

body = s.rstrip()
old_tail = 'if __name__ == "__main__":\n    unittest.main()'
assert body.endswith(old_tail), repr(body[-80:])
body = body[: -len(old_tail)].rstrip('\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(body + '\n' + NEW)
print('appended')
