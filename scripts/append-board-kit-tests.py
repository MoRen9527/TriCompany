# -*- coding: utf-8 -*-
# board kit 豁免回归两案（CTO 批 2026-09-17 20:1x）：board 零 issues + bs 不回归
import io

p = 'runtime/cognition/employee_source_kit_validation.py'
s = io.open(p, encoding='utf-8').read()

NEW = r'''

# ── board kit 豁免（2026-09-17 CTO 裁）：无合成件的单源治理席名册位 ──────────

class BoardKitExemptionValidation(unittest.TestCase):
    def test_live_board_kit_validate_zero_issues(self) -> None:
        """实盘 board：SYNTHETIC_PATH_OVERRIDES 入册后 validate 零 issues
        （探缺豁免生效——board 三件形态无五件套无复合件）。"""
        repo_root = Path(__file__).resolve().parents[2]
        result = validate_employee_source_kit(repo_root, "board")
        self.assertEqual(result.issues, (), [i.message for i in result.issues])

    def test_business_strategy_override_path_unchanged(self) -> None:
        """bs 原路径不回归：名册扩条不影响既有 bs 条目（路径+豁免集双断）。"""
        self.assertEqual(
            SYNTHETIC_PATH_OVERRIDES.get("business-strategy"),
            Path("source-agents") / "registries" / "business-strategy.agent.md",
        )
        self.assertIn("board", SYNTHETIC_PATH_OVERRIDES)
        self.assertIn("business-strategy", COGNITIVE_LAYER_EXEMPT_EMPLOYEE_IDS)
        self.assertIn("board", COGNITIVE_LAYER_EXEMPT_EMPLOYEE_IDS)


if __name__ == "__main__":
    unittest.main()
'''

body = s.rstrip()
old_tail = 'if __name__ == "__main__":\n    unittest.main()'
assert body.endswith(old_tail), repr(body[-60:])
body = body[: -len(old_tail)].rstrip('\n')
# import 补：SYNTHETIC_PATH_OVERRIDES / COGNITIVE_LAYER_EXEMPT_EMPLOYEE_IDS 是否已导入
head = s[: s.index('class ')]
need = []
for name in ('SYNTHETIC_PATH_OVERRIDES', 'COGNITIVE_LAYER_EXEMPT_EMPLOYEE_IDS'):
    if name not in head:
        need.append(name)
if need:
    s_head = s
    for name in need:
        s_head = s_head.replace('    validate_employee_source_kit,\n)', f'    {name},\n    validate_employee_source_kit,\n)', 1)
    s = s_head

s = body + '\n' + NEW
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('appended; imports added:', need)
