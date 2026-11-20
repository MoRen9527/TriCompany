"""D6 白盒 — activation_gate 激活判据件（cto-d6d7-activation-ns9-survey
§八案族承·挡位边纯判读面）。

锚定面：清单逐条判读+全兑现 ready+单条缺 fail-closed+D6 自身豁免钉（防死锁
§二.2）+D7/S5 不入清单+知情停点语义（first_round_pending=stop+载荷拟稿）+
放行令消费（令面非时面）+切换宣告载荷+契约 ValueError+never raises+零写面
断言（判读面纯函数）。

跑法：cd <worktree 根> && python -m unittest runtime.cognition.test_activation_gate -v
"""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.activation_gate import (
    ITEM_LABELS,
    check_activation,
)


def _checks(**kw) -> dict:
    base = {
        "A1_d1_d5_done": True,
        "A2_whitebox_zero_new_red": True,
        "A3_guard_anchors_ok": True,
        "A4_equivalence_and_zero_touch": True,
    }
    base.update(kw)
    return base


class ItemVerdictTest(unittest.TestCase):
    """清单逐条判读案（A1-A4 各案）+全兑现+单条缺 fail-closed。"""

    def test_all_met_ready(self) -> None:
        r = check_activation(_checks())
        self.assertTrue(r["ok"])
        self.assertEqual(r["gate"], "ready")
        self.assertEqual(r["unmet"], [])
        self.assertEqual(len(r["items"]), 4)  # 逐条读数面

    def test_each_item_unmet_blocks(self) -> None:
        for key in ("A1_d1_d5_done", "A2_whitebox_zero_new_red",
                    "A3_guard_anchors_ok", "A4_equivalence_and_zero_touch"):
            r = check_activation(_checks(**{key: False}))
            self.assertEqual(r["gate"], "blocked", key)
            self.assertFalse(r["ok"])
            self.assertEqual(r["unmet"], [key])
            self.assertFalse(r["items"][key]["ok"])
            self.assertIsNone(r["switch_announce"])  # blocked 零宣告面

    def test_a3_unmet_notes_crosspoint(self) -> None:
        r = check_activation(_checks(A3_guard_anchors_ok=False))
        self.assertIn("交点位", r["detail"])  # D6/D7 真实交点位如实注

    def test_item_labels_present(self) -> None:
        r = check_activation(_checks())
        for key, item in r["items"].items():
            self.assertEqual(item["label"], ITEM_LABELS[key])


class DeadlockExemptionTest(unittest.TestCase):
    """防死锁自指豁免钉（§二.2·白名单拒=ValueError 机械面零豁口）。"""

    def test_d6_self_exempt_rejected(self) -> None:
        with self.assertRaises(ValueError):
            check_activation(_checks(d6_done=True))  # 判据含自身=死锁·拒

    def test_activation_gate_done_rejected(self) -> None:
        with self.assertRaises(ValueError):
            check_activation(_checks(activation_gate_done=True))

    def test_d7_not_in_checklist(self) -> None:
        with self.assertRaises(ValueError):
            check_activation(_checks(d7_done=True))  # D7=起跑前置门反向·零入

    def test_s5_not_in_checklist(self) -> None:
        with self.assertRaises(ValueError):
            check_activation(_checks(s5_window_done=True))  # 义融首轮·零入

    def test_unknown_key_rejected(self) -> None:
        with self.assertRaises(ValueError):
            check_activation(_checks(bogus_key=True))


class FirstRoundStopSemanticsTest(unittest.TestCase):
    """知情停点语义面（§三·D6=语义面·执行面=D7 分工零夹带）。"""

    def test_first_round_complete_stops(self) -> None:
        r = check_activation(_checks(first_round_complete=True))
        self.assertEqual(r["gate"], "ready")  # 挡位面 ready
        p = r["first_round_pending"]
        self.assertEqual(p["state"], "stop")  # 阻塞停非知会续跑
        self.assertIsNone(p["authority_ref"])
        self.assertIn("CEO", p["note"])
        self.assertIn("候您一眼知情", p["brief"]["summary"])  # 大白话载荷拟稿
        for slot in ("close_verdict", "score_total", "retry_count", "exit_reading"):
            self.assertIsNone(p["brief"][slot])  # 零读数槽位（采集位调用面）

    def test_round_reading_fills_brief_slots(self) -> None:
        reading = {"close_verdict": "pass", "score_total": 92.5,
                   "retry_count": 0, "exit_reading": "95 线未达"}
        r = check_activation(_checks(first_round_complete=True,
                                     round_reading=reading))
        brief = r["first_round_pending"]["brief"]
        self.assertEqual(brief["close_verdict"], "pass")
        self.assertEqual(brief["score_total"], 92.5)
        self.assertEqual(brief["retry_count"], 0)

    def test_no_first_round_no_pending(self) -> None:
        r = check_activation(_checks())
        self.assertIsNone(r["first_round_pending"])  # 二轮起全自动零停点面


