"""D5 白盒 — close_retry_gate retry 分叉+两态等价性锚（勘面卷 §四案族承）。

锚定面（cto-d5-close-identity-survey-20261120 §四 verbatim）：
  retry 分叉白盒——≥90 免 retry 案/<90 落 flag 案/边界 90=免案钉（90e06cddd
  承）/两 retry 上限 escalated 落卷案/resume 指令拟稿案/score.json 缺席 skip
  面案/非数值 skip 案/never raises 奇异输入族案/原子写断言案；
  两态等价性锚（§二.5）——close 输入面与联审产物零耦合断言案+prod 直走
  close 照跑两态同一案（零新铸运行时件·等价由 close 输入面同一性结构承载）。

跑法：cd <worktree 根> && python -m unittest runtime.cognition.test_close_retry_gate -v
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.close_retry_gate import (
    ESCALATE_AFTER_RETRIES,
    RESUME_STAGE_SCORE,
    check_retry_fork,
)
from runtime.cognition.close_skill import run_close

STAGE_FILES = ("preflight.json", "qualify.json", "plan.json", "dce.json",
               "verify.json", "score.json")


def _mk_close(score: float | None = None, verdict: str = "pass") -> dict:
    close = {"verdict": verdict, "run_id": "run-d5-1",
             "from_week": "2026-W46", "to_week": "2026-W47"}
    return close


def _mk_run(root: Path, score: float | None = 85.0,
            close_verdict: str = "pass") -> Path:
    """retry 前置 fixture：close.json（verdict pass）+score.json（score 键）。"""
    rd = root / "shift-W47-r2"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "close.json").write_text(
        json.dumps(_mk_close(verdict=close_verdict)), encoding="utf-8")
    if score is not None:
        (rd / "score.json").write_text(
            json.dumps({"verdict": "pass", "score": score}), encoding="utf-8")
    return rd


def _read_flag(rd: Path) -> dict:
    return json.loads((rd / "retry_flag.json").read_text(encoding="utf-8"))


class RetryForkDecisionTest(unittest.TestCase):
    """出口二值+边界钉（90e06cddd 承）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_score_ge_threshold_skips(self) -> None:
        rd = _mk_run(self.root, score=95.0)
        r = check_retry_fork(rd)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "skip")
        self.assertFalse((rd / "retry_flag.json").exists())  # 免 retry 零落卷

    def test_boundary_90_exactly_no_retry(self) -> None:
        rd = _mk_run(self.root, score=90)
        r = check_retry_fork(rd)
        self.assertEqual(r["state"], "skip")  # 90=免钉（<90 判据·90e06cddd 承）
        self.assertFalse((rd / "retry_flag.json").exists())

    def test_score_below_threshold_retries_with_flag(self) -> None:
        rd = _mk_run(self.root, score=85.5)
        r = check_retry_fork(rd)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "retry")
        flag = _read_flag(rd)
        self.assertEqual(
            set(flag.keys()),
            {"retry_flag", "retry_count", "internal_score", "threshold",
             "run_id", "from_week", "to_week", "escalated", "flagged_at"})
        self.assertEqual(flag["retry_flag"], "pending-retry")
        self.assertEqual(flag["retry_count"], 1)  # 首遇=当周计数 1
        self.assertEqual(flag["internal_score"], 85.5)
        self.assertEqual(flag["threshold"], 90)
        self.assertEqual(flag["run_id"], "run-d5-1")
        self.assertEqual(flag["from_week"], "2026-W46")
        self.assertFalse(flag["escalated"])
        self.assertIn("T", flag["flagged_at"])  # UTC ISO8601 面

    def test_custom_threshold_respected(self) -> None:
        rd = _mk_run(self.root, score=92)
        r = check_retry_fork(rd, threshold=95)
        self.assertEqual(r["state"], "retry")
        self.assertEqual(_read_flag(rd)["threshold"], 95)

    def test_resume_hint_draft_shape(self) -> None:
        rd = _mk_run(self.root, score=80)
        r = check_retry_fork(rd)
        hint = r.get("resume_hint")
        self.assertIsInstance(hint, dict)
        self.assertEqual(hint["resume_stage"], RESUME_STAGE_SCORE)
        self.assertEqual(hint["stage_name"], "score")
        self.assertIn(str(rd), hint["resume_command"])
        self.assertIn("resume-stage", hint["resume_command"])
        # 拟稿不入 flag 九键卷面（零扩键·§三.3 定谳承）
        self.assertNotIn("resume_hint", _read_flag(rd))


