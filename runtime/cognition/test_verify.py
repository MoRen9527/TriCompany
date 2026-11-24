"""FADE-001 阶段 5 verify cli 单测（白盒·注入式案族·plan_scope 测试同形制）。

案族对表（fsd-ten-stage-tech-collab §三 阶段 5 行+STE 锚④ γ 对表锚）：
  ①plan 基准面（毒化拦·替身禁令 NOT_FOUND）
  ②γ 归位数学面（start_date isocalendar==to_week·skip/坏格式案）
  ③新周 index active 断言（NOT_FOUND/缺键/ambiguous 三负路径）
  ④--strict 生产形对表（全中/赤字/坏 index 三案·发现 28 勘修形：对表域=
    旧周 trees/ 目录存在性·原地封存语义——2026-11-14 γ 施工勘正）
  ⑤exit code+落卷面（哑卷防线）
"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.verify import (
    VERIFY_VERSION,
    check_gamma,
    run_verify,
)
from runtime.cognition import verify as verify_mod


def _mk_plan(run: Path, migrate: list[str] | None = None, verdict: str = "pass") -> Path:
    """造 plan.json（阶段 3 产物基准面 fixture）。"""
    run.mkdir(parents=True, exist_ok=True)
    p = run / "plan.json"
    m = [{"entry": e, "kind": "dir", "reason_codes": ["x"]} for e in (migrate or [])]
    p.write_text(
        json.dumps(
            {
                "plan_version": "1.0.0",
                "run_id": "shift-W46-test",
                "from_week": "W46",
                "to_week": "W47",
                "verdict": verdict,
                "migrate": m,
                "keep": [],
                "carry_over": [],
                "counts": {
                    "migrate": len(m), "keep": 0, "carry_over": 0,
                },
                "bidirectional_ok": True,
                "check_time": "2026-11-15T15:50:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    return p


def _mk_from_week(root: Path, trees: list[str] | None = None,
                  week: str = "W46", with_trees: bool = True) -> Path:
    """造旧周目录+trees/ 树目录（发现 28 勘修形 strict 对表域 fixture）。

    原地封存语义：树目录留在旧周 trees/ 下=landed（迁移器不物理搬家）。
    with_trees=False 造「旧周目录在但 trees/ 子目录缺」负形态。
    """
    wk = root / f"2026-{week}"
    wk.mkdir(parents=True, exist_ok=True)
    if with_trees:
        trees_dir = wk / "trees"
        trees_dir.mkdir(parents=True, exist_ok=True)
        for t in (trees or []):
            (trees_dir / t).mkdir(parents=True, exist_ok=True)
    return wk


def _mk_to_week(root: Path, done_from_prev: list[str] | None = None,
                active: list[str] | None = None, with_key: bool = True) -> Path:
    """造 to 周目录+OP index（activeTrees 键 fixture·断言 C 结构面）。"""
    # v8 item1：strict 必填→migrate_vs_index 生效·from 周目录随建（空 trees·幂等）
    (root / "2026-W46" / "trees").mkdir(parents=True, exist_ok=True)
    wk = root / "2026-W47"
    wk.mkdir(parents=True, exist_ok=True)
    data = {
        "activeTrees": [{"name": a} for a in (active or [])] if with_key else None,
        "doneTreesFromPreviousWeek": [{"name": d} for d in (done_from_prev or [])],
        "doneTreesThisWeek": [],
    }
    if not with_key:
        data.pop("activeTrees")
    (wk / "OP-202611-W47-001.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    return wk


def _args(root: Path, run: Path, **kw) -> argparse.Namespace:
    # plan fixture 由调用方显式 _mk_plan 造（禁 autoload 覆写——毒化/赤字案 fixture 保真）
    base = dict(
        plan_file=str(run / "plan.json"),
        from_week="W46", to_week="W47",
        start_date="2026-11-16",
        run_dir=str(run), run_id="shift-W46-test",
        operating_root=str(root), strict=True,   # v8 item1：--strict 必填（旧 False 形退役）
    )
    base.update(kw)
    return argparse.Namespace(**base)


class VerifyPassTest(unittest.TestCase):
    """预演形全过案：plan 好+γ 对+index 在 → exit 0·checks 结构全。"""

    def test_preview_pass_structure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 0, json.dumps(v.get("reasons"), ensure_ascii=False))
            self.assertEqual(v["verdict"], "pass")
            self.assertEqual(v["verify_version"], VERIFY_VERSION)
            names = [c["check"] for c in v["checks"]]
            # WP5 对账红闸勘正（获批改形 2026-11-18）：checks 序列增 reconciliation
            # DP-20261123-015：checks 序列增 plan_structure_full（全量质量门·spawn/CLI 门等值）
            self.assertEqual(names, ["plan_baseline", "run_id_match", "reconciliation",
                                     "plan_structure_full", "strict_required",
                                     "gamma_week", "new_week_index", "migrate_vs_index"])
            self.assertTrue(v["strict_mode"])   # v8 item1：strict 必填——预览亦严格形
            self.assertTrue(v["check_time"])


class FailureClassTest(unittest.TestCase):
    """R10-COO-01：红因自动归族（argv/timeout/truncation/tool_explore/unclassified）。"""

    def test_argv_class(self):
        self.assertIn("argv", verify_mod.classify_failure("unrecognized arguments: --x"))

    def test_timeout_class(self):
        self.assertIn("timeout", verify_mod.classify_failure("spawnSync python3 ETIMEDOUT"))

    def test_truncation_and_tool(self):
        self.assertIn("truncation", verify_mod.classify_failure("finish reason max-tokens"))
        self.assertIn("tool_explore", verify_mod.classify_failure("429 rate limit during tool calls"))

    def test_pass_round_empty_list(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run))
            self.assertEqual(v.get("failure_class"), [])


class VerifyPlanStructureFullTest(unittest.TestCase):
    """DP-20261123-015 全量质量门：缺 bidirectional_ok/annotation 的旧 form 卷=红；合规卷=绿。"""

    def test_old_plan_missing_bidirectional_and_annotation_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            pf = run / "plan.json"
            plan = json.loads(pf.read_text(encoding="utf-8"))
            plan.pop("bidirectional_ok", None)                     # resume 轮实锤缺项
            # resume 轮实锤：readings 在但 annotation 空（34 条）
            plan["agent_readings"] = [
                {"tree": "t1", "domain": "tree", "disposition": "keep",
                 "rationale": "r", "evidence_ref": ["plan.json"]},
            ]
            pf.write_text(json.dumps(plan), encoding="utf-8")
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertEqual(v["verdict"], "fail")
            sf = [c for c in v["checks"] if c["check"] == "plan_structure_full"][0]
            self.assertFalse(sf["ok"])
            joined = " ".join(sf["reasons"])
            self.assertIn("bidirectional_ok", joined)
            self.assertIn("annotation", joined)

    def test_full_compliant_plan_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run))
            sf = [c for c in v["checks"] if c["check"] == "plan_structure_full"][0]
            self.assertTrue(sf["ok"])
            self.assertEqual(code, 0)


class VerifyPlanBaselineTest(unittest.TestCase):
    """plan 基准面：缺=NOT_FOUND 替身禁令·毒化=拦不接棒。"""

    def test_plan_missing_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_to_week(root)
            args = _args(root, root / "run")
            args.plan_file = str(root / "run" / "no-such-plan.json")
            code, v = run_verify(args)
            self.assertEqual(code, 2)
            self.assertEqual(v["verdict"], "fail")
            self.assertTrue(any("NOT_FOUND" in r for r in v["reasons"]))

    def test_plan_verdict_fail_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, verdict="fail")
            _mk_to_week(root)
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertTrue(any("毒化" in r for r in v["reasons"]))

    def test_plan_counts_poisoned_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            p = _mk_plan(run, migrate=["a"])
            # 毒化：counts 与实长不符
            data = json.loads(p.read_text(encoding="utf-8"))
            data["counts"]["migrate"] = 99
            p.write_text(json.dumps(data), encoding="utf-8")
            _mk_to_week(root)
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertTrue(any("counts.migrate" in r for r in v["reasons"]))


class VerifyGammaTest(unittest.TestCase):
    """γ 归位数学面（二道闸归位·STE 锚④前置件）。"""

    def test_gamma_ok(self) -> None:
        ok, reasons = check_gamma("W47", "2026-11-16")
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_gamma_mismatch(self) -> None:
        ok, reasons = check_gamma("W48", "2026-11-16")
        self.assertFalse(ok)
        self.assertTrue(any("gamma_mismatch" in r for r in reasons))

    def test_gamma_skip_without_start_date(self) -> None:
        ok, reasons = check_gamma("W47", None)
        self.assertTrue(ok)
        self.assertTrue(reasons[0].startswith("gamma_skip"))

    def test_gamma_bad_start_date(self) -> None:
        ok, reasons = check_gamma("W47", "not-a-date")
        self.assertFalse(ok)
        self.assertTrue(any("unparsable" in r for r in reasons))


class VerifyIndexTest(unittest.TestCase):
    """新周 index active 断言负路径三向。"""

    def test_to_week_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertTrue(any("to_week dir not found" in r for r in v["reasons"]))

    def test_op_index_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            (root / "2026-W47").mkdir(parents=True)
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertTrue(any("OP index not found" in r for r in v["reasons"]))

    def test_active_trees_key_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, with_key=False)
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertTrue(any("activeTrees" in r for r in v["reasons"]))

    def test_latest_op_by_mtime_not_lexicographic(self) -> None:
        """妆容劫持防族规负路径（PM §四/STE §三.4）：字典序大但 mtime 旧的 OP
        不得劫持读数（mtime 序正形·陷阱案常备形）。"""
        import os
        import time
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            wk = _mk_to_week(root, active=["live"])  # OP-...-001（mtime 现在·合法）
            hijack = wk / "OP-202611-W47-999.json"   # 字典序大·mtime 一小时前·broken
            hijack.write_text("{ broken", encoding="utf-8")
            old = time.time() - 3600
            os.utime(hijack, (old, old))
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 0, json.dumps(v.get("reasons"), ensure_ascii=False))

    def test_ambiguous_year_dirs(self) -> None:
        """双年段命中（2025-W47+2026-W47）无 start_date → glob fallback ambiguous 不猜。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root)  # 2026-W47 + OP index
            (root / "2025-W47").mkdir(parents=True)
            args = _args(root, run, start_date=None)  # 走 glob fallback 路径
            code, v = run_verify(args)
            self.assertEqual(code, 2)
            self.assertTrue(any("ambiguous" in r for r in v["reasons"]))


