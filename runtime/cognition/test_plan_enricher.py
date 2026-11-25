"""plan_enricher 单测（DP-20261123-018 item1-4/6·charter-060521Z 泛化形）。"""
from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
from pathlib import Path

from runtime.cognition import plan_enricher as m


def _mk_tree(root: Path, name: str, files: dict[str, str], with_op: bool = True) -> Path:
    d = root / name
    d.mkdir(parents=True)
    for fn, content in files.items():
        (d / fn).write_text(content, encoding="utf-8")
    if with_op:
        (d / "tree-op.json").write_text('{"a":1}', encoding="utf-8")
    return d


class EnrichPlanTest(unittest.TestCase):
    def _fixture(self):
        tmv = Path(tempfile.mkdtemp())
        op = tmv / "docs" / "workflow" / "operating-records"
        w47 = op / "2026-W47"
        w48 = op / "2026-W48"
        tr47 = w47 / "trees"
        tr47.mkdir(parents=True)
        _mk_tree(tr47, "t1", {"a.md": "x"})
        _mk_tree(tr47, "t2", {"b.md": "yy"}, with_op=False)
        _mk_tree(tr47, "bod-tick", {"c.md": "z"})
        tr48 = w48 / "trees"
        tr48.mkdir(parents=True)
        (tr48 / "alpha").mkdir()
        (tr48 / "beta").mkdir()
        (w48 / "round-gate-sop-x.md").write_text("loose", encoding="utf-8")
        (w48 / "OP-202611-W48-001.json").write_text("{}", encoding="utf-8")
        run_dir = Path(tempfile.mkdtemp())
        plan = {
            "from_week": "W47", "to_week": "W48",
            "keep": [{"item_id": "t1"}, {"item_id": "t2"}],
            "migrate": [{"item_id": "bod-tick"}],
            "carry_over": [{"item_id": "C1", "owner": "CTO"}],
            "families": [
                {"family_id": "A", "items": [{"item_id": "A1"}, {"item_id": "E1"}]},
                {"family_id": "F", "items": [{"item_id": "F2"}, {"item_id": "F3"}]},
            ],
        }
        return plan, run_dir, str(tmv)

    def test_enrich_full(self):
        plan, run_dir, tmv = self._fixture()
        stats = m.enrich_plan(plan, run_dir, tmv)
        # ① tree-facts 六字段
        tf = json.loads((run_dir / "tree-facts.json").read_text(encoding="utf-8"))
        self.assertEqual(set(tf["trees"]), {"t1", "t2", "bod-tick"})
        for v in tf["trees"].values():
            for k in ("path", "file_count", "total_bytes", "tree_op_size", "sha256_16", "mtime"):
                self.assertIn(k, v)
        self.assertEqual(len(tf["trees"]["t1"]["sha256_16"]), 16)
        self.assertEqual(stats["tree_facts"], 3)
        # ② observed 注入
        self.assertEqual(plan["keep"][0]["observed"]["file_count"], 2)   # a.md + tree-op.json
        self.assertEqual(plan["keep"][0]["confidence"], "high")
        self.assertEqual(plan["keep"][1]["confidence"], "high")
        # ③ 动态周键名 backfill/loose
        ia = plan["index_assertions"]
        self.assertEqual(ia["w48_backfill_ids"], ["alpha", "beta"])
        self.assertEqual(ia["w48_loose_files"], ["round-gate-sop-x.md"])   # OP-* 排除
        self.assertEqual(ia["w48_expected_active_count"], 2)
        # ④ families owner 映射（charter 镜像）
        fam_items = {it["item_id"]: it for f in plan["families"] for it in f["items"]}
        self.assertEqual(fam_items["A1"]["owner"], "COS")
        self.assertEqual(fam_items["E1"]["owner"], "COS")
        self.assertEqual(fam_items["F2"]["owner"], "CPO")
        self.assertEqual(fam_items["F2"]["due"], "2026-11-23")
        self.assertEqual(fam_items["F3"]["owner"], "CAO")
        for it in fam_items.values():
            for k in ("owner", "timebox", "acceptance", "depends_on"):
                self.assertIn(k, it)
        # ⑤ raci（3 项 + 1 散件）
        self.assertEqual(stats["raci_items"], 4)
        self.assertTrue(plan["staffing"]["raci"]["t1"]["accountable"])
        self.assertIn("round-gate-sop-x.md", plan["staffing"]["raci"])
        # ⑥ carry_over accountable 单席
        self.assertEqual(plan["carry_over"][0]["accountable"], "CTO")
        self.assertEqual(plan["carry_over"][0]["consulted"], ["COS"])

    def test_no_tmv_root_skips_gracefully(self):
        plan, run_dir, _ = self._fixture()
        stats = m.enrich_plan(plan, run_dir, None)
        self.assertTrue(stats["errors"])
        self.assertEqual(stats["tree_facts"], 0)
        # tree-facts 文件仍落（空 trees·as-is 记录）
        tf = json.loads((run_dir / "tree-facts.json").read_text(encoding="utf-8"))
        self.assertEqual(tf["trees"], {})

    def test_missing_week_dirs_no_crash(self):
        plan, run_dir, tmv = self._fixture()
        plan["from_week"] = "W99"
        plan["to_week"] = "W98"
        stats = m.enrich_plan(plan, run_dir, tmv)
        self.assertEqual(stats["tree_facts"], 0)
        self.assertEqual(plan["index_assertions"]["w98_backfill_ids"], [])


