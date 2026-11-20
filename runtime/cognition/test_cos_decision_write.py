"""D4 写面白盒 — write_cos_decision 接口契约钉（镜像族先例形·勘面卷 §三）。

锚定面（cto-d4-cosreferee-interface-survey-20261120 §三 verbatim）：
  原子写案 + 防重默认拒/显式 overwrite 案 + 六键 schema 校验案 +
  二值域出域 ValueError 案 + never raises 奇异输入族案（门族同构承）。

跑法：cd <worktree 根> && python -m unittest runtime.cognition.test_cos_decision_write -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from runtime.cognition.cos_decision_write import (
    EVOLUTION_DECISIONS,
    write_cos_decision,
)


def _write(root: Path, **kw) -> dict:
    """默认合法参数写卷（overrides 覆写）——奇异面单变量隔离。"""
    args = dict(
        run_dir=root,
        eviction_decision="evolve",
        rationale="7 席意见汇总：均分 96>95 线·建议迭代（综合评估·不投票制）",
        joint_review_avg_score=96.0,
        internal_score=91.0,
        instance="m-fsd",
    )
    args.update(kw)
    return write_cos_decision(**args)


def _read(root: Path) -> dict:
    return json.loads((root / "cos-score.json").read_text(encoding="utf-8"))


class AtomicWriteSchemaTest(unittest.TestCase):
    """三伴生②＋六键 schema（§一.2 定谳承）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "shift-W47-r2"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_write_ok_six_keys_exact(self) -> None:
        r = _write(self.root)
        self.assertTrue(r["ok"])
        self.assertTrue(r["path"].replace("\\", "/").endswith("cos-score.json"))
        payload = _read(self.root)
        self.assertEqual(
            set(payload.keys()),
            {"eviction_decision", "rationale", "joint_review_avg_score",
             "internal_score", "instance", "decided_at"})
        self.assertEqual(payload["eviction_decision"], "evolve")
        self.assertEqual(payload["joint_review_avg_score"], 96.0)
        self.assertEqual(payload["internal_score"], 91.0)
        self.assertEqual(payload["instance"], "m-fsd")
        self.assertEqual(r["overwritten"], False)

    def test_decided_at_none_now_utc_iso(self) -> None:
        r = _write(self.root, decided_at=None)
        dt = datetime.fromisoformat(r["decided_at"])
        self.assertIsNotNone(dt.tzinfo)  # UTC ISO8601 带时区（D-47 面同构）

    def test_decided_at_explicit_passthrough(self) -> None:
        r = _write(self.root, decided_at="2026-11-20T12:00:00+00:00")
        self.assertEqual(_read(self.root)["decided_at"], "2026-11-20T12:00:00+00:00")
        self.assertEqual(r["decided_at"], "2026-11-20T12:00:00+00:00")

    def test_write_to_nested_missing_dir_ok(self) -> None:
        deep = self.root / "a" / "b"
        r = _write(deep)
        self.assertTrue(r["ok"])
        self.assertTrue((deep / "cos-score.json").is_file())

    def test_int_scores_accepted(self) -> None:
        r = _write(self.root, joint_review_avg_score=95, internal_score=88)
        self.assertTrue(r["ok"])
        p = _read(self.root)
        self.assertEqual(p["joint_review_avg_score"], 95)
        self.assertEqual(p["internal_score"], 88)

    def test_decision_and_instance_normalized(self) -> None:
        r = _write(self.root, eviction_decision="  HOLD ", instance=" m-fsd ")
        self.assertTrue(r["ok"])
        p = _read(self.root)
        self.assertEqual(p["eviction_decision"], "hold")
        self.assertEqual(p["instance"], "m-fsd")