class VerifyStrictTest(unittest.TestCase):
    """--strict 生产形对表（发现 28 勘修形：plan.migrate vs 旧周 trees/ 存在性）。

    对表域勘修（2026-11-14 γ 施工）：原形=to 周 OP index done∪active 并集（与
    迁移执行域零机械联动·首拍空壳 index 必炸）→现形=旧周 trees/ 目录存在性
    （原地封存语义）。to 周 index 断言（断言 C）独立拦·零触。
    """

    def test_strict_all_matched(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a", "tree-b"])
            _mk_from_week(root, trees=["tree-a", "tree-b"])
            _mk_to_week(root, done_from_prev=["tree-a"], active=["tree-a"])
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 0, json.dumps(v.get("reasons"), ensure_ascii=False))
            chk = next(c for c in v["checks"] if c["check"] == "migrate_vs_index")
            # 逐项读数（PM §一 段 5 行）：全中=items 全 landed
            self.assertEqual(
                [i["status"] for i in chk["items"]], ["landed", "landed"]
            )

    def test_strict_deficit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a", "missing-one"])
            _mk_from_week(root, trees=["tree-a"])
            _mk_to_week(root)
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 2)
            self.assertTrue(any("missing-one" in r for r in v["reasons"]))
            # 逐项读数：deficit 面 missing 标注+landed 面（landed=全集−missing 可推导）
            chk = next(c for c in v["checks"] if c["check"] == "migrate_vs_index")
            by_entry = {i["entry"]: i["status"] for i in chk["items"]}
            self.assertEqual(by_entry["tree-a"], "landed")
            self.assertEqual(by_entry["missing-one"], "missing")

    def test_strict_bad_index(self) -> None:
        """坏 to 周 index 拦截源=断言 C（new_week_index·非 strict 也拦）——
        strict 对表段不触发（errors 非空短路·checks 零 migrate_vs_index 条目）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a"])
            _mk_from_week(root, trees=["tree-a"])
            wk = _mk_to_week(root)
            (wk / "OP-202611-W47-001.json").write_text("{ broken", encoding="utf-8")
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 2)
            self.assertTrue(any("unreadable" in r for r in v["reasons"]))
            self.assertNotIn(
                "migrate_vs_index", [c["check"] for c in v["checks"]],
                "strict 对表段不触发（上游 errors 短路）",
            )

    def test_strict_empty_to_index_but_trees_present_passes(self) -> None:
        """发现 28 核心回归案：to 周 index 空壳（activeTrees=[]+
        doneTreesFromPreviousWeek=[]·W46 实锚形态=index 与实盘脱节）但旧周
        trees/ 全在 → strict exit 0（首拍不炸=勘修正形直证）。

        原形判据下此形态对表全 missing→exit 2 首拍必炸（发现 28 机理）；
        勘修后对表域=旧周 trees/ 存在性·空壳 index 零触。
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a", "tree-b", "tree-c"])
            _mk_from_week(root, trees=["tree-a", "tree-b", "tree-c"])
            _mk_to_week(root, done_from_prev=[], active=[])  # 空壳 index（W46 实锚形）
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 0, json.dumps(v.get("reasons"), ensure_ascii=False))
            chk = next(c for c in v["checks"] if c["check"] == "migrate_vs_index")
            self.assertEqual(
                [i["status"] for i in chk["items"]], ["landed", "landed", "landed"]
            )

    def _drop_auto_week(self, root):
        import shutil
        p = root / "2026-W46"
        if p.exists():
            shutil.rmtree(p)

    def test_strict_from_week_dir_missing(self) -> None:
        """旧周目录不在 → strict 对表域不可得 NOT_FOUND 拦（替身禁令同族）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a"])
            _mk_to_week(root)
            self._drop_auto_week(root)                    # v8 item1：撤自动建的 from 周
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 2)
            self.assertTrue(any("from_week dir not found" in r for r in v["reasons"]))

    def test_strict_from_week_trees_dir_missing(self) -> None:
        """旧周目录在但 trees/ 子目录缺 → NOT_FOUND 拦（对表域=trees/ 面）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a"])
            _mk_from_week(root, with_trees=False)
            _mk_to_week(root)
            # v8 item1：撤自动建的空 trees（本负例须无 trees/）
            import shutil
            if (root / "2026-W46" / "trees").exists():
                shutil.rmtree(root / "2026-W46" / "trees")
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 2)
            self.assertTrue(any("trees/ dir not found" in r for r in v["reasons"]))

    def test_strict_from_week_ambiguous(self) -> None:
        """双年段命中（2025-W46+2026-W46）→ ambiguous 不猜（glob fallback
        同族形态·与 to_week ambiguous 案对表）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a"])
            _mk_from_week(root, trees=["tree-a"])           # 2026-W46
            (root / "2025-W46" / "trees").mkdir(parents=True)  # 2025-W46
            _mk_to_week(root)
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 2)
            self.assertTrue(any("ambiguous" in r for r in v["reasons"]))

    def test_strict_file_entry_tolerated(self) -> None:
        """散文件树容忍案：trees/<entry> 为文件非目录 → landed（存在性判据=
        Path.exists()·kind 面不判——发现 4 kind 错标债在 plan_scope 域·本函数
        零预设 kind）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["tree-a", "loose-file"])
            _mk_from_week(root, trees=["tree-a"])
            (root / "2026-W46" / "trees" / "loose-file").write_text(
                "x", encoding="utf-8"
            )
            _mk_to_week(root)
            code, v = run_verify(_args(root, run, strict=True))
            self.assertEqual(code, 0, json.dumps(v.get("reasons"), ensure_ascii=False))
            chk = next(c for c in v["checks"] if c["check"] == "migrate_vs_index")
            by_entry = {i["entry"]: i["status"] for i in chk["items"]}
            self.assertEqual(by_entry["loose-file"], "landed")