class TimingFieldsTest(unittest.TestCase):
    """DP-036/coo-1（charter-150927Z）：plan 时标倒序修正——高级字段面 + check_time 实测源。"""

    def _run(self):
        fixture = EnrichPlanTest()
        plan, run_dir, tmv = fixture._fixture()
        stats = m.enrich_plan(plan, run_dir, tmv)
        return plan, run_dir, stats, json.loads((run_dir / "tree-facts.json").read_text(encoding="utf-8"))

    def test_advanced_fields_present_and_nonnull(self):
        plan, _rd, _st, tf = self._run()
        for key in ("hard_clock", "batch_timetable", "stop_loss", "rollback_order",
                    "self_checks", "resume_dedup", "window_conflicts"):
            self.assertIn(key, plan)
            self.assertTrue(plan[key], key)          # 非空
        self.assertEqual(plan["check_time"], tf["generated_at"])   # 实测源
        self.assertEqual(plan["hard_clock"]["source"][:14], "tree-facts.gen")

    def test_items_timing_and_evidence(self):
        plan, _rd, _st, tf = self._run()
        for item in plan["keep"] + plan["migrate"]:
            self.assertIn("actual_landed_at", item)
            self.assertTrue(str(item["evidence_ref"]).startswith("tree-facts.json#/"))
            self.assertTrue(item.get("owner"))
        for i, co in enumerate(plan["carry_over"]):
            self.assertIn("actual_landed_at", co)
            self.assertEqual(co["evidence_ref"], f"plan.json#/carry_over/{i}")

    def test_observed_items_use_measured_time_not_tree_mtime(self):
        # v8 item2：树时间戳不冒充——actual=tree-facts.generated_at（采集实测时点）
        plan, _rd, _st, tf = self._run()
        item = plan["keep"][0]
        self.assertEqual(item["actual_landed_at"], tf["generated_at"])
        self.assertNotEqual(item["actual_landed_at"], tf["trees"][item["item_id"]]["mtime"])

    def test_window_conflicts_over_480(self):
        # v8 item2：cost-log 段耗时>480s 入 window_conflicts（实测对表·tmv 面走全流程）
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        import json as _j
        (run_dir / "cost-log.jsonl").write_text(chr(10).join([
            _j.dumps({"stage": "plan_skill", "started": "2026-11-24T00:00:00+00:00",
                      "finished": "2026-11-24T00:03:00+00:00"}),
            _j.dumps({"stage": "score_skill", "started": "2026-11-24T00:00:00+00:00",
                      "finished": "2026-11-24T00:12:00+00:00"}),   # 720s > 480
        ]), encoding="utf-8")
        m.enrich_plan(plan, run_dir, tmv)
        conflicts = (plan.get("window_conflicts") or {}).get("conflicts") or []
        self.assertTrue(any(c.get("stage") == "score_skill" and c.get("overrun_s") and c["overrun_s"] > 480
                            for c in conflicts))
        # actual 双录：plan_skill 180s 不入冲突
        self.assertFalse(any(c.get("stage") == "plan_skill" for c in conflicts))