class ConservativeSkipTest(unittest.TestCase):
    """保守 skip 面（门族同构承·零落卷）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _assert_skip_no_flag(self, rd: Path, r: dict) -> None:
        self.assertEqual(r["state"], "skip")
        self.assertFalse((rd / "retry_flag.json").exists())

    def test_close_json_absent_skip(self) -> None:
        rd = self.root / "shift-W47-r1"
        rd.mkdir()
        (rd / "score.json").write_text(json.dumps({"score": 50}), encoding="utf-8")
        self._assert_skip_no_flag(rd, check_retry_fork(rd))

    def test_close_verdict_fail_skip(self) -> None:
        rd = _mk_run(self.root, score=50, close_verdict="fail")
        r = check_retry_fork(rd)
        self._assert_skip_no_flag(rd, r)  # 收口门毒化=升级域管非 retry 面
        self.assertIn("升级域", r["detail"])

    def test_score_json_absent_skip(self) -> None:
        rd = _mk_run(self.root, score=None)
        self._assert_skip_no_flag(rd, check_retry_fork(rd))

    def test_score_non_numeric_skips(self) -> None:
        for bad in ("abc", None, True, {"x": 1}):
            rd = _mk_run(self.root)
            (rd / "score.json").write_text(json.dumps({"score": bad}),
                                           encoding="utf-8")
            self._assert_skip_no_flag(rd, check_retry_fork(rd))

    def test_score_missing_key_skip(self) -> None:
        rd = _mk_run(self.root)
        (rd / "score.json").write_text(json.dumps({"verdict": "pass"}),
                                       encoding="utf-8")
        self._assert_skip_no_flag(rd, check_retry_fork(rd))

    def test_score_out_of_domain_skip(self) -> None:
        rd = _mk_run(self.root, score=150)
        self._assert_skip_no_flag(rd, check_retry_fork(rd))  # 坏值保守 skip

    def test_score_unparsable_skip(self) -> None:
        rd = _mk_run(self.root)
        (rd / "score.json").write_text("{ broken", encoding="utf-8")
        self._assert_skip_no_flag(rd, check_retry_fork(rd))


class RetryCountEscalationTest(unittest.TestCase):
    """次数上限语义（§三.4·当周 state 面=flag 族自持·escalated 非熔断）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_second_retry_count_carries(self) -> None:
        rd1 = _mk_run(self.root, score=70)
        (rd1.rename(self.root / "shift-W47-r1"))
        r1 = check_retry_fork(self.root / "shift-W47-r1")
        self.assertEqual(r1["retry_count"], 1)
        rd2 = _mk_run(self.root, score=75)
        rd2.rename(self.root / "shift-W47-r2")
        r2 = check_retry_fork(self.root / "shift-W47-r2")
        self.assertEqual(r2["retry_count"], 2)  # 当周 state 面=flag 族 max+1
        self.assertFalse(r2["escalated"])

    def test_double_retry_escalated_not_fuse(self) -> None:
        for name, score in (("shift-W47-r1", 70), ("shift-W47-r2", 72)):
            rd = _mk_run(self.root, score=score)
            rd.rename(self.root / name)
            check_retry_fork(self.root / name)
        rd3 = _mk_run(self.root, score=74)
        rd3.rename(self.root / "shift-W47-r3")
        r3 = check_retry_fork(self.root / "shift-W47-r3")
        self.assertEqual(r3["state"], "retry")
        self.assertEqual(r3["retry_count"], 3)
        self.assertTrue(r3["escalated"])  # 已两 retry 仍<90 → escalated=true
        flag = _read_flag(self.root / "shift-W47-r3")
        self.assertTrue(flag["escalated"])
        # 如实呈报非熔断：retry 照落卷照出拟稿（零停工面）
        self.assertIn("resume_hint", r3)
        self.assertIn("escalated", r3["detail"])
        self.assertEqual(ESCALATE_AFTER_RETRIES, 2)  # 上限常量定谳钉


