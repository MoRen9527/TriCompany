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

    def test_b_loop_window_self_attested_pass(self) -> None:
        """B 族 loop 轮增补钉（2026-11-16·CTO 46afd9bc3 §三裁 owner=STE·
        判据语义=STE 裁）：loop-window 轮=管线自证形态（mode+loop_source
        值面三锚硬读·非窗判豁免）。白天拍（窗判必红形）+自证齐 → pass。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "preflight.json").write_text(json.dumps({
                "verdict": "pass", "exit_code": 0,
                "assertions": {"week_math": {"mode": "loop-window",
                                             "loop_source": "marker",
                                             "ok": True}},
            }, ensure_ascii=False), encoding="utf-8")
            state, reasons = score_engine._judge_b(
                "shift-W47-20261117T143000Z", run)  # 白天 14:30=窗外形
            self.assertEqual(state, "pass")
            self.assertTrue(any("loop_source=marker" in r for r in reasons))

    def test_b_loop_window_bad_runid_still_fails(self) -> None:
        """T1-1 正则=任何轮硬前提零豁免钉：mode=loop-window 不救 run_id
        形坏（双 W bug 形照拒——防「loop 轮豁免一切」放宽向·C 族钉案同构）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "preflight.json").write_text(json.dumps({
                "assertions": {"week_math": {"mode": "loop-window",
                                             "loop_source": "cli"}},
            }), encoding="utf-8")
            state, _ = score_engine._judge_b(
                "shift-WW46-20261116T002143Z", run)  # 第 10 轮实锚双 W 形
            self.assertEqual(state, "fail")

    def test_b_loop_window_loop_source_incomplete_fail_closed(self) -> None:
        """自证链不完整 fail-closed 钉：mode=loop-window 而 loop_source
        缺失/未知值=fail（读数保真·零豁免——值面必读非仅存在性）。"""
        with tempfile.TemporaryDirectory() as td:
            cases = [("missing", {"mode": "loop-window"}),
                     ("unknown", {"mode": "loop-window",
                                  "loop_source": "unknown-channel"})]
            for tag, wm in cases:
                run = Path(td) / f"run_{tag}"
                run.mkdir()
                (run / "preflight.json").write_text(json.dumps({
                    "assertions": {"week_math": wm},
                }), encoding="utf-8")
                state, reasons = score_engine._judge_b(
                    "shift-W47-20261117T143000Z", run)
                self.assertEqual(state, "fail", f"loop_source {tag} 形须红")
                self.assertTrue(any("自证链不完整" in r for r in reasons))

    def test_b_sunday_and_no_mode_unchanged(self) -> None:
        """零行为漂移钉：cron-sunday 现行窗判不变+无 week_math 键（预演/
        旧卷）走现行窗判+preflight 卷缺席走窗判——增补面只扩 loop-window
        精确命中·其余一切原样（预演线如实出红维持）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "preflight.json").write_text(json.dumps({
                "assertions": {"week_math": {"mode": "cron-sunday",
                                             "ok": True}},
            }), encoding="utf-8")
            # cron-sunday 窗内 pass（现行不变）
            state, _ = score_engine._judge_b(
                "shift-W46-20261114T235000Z", run)
            self.assertEqual(state, "pass")
            # cron-sunday 窗外 fail（现行不变）
            state, reasons = score_engine._judge_b(
                "shift-W46-20261114T160000Z", run)
            self.assertEqual(state, "fail")
            self.assertTrue(any("23:50,23:59" in r for r in reasons))
            # 无 week_math 键（预演卷形）窗外 fail（零行为漂移）
            run2 = Path(td) / "run2"
            run2.mkdir()
            (run2 / "preflight.json").write_text(
                json.dumps({"assertions": {}}, ensure_ascii=False),
                encoding="utf-8")
            state, _ = score_engine._judge_b(
                "shift-W46-20261114T160000Z", run2)
            self.assertEqual(state, "fail")
            # preflight 卷缺席走窗判（原 B 案同语义现行为）
            state, _ = score_engine._judge_b(
                "shift-W46-20261114T235000Z", Path(td) / "absent")
            self.assertEqual(state, "pass")

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

    def test_run_id_double_w_bug_shape_rejected(self) -> None:
        """run_id 双 W 形拒绝钉案（C 族修件窗·CTO 裁 A 2026-11-16）：
        payload 模板 shift-W{fromWeek}+{fromWeek}=W46 展开=shift-WW46 双 W——
        第 10 轮 22 分缺口实锚根因（B/C 两族正则恒错配）。本案钉双 W 形
        T1-1 正则拒·B/C 两族 fail——防模板回退与判据放宽二向回退（修复后
        run_id 归一单 W=shift-W46-… 门禁契约正形）。"""
        with tempfile.TemporaryDirectory() as td:
            bug_id = "shift-WW46-20261116T002143Z"  # 第 10 轮实锚形
            # B 族：双 W 正则拒（时戳段不可得）
            state, reasons = score_engine._judge_b(bug_id, Path(td))
            self.assertEqual(state, "fail")
            self.assertTrue(any("T1-1 正则" in r for r in reasons))
            # C 族：双 W 正则拒
            state, reasons = score_engine._judge_c(bug_id, Path(td))
            self.assertEqual(state, "fail")
            self.assertTrue(any("T1-1 正则" in r for r in reasons))
            # 对照：单 W 正形（模板修复后形）正则合窗内 pass
            state, _ = score_engine._judge_b("shift-W46-20261114T235000Z", Path(td))
            self.assertEqual(state, "pass")

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
        """真权重 C 红数学边界：B9+D9+E9+G19=46<79 → cap 不压（上限语义·不超不动）
        ·caps_applied 空=如实（cap 形备未触发非缺陷）。
        〔期望校正并盘 100 形·v2.0.0 直加制：原 76.9=50/65 归一化形（沿革留痕）——
        C 新权重 13·C 红余机判直加=46.0；正道可达=C 判据真跑见本断言 fail 态。〕"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score("shift-W46-20261114T235901Z", str(run), "W46", "W47")
            self.assertAlmostEqual(p["total_score"], 56.0)   # 件①：C 红机判 32+采集 na 24
            self.assertEqual(p["redline_caps_applied"], [])
            self.assertEqual(p["verdict"], "fail")

    def test_g_red_caps_total_at_59(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # verify items missing → G 红·其余机判 pass → 直加制 B9+C13+D9+E9=40
            # +采集满分 31+主观满分 10=81>59 → G cap 59（正道可达 cap 形·并盘 100 形
            # 期望校正：原 45/65=69.2 归一化形沿革留痕——直加制下纯机判 40<59 cap 不触，
            # 本案构造扩采集/主观满分至 81 使 cap 真触发=cap 生效语义保留）
            run = _make_run_dir(Path(td), verify_items=[
                {"entry": "tree-a", "status": "missing"}])
            # 采集/主观满分卷（正道可达：值席采集 A/F/H 全 pass=31+判卷 I1=4/I2=3/I3=3=10）
            (run / "collection-score.json").write_text(json.dumps({
                "score_version": "1.0.0", "run_id": RUN_ID,
                "entries": [{"family_id": f, "verdict": "pass",
                             "rationale": "采集读数在卷", "evidence_ref": "dive.json"}
                            for f in ("A", "F", "H")]}, ensure_ascii=False), encoding="utf-8")
            (run / "subjective-score.json").write_text(json.dumps({
                "score_version": "1.0.0", "run_id": RUN_ID,
                "entries": [{"criterion": "I1", "score": 4, "rationale": "锚判读：记录随周封存·活随人带走", "evidence_ref": "plan.json"},
                            {"criterion": "I2", "score": 3, "rationale": "批次预案降级链三面齐", "evidence_ref": "plan.json"},
                            {"criterion": "I3", "score": 3, "rationale": "reasons 实判断·指针全可达", "evidence_ref": "close.json"}],
                "judge_faces": {"initial": "duty"}, }, ensure_ascii=False), encoding="utf-8")
            (run / "close.json").write_text(json.dumps({"run_state": "succeeded"}),
                                            encoding="utf-8")   # I3 evidence_ref 可达（主观 10 满）
            p = run_score(RUN_ID, str(run), "W46", "W47")
            self.assertEqual(
                next(f for f in p["families"] if f["family_id"] == "G")["state"],
                "fail")
            self.assertEqual(p["total_score"], 59.0)   # v2.1.0 G cap：27+24+10=61→59
            self.assertEqual(p["redline_caps_applied"][0]["family_id"], "G")

    def test_total_is_three_domain_direct_add(self) -> None:
        """总分=三域直加制（并盘 100 形 v2.0.0）——机判全绿卷两卷缺席态：
        B..G pass → total=59（机判域原值和·59 与 REDLINE G cap 59 数值偶合无关）
        +pending 41（采集 31+主观 10）+projection=100·采集/主观族 score=null 分层。
        〔期望校正：原案 test_total_is_machine_domain_normalized 100.0=65/65 归一化形
        （沿革留痕）——正道可达=机判 B..G 五族真跑 pass 见本断言+projection 勾稽。〕"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            self.assertEqual(p["total_score"], 65.0)   # 件①：机判 41+采集 na 24
            self.assertEqual(p["verdict"], "pass")
            self.assertEqual(p["total_pending_weight"], 35)   # 件①：仅 I 主观 35 pending
            self.assertEqual(p["total_projection"], 100.0)   # v2.1.0：41+59
            self.assertEqual(p["domain_breakdown"], {"machine": 41.0, "collection": 24.0, "subjective": 0.0})   # 件①：采集 na→weight 24
            manual = {f["family_id"]: f for f in p["families"]
                      if f["family_id"] in score_engine.MANUAL_FAMILIES}
            self.assertEqual(set(manual), {"A", "F", "H"})
            self.assertTrue(all(f["state"] == "manual" and f["score"] == f["weight"]
                                for f in manual.values()))   # 件①：na→weight 非 null
            subjective = {f["family_id"]: f for f in p["families"]
                          if f["family_id"] in score_engine.SUBJECTIVE_FAMILIES}
            self.assertEqual(set(subjective), {"I"})
            self.assertTrue(all(f["state"] == "partial" and f["score"] is None
                                for f in subjective.values()))   # v8 item8：缺席=partial
            self.assertEqual(p["machine_domain_weight"], 41)
            self.assertEqual(p["manual_domain_weight"], 24)   # v2.1.0：采集域 6+9+9
            self.assertEqual(p["subjective_domain_weight"], 35)
            self.assertEqual(p["manual_domain_weight"], 24)   # v2.1.0：采集域 6+9+9


class F2ManualTest(unittest.TestCase):
    """F2 免评案：F=manual score=null（不冒充机判）+special_clause 引用随行。"""

    def test_f_is_manual_with_collection_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            f = next(f for f in p["families"] if f["family_id"] == "F")
            self.assertEqual(f["state"], "manual")
            self.assertEqual(f["score"], f["weight"])   # 件①：F engine 采集 na→weight（9）
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
            self.assertEqual(f["score"], f["weight"])   # 件①：na→weight（9）


class DegradationTest(unittest.TestCase):
    """降级三案（缺件≠引擎坏=设计行为·engine 不外抛破链）。"""

    def test_empty_run_dir_structured_degrade(self) -> None:
        """空 run_dir → 结构化降级（缺件明细）→ verdict=fail。

        B 族独立于 run_dir（判据=run_id 时戳窗·窗内 RUN_ID→pass=9 直加制
        设计面如实）·C/D/E/G=缺件 fail·manual 域如实 → total=9 非 0。
        〔期望校正并盘 100 形·v2.0.0 直加制：原 15.4=10/65 归一化形（沿革留痕）——
        B 新权重 9·直加=9.0；正道可达=B 窗判真跑见本断言 pass。〕"""
        p = run_score(RUN_ID, "D:/nonexistent-run-dir", "W46", "W47")
        self.assertEqual(p["verdict"], "fail")
        self.assertAlmostEqual(p["total_score"], 30.0)   # 件①：B6+A/F/H na 24
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



class V8Item8PartialTest(unittest.TestCase):
    """v8 item8：_judge_subjective 卷缺席→partial（非 pending）·run_state 联动。"""

    def test_judge_subjective_absent_partial(self):
        import tempfile as _tf
        with _tf.TemporaryDirectory() as td:
            state, score = score_engine._judge_subjective(Path(td), "r1")
            self.assertEqual(state, "partial")
            self.assertIsNone(score)


class AutoCollectTest(unittest.TestCase):
    """a 案件①（CEO 批）：A/F/H engine 自动采集三分离件（producer=engine·na→weight·旧卷回读冻结）。"""

    def test_a_collect_pass_and_file(self):
        d = Path(tempfile.mkdtemp())
        (d / "jobs.json").write_text(json.dumps({"jobs": [{"id": "j1"}]}), encoding="utf-8")
        ent = score_engine._collect_a(d)
        self.assertEqual(ent["verdict"], "pass")
        got = score_engine._engine_collect_entry(d, "r1", "A")
        self.assertEqual(got["family_id"], "A")
        doc = json.loads((d / "collection" / "collection-A.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["producer"], "engine")
        self.assertEqual(doc["axis"], "acceptance")   # 件④：验收轴字段
        self.assertEqual(doc["run_id"], "r1")

    def test_f_na_zero_trigger(self):
        d = Path(tempfile.mkdtemp())
        ent = score_engine._collect_f(d)
        self.assertEqual(ent["verdict"], "na")

    def test_h_na_no_plan_declaration(self):
        d = Path(tempfile.mkdtemp())               # 无 plan.patrol_plan → na（设计内）
        ent = score_engine._collect_h(d)
        self.assertEqual(ent["verdict"], "na")

    def test_h_manual_when_source_missing(self):
        d = Path(tempfile.mkdtemp())
        pp = {"who": "c", "window": "w", "cadence_layers": {
            "bod_patrol": {"cadence": "15m"},
            "duty_patrol": {"cadence": "15m"}}}
        (d / "plan.json").write_text(json.dumps({"patrol_plan": pp}), encoding="utf-8")
        ent = score_engine._collect_h(d)           # 声明在·源缺 → manual（异常）
        self.assertEqual(ent["verdict"], "manual")

    def test_h_pass_when_cadence_matches(self):
        d = Path(tempfile.mkdtemp())
        pp = {"who": "c", "window": "w", "cadence_layers": {
            "bod_patrol": {"cadence": "15m"},
            "duty_patrol": {"cadence": "15m"}}}
        (d / "plan.json").write_text(json.dumps({"patrol_plan": pp}), encoding="utf-8")
        src = d / "patrol-source.jsonl"
        src.write_text(chr(10).join(json.dumps({"ts": f"t{i}", "seat": "bod", "cadence_min": 15})
                                    for i in range(3)), encoding="utf-8")
        old = __import__("os").environ.get("PATROL_SOURCE")
        __import__("os").environ["PATROL_SOURCE"] = str(src)
        try:
            ent = score_engine._collect_h(d)
        finally:
            if old is None:
                __import__("os").environ.pop("PATROL_SOURCE", None)
            else:
                __import__("os").environ["PATROL_SOURCE"] = old
        self.assertEqual(ent["verdict"], "pass")

    def test_run_id_mismatch_ignored(self):
        d = Path(tempfile.mkdtemp())
        (d / "collection").mkdir()
        (d / "collection" / "collection-A.json").write_text(json.dumps({
            "producer": "engine", "run_id": "OTHER",
            "entries": [{"family_id": "A", "verdict": "pass"}]}), encoding="utf-8")
        self.assertIsNone(score_engine._engine_collect_entry(d, "r1", "A"))


    def test_h_bod_patrol_six_minutes_matches(self):
        import os as _os, tempfile as _tf
        d = Path(_tf.mkdtemp())
        pp = {"who": "c", "window": "w", "cadence_layers": {
            "bod_patrol": {"cadence": "6m"},
            "duty_patrol": {"cadence": "15m"},
            "note": "两节律不混"}}
        (d / "plan.json").write_text(json.dumps({"patrol_plan": pp}), encoding="utf-8")
        src = d / "patrol-source.jsonl"
        rows = [{"ts": f"t{i}", "seat": "bod", "cadence_min": 6} for i in range(5)]
        rows += [{"ts": f"d{i}", "seat": "duty", "cadence_min": 15} for i in range(5)]
        src.write_text(chr(10).join(json.dumps(r) for r in rows), encoding="utf-8")
        old = _os.environ.get("PATROL_SOURCE")
        _os.environ["PATROL_SOURCE"] = str(src)
        try:
            ent = score_engine._collect_h(d)
        finally:
            if old is None:
                _os.environ.pop("PATROL_SOURCE", None)
            else:
                _os.environ["PATROL_SOURCE"] = old
        self.assertEqual(ent["verdict"], "pass")      # bod 6m 对上·duty 15m 不计入
        self.assertIn("bod tick=5", ent["rationale"])

    def test_h_no_bod_patrol_spec_missing_na(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        pp = {"who": "c", "cadence": "15m", "window": "w"}
        (d / "plan.json").write_text(json.dumps({"patrol_plan": pp}), encoding="utf-8")
        ent = score_engine._collect_h(d)
        self.assertEqual(ent["verdict"], "na")
        self.assertIn("spec 缺失注", ent["rationale"])

    def test_f_bounded_scan_cap_and_recent_only(self):
        import os as _os, tempfile as _tf, time as _t
        d = Path(_tf.mkdtemp())
        logs = d / "logs"
        logs.mkdir()
        old_t = _t.time() - 3 * 86400
        for i in range(600):        # 大量旧件（模拟大目录·不用 glob）
            fp = logs / f"old-{i}.log"
            fp.write_text("x" + chr(10), encoding="utf-8")
            _os.utime(fp, (old_t, old_t))
        for i in range(3):
            (logs / f"new-{i}.log").write_text("ERROR rec" + chr(10), encoding="utf-8")
        old = _os.environ.get("TRIRMC_LOGS")
        _os.environ["TRIRMC_LOGS"] = str(logs)
        try:
            ent = score_engine._collect_f(d)
        finally:
            if old is None:
                _os.environ.pop("TRIRMC_LOGS", None)
            else:
                _os.environ["TRIRMC_LOGS"] = old
        self.assertEqual(ent["verdict"], "pass")
        self.assertIn("24h 3 件", ent["rationale"])   # 只扫近 24h（600 旧件排除）

    def test_h_cadence_layers_six_minutes(self):
        import os as _os, tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "plan.json").write_text(json.dumps({"patrol_plan": {
            "who": "c", "window": "w", "cadence_layers": {
                "bod_patrol": {"cadence": "6m"}, "duty_patrol": {"cadence": "15m"}}}}),
            encoding="utf-8")
        src = d / "patrol-source.jsonl"
        src.write_text(chr(10).join(json.dumps({"ts": f"t{i}", "seat": "bod", "cadence_min": 6})
                                    for i in range(4)), encoding="utf-8")
        old = _os.environ.get("PATROL_SOURCE")
        _os.environ["PATROL_SOURCE"] = str(src)
        try:
            ent = score_engine._collect_h(d)
        finally:
            if old is None:
                _os.environ.pop("PATROL_SOURCE", None)
            else:
                _os.environ["PATROL_SOURCE"] = old
        self.assertEqual(ent["verdict"], "pass")
        self.assertIn("bod_patrol=6m", ent["rationale"])

    def test_h_old_plan_form_spec_missing_na(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "plan.json").write_text(json.dumps({"patrol_plan": {
            "who": "c", "cadence": "15m", "window": "w"}}), encoding="utf-8")
        ent = score_engine._collect_h(d)
        self.assertEqual(ent["verdict"], "na")
        self.assertIn("spec 缺失注", ent["rationale"])


class CollectPathSourceTest(unittest.TestCase):
    """engine 采集路径修（CTO 令 2026-11-25）：A=$TRIRMC_JOBS / F=$TRIRMC_LOGS glob / H=PATROL_SOURCE(tmv)."""

    def test_a_env_override_hits(self):
        import os as _os, tempfile as _tf
        d = Path(_tf.mkdtemp())
        jobs = d / "jobs.json"
        jobs.write_text(json.dumps({"jobs": [{"id": "j1"}]}), encoding="utf-8")
        old = _os.environ.get("TRIRMC_JOBS")
        _os.environ["TRIRMC_JOBS"] = str(jobs)
        try:
            ent = score_engine._collect_a(d)
        finally:
            if old is None:
                _os.environ.pop("TRIRMC_JOBS", None)
            else:
                _os.environ["TRIRMC_JOBS"] = old
        self.assertEqual(ent["verdict"], "pass")
        self.assertIn("md5=", ent["rationale"])

    def test_f_logs_glob_hits(self):
        import os as _os, tempfile as _tf
        d = Path(_tf.mkdtemp())
        logs = d / "logs"
        logs.mkdir()
        (logs / "a.log").write_text("RUN_ID: r1" + chr(10) + "ERROR: boom" + chr(10), encoding="utf-8")
        (logs / "b.log").write_text("trigger: auto" + chr(10), encoding="utf-8")
        old = _os.environ.get("TRIRMC_LOGS")
        _os.environ["TRIRMC_LOGS"] = str(logs)
        try:
            ent = score_engine._collect_f(d)
        finally:
            if old is None:
                _os.environ.pop("TRIRMC_LOGS", None)
            else:
                _os.environ["TRIRMC_LOGS"] = old
        self.assertEqual(ent["verdict"], "pass")
        self.assertIn("匹配行=3", ent["rationale"])

    def test_h_patrol_source_hits_machine_judge(self):
        import os as _os, tempfile as _tf
        d = Path(_tf.mkdtemp())
        pp = {"who": "c", "window": "w", "cadence_layers": {
            "bod_patrol": {"cadence": "15m"}, "duty_patrol": {"cadence": "15m"}}}
        (d / "plan.json").write_text(json.dumps({"patrol_plan": pp}), encoding="utf-8")
        src = d / "patrol-source.jsonl"
        src.write_text(chr(10).join(json.dumps({"ts": f"t{i}", "seat": "bod", "cadence_min": 15})
                                    for i in range(3)), encoding="utf-8")
        old = _os.environ.get("PATROL_SOURCE")
        _os.environ["PATROL_SOURCE"] = str(src)
        try:
            ent = score_engine._collect_h(d)
        finally:
            if old is None:
                _os.environ.pop("PATROL_SOURCE", None)
            else:
                _os.environ["PATROL_SOURCE"] = old
        self.assertEqual(ent["verdict"], "pass")   # 源在=机判 pass

    def test_h_source_missing_manual(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        pp = {"who": "c", "window": "w", "cadence_layers": {
            "bod_patrol": {"cadence": "15m"}, "duty_patrol": {"cadence": "15m"}}}
        (d / "plan.json").write_text(json.dumps({"patrol_plan": pp}), encoding="utf-8")
        import os as _os
        for k in ("PATROL_SOURCE", "FADE_PATROL_SOURCE", "FADE_OPERATING_ROOT"):
            _os.environ.pop(k, None)
        ent = score_engine._collect_h(d)
        self.assertEqual(ent["verdict"], "manual")


class T3bManifestTest(unittest.TestCase):
    """T3b（任务书 e0dfa6481）：manifest 全覆盖+逐件 run_id 对表+缺件显式。"""

    def test_manifest_lists_and_missing_explicit(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "score.json").write_text(json.dumps({"run_id": "r1"}), encoding="utf-8")
        (d / "close.json").write_text(json.dumps({"run_id": "r1"}), encoding="utf-8")
        (d / "collection").mkdir()
        (d / "collection" / "collection-A.json").write_text(
            json.dumps({"run_id": "r1"}), encoding="utf-8")
        man = score_engine._artifacts_manifest(d, "r1")
        self.assertTrue(man["checked"])
        names = {i["file"] for i in man["items"]}
        self.assertIn("score.json", names)
        self.assertIn("collection/collection-A.json", names)
        self.assertIn("preflight.json", man["missing"])     # 缺件显式记
        sc = [i for i in man["items"] if i["file"] == "score.json"][0]
        self.assertTrue(sc["run_id_match"])
        self.assertEqual(len(sc["sha256_16"]), 16)        # T3c：逐件全量 hash
        self.assertTrue(sc["parse_ok"])
        self.assertGreater(sc["size"], 0)

    def test_run_id_mismatch_recorded(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "verify.json").write_text(json.dumps({"run_id": "OTHER"}), encoding="utf-8")
        man = score_engine._artifacts_manifest(d, "r1")
        self.assertIn("verify.json", man["run_id_mismatch"])


class S4EmptyEvidenceTest(unittest.TestCase):
    """S4b（r36 任务书）：verify items 空证（evidence_ref 空）→ G fail。"""

    def test_g_empty_evidence_fails(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "preflight.json").write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
        (d / "qualify.json").write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
        (d / "plan.json").write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
        (d / "dce.json").write_text(json.dumps({"verdict": "pass"}), encoding="utf-8")
        (d / "verify.json").write_text(json.dumps({"verdict": "pass", "checks": [
            {"check": "migrate_vs_index", "ok": True, "items": [
                {"entry": "t1", "status": "landed", "evidence_ref": ""}]}]}), encoding="utf-8")
        state, reasons = score_engine._judge_g("r1", d)
        self.assertEqual(state, "fail")
        self.assertTrue(any("空证" in x for x in reasons))


class S6RegimeCountsAutoTest(unittest.TestCase):
    """S6（r36 任务书）：单一 100 制 / 三面 counts 同口径 / 禁 auto 冒充。"""

    def test_regime_single_100(self):
        r = score_engine._regime_check(None)
        self.assertEqual(r["rubric_total"], 100)
        self.assertTrue(r["ok"])
        self.assertEqual(r["rubric_version"], score_engine.RUBRIC_VERSION)

    def test_regime_legacy_weight_face_violation(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "score-skill.json").write_text(json.dumps({"weight_face": {
            "total_basis": 65, "subjective_i_family": {"I1": 14, "I2": 11, "I3": 10}}}),
            encoding="utf-8")
        r = score_engine._regime_check(d)
        self.assertFalse(r["ok"])
        self.assertTrue(any("非 100 制" in x for x in r["violations"]))
        self.assertTrue(any("旧 14/11/10" in x for x in r["violations"]))

    def test_counts_mismatch_note(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "plan.json").write_text(json.dumps({"families": [{"items": [{}, {}, {}]}]}),
                                     encoding="utf-8")
        (d / "opinions.json").write_text(json.dumps({"opinions": [{}, {}]}), encoding="utf-8")
        r = score_engine._counts_check(d)
        self.assertFalse(r["ok"])
        self.assertTrue(any("口径差" in x for x in r["notes"]))

    def test_auto_label_required(self):
        doc = {"score": {"families": [{"family_id": "I",
                                       "reasons": ["r34 时序补算：…"]}]}}
        viol = score_engine._check_auto_label(doc)
        self.assertTrue(viol)
        doc["score"]["judge_faces"] = {"subjective": "auto-backfill"}
        self.assertEqual(score_engine._check_auto_label(doc), [])


class S7CostAttributionTest(unittest.TestCase):
    """S7（r36 任务书·CFO 面）：成本三面归因/stage 分列/auto fail-safe 非静默 0。"""

    def test_three_faces_and_stage(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        rows = [
            {"stage": "verify", "tokens_in": 100, "tokens_out": 10},
            {"stage": "score_skill", "input_tokens": 50, "output_tokens": 5},
            {"stage": "plan_scope", "tokens": 20},
            {"stage": "close", "tokens_in": None, "tokens_out": 3},   # null 面
        ]
        (d / "cost-log.jsonl").write_text(chr(10).join(json.dumps(r) for r in rows), encoding="utf-8")
        ca = score_engine._cost_attribution(d)
        self.assertTrue(ca["checked"])
        self.assertEqual(ca["faces"]["machine"]["in"], 100)
        self.assertEqual(ca["faces"]["subjective"]["in"], 50)
        self.assertEqual(ca["faces"]["manual"]["in"], 20)
        self.assertEqual(ca["cost_by_stage"]["verify"], {"in": 100, "out": 10})
        self.assertGreaterEqual(ca["null_skipped"], 1)     # null 不计入（记 skipped）

    def test_auto_zero_total_degraded_not_silent_zero(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "subjective-score.json").write_text(json.dumps({
            "run_id": "r1",
            "entries": [{"criterion": "I1", "score": 4, "rationale": ""},   # 全裸分被拒
                        {"criterion": "I2", "score": 3, "rationale": " "}],
            "judge_faces": {"initial": "duty"}}), encoding="utf-8")
        state, score = score_engine._judge_subjective(d, "r1", 35)
        self.assertEqual(state, "manual")     # degraded（非靜默 0）
        self.assertIsNone(score)


    def test_unparsable_file_parse_ok_false(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "dce.json").write_text("not json at all", encoding="utf-8")
        man = score_engine._artifacts_manifest(d, "r1")
        ent = [i for i in man["items"] if i["file"] == "dce.json"][0]
        self.assertFalse(ent["parse_ok"])                 # 不可解析显式
        self.assertEqual(len(ent["sha256_16"]), 16)       # hash 仍可算


class B2CostDceTest(unittest.TestCase):
    """B2：CFO1 残差台账·COS9 wrong_order 逐条裁定。"""

    def test_residual_ledger(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "cost-log.jsonl").write_text(chr(10).join(json.dumps(r) for r in [
            {"stage": "verify", "tokens_in": None, "tokens_out": None},
            {"stage": "score_skill", "tokens_in": 5, "tokens_out": 1}]), encoding="utf-8")
        ca = score_engine._cost_attribution(d)
        ledger = ca.get("residual_ledger") or []
        self.assertTrue(any(x["stage"] == "verify" and x["action"] == "escalate-cfo" for x in ledger))

    def test_wrong_order_notes_only_after_ac2(self):
        # A+C 重构后：wrong_order 只 notes 不 fail（原 COS9 strict 语义被 CEO 架构令取代）
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        for fn, body in (("preflight.json", {"verdict": "pass"}),
                         ("qualify.json", {"verdict": "pass"}),
                         ("plan.json", {"verdict": "pass"}),
                         ("verify.json", {"verdict": "pass", "checks": [
                             {"check": "migrate_vs_index", "ok": True, "items": []}]}),
                         ("dce.json", {"verdict": "pass",
                                       "execution_diff": {"wrong_order": ["t1", "t2"]}})):
            (d / fn).write_text(json.dumps(body), encoding="utf-8")
        state, reasons = score_engine._judge_g("r1", d)
        self.assertEqual(state, "pass")
        self.assertTrue(any("wrong_order 清单项" in x for x in reasons))   # C+B 新文案（非封存类）


class B4CostChannelTest(unittest.TestCase):
    """B4：CFO4 轮级成本通道 fail-closed 可见。"""

    def test_channel_not_ok_when_all_null(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "cost-log.jsonl").write_text(json.dumps(
            {"stage": "verify", "tokens_in": None, "tokens_out": None}) + chr(10), encoding="utf-8")
        ca = score_engine._cost_attribution(d)
        self.assertFalse(ca.get("channel_ok"))
        self.assertIn("不可得", ca.get("fail_closed_note", ""))


class AC2WrongOrderNotesTest(unittest.TestCase):
    """A+C（CEO 架构令）：wrong_order 只 notes 不 fail·键名双形·语义判归段 7。"""

    def _mk(self, wo):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        for fn, body in (("preflight.json", {"verdict": "pass"}),
                         ("qualify.json", {"verdict": "pass"}),
                         ("plan.json", {"verdict": "pass", "families": [], "keep": [], "migrate": []}),
                         ("verify.json", {"verdict": "pass", "checks": [
                             {"check": "migrate_vs_index", "ok": True, "items": []}]})):
            (d / fn).write_text(json.dumps(body), encoding="utf-8")
        (d / "dce.json").write_text(json.dumps({"verdict": "pass",
                                                "execution_diff": {"wrong_order": wo}}), encoding="utf-8")
        return d

    def test_notes_only_never_fail(self):
        d = self._mk(["t1", "t2"])
        state, reasons = score_engine._judge_g("r1", d)
        self.assertEqual(state, "pass")                       # 链照跑
        self.assertTrue(any("段 7" in r for r in reasons))

    def test_key_name_dual_shape(self):
        d = self._mk([{"wrong_order_item": "tA"}, {"item": "tB"}, "tC"])
        g = score_engine._wrong_order_gate(d)
        names = " ".join(g["notes"])
        self.assertIn("tA", names)
        self.assertIn("tB", names)
        self.assertIn("tC", names)


class SubjectiveCollectionConsumeTest(unittest.TestCase):
    """并盘 100 形 v2.0.0 判卷/采集消费链正道可达案（双件套第二件·证明例）。

    机判锚三面：①卷在分值进 total（59+31+10=100 满盘勾稽）②禁裸分锚
    （rationale 空判据不计）③卷缺席 pending 分层（score=null 不冒充）。"""

    def _full_run(self, base: Path) -> Path:
        run = _make_run_dir(base)
        (run / "collection-score.json").write_text(json.dumps({
            "score_version": "1.0.0", "run_id": RUN_ID,
            "entries": [{"family_id": f, "verdict": "pass",
                         "rationale": "采集读数在卷", "evidence_ref": "dive.json"}
                        for f in ("A", "F", "H")]}, ensure_ascii=False), encoding="utf-8")
        (run / "subjective-score.json").write_text(json.dumps({
            "score_version": "1.0.0", "run_id": RUN_ID,
            "entries": [{"criterion": "I1", "score": 4, "rationale": "锚判读在卷", "evidence_ref": "plan.json"},
                        {"criterion": "I2", "score": 3, "rationale": "三面齐", "evidence_ref": "plan.json"},
                        {"criterion": "I3", "score": 3, "rationale": "指针全可达", "evidence_ref": "plan.json"}],
            "judge_faces": {"initial": "duty"}}, ensure_ascii=False), encoding="utf-8")
        return run

    def test_full_score_projection_100(self) -> None:
        """满盘勾稽：机判 59+采集 31+主观 10=100（勘正①公式活体）。"""
        with tempfile.TemporaryDirectory() as td:
            p = run_score(RUN_ID, str(self._full_run(Path(td))), "W46", "W47")
            # v2.1.0：主观卷 10 分 × 35 权/10=35 → 41+24+35=100（满盘勾稽）
            self.assertEqual(p["total_score"], 100.0)
            self.assertEqual(p["total_pending_weight"], 0)
            self.assertEqual(p["total_projection"], 100.0)
            self.assertEqual(p["domain_breakdown"], {"machine": 41.0, "collection": 24.0, "subjective": 35.0})
            self.assertEqual(p["verdict"], "pass")

    def test_bare_score_rejected(self) -> None:
        """禁裸分锚活体：rationale 空的判据不计（I1 裸分→主观 10-4=6）。"""
        with tempfile.TemporaryDirectory() as td:
            run = self._full_run(Path(td))
            doc = json.loads((run / "subjective-score.json").read_text(encoding="utf-8"))
            doc["entries"][0]["rationale"] = ""
            (run / "subjective-score.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            p = run_score(RUN_ID, str(run), "W46", "W47")
            # 裸分锚拒 I1 → 余 I2=3/I3=3=6 → ×3.5=21
            self.assertEqual(p["domain_breakdown"]["subjective"], 21.0)
            self.assertEqual(p["total_score"], 86.0)   # 41+24+21

    def test_missing卷_partial_layered(self) -> None:
        """卷缺席=partial 分层（v8 item8·score=null 不冒充·run_state 联动可观测）。"""
        with tempfile.TemporaryDirectory() as td:
            run = _make_run_dir(Path(td))
            p = run_score(RUN_ID, str(run), "W46", "W47")
            subj = next(f for f in p["families"] if f["family_id"] == "I")
            self.assertEqual(subj["state"], "partial")
            self.assertIsNone(subj["score"])
            self.assertEqual(p.get("run_state"), "partial")
            self.assertEqual(p["total_pending_weight"], 35)   # 件①：仅 I 主观 35 pending


class RunIdFourFormsTest(unittest.TestCase):
    """DP-20261123-016（CTO 派令+CPO 会签 2ceae9804）：run_id 四形正例+负例保持。"""

    def test_four_forms_positive(self) -> None:
        for rid in (
            "shift-W46-20261114T235000Z",              # 裸形
            "shift-W47-loop-20261122T142315Z",         # -loop
            "shift-W48-ignite-20261123T005158Z",       # -ignite
            "shift-W48-official-20261123T010000Z",     # -official
            "shift-W48-resume4-20261123T053031Z",      # -resume\d*
        ):
            self.assertTrue(score_engine._RUN_ID_RE.match(rid), rid)

    def test_negatives_hold(self) -> None:
        self.assertFalse(score_engine._RUN_ID_RE.match("shift-WW46-20261116T002143Z"))   # 双 W
        self.assertFalse(score_engine._RUN_ID_RE.match("shift-W48-bogus-20261123T010000Z"))  # 未知形


class S2ImprovementBlockTest(unittest.TestCase):
    """S2-2/3/4：改进率 Δ/prev·逐席逐维表·门槛参数化·双轨分 k 参数化。"""

    def _mk(self):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        prev = base / "prev"; prev.mkdir()
        cur = base / "cur"; cur.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 50, "b": 60},
            "faces": {"cos": {"dimensions": [
                {"dimension_id": "d1", "score": 50}, {"dimension_id": "d2", "score": 40}]}}}),
            encoding="utf-8")
        (cur / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 55, "b": 65},
            "faces": {"cos": {"dimensions": [
                {"dimension_id": "d1", "score": 60}, {"dimension_id": "d2", "score": 42}]}}}),
            encoding="utf-8")
        return cur

    def test_rate_and_table(self):
        d = self._mk()
        b = score_engine._improvement_block(d)
        self.assertTrue(b["checked"])
        per = {x["dimension_id"]: x for x in b["improvement_rate"]["per_dim"]}
        self.assertEqual(per["d1"]["delta"], 10.0)
        self.assertEqual(per["d1"]["rate"], 0.2)
        self.assertEqual(per["d2"]["delta"], 2.0)
        self.assertTrue(any(x["seat"] == "cos" and x["dimension_id"] == "d1" for x in b["by_seat"]))
        self.assertAlmostEqual(b["improvement_rate"]["total_rate"], round(12 / 90, 4), places=4)

    def test_threshold_and_k_params(self):
        import os as _os
        d = self._mk()
        old1, old2 = _os.environ.get("IMPROVE_MIN_RATE"), _os.environ.get("IMPROVE_K")
        _os.environ["IMPROVE_MIN_RATE"] = "0.1"
        _os.environ["IMPROVE_K"] = "0.5"
        try:
            b = score_engine._improvement_block(d)
        finally:
            for k, v in (("IMPROVE_MIN_RATE", old1), ("IMPROVE_K", old2)):
                if v is None:
                    _os.environ.pop(k, None)
                else:
                    _os.environ[k] = v
        below = b["below_threshold_dims"]              # ②：per-dim 面改名参考
        self.assertTrue(any(x["dimension_id"] == "d2" for x in below))
        self.assertIn("below_threshold", b)            # repair 判面存在（本 fixture 无 refill→None）
        dt = b["dual_track"]
        self.assertEqual(dt["exposure"], {"a": 55, "b": 65})
        self.assertAlmostEqual(dt["improvement"], round(0.5 * b["improvement_rate"]["total_rate"], 3))
        self.assertIsNotNone(dt["combined"])


class RepairRateTest(unittest.TestCase):
    """修复率 100% 机制：分母=该修（defer_kind 白名单移出）·缺省门槛 1.0。"""

    def _mk(self, fixed_cnt, prev_items, min_rate=None):
        import tempfile as _tf, os as _os
        base = Path(_tf.mkdtemp())
        prev = base / "prev"; prev.mkdir()
        cur = base / "cur"; cur.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 50, "b": 60},
            "refill": {"items": prev_items}}), encoding="utf-8")
        cur_items = ([{"status": "fixed", "prev_opinion_id": f"p{i}"} for i in range(fixed_cnt)]
                     + [{"status": "carried", "prev_opinion_id": None}])
        (cur / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 55, "b": 65},
            "refill": {"items": cur_items}}), encoding="utf-8")
        old = _os.environ.get("IMPROVE_MIN_RATE")
        if min_rate is not None:
            _os.environ["IMPROVE_MIN_RATE"] = str(min_rate)
        else:
            _os.environ.pop("IMPROVE_MIN_RATE", None)
        try:
            return score_engine._improvement_block(cur)
        finally:
            if old is None:
                _os.environ.pop("IMPROVE_MIN_RATE", None)
            else:
                _os.environ["IMPROVE_MIN_RATE"] = old

    def test_all_fixed_rate_1_passes(self):
        prev = [{"status": "deferred", "defer_kind": None, "prev_opinion_id": f"p{i}"} for i in range(3)]
        b = self._mk(3, prev)
        self.assertEqual(b["repair"]["repair_rate"], 1.0)
        self.assertFalse(b["below_threshold"]["below"])

    def test_one_unfixed_no_kind_red(self):
        prev = [{"status": "deferred", "defer_kind": None, "prev_opinion_id": f"p{i}"} for i in range(3)]
        b = self._mk(2, prev)
        self.assertAlmostEqual(b["repair"]["repair_rate"], round(2 / 3, 4))
        self.assertTrue(b["below_threshold"]["below"])

    def test_remaining_whitelist_without_kind_by_invalid(self):
        # kind_by 审计分离（CTO 令 2026-11-26·旧语义随改）：白名单 kind 无 kind_by=无效豁免→计该修
        prev = ([{"status": "deferred", "defer_kind": None, "prev_opinion_id": f"p{i}"} for i in range(2)]
                + [{"status": "deferred", "defer_kind": "external_dependency", "prev_opinion_id": "px"}])
        b = self._mk(2, prev)
        self.assertEqual(b["repair"]["should_fix"], 3)        # 3=无效豁免实锚
        self.assertAlmostEqual(b["repair"]["repair_rate"], round(2 / 3, 4))
        self.assertTrue(b["below_threshold"]["below"])        # <1.0 RED

    def test_remaining_whitelist_with_kind_by_exempt(self):
        prev = ([{"status": "deferred", "defer_kind": None, "prev_opinion_id": f"p{i}"} for i in range(2)]
                + [{"status": "deferred", "defer_kind": "external_dependency",
                    "kind_by": "cos", "prev_opinion_id": "px"}])
        b = self._mk(2, prev)
        self.assertEqual(b["repair"]["should_fix"], 2)        # 有效豁免移出
        self.assertEqual(b["repair"]["repair_rate"], 1.0)
        self.assertFalse(b["below_threshold"]["below"])


class KindByAuditTest(unittest.TestCase):
    """kind_by 审计分离（堵自证·CTO 令 2026-11-26）：白名单+kind_by 非空=有效豁免·缺=该修。"""

    def _mk(self, prev_items):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        prev = base / "prev"; prev.mkdir()
        cur = base / "cur"; cur.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 50, "b": 60},
            "refill": {"items": prev_items}}), encoding="utf-8")
        (cur / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 55, "b": 65},
            "refill": {"items": [{"status": "fixed", "prev_opinion_id": "p0"}]}}),
            encoding="utf-8")
        return score_engine._improvement_block(cur)

    def test_valid_exemption_with_kind_by(self):
        prev = [{"status": "deferred", "defer_kind": None, "prev_opinion_id": "p0"},
                {"status": "deferred", "defer_kind": "external_dependency", "kind_by": "cos",
                 "prev_opinion_id": "p1"}]
        b = self._mk(prev)
        self.assertEqual(b["repair"]["should_fix"], 1)        # 白名单+kind_by 移出
        self.assertEqual(b["repair"]["repair_rate"], 1.0)
        self.assertFalse(b["below_threshold"]["below"])

    def test_invalid_exemption_without_kind_by(self):
        prev = [{"status": "deferred", "defer_kind": None, "prev_opinion_id": "p0"},
                {"status": "deferred", "defer_kind": "external_dependency",
                 "prev_opinion_id": "p1"}]   # kind_by 缺
        b = self._mk(prev)
        self.assertEqual(b["repair"]["should_fix"], 2)        # 无效豁免→计该修
        self.assertEqual(b["repair"]["repair_rate"], 0.5)
        self.assertTrue(b["below_threshold"]["below"])        # <1.0 RED


class RepairIntersectionTest(unittest.TestCase):
    """repair 分子同口径交集（CTO 2026-11-26）：resolved=should_fix∩fixed·rate≤1.0·total 参考。"""

    def _mk(self, prev_items, cur_fixed_ids, extra_fixed=0):
        import tempfile as _tf
        base = Path(_tf.mkdtemp())
        prev = base / "prev"; prev.mkdir()
        cur = base / "cur"; cur.mkdir()
        (prev / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 50, "b": 60},
            "refill": {"items": prev_items}}), encoding="utf-8")
        cur_items = [{"status": "fixed", "prev_opinion_id": i} for i in cur_fixed_ids]
        cur_items += [{"status": "fixed", "prev_opinion_id": f"new-{i}"} for i in range(extra_fixed)]
        (cur / "joint-review.json").write_text(json.dumps({
            "seat_means": {"a": 55, "b": 65},
            "refill": {"items": cur_items}}), encoding="utf-8")
        return score_engine._improvement_block(cur)

    def test_intersection_rate_capped_and_total_reference(self):
        prev = [{"status": "deferred", "defer_kind": None, "prev_opinion_id": f"p{i}"}
                for i in range(17)]
        fixed_ids = [f"p{i}" for i in range(15)]
        b = self._mk(prev, fixed_ids, extra_fixed=27)          # 总 fixed=42
        r = b["repair"]
        self.assertEqual(r["prev_pending"], 17)
        self.assertEqual(r["fixed_prev_pending_resolved"], 15)
        self.assertAlmostEqual(r["repair_rate"], round(15 / 17, 4))
        self.assertLessEqual(r["repair_rate"], 1.0)
        self.assertEqual(r["fixed_this_round_total"], 42)       # 参考面

    def test_full_resolution_rate_1(self):
        prev = [{"status": "carried", "defer_kind": None, "prev_opinion_id": f"p{i}"}
                for i in range(17)]
        b = self._mk(prev, [f"p{i}" for i in range(17)])
        self.assertEqual(b["repair"]["repair_rate"], 1.0)       # 上限
        self.assertFalse(b["below_threshold"]["below"])


class E5CrossPlaneTest(unittest.TestCase):
    """E5：score families ∩ joint dimensions = ∅（边界禁混）。"""

    def test_no_overlap_ok(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "joint-review.json").write_text(json.dumps({"faces": {"cos": {"dimensions": [
            {"dimension_id": "migrate_accuracy", "score": 80}]}}}), encoding="utf-8")
        r = score_engine._cross_check_planes(d)
        self.assertTrue(r["ok"])
        self.assertEqual(r["overlap"], [])

    def test_overlap_flagged(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        (d / "joint-review.json").write_text(json.dumps({"faces": {"cos": {"dimensions": [
            {"dimension_id": "A", "score": 80}]}}}), encoding="utf-8")   # 撞 score 族 id
        r = score_engine._cross_check_planes(d)
        self.assertFalse(r["ok"])
        self.assertEqual(r["overlap"], ["A"])


class E2ScorePlanePurityTest(unittest.TestCase):
    """E2（进化架构）：score 移除进化指标（仅指针桩）。"""

    def test_score_has_no_improvement_block(self):
        import tempfile as _tf
        d = Path(_tf.mkdtemp())
        out = score_engine.run_score("r1", str(d), "W46", "W47")
        self.assertNotIn("improvement_block", out)
        self.assertNotIn("dual_track", out)                  # 顶层键面（措辞出现于指针 note 不算）
        self.assertIn("improvement_block_ref", out)          # 指针桩
        self.assertEqual(out["improvement_block_ref"]["moved_to"],
                         "joint-review.json#/improvement_block")
