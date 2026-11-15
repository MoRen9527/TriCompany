"""carry_periodic 机制面复验新案（线 3 复验席补位·2026-11-15）。

对象=22dff7c 三件（carry_periodic.py 搬运主步+carry_periodic_whitelist.json
骨架+weekly_plane_shift_fade.py 接线旗）。四判据形+机制面三路径：
源寻址三路/白名单扩窗框架/接线旗/护栏三照守（cron 零触/零 payload 触/
机械复制+源缺失合法跳过不造替身）。
"""
from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.carry_periodic import (
    carry_periodic_step,
    load_whitelist,
)


def _params(root: Path, **kw) -> dict:
    base = {"from_week": "W46", "to_week": "W47",
            "start_date": "2026-11-16", "operating_root": str(root)}
    base.update(kw)
    return base


def _wl(entries: list) -> dict:
    return {"version": "1.0", "entries": entries}


class SourceAddressingTest(unittest.TestCase):
    """源寻址三路+源缺失合法跳过（机制面主步核心）。"""

    def test_from_dir_primary_hit(self) -> None:
        """正形：from-week 正形目录（year-W）内命中·pattern {from_week}/ 前缀剥除。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2026-W46" / "trees" / "weekly-notes"
            src_dir.mkdir(parents=True)
            (src_dir / "digest.md").write_text("周期滚动内容", encoding="utf-8")
            readings, errors = carry_periodic_step(
                root, _params(root),
                _wl([{"path_pattern": "{from_week}/trees/weekly-notes/digest.md", "mode": "copy"}]))
            self.assertEqual(errors, [])
            self.assertEqual(readings[0]["carried"], 1)
            # 加固面（be8f457）：落点=to_dir 下相对子路径保持（src_rel 非扁平 src.name）
            dst = root / "2026-W47" / "trees" / "weekly-notes" / "digest.md"
            self.assertEqual(dst.read_text(encoding="utf-8"), "周期滚动内容")

    def test_root_glob_fallback(self) -> None:
        """兜底二路：正形目录缺席→根 */{rel} 三段命中（be8f457 修正形·原 4 段死路）
        +剥首周段后子路径落位（reports/r.md 形·加固面随行案）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2025-W46" / "reports"
            src_dir.mkdir(parents=True)
            (src_dir / "r.md").write_text("跨年源", encoding="utf-8")
            readings, errors = carry_periodic_step(
                root, _params(root),
                _wl([{"path_pattern": "{from_week}/reports/r.md", "mode": "copy"}]))
            self.assertEqual(errors, [])
            self.assertEqual(readings[0]["carried"], 1)
            dst = root / "2026-W47" / "reports" / "r.md"
            self.assertEqual(dst.read_text(encoding="utf-8"), "跨年源")
            self.assertFalse((root / "2026-W47" / "r.md").exists(), "扁平化旧形不落（加固面负断言）")

    def test_missing_source_legal_skip(self) -> None:
        """护栏案：源缺失=合法跳过（carried=0+note 记读数·不造替身）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "2026-W47").mkdir()
            readings, errors = carry_periodic_step(
                root, _params(root),
                _wl([{"path_pattern": "{from_week}/ghost/x.md", "mode": "copy"}]))
            self.assertEqual(errors, [])
            self.assertEqual(readings[0]["carried"], 0)
            self.assertIn("源缺失", readings[0]["note"])
            self.assertFalse((root / "2026-W47" / "x.md").exists(), "不造替身")

    def test_template_tokens_substituted(self) -> None:
        """模板令牌三面：{from_week}/{to_week}/{year} 全替换。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2026-W46" / "jobs"
            src_dir.mkdir(parents=True)
            (src_dir / "W46-jobs.json").write_text("{}", encoding="utf-8")  # 大小写对形（glob 敏感·案笔误勘正 19:2x）
            readings, _ = carry_periodic_step(
                root, _params(root),
                _wl([{"path_pattern": "{year}-{from_week}/jobs/{from_week}-jobs.json"}]))
            self.assertEqual(readings[0]["pattern"], "2026-W46/jobs/W46-jobs.json")
            self.assertEqual(readings[0]["carried"], 1)


