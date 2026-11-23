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
        self.assertEqual(cs["guard_hits"], {"a": 1, "b": 0, "c": 0})
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


if __name__ == "__main__":
    unittest.main()