class ExitCodeAndWriteTest(unittest.TestCase):
    """main 层：verify.json 落卷+哑卷防线。"""

    def test_main_writes_verify_json_and_exit0(self) -> None:
        from runtime.cognition.verify import main
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live"])
            argv = [
                "--plan-file", str(run / "plan.json"),
                "--from-week", "W46", "--to-week", "W47",
                "--start-date", "2026-11-16",
                "--run-dir", str(run),
                "--run-id", "shift-W46-test",
                "--operating-root", str(root),
                "--run-id", "shift-W46-test", "--strict",   # v8 item1 必填
            ]
            self.assertEqual(main(argv), 0)
            v = json.loads((run / "verify.json").read_text(encoding="utf-8"))
            self.assertEqual(v["verdict"], "pass")
            self.assertEqual(v["run_id"], "shift-W46-test")

    def test_unwritable_run_dir_is_exit2(self) -> None:
        from runtime.cognition.verify import main
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root)
            blocker = root / "blocked"
            blocker.write_text("file not dir", encoding="utf-8")
            argv = [
                "--plan-file", str(run / "plan.json"),
                "--from-week", "W46", "--to-week", "W47",
                "--start-date", "2026-11-16",
                "--run-dir", str(blocker),
                "--operating-root", str(root),
                "--run-id", "shift-W46-test", "--strict",   # v8 item1 必填
            ]
            self.assertEqual(main(argv), 2)


