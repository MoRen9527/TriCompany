"""loop_joint_review_spawn 单测（CTO 裁 2026-11-23：可比性系数随卷落·附卷不并入判级）。"""
from __future__ import annotations

import json
import pathlib
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


class SeatSandbox019Test(unittest.TestCase):
    def test_sandbox_unique(self):
        a, b = m._seat_sandbox(), m._seat_sandbox()
        self.assertNotEqual(a, b)
        self.assertTrue(a.name.startswith('fade-seat-sandbox-'))

    def test_constrained_prompt_forbids_writes(self):
        dims = [{"id": f"x-{k}", "name": "n", "definition": "d", "object_scope": "both"} for k in (1, 2, 3)]
        pr = m._constrained_prompt("cos", dims)
        self.assertIn('禁创建/修改/删除任何文件', pr)
        self.assertIn('x-1', pr)


class ImprovementsClauseTest(unittest.TestCase):
    """DP-017 追补（CTO 裁 2026-11-23）：constrained prompt 必载 improvements 五字段段（生成器输入契约）。"""

    def test_constrained_prompt_requires_improvements_five_fields(self):
        dims = [{"id": "x-1", "name": "n", "definition": "d", "object_scope": "both"}]
        pr = m._constrained_prompt("cos", dims)
        self.assertIn("improvements", pr)
        for k in ("title", "target", "change", "verify", "rollback"):
            self.assertIn(k, pr)


class ConstrainedImprovementsCarryTest(unittest.TestCase):
    """R10 追补：constrained 面须携带 improvements（resume10 实锚·生成器输入契约）。"""

    def test_constrained_face_keeps_improvements(self):
        import argparse
        from unittest import mock
        five = {"title": "t", "target": "plan.json", "change": "c", "verify": "v", "rollback": "r"}
        seats_tbl = {s: {"dimensions": [
            {"id": f"{s}-{k}", "name": "n", "definition": "d", "object_scope": "both"}
            for k in (1, 2, 3)]} for s in m.SEATS}
        sheet = {"seat": "cos",
                 "dimensions": [{"dimension_id": "cos-1", "object": "A", "score": 80}],
                 "improvements": [five]}
        rd = Path(tempfile.mkdtemp())
        args = argparse.Namespace(run_dir=str(rd), run_id="t", spawn_timeout=5)
        with mock.patch.object(m, "_load_dimension_table",
                               return_value={"table_version": "v1", "status": "ready",
                                             "seats": seats_tbl}),              mock.patch.object(m, "_spawn_seat",
                               return_value={"rc": 0, "out": json.dumps(sheet), "err": ""}):
            rc, out = m.run(args)
        self.assertEqual(rc, 0, out.get("verdict"))
        ops = json.loads((rd / "opinions.json").read_text(encoding="utf-8"))["opinions"]
        self.assertTrue(ops)
        self.assertEqual(ops[0].get("title"), "t")   # 五字段经 face 携带入 opinions
        self.assertEqual(ops[0].get("owner_seat"), "cos")


class ParallelJointReviewTest(unittest.TestCase):
    """DP-036（DP-028 并入）：并发 4+3 / 串行回退 / 各席独立产物 / 聚合单写。"""

    def _table(self):
        return {s: {"dimensions": [
            {"id": f"{s}-{k}", "name": "n", "definition": "d", "object_scope": "both"}
            for k in (1, 2, 3)]} for s in m.SEATS}

    def _args(self, d):
        import argparse
        return argparse.Namespace(run_dir=d, run_id="par", spawn_timeout=5)

    def _spawn_factory(self, tracker):
        import threading, time as _t
        lock = threading.Lock()

        def fake(seat, rd, rid, timeout_s=900, extra_hint="", prompt_head=None, prompt_override=None):
            with lock:
                tracker["active"] += 1
                tracker["max"] = max(tracker["max"], tracker["active"])
                tracker["seats"].append(seat)
            _t.sleep(0.05)
            with lock:
                tracker["active"] -= 1
            sheet = {"seat": seat,
                     "dimensions": [{"dimension_id": f"{seat}-1", "object": "A", "score": 80}],
                     "improvements": [{"title": f"t-{seat}", "target": "plan.json",
                                       "change": "c", "verify": "v", "rollback": "r"}]}
            return {"rc": 0, "out": json.dumps(sheet), "err": ""}
        return fake

    def test_parallel_batches_and_per_seat_artifacts(self):
        import tempfile
        from unittest import mock
        tr = {"active": 0, "max": 0, "seats": []}
        with tempfile.TemporaryDirectory() as d,              mock.patch.object(m, "_load_dimension_table", return_value={
                 "table_version": "v1", "status": "ready", "seats": self._table()}),              mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              mock.patch.object(m, "_spawn_seat", side_effect=self._spawn_factory(tr)):
            rc, out = m.run(self._args(d))
            self.assertEqual(rc, 0)
            self.assertEqual(tr["max"], 4)                     # 首批 4 并发（4+3 分批）
            self.assertEqual(len(tr["seats"]), 7)
            for s in m.SEATS:                                   # ①各席独立产物
                self.assertTrue((pathlib.Path(d) / f"opinions-{s}.json").is_file(), s)
            jr = json.loads((pathlib.Path(d) / "joint-review.json").read_text(encoding="utf-8"))
            self.assertEqual(len(jr.get("faces") or {}), 7)     # ②聚合器单写·七席齐

    def test_serial_fallback(self):
        import tempfile
        from unittest import mock
        old = m._JOINT_PARALLEL
        m._JOINT_PARALLEL = False
        try:
            tr = {"active": 0, "max": 0, "seats": []}
            with tempfile.TemporaryDirectory() as d,                  mock.patch.object(m, "_load_dimension_table", return_value={
                     "table_version": "v1", "status": "ready", "seats": self._table()}),                  mock.patch.object(m, "_deepseek_balance_cny", return_value=None),                  mock.patch.object(m, "_spawn_seat", side_effect=self._spawn_factory(tr)):
                rc, out = m.run(self._args(d))
                self.assertEqual(rc, 0)
                self.assertEqual(tr["max"], 1)                  # ⑤回退=串行
                self.assertFalse(out.get("parallel"))
        finally:
            m._JOINT_PARALLEL = old


