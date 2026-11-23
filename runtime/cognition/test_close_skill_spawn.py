"""close_skill_spawn 单测（DP-20261123-018 item7：cost_settlement 可结算块）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition import close_skill_spawn as m


class CostSettlementTest(unittest.TestCase):
    def _mk(self, lines):
        d = Path(tempfile.mkdtemp())
        (d / m._COST_LOG_NAME).write_text(
            "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines), encoding="utf-8")
        return d

    def test_settlement_totals_and_unavailable_reason(self):
        d = self._mk([
            {"stage": "plan_skill", "duration_s": 30.5, "seats": ["cos"], "delta_cny": 0.12},
            {"stage": "score_skill", "duration_s": 600.0, "seats": ["cos", "coo"], "delta_cny": None},
        ])
        cs = m._build_cost_settlement(d, {"cost_guard_warning": "w"})
        self.assertEqual(len(cs["stages"]), 2)
        self.assertEqual(cs["total_duration_s"], 630.5)
        self.assertEqual(cs["total_delta_cny"], 0.12)
        self.assertIn("unavailable for 1/2", cs["unavailable_reason"])
        self.assertEqual(cs["guard_hits"], {"a": 1, "b": 0, "c": 0, "d": 0})

    def test_guard_hits_semantic_split(self):
        """DP-040-03 T3: b/c 语义分立——余额门只点亮 c·累计门只点亮 b（旧件 reason fallback 也验）。"""
        d = self._mk([])
        # 新件：显式 guard 字段
        cs = m._build_cost_settlement(d, {"cost_guard": {"paused": True, "guard": "c"}})
        self.assertEqual(cs["guard_hits"]["c"], 1)
        self.assertEqual(cs["guard_hits"]["b"], 0)
        cs = m._build_cost_settlement(d, {"cost_guard": {"paused": True, "guard": "b"}})
        self.assertEqual(cs["guard_hits"]["b"], 1)
        self.assertEqual(cs["guard_hits"]["c"], 0)
        # 旧件：无 guard 字段·从 reason 解析
        cs = m._build_cost_settlement(
            d, {"cost_guard": {"paused": True, "reason": "balance < 20 CNY floor (CFO guard c)"}})
        self.assertEqual(cs["guard_hits"]["c"], 1)
        cs = m._build_cost_settlement(
            d, {"cost_guard": {"paused": True, "reason": "accumulated spend >= 10 CNY cap (CFO guard b)"}})
        self.assertEqual(cs["guard_hits"]["b"], 1)
        # null 升级提示 -> d 键
        cs = m._build_cost_settlement(d, {"cost_guard_warning_balance": "x"})
        self.assertEqual(cs["guard_hits"]["d"], 1)
        self.assertEqual(cs["settled_by"], "CFO")
        self.assertIn("settled_at", cs)

    def test_all_null_delta_forces_reason(self):
        d = self._mk([{"stage": "x", "duration_s": 1.0, "seats": [], "delta_cny": None}])
        cs = m._build_cost_settlement(d, {})
        self.assertIsNone(cs["total_delta_cny"])
        self.assertIn("1/1", cs["unavailable_reason"])

    def test_no_cost_log_zero_stages(self):
        d = Path(tempfile.mkdtemp())
        cs = m._build_cost_settlement(d, {})
        self.assertEqual(cs["stages"], [])
        self.assertEqual(cs["total_duration_s"], 0.0)


class CloseFieldsTest(unittest.TestCase):
    """R10-COS-01/CHO-02：runid_origin/charter_ref/意见消化率。"""

    def test_fields_and_digest_rate(self):
        d = Path(tempfile.mkdtemp())
        (d / "opinions.json").write_text(json.dumps(
            {"opinions": [{"title": "t1"}, {"title": "t2"}, {"title": "t3"}]}), encoding="utf-8")
        (d / "charter-20261123T000000Z.json").write_text(
            json.dumps({"items": [{"title": "a"}, {"title": "b"}]}), encoding="utf-8")
        cf = m._build_close_fields(d, "shift-W48-resume9-20261123T085137Z")
        self.assertEqual(cf["runid_origin"], "resume9")
        self.assertEqual(cf["opinions_in"], 3)
        self.assertEqual(cf["items_consumed"], 2)
        self.assertEqual(cf["digest_rate"], 0.667)
        self.assertIn("undigested_note", cf)

    def test_origin_forms(self):
        self.assertEqual(m._runid_origin("shift-W48-loop-20261123T000000Z"), "loop")
        self.assertEqual(m._runid_origin("shift-W48-ignite-20261123T000000Z"), "ignite")
        self.assertEqual(m._runid_origin("shift-W48-20261123T000000Z"), "bare")

    def test_opinion_dispositions_seven(self):
        """DP-033 cho-1：7 条意见逐条处置表（consumed/rejected/deferred）·digest_rate 由表计算。"""
        d = Path(tempfile.mkdtemp())
        seats = ["cos", "coo", "cao", "cpo", "cto", "cho", "cfo"]
        ops = [{"opinion_id": "op-%d" % i, "seat": s, "title": "t%d" % i}
               for i, s in enumerate(seats)]
        (d / "opinions.json").write_text(json.dumps({"opinions": ops}, ensure_ascii=False),
                                         encoding="utf-8")
        (d / "charter-20261123T000000Z.json").write_text(json.dumps({"items": [
            {"opinion_id": "op-0", "owner_seat": "cos"},
            {"opinion_id": "op-5", "owner_seat": "cho"}]}, ensure_ascii=False), encoding="utf-8")
        (d / "opinion_dispositions.json").write_text(json.dumps({"dispositions": [
            {"opinion_id": "op-%d" % i, "state": "rejected", "owner_seat": "cto",
             "reason": "五字段缺失被 charter-hook 退回·候补件", "evidence_ref": "charter-hook.log"}
            for i in (1, 2, 3, 4, 6)]}, ensure_ascii=False), encoding="utf-8")
        cf = m._build_close_fields(d, "shift-W48-resume10-20261123T115623Z")
        rows = cf["opinion_dispositions"]
        self.assertEqual(len(rows), 7)
        self.assertEqual({r["opinion_id"] for r in rows}, {"op-%d" % i for i in range(7)})
        for r in rows:
            self.assertTrue(r["owner_seat"], r)
            self.assertTrue(r["state"], r)
            self.assertTrue(r["reason"], r)
        states = {r["opinion_id"]: r["state"] for r in rows}
        self.assertEqual(states["op-0"], "consumed")
        self.assertEqual(states["op-5"], "consumed")
        self.assertEqual(states["op-1"], "rejected")
        self.assertEqual(cf["items_consumed"], 2)
        self.assertEqual(cf["digest_rate"], 0.286)
        self.assertEqual(cf["runid_origin"], "resume10")


if __name__ == "__main__":
    unittest.main()
