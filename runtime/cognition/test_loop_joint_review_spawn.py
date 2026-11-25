"""loop_joint_review_spawn 单测（CTO 裁 2026-11-23：可比性系数随卷落·附卷不并入判级）。"""
from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
from unittest import mock
import os as _os_ab
_os_ab.environ.setdefault("LOOP_JOINT_AB_STRICT", "0")   # T1b 严校验由 T1bABColumnsTest 直测·legacy 形回退
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


class LiteModeTest(unittest.TestCase):
    """v8 item13 lite 直提（CPO spec 五断言：无维分拒/双锚拒/全纳/mode 字段/回滚）。"""

    def _run(self, *, mode="lite", sheet_by_seat=None, env_off=False, d=None):
        import argparse, os as _os
        sheet_by_seat = sheet_by_seat or {}
        def fake_spawn(seat, run_dir, run_id, timeout_s=None, prompt_override=None, **kw):
            sheet = sheet_by_seat.get(seat, {"items": [
                {"claim": f"{seat}-改", "gap_type": "改进", "evidence_ref": "x.json"}]})
            return {"rc": 0, "out": json.dumps(sheet), "err": ""}
        args = argparse.Namespace(run_dir=str(d), run_id="r1", spawn_timeout=5, review_mode=mode)
        prev = _os.environ.pop("LOOP_JOINT_REVIEW_LITE", None)
        if env_off:
            _os.environ["LOOP_JOINT_REVIEW_LITE"] = "0"
        try:
            _tbl = {"table_version": "v1", "status": "ready",
                    "anchor_dimensions": [], "seats": {
                        s: {"dimensions": [{"id": f"{s}-{k}", "name": "n", "definition": "d",
                                            "object_scope": "both"} for k in (1, 2, 3)]}
                            for s in m.SEATS}}
            with mock.patch.object(m, "_load_dimension_table", return_value=_tbl),                  mock.patch.object(m, "_deepseek_balance_cny", return_value=None),                  mock.patch.object(m, "_spawn_seat", side_effect=fake_spawn):
                return m.run(args)
        finally:
            if env_off:
                _os.environ.pop("LOOP_JOINT_REVIEW_LITE", None)
            if prev is not None:
                _os.environ["LOOP_JOINT_REVIEW_LITE"] = prev

    def test_assert1_no_dims_failclosed(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self._run(d=d, sheet_by_seat={"cos": {"dimensions": {"x": 1}}})
            cosf = out["faces"]["cos"]
            self.assertTrue(cosf.get("absent"))
            self.assertIn("模式隔离", str(cosf.get("reason")))

    def test_assert2_double_anchor_failclosed(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self._run(d=d, sheet_by_seat={"coo": {"items": [
                {"claim": "x", "evidence_ref": ""}]}})
            self.assertTrue(out["faces"]["coo"].get("absent"))
            self.assertIn("双锚", str(out["faces"]["coo"].get("reason")))

    def test_assert3_full_inclusion(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self._run(d=d)
            self.assertEqual(code, 0)
            ops = json.loads(Path(d, "opinions.json").read_text(encoding="utf-8"))
            self.assertEqual(len(ops["opinions"]), 7)      # 七席×1 条全纳（无截断）
            self.assertEqual(out["opinions_total"], 7)
            jr = json.loads(Path(d, "joint-review.json").read_text(encoding="utf-8"))
            self.assertEqual(jr["review_mode"], "lite")
            self.assertEqual(jr["opinions_total"], 7)
            self.assertEqual(jr["dims_count"], {"a": 0, "b": 0})   # 不进聚合

    def test_assert4_env_off_forces_full(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self._run(d=d, mode="lite", env_off=True)
            self.assertEqual(out.get("review_mode"), "full")

    def test_assert5_lite_rollback_field(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self._run(d=d)
            self.assertEqual(out.get("review_mode"), "lite")
            self.assertTrue(Path(d, "opinions-lite.json").is_file())


class LowDimCoverageTest(unittest.TestCase):
    """件2（CEO 批）：低分维<70 强制逐维一条——对表防再丢。"""

    def _dim(self, did, score):
        return {"dimension_id": did, "object": "a", "score": score}

    def test_three_low_dims_three_opinions_mapped(self):
        faces = {"cos": {
            "dimensions": [self._dim("d1", 40), self._dim("d2", 55), self._dim("d3", 60)],
            "improvements": [{"title": "x", "dimension_id": "d1"},
                             {"title": "y", "dimension_id": "d2"},
                             {"title": "z", "dimension_id": "d3"}]}}
        cov = m._low_dim_coverage(faces)
        self.assertEqual(cov["low_dim_count"], 3)
        self.assertEqual(cov["opinion_count"], 3)
        self.assertEqual(cov["mapped_low_dims"], 3)
        self.assertEqual(cov["uncovered"], [])

    def test_uncovered_low_dim_recorded(self):
        faces = {"coo": {
            "dimensions": [self._dim("d1", 30), self._dim("d2", 65)],
            "improvements": [{"title": "only-d1", "dimension_id": "d1"}]}}
        cov = m._low_dim_coverage(faces)
        self.assertEqual(cov["low_dim_count"], 2)
        self.assertEqual(len(cov["uncovered"]), 1)
        self.assertEqual(cov["uncovered"][0]["dimension_id"], "d2")

    def test_prompt_states_mandatory_rule(self):
        dims = [{"id": "d1", "name": "n", "definition": "d", "object_scope": "both"}]
        pr = m._constrained_prompt("cos", dims)
        self.assertIn("每维 score<70", pr)
        self.assertIn("条数不限", pr)
        self.assertIn("dimension_id", pr)


class LowDimGateTest(unittest.TestCase):
    """c 主修（CTO 令 2026-11-25）：低分维无对应改进=门 fail（r33 根因回归）。"""

    def _faces(self, dims, imps):
        return {"cos": {"dimensions": dims, "improvements": imps}}

    def test_low_dims_without_improvements_fails(self):
        faces = self._faces([{"dimension_id": "d1", "object": "a", "score": 40}], [])
        g = m._low_dim_gate(faces)
        self.assertFalse(g["ok"])
        self.assertIn("低分维无对应改进", g["reason"])

    def test_low_dims_with_matched_improvement_passes(self):
        faces = self._faces([{"dimension_id": "d1", "object": "a", "score": 40}],
                            [{"title": "x", "dimension_id": "d1"}])
        self.assertTrue(m._low_dim_gate(faces)["ok"])

    def test_no_low_dims_no_improvement_passes(self):
        faces = self._faces([{"dimension_id": "d1", "object": "a", "score": 88}],
                            [{"title": "no-improvement"}])
        self.assertTrue(m._low_dim_gate(faces)["ok"])

    def test_run_level_fail_when_uncovered(self):
        """run() 层面：低分维+0 意见 → rc=2 且 joint-review.json 已落卷（落卷照旧+拦）。"""
        import tempfile as _tf
        from unittest import mock as _mock
        d = Path(_tf.mkdtemp())
        def fake(seat, run_dir, run_id, timeout_s=None, prompt_override=None, **kw):
            return {"rc": 0, "out": json.dumps({
                "seat": seat,
                "dimensions": [{"dimension": f"{seat}-1", "dimension_id": f"{seat}-1",
                                "object": "A", "score": 40, "rationale": "L2"}],
                "improvements": []}), "err": ""}
        tbl = {"table_version": "v1", "status": "ready", "anchor_dimensions": [], "seats": {
            s: {"dimensions": [{"id": f"{s}-{k}", "name": "n", "definition": "d",
                                "object_scope": "both"} for k in (1, 2, 3)]} for s in m.SEATS}}
        import argparse
        args = argparse.Namespace(run_dir=str(d), run_id="r33", spawn_timeout=5,
                                  review_mode="full")
        with _mock.patch.object(m, "_load_dimension_table", return_value=tbl),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              _mock.patch.object(m, "_spawn_seat", side_effect=fake):
            code, out = m.run(args)
        self.assertEqual(code, 2)
        self.assertIn("低分维无对应改进", str(out.get("verdict")))
        self.assertTrue(Path(d, "joint-review.json").is_file())


class T1aPerSeatTraceTest(unittest.TestCase):
    """T1a（任务书 e0dfa6481）：七席独立落卷不合订+回填 N 进 N 出。"""

    def _run(self, d, imps_per_seat=2):
        import argparse
        from unittest import mock as _mock
        def fake(seat, run_dir, run_id, timeout_s=None, prompt_override=None, **kw):
            imps = [{"title": f"{seat}-T{i}", "target": f"src/{seat}{i}.ts",
                     "change": "c", "verify": "v", "rollback": "r"} for i in range(imps_per_seat)]
            return {"rc": 0, "out": json.dumps({"seat": seat, "dimensions": [
                {"dimension": f"{seat}-1", "dimension_id": f"{seat}-1", "object": "A",
                 "score": 88, "rationale": "L4"}], "improvements": imps}), "err": ""}
        tbl = {"table_version": "v1", "status": "ready", "anchor_dimensions": [], "seats": {
            s: {"dimensions": [{"id": f"{s}-{k}", "name": "n", "definition": "d",
                                "object_scope": "both"} for k in (1, 2, 3)]} for s in m.SEATS}}
        args = argparse.Namespace(run_dir=str(d), run_id="t1a", spawn_timeout=5, review_mode="full")
        with _mock.patch.object(m, "_load_dimension_table", return_value=tbl),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              _mock.patch.object(m, "_spawn_seat", side_effect=fake):
            return m.run(args)

    def test_per_seat_files_and_unmerged_opinions(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        code, out = self._run(d)
        self.assertEqual(code, 0)
        for seat in m.SEATS:
            self.assertTrue((d / f"opinions-{seat}.json").is_file(), seat)   # 7 席独立卷保留
        ops = json.loads((d / "opinions.json").read_text(encoding="utf-8"))["opinions"]
        self.assertEqual(len(ops), 14)                        # 7×2 逐改善条目化（非 7 合订）
        seats = {o["owner_seat"] for o in ops}
        self.assertEqual(seats, set(m.SEATS))                 # 七席溯源齐
        self.assertEqual(len({o["opinion_id"] for o in ops}), 14)

    def test_refill_n_into_m(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        prev = base / "prev-run"; prev.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({"opinions_total": 10}),
                                                encoding="utf-8")
        cur = base / "cur-run"; cur.mkdir()
        code, out = self._run(cur)
        jr = json.loads((cur / "joint-review.json").read_text(encoding="utf-8"))
        self.assertEqual(jr["refill"]["prev_run"], "prev-run")
        self.assertEqual(jr["refill"]["prev_total"], 10)
        self.assertEqual(jr["refill"]["current_total"], 14)
        self.assertTrue(jr["refill"]["ok"])                   # N 进（10）M 出（14）守恒


class T1bABColumnsTest(unittest.TestCase):
    """T1b（任务书 e0dfa6481）：A/B 双列独立·两列必齐·不共用 rationale。"""

    def _dims(self):
        return [{"id": "d-both", "name": "n", "object_scope": "both"},
                {"id": "d-a", "name": "n2", "object_scope": "A"}]

    def test_missing_b_column_violation(self):
        entries = [{"dimension_id": "d-both", "object": "A", "score": 80},
                   {"dimension_id": "d-a", "object": "A", "score": 70}]
        viol = m._check_ab_columns(entries, self._dims())
        self.assertTrue(any("B 列缺" in v for v in viol))

    def test_both_columns_and_no_shared_rationale(self):
        entries = [{"dimension_id": "d-both", "object": "A", "score": 80, "rationale": "ra"},
                   {"dimension_id": "d-both", "object": "B", "score": 75, "rationale": "rb"},
                   {"dimension_id": "d-a", "object": "A", "score": 70, "rationale": "rc"}]
        self.assertEqual(m._check_ab_columns(entries, self._dims()), [])

    def test_duplicate_and_shared_rationale_violations(self):
        entries = [{"dimension_id": "d-both", "object": "A", "score": 80, "rationale": "same"},
                   {"dimension_id": "d-both", "object": "A", "score": 81, "rationale": "same"},
                   {"dimension_id": "d-both", "object": "B", "score": 75, "rationale": "same"}]
        viol = m._check_ab_columns(entries, self._dims())
        self.assertTrue(any("重复" in v for v in viol))
        self.assertTrue(any("同一串" in v for v in viol))

    def test_prompt_states_ab_independence(self):
        dims = [{"id": "d1", "name": "n", "definition": "d", "object_scope": "both"}]
        pr = m._constrained_prompt("cos", dims)
        self.assertIn("A/B 双列独立", pr)
        self.assertIn("禁只打一栏", pr)


class T1cRefillItemsTest(unittest.TestCase):
    """T1c（任务书 e0dfa6481·与 T6 合并）：上轮 N 条逐条结账（done/deferred/dropped·缺=missing）。"""

    def _run(self, d, settle_map):
        import argparse
        from unittest import mock as _mock
        def fake(seat, run_dir, run_id, timeout_s=None, prompt_override=None, **kw):
            imps = []
            for prev_id, st in settle_map.get(seat, []):
                imps.append({"title": f"{seat}-{prev_id}-fix", "target": f"src/{seat}-{prev_id}.ts",
                             "change": "c", "verify": "v", "rollback": "r",
                             "settles": prev_id, "status": st, "reason": "why"})
            if not imps:
                imps.append({"title": f"{seat}-T0", "target": f"src/{seat}0.ts",
                             "change": "c", "verify": "v", "rollback": "r"})
            return {"rc": 0, "out": json.dumps({"seat": seat, "dimensions": [
                {"dimension": f"{seat}-1", "dimension_id": f"{seat}-1", "object": "A",
                 "score": 88, "rationale": "L4"}], "improvements": imps}), "err": ""}
        tbl = {"table_version": "v1", "status": "ready", "anchor_dimensions": [], "seats": {
            s: {"dimensions": [{"id": f"{s}-{k}", "name": "n", "definition": "d",
                                "object_scope": "both"} for k in (1, 2, 3)]} for s in m.SEATS}}
        args = argparse.Namespace(run_dir=str(d), run_id="t1c", spawn_timeout=5, review_mode="full")
        with _mock.patch.object(m, "_load_dimension_table", return_value=tbl),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              _mock.patch.object(m, "_spawn_seat", side_effect=fake):
            return m.run(args)

    def _prev(self, base, ids):
        prev = base / "prev-run"; prev.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({"opinions_total": len(ids)}),
                                                encoding="utf-8")
        (prev / "opinions.json").write_text(json.dumps({"opinions": [
            {"opinion_id": i, "title": f"prev-{i}"} for i in ids]}), encoding="utf-8")
        return prev

    def test_all_prev_items_settled(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        self._prev(base, ["p1", "p2"])
        cur = base / "cur-run"; cur.mkdir()
        code, out = self._run(cur, {"cos": [("p1", "done")], "coo": [("p2", "deferred")]})
        jr = json.loads((cur / "joint-review.json").read_text(encoding="utf-8"))
        rf = jr["refill"]
        self.assertEqual(len(rf["items"]), 2)                     # 逐条可查
        self.assertEqual([x["status"] for x in rf["items"]], ["done", "deferred"])
        self.assertEqual(rf["missing"], [])
        self.assertTrue(rf["items_ok"])
        self.assertIn("prev_total", rf)                           # 总数表并存

    def test_missing_settlement_recorded(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        self._prev(base, ["p1", "p2"])
        cur = base / "cur-run2"; cur.mkdir()
        code, out = self._run(cur, {"cos": [("p1", "done")]})     # p2 未结账
        jr = json.loads((cur / "joint-review.json").read_text(encoding="utf-8"))
        rf = jr["refill"]
        self.assertEqual(rf["missing"], ["p2"])
        self.assertFalse(rf["items_ok"])
        carried = [x for x in rf["items"] if x["status"] == "carried"]
        self.assertEqual(len(carried), 1)


class ObjectCaseNormalizeTest(unittest.TestCase):
    """r34 第四修（CTO 令）：object 小写归一 valid（非 fail）·大写照旧。"""

    def _dims(self):
        return [{"id": "d1", "name": "n", "object_scope": "both"},
                {"id": "d2", "name": "n2", "object_scope": "A"}]

    def test_lowercase_normalized_valid(self):
        entries = [{"dimension_id": "d1", "object": "a", "score": 80},
                   {"dimension_id": "d1", "object": "b", "score": 75},
                   {"dimension_id": "d2", "object": "a", "score": 70}]
        ok, viol = m._validate_seat_scores(entries, self._dims())
        self.assertEqual(viol, [])
        self.assertEqual(len(ok), 3)
        self.assertEqual({e["object"] for e in ok}, {"A", "B"})

    def test_uppercase_unchanged(self):
        entries = [{"dimension_id": "d1", "object": "A", "score": 80},
                   {"dimension_id": "d1", "object": "B", "score": 75}]
        ok, viol = m._validate_seat_scores(entries, self._dims())
        self.assertEqual(viol, [])
        self.assertEqual(len(ok), 2)


class FilteredInvalidTraceTest(unittest.TestCase):
    """落痕修（CTO 核令 2026-11-25）：五字段不全被过滤条目显式记（r34 72→64 类不再静默）。"""

    def test_invalid_improvement_recorded(self):
        import argparse, tempfile as _tf
        from unittest import mock as _mock
        d = Path(_tf.mkdtemp())
        def fake(seat, run_dir, run_id, timeout_s=None, prompt_override=None, **kw):
            imps = [{"title": "ok-1", "target": "src/a.ts", "change": "c", "verify": "v", "rollback": "r"},
                    {"title": "bad-1", "target": "src/b.ts"}]           # 缺 change/verify/rollback
            return {"rc": 0, "out": json.dumps({"seat": seat, "dimensions": [
                {"dimension": f"{seat}-1", "dimension_id": f"{seat}-1", "object": "A",
                 "score": 88, "rationale": "L4"}], "improvements": imps}), "err": ""}
        tbl = {"table_version": "v1", "status": "ready", "anchor_dimensions": [], "seats": {
            s: {"dimensions": [{"id": f"{s}-{k}", "name": "n", "definition": "d",
                                "object_scope": "both"} for k in (1, 2, 3)]} for s in m.SEATS}}
        args = argparse.Namespace(run_dir=str(d), run_id="ft", spawn_timeout=5, review_mode="full")
        with _mock.patch.object(m, "_load_dimension_table", return_value=tbl),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              _mock.patch.object(m, "_spawn_seat", side_effect=fake):
            code, out = m.run(args)
        jr = json.loads((d / "joint-review.json").read_text(encoding="utf-8"))
        fi = jr.get("opinions_filtered_invalid") or []
        self.assertTrue(fi)
        self.assertEqual(len([x for x in fi if x["title"] == "bad-1"]), len(m.SEATS))
        self.assertIn("change", fi[0]["missing"])
        ops = json.loads((d / "opinions.json").read_text(encoding="utf-8"))["opinions"]
        self.assertTrue(all(o.get("title") == "ok-1" for o in ops))


class S8EvidenceTest(unittest.TestCase):
    """S8（r36 任务书·CTO 令）：证据去模板化/同源抽查 + spawn-vs-CLI 等效回归。"""

    def _faces(self, evs):
        return {"cos": {"improvements": [{"title": f"T{i}", "target": e, "evidence_ref": e}
                                         for i, e in enumerate(evs)]}}

    def test_generic_evidence_violation(self):
        d = Path(".")
        r = m._evidence_check(self._faces(["run_dir/", "<path>", "plan"]), d)
        self.assertFalse(r["ok"])
        self.assertTrue(any("泛化" in v for v in r["violations"]))
        self.assertTrue(any("占位形" in v for v in r["violations"]))
        self.assertTrue(any("无具体文件名" in v for v in r["violations"]))

    def test_concrete_evidence_passes_with_sampling(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "dce.json").write_text("{}", encoding="utf-8")
        (d / "plan.json").write_text("{}", encoding="utf-8")
        r = m._evidence_check(self._faces(["dce.json", "plan.json:3"]), d)
        self.assertTrue(r["ok"], r["violations"])
        self.assertEqual(len(r["sampled_sources"]), 2)
        self.assertTrue(all(s["exists"] for s in r["sampled_sources"]))

    def test_spawn_vs_cli_equivalence(self):
        # 同一输入两路：spawn 面（lower/upper 混排）与 CLI 面（规范大写）经同一校验器 →
        # 归一化输出一致（等效性回归·允许形差已归一）
        dims = [{"id": "d1", "name": "n", "object_scope": "both"}]
        via_spawn = [{"dimension_id": "d1", "object": "a", "score": 80},
                     {"dimension_id": "d1", "object": "B", "score": 70}]
        via_cli = [{"dimension_id": "d1", "object": "A", "score": 80},
                   {"dimension_id": "d1", "object": "B", "score": 70}]
        ok1, v1 = m._validate_seat_scores(via_spawn, dims)
        ok2, v2 = m._validate_seat_scores(via_cli, dims)
        norm1 = sorted((e["dimension_id"], e["object"], e["score"]) for e in ok1)
        norm2 = sorted((e["dimension_id"], e["object"], e["score"]) for e in ok2)
        self.assertEqual(v1, [])
        self.assertEqual(v2, [])
        self.assertEqual(norm1, norm2)


class A1LedgerRefillTest(unittest.TestCase):
    """A1（CEO 批任务书 §6.2③）：refill 消费结账表——fixed 优先·缺表 graceful。"""

    def _run(self, d):
        import argparse
        from unittest import mock as _mock
        def fake(seat, run_dir, run_id, timeout_s=None, prompt_override=None, **kw):
            return {"rc": 0, "out": json.dumps({"seat": seat, "dimensions": [
                {"dimension": f"{seat}-1", "dimension_id": f"{seat}-1", "object": "A",
                 "score": 88, "rationale": "L4"}], "improvements": [
                {"title": f"{seat}-fix", "target": f"src/{seat}.ts", "change": "c",
                 "verify": "v", "rollback": "r"}]}), "err": ""}
        tbl = {"table_version": "v1", "status": "ready", "anchor_dimensions": [], "seats": {
            s: {"dimensions": [{"id": f"{s}-{k}", "name": "n", "definition": "d",
                                "object_scope": "both"} for k in (1, 2, 3)]} for s in m.SEATS}}
        args = argparse.Namespace(run_dir=str(d), run_id="a1", spawn_timeout=5, review_mode="full")
        with _mock.patch.object(m, "_load_dimension_table", return_value=tbl),              _mock.patch.object(m, "_deepseek_balance_cny", return_value=None),              _mock.patch.object(m, "_spawn_seat", side_effect=fake):
            return m.run(args)

    def _prev(self, base):
        prev = base / "prev-run"; prev.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({"opinions_total": 2}), encoding="utf-8")
        (prev / "opinions.json").write_text(json.dumps({"opinions": [
            {"opinion_id": "p-fixed", "title": "T1"},
            {"opinion_id": "p-open", "title": "T2"}]}), encoding="utf-8")
        return prev

    def test_ledger_fixed_wins(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        self._prev(base)
        cur = base / "cur-run"; cur.mkdir()
        (cur / "acceptance-ledger-r36-s4s8-20261125.json").write_text(json.dumps({"items": [
            {"opinion_id": "p-fixed", "status": "fixed", "evidence": "dce.json:12",
             "verified_by": "cto", "verified_at": "2026-11-25"}]}), encoding="utf-8")
        self._run(cur)
        jr = json.loads((cur / "joint-review.json").read_text(encoding="utf-8"))
        items = {i["prev_opinion_id"]: i for i in jr["refill"]["items"]}
        self.assertEqual(items["p-fixed"]["status"], "fixed")
        self.assertEqual(items["p-fixed"]["evidence"], "dce.json:12")
        self.assertEqual(items["p-open"]["status"], "carried")   # 表外件照旧

    def test_no_ledger_graceful(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        self._prev(base)
        cur = base / "cur2"; cur.mkdir()
        self._run(cur)
        jr = json.loads((cur / "joint-review.json").read_text(encoding="utf-8"))
        sts = [i["status"] for i in jr["refill"]["items"]]
        self.assertEqual(sorted(sts), ["carried", "carried"])

    def test_malformed_ledger_graceful(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        self._prev(base)
        cur = base / "cur3"; cur.mkdir()
        (cur / "acceptance-ledger-bad.json").write_text("not json", encoding="utf-8")
        self._run(cur)
        jr = json.loads((cur / "joint-review.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(i["status"] for i in jr["refill"]["items"]),
                         ["carried", "carried"])


if __name__ == "__main__":
    unittest.main()
