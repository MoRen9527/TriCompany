"""cos_decision_gate.py 单测 — D3 层 2·COS 进化判决门（cto-gate-interface-ruling
§二 层 2·白盒对表=CeoRulingGateTest 10 案镜像族+骨架回归锚）。

镜像族（check_ceo_ruling 十案同款形）：skip 二案/awaiting 二案（含 72h 升级）/
evolve/hold 二值域案/坏值·坏卷保守拦二案/mtime 最新案/本轮空壳自然排除案。
同构增补案（如实注·非镜像）：F2 空壳排除钉/F3 残拍排除钉/eviction_decision
键缺保守拦/never raises 异常面四案族。

跑法：cd TriCompany && python -m unittest runtime.cognition.test_cos_decision_gate -v
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.cos_decision_gate import check_cos_decision


def _score(decision: str = "evolve", rationale: str = "7 席均分 96.2 过 95 线",
           avg=96.2, internal=91.0, decided_at="2026-11-20T00:00:00Z") -> dict:
    return {
        "eviction_decision": decision,
        "rationale": rationale,
        "joint_review_avg_score": avg,
        "fade001_internal_score": internal,
        "decided_at": decided_at,
    }


class CosDecisionGateTest(unittest.TestCase):
    """check_cos_decision 四态+skip+3 天催办案族（CeoRulingGateTest 10 案镜像）。"""

    def _mk_runs(self, root: Path, run_name: str = "shift-W47-test",
                 with_preflight: bool = True,
                 score: dict | None = None,
                 age_days: float | None = None,
                 full_run: bool = True) -> Path:
        rd = root / run_name
        rd.mkdir(parents=True, exist_ok=True)
        if with_preflight:
            (rd / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
        if full_run:
            # F3 语义（完整轮=close.json 在）——镜像族 fixture 同构承。
            (rd / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
        if score is not None:
            (rd / "cos-score.json").write_text(json.dumps(score), encoding="utf-8")
        if age_days is not None:
            import os as _os
            ts = time.time() - age_days * 86400
            _os.utime(rd / "preflight.json", (ts, ts))
        return rd

    # ── 镜像案 1/2：skip 向后兼容 ─────────────────────────────────────

    def test_skip_when_no_runs_root(self) -> None:
        r = check_cos_decision(None)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "skip")

    def test_skip_when_root_missing(self) -> None:
        r = check_cos_decision("/tmp/definitely-not-here-cd3a17")
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "skip")

    # ── 镜像案 3/4：awaiting-decision 挂起+72h 升级 ──────────────────

    def test_absent_awaiting_decision(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), score=None)
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-decision")
            self.assertIn("fail-closed", r["detail"])
            self.assertNotIn("escalated", r)

    def test_absent_over_72h_escalates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), age_days=4.0)
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-decision")
            self.assertTrue(r.get("escalated"))
            self.assertGreater(r.get("prev_run_age_h", 0), 72)

    # ── 镜像案 5/6：evolve 放行 / hold 判止 ──────────────────────────

    def test_evolve_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), score=_score("evolve"))
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertTrue(r["ok"])
            self.assertEqual(r["state"], "evolve")
            self.assertEqual(r["rationale"], "7 席均分 96.2 过 95 线")
            self.assertEqual(r["scores"]["joint_review_avg_score"], 96.2)
            self.assertEqual(r["scores"]["fade001_internal_score"], 91.0)

    def test_hold_gate_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), score=_score("hold", rationale="缺陷同根连现"))
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "hold")
            self.assertEqual(r["rationale"], "缺陷同根连现")

    # ── 镜像案 7/8：坏值·坏卷保守拦 ─────────────────────────────────

    def test_bad_decision_conservative_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), score=_score("maybe"))
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-decision")
            self.assertIn("非二值域", r["detail"])

    def test_unparsable_score_conservative_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = self._mk_runs(Path(td))
            (rd / "cos-score.json").write_text("{ broken", encoding="utf-8")
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-decision")

    # ── 镜像案 9/10：prev 选择语义 ──────────────────────────────────

    def test_latest_prev_run_selected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), run_name="shift-W47-old",
                          score=_score("hold", decided_at="2026-11-19T00:00:00Z"))
            time.sleep(0.05)
            self._mk_runs(Path(td), run_name="shift-W47-new",
                          score=_score("evolve", decided_at="2026-11-20T00:00:00Z"))
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertEqual(r["state"], "evolve")  # mtime 最新=上轮
            self.assertEqual(r["prev_run_dir"], "shift-W47-new")

    def test_current_run_dir_naturally_excluded(self) -> None:
        """本轮 run_dir（无 preflight 产物·payload 前建空壳）自然排除钉。"""
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), score=_score("evolve"))
            time.sleep(0.05)
            (Path(td) / "shift-W47-current").mkdir()  # 本轮空壳（零 preflight）
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertEqual(r["state"], "evolve")
            self.assertEqual(r["prev_run_dir"], "shift-W47-test")

    # ── 同构增补案（F2/F3 排除钉·如实注非镜像） ─────────────────────

    def test_empty_shell_pf_excluded(self) -> None:
        """F2 空壳排除钉（ns4 首拍实锚同构承）：零字节 pf=进程壳——gate 排除。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prev = root / "shift-W47-prev"
            prev.mkdir()
            (prev / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (prev / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (prev / "cos-score.json").write_text(json.dumps(_score("evolve")),
                                                 encoding="utf-8")
            time.sleep(0.05)
            shell = root / "shift-W47-shell"  # 本轮进程壳（零字节 pf+close 毕形混态）
            shell.mkdir()
            (shell / "preflight.json").write_text("", encoding="utf-8")
            (shell / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (shell / "cos-score.json").write_text(json.dumps(_score("hold")),
                                                  encoding="utf-8")
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertEqual(r["prev_run_dir"], "shift-W47-prev")
            self.assertEqual(r["state"], "evolve")

    def test_partial_run_excluded(self) -> None:
        """F3 残拍排除钉（ns4 第二拍实锚同构承）：pf 落卷零 close=awaiting 拍
        残链——非完整轮非判决对象轮。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            full = root / "shift-W47-full"
            full.mkdir()
            (full / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (full / "close.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (full / "cos-score.json").write_text(json.dumps(_score("evolve")),
                                                 encoding="utf-8")
            time.sleep(0.05)
            partial = root / "shift-W47-partial"  # 残拍（pf 有·close 无）
            partial.mkdir()
            (partial / "preflight.json").write_text('{"verdict": "pass"}', encoding="utf-8")
            (partial / "cos-score.json").write_text(json.dumps(_score("hold")),
                                                    encoding="utf-8")
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertEqual(r["prev_run_dir"], "shift-W47-full")
            self.assertEqual(r["state"], "evolve")

    # ── 增补案：键缺保守拦+never raises（校准⑤白盒案补承） ──────────

    def test_missing_eviction_decision_conservative_red(self) -> None:
        """卷在但 eviction_decision 键缺=保守拦（非二值域同族）。"""
        with tempfile.TemporaryDirectory() as td:
            self._mk_runs(Path(td), score={"rationale": "缺判定键"})
            r = check_cos_decision(td, now_ts=datetime.now(timezone.utc))
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "awaiting-decision")

    def test_never_raises_on_weird_inputs(self) -> None:
        """never raises 异常面族（校准⑤）：奇异输入零 raise 恒返 dict。"""
        with tempfile.TemporaryDirectory() as td:
            weird = Path(td) / "not-a-dir.txt"
            weird.write_text("file", encoding="utf-8")
            for root in (None, "", str(weird), td):
                r = check_cos_decision(root if root != "" else None)
                self.assertIsInstance(r, dict)
                self.assertIn("ok", r)
                self.assertIn("state", r)


if __name__ == "__main__":
    unittest.main()
