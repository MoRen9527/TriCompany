"""close_skill_spawn 单测（DP-20261123-018 item7：cost_settlement 可结算块）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition import close_skill_spawn as m
import os
os.environ.setdefault("FADE_CLOSE_ACCEPTANCE", "0")   # v8 item10 门由专项案直测
os.environ.setdefault("FADE_PATROL_CHECK", "0")        # v8 item11 门由专项案直测


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

    def test_item7_count_trigger_runs(self):
        """v8 item7: _count_trigger_runs 按 trigger 计数（auto fail-safe 判据）。"""
        d = Path(tempfile.mkdtemp())
        self.assertEqual(m._count_trigger_runs(d, "auto"), 0)  # 无 cost-log
        (d / "cost-log.jsonl").write_text(
            '{"trigger":"auto","stage":"a"}\n{"trigger":"manual","stage":"b"}\n{"stage":"c"}\n',
            encoding="utf-8")
        self.assertEqual(m._count_trigger_runs(d, "auto"), 1)
        self.assertEqual(m._count_trigger_runs(d, "manual"), 1)

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


class StructureExportGateTest(unittest.TestCase):
    """T1③（CTO 落点 b）：结构缺陷→upgrade_list 复用·双机械形·cap 1/2·债务表升级。"""

    def test_label_whitelist_and_mechanical_evidence(self):
        d = Path(tempfile.mkdtemp())
        sheet = {"upgrade_list": [
            {"item": "s1", "kind": "structural_defect", "source": "plan.json#/x"},
            {"item": "s2", "kind": "other", "source": "note.md"},
        ]}
        g = m._apply_structure_export_gate(sheet, d)
        self.assertEqual(g["structural_count"], 1)
        it = sheet["upgrade_list"][0]
        self.assertEqual(it["structure_label"], "结构性缺陷·非单条改进可解")
        self.assertTrue(it["evidence_mechanical"])
        self.assertNotIn("structural", sheet["upgrade_list"][1])   # 非白名单零动

    def test_semantic_only_item_flagged_not_mechanical(self):
        d = Path(tempfile.mkdtemp())
        sheet = {"upgrade_list": [{"item": "s", "kind": "structural_defect", "source": "随口说"}]}
        m._apply_structure_export_gate(sheet, d)
        self.assertFalse(sheet["upgrade_list"][0]["evidence_mechanical"])   # 语义判读禁入面

    def test_cap_half_exceeded_marked(self):
        d = Path(tempfile.mkdtemp())
        sheet = {"upgrade_list": [
            {"item": "s1", "kind": "structural_defect", "source": "plan.json"},
            {"item": "s2", "kind": "structural_defect", "source": "plan.json"},
            {"item": "n1", "kind": "other"},
        ]}   # 3 条·cap=1 → 第二条标 rejected
        g = m._apply_structure_export_gate(sheet, d)
        self.assertFalse(g["cap_ok"])
        self.assertTrue(sheet["upgrade_list"][1].get("structure_export_rejected"))

    def test_debt_escalates_after_two_prev_rounds(self):
        d = Path(tempfile.mkdtemp())
        for name in ("runA", "runB"):
            rd = d / name
            rd.mkdir()
            (rd / "structure-export-debt.json").write_text(
                json.dumps({"structural_count": 1, "action_taken": False}), encoding="utf-8")
        cur = d / "runC"
        cur.mkdir()
        sheet = {"upgrade_list": [{"item": "s", "kind": "structural_defect", "source": "plan.json"}]}
        g = m._apply_structure_export_gate(sheet, cur)
        self.assertTrue(g["escalate"])


class SevenSeatsGateTest(unittest.TestCase):
    """v8 item4：close 前七席强制（opinions 席位集齐 7·缺一=partial）。"""

    def _mk(self, seats):
        d = Path(tempfile.mkdtemp())
        ops = [{"seat": s, "opinion_id": f"{s}-1"} for s in seats]
        (d / "opinions.json").write_text(json.dumps({"opinions": ops}), encoding="utf-8")
        return d

    def test_seven_present_ok(self):
        d = self._mk(["cos", "coo", "cao", "cpo", "cto", "cho", "cfo"])
        r = m._check_seven_seats(d)
        self.assertTrue(r["ok"])
        self.assertEqual(r["missing"], [])

    def test_prev_seven_present_ok(self):
        """v8 item4 根修：prev 联审七席齐→过（source=prev）。"""
        base = Path(tempfile.mkdtemp())
        cur = base / "run-cur"; cur.mkdir()
        prev = base / "run-prev"; prev.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({"faces": {
            s: {"dimensions": []} for s in
            ["cos", "coo", "cao", "cpo", "cto", "cho", "cfo"]}}), encoding="utf-8")
        r = m._check_seven_seats(cur)
        self.assertTrue(r["ok"])
        self.assertFalse(r.get("degraded"))
        self.assertEqual(r["source"], str(prev))

    def test_prev_missing_seat_warn_degraded(self):
        """v8 item4 根修：prev 七席缺→WARN 降级（时序错位非施工失败）。"""
        base = Path(tempfile.mkdtemp())
        cur = base / "run-cur"; cur.mkdir()
        prev = base / "run-prev"; prev.mkdir()
        (prev / "opinions.json").write_text(json.dumps({"opinions": [
            {"seat": s} for s in ["cos", "coo", "cao", "cpo", "cto"]]}), encoding="utf-8")
        r = m._check_seven_seats(cur)
        self.assertTrue(r["ok"])
        self.assertTrue(r.get("degraded"))
        self.assertIn("段 10 后", r["reason"])
        self.assertEqual(sorted(r["missing"]), ["cfo", "cho"])


class V8Item10AcceptanceTest(unittest.TestCase):
    """v8 item10：close-acceptance 三值复算对表（声明 vs 复算两侧值）。"""

    def test_build_and_recompute(self):
        d = Path(tempfile.mkdtemp())
        (d / "alerts.jsonl").write_text(chr(10).join([
            json.dumps({"family": "A", "latency_s": 3}),
            json.dumps({"family": "A", "latency_s": 5}),
            json.dumps({"family": "B", "latency_s": 2}),
        ]), encoding="utf-8")
        doc = m._build_close_acceptance(d)
        self.assertEqual(doc["total"], 3)
        self.assertEqual(doc["by_family"], {"A": 2, "B": 1})
        self.assertEqual(doc["max_latency"], 5.0)
        self.assertTrue(m._verify_close_acceptance(d)["ok"])

    def test_tampered_declaration_rejected(self):
        d = Path(tempfile.mkdtemp())
        (d / "alerts.jsonl").write_text(json.dumps({"family": "A", "latency_s": 1}), encoding="utf-8")
        m._build_close_acceptance(d)
        doc = json.loads((d / "close-acceptance.json").read_text(encoding="utf-8"))
        doc["total"] = 9
        (d / "close-acceptance.json").write_text(json.dumps(doc), encoding="utf-8")
        v = m._verify_close_acceptance(d)
        self.assertFalse(v["ok"])
        self.assertIn("声明=9", v["reason"])


class V8Item11PatrolTest(unittest.TestCase):
    """v8 item11 close 侧：patrol log 重数拍频对表（缺 log/缺计划=fail-closed）。"""

    def _mk(self, d, cadence="15m", ticks=3, gap_min=15):
        (d / "plan.json").write_text(json.dumps({"patrol_plan": {
            "who": "cos-duty", "cadence": cadence, "window": "w"}}), encoding="utf-8")
        from datetime import datetime, timedelta, timezone
        base = datetime(2026, 11, 24, tzinfo=timezone.utc)
        lines = [json.dumps({"ts": (base + timedelta(minutes=gap_min * i)).isoformat()})
                 for i in range(ticks)]
        (d / "patrol-log.jsonl").write_text(chr(10).join(lines), encoding="utf-8")

    def test_match_ok(self):
        d = Path(tempfile.mkdtemp())
        self._mk(d)
        r = m._check_patrol_plan(d, {})
        self.assertTrue(r["ok"], r["reason"])
        self.assertEqual(r["measured_median_min"], 15.0)

    def test_plan_missing_fail(self):
        d = Path(tempfile.mkdtemp())
        r = m._check_patrol_plan(d, {})
        self.assertFalse(r["ok"])
        self.assertIn("patrol_plan", r["reason"])

    def test_log_missing_warn_degraded(self):
        """BOD 裁准（CTO 令 2026-11-25）：patrol-log 缺=设计缺口→WARN 降级非 fail·留痕不静默。"""
        d = Path(tempfile.mkdtemp())
        (d / "plan.json").write_text(json.dumps({"patrol_plan": {
            "who": "c", "cadence": "15m", "window": "w"}}), encoding="utf-8")
        sheet: dict = {}
        r = m._check_patrol_plan(d, sheet)
        self.assertTrue(r["ok"])
        self.assertTrue(r.get("degraded"))
        self.assertIn("设计缺口", r["reason"])
        self.assertIn("patrol_check", sheet)

    def test_log_present_mismatch_still_fail(self):
        """有 patrol-log → 照对表；拍频不符仍 fail（门不取消）。"""
        d = Path(tempfile.mkdtemp())
        self._mk(d, cadence="15m", ticks=3, gap_min=5)   # 实测 5min ≠ 声明 15m
        r = m._check_patrol_plan(d, {})
        self.assertFalse(r["ok"])
        self.assertIn("拍频对表败", r["reason"])


class RunStateAuthorityTest(unittest.TestCase):
    """v8 run_state 权威化（SDE 定谳）：TC 判定覆盖席自判。"""

    def test_seat_partial_overridden_when_seven_ok(self):
        sheet, out = {"run_state": "partial"}, {}
        m._apply_run_state_authority(sheet, out, {"ok": True})
        self.assertEqual(sheet["run_state"], "succeeded")
        self.assertEqual(out["run_state_authority"], "tc_override_ok")

    def test_seat_failed_overridden_when_seven_ok(self):
        sheet, out = {"run_state": "failed"}, {}
        m._apply_run_state_authority(sheet, out, {"ok": True, "degraded": True})
        self.assertEqual(sheet["run_state"], "succeeded")   # degraded 亦 TC ok

    def test_seven_not_ok_keeps_partial(self):
        sheet, out = {"run_state": "succeeded"}, {}
        m._apply_run_state_authority(sheet, out, {"ok": False})
        self.assertEqual(sheet["run_state"], "partial")
        self.assertTrue(out["seven_seats_partial"])


class PatrolTwoFormTest(unittest.TestCase):
    """两形漂移双修（CTO 令 2026-11-25）：新形 cadence_layers 无顶层 cadence → close gate pass；旧形 pass。"""

    def _mk(self, plan_pp, log_rows):
        d = Path(tempfile.mkdtemp())
        (d / "plan.json").write_text(json.dumps({"patrol_plan": plan_pp}), encoding="utf-8")
        (d / "patrol-log.jsonl").write_text(chr(10).join(
            json.dumps(r) for r in log_rows), encoding="utf-8")
        return d

    def test_new_form_cadence_layers_only_passes(self):
        pp = {"who": "cos-duty", "window": "w", "cadence_layers": {
            "bod_patrol": {"cadence": "6m"}, "duty_patrol": {"cadence": "15m"}}}
        d = self._mk(pp, [{"ts": f"2026-11-24T00:{i * 15:02d}:00+00:00"} for i in range(3)])
        sheet: dict = {}
        r = m._check_patrol_plan(d, sheet)
        self.assertTrue(r["ok"], r.get("reason"))

    def test_old_form_passes(self):
        pp = {"who": "cos-duty", "cadence": "15m", "window": "w"}
        d = self._mk(pp, [{"ts": f"2026-11-24T00:{i * 15:02d}:00+00:00"} for i in range(3)])
        r = m._check_patrol_plan(d, {})
        self.assertTrue(r["ok"], r.get("reason"))


if __name__ == "__main__":
    unittest.main()