class V8Item1ForcedRunIdStrictTest(unittest.TestCase):
    """v8 item1：run_id 对表强制 + strict 必填（对不上即 fail）。"""

    def test_run_id_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run, run_id="shift-W46-OTHER"))
            self.assertEqual(code, 2)
            rid = [c for c in v["checks"] if c["check"] == "run_id_match"][0]
            self.assertFalse(rid["ok"])
            self.assertIn("隔离主键", " ".join(rid["reasons"]))

    def test_strict_required_missing_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run, strict=False))
            self.assertEqual(code, 2)
            sr = [c for c in v["checks"] if c["check"] == "strict_required"][0]
            self.assertFalse(sr["ok"])

    def test_main_requires_run_id_arg(self):
        from runtime.cognition.verify import main
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            _mk_to_week(root, active=["live-tree"])
            argv = ["--plan-file", str(run / "plan.json"), "--from-week", "W46",
                    "--to-week", "W47", "--start-date", "2026-11-16",
                    "--run-dir", str(run), "--operating-root", str(root), "--strict"]
            with self.assertRaises(SystemExit):        # argparse required 拒
                main(argv)


class V8Item5RetryNormalizationTest(unittest.TestCase):
    """v8 item5：retry 编号隔离主键——run_id 本体去后缀·retry_seq/retry_of 字段化。"""

    def test_normalize_helper(self):
        from runtime.cognition.verify import normalize_run_id
        self.assertEqual(normalize_run_id("shift-W48-resume8-retry1"),
                         ("shift-W48-resume8", 1, "shift-W48-resume8"))
        self.assertEqual(normalize_run_id("shift-W48-resume8"), ("shift-W48-resume8", None, None))

    def test_verify_json_uses_base_run_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)                       # plan.run_id = shift-W46-test（本体）
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run, run_id="shift-W46-test-retry2"))
            self.assertEqual(code, 0)           # 带后缀输入→归一后对表通过
            self.assertEqual(v["run_id"], "shift-W46-test")
            self.assertEqual(v["retry_seq"], 2)
            self.assertEqual(v["retry_of"], "shift-W46-test")


