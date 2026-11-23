"""FADE-001 阶段 6 score cli 骨架单测（路径分立三态·CTO 精化一对表）。

score_engine 实弹装配连带（2026-11-14 CEO 11:45 直令·令③）：main 级 absent
案改 mock.patch 显式构造（原形依赖沙箱无 engine 的环境巧合——engine 落仓即被
探测实弹=设计行为·环境巧合面即翻红）+真 engine 集成案增（skipUnless 守卫=
engine_absent 系 J7 合法态的自护非永久跳过·engine 落仓后自动激活真跑）。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition import score_cli
from runtime.cognition.score_cli import run_score

_ENGINE_SPEC = importlib.util.find_spec("runtime.cognition.score_engine")


def _args(**kw) -> argparse.Namespace:
    base = dict(
        run_dir="unused", run_id="shift-W46-test",
        from_week="W46", to_week="W47",
    )
    base.update(kw)
    return argparse.Namespace(**base)


class ScorePathSplitTest(unittest.TestCase):
    """三态路径分立（精化一：跑了但败≠引擎缺席·J7 升级面仅限缺席路径）。"""

    def test_engine_absent_is_j7_upgrade_path(self) -> None:
        with mock.patch.object(score_cli, "import_module", side_effect=ImportError):
            code, s = run_score(_args())
        self.assertEqual(code, 2)
        self.assertEqual(s["engine_state"], "engine_absent")
        self.assertTrue(any("J7" in r for r in s["reasons"]))

    def test_executed_ok(self) -> None:
        fake = mock.MagicMock()
        fake.run_score.return_value = {"total": 88, "items": []}
        with mock.patch.object(score_cli, "import_module", return_value=fake):
            code, s = run_score(_args())
        self.assertEqual(code, 0)
        self.assertEqual(s["engine_state"], "executed_ok")
        self.assertEqual(s["score"]["total"], 88)

    def test_executed_failed_not_absent(self) -> None:
        """跑了但抛异常=executed_failed 非缺席路径（告警级分立面）。"""
        fake = mock.MagicMock()
        fake.run_score.side_effect = RuntimeError("boom")
        with mock.patch.object(score_cli, "import_module", return_value=fake):
            code, s = run_score(_args())
        self.assertEqual(code, 2)
        self.assertEqual(s["engine_state"], "executed_failed")
        self.assertFalse(any("J7" in r for r in s["reasons"]))
        self.assertTrue(any("COS" in r for r in s["reasons"]))

    def test_non_dict_return_is_executed_failed(self) -> None:
        fake = mock.MagicMock()
        fake.run_score.return_value = "not a dict"
        with mock.patch.object(score_cli, "import_module", return_value=fake):
            code, s = run_score(_args())
        self.assertEqual(code, 2)
        self.assertEqual(s["engine_state"], "executed_failed")


class ScoreWriteTest(unittest.TestCase):
    def test_main_writes_score_json_engine_absent(self) -> None:
        """absent 态显式构造（令③连带勘正）：mock import_module 抛 ImportError
        ——不依赖沙箱环境巧合（engine 落仓即实弹·探测面 present 后此案仍须
        验证 absent 分支行为=分支覆盖面）。"""
        from runtime.cognition.score_cli import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            argv = [
                "--run-dir", str(run), "--run-id", "r1",
                "--from-week", "W46", "--to-week", "W47",
            ]
            with mock.patch.object(score_cli, "import_module",
                                   side_effect=ImportError):
                code = main(argv)
            self.assertEqual(code, 2)
            s = json.loads((run / "score.json").read_text(encoding="utf-8"))
            self.assertEqual(s["engine_state"], "engine_absent")
            self.assertEqual(s["verdict"], "fail")

    @unittest.skipUnless(_ENGINE_SPEC,
                         "score_engine 未落仓（engine_absent=J7 合法态·落仓后自动激活）")
    def test_main_with_real_engine_empty_run_dir_degrades(self) -> None:
        """真 engine 集成案（令③）：main 零 mock 真跑——空 run_dir → engine
        结构化降级（executed_ok=engine 返回了 dict·verdict=fail=读数面）
        ·reasons 载缺件明细（哑卷≠引擎坏=设计行为）。"""
        from runtime.cognition.score_cli import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"  # 不创建=空 run_dir
            argv = [
                "--run-dir", str(run), "--run-id", "shift-W46-20261114T120000Z",
                "--from-week", "W46", "--to-week", "W47",
            ]
            code = main(argv)
            self.assertEqual(code, 0, "executed_ok 路径 rc=0（降级读数非 CLI 败）")
            s = json.loads((run / "score.json").read_text(encoding="utf-8"))
            self.assertEqual(s["engine_state"], "executed_ok")
            # 两层 verdict 分明（CLI 契约面 L78-86）：顶层 verdict=CLI 执行面
            # 成败（reasons 空=pass·rc=0）·engine 判卷读数=内嵌 score.verdict。
            self.assertEqual(s["verdict"], "pass", "CLI 执行面绿（engine 跑成无异常）")
            score = s["score"]
            self.assertEqual(score["verdict"], "fail",
                             "空 run_dir 全缺件=engine 判卷 verdict fail")
            self.assertTrue(score["families"], "缺件明细应在 families 结构化载明")


# ── r12 批2 refine 用例（CTO §三 影响面第 5 件·2026-11-23）：score_cli 扩读 exam.json ──


class ExamObjectiveTest(unittest.TestCase):
    """objective 受限三式机判（path_exists/json_field/regex；自由文本=skipped 不造假判）。"""

    def _run(self, exam: dict | None, files: dict | None = None) -> dict:
        d = Path(tempfile.mkdtemp())
        for name, content in (files or {}).items():
            (d / name).write_text(content, encoding="utf-8")
        if exam is not None:
            (d / "exam.json").write_text(json.dumps(exam), encoding="utf-8")
        score = {"score_version": "t", "run_id": "r", "from_week": "W47", "to_week": "W48",
                 "check_time": "t"}
        loaded = score_cli._load_exam(d)
        if loaded is not None:
            score["exam_objective"] = score_cli.evaluate_exam_objective(loaded, d)
        return score

    def test_no_exam_key_absent(self):
        self.assertNotIn("exam_objective", self._run(None))

    def test_path_exists_pass_fail(self):
        d = Path(tempfile.mkdtemp())
        (d / "present.json").write_text("{}", encoding="utf-8")
        exam = {"objective": [
            {"id": "O1", "dimension": "d", "assertion": "path_exists:present.json"},
            {"id": "O2", "dimension": "d", "assertion": "path_exists:absent.json"},
        ]}
        (d / "exam.json").write_text(json.dumps(exam), encoding="utf-8")
        loaded = score_cli._load_exam(d)
        out = score_cli.evaluate_exam_objective(loaded, d)
        self.assertEqual([i["result"] for i in out["items"]], ["pass", "fail"])
        self.assertEqual(out["counts"], {"pass": 1, "fail": 1, "skipped": 0})

    def test_json_field_eq_contains_exists(self):
        files = {"s.json": json.dumps({"verdict": "pass", "counts": {"migrate": 3}, "tags": "ab"})}
        exam = {"objective": [
            {"id": "O1", "assertion": "json_field:s.json::verdict::eq:pass"},
            {"id": "O2", "assertion": "json_field:s.json::verdict::ne:fail"},
            {"id": "O3", "assertion": "json_field:s.json::counts.migrate::exists:x"},
            {"id": "O4", "assertion": "json_field:s.json::tags::contains:b"},
            {"id": "O5", "assertion": "json_field:s.json::nope::exists:x"},
        ]}
        out = self._run_with(dict(files), exam)
        self.assertEqual([i["result"] for i in out["items"]], ["pass", "pass", "pass", "pass", "fail"])

    def _run_with(self, files, exam):
        d = Path(tempfile.mkdtemp())
        for n, c in files.items():
            (d / n).write_text(c, encoding="utf-8")
        loaded = {"objective": exam["objective"]}
        return score_cli.evaluate_exam_objective(loaded, d)

    def test_regex_and_free_text_skipped(self):
        files = {"plan.json": json.dumps({"families": [1, 2]})}
        exam = {"objective": [
            {"id": "O1", "assertion": "regex:plan.json::families"},
            {"id": "O2", "assertion": "自由文本断言（无结构前缀）"},
        ]}
        out = self._run_with(dict(files), exam)
        self.assertEqual(out["items"][0]["result"], "pass")
        self.assertEqual(out["items"][1]["result"], "skipped")
        self.assertIn("value-seat", out["items"][1]["detail"])

    def test_malformed_file_fail_not_crash(self):
        out = self._run_with({"s.json": "not json"}, {"objective": [
            {"id": "O1", "assertion": "json_field:s.json::a::eq:1"}]})
        self.assertEqual(out["items"][0]["result"], "fail")

    def test_run_score_integrates_readout(self):
        """run_score 集成：exam 在=score.json 得 exam_objective 段；权重不入 total_score。"""
        d = Path(tempfile.mkdtemp())
        (d / "exam.json").write_text(json.dumps({"objective": [
            {"id": "O1", "dimension": "d", "assertion": "path_exists:exam.json"}]}), encoding="utf-8")
        args = _args(run_dir=str(d))
        with mock.patch.object(score_cli, "probe_score_engine", return_value=(None, "engine_absent")):
            _, score = run_score(args)
        self.assertIn("exam_objective", score)
        self.assertEqual(score["exam_objective"]["counts"]["pass"], 1)
        self.assertNotIn("score", score)  # engine_absent 面照旧（读数段不改变原语义）


if __name__ == "__main__":
    unittest.main()
