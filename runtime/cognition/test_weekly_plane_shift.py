"""weekly_plane_shift.shift_carry_over 单测（笔 5 头部刷新改形·2026-11-15）。

案族对表（CTO 增补令笔 5·设计定稿卷 §二）：
  ① LG-072 新形四字段刷新（标题周号/sourceOfTruth 路径/lastSyncedAt/继承链追加）
  ② 头部残留断言＝「W45 未决事项」字样零残留+四字段值面对表
  ③ 旧形 2 字段（继承自/平移日期）回归钉——四字段对旧形零命中零害
  ④ dry-run 零写盘 / dst 已存在 skip（既有行为回归）

weekly_plane_shift 面此前零测试件——本件为首测试件（手作·白盒注入形）。
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.weekly_plane_shift import shift_carry_over

NOW = datetime(2026, 11, 15, 15, 50, 0, tzinfo=timezone.utc)

_HEADER_W45 = """# W45 未决事项 (Unresolved Items)

- sourceOfTruth: 本件（docs/workflow/operating-records/2026-W45/OP-202611-W45-001.unresolved-items.md）
- syncMode: rolling-weekly（每周平移；仅现役区随周滚动）
- lastSyncedAt: 2026-11-05T08:11:20Z（W45 平移刷正批·B 包核对）
- 负责人: CEOChiefOfStaff（小贾）
- 继承链: W41 同名件平移（2026-10-12）→ W44 同名件平移（2026-11-01 迁移窗·0cc423283）

---

## §1 现役区

| ID | 优先级 | 事项 | owner | 周 | 状态 |
|---|---|---|---|---|---|
| `CARRY-20260728-004` | P1 | tui 对齐 | CTO→FSD | 3w+ ⚠️ | frozen——冻结维持 |
| `CARRY-042` | P2 | 旧债 | COS | 1w+ | 待裁 |
"""

_HEADER_LEGACY = """# W45 未决事项 (Unresolved Items)

> **继承自**：`2026-W44/OP-202611-W44-001.unresolved-items.md`（W44）
> **平移日期**：2026-11-01（W45 起始日）

## §1 现役区

