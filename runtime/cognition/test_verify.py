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
        operating_root=str(root), strict=False,
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
            self.assertEqual(names, ["plan_baseline", "gamma_week", "new_week_index"])
            self.assertFalse(v["strict_mode"])
            self.assertTrue(v["check_time"])


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
            ]
            self.assertEqual(main(argv), 2)


if __name__ == "__main__":
    unittest.main()
