"""COS final-summary 单测（③②：判断式终版面）。"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition import cos_final_summary_spawn as m


class CosFinalTest(unittest.TestCase):
    def test_merge_requires_rationale(self):
        d = Path(tempfile.mkdtemp())
        (d / "close.json").write_text(json.dumps({"run_state": "succeeded"}), encoding="utf-8")
        self.assertIsNone(m._merge_final(d, {"final": {"conclusion": "x"}}))     # rationale 缺=拒
        fin = m._merge_final(d, {"final": {"conclusion": "x", "rationale": "judgement"}})
        self.assertEqual(fin["conclusion"], "x")
        doc = json.loads((d / "close.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["final"]["rationale"], "judgement")
        self.assertEqual(doc["run_state"], "succeeded")                        # 初版保留

    def test_run_writes_final_via_spawn(self):
        d = Path(tempfile.mkdtemp())
        (d / "close.json").write_text("{}", encoding="utf-8")
        payload = json.dumps({"final": {
            "seven_seat_points": [{"seat": "cos", "point": "p"}],
            "divergences": [], "conclusion": "ok",
            "diff_vs_initial": "d", "rationale": "判断式汇总"}})
        import argparse
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5)
        with mock.patch.object(m, "_spawn_seat", return_value={"rc": 0, "out": payload, "err": ""}):
            code, out = m.run(args)
        self.assertEqual(code, 0)
        self.assertEqual(out["verdict"], "pass")
        doc = json.loads((d / "close.json").read_text(encoding="utf-8"))
        self.assertIn("final", doc)

    def test_spawn_unavailable_zero_break(self):
        d = Path(tempfile.mkdtemp())
        import argparse
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5)
        with mock.patch.object(m, "_spawn_seat", return_value={"rc": -2, "out": "", "err": "n/a"}):
            code, out = m.run(args)
        self.assertEqual(code, -2)
        self.assertIn("零阻断", out["verdict"])


if __name__ == "__main__":
    unittest.main()