| `CARRY-20260728-004` | P1 | tui | CTO→FSD | 5w+ ⚠️ | frozen |
"""


def _mk_from_week(root: Path, name: str, text: str) -> Path:
    week = root / "2026-W45"
    week.mkdir(parents=True)
    src = week / name
    src.write_text(text, encoding="utf-8")
    return src


class CarryHeaderRefreshTest(unittest.TestCase):
    """笔 5 头部四字段刷新案族（LG-072 新形·W42 起五连残留家族顺修）。"""

    def test_header_four_fields_refreshed(self) -> None:
        """新形四字段值面对表：标题刷 W46/sourceOfTruth 新路径/lastSyncedAt
        新时刻/继承链追加新跳——既有键零动+CARRY 计数器照 bump。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_W45)
            result = shift_carry_over(
                "W45", "W46", root, "2026-11-15", dry_run=False, now=NOW)
            self.assertEqual(result["status"], "written", str(result))
            dst = root / "2026-W46" / "OP-202611-W46-001.unresolved-items.md"
            text = dst.read_text(encoding="utf-8")
            # ① 标题
            self.assertTrue(text.startswith("# W46 未决事项 (Unresolved Items)"))
            # ② sourceOfTruth 新路径（新周目录+新 OP 号）
            self.assertIn(
                "- sourceOfTruth: 本件（docs/workflow/operating-records/2026-W46/"
                "OP-202611-W46-001.unresolved-items.md）", text)
            # ③ lastSyncedAt＝注入时刻（机械刷新注记形）
            self.assertIn(
                "- lastSyncedAt: 2026-11-15T15:50:00Z（W45→W46 平移刷正·迁移器机械刷新）",
                text)
            # ④ 继承链追加新跳·历史跳零动
            self.assertIn(
                "→ W46 同名件平移（2026-11-15 迁移窗·迁移器自动平移·头部随周刷正）",
                text)
            self.assertIn("W44 同名件平移（2026-11-01 迁移窗·0cc423283）", text)
            # 头部残留断言：旧标题字样零残留（继承链链史字样另案豁免）
            self.assertNotIn("W45 未决事项", text)
            # 既有行为回归：CARRY 计数器 bump（3w+→4w+·4w 触 ⚠️）
            self.assertIn("| 4w+ ⚠️ |", text)
            self.assertNotIn("3w+", text)
            # src 零动（carry=读源写新·源文件照旧）
            self.assertIn("# W45 未决事项", (root / "2026-W45" /
                          "OP-202611-W45-001.unresolved-items.md").read_text(encoding="utf-8"))

    def test_source_of_truth_line_no_stale_week_path(self) -> None:
        """sourceOfTruth 行残留专项：行值面不含旧周路径（继承链行豁免——
        链史含旧周字样合法）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_W45)
            shift_carry_over("W45", "W46", root, "2026-11-15",
                             dry_run=False, now=NOW)
            text = (root / "2026-W46" /
                    "OP-202611-W46-001.unresolved-items.md").read_text(encoding="utf-8")
            sot_line = next(l for l in text.splitlines()
                            if l.startswith("- sourceOfTruth:"))
            self.assertNotIn("2026-W45", sot_line)
            self.assertNotIn("OP-202611-W45-001", sot_line)

    def test_legacy_header_two_fields_regression(self) -> None:
        """旧形回归钉：继承自/平移日期 2 字段照刷·四新字段对旧形零命中零炸
        （标题仍刷——re.sub 无匹配原样语义）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_LEGACY)
            result = shift_carry_over("W45", "W46", root, "2026-11-15",
                                      dry_run=False, now=NOW)
            self.assertEqual(result["status"], "written", str(result))
            text = (root / "2026-W46" /
                    "OP-202611-W46-001.unresolved-items.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# W46 未决事项"))
            self.assertIn("> **继承自**：`2026-W45/OP-202611-W45-001.unresolved-items.md`（W45）",
                          text)
            self.assertIn("> **平移日期**：2026-11-15（W46 起始日）", text)
            # 旧形无四新字段→无对应行（零注入）
            self.assertNotIn("- lastSyncedAt:", text)
            self.assertNotIn("- 继承链:", text)

    def test_chain_appends_per_shift(self) -> None:
        """继承链累积案：连续两跳平移（W45→W46→W47）链史两跳依序追加。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_W45)
            t1 = datetime(2026, 11, 15, 23, 50, 0, tzinfo=timezone.utc)
            shift_carry_over("W45", "W46", root, "2026-11-15", dry_run=False, now=t1)
            # 第二跳：源=W46 dst 文件→W47（glob 按 from_week 找）
            t2 = datetime(2026, 11, 22, 23, 50, 0, tzinfo=timezone.utc)
            result = shift_carry_over("W46", "W47", root, "2026-11-22",
                                      dry_run=False, now=t2)
            self.assertEqual(result["status"], "written", str(result))
            text = (root / "2026-W47" /
                    "OP-202611-W47-001.unresolved-items.md").read_text(encoding="utf-8")
            self.assertIn("→ W46 同名件平移（2026-11-15 迁移窗", text)
            self.assertIn("→ W47 同名件平移（2026-11-22 迁移窗", text)
            self.assertNotIn("W46 未决事项", text)  # 标题随跳刷新
            sot_line = next(l for l in text.splitlines()
                            if l.startswith("- sourceOfTruth:"))
            self.assertIn("2026-W47", sot_line)

    def test_dry_run_no_write(self) -> None:
        """dry-run 零写盘：would-write·dst 不落。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_W45)
            result = shift_carry_over("W45", "W46", root, "2026-11-15",
                                      dry_run=True, now=NOW)
            self.assertEqual(result["status"], "would-write")
            self.assertFalse((root / "2026-W46").exists())

    def test_skip_when_dst_exists(self) -> None:
        """dst 已存在→skip 零触（幂等护栏·既有行为回归）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_W45)
            to_dir = root / "2026-W46"
            to_dir.mkdir(parents=True)
            (to_dir / "OP-202611-W46-001.unresolved-items.md").write_text(
                "existing", encoding="utf-8")
            result = shift_carry_over("W45", "W46", root, "2026-11-15",
                                      dry_run=False, now=NOW)
            self.assertEqual(result["status"], "skip")

    def test_default_now_mechanical_clock(self) -> None:
        """now 缺省=机械时钟生成（调用面零触直证·lastSyncedAt 行取当刻形）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_from_week(root, "OP-202611-W45-001.unresolved-items.md", _HEADER_W45)
            result = shift_carry_over("W45", "W46", root, "2026-11-15", dry_run=False)
            self.assertEqual(result["status"], "written", str(result))
            text = (root / "2026-W46" /
                    "OP-202611-W46-001.unresolved-items.md").read_text(encoding="utf-8")
            ls_line = next(l for l in text.splitlines()
                           if l.startswith("- lastSyncedAt:"))
            self.assertIn("平移刷正·迁移器机械刷新", ls_line)  # 形面断言（值面机械时钟·不锁值）


# ── r12 批 1 持久化用例（CTO 初审候补①·2026-11-23）：活件族承接 / 逐项留痕 / validate 判据 ──

from runtime.cognition.weekly_plane import _carry_live_family
from runtime.cognition.weekly_plane_shift import _collect_carry_over_items, _live_family_missing