class ContractValueErrorTest(unittest.TestCase):
    """契约面 fail-fast（二值域出域 ValueError 案·白盒锚定谳承）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_out_of_domain_raises(self) -> None:
        # "evolve " 系归一接受面（strip/lower 后入域·归一案钉）——不列出域循环
        for bad in ("abort", "continue", "", None, 123):
            with self.assertRaises(ValueError):
                _write(self.root, eviction_decision=bad)
        self.assertFalse((self.root / "cos-score.json").exists())  # 零出域值入卷

    def test_domain_constants_frozen_shape(self) -> None:
        self.assertEqual(EVOLUTION_DECISIONS, ("evolve", "hold"))

    def test_empty_rationale_raises(self) -> None:
        for bad in ("", "   ", None, 42):
            with self.assertRaises(ValueError):
                _write(self.root, rationale=bad)

    def test_empty_instance_raises(self) -> None:
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                _write(self.root, instance=bad)

    def test_non_numeric_score_raises(self) -> None:
        with self.assertRaises(ValueError):
            _write(self.root, joint_review_avg_score="96")
        with self.assertRaises(ValueError):
            _write(self.root, internal_score="91")

    def test_bool_score_raises_int_trap(self) -> None:
        # bool⊂int 陷阱同族（骨架 aggregate_scores 同款）
        with self.assertRaises(ValueError):
            _write(self.root, joint_review_avg_score=True)
        with self.assertRaises(ValueError):
            _write(self.root, internal_score=False)

    def test_validation_error_writes_nothing(self) -> None:
        with self.assertRaises(ValueError):
            _write(self.root, eviction_decision="bogus")
        self.assertEqual(list(self.root.iterdir()), [])  # 零半卷零残件


class IdempotentGuardTest(unittest.TestCase):
    """三伴生③：防重默认拒覆写 + 显式 overwrite 勘正链。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "shift-W47-r2"
        r = _write(self.root, eviction_decision="evolve",
                   decided_at="2026-11-20T11:00:00+00:00")
        assert r["ok"]
        self.first = _read(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_default_refuses_overwrite(self) -> None:
        r = _write(self.root, eviction_decision="hold", rationale="勘正：重判")
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "already_decided")
        self.assertEqual(_read(self.root), self.first)  # 原卷零变（终局事件源）

    def test_explicit_overwrite_with_trace(self) -> None:
        r = _write(self.root, eviction_decision="hold",
                   rationale="勘正重判：复核后降档（理由入 rationale·调用方义务）",
                   overwrite=True)
        self.assertTrue(r["ok"])
        self.assertTrue(r["overwritten"])
        p = _read(self.root)
        self.assertEqual(p["eviction_decision"], "hold")
        self.assertEqual(p["overwritten"], True)
        self.assertEqual(p["previous_decided_at"], "2026-11-20T11:00:00+00:00")

    def test_corrupt_previous_overwritable(self) -> None:
        # 坏卷/非二值旧卷=非 decided 卷→默认可覆写（零静默·读面保守拦同族）
        (self.root / "cos-score.json").write_text("{not-json", encoding="utf-8")
        r = _write(self.root, eviction_decision="evolve")
        self.assertTrue(r["ok"])
        self.assertFalse(r["overwritten"])

    def test_non_binary_previous_overwritable(self) -> None:
        p = self.root / "cos-score.json"
        p.write_text(json.dumps({"eviction_decision": "bogus"}), encoding="utf-8")
        r = _write(self.root, eviction_decision="evolve")
        self.assertTrue(r["ok"])
        self.assertEqual(_read(self.root)["eviction_decision"], "evolve")


class NeverRaisesTest(unittest.TestCase):
    """运行面 never raises 保守返 dict（门族同构承·奇异输入族）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.file_as_dir = Path(self._tmp.name) / "not-a-dir"
        self.file_as_dir.write_text("x", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_run_dir_is_file_returns_dict(self) -> None:
        r = _write(self.file_as_dir)  # mkdir 撞文件→运行面异常保守返
        self.assertFalse(r["ok"])
        self.assertIn("write failed", r["reason"])

    def test_return_contract_always_dict_shape(self) -> None:
        for r in (_write(self.file_as_dir),):
            self.assertIsInstance(r, dict)
            self.assertIn("ok", r)
            self.assertIn("path", r)


if __name__ == "__main__":
    unittest.main()
