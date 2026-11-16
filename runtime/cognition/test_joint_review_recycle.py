"""joint_review_recycle 白盒单测（W2 施工件·回收段）。

覆盖：verdict 六态全谱/schema fail-closed（零强判·失配拒收不计 quorum）/
三域直加计算/席均/改进卷指针/挂起态 exit 0 解耦语义/落卷双面。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.joint_review_recycle import (  # noqa: E402
    collect_scores,
    decide,
    dim_a_domain_score,
    dim_b_domain_score,
    machine_domain_score,
    run_recycle,
    validate_dim_a,
    validate_dim_b,
)


def mk_dim_a(seat: str, scores: dict[str, int]) -> dict:
    return {
        "score_version": "1.0.0", "seat": seat, "dim": "A",
        "form": "subjective 试卷形",
        "entries": [
            {"criterion": c, "score": s, "rationale": "r", "evidence_ref": "e"}
            for c, s in scores.items()
        ],
    }


def mk_dim_b(seat: str, verdicts: dict[str, str]) -> dict:
    weight = {"A": 10, "F": 8, "H": 7}
    return {
        "score_version": "1.0.0", "seat": seat, "dim": "B",
        "form": "collection 试卷形·二值制",
        "entries": [
            {"family_id": f, "verdict": v, "weight": weight[f],
             "rationale": "r", "evidence_ref": "e"}
            for f, v in verdicts.items()
        ],
    }


def _plant(root: Path, seat: str, a_scores=None, b_verdicts=None, bad_a=None, imp=False):
    (root / f"joint-review-{seat}-dimA-score.json").write_text(
        json.dumps(bad_a if bad_a is not None else mk_dim_a(seat, a_scores or {"I1": 8, "I2": 7})),
        encoding="utf-8")
    (root / f"joint-review-{seat}-dimB-score.json").write_text(
        json.dumps(mk_dim_b(seat, b_verdicts or {"A": "pass", "F": "pass", "H": "fail"})),
        encoding="utf-8")
    if imp:
        (root / f"joint-review-{seat}-improvement.json").write_text(
            json.dumps({"seat": seat, "items": ["x"]}), encoding="utf-8")


def _mk_run_dir(root: Path) -> Path:
    rd = root / "runs" / "shift-W46-20261116T000000Z"
    rd.mkdir(parents=True)
    (rd / "score.json").write_text(json.dumps({
        "score": {"families": [
            {"family_id": "B", "score": 12}, {"family_id": "C", "score": 9},
            {"family_id": "A", "score": None},
        ]},
    }), encoding="utf-8")
    return rd


class SchemaCase(unittest.TestCase):
    """schema fail-closed（§四.3·零强判）。"""

    def test_dim_a_ok_and_defects(self):
        self.assertEqual(validate_dim_a(mk_dim_a("CTO", {"I1": 8})), [])
        errs = validate_dim_a({"dim": "B", "seat": "X",
                               "entries": [{"criterion": "c", "score": 11}]})
        self.assertTrue(any("dim!=A" in e for e in errs))
        self.assertTrue(any("score 非 0-10" in e for e in errs))

    def test_dim_b_ok_and_defects(self):
        self.assertEqual(validate_dim_b(mk_dim_b("COS", {"A": "pass"})), [])
        errs = validate_dim_b({"dim": "A", "seat": "X", "entries": [
            {"family_id": "Z", "verdict": "maybe", "weight": "10"}]})
        self.assertTrue(any("dim!=B" in e for e in errs))
        self.assertTrue(any("family_id 非 A/F/H" in e for e in errs))
        self.assertTrue(any("verdict 非 pass/fail" in e for e in errs))
        self.assertTrue(any("weight" in e for e in errs))


class CollectCase(unittest.TestCase):
    """卷池回收：present/absent/mismatch 三面分立。"""

    def test_full_pool_and_absent_and_mismatch(self):
        with TemporaryDirectory() as td:
            sr = Path(td)
            _plant(sr, "COS", a_scores={"I1": 9})
            _plant(sr, "COO")
            _plant(sr, "CTO", bad_a={"dim": "X", "seat": "CTO", "entries": []})
            # 其余四席缺席
            pool = collect_scores(sr)
            self.assertEqual(pool["valid"], ["COS", "COO"])
            self.assertEqual(pool["absent"], ["CAO", "CPO", "CHO", "CFO"])
            self.assertEqual(pool["mismatch"][0]["seat"], "CTO")

    def test_improvement_collected(self):
        with TemporaryDirectory() as td:
            sr = Path(td)
            _plant(sr, "COS", imp=True)
            pool = collect_scores(sr)
            self.assertEqual(pool["improvements"], [{"seat": "COS", "ref": "joint-review-COS-improvement.json"}])


class DomainScoreCase(unittest.TestCase):
    """三域直加对形（score_engine v2.0.0 并盘 100 形）。"""

    def test_machine_sum_skips_null_and_non_machine(self):
        with TemporaryDirectory() as td:
            rd = _mk_run_dir(Path(td))
            total, fams = machine_domain_score(rd)
            self.assertEqual((total, fams), (21, {"B": 12, "C": 9}))  # A=null/非机判族零计入

    def test_dim_b_seat_mean_pass_weight(self):
        with TemporaryDirectory() as td:
            sr = Path(td)
            _plant(sr, "COS", b_verdicts={"A": "pass", "F": "pass", "H": "fail"})  # 10+8+0=18
            _plant(sr, "CTO", b_verdicts={"A": "pass", "F": "fail", "H": "pass"})  # 10+0+7=17
            pool = collect_scores(sr)
            self.assertEqual(dim_b_domain_score(pool["dim_b_pool"]), 17.5)

    def test_dim_a_seat_mean(self):
        with TemporaryDirectory() as td:
            sr = Path(td)
            _plant(sr, "COS", a_scores={"I1": 9, "I2": 7})   # 16
            _plant(sr, "CTO", a_scores={"I1": 8, "I2": 8})   # 16
            pool = collect_scores(sr)
            self.assertEqual(dim_a_domain_score(pool["dim_a_pool"]), 16.0)


class DecideSixVerdictsCase(unittest.TestCase):
    """verdict 六态全谱钉案。"""

    def _pool(self, n_valid=5, mismatch=(), improvements=None):
        return {"valid": [f"S{i}" for i in range(n_valid)],
                "absent": [s for s in ("COS", "COO", "CAO", "CPO", "CTO", "CHO", "CFO")
                           if s not in [f"S{i}" for i in range(n_valid)]],
                "mismatch": list(mismatch),
                "dim_a_pool": [mk_dim_a("X", {"I1": 8})] * n_valid,
                "dim_b_pool": [mk_dim_b("X", {"A": "pass", "F": "pass", "H": "pass"})] * n_valid,
                "improvements": improvements or []}

    def test_contract_mismatch_all_invalid(self):
        v, d = decide({"valid": [], "mismatch": [{"seat": "X", "errors": ["e"]}]},
                      Path("."), None, 1, 3, 5)
        self.assertEqual(v, "contract_mismatch")

    def test_pending_quorum(self):
        v, d = decide(self._pool(n_valid=4), Path("."), 60.0, 1, 3, 5)
        self.assertEqual(v, "pending_quorum")
        self.assertEqual(d["quorum_required"], 5)
        self.assertIn("照跑不阻塞", d["note"])

    def test_pending_threshold(self):
        v, d = decide(self._pool(), Path("."), None, 1, 3, 5)
        self.assertEqual(v, "pending_threshold")
        self.assertIn("留参", d["note"])

    def test_converge(self):
        # 机判 21+dimB 25*5 席均 25+dimA 8*5 席均 8 = 54
        with TemporaryDirectory() as td:
            rd = _mk_run_dir(Path(td))
            v, d = decide(self._pool(), rd, 50.0, 1, 3, 5)
            self.assertEqual(v, "converge")
            self.assertEqual(d["total"], 54.0)
            self.assertIn("关 loop 候 CEO 终认", d["action_directive"])

    def test_loop_next_with_improvement_refs(self):
        with TemporaryDirectory() as td:
            rd = _mk_run_dir(Path(td))
            imp = [{"seat": "CTO", "ref": "joint-review-CTO-improvement.json"}]
            v, d = decide(self._pool(improvements=imp), rd, 90.0, 1, 3, 5)
            self.assertEqual(v, "loop_next")
            self.assertIn("marker 序", d["action_directive"])
            self.assertIn("X-Internal-Token", d["action_directive"])
            self.assertEqual(d["improvement_refs"], imp)

    def test_escalate_at_max_round(self):
        with TemporaryDirectory() as td:
            rd = _mk_run_dir(Path(td))
            v, d = decide(self._pool(), rd, 90.0, 3, 3, 5)
            self.assertEqual(v, "escalate_ruling")
            self.assertIn("禁自主续转", d["action_directive"])


class RunRecycleCase(unittest.TestCase):
    """run_recycle 落卷+exit 语义（挂起态 exit 0）。"""

    def test_pending_quorum_exit0_and_land(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            rd = _mk_run_dir(root)
            sr = root / "scores"; sr.mkdir()
            _plant(sr, "COS")  # 1 席有效 < quorum 5
            tree = root / "tree" / "recycle.json"
            args = __import__("argparse").Namespace(
                run_dir=str(rd), run_id="shift-X-1", scores_root=str(sr),
                round=1, max_rounds=3, quorum=5, threshold=None,
                tree_file=str(tree))
            code, out = run_recycle(args)
            self.assertEqual(code, 0)
            self.assertEqual(out["verdict"], "pending_quorum")
            self.assertTrue((rd / "joint-review-recycle.json").is_file())
            self.assertTrue(tree.is_file())


if __name__ == "__main__":
    unittest.main()