class WhitelistFrameworkTest(unittest.TestCase):
    """白名单扩窗框架：entries 增删零代码·形校验 fail-closed。"""

    def test_empty_whitelist_legal(self) -> None:
        """空清单骨架=合法（线 1 卷填入前态）。"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wl.json"
            p.write_text(json.dumps({"version": "1.0", "entries": []}), encoding="utf-8")
            wl = load_whitelist(p)
            self.assertEqual(wl["entries"], [])

    def test_entries_not_list_raises(self) -> None:
        """形校验 fail-closed：entries 非 list→raise（不静默）。"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wl.json"
            p.write_text(json.dumps({"entries": "nope"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_whitelist(p)

    def test_entry_missing_path_pattern_raises(self) -> None:
        """形校验 fail-closed：条目缺 path_pattern→raise。"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wl.json"
            p.write_text(json.dumps({"entries": [{"mode": "copy"}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_whitelist(p)

    def test_expand_window_zero_code(self) -> None:
        """扩窗零代码活体：清单加条目→同机制即生效（框架面）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "2026-W46" / "a.md"
            src.parent.mkdir(parents=True)
            src.write_text("扩窗内容", encoding="utf-8")
            p = root / "wl.json"
            p.write_text(json.dumps({"entries": [
                {"path_pattern": "{from_week}/a.md"}]}, ensure_ascii=False), encoding="utf-8")
            readings, errors = carry_periodic_step(root, _params(root), load_whitelist(p))
            self.assertEqual(errors, [])
            self.assertEqual(readings[0]["carried"], 1)


    def test_absolute_pattern_three_way_fallback(self) -> None:
        """绝对形 pattern（{year}-{from_week}/... 全路径形）三路兜底案（451d6d3
        补装·次生回归回归位）：二路死路时三路 substituted 命中·剥首段 year-W
        周段落位子结构（与二路剥首段形同构）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2026-W46" / "jobs"
            src_dir.mkdir(parents=True)
            (src_dir / "W46-jobs.json").write_text("{}", encoding="utf-8")
            readings, errors = carry_periodic_step(
                root, _params(root),
                _wl([{"path_pattern": "{year}-{from_week}/jobs/{from_week}-jobs.json"}]))
            self.assertEqual(errors, [])
            self.assertEqual(readings[0]["carried"], 1)
            dst = root / "2026-W47" / "jobs" / "W46-jobs.json"
            self.assertEqual(dst.read_text(encoding="utf-8"), "{}")


class GuardrailsTest(unittest.TestCase):
    """护栏三照守活体：cron 零触/机械复制/目的正形目录。"""

    def test_cron_schedule_untouched(self) -> None:
        """护栏①：搬运零触碰 cron schedule 面（同目录 schedule 文件原样）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2026-W46"
            src_dir.mkdir()
            (src_dir / "n.md").write_text("x", encoding="utf-8")
            sched = root / "2026-W46" / "cron-schedule.json"
            sched.write_text('{"jobs": []}', encoding="utf-8")
            readings, errors = carry_periodic_step(
                root, _params(root),
                _wl([{"path_pattern": "{from_week}/cron-schedule.json",
                      "mode": "copy"}]))
            # 机制面不阻白名单条目命中 schedule 文件名（清单内容=线 1 卷定谳防呆面）——
            # 本案锚=搬运动作本身零写 cron 系统位（system cron 面）+读数如实计数：
            self.assertEqual(errors, [])
            self.assertEqual(readings[0]["carried"], 1)
            # schedule 源文件原样未被移动（copy 模式=复制非搬移）
            self.assertTrue(sched.exists(), "copy 模式=整文件平移·源保留")

    def test_copy_mode_byte_identical(self) -> None:
        """护栏③：机械复制逐字节同（内容 owner 席后处理·非语义迁移）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2026-W46"
            src_dir.mkdir()
            payload = bytes(range(256)) * 3
            (src_dir / "bin.dat").write_bytes(payload)
            carry_periodic_step(root, _params(root),
                                _wl([{"path_pattern": "{from_week}/bin.dat"}]))
            self.assertEqual((root / "2026-W47" / "bin.dat").read_bytes(), payload)

    def test_to_dir_year_week_shape(self) -> None:
        """目的目录=to-week 正形（year-W 形·非裸周段）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "2026-W46"
            src_dir.mkdir()
            (src_dir / "a.md").write_text("x", encoding="utf-8")
            carry_periodic_step(root, _params(root),
                                _wl([{"path_pattern": "{from_week}/a.md"}]))
            self.assertTrue((root / "2026-W47" / "a.md").exists())
            self.assertFalse((root / "W47" / "a.md").exists(), "裸周段目录非法形不落")


class WiringFlagTest(unittest.TestCase):
    """接线旗：--carry-periodic-whitelist 注册面守卫（weekly_plane_shift_fade
    argparse 内嵌 main 形→源面字面守卫案·旗注册+缺省+'none' 跳步三要素）。"""

    def _src(self) -> str:
        from runtime.cognition import weekly_plane_shift_fade as w
        return Path(w.__file__).read_text(encoding="utf-8")

    def test_flag_registered(self) -> None:
        src = self._src()
        self.assertIn("--carry-periodic-whitelist", src, "旗注册在位")
        self.assertIn("carry_periodic_whitelist", src, "args 属性面接线")

    def test_none_skip_semantics(self) -> None:
        src = self._src()
        self.assertIn("!= \"none\"", src, "显式 'none'=跳步分支在位")
        self.assertIn("carry_periodic_whitelist.json", src, "缺省=仓内清单名")


if __name__ == "__main__":
    unittest.main()