class PlanFreezeTest(unittest.TestCase):
    """v8 item9：plan-freeze.json 每树四字段（+source_path 复算锚）。"""

    def test_freeze_four_fields(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        m.enrich_plan(plan, run_dir, tmv)
        fz = json.loads((run_dir / "plan-freeze.json").read_text(encoding="utf-8"))
        self.assertEqual(len(fz["trees"]), 3)
        for ent in fz["trees"]:
            for k in ("tree_id", "md5", "size", "counts", "source_path"):
                self.assertIn(k, ent)
            self.assertEqual(len(ent["md5"]), 32)


class PatrolPlanTest(unittest.TestCase):
    """v8 item11（plan 侧）：值守计划 {who, cadence, window} 登记（close 侧对表待同文件 pop）。"""

    def test_patrol_plan_fields(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        m.enrich_plan(plan, run_dir, tmv)
        pp = plan.get("patrol_plan") or {}
        for k in ("who", "window"):
            self.assertTrue(pp.get(k), k)
        layers = pp.get("cadence_layers") or {}
        self.assertEqual(layers.get("bod_patrol", {}).get("cadence"), "6m")
        self.assertTrue(layers.get("duty_patrol", {}).get("cadence"))

    def test_patrol_bod_default_six_and_env_override(self):
        import os as _os
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        m.enrich_plan(plan, run_dir, tmv)
        bod = ((plan.get("patrol_plan") or {}).get("cadence_layers") or {}).get("bod_patrol")
        self.assertEqual(bod.get("cadence"), "6m")     # 默认 6m（CEO 拍读令）
        plan2, run_dir2, tmv2 = fx._fixture()
        old = _os.environ.get("FADE_PATROL_CADENCE")
        _os.environ["FADE_PATROL_CADENCE"] = "9m"
        try:
            m.enrich_plan(plan2, run_dir2, tmv2)
        finally:
            if old is None:
                _os.environ.pop("FADE_PATROL_CADENCE", None)
            else:
                _os.environ["FADE_PATROL_CADENCE"] = old
        duty = ((plan2.get("patrol_plan") or {}).get("cadence_layers") or {}).get("duty_patrol")
        self.assertEqual(duty.get("cadence"), "9m")    # env 覆盖生效（duty 层）


class T3aFreezeHashesTest(unittest.TestCase):
    """T3a（任务书 e0dfa6481）：families 各树 hash + artifacts 前后对表。"""

    def test_families_trees_hashed(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        plan["families"] = [{"family_id": "A", "items": [
            {"item_id": "t1", "target": "t1"}]}]
        m.enrich_plan(plan, run_dir, tmv)
        fz = json.loads((run_dir / "plan-freeze.json").read_text(encoding="utf-8"))
        self.assertTrue(fz.get("families_trees"))
        ent = fz["families_trees"][0]
        self.assertEqual(ent["family_id"], "A")
        self.assertEqual(len(ent["md5"]), 32)

    def test_artifacts_plan_exam_and_tamper(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from runtime.cognition import plan_skill_spawn as ps
        d = Path(tempfile.mkdtemp())
        (d / "plan.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
        (d / "exam.json").write_text(json.dumps({"y": 2}), encoding="utf-8")
        (d / "plan-freeze.json").write_text(json.dumps({"trees": [], "artifacts": {}}),
                                            encoding="utf-8")
        # 冻结戳
        import hashlib
        fz = json.loads((d / "plan-freeze.json").read_text(encoding="utf-8"))
        fz["artifacts"] = {f: hashlib.sha256((d / f).read_bytes()).hexdigest()[:16]
                           for f in ("plan.json", "exam.json")}
        (d / "plan-freeze.json").write_text(json.dumps(fz), encoding="utf-8")
        src = Path(ps.__file__).parent / "plan_skill_spawn.py"
        _ = src
        # 一致→pass
        chk = ps._verify_plan_freeze(d)
        self.assertTrue(chk["ok"], chk.get("reason"))
        # 篡改 plan.json → 前后对表败
        (d / "plan.json").write_text(json.dumps({"x": 2}), encoding="utf-8")
        chk2 = ps._verify_plan_freeze(d)
        self.assertFalse(chk2["ok"])
        self.assertIn("前后不一致", chk2["reason"])


class B2PlanFieldsTest(unittest.TestCase):
    """B2：CAO8 顶层件 observed/dest/actual·CTO2 notify·CTO4 risk_grading。"""

    def test_top_level_notify_risk(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        # 造顶层 loose 文件（to_week 目录）
        to_dir = next((Path(tmv) / "docs" / "workflow" / "operating-records").glob("*-" + plan["to_week"]))
        (to_dir / "daily-progress.md").write_text("x", encoding="utf-8")
        m.enrich_plan(plan, run_dir, tmv)
        top = plan.get("top_level_items") or []
        ent = next((x for x in top if x["name"] == "daily-progress.md"), None)
        self.assertIsNotNone(ent)
        self.assertTrue(ent["observed"]["path"].endswith("daily-progress.md"))
        self.assertEqual(ent["dest"], "daily-progress.md")
        self.assertTrue(ent["actual_landed_at"])            # 实测 mtime 非生成时点
        self.assertIn("on_fail", plan["notify"])
        self.assertEqual(plan["risk_grading"]["levels"], ["low", "med", "high"])


class B3SignLoadTest(unittest.TestCase):
    """B3：CHO3 migrate 签名/dest·CHO10 席负载表。"""

    def test_migrate_signature_and_seat_load(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        plan.setdefault("families", []).append({"family_id": "B", "items": [
            {"item_id": "t1", "owner": "CTO"}, {"item_id": "t2", "owner": "CTO"}]})
        m.enrich_plan(plan, run_dir, tmv)
        mig = (plan.get("migrate") or [{}])[0]
        self.assertTrue(mig.get("dest"))
        sig = mig.get("signature") or {}
        self.assertEqual(sig.get("seat"), mig.get("owner"))
        self.assertTrue(sig.get("signed_at"))
        load = (plan.get("staffing") or {}).get("seat_load") or {}
        self.assertGreaterEqual(load.get("CTO", 0), 2)
        self.assertIn("seat_overload", plan.get("staffing") or {})


class B4AuthorityBackfillTest(unittest.TestCase):
    """B4：CHO7 批权五要件/形式审查·CHO9 backfill 逐条 owner。"""

    def test_batch_authority_and_backfill_owners(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        plan.setdefault("families", []).append({"family_id": "B", "items": [
            {"item_id": "t1", "target": "t1", "owner": "CTO"}]})
        m.enrich_plan(plan, run_dir, tmv)
        ba = plan.get("batch_authority") or {}
        self.assertEqual(len(ba.get("five_elements") or {}), 5)
        self.assertEqual(ba.get("form_review", {}).get("by"), "COS")
        bo = plan.get("backfill_owners") or []
        self.assertTrue(bo)
        self.assertTrue(all("owner" in x for x in bo))


class B5PlanFieldsTest(unittest.TestCase):
    """B5：silence_recompute（COO4）+ name_registry_table（CPO3）。"""

    def test_silence_and_registry(self):
        fx = EnrichPlanTest()
        plan, run_dir, tmv = fx._fixture()
        m.enrich_plan(plan, run_dir, tmv)
        sr = plan.get("silence_recompute") or {}
        self.assertTrue(sr.get("recomputed"))
        self.assertIn("gaps", sr)
        nr = plan.get("name_registry_table") or {}
        self.assertIn("backfill_ids", nr)
        self.assertIn("unregistered", nr)


if __name__ == "__main__":
    unittest.main()