class ReleaseRefConsumptionTest(unittest.TestCase):
    """放行令消费案（停点解除=令面非时面·§三.3）。"""

    def test_release_ref_releases_stop(self) -> None:
        r = check_activation(_checks(first_round_complete=True,
                                     release_ref="CEO-2026-11-21-01"))
        p = r["first_round_pending"]
        self.assertEqual(p["state"], "released")
        self.assertEqual(p["authority_ref"], "CEO-2026-11-21-01")
        self.assertIn("放行一次非逐轮放行", p["note"])

    def test_empty_release_ref_stays_stopped(self) -> None:
        r = check_activation(_checks(first_round_complete=True,
                                     release_ref="   "))
        p = r["first_round_pending"]
        self.assertEqual(p["state"], "stop")  # 无 ref=拒绝 fail-closed

    def test_release_ref_without_first_round_ignored(self) -> None:
        r = check_activation(_checks(release_ref="CEO-x"))
        self.assertIsNone(r["first_round_pending"])  # 零首轮面零停点可解


class SwitchAnnounceTest(unittest.TestCase):
    """切换宣告载荷案（§四.3·宣告=呈报面动作非码面分支）。"""

    def test_ready_carries_announce_payload(self) -> None:
        r = check_activation(_checks())
        a = r["switch_announce"]
        self.assertEqual(a["notify_target"], "COO")
        self.assertIn("知会", a["nature"])
        self.assertIn("非批门", a["nature"])  # 候=知会非候批（§四.1 歧义消解承）
        self.assertIn("自动挡已生效", a["announce"])

    def test_blocked_no_announce(self) -> None:
        r = check_activation(_checks(A1_d1_d5_done=False))
        self.assertIsNone(r["switch_announce"])


class ContractValueErrorTest(unittest.TestCase):
    """契约面 ValueError fail-fast（D4 校验两分同构·try 外）。"""

    def test_non_dict_checks_rejected(self) -> None:
        for bad in (None, [], "checks", 123):
            with self.assertRaises(ValueError):
                check_activation(bad)

    def test_missing_required_key_rejected(self) -> None:
        for key in ("A1_d1_d5_done", "A2_whitebox_zero_new_red",
                    "A3_guard_anchors_ok", "A4_equivalence_and_zero_touch"):
            checks = _checks()
            del checks[key]
            with self.assertRaises(ValueError):
                check_activation(checks)

    def test_non_bool_item_value_rejected(self) -> None:
        for bad in (1, "yes", None, {"x": 1}):
            with self.assertRaises(ValueError):
                check_activation(_checks(A1_d1_d5_done=bad))

    def test_non_bool_optional_first_round_rejected(self) -> None:
        with self.assertRaises(ValueError):
            check_activation(_checks(first_round_complete=1))


class NeverRaisesTest(unittest.TestCase):
    """运行面 never raises 奇异输入族（值面怪对象恒返 dict 零 raise）。"""

    def test_weird_optional_values_return_dict(self) -> None:
        class Boom:
            def __str__(self):
                raise RuntimeError("boom")

        for kw in ({"round_reading": "not-a-dict"},
                   {"round_reading": 123},
                   {"release_ref": 123},
                   {"release_ref": Boom()},
                   {"release_ref": {"nested": True}}):
            r = check_activation(_checks(first_round_complete=True, **kw))
            self.assertIsInstance(r, dict)
            self.assertIn(r["gate"], ("ready", "blocked"))

    def test_return_contract_shape(self) -> None:
        r = check_activation(_checks(first_round_complete=True))
        for key in ("ok", "gate", "gate_version", "items", "unmet",
                    "first_round_pending", "switch_announce"):
            self.assertIn(key, r)


class ZeroWriteFaceTest(unittest.TestCase):
    """零写面断言（判读面纯函数·§八案族）。"""

    def test_no_filesystem_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            before = sorted(p.name for p in Path(td).iterdir())
            check_activation(_checks(first_round_complete=True))
            check_activation(_checks(A3_guard_anchors_ok=False))
            after = sorted(p.name for p in Path(td).iterdir())
            self.assertEqual(before, after)  # 调用前后零文件面变化

    def test_source_zero_file_io_tokens(self) -> None:
        import runtime.cognition.activation_gate as mod
        src = inspect.getsource(mod)
        for token in ("open(", "write_text", "read_text", "mkdir",
                      "os.replace", "mkstemp", "rglob"):
            self.assertNotIn(token, src)  # 判读面零文件 IO 字样（纯函数钉）


if __name__ == "__main__":
    unittest.main()
