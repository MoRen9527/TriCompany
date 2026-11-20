"""gate_probe_production.py 单测 — D3 层 3·生产探针投影族（cto-gate-interface-ruling
§二 层 3·校准①②白盒）。

案族：AND 投影映射（判止/挂起/skip 中性/放行）+双门崩 fail-closed+审计 log
stderr 面。集成锚案（production_gate_probe 传 run_review·gate_state 断言）落
骨架镜像面白盒（score_skill.py 部署窗随迁·本树零 score_skill——如实注）。

跑法：cd TriCompany && python -m unittest runtime.cognition.test_gate_probe_production -v
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr

from runtime.cognition.gate_probe_production import production_gate_probe


def _ceo(state: str, ok: bool | None = None) -> dict:
    if ok is None:
        ok = state in ("continue", "skip")
    return {"ok": ok, "state": state, "detail": f"ceo {state}",
            "prev_run_dir": "shift-W47-prev"}


def _cos(state: str, ok: bool | None = None) -> dict:
    if ok is None:
        ok = state in ("evolve", "skip")
    return {"ok": ok, "state": state, "detail": f"cos {state}",
            "prev_run_dir": "shift-W47-prev"}


class GateProbeProjectionTest(unittest.TestCase):
    """AND 投影映射族（施工选定形·候 CTO 终审如实注）。"""

    def test_continue_and_evolve_passes(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("continue"),
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        self.assertEqual(r, "continue")

    def test_layer1_terminate_wins(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("terminated"),
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        self.assertEqual(r, "terminate")

    def test_layer2_hold_terminates(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("continue"),
                                  cos_fn=lambda r, n=None: _cos("hold"))
        self.assertEqual(r, "terminate")

    def test_layer1_awaiting_absent(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("awaiting-ruling"),
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        self.assertEqual(r, "absent")

    def test_layer2_awaiting_absent(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("continue"),
                                  cos_fn=lambda r, n=None: _cos("awaiting-decision"))
        self.assertEqual(r, "absent")

    def test_double_skip_absent(self) -> None:
        """校准①映射表承：skip→absent（首轮面=开轮令域非本门域·如实注）。"""
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("skip"),
                                  cos_fn=lambda r, n=None: _cos("skip"))
        self.assertEqual(r, "absent")

    def test_skip_neutral_with_evolve(self) -> None:
        """skip 中性门（ok=True 向后兼容）+层 2 有效态→另一门决定。"""
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("skip"),
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        self.assertEqual(r, "continue")

    def test_skip_neutral_with_continue(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("continue"),
                                  cos_fn=lambda r, n=None: _cos("skip"))
        self.assertEqual(r, "continue")

    def test_awaiting_with_skip_absent(self) -> None:
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("awaiting-ruling"),
                                  cos_fn=lambda r, n=None: _cos("skip"))
        self.assertEqual(r, "absent")

    def test_unknown_state_conservative_absent(self) -> None:
        """越域态保守 absent（零放行默认·同构保守拦精神）。"""
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("weird"),
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        self.assertEqual(r, "absent")


class GateProbeFailClosedTest(unittest.TestCase):
    """双门崩 fail-closed+审计 log 面（校准⑤ never raises 承）。"""

    def test_layer1_crash_absent(self) -> None:
        def boom(r, n=None):
            raise RuntimeError("l1 boom")
        r = production_gate_probe(ceo_fn=boom,
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        self.assertEqual(r, "absent")

    def test_layer2_crash_absent(self) -> None:
        def boom(r, n=None):
            raise RuntimeError("l2 boom")
        r = production_gate_probe(ceo_fn=lambda r, n=None: _ceo("continue"),
                                  cos_fn=boom)
        self.assertEqual(r, "absent")

    def test_never_raises_returns_str(self) -> None:
        """恒返 str（B 注入形契约面·31 案零改动锚）。"""
        def boom(r, n=None):
            raise ValueError("x")
        r = production_gate_probe(ceo_fn=boom, cos_fn=boom)
        self.assertIsInstance(r, str)
        self.assertIn(r, ("continue", "terminate", "absent"))

    def test_audit_log_to_stderr(self) -> None:
        """审计面→stderr（校准②承：detail/age/escalated 留探针 log）。"""
        buf = io.StringIO()
        with redirect_stderr(buf):
            production_gate_probe(ceo_fn=lambda r, n=None: _ceo("continue"),
                                  cos_fn=lambda r, n=None: _cos("evolve"))
        out = buf.getvalue()
        self.assertIn("[gate-probe]", out)
        self.assertIn("l1=continue", out)
        self.assertIn("l2=evolve", out)


if __name__ == "__main__":
    unittest.main()
