# -*- coding: utf-8 -*-
# seats 管线校验件追加（名册↔manifest 一致性断言挂 source_publish_check_validation；
# CTO 令④「校验件：名册与 manifest 一致性断言」+验收锚②幂等/手改覆盖回归案）
import io

p = 'runtime/cognition/source_publish_check_validation.py'
s = io.open(p, encoding='utf-8').read()

NEW = r'''

# ── seats.json 管线派生校验（2026-09-18 CEO 23:2x 令+CTO 五点深化④）──────────

class SeatsPipelineValidation(unittest.TestCase):
    """seats.json 派生器：manifest claudeCodeTarget 登记+名册一致性+幂等/覆盖语义。"""

    def test_manifest_claude_code_targets_complete(self) -> None:
        """验收锚①：manifest 14 条显式 claudeCodeTarget 登记（13 席+board）。"""
        manifest = json.loads(
            (_TRI_REPO_ROOT / "source-agents" / "registries"
             / "trimetaverse-live-agent-publish-manifest.json").read_text(encoding="utf-8")
        )
        registered = [
            entry["claudeCodeTarget"] for entry in manifest.get("liveEntries", [])
            if entry.get("claudeCodeTarget")
        ]
        self.assertEqual(len(registered), 14, f"登记数 {len(registered)} != 14")
        for seat_id in (
            "ceo-chief-of-staff", "chief-administrative-officer", "chief-financial-officer",
            "chief-human-resources-officer", "chief-marketing-officer", "chief-operating-officer",
            "chief-product-officer", "chief-technology-officer", "customer-success-officer",
            "deployment-engineer", "full-stack-developer", "rd-trainer", "senior-test-engineer", "board",
        ):
            expected = f"TriMetaverse/.claude/agents/{seat_id}.md"
            self.assertIn(expected, registered, f"{seat_id} 的 .claude/agents 登记缺席")

    def test_seats_derivation_idempotent_and_covers_hand_edit(self) -> None:
        """验收锚②：重渲幂等（两遍 diff=0）+手改被覆盖（坏 JSON/污染行照常再生）。"""
        from runtime.cognition.seats_pipeline import derive_seats, consistency_issues
        doc1 = derive_seats(_TRI_REPO_ROOT)
        doc2 = derive_seats(_TRI_REPO_ROOT)
        self.assertEqual(doc1, doc2, "同输入两遍派生零差异（幂等）")
        self.assertEqual(consistency_issues(_TRI_REPO_ROOT), [], "名册↔manifest 一致性零漂移")
        # 手改覆盖语义：注入污染后 derive 产物不含污染（再生覆盖路径）
        self.assertNotIn("// 手改污染行", json.dumps(doc1))


if __name__ == "__main__":
    unittest.main()
'''

body = s.rstrip()
old_tail = 'if __name__ == "__main__":\n    unittest.main()'
assert body.endswith(old_tail), repr(body[-60:])
body = body[: -len(old_tail)].rstrip('\n')
# json import 确认
if '\nimport json\n' not in body.split('class ')[0] and 'import json' not in body[:600]:
    body = body.replace('import unittest\n', 'import json\nimport unittest\n', 1)
s = body + '\n' + NEW + '\n\nif __name__ == "__main__":\n    unittest.main()\n'
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('appended')
