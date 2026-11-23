"""loop_joint_review_spawn 单测（CTO 裁 2026-11-23：可比性系数随卷落·附卷不并入判级）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition import loop_joint_review_spawn as m


def _faces(dims: list[dict]) -> dict:
    return {"cos": {"dimensions": dims}}


class ComparabilityCoefficientTest(unittest.TestCase):
    def test_jaccard_against_previous_round(self):
        root = Path(tempfile.mkdtemp())
        prev, cur = root / "r-prev", root / "r-cur"
        prev.mkdir(); cur.mkdir()
        (prev / "joint-review.json").write_text(json.dumps(
            {"faces": _faces([{"object": "a", "dimension": "x"},
                              {"object": "b", "dimension": "y"}])}), encoding="utf-8")
        jr = {"faces": _faces([{"object": "a", "dimension": "x"},
                               {"object": "a", "dimension": "z"},
                               {"object": "b", "dimension": "y"}])}
        cc = m._comparability_coefficient(cur, jr)
        self.assertEqual(cc["prev_run"], "r-prev")
        self.assertEqual(cc["jaccard_a"], 0.5)   # {x} ∩ {x,z} → 1/2
        self.assertEqual(cc["jaccard_b"], 1.0)

    def test_no_previous_round(self):
        solo = Path(tempfile.mkdtemp()) / "solo"
        solo.mkdir()
        jr = {"faces": _faces([{"object": "a", "dimension": "x"}])}
        cc = m._comparability_coefficient(solo, jr)
        self.assertIsNone(cc["prev_run"])

    def test_empty_sets_return_none(self):
        root = Path(tempfile.mkdtemp())
        prev, cur = root / "p", root / "c"
        prev.mkdir(); cur.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({"faces": {}}), encoding="utf-8")
        cc = m._comparability_coefficient(cur, {"faces": {}})
        self.assertIsNone(cc["jaccard_a"])
        self.assertIsNone(cc["jaccard_b"])


class RunIdNameOrderingTest(unittest.TestCase):
    """CTO 建议（2026-11-23）：前轮按 runId 命名时戳取序·mtime 被外部污染时仍取真正前一。"""

    def test_name_timestamp_beats_polluted_mtime(self):
        import os
        root = Path(tempfile.mkdtemp())
        older = root / "shift-W48-loop-20261122T100000Z"   # 时戳早
        newer = root / "shift-W48-resume4-20261123T053031Z"  # 时戳晚
        cur = root / "shift-W48-resume5-20261123T090000Z"
        for d in (older, newer, cur):
            d.mkdir()
        faces = {"faces": _faces([{"object": "a", "dimension": "x"}])}
        for d in (older, newer):
            (d / "joint-review.json").write_text(json.dumps(faces), encoding="utf-8")
        # 污染：把更早轮的 joint-review.json mtime 拨到最新（模拟外部写）
        os.utime(older / "joint-review.json", (2_000_000_000, 2_000_000_000))
        cc = m._comparability_coefficient(cur, faces)
        self.assertEqual(cc["prev_run"], "shift-W48-resume4-20261123T053031Z")  # 命名时戳胜出


# ── DP-20261123-017 维度冻结四案（CTO 规格 1b51e7eca §三）──


def _full_table() -> dict:
    seats = {}
    for i, seat in enumerate(m.SEATS):
        seats[seat] = {"dimensions": [
            {"id": f"{seat}-{j+1}", "name": f"d{j+1}", "definition": "x",
             "object_scope": "both"} for j in range(3)]}
    return {"version": "1.0.0", "table_version": "v1", "status": "ready", "seats": seats}


class DimensionTableTest(unittest.TestCase):
    def test_schema_validation(self):
        self.assertEqual(m._validate_table(_full_table(), m.SEATS), [])
        bad = _full_table()
        bad["seats"]["cos"]["dimensions"] = bad["seats"]["cos"]["dimensions"][:1]  # 1 维
        errs = m._validate_table(bad, m.SEATS)
        self.assertTrue(any("cos" in e and "<3" in e for e in errs))
        bad2 = _full_table()
        bad2["seats"]["coo"]["dimensions"][0]["object_scope"] = "X"
        self.assertTrue(any("object_scope" in e for e in m._validate_table(bad2, m.SEATS)))

    def test_out_of_table_rejected(self):
        dims = _full_table()["seats"]["cto"]["dimensions"]
        ok, viol = m._validate_seat_scores(
            [{"dimension_id": "cto-1", "object": "A", "score": 80},
             {"dimension_id": "fake-9", "object": "A", "score": 90},
             {"dimension_id": "cto-2", "object": "C", "score": 90},
             {"dimension_id": "cto-3", "object": "A", "score": 190}], dims)
        self.assertEqual([e["dimension_id"] for e in ok], ["cto-1"])
        self.assertEqual(len(viol), 3)   # 越表/坏对象/超域分

    def test_same_table_version_comparability_is_one(self):
        root = Path(tempfile.mkdtemp())
        prev, cur = root / "shift-W48-a-20261123T000000Z", root / "shift-W48-b-20261123T010000Z"
        prev.mkdir(); cur.mkdir()
        faces = _faces([{"object": "a", "dimension": "x"}])
        for d in (prev, cur):
            (d / "joint-review.json").write_text(json.dumps(
                {"faces": faces, "dimension_table_version": "v1"}), encoding="utf-8")
        cc = m._comparability_coefficient(cur, {"faces": faces, "dimension_table_version": "v1"})
        self.assertEqual(cc["jaccard_a"], 1.0)
        self.assertEqual(cc["jaccard_b"], 1.0)
        self.assertIn("same dimension-table version", cc["note"])

    def test_seat_means_deterministic(self):
        faces = {"s1": {"dimensions": [
            {"object": "a", "score": 80.0}, {"object": "a", "score": 60.0},
            {"object": "b", "score": 90.0}]},
            "s2": {"dimensions": [{"object": "a", "score": 40.0}, {"object": "b", "score": 50.0}]}}
        r1 = m._seat_means(faces)
        r2 = m._seat_means(json.loads(json.dumps(faces)))
        self.assertEqual(r1, r2)                       # 确定性
        self.assertEqual(r1["a"], 55.0)                # 席内均值 s1=70,s2=40 → 跨席 (70+40)/2=55（mean-of-seat-means 非总均值）
        self.assertEqual(r1["b"], 70.0)                # (90+50)/2


if __name__ == "__main__":
    unittest.main()
