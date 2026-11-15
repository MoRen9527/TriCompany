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


# ── 1.1.0 agent 化案族（2026-11-15 施工·设计定稿卷 §二笔 3+栏 A 裁决卷 §三） ──

from urllib.error import URLError


def _mock_agent_response(text: str) -> dict:
    """TriRMC agent loop JSON mode 响应形 mock（app.ts L605 {ok,turns,events[]}）。"""
    return {"ok": True, "turns": "completed",
            "events": [{"type": "assistant", "text": text}]}


def _agent_json(family: str, conf: float, reasons: str = "依据") -> str:
    import json as _j
    return _j.dumps({"family": family, "confidence": conf, "reasons": reasons},
                    ensure_ascii=False)


def _mk_default_tree(week: Path, name: str) -> Path:
    """慢道形态树 a)：无 tree-op 无 auth=degrade 默认 keep 候选。"""
    t = week / "trees" / name
    t.mkdir(parents=True)
    (t / "tick-log.md").write_text("log", encoding="utf-8")
    return t


def _mk_conflict_tree(week: Path, name: str) -> Path:
    """慢道形态 b)冲突树：tree-op status=closed（keep 向）∧ auth 未过期（migrate 向）。"""
    t = week / "trees" / name
    t.mkdir(parents=True)
    (t / "tree-op.json").write_text(json.dumps({"status": "closed"}), encoding="utf-8")
    expiry = (NOW + timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (t / "authorization.json").write_text(json.dumps({"expiry": expiry}), encoding="utf-8")
    return t


def _agent_args(root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        from_week="W46", to_week="W47", run_dir=str(root / "run"),
        run_id="r-agent", operating_root=str(root),
        op_id=None, start_date=None, agent_endpoint=None,
    )


class AgentSlowPathTest(unittest.TestCase):
    """慢道 agent 判断面案族（mock 注入·零真网络——mock.patch plan_scope._call_agent）。"""

    def _plan_with_mock(self, root: Path, agent_text: str):
        """通用编排：调用方 root（树已预造于其 week 下）+补 unresolved 真表行+
        patch _call_agent→run_plan。"""
        week = root / "2026-W46"
        (week / "OP-202611-W46-001.unresolved-items.md").write_text(
            "| `CARRY-20260728-004` | P1 | tui | CTO→FSD | frozen——冻结维持 | 注 |\n"
            "| `CARRY-042` | P2 | 旧债 | COS | 待裁 | 注 |\n",
            encoding="utf-8",
        )  # 真表行形（照 PlanAllPass fixture·parse_carry_rows 需表行）
        with mock.patch(
            "runtime.cognition.plan_scope._call_agent",
            return_value=_mock_agent_response(agent_text),
        ) as m:
            code, plan = run_plan(_agent_args(root), now=NOW)
        return code, plan, m

    def test_slow_default_tree_agent_carry_periodic_to_migrate(self) -> None:
        """慢道正常判定形①：默认 keep 树→agent 判 carry_periodic→投影 migrate
        （契约三族·readings source=agent plan_family=migrate）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_default_tree(week, "live-a")
        code, plan, m = self._plan_with_mock(
            root, _agent_json("carry_periodic", 0.9, "weekly rolling"),
        )
        self.assertEqual(code, 0, json.dumps(plan.get("reasons"), ensure_ascii=False))
        self.assertTrue(any(x["entry"] == "live-a" for x in plan["migrate"]))
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "live-a")
        self.assertEqual(rd["source"], "agent")
        self.assertEqual(rd["family"], "carry_periodic")
        self.assertEqual(rd["plan_family"], "migrate")
        mig_entry = next(x for x in plan["migrate"] if x["entry"] == "live-a")
        self.assertIn("agent_family_carry_periodic", mig_entry["reason_codes"])
        self.assertTrue(m.called)

    def test_conflict_tree_routes_to_agent(self) -> None:
        """慢道正常判定形②：冲突树（status closed∧auth active）→agent 判
        weekly_selfbuild→keep+selfbuild_expected 标注（现役短路链被 agent 面接管）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_conflict_tree(week, "tick-tree")
        code, plan, _ = self._plan_with_mock(
            root, _agent_json("weekly_selfbuild", 0.85, "selfbuild tick tree"))
        self.assertEqual(code, 0)
        self.assertTrue(any(k["entry"] == "tick-tree" for k in plan["keep"]))
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "tick-tree")
        self.assertEqual(rd["annotation"], "selfbuild_expected")
        self.assertEqual(rd["plan_family"], "keep")

    def test_agent_output_malformed_fail_closed(self) -> None:
        """结构门拒收形：family 越五枚举值域→keep+agent_output_malformed+
        readings source=failed_fallback（替身禁令精神·agent 输出不可信面不盲收）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_default_tree(week, "t1")
        code, plan, _ = self._plan_with_mock(
            root, _agent_json("migration", 0.9, "x"))  # 越值域
        self.assertEqual(code, 0)
        self.assertTrue(any(k["entry"] == "t1" for k in plan["keep"]))
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "t1")
        self.assertEqual(rd["source"], "failed_fallback")
        self.assertEqual(rd["plan_family"], "keep")

    def test_agent_low_confidence_conservative_keep(self) -> None:
        """低置信降级形：confidence 0.4<0.6→投影前拦 keep+agent_low_confidence
        （误封存可候审补救·误迁移不可逆）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_default_tree(week, "t2")
        code, plan, _ = self._plan_with_mock(
            root, _agent_json("carry_periodic", 0.4, "unsure"))
        self.assertTrue(any(k["entry"] == "t2" for k in plan["keep"]))
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "t2")
        self.assertEqual(rd["source"], "failed_fallback")
        self.assertEqual(rd["confidence"], 0.4)

    def test_agent_call_failed_urlerror_fail_closed(self) -> None:
        """调用失败 fail-closed 形：URLError→keep+agent_call_failed:URLError·段照跑。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_default_tree(week, "t3")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        side_effect=URLError("conn refused")):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)  # fail-closed=段不炸·plan.json 照落卷
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "t3")
        self.assertEqual(rd["source"], "failed_fallback")
        self.assertIn("agent_call_failed", rd["reasons"])
        self.assertTrue(any(k["entry"] == "t3" for k in plan["keep"]))

    def test_agent_timeout_fail_closed_zero_retry(self) -> None:
        """超时形：TimeoutError→keep+agent_call_failed:TimeoutError（60s 零重试语义·
        mock 面只验异常族投影——重试 0 次由 _call_agent 无循环实现保证）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_default_tree(week, "t4")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        side_effect=TimeoutError("timed out")) as m:
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        self.assertEqual(m.call_count, 1)  # 慢树 1 次（本 fixture 无顶层件·零重试直证）
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "t4")
        self.assertIn("TimeoutError", rd["reasons"])

    def test_five_family_projection_table(self) -> None:
        """五分类投影案：五 family 五树·side_effect 依 sorted 名序返回——
        carry_periodic→migrate·其余四族→keep+各语义标注（栏 A 裁决 §二表直证）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        names = ["a-carry", "b-templated", "c-selfbuild", "d-ongoing", "e-shot"]
        for n in names:
            _mk_default_tree(week, n)
        verdicts = [
            ("carry_periodic", 0.9), ("new_week_templated", 0.9),
            ("weekly_selfbuild", 0.9), ("active_tree_ongoing", 0.9),
            ("one_shot", 0.9),
        ]
        side = [_mock_agent_response(_agent_json(f, c)) for f, c in verdicts]
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        side_effect=side):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0, json.dumps(plan.get("reasons"), ensure_ascii=False))
        by_tree = {r["tree"]: r for r in plan["agent_readings"]}
        self.assertEqual(by_tree["a-carry"]["plan_family"], "migrate")
        self.assertEqual(by_tree["b-templated"]["annotation"],
                         "expected_absent@W47")
        self.assertEqual(by_tree["c-selfbuild"]["annotation"], "selfbuild_expected")
        self.assertEqual(by_tree["d-ongoing"]["annotation"],
                         "ongoing_ledger_handover")
        self.assertEqual(by_tree["e-shot"]["annotation"], "one_shot_frozen")
        mig = {x["entry"] for x in plan["migrate"]}
        self.assertEqual(mig, {"a-carry"})  # 树级 migrate 收敛面（栏 A §二语义）

    def test_slow_path_limit_skips_over(self) -> None:
        """附款①上界断言：16 棵慢道树→sorted 名序前 15 进 agent·第 16 棵
        skipped_over_limit fail-closed keep（段时长保险丝）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        for i in range(16):
            _mk_default_tree(week, f"tree-{i:02d}")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        return_value=_mock_agent_response(
                            _agent_json("one_shot", 0.9))) as m:
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        self.assertEqual(m.call_count, 15)  # 前 15 树各 1 次（第 16 skipped 不调用）
        skipped = [r for r in plan["agent_readings"]
                   if "skipped_over_limit" in r["reasons"]]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["source"], "failed_fallback")

    def test_closeout_conflict_gate(self) -> None:
        """附款②机械门：agent 判 carry_periodic（投影 migrate）∧树含 closeout 形
        文件名→降级 keep+migrate_closeout_conflict 候人工复核。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        t = _mk_default_tree(week, "review-tree")
        (t / "fsd-brief-closeout-20261115.md").write_text("x", encoding="utf-8")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        return_value=_mock_agent_response(
                            _agent_json("carry_periodic", 0.95))):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        self.assertTrue(any(k["entry"] == "review-tree" for k in plan["keep"]))
        rd = next(r for r in plan["agent_readings"] if r["tree"] == "review-tree")
        self.assertEqual(rd["gate"], "migrate_closeout_conflict")
        self.assertIn("migrate_closeout_conflict",
                      next(k["reason_codes"] for k in plan["keep"]
                           if k["entry"] == "review-tree"))

    def test_ongoing_count_note_over_threshold(self) -> None:
        """栏 A ⑥未完树计数判据（判据面非闸面）：3 棵 active_tree_ongoing→
        各该 readings reasons 如实尾注 week_unfinished_trees=3·不拦停不改判。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        for n in ("on-a", "on-b", "on-c"):
            _mk_default_tree(week, n)
        side = [_mock_agent_response(_agent_json("active_tree_ongoing", 0.9))
                for _ in range(4)]  # 树 3+顶层件 1
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        side_effect=side):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        ongs = [r for r in plan["agent_readings"]
                if r["family"] == "active_tree_ongoing"]
        self.assertEqual(len(ongs), 3)
        for r in ongs:
            self.assertIn("week_unfinished_trees=3", r["reasons"])

    def test_bidirectional_with_agent_tree(self) -> None:
        """双向断言协作案：agent 判定树入 M∪K=S——carry_periodic 树进 migrate·
        bidirectional_ok=True·断言权在脚本（agent 只是分类读数生产者）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_default_tree(week, "agent-mig")
        (week / "trees" / "closed-one").mkdir(parents=True)
        (week / "trees" / "closed-one" / "tree-op.json").write_text(
            json.dumps({"status": "done"}), encoding="utf-8")  # 快道 keep
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        return_value=_mock_agent_response(
                            _agent_json("carry_periodic", 0.9))):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        self.assertTrue(plan["bidirectional_ok"])
        self.assertEqual(plan["counts"]["migrate"], 1)
        self.assertEqual(plan["counts"]["keep"], 1)

    def test_fast_path_untouched_alongside_slow(self) -> None:
        """快道回归钉：同场快道树（auth active+tree-op closed）照 fast_path 直出·
        慢道树走 agent——分流互不染（既有行为零变·readings 元面直证）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_tree_auth_active(week, "fast-live")
        done = week / "trees" / "fast-done"
        done.mkdir()
        (done / "tree-op.json").write_text(json.dumps({"status": "closed"}),
                                           encoding="utf-8")
        _mk_default_tree(week, "slow-x")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        return_value=_mock_agent_response(
                            _agent_json("one_shot", 0.9))) as m:
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        by_tree = {r["tree"]: r for r in plan["agent_readings"]}
        self.assertEqual(by_tree["fast-live"]["source"], "fast_path")
        self.assertEqual(by_tree["fast-done"]["source"], "fast_path")
        self.assertEqual(by_tree["slow-x"]["source"], "agent")
        mig = {x["entry"] for x in plan["migrate"]}
        self.assertEqual(mig, {"fast-live"})  # 快道机械判零改直证


