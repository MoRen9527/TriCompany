"""joint_review_trigger 白盒单测（W2 施工件·触发段）。

覆盖：契约最小字段形/skip fail-closed 面双态/材料指针锚/三域分现/mode
注记/树面双落/notify 降级面/契约钉案（skip 不产 trigger 卷）。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.joint_review_trigger import (  # noqa: E402
    TRIGGER_VERSION,
    build_parser,
    build_trigger,
    domain_readings,
    run_trigger,
    write_trigger,
)


def _mk_run_dir(root: Path, run_state: str = "ok", mode: str = "loop-window") -> Path:
    """假 run_dir：manifest+preflight+score 三卷最小 fixtures。"""
    rd = root / "runs" / "shift-W46-20261116T000000Z"
    rd.mkdir(parents=True)
    stages = {n: "pass" for n in (
        "preflight.json", "qualify.json", "plan.json", "dce.json",
        "verify.json", "score.json", "close.json")}
    if run_state == "failed":
        stages["verify.json"] = "fail"
    (rd / "manifest.json").write_text(json.dumps({
        "manifest_version": "1.0.0", "run_id": rd.name,
        "from_week": "W46", "to_week": "W47",
        "stages": stages, "run_state": run_state,
    }), encoding="utf-8")
    (rd / "preflight.json").write_text(json.dumps({
        "verdict": "pass",
        "assertions": {"week_math": {"mode": mode}},
    }), encoding="utf-8")
    (rd / "score.json").write_text(json.dumps({
        "score_version": "1.0.0", "run_id": rd.name,
        "score": {"score_engine_version": "2.0.0", "families": [
            {"family_id": "B", "state": "machine", "score": 12, "weight": 12},
            {"family_id": "A", "state": "manual", "score": None, "weight": 10},
            {"family_id": "I", "state": "subjective", "score": None, "weight": 10},
        ]},
    }), encoding="utf-8")
    (rd / "plan.json").write_text(json.dumps({
        "counts": {"files": 3}, "agent_readings": ["a1"],
    }), encoding="utf-8")
    return rd


class TriggerContractCase(unittest.TestCase):
    """契约最小字段形钉案（W1§二 七项全列）。"""

    def test_min_field_shape_all_present(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            rd = _mk_run_dir(root)
            tmv = root / "tmv"; tmv.mkdir()
            args = build_parser().parse_args([
                "--run-dir", str(rd), "--run-id", rd.name,
                "--from-week", "W46", "--to-week", "W47",
                "--tmv-root", str(tmv), "--no-notify"])
            code, out = run_trigger(args)
            self.assertEqual(code, 0)
            for key in ("trigger_version", "loop_run_id", "run_dir",
                        "dim_a_materials", "dim_b_materials",
                        "domain_readings", "score_threshold",
                        "mode", "trigger_time"):
                self.assertIn(key, out, f"契约字段缺: {key}")
            self.assertEqual(out["loop_run_id"], rd.name)
            self.assertIsNone(out["score_threshold"])  # 接口位留参不代裁

    def test_dim_pointers_and_sha_anchor(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            rd = _mk_run_dir(root)
            tmv = root / "tmv"; tmv.mkdir()
            args = build_parser().parse_args([
                "--run-dir", str(rd), "--run-id", rd.name,
                "--from-week", "W46", "--to-week", "W47",
                "--tmv-root", str(tmv), "--no-notify"])
            _, out = run_trigger(args)
            refs_a = [d["ref"] for d in out["dim_a_materials"]]
            self.assertEqual(refs_a, ["manifest.json", "score.json", "plan.json"])
            self.assertTrue(all(d["sha16"] for d in out["dim_a_materials"]))
            kinds_b = [d["kind"] for d in out["dim_b_materials"]]
            self.assertEqual(kinds_b, ["counts", "ar", "unresolved_diff", "ops_commit"])
            ops = [d for d in out["dim_b_materials"] if d["kind"] == "ops_commit"][0]
            self.assertIn("hash", ops)  # 指针面在（值面可 None=失败如实）

    def test_domain_readings_three_domains(self):
        with TemporaryDirectory() as td:
            rd = _mk_run_dir(Path(td))
            dr = domain_readings(rd)
            self.assertEqual(dr["machine"]["score"], 12)  # 机判族实分求和·manual/subj 零计入
            self.assertEqual(dr["machine"]["families"], {"B": 12})
            self.assertEqual(dr["duty_collection"], "pending")  # 未落卷=pending 非冒充
            self.assertEqual(dr["subjective"], "pending")

    def test_mode_note_from_preflight(self):
        with TemporaryDirectory() as td:
            rd = _mk_run_dir(Path(td), mode="cron-sunday")
            from runtime.cognition.joint_review_trigger import mode_note
            self.assertEqual(mode_note(rd), "cron-sunday")


class TriggerFailClosedCase(unittest.TestCase):
    """skip fail-closed 面（W1§四.2）：run_state!=ok → skip 卷·零 trigger 卷。"""

    def test_failed_state_produces_skip_exit0(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            rd = _mk_run_dir(root, run_state="failed")
            args = build_parser().parse_args([
                "--run-dir", str(rd), "--run-id", rd.name,
                "--from-week", "W46", "--to-week", "W47", "--no-notify"])
            code, out = run_trigger(args)
            self.assertEqual(code, 0)
            self.assertEqual(out["verdict"], "skip")
            self.assertIn("!= ok", out["reason"])
            self.assertTrue((rd / "joint-review-trigger-skip.json").is_file())
            # 契约钉案：skip 态不产 trigger 卷（防双卷并存混淆）
            self.assertFalse((rd / "joint-review-trigger.json").exists())

    def test_manifest_absent_produces_skip(self):
        with TemporaryDirectory() as td:
            rd = Path(td) / "empty-run"; rd.mkdir()
            args = build_parser().parse_args([
                "--run-dir", str(rd), "--run-id", "shift-X-1",
                "--from-week", "W46", "--to-week", "W47", "--no-notify"])
            code, out = run_trigger(args)
            self.assertEqual(code, 0)
            self.assertEqual(out["verdict"], "skip")
            self.assertIn("manifest_absent", out["reason"])


class TriggerTreeLandingCase(unittest.TestCase):
    """树面双落（归属周自动算·best-effort）。"""

    def test_dual_landing_tree_path(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            rd = _mk_run_dir(root)
            tmv = root / "tmv"; tmv.mkdir()
            payload = build_trigger(rd, tmv, rd.name, "W46", "W47")
            out = write_trigger(payload, rd, tmv, "fade001-loop-joint-review")
            self.assertTrue((rd / "joint-review-trigger.json").is_file())
            tree_file = out["_landed"]["tree"]
            self.assertIsNotNone(tree_file)
            parts = Path(tree_file).parts
            self.assertIn("trees", parts)
            self.assertIn("fade001-loop-joint-review", parts)
            back = json.loads(Path(tree_file).read_text(encoding="utf-8"))
            self.assertEqual(back["loop_run_id"], rd.name)
            # ISO 周目录形（2026-Wxx 惯例）
            import re
            self.assertTrue(re.search(r"20\d\d-W\d\d", tree_file))


if __name__ == "__main__":
    unittest.main()
