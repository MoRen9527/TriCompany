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


if __name__ == "__main__":
    unittest.main()