class AnchorPanelTest(unittest.TestCase):
    """T1/T7：共维锚独立面板（main 聚合零动·spread 告警·不入判级）。"""

    def test_anchor_panel_and_spread_warning(self):
        import argparse, io as _io, contextlib
        from unittest import mock
        anchors = [{"id": f"anchor-{k}", "name": f"A{k}", "definition": "d", "object_scope": "both"}
                   for k in (1, 2, 3)]
        seats = {s: {"dimensions": [
            {"id": f"{s}-{k}", "name": "n", "definition": "d", "object_scope": "both"}
            for k in (1, 2, 3)]} for s in m.SEATS}

        def fake(seat, rd, rid, timeout_s=900, extra_hint="", prompt_head=None, prompt_override=None):
            score = 90 if seat in ("cos", "coo") else 50     # anchor-1 spread=40>30
            sheet = {"seat": seat,
                     "dimensions": [{"dimension_id": f"{seat}-1", "object": "A", "score": 80},
                                    {"dimension_id": "anchor-1", "object": "A", "score": score}],
                     "improvements": [{"title": "t", "target": "plan.json", "change": "c",
                                       "verify": "v", "rollback": "r", "owner_seat": seat}]}
            return {"rc": 0, "out": json.dumps(sheet), "err": ""}

        rd = Path(tempfile.mkdtemp())
        err = _io.StringIO()
        with mock.patch.object(m, "_load_dimension_table", return_value={
                "table_version": "v1", "status": "ready", "seats": seats,
                "anchor_dimensions": anchors}),              mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              mock.patch.object(m, "_spawn_seat", side_effect=fake),              contextlib.redirect_stderr(err):
            rc, out = m.run(argparse.Namespace(run_dir=str(rd), run_id="anc", spawn_timeout=5))
        self.assertEqual(rc, 0)
        jr = json.loads((rd / "joint-review.json").read_text(encoding="utf-8"))
        ap = jr.get("anchor_dimensions") or {}
        self.assertEqual(ap.get("agg_version"), "1.0.0")
        self.assertEqual(ap.get("dim_ids"), ["anchor-1", "anchor-2", "anchor-3"])
        self.assertEqual(ap.get("spread", {}).get("anchor-1"), 40)      # 90-50
        self.assertIn("anchor spread>30", err.getvalue())               # 告警留痕
        # main 聚合零动：anchor 分不进 dims_count
        self.assertEqual(jr.get("dims_count", {}).get("a"), len(m.SEATS))  # 每席仅 1 条 main A 分
        self.assertIn("not in scoring", ap.get("note", ""))


class RationalePassthroughTest(unittest.TestCase):
    """DP-049：席面 rationale 随条目透传 joint-review dims（无则不注）。"""

    def _run(self, with_rationale: bool):
        import argparse
        from unittest import mock
        seats = {s: {"dimensions": [
            {"id": f"{s}-{k}", "name": "n", "definition": "d", "object_scope": "both"}
            for k in (1, 2, 3)]} for s in m.SEATS}

        def fake(seat, rd, rid, timeout_s=900, extra_hint="", prompt_head=None, prompt_override=None):
            d = {"dimension_id": f"{seat}-1", "object": "A", "score": 80}
            if with_rationale:
                d["rationale"] = f"理据-{seat}"
            return {"rc": 0, "out": json.dumps({"seat": seat, "dimensions": [d],
                                                "improvements": []}), "err": ""}

        rd = Path(tempfile.mkdtemp())
        with mock.patch.object(m, "_load_dimension_table", return_value={
                "table_version": "v1", "status": "ready", "seats": seats}),              mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              mock.patch.object(m, "_spawn_seat", side_effect=fake):
            rc, out = m.run(argparse.Namespace(run_dir=str(rd), run_id="rat", spawn_timeout=5))
        return json.loads((rd / "joint-review.json").read_text(encoding="utf-8"))

    def test_rationale_passthrough(self):
        jr = self._run(True)
        dims = (jr["faces"][m.SEATS[0]].get("dimensions") or [])
        self.assertEqual(dims[0].get("rationale"), f"理据-{m.SEATS[0]}")

    def test_no_rationale_no_key(self):
        jr = self._run(False)
        dims = (jr["faces"][m.SEATS[0]].get("dimensions") or [])
        self.assertNotIn("rationale", dims[0])


if __name__ == "__main__":
    unittest.main()