class AtomicWriteTest(unittest.TestCase):
    """原子写断言案（tmp+replace·零残件·D4 同形）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_atomic_write_no_residue(self) -> None:
        rd = _mk_run(self.root, score=66)
        r = check_retry_fork(rd)
        self.assertEqual(r["state"], "retry")
        residues = [p.name for p in rd.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(residues, [])  # 零 .tmp 残件
        flag = _read_flag(rd)  # 卷面可解析（零半卷）
        self.assertEqual(flag["retry_flag"], "pending-retry")


class NeverRaisesTest(unittest.TestCase):
    """never raises 奇异输入族（运行面保守返 dict·D3/D4 先例形）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.file_as_dir = Path(self._tmp.name) / "not-a-dir"
        self.file_as_dir.write_text("x", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_weird_inputs_return_dict(self) -> None:
        for rd in (None, "", self.file_as_dir, 12345):
            try:
                r = check_retry_fork(rd)
            except TypeError:
                self.fail(f"check_retry_fork raised on {rd!r}")
            self.assertIsInstance(r, dict)
            self.assertIn("state", r)
            self.assertIn(r["state"], ("retry", "skip"))


class _CloseRunFixture:
    """两态等价性锚 fixture：结构完整 run（六段产物+close+manifest）。"""

    @staticmethod
    def build(root: Path, with_joint_review: bool) -> Path:
        rd = root / ("with-jr" if with_joint_review else "prod-direct")
        rd.mkdir(parents=True)
        for name in STAGE_FILES:
            payload = {"verdict": "pass"}
            if name == "score.json":
                payload["score"] = 91.0
            (rd / name).write_text(json.dumps(payload), encoding="utf-8")
        (rd / "close.json").write_text(json.dumps({"verdict": "pass"}),
                                       encoding="utf-8")
        (rd / "manifest.json").write_text(
            json.dumps({"run_state": "ok", "manifest_version": "1.0.0"}),
            encoding="utf-8")
        if with_joint_review:
            # 联审产物卷（进化面域·§二.1 不入 close 输入）
            (rd / "cos-score.json").write_text(
                json.dumps({"eviction_decision": "evolve", "internal_score": 91.0}),
                encoding="utf-8")
        return rd


def _run_close_on(rd: Path) -> dict:
    args = argparse.Namespace(run_dir=str(rd), run_id="run-eq-1",
                              from_week="2026-W46", to_week="2026-W47")
    _, close = run_close(args)
    return close


class TwoStateEquivalenceAnchorTest(unittest.TestCase):
    """两态等价性恒等式锚（§二.5·零新铸运行时件·白盒承载）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_close_input_independent_of_joint_review(self) -> None:
        """锚①：close 输入面与联审产物零耦合——run_close 输出零联审感知字段
        （§二.1 输入面同一性·扫描域=六件+close+manifest 零 cos-score）。"""
        rd = _CloseRunFixture.build(self.root, with_joint_review=False)
        close = _run_close_on(rd)
        self.assertNotIn("reasons", close)  # 结构门零毒化
        flat = json.dumps(close, ensure_ascii=False)
        for joint_token in ("cos-score", "eviction_decision", "joint_review",
                            "escalated_decision"):
            self.assertNotIn(joint_token, flat)  # 零联审产物字样入 close 卷
        # 段产物 notes/evidence 域=六件+close+manifest（零联审卷条目）
        noted = [n.split(":")[0] for n in close["stage_artifact_notes"]]
        self.assertNotIn("cos-score.json", noted)

    def test_close_skill_source_zero_joint_review_tokens(self) -> None:
        """锚①静态面：close_skill 源文本零联审分支（现役实况实证·§二.2
        零感知即零分叉=等价性结构性成立非约定成立）。"""
        src = Path(
            __import__("runtime.cognition.close_skill",
                       fromlist=["close_skill"]).__file__).read_text(
            encoding="utf-8")
        for token in ("cos-score", "cos_score", "eviction_decision",
                      "joint_review", "check_cos_decision"):
            self.assertNotIn(token, src)

    def test_prod_direct_walk_two_states_identical(self) -> None:
        """锚②：prod 直走（无联审卷）vs 联审轮（cos-score.json 在）——
        run_close 两态输出剔 check_time/path 归一后逐键全等（§二.2 两态完全
        同一·close 侧零联审感知实证）。"""
        rd_a = _CloseRunFixture.build(self.root, with_joint_review=False)
        rd_b = _CloseRunFixture.build(self.root, with_joint_review=True)
        close_a = _run_close_on(rd_a)
        close_b = _run_close_on(rd_b)
        a = copy.deepcopy(close_a)
        b = copy.deepcopy(close_b)
        for c, rd in ((a, rd_a), (b, rd_b)):
            c.pop("check_time")  # 时点面剔（写序时点非结构面）
            for ev in c["evidence"]:
                ev["path"] = ev["path"].replace(str(rd), "<RUN>")
        self.assertEqual(a, b)  # 两态逐键全等（等价性结构承载实证）


if __name__ == "__main__":
    unittest.main()
