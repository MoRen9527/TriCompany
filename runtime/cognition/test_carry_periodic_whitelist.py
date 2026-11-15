"""清单面复验新案（线 3 复验席补位·2026-11-15 速办）。

对象=5c1df48 五件族填装+机制三小件；判据基座=weekly-plane-must-migrate-registry.md
（线 2 制度卷 e37802ee8）逐件判据形。全谱端到端：五件族+改名+取新+defer
防双载+K1/K2 expected_absent 面+copy-latest 日期形过滤（阻塞级翻转位）。
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.carry_periodic import (
    carry_periodic_step,
    load_whitelist,
)

_WHITELIST = Path(__file__).parent / "carry_periodic_whitelist.json"


def _five_family_tree(root: Path) -> Path:
    """线 3 端到端真树形：from-week 五件族全构造（含混形件+K1/K2 旧周形）。"""
    src = root / "2026-W46"
    src.mkdir(parents=True)
    (src / "company-demand-pool.md").write_text("池身", encoding="utf-8")
    (src / "daily-progress.md").write_text("进度流水", encoding="utf-8")
    (src / "task-inventory-20261110.md").write_text("周内旧表", encoding="utf-8")
    (src / "task-inventory-20261112.md").write_text("当周现役真身", encoding="utf-8")
    (src / "task-inventory-notes.md").write_text("混形非日期件", encoding="utf-8")
    (src / "OP-202611-W46-001.json").write_text('{"week": "W46"}', encoding="utf-8")
    (src / "OP-202611-W46-001.unresolved-items.md").write_text(
        "# 现役区\n\n未决事项\n", encoding="utf-8")
    (src / "cfo-quota-daily-w46.md").write_text("K1 旧周形", encoding="utf-8")
    (src / "scoring-ledger-w46.md").write_text("K2 旧周形", encoding="utf-8")
    return src


class FiveFamilyEndToEndTest(unittest.TestCase):
    """五件族端到端全谱（判据基座=registry 五件逐件）。"""

    def test_five_family_full_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _five_family_tree(root)
            wl = load_whitelist(_WHITELIST)
            readings, errors = carry_periodic_step(
                root, {"from_week": "W46", "to_week": "W47",
                       "start_date": "2026-11-16", "operating_root": str(root)}, wl)
            self.assertEqual(errors, [])
            to = root / "2026-W47"
            by_pattern = {r["pattern"]: r for r in readings}
            # 件3 demand-pool 直搬
            self.assertEqual(by_pattern["company-demand-pool.md"]["carried"], 1)
            self.assertEqual((to / "company-demand-pool.md").read_text(encoding="utf-8"), "池身")
            # 件4 daily-progress 直搬
            self.assertEqual(by_pattern["daily-progress.md"]["carried"], 1)
            self.assertTrue((to / "daily-progress.md").exists())
            # 件5 task-inventory copy-latest：取最大日期形单件（真身承继·混形件不取）
            inv = by_pattern["task-inventory-*.md"]
            self.assertEqual(inv["carried"], 1)
            self.assertTrue((to / "task-inventory-20261112.md").exists(),
                            "当周现役真身承继（registry 件5·r78）")
            self.assertFalse((to / "task-inventory-notes.md").exists(),
                             "混形非日期件不取（日期形过滤·阻塞级翻转位）")
            self.assertFalse((to / "task-inventory-20261110.md").exists(),
                             "非最新日期件不取")
            # 件1 OP json rename_to 新周号正形
            op = by_pattern["OP-*-W46-001.json"]
            self.assertEqual(op["carried"], 1)
            self.assertTrue((to / "OP-202611-W47-001.json").exists())
            self.assertEqual(json.loads((to / "OP-202611-W47-001.json").read_text(encoding="utf-8"))["week"], "W46")
            # 件2 unresolved defer 防双载
            un = by_pattern["OP-*-W46-001.unresolved-items.md"]
            self.assertEqual(un["carried"], 0)
            self.assertIn("defer_to_impl", un["note"])
            self.assertFalse((to / "OP-202611-W47-001.unresolved-items.md").exists())
            # 搬运=copy 源保留（K1/K2 expected_absent 基座：旧周件不被移动）
            self.assertTrue((root / "2026-W46" / "cfo-quota-daily-w46.md").exists())
            self.assertTrue((root / "2026-W46" / "scoring-ledger-w46.md").exists())


class K1K2ExpectedAbsentGuardTest(unittest.TestCase):
    """K1/K2 keep_expected_absent 登记块守卫（registry 留置族·误迁=告警面）。"""

    def test_registry_block_in_whitelist(self) -> None:
        wl = load_whitelist(_WHITELIST)
        raw = json.loads(_WHITELIST.read_text(encoding="utf-8"))
        block = raw.get("keep_expected_absent") or []
        patterns = [b["pattern"] for b in block]
        self.assertIn("cfo-quota-daily-w{to_week}.md", patterns, "K1 登记块在卷")
        self.assertIn("scoring-ledger-w{to_week}.md", patterns, "K2 登记块在卷")

    def test_k1_k2_never_carried_by_whitelist(self) -> None:
        """K1/K2 旧周形件零入搬运集（留置族·机制面 zero-carry）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _five_family_tree(root)
            wl = load_whitelist(_WHITELIST)
            readings, _ = carry_periodic_step(
                root, {"from_week": "W46", "to_week": "W47",
                       "start_date": "2026-11-16", "operating_root": str(root)}, wl)
            to = root / "2026-W47"
            self.assertFalse((to / "cfo-quota-daily-w46.md").exists(), "K1 误迁=零")
            self.assertFalse((to / "scoring-ledger-w46.md").exists(), "K2 误迁=零")


class MechanismThreeSmallTest(unittest.TestCase):
    """机制三小件：{month} 令牌/rename_to 模板/copy-latest 映射。"""

    def test_month_token_in_rename(self) -> None:
        """{month} 令牌活体：rename_to {year}{month} 形=202611。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "2026-W46"
            src.mkdir()
            (src / "OP-202611-W46-001.json").write_text("{}", encoding="utf-8")
            readings, _ = carry_periodic_step(
                root, {"from_week": "W46", "to_week": "W47",
                       "start_date": "2026-11-16", "operating_root": str(root)},
                {"entries": [{"path_pattern": "OP-*-{from_week}-001.json",
                                                "rename_to": "OP-{year}{month}-{to_week}-001.json"}]})
            self.assertEqual(readings[0]["carried"], 1)
            self.assertTrue((root / "2026-W47" / "OP-202611-W47-001.json").exists())


if __name__ == "__main__":
    unittest.main()