if __name__ == "__main__":
    unittest.main()


# ── 1.1.0 WP5 对账红闸案族（2026-11-18·notice-185 统改施工白盒·拆解任务书获批面） ──

from runtime.cognition.plan_scope import reconcile_counts_readings
from runtime.cognition.verify import check_reconciliation


class WP5ReconciliationGateTest(unittest.TestCase):
    """WP5 对账红闸案族：counts↔readings 差额>0 即红（注入即红锚·
    check_plan_baseline 族同构形）。"""

    def test_injection_immediate_red_function_level(self) -> None:
        """函数级注入即红钉：counts.migrate=99 vs readings 1→(False, R1 差额)。"""
        plan = {
            "counts": {"migrate": 99, "keep": 0},
            "agent_readings": [{"tree": "a", "domain": "tree"}],
        }
        ok, reasons = check_reconciliation(plan)
        self.assertFalse(ok)
        self.assertTrue(any("R1" in r for r in reasons))

    def test_injection_immediate_red_run_verify_integration(self) -> None:
        """集成注入即红钉：run_verify 消费差额 plan→reconciliation check
        ok=False+verdict=fail+exit 2（红闸在链实证）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run)
            # 注入：counts.migrate=99（vs readings 域缺位→skip 面）——改注入形态：
            # 1.2.0 形 plan（带 agent_readings+counts 差额）
            plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
            plan["agent_readings"] = [{"tree": "live-tree", "domain": "tree",
                                       "annotation": "a", "rationale": "r",
                                       "evidence_ref": ["e"],
                                       "disposition": "migrate"}]
            plan["counts"]["migrate"] = 99
            (run / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 2)
            self.assertEqual(v["verdict"], "fail")
            rec = next(c for c in v["checks"] if c["check"] == "reconciliation")
            self.assertFalse(rec["ok"])
            self.assertTrue(any("R1" in r for r in rec["reasons"]))

    def test_zero_diff_passes_green(self) -> None:
        """零差额绿面钉：counts↔readings 一致 1.2.0 形 plan→reconciliation
        ok=True 零红（红闸不误伤）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            _mk_plan(run, migrate=["live-tree"])
            # v8 item1：strict migrate_vs_index 需 from 周 trees/ 实存（负 fixture 供树）
            (root / "2026-W46" / "trees" / "live-tree").mkdir(parents=True, exist_ok=True)
            plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
            plan["agent_readings"] = [
                {"tree": "live-tree", "domain": "tree", "annotation": "a",
                 "rationale": "r", "evidence_ref": ["e"],
                 "disposition": "migrate"},
            ]
            (run / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            _mk_to_week(root, active=["live-tree"])
            code, v = run_verify(_args(root, run))
            self.assertEqual(code, 0, json.dumps(v.get("reasons"), ensure_ascii=False))
            rec = next(c for c in v["checks"] if c["check"] == "reconciliation")
            self.assertTrue(rec["ok"])

    def test_old_shape_plan_skip_note_not_red(self) -> None:
        """1.0.0 旧形 plan（agent_readings 缺位）→对账域缺位 skip 注·零红
        （向后兼容容忍族——verify 消费面既有全绿零波及直证）。"""
        ok, reasons = check_reconciliation({"counts": {"migrate": 1, "keep": 0}})
        self.assertTrue(ok)
        self.assertTrue(any("skip" in r for r in reasons))

    def test_plan_baseline_fail_reconciliation_unavailable(self) -> None:
        """基准面缺失形：plan NOT_FOUND→reconciliation check 记不可用（不误报
        差额——红闸可用性面如实记）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_to_week(root)
            args = _args(root, root / "run")
            args.plan_file = str(root / "run" / "no-such-plan.json")
            code, v = run_verify(args)
            self.assertEqual(code, 2)
            rec = next(c for c in v["checks"] if c["check"] == "reconciliation")
            self.assertFalse(rec["ok"])
            self.assertTrue(any("不可用" in r or "failed" in r
                                for r in rec.get("reasons", [])))


class R4SanctionGateTest(unittest.TestCase):
    """①三态红闸案族（notice-214 款一·2026-11-19）：top_level 件强制逐件
    三态标注（迁/留/封）——缺/越域=红闸拒 pass。"""

    def test_missing_sanction_red(self) -> None:
        """缺三态词→红闸拒（R4 面直证）。"""
        plan = {
            "counts": {"migrate": 0, "keep": 0, "top_level": 1},
            "agent_readings": [{"tree": "t.md", "domain": "top_level",
                                "sanction": None}],
        }
        ok, diffs = reconcile_counts_readings(plan)
        self.assertFalse(ok)
        self.assertTrue(any("R4" in d for d in diffs))

    def test_out_of_domain_sanction_red(self) -> None:
        plan = {
            "counts": {"migrate": 0, "keep": 0, "top_level": 1},
            "agent_readings": [{"tree": "t.md", "domain": "top_level",
                                "sanction": "挂"}],
        }
        ok, diffs = reconcile_counts_readings(plan)
        self.assertFalse(ok)
        self.assertTrue(any("R4" in d for d in diffs))

    def test_three_domain_sanctions_green(self) -> None:
        """三态词全载（迁/留/封）→零红（红闸不误伤）。"""
        plan = {
            "counts": {"migrate": 0, "keep": 0, "top_level": 3},
            "agent_readings": [
                {"tree": "a", "domain": "top_level", "sanction": "迁"},
                {"tree": "b", "domain": "top_level", "sanction": "留"},
                {"tree": "c", "domain": "top_level", "sanction": "封"},
            ],
        }
        ok, diffs = reconcile_counts_readings(plan)
        self.assertTrue(ok, diffs)
        self.assertTrue(all("R4" not in d for d in diffs))