class LiveFamilyCarryTest(unittest.TestCase):
    """#3 _carry_live_family 承接形（复制+改名+幂等）。"""

    def _mk(self):
        root = Path(tempfile.mkdtemp())
        fw, tw = root / "2026-W47", root / "2026-W48"
        fw.mkdir(); tw.mkdir()
        (fw / "daily-progress.md").write_text("dp", encoding="utf-8")
        (fw / "company-demand-pool.md").write_text("pool", encoding="utf-8")
        (fw / "cfo-quota-daily-w47.md").write_text("q47", encoding="utf-8")
        (fw / "convene").mkdir()
        (fw / "convene" / "agenda.md").write_text("ag", encoding="utf-8")
        return root, fw, tw

    def test_carry_full(self):
        _, fw, tw = self._mk()
        changes = _carry_live_family(fw, tw, "W47", "W48")
        self.assertEqual(len(changes), 4)
        self.assertTrue((tw / "daily-progress.md").is_file())
        self.assertTrue((tw / "company-demand-pool.md").is_file())
        self.assertTrue((tw / "cfo-quota-daily-w48.md").is_file())          # 改名承接
        self.assertFalse((tw / "cfo-quota-daily-w47.md").exists())
        self.assertTrue((tw / "convene" / "agenda.md").is_file())

    def test_idempotent(self):
        _, fw, tw = self._mk()
        _carry_live_family(fw, tw, "W47", "W48")
        again = _carry_live_family(fw, tw, "W47", "W48")
        self.assertEqual(again, [])  # 已存在=零动作

    def test_quota_prefers_from_week_not_lexicographic_first(self):
        """CTO 复审边缘：残留 w46/w47 并存→取 w47（精确名）非字典序首件 w46。"""
        _, fw, tw = self._mk()
        (fw / "cfo-quota-daily-w46.md").write_text("q46", encoding="utf-8")
        _carry_live_family(fw, tw, "W47", "W48")
        self.assertEqual((tw / "cfo-quota-daily-w48.md").read_text(encoding="utf-8"), "q47")

    def test_quota_fallback_latest_mtime(self):
        """无精确名时按 mtime 取最新（非字典序）。"""
        root, fw, tw = self._mk()
        (fw / "cfo-quota-daily-w47.md").unlink()
        old = fw / "cfo-quota-daily-w45.md"
        new = fw / "cfo-quota-daily-w46.md"
        old.write_text("q45", encoding="utf-8")
        new.write_text("q46", encoding="utf-8")
        import os
        os.utime(old, (1_700_000_000, 1_700_000_000))
        _carry_live_family(fw, tw, "W99", "W48")
        self.assertEqual((tw / "cfo-quota-daily-w48.md").read_text(encoding="utf-8"), "q46")


class TodoListCarryTest(unittest.TestCase):
    """R10-CPO-02：活件族承接含 todo-list-*.md。"""

    def test_todo_list_carried(self):
        root = Path(tempfile.mkdtemp())
        fw, tw = root / "2026-W47", root / "2026-W48"
        fw.mkdir(); tw.mkdir()
        (fw / "todo-list-w47.md").write_text("todo", encoding="utf-8")
        changes = _carry_live_family(fw, tw, "W47", "W48")
        self.assertTrue((tw / "todo-list-w47.md").is_file())
        self.assertTrue(any(c.get("item") == "todo-list-w47.md" for c in changes))


class CarryOverItemsTest(unittest.TestCase):
    """#2/#7 _collect_carry_over_items 逐项留痕（treeId/from_week/reason/tree_op_hash·跨步零泄漏）。"""

    def test_items_and_hash(self):
        d = Path(tempfile.mkdtemp())
        top = d / "tree-op.json"
        top.write_text('{"a":1}', encoding="utf-8")
        results = [
            {"step": "carry_over", "result": {"status": "pass", "changes": [
                {"treeId": "t-001", "from_week": "W47", "reason": "cross-week", "path": str(top)},
                {"treeId": "t-002", "from_week": "W47", "reason": "blocked"},
            ]}},
            {"step": "migrate", "result": {"status": "pass", "changes": [{"treeId": "x"}]}},
        ]
        items = _collect_carry_over_items(results)
        self.assertEqual(len(items), 2)
        self.assertEqual(sorted(items[0].keys()), ["from_week", "reason", "treeId", "tree_op_hash"])
        self.assertEqual(len(items[0]["tree_op_hash"]), 16)
        self.assertNotIn("tree_op_hash", items[1])   # 无路径件不造假 hash
        self.assertTrue(all(i["treeId"].startswith("t-") for i in items))


class LiveFamilyValidateTest(unittest.TestCase):
    """#1 _live_family_missing 判据（红=四缺全列 / 绿=空表）。"""

    def test_red_all_missing(self):
        d = Path(tempfile.mkdtemp())
        self.assertEqual(_live_family_missing(d),
                         ["daily-progress.md", "company-demand-pool.md",
                          "cfo-quota-daily-*.md", "convene/", "todo-list-*.md"])   # R10-CPO-02 增 todo-list

    def test_green_when_complete(self):
        d = Path(tempfile.mkdtemp())
        for n in ("daily-progress.md", "company-demand-pool.md", "cfo-quota-daily-w48.md",
                  "todo-list-w48.md"):   # R10-CPO-02：todo-list 族必在
            (d / n).write_text("x", encoding="utf-8")
        (d / "convene").mkdir()
        self.assertEqual(_live_family_missing(d), [])


if __name__ == "__main__":
    unittest.main()