class TopFilesAgentTest(unittest.TestCase):
    """顶层文件判断域案族（栏 A 裁决①·纯读数面零触三清单）。"""

    def test_top_files_domain_readings_zero_list_touch(self) -> None:
        """顶层 2 件判断：carry_periodic/new_week_templated 各投——readings
        domain=top_level·三清单零触（M∪K=S 域=trees/ 不变）。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        (week / "company-demand-pool.md").write_text("pool", encoding="utf-8")
        (week / "cfo-quota-daily-w46.md").write_text("q", encoding="utf-8")
        verdict_files = json.dumps({"files": [
            {"name": "company-demand-pool.md", "family": "carry_periodic",
             "confidence": 0.9, "reasons": "weekly rolling pool"},
            {"name": "cfo-quota-daily-w46.md", "family": "new_week_templated",
             "confidence": 0.85, "reasons": "weekly suffix param"},
        ]}, ensure_ascii=False)
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        return_value=_mock_agent_response(verdict_files)):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        tops = [r for r in plan["agent_readings"] if r["domain"] == "top_level"]
        self.assertEqual(len(tops), 2)
        by_name = {r["tree"]: r for r in tops}
        self.assertEqual(by_name["company-demand-pool.md"]["plan_family"],
                         "migrate")  # 投影读数面（迁移器消费形候 CTO 面·清单零触）
        self.assertEqual(by_name["cfo-quota-daily-w46.md"]["annotation"],
                         "expected_absent@W47")
        # 三清单零触直证：顶层件名不入 migrate/keep
        all_listed = {x["entry"] for x in plan["migrate"] + plan["keep"]}
        self.assertNotIn("company-demand-pool.md", all_listed)
        self.assertNotIn("cfo-quota-daily-w46.md", all_listed)
        self.assertTrue(plan["bidirectional_ok"])

    def test_top_files_call_failed_zero_action(self) -> None:
        """顶层判断失败 fail-closed：逐件 failed_fallback 零动作读数·段照跑。"""
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        (week / "daily-progress.md").write_text("d", encoding="utf-8")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        side_effect=URLError("down")):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        tops = [r for r in plan["agent_readings"] if r["domain"] == "top_level"]
        self.assertEqual(len(tops), 1)
        self.assertEqual(tops[0]["source"], "failed_fallback")
        self.assertEqual(tops[0]["plan_family"], "keep")
        self.assertIn("agent_call_failed", tops[0]["reasons"])


class CarryAnnotationTest(unittest.TestCase):
    """carry 行三标注案（联审附款三·既有键零动纯增补）。"""

    def test_carry_row_source_dest_pending_reason(self) -> None:
        import tempfile
        p = Path(tempfile.mkdtemp()) / "OP.unresolved-items.md"
        p.write_text(
            "| `CARRY-20260728-004` | P1 | tui | CTO→FSD | frozen——冻结维持 | 注 |\n"
            "| `CARRY-042` | P2 | 旧债 | COS | 待裁 | 注 |\n",
            encoding="utf-8",
        )
        rows, other, err = parse_carry_rows(p)
        self.assertIsNone(err)
        self.assertEqual(rows[0]["source"], "unresolved-items §1 现役区")
        self.assertEqual(rows[0]["dest"], "frozen")
        self.assertIn("冻结", rows[0]["pending_reason"])
        self.assertEqual(rows[1]["dest"], "pending_review")
        self.assertIn("候人工复核", rows[1]["pending_reason"])
        # 既有键零动直证
        self.assertEqual(rows[0]["status_to"], "frozen")
        self.assertEqual(rows[0]["carry_id"], "CARRY-20260728-004")


class ContractV110Test(unittest.TestCase):
    """1.1.0 契约面案：plan_version 升版+agent_readings 键族+既有十键零动。"""

    def test_contract_keys_and_version(self) -> None:
        import tempfile
        root = Path(tempfile.mkdtemp())
        week = _mk_week(root)
        _mk_tree_auth_active(week, "live")
        (week / "company-demand-pool.md").write_text("p", encoding="utf-8")
        with mock.patch("runtime.cognition.plan_scope._call_agent",
                        return_value=_mock_agent_response(json.dumps({"files": [
                            {"name": "company-demand-pool.md",
                             "family": "carry_periodic", "confidence": 0.9,
                             "reasons": "rolling"}]}, ensure_ascii=False))):
            code, plan = run_plan(_agent_args(root), now=NOW)
        self.assertEqual(code, 0)
        self.assertEqual(plan["plan_version"], "1.1.0")
        # 既有十键零动+新键一族
        for key in ("plan_version", "run_id", "from_week", "to_week",
                    "migrate", "keep", "carry_over", "counts",
                    "bidirectional_ok", "check_time"):
            self.assertIn(key, plan)
        self.assertIn("agent_readings", plan)
        rd = {r["tree"]: r for r in plan["agent_readings"]}
        self.assertEqual(rd["live"]["source"], "fast_path")       # 快道树元
        self.assertEqual(
            rd["company-demand-pool.md"]["domain"], "top_level")  # 顶层件元
        # 结构门对 1.1.0 形零破（extra keys 容忍族）
        self.assertEqual(_structure_gate(plan), [])


if __name__ == "__main__":
    unittest.main()


class ExtractAgentTextDeltaRepairTest(unittest.TestCase):
    """勘修改动面新案（6272005 复验席补位·2026-11-15）：delta 主路径+旧键兼容。

    根因定谳卷 2575cd935：引擎文本信道=content_delta（键=delta）——旧提取键
    （text/content/message）不含 delta→逆序命中 tool_result 裸输出→判卷必败
    =unparseable 15 族。修复形=delta 串联主路径+旧键兼容保留。"""

    def test_delta_concat_primary_path(self) -> None:
        """正路径：content_delta 分段×3 串联=完整判定文·tool_result 裸输出不沾。"""
        from runtime.cognition.plan_scope import _extract_agent_text
        result = {"events": [
            {"type": "content_delta", "delta": '{"verdict":'},
            {"type": "content_delta", "delta": ' "pass",'},
            {"type": "content_delta", "delta": ' "reasons": []}'},
            {"type": "tool_result", "content": "裸工具输出噪声·不得命中"},
        ]}
        self.assertEqual(_extract_agent_text(result),
                         '{"verdict": "pass", "reasons": []}')

    def test_delta_empty_segments_skipped(self) -> None:
        """边界：空/空白 delta 段跳过（strip 过滤）·有效段仍串联。"""
        from runtime.cognition.plan_scope import _extract_agent_text
        result = {"events": [
            {"type": "content_delta", "delta": "A"},
            {"type": "content_delta", "delta": "   "},
            {"type": "content_delta", "delta": "B"},
        ]}
        self.assertEqual(_extract_agent_text(result), "AB")

    def test_events_non_list_returns_none(self) -> None:
        """异常路径：events 非 list→None（不抛破链）。"""
        from runtime.cognition.plan_scope import _extract_agent_text
        self.assertIsNone(_extract_agent_text({"events": "nope"}))
        self.assertIsNone(_extract_agent_text({}))

    def test_legacy_keys_reverse_compat(self) -> None:
        """兼容路径：纯旧键事件族（无 delta）→逆序命中末事件 text（旧族活体）。"""
        from runtime.cognition.plan_scope import _extract_agent_text
        result = {"events": [
            {"type": "text", "text": "旧形早段"},
            {"type": "text", "text": "旧形末段判定文"},
        ]}
        self.assertEqual(_extract_agent_text(result), "旧形末段判定文")


class PlanPayloadFromWeekDirTest(unittest.TestCase):
    """勘修改动面新案②（6272005）：plan 载荷随载 from_week_dir year-W 正形。

    file missing 7 两形并存机制面根治锚：下游消费面以载荷 from_week_dir 为准
    （裸 from_week 无年段=缺位根因）。"""

    def _args(self, root: str, **kw) -> argparse.Namespace:
        base = dict(
            from_week="W46", to_week="W47", run_dir=str(Path(root) / "run"),
            run_id="r", operating_root=root, op_id=None, start_date=None,
        )
        base.update(kw)
        return argparse.Namespace(**base)

    def test_payload_carries_resolved_dir(self) -> None:
        """正形：resolved 周目录→载荷 from_week_dir=year-W 形（2026-W46）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            week = root / "2026-W46"
            (week / "trees").mkdir(parents=True)
            (week / "trees" / "note.md").write_text("x", encoding="utf-8")
            code, plan = run_plan(self._args(str(root), start_date="2026-11-16"), now=NOW)
            self.assertEqual(code, 0, json.dumps(plan.get("reasons"), ensure_ascii=False))
            self.assertIn("from_week_dir", plan)
            self.assertEqual(plan["from_week_dir"], "2026-W46")

    def test_payload_dir_none_when_unresolved(self) -> None:
        """旁证缺位形：unresolved→from_week_dir=None·不拦（旁证语义）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            code, plan = run_plan(self._args(str(root)), now=NOW)
            self.assertIn("from_week_dir", plan)
            self.assertIsNone(plan["from_week_dir"])
