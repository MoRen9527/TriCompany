"""score_engine 实弹引擎单测（白盒全谱·2026-11-14 CEO 11:45 直令令④）。

案族对表（CTO 派工令四笔之 4）：判据逐族案（B/C/D/E/G 机判域）+红灯 cap 两案
（C 红→79·G 红→59·REDLINE_CAPS 引用面）+F2 免评案（F=manual score=null）+
T1 三断言案（T1-1 正则+同串/T1-2 值面非存在性/T1-3 manual 域注）+空 run_dir
降级案+坏 json 降级案+rubric 缺席降级案。

两分裁决锚（engine docstring 同源）：机判域 B/C/D/E/G=65·manual 域 A/F/H=35
出分母·总分=机判域归一化百分制·verdict 集合={pass, fail}·缺件≠引擎坏。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition import score_engine
from runtime.cognition.score_engine import run_score

# 窗内 run_id（23:50 ∈ B 族窗·正则合·作段产物同串锚值）
RUN_ID = "shift-W46-20261114T235000Z"


def _pass_stage(name: str, run_id: str = RUN_ID, **extra) -> dict:
    """段产物 pass 通用卷（verdict 面+run_id 同串+extra 值面）。"""
    return {"verdict": "pass", "run_id": run_id, **extra}


def _make_run_dir(root: Path, *, verify_items=None, qualify_assertions=None,
                  preflight_extra=None, run_id: str = RUN_ID) -> Path:
    """score 时点链上已应落五段产物绿卷（G 族齐性判据正形）。"""
    run = root / "run"
    run.mkdir()
    stages = {
        "preflight.json": {
            **_pass_stage("preflight", run_id, exit_code=0),
            **(preflight_extra or {}),
        },
        "qualify.json": _pass_stage("qualify", run_id, exit_code=0, assertions=(
            qualify_assertions or {
                k: {"ok": True} for k in score_engine._QUALIFY_ASSERTION_KEYS
            })),
        "plan.json": _pass_stage("plan", run_id, migrate=[], keep=[]),
        "dce.json": _pass_stage("dce", run_id, steps=[]),
        "verify.json": _pass_stage("verify", run_id, checks=[
            {"check": "migrate_vs_index",
             "items": verify_items if verify_items is not None
             else [{"entry": "tree-a", "status": "landed"}]},
        ]),
    }
    for name, data in stages.items():
        (run / name).write_text(json.dumps(data, ensure_ascii=False),
                                encoding="utf-8")
    return run


class JudgePerFamilyTest(unittest.TestCase):
    """判据逐族案（机判域 B/C/D/E/G）。"""

    def test_b_window_pass_and_out_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # 窗内（23:50）pass
            state, _ = score_engine._judge_b("shift-W46-20261114T235000Z", Path(td))
            self.assertEqual(state, "pass")
            # 窗外（白天预演 16:00）→ 如实出红（零豁免·读数保真）
            state, reasons = score_engine._judge_b(
                "shift-W46-20261114T160000Z", Path(td))
            self.assertEqual(state, "fail")
            self.assertTrue(any("预演" in r for r in reasons))
            # 正则破 → fail（时戳段不可得）
            state, _ = score_engine._judge_b("bad-id", Path(td))
            self.assertEqual(state, "fail")

    def test_c_regex_and_samestring(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            # 正则合+同串命中 → pass
            state, reasons = score_engine._judge_c(RUN_ID, run)
            self.assertEqual(state, "pass")
            self.assertTrue(any("同串 5 件" in r for r in reasons))
            # 正则合但零同串（run_dir 卷内异串）→ fail
            state, reasons = score_engine._judge_c(
                "shift-W46-20261114T235901Z", run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("计数 0" in r for r in reasons))
            # 正则破 → fail
            state, _ = score_engine._judge_c("r1", run)
            self.assertEqual(state, "fail")

    def test_d_value_face_not_existence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            state, _ = score_engine._judge_d(RUN_ID, run)
            self.assertEqual(state, "pass")
            # verdict=fail 值面 → 红（存在性过≠值面过）
            (run / "preflight.json").write_text(
                json.dumps(_pass_stage("preflight", RUN_ID, exit_code=2,
                                       **{"verdict": "fail"})),
                encoding="utf-8")
            state, reasons = score_engine._judge_d(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("exit_code" in r for r in reasons))
            # 缺件 → fail
            (run / "preflight.json").unlink()
            state, reasons = score_engine._judge_d(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("缺件" in r for r in reasons))

    def test_e_five_assertions_value_face(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            state, _ = score_engine._judge_e(RUN_ID, run)
            self.assertEqual(state, "pass")
            # 一键 ok=False → 红（假绿=漏报毒·值面必读）
            bad = {k: {"ok": True} for k in score_engine._QUALIFY_ASSERTION_KEYS}
            bad["disk_free"] = {"ok": False, "reason": "low disk"}
            (run / "qualify.json").write_text(
                json.dumps(_pass_stage("qualify", RUN_ID, exit_code=2,
                                       **{"verdict": "fail", "assertions": bad})),
                encoding="utf-8")
            state, reasons = score_engine._judge_e(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("disk_free" in r for r in reasons))
            # 过态字段 ok=null（T1-2 红面）→ 红
            nulls = {k: {"ok": True} for k in score_engine._QUALIFY_ASSERTION_KEYS}
            nulls["identity"] = {"ok": None}
            (run / "qualify.json").write_text(
                json.dumps(_pass_stage("qualify", RUN_ID, exit_code=0,
                                       assertions=nulls)), encoding="utf-8")
            state, reasons = score_engine._judge_e(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("null" in r for r in reasons))
            # 缺件 → fail
            (run / "qualify.json").unlink()
            state, _ = score_engine._judge_e(RUN_ID, run)
            self.assertEqual(state, "fail")

    def test_g_chain_completeness_and_items(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            state, _ = score_engine._judge_g(RUN_ID, run)
            self.assertEqual(state, "pass")
            # verify items 一项 missing → 红（对表面）
            (run / "verify.json").write_text(json.dumps(
                _pass_stage("verify", RUN_ID, checks=[
                    {"check": "migrate_vs_index",
                     "items": [{"entry": "tree-a", "status": "landed"},
                               {"entry": "tree-b", "status": "missing"}]},
                ])), encoding="utf-8")
            state, reasons = score_engine._judge_g(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("tree-b" in r for r in reasons))
            # 段产物缺一件（dce.json 删）→ 红（齐性面）
            (run / "verify.json").write_text(json.dumps(
                _pass_stage("verify", RUN_ID, checks=[
                    {"check": "migrate_vs_index",
                     "items": [{"entry": "tree-a", "status": "landed"}]}])),
                encoding="utf-8")
            (run / "dce.json").unlink()
            state, reasons = score_engine._judge_g(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("dce.json" in r for r in reasons))
            # 段 verdict 拦截面 → 红
            (run / "dce.json").write_text(
                json.dumps(_pass_stage("dce", RUN_ID, **{"verdict": "fail"})),
                encoding="utf-8")
            state, reasons = score_engine._judge_g(RUN_ID, run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("dce.json" in r for r in reasons))


class RedlineCapTest(unittest.TestCase):
    """红灯 cap 案（REDLINE_CAPS 引用面·零硬编码·红灯不洗白）。

    数学边界注（mock 构造裁决）：真考卷权重下 C 红天花板=50/65=76.9<79——
    cap 语义=总分上限保险丝（不超不压）。令文「C 红→79」触发面用 mock 权重
    放大构造（机判域 95·C 红 80/95=84.2>79→压回）；真权重边界另案如实钉。
    """

    def _amplified_meta(self) -> dict:
        """权重放大考卷替身（机判域 B20/C15/D20/E20/G20=95·manual 35 原样）。"""
        meta, _ = score_engine._load_rubric()
        for fid, w in (("B", 20), ("D", 20), ("E", 20), ("G", 20)):
            meta[fid] = {**meta[fid], "weight": w}
        return meta

    def test_c_red_caps_total_at_79(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # 卷内同串=RUN_ID（窗内）·args 传异串（窗内正则合）→ B pass/C fail
            # ·D/E/G pass → 放大域 80/95=84.2 → C cap 79 → total=79.0
            run = _make_run_dir(Path(td))
            with mock.patch.object(score_engine, "_load_rubric",
                                   return_value=(self._amplified_meta(), [])):
                p = run_score("shift-W46-20261114T235901Z", str(run), "W46", "W47")
            self.assertEqual(
                next(f for f in p["families"] if f["family_id"] == "C")["state"],
                "fail")
            self.assertEqual(p["total_score"], 79.0)
            self.assertEqual(p["redline_caps_applied"][0]["family_id"], "C")
            self.assertEqual(p["verdict"], "fail", "红灯不洗白")

    def test_c_red_real_rubric_math_ceiling_below_cap(self) -> None:
        """真权重 C 红数学边界：50/65=76.9<79 → cap 不压（上限语义·不超不动）
        ·caps_applied 空=如实（cap 形备未触发非缺陷）。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score("shift-W46-20261114T235901Z", str(run), "W46", "W47")
            self.assertAlmostEqual(p["total_score"], 76.9)
            self.assertEqual(p["redline_caps_applied"], [])
            self.assertEqual(p["verdict"], "fail")

    def test_g_red_caps_total_at_59(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # verify items missing → G 红·其余机判 pass → 45/65=69.2 → G cap 59
            run = _make_run_dir(Path(td), verify_items=[
                {"entry": "tree-a", "status": "missing"}])
            p = run_score(RUN_ID, str(run), "W46", "W47")
            self.assertEqual(
                next(f for f in p["families"] if f["family_id"] == "G")["state"],
                "fail")
            self.assertEqual(p["total_score"], 59.0)
            self.assertEqual(p["redline_caps_applied"][0]["family_id"], "G")

    def test_total_is_machine_domain_normalized(self) -> None:
        """总分=机判域归一化（manual 35 出分母·裁决锚 docstring）——全绿卷
        B..G pass → 100.0（65 分机判满=归一后 100）·manual 族 score=null。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            self.assertEqual(p["total_score"], 100.0)
            self.assertEqual(p["verdict"], "pass")
            manual = {f["family_id"]: f for f in p["families"]
                      if f["family_id"] in score_engine.MANUAL_FAMILIES}
            self.assertEqual(set(manual), {"A", "F", "H"})
            self.assertTrue(all(f["state"] == "manual" and f["score"] is None
                                for f in manual.values()))
            self.assertEqual(p["machine_domain_weight"], 65)
            self.assertEqual(p["manual_domain_weight"], 35)


class F2ManualTest(unittest.TestCase):
    """F2 免评案：F=manual score=null（不冒充机判）+special_clause 引用随行。"""

    def test_f_is_manual_with_collection_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            f = next(f for f in p["families"] if f["family_id"] == "F")
            self.assertEqual(f["state"], "manual")
            self.assertIsNone(f["score"])
            self.assertTrue(any("值席采集域" in r for r in f["reasons"]))
            self.assertTrue(any("collection_cmd" in r or "告警" in r
                                for r in f["reasons"]),
                            "采集锚（考卷 collection_cmd 引用）应随行")


class T1AssertionsTest(unittest.TestCase):
    """T1 三断言案（a2c246908 判据面行为锚）。"""

    def test_t1_1_regex_and_samestring_via_c(self) -> None:
        """T1-1（C 族）：正则金值+段产物同串结构锚（见 JudgePerFamilyTest
        test_c_regex_and_samestring 全谱——本案钉 run_score 全链面）。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            c = next(f for f in p["families"] if f["family_id"] == "C")
            self.assertEqual(c["state"], "pass")
            self.assertTrue(any("T1-1" in r for r in c["reasons"]))

    def test_t1_2_value_face_via_d_e(self) -> None:
        """T1-2（D+E 族）：值面必读非仅存在性——preflight exit_code 非 0 与
        qualify ok=null 各自独立拦（值面读数·非文件存在即过）。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(
                Path(td),
                preflight_extra={"exit_code": 2, "verdict": "fail"},
                qualify_assertions={
                    k: {"ok": True} for k in score_engine._QUALIFY_ASSERTION_KEYS
                } | {"run_dir": {"ok": None}},
            )
            p = run_score(RUN_ID, str(run), "W46", "W47")
            states = {f["family_id"]: f["state"] for f in p["families"]}
            self.assertEqual(states["D"], "fail", "T1-2 后半：preflight 退出码非 0 红")
            self.assertEqual(states["E"], "fail", "T1-2 前半：过态字段 null 红")

    def test_t1_3_alarm_face_is_manual_domain(self) -> None:
        """T1-3（F 族告警面）：值席面采集——engine 判 manual 不冒充机判
        （成跑零触发满分判读=值席补判面·F2 免评语义在考卷 special_clause）。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            f = next(f for f in p["families"] if f["family_id"] == "F")
            self.assertEqual(f["state"], "manual")
            self.assertIsNone(f["score"])


class DegradationTest(unittest.TestCase):
    """降级三案（缺件≠引擎坏=设计行为·engine 不外抛破链）。"""

    def test_empty_run_dir_structured_degrade(self) -> None:
        """空 run_dir → 结构化降级（缺件明细）→ verdict=fail。

        B 族独立于 run_dir（判据=run_id 时戳窗·窗内 RUN_ID→pass=10/65=15.4
        设计面如实）·C/D/E/G=缺件 fail·manual 域如实 → total=15.4 非 0。"""
        p = run_score(RUN_ID, "D:/nonexistent-run-dir", "W46", "W47")
        self.assertEqual(p["verdict"], "fail")
        self.assertAlmostEqual(p["total_score"], 15.4)
        states = {f["family_id"]: f["state"] for f in p["families"]}
        self.assertEqual(states["B"], "pass", "B 窗判独立于 run_dir（时戳面）")
        self.assertEqual(
            {k: states[k] for k in ("C", "D", "E", "G")},
            {k: "fail" for k in ("C", "D", "E", "G")})
        self.assertTrue(all(f["reasons"] for f in p["families"]),
                        "缺件明细应逐族入 reasons")

    def test_bad_json_degrades_not_raises(self) -> None:
        """坏 json（段产物解析败）→ 该族 fail+reasons 载坏卷·engine 不炸。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            (run / "qualify.json").write_text("{bad json", encoding="utf-8")
            p = run_score(RUN_ID, str(run), "W46", "W47")
            e = next(f for f in p["families"] if f["family_id"] == "E")
            self.assertEqual(e["state"], "fail")
            self.assertTrue(any("坏卷" in r for r in e["reasons"]))
            g = next(f for f in p["families"] if f["family_id"] == "G")
            self.assertEqual(g["state"], "fail", "链齐性面坏卷同红")

    def test_rubric_file_missing_degrades_all_fail(self) -> None:
        """rubric 文件缺席 → 全族降级 fail·rubric_loaded=False·verdict=fail
        （考卷缺席降级案·engine 不炸）。"""
        ghost = Path("D:/nonexistent/rubric-ghost.json")
        with mock.patch.object(score_engine, "_RUBRIC_FILE", ghost):
            p = run_score(RUN_ID, "D:/nonexistent-run-dir", "W46", "W47")
        self.assertFalse(p["rubric_loaded"])
        self.assertTrue(all(f["state"] == "fail" for f in p["families"]))
        self.assertEqual(p["verdict"], "fail")
        self.assertTrue(any("考卷缺席" in r
                            for f in p["families"] for r in f["reasons"]))


class GbkSafePayloadTest(unittest.TestCase):
    """payload GBK 可编码断案（CLI main print 面 GBK 宿主零炸——实测坑位钉
    案防回归：∈/∉ 等非 GBK 字符禁入 engine payload/reasons 字符面）。"""

    def test_payload_gbk_encodable_all_scenarios(self) -> None:
        scenarios = [
            (RUN_ID, "D:/nonexistent-run-dir"),           # 全缺件降级
            ("shift-W46-20261114T160000Z", None),          # 白天预演出红
            ("bad-id", None),                              # 正则破
        ]
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            (run / "qualify.json").write_text("{bad", encoding="utf-8")
            scenarios.append((RUN_ID, str(run)))           # 坏卷降级
            for rid, rd in scenarios:
                payload = run_score(rid, rd or "D:/x", "W46", "W47")
                blob = json.dumps(payload, ensure_ascii=False)
                blob.encode("gbk")  # 不炸=GBK 宿主 print 面安全


class NoRedlineHardcodeTest(unittest.TestCase):
    """engine 零硬编码上限值（同值同源令②）：REDLINE_CAPS 引用面身份断言。"""

    def test_engine_imports_caps_from_rubric_module(self) -> None:
        from runtime.cognition import score_rubric
        self.assertIs(score_engine.REDLINE_CAPS, score_rubric.REDLINE_CAPS,
                      "engine 消费面与考卷结构门同源同对象")
        self.assertEqual(score_rubric.REDLINE_CAPS, {"C": 79, "G": 59})


if __name__ == "__main__":
    unittest.main()
