"""FADE-001 阶段 3 plan_scope 单测（白盒·注入式案族·DEM-009 同款精神）。

案族对表（fsd-ten-stage-tech-collab §二.7+CTO 裁②精化+STE 锚草案五条）：
  ①schema 结构门断言（STE 锚①·tri-fade011-plan 结构门先例——协议管不变量·extra 容忍）
  ②双向枚举断言（STE 锚②）  ③carry_over 带状态去向（STE 锚③·CARRY 两形）
  ⑤替身禁令负路径三向（STE 锚⑤·S51 先例：NOT_FOUND/不可读 FAIL/结构门非橡皮图章）

runner 形态注（STE 锚族原则 5）：本件=unittest 案族·毕报读数声明=显式模块指定形
  `python -m unittest runtime.cognition.test_plan_scope`（禁目录形笼统 fail）。
"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from runtime.cognition.plan_scope import (
    PLAN_VERSION,
    _structure_gate,
    bidirectional_check,
    classify_dir,
    parse_carry_rows,
    run_plan,
    scan_trees,
)

NOW = datetime(2026, 11, 15, 15, 50, 0, tzinfo=timezone.utc)


def _mk_week(root: Path) -> Path:
    """造最小周目录形（实盘年段名正形）：2026-W46/{trees/, OP-*.unresolved-items.md}。"""
    week = root / "2026-W46"
    (week / "trees").mkdir(parents=True)
    return week


def _mk_tree_auth_active(week: Path, name: str) -> Path:
    t = week / "trees" / name
    t.mkdir()
    expiry = (NOW + timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (t / "authorization.json").write_text(
        json.dumps({"expiry": expiry}), encoding="utf-8"
    )
    return t


class PlanAllPassTest(unittest.TestCase):
    """全过案：migrate+keep+散文件+CARRY 两形→exit 0·plan.json 结构全。"""

    def test_all_pass_structure_and_exit0(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = _mk_week(root)
            _mk_tree_auth_active(week, "fade001-live")
            done = week / "trees" / "bod-tick"
            done.mkdir()
            (done / "tree-op.json").write_text(
                json.dumps({"status": "closed"}), encoding="utf-8"
            )
            (week / "trees" / "mapping-note.md").write_text("x", encoding="utf-8")
            (week / "OP-202611-W46-001.unresolved-items.md").write_text(
                "| `CARRY-20260728-004` | P1 | tui 对齐 | CTO→FSD | frozen——冻结维持 | 注 |\n"
                "| `CARRY-042` | P2 | 旧债 | COS | 待裁 | 注 |\n"
                "| `REGR-001`（族） | P1 | 四回归 | 研发 | 待修 | 注 |\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                from_week="W46", to_week="W47", run_dir=str(root / "run"),
                run_id="shift-W46-20261115T155000Z", operating_root=str(root),
                op_id=None, start_date=None,
            )
            code, plan = run_plan(args, now=NOW)
            self.assertEqual(code, 0, json.dumps(plan, ensure_ascii=False))
            self.assertEqual(plan["verdict"], "pass")
            self.assertTrue(plan["bidirectional_ok"])
            self.assertEqual(plan["counts"]["migrate"], 1)
            self.assertEqual(plan["counts"]["keep"], 2)
            self.assertEqual(plan["counts"]["carry_over"], 2)
            self.assertEqual(plan["other_unresolved_count"], 1)
            self.assertEqual(plan["migrate"][0]["entry"], "fade001-live")
            # 发现 4：kind=is_dir 实值——目录标 dir·散文件标 file（不再恒 dir）
            self.assertEqual(plan["migrate"][0]["kind"], "dir")
            keep_by_entry = {k["entry"]: k for k in plan["keep"]}
            self.assertEqual(keep_by_entry["bod-tick"]["kind"], "dir")
            self.assertEqual(keep_by_entry["mapping-note.md"]["kind"], "file")
            self.assertEqual(plan["carry_over"][0]["carry_id"], "CARRY-20260728-004")
            self.assertEqual(plan["carry_over"][0]["status_to"], "frozen")
            self.assertEqual(plan["carry_over"][1]["carry_id"], "CARRY-042")
            self.assertEqual(plan["carry_over"][1]["status_to"], "pending_review")
            # plan.json 已落卷（main 落卷面由 ExitCodeTest 覆盖·此处 run_plan 层断言结构门键族）
            for key in ("plan_version", "run_id", "from_week", "to_week",
                        "migrate", "keep", "carry_over", "counts",
                        "bidirectional_ok", "check_time"):
                self.assertIn(key, plan)
            self.assertEqual(plan["plan_version"], PLAN_VERSION)


class ClassifyChainTest(unittest.TestCase):
    """degrade 链白盒：tree-op status→authorization expiry→默认 keep（保守方向）。"""

    def _cls(self, tree: Path) -> tuple[str, list[str]]:
        return classify_dir(tree, NOW)

    def test_tree_op_done_is_keep(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            (t / "tree-op.json").write_text('{"status": "done"}', encoding="utf-8")
            cat, reasons = self._cls(t)
            self.assertEqual(cat, "keep")
            self.assertEqual(reasons, ["tree_op_status:done"])

    def test_tree_op_active_is_migrate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            (t / "tree-op.json").write_text('{"status": "active"}', encoding="utf-8")
            cat, _ = self._cls(t)
            self.assertEqual(cat, "migrate")

    def test_no_markers_defaults_keep(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            (t / "tick-log.md").write_text("log", encoding="utf-8")
            cat, reasons = self._cls(t)
            self.assertEqual(cat, "keep")
            self.assertIn("no_active_markers_default_keep", reasons)

    def test_authorization_expired_is_keep(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            expired = (NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            (t / "authorization.json").write_text(
                json.dumps({"expiry": expired}), encoding="utf-8"
            )
            cat, reasons = self._cls(t)
            self.assertEqual(cat, "keep")
            self.assertIn("authorization_expired", reasons)

    def test_authorization_active_is_migrate_distinct_reason(self) -> None:
        """发现 30 拆码案①：exp>now 确证活授权=authorization_active——
        与解析败态读数分家（原合一码系判读歧义源·CTO mount-gate 亲历）。"""
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            future = (NOW + timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")
            (t / "authorization.json").write_text(
                json.dumps({"expiry": future}), encoding="utf-8"
            )
            cat, reasons = self._cls(t)
            self.assertEqual(cat, "migrate")
            self.assertEqual(reasons, ["authorization_active"])

    def test_authorization_unparsable_is_migrate_conservative(self) -> None:
        """解析败=保守在途（过期判断不可得时不放行·漏报毒于误报）。
        发现 30 拆码案②：reason 码=authorization_unparsable（原合一码拆两态）。"""
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            (t / "authorization.json").write_text(
                json.dumps({"expiry": "not-a-date"}), encoding="utf-8"
            )
            cat, reasons = self._cls(t)
            self.assertEqual(cat, "migrate")
            self.assertIn("authorization_unparsable", reasons)
            self.assertNotIn(
                "authorization_active_or_unparsable", reasons
            )  # 旧合一码退役断言（防回退）

    def test_bad_tree_op_degrades_not_crashes(self) -> None:
        """坏 tree-op.json=降级续链非炸（替身禁令边界：降级到 authorization/keep 面）。"""
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t"
            t.mkdir()
            (t / "tree-op.json").write_text("{ broken json", encoding="utf-8")
            cat, _ = self._cls(t)
            self.assertEqual(cat, "keep")


class CarryRowsTest(unittest.TestCase):
    """CARRY 两形+other 计数+缺文件合法空集。"""

    def test_two_forms_and_other_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "OP-202611-W46-001.unresolved-items.md"
            p.write_text(
                "| `CARRY-20260728-006` | P2 | tui P2 | CTO | frozen——冻结维持（W35 CEO 裁） | 注 |\n"
                "| `CARRY-005` | P3 | 旧账 | COS | 已修·销账（fa8c2e8a1） | 注 |\n"
                "| `REGR-004/005`（族） | P1 | 回归 | 研发 | 待修 | 注 |\n"
                "| `BUG-20260805-003` | - | 别名 | SDE | 已修·销账 | 注 |\n",
                encoding="utf-8",
            )
            rows, other, err = parse_carry_rows(p)
            self.assertIsNone(err)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["carry_id"], "CARRY-20260728-006")
            self.assertEqual(rows[0]["status_to"], "frozen")
            self.assertEqual(rows[1]["status_to"], "closed")
            self.assertEqual(other, 2)  # REGR+BUG 进 other 不进 carry_over

    def test_missing_file_is_legal_empty(self) -> None:
        rows, other, err = parse_carry_rows(Path("Z:/no/such/file.md"))
        self.assertEqual((rows, other, err), ([], 0, None))


class BidirectionalTest(unittest.TestCase):
    """双向枚举断言纯函数白盒（STE 锚②）。"""

    ENTRIES = {"a": ["migrate"], "b": ["keep"], "c.md": ["keep"]}

    def test_pass_full_coverage(self) -> None:
        ok, v = bidirectional_check(self.ENTRIES, ["a"], ["b", "c.md"])
        self.assertTrue(ok)
        self.assertEqual(v, [])

    def test_uncovered_violation(self) -> None:
        ok, v = bidirectional_check(self.ENTRIES, [], ["b"])
        self.assertFalse(ok)
        self.assertTrue(any("uncovered" in x for x in v))

    def test_overlap_violation(self) -> None:
        ok, v = bidirectional_check(self.ENTRIES, ["a"], ["a", "b", "c.md"])
        self.assertFalse(ok)
        self.assertTrue(any("overlap" in x for x in v))

    def test_phantom_violation(self) -> None:
        """清单外幽灵（清单内不存在=分类器替身产物·防假绿）。"""
        ok, v = bidirectional_check(self.ENTRIES, ["a", "ghost"], ["b", "c.md"])
        self.assertFalse(ok)
        self.assertTrue(any("phantom" in x for x in v))


class SubstituteBanTest(unittest.TestCase):
    """替身禁令三向（STE 锚⑤·S51 先例形）。"""

    def _args(self, root: str, run: str) -> argparse.Namespace:
        return argparse.Namespace(
            from_week="W46", to_week="W47", run_dir=run,
            run_id="r", operating_root=root, op_id=None, start_date=None,
        )

    def test_not_found_is_fail_expected_not_substitute(self) -> None:
        """①NOT_FOUND：trees 缺失→exit 2 verdict=fail·零替身清单。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            code, plan = run_plan(self._args(str(root), str(root / "run")), now=NOW)
            self.assertEqual(code, 2)
            self.assertEqual(plan["verdict"], "fail")
            self.assertEqual(plan["migrate"], [])
            self.assertTrue(any("NOT_FOUND" in r for r in plan["reasons"]))

    def test_unreadable_dir_is_fail_expected(self) -> None:
        """②不可读：扫描异常→exit 2·不造空集替身（mock iterdir 注入）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = _mk_week(root)
            args = self._args(str(root), str(root / "run"))
            with mock.patch.object(
                Path, "iterdir", side_effect=PermissionError(13, "denied")
            ):
                code, plan = run_plan(args, now=NOW)
            self.assertEqual(code, 2)
            self.assertEqual(plan["verdict"], "fail")
            self.assertTrue(any("unreadable" in r for r in plan["reasons"]))

    def test_structure_gate_not_rubber_stamp(self) -> None:
        """③结构门非橡皮图章：counts 与清单实长不符=毒化拦（禁假卷）。"""
        poisoned = {
            "plan_version": PLAN_VERSION, "run_id": "r", "from_week": "W46",
            "to_week": "W47", "migrate": [{"entry": "a"}], "keep": [],
            "carry_over": [], "counts": {"migrate": 2, "keep": 0, "carry_over": 0},
            "bidirectional_ok": True, "check_time": NOW.isoformat(),
        }
        errors = _structure_gate(poisoned)
        self.assertTrue(any("migrate" in e for e in errors))


class StructureGateExtraKeysTest(unittest.TestCase):
    """协议管不变量实例管载体（tri-fade011 先例）：extra keys 容忍。"""

    GOOD = {
        "plan_version": PLAN_VERSION, "run_id": "r", "from_week": "W46",
        "to_week": "W47", "migrate": [], "keep": [{"entry": "b"}],
        "carry_over": [], "counts": {"migrate": 0, "keep": 1, "carry_over": 0},
        "bidirectional_ok": True, "check_time": NOW.isoformat(),
        "future_field": {"whatever": 1},
    }

    def test_extra_keys_tolerated(self) -> None:
        self.assertEqual(_structure_gate(dict(self.GOOD)), [])

    def test_missing_required_key_rejected(self) -> None:
        bad = dict(self.GOOD)
        del bad["bidirectional_ok"]
        errors = _structure_gate(bad)
        self.assertTrue(any("bidirectional_ok" in e for e in errors))

    def test_bidir_contradiction_rejected(self) -> None:
        bad = dict(self.GOOD)
        bad["bidirectional_ok"] = False
        del bad["future_field"]
        errors = _structure_gate(bad)
        self.assertTrue(any("矛盾态" in e for e in errors))


class IndexDriftTest(unittest.TestCase):
    """index 旁证层：脱节读数如实·读败不拦（§二.8①）。"""

    def test_drift_reading(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            week = Path(td)
            (week / "OP-202611-W46-001.json").write_text(
                json.dumps({"activeTrees": [], "doneTreesThisWeek": []}),
                encoding="utf-8",
            )

            from runtime.cognition.plan_scope import index_drift
            d = index_drift(week, migrate_count=3)
            self.assertEqual(d["index_activeTrees"], 0)
            self.assertEqual(d["plan_migrate"], 3)

    def test_no_index_is_note_not_error(self) -> None:
        from runtime.cognition.plan_scope import index_drift
        with tempfile.TemporaryDirectory() as td:
            d = index_drift(Path(td), 0)
            self.assertIn("note", d)
            self.assertNotIn("error", d)


class ExitCodeAndWriteTest(unittest.TestCase):
    """exit code 案+plan.json 落卷面（main 层）。"""

    def test_main_writes_plan_json_and_exit0(self) -> None:
        from runtime.cognition.plan_scope import main
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = _mk_week(root)
            _mk_tree_auth_active(week, "live-tree")
            argv = [
                "--from-week", "W46", "--to-week", "W47",
                "--run-dir", str(root / "run"),
                "--run-id", "shift-W46-test",
                "--operating-root", str(root),
            ]
            code = main(argv)
            self.assertEqual(code, 0)
            plan = json.loads((root / "run" / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["verdict"], "pass")
            self.assertEqual(plan["run_id"], "shift-W46-test")

    def test_unwritable_run_dir_is_exit2(self) -> None:
        """落卷败=哑卷防线 exit 2（同 qualify run dir 语义族）。"""
        from runtime.cognition.plan_scope import main
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = _mk_week(root)
            _mk_tree_auth_active(week, "live-tree")
            blocker = root / "run"
            blocker.write_text("i am a file, not a dir", encoding="utf-8")
            argv = [
                "--from-week", "W46", "--to-week", "W47",
                "--run-dir", str(blocker),
                "--operating-root", str(root),
            ]
            self.assertEqual(main(argv), 2)


class WeekDirResolveTest(unittest.TestCase):
    """周目录年段名解析（实盘 `2026-W46` 形·实弹预演第二处实锚）。"""

    def _args(self, root: str, **kw) -> argparse.Namespace:
        base = dict(
            from_week="W46", to_week="W47", run_dir=str(Path(root) / "run"),
            run_id="r", operating_root=root, op_id=None, start_date=None,
        )
        base.update(kw)
        return argparse.Namespace(**base)

    def test_start_date_resolves_year_prefixed_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = root / "2026-W46"
            (week / "trees").mkdir(parents=True)
            _mk_tree_auth_active(week, "live")
            code, plan = run_plan(
                self._args(str(root), start_date="2026-11-16"), now=NOW
            )
            self.assertEqual(code, 0, json.dumps(plan.get("reasons"), ensure_ascii=False))
            self.assertEqual(plan["counts"]["migrate"], 1)

    def test_glob_fallback_unique_hit(self) -> None:
        """无 start_date→glob `*-W46` 唯一命中 fallback（裸 W46 不命中=实盘形必须年段）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = root / "2026-W46"
            (week / "trees").mkdir(parents=True)
            (week / "trees" / "note.md").write_text("x", encoding="utf-8")
            code, plan = run_plan(self._args(str(root)), now=NOW)
            self.assertEqual(code, 0)
            self.assertEqual(plan["counts"]["keep"], 1)

    def test_ambiguous_multi_hit_fails_closed(self) -> None:
        """跨年双命中（2025-W46+2026-W46）无 start_date→exit 2 不猜。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for y in ("2025", "2026"):
                (root / f"{y}-W46" / "trees").mkdir(parents=True)
            code, plan = run_plan(self._args(str(root)), now=NOW)
            self.assertEqual(code, 2)
            self.assertEqual(plan["verdict"], "fail")
            self.assertTrue(any("ambiguous" in r for r in plan["reasons"]))

    def test_bare_week_dir_not_matched(self) -> None:
        """裸 `W46` 目录名 glob 不命中→NOT_FOUND（实弹预演第一跑实锚形态）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = root / "W46"
            (week / "trees").mkdir(parents=True)
            code, plan = run_plan(self._args(str(root)), now=NOW)
            self.assertEqual(code, 2)
            self.assertTrue(any("NOT_FOUND" in r for r in plan["reasons"]))


if __name__ == "__main__":
    unittest.main()
