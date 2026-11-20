"""FADE-001 阶段 8 close skill 骨架单测（漏报护栏·CTO 精化二对表）。"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.close_skill import (
    _structure_gate,
    run_close,
    scan_stage_artifacts,
)


def _args(**kw) -> argparse.Namespace:
    base = dict(run_dir="unused", run_id="shift-W46-test",
                from_week="W46", to_week="W47")
    base.update(kw)
    return argparse.Namespace(**base)


class ScanStageArtifactsTest(unittest.TestCase):
    def test_empty_run_dir_notes_not_substitute(self) -> None:
        """全段缺件=notes 如实注记零替身读数·upgrade_list 空=extracted 合法态。"""
        with tempfile.TemporaryDirectory() as td:
            fails, notes = scan_stage_artifacts(Path(td))
            self.assertEqual(fails, [])
            self.assertEqual(len(notes), 6)  # 发现 12 扩 dce.json 后六件形
            self.assertTrue(all("absent" in n for n in notes))

    def test_fail_stage_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "plan.json").write_text(
                json.dumps({"verdict": "fail", "reasons": ["bidir 违"]}),
                encoding="utf-8",
            )
            fails, notes = scan_stage_artifacts(run)
            self.assertEqual(len(fails), 1)
            self.assertEqual(fails[0]["stage"], "plan.json")
            self.assertEqual(len(notes), 5)

    def test_dce_json_fail_stage_extracted(self) -> None:
        """发现 12 扩域案：dce.json（段 4 产物）入扫描域——verdict=fail 同提取
        升级条目（rc_guard 拦停/failed_step 读数面）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "dce.json").write_text(
                json.dumps({"verdict": "fail", "failed_step": "migrate",
                            "reasons": ["rc_guard: migrate exit 2"]}),
                encoding="utf-8",
            )
            fails, _ = scan_stage_artifacts(run)
            self.assertEqual(len(fails), 1)
            self.assertEqual(fails[0]["stage"], "dce.json")
            self.assertEqual(fails[0]["trigger"], "stage_artifact_fail")

    def test_dce_json_absent_noted_in_scan(self) -> None:
        """发现 12 扩域案：dce.json 缺件=absent 如实注记（不拦·六件扫描域断言）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "preflight.json").write_text(
                json.dumps({"verdict": "pass"}), encoding="utf-8"
            )
            fails, notes = scan_stage_artifacts(run)
            self.assertEqual(fails, [])
            dce_notes = [n for n in notes if n.startswith("dce.json")]
            self.assertEqual(len(dce_notes), 1)
            self.assertIn("absent", dce_notes[0])

    def test_upgrade_entry_five_field_spec(self) -> None:
        """升级条目五字段 spec（PM §二）：run_id/stage+trigger/routing/evidence/state。"""
        import re
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "plan.json").write_text(
                json.dumps({"verdict": "fail", "reasons": ["x"]}),
                encoding="utf-8",
            )
            rid = "shift-W46-20261115T160000Z"
            fails, _ = scan_stage_artifacts(run, run_id=rid)
            e = fails[0]
            self.assertEqual(e["run_id"], rid)  # 贯穿主键·正则面
            self.assertRegex(e["run_id"], r"shift-W\d+-\d{8}T\d{6}Z")
            self.assertEqual(e["stage"], "plan.json")  # 段位+触发源
            self.assertEqual(e["trigger"], "stage_artifact_fail")
            self.assertIn(e["routing"], ("候 COS", "候 CEO"))  # 分级二值·终裁归 COS
            self.assertIn("plan.json", e["evidence"])  # 证据指针（禁零锚条目）
            self.assertEqual(e["state"], "open")  # 默认 open·流转 COS 后置 routed

    def test_score_absent_engine_marks_j7(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "score.json").write_text(
                json.dumps({"verdict": "fail", "engine_state": "engine_absent",
                            "reasons": ["score_engine module absent"]}),
                encoding="utf-8",
            )
            fails, _ = scan_stage_artifacts(run)
            self.assertTrue(all("J7" in r for r in fails[0]["reasons"]))
            self.assertEqual(fails[0]["trigger"], "J7_score_engine_absent")

    def test_unreadable_artifact_is_upgrade_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "verify.json").write_text("{ broken", encoding="utf-8")
            fails, _ = scan_stage_artifacts(run)
            self.assertEqual(len(fails), 1)
            self.assertTrue(any("unreadable" in r for r in fails[0]["reasons"]))
            self.assertEqual(fails[0]["trigger"], "artifact_unreadable")


class StructureGateTest(unittest.TestCase):
    """精化二护栏机械面：upgrade_list_state 显式二值禁静默缺省。"""

    GOOD = {
        "close_version": "1.1.0", "run_id": "r", "from_week": "W46",
        "to_week": "W47", "upgrade_list_state": "extracted",
        "upgrade_list": [], "run_state": "ok",
        "notify_target": "COS", "verdict": "pass",
        # WP7 hash 算法形勘正（获批改形 2026-11-18）：evidence 五元组
        # （补 hash·sha256_16 算法形标注正形——D-47 算法形标注防线）
        "evidence": [{"stage_artifact": "plan.json", "path": "plan.json",
                      "present": True,
                      "hash": "sha256_16:0123456789abcdef"}],
        "check_time": "2026-11-15T15:50:00+00:00",
    }

    def test_good_passes(self) -> None:
        self.assertEqual(_structure_gate(dict(self.GOOD)), [])

    def test_missing_state_key_rejected(self) -> None:
        bad = dict(self.GOOD)
        del bad["upgrade_list_state"]
        errors = _structure_gate(bad)
        self.assertTrue(any("upgrade_list_state" in e for e in errors))

    def test_silent_default_value_rejected(self) -> None:
        """state 值非显式二值（None/空/别词）=拦。"""
        for bad_val in (None, "", "auto", "skipped"):
            bad = dict(self.GOOD)
            bad["upgrade_list_state"] = bad_val
            errors = _structure_gate(bad)
            self.assertTrue(
                any("禁静默缺省" in e for e in errors), f"state={bad_val!r} 未拦"
            )

    def test_notify_target_must_be_cos(self) -> None:
        bad = dict(self.GOOD)
        bad["notify_target"] = "BOD"
        errors = _structure_gate(bad)
        self.assertTrue(any("notify_target" in e for e in errors))


class RunCloseTest(unittest.TestCase):
    def test_run_close_full_pass_empty_upgrade_list(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, c = run_close(_args(run_dir=td))
            self.assertEqual(code, 0)
            self.assertEqual(c["upgrade_list_state"], "extracted")
            self.assertEqual(c["upgrade_list"], [])
            self.assertEqual(c["notify_target"], "COS")

    def test_main_writes_close_json(self) -> None:
        from runtime.cognition.close_skill import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            code = main([
                "--run-dir", str(run), "--run-id", "r2",
                "--from-week", "W46", "--to-week", "W47",
            ])
            self.assertEqual(code, 0)
            c = json.loads((run / "close.json").read_text(encoding="utf-8"))
            self.assertIn("upgrade_list_state", c)  # 精化二：键必须显式在
            self.assertIn(c["upgrade_list_state"], ("extracted", "not_extracted"))


# ── 1.1.0 WP7 收口自洽案族（2026-11-18·notice-185 统改施工白盒·拆解任务书获批面） ──


class WP7CloseSelfConsistencyTest(unittest.TestCase):
    """WP7 收口自洽案族：run_state 单值源（manifest 引用形）+notes 自指消除+
    evidence 四元组补 hash（sha256_16 算法形）。"""

    def _mk_run(self, run: Path, files: dict[str, str] | None = None) -> None:
        run.mkdir(parents=True, exist_ok=True)
        for name, content in (files or {}).items():
            (run / name).write_text(content, encoding="utf-8")

    def test_run_state_single_source_pending_manifest(self) -> None:
        """单值源钉①（manifest 缺席=常态）：close 不自判 stale——run_state=
        pending_manifest 显式引用态（双面矛盾消除·终态权威在 manifest）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            self._mk_run(run, {"plan.json": json.dumps({"verdict": "pass"})})
            code, c = run_close(_args(run_dir=str(run)))
            self.assertEqual(code, 0)
            self.assertEqual(c["run_state"], "pending_manifest")
            self.assertEqual(c["run_state_source"], "pending")

    def test_run_state_single_source_manifest_value(self) -> None:
        """单值源钉②（manifest 在盘）：close run_state=manifest run_state 原值
        （零自判·引用直读）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            self._mk_run(run, {
                "plan.json": json.dumps({"verdict": "pass"}),
                "manifest.json": json.dumps({"run_state": "failed"}),
            })
            code, c = run_close(_args(run_dir=str(run)))
            self.assertEqual(code, 0)
            self.assertEqual(c["run_state"], "failed")  # manifest 原值·非自判
            self.assertEqual(c["run_state_source"], "manifest")

    def test_self_reference_eliminated(self) -> None:
        """自指消除钉：notes 含 close.json self_artifact 显式语义条·零
        「close.json: absent」自指形（notes 载 absent 而件在=原自指实锚禁再现）。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            self._mk_run(run, {"plan.json": json.dumps({"verdict": "pass"})})
            code, c = run_close(_args(run_dir=str(run)))
            self.assertEqual(code, 0)
            notes = "\n".join(c["stage_artifact_notes"])
            self.assertIn("self_artifact", notes)
            self.assertNotIn("close.json: absent", notes)
            # 存在性实查形：在盘件 notes 零 absent 误注
            self.assertNotIn("plan.json: absent", notes)

    def test_evidence_hash_algo_tagged_sha16(self) -> None:
        """hash 钉：evidence 全条 hash 载+算法形标注（sha256_16: 前缀·D-47
        算法形标注防线）——在盘件=16 hex 摘要投影·缺席件=not_computed:absent。"""
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            self._mk_run(run, {"plan.json": json.dumps({"verdict": "pass"})})
            code, c = run_close(_args(run_dir=str(run)))
            self.assertEqual(code, 0)
            by_name = {e["stage_artifact"]: e for e in c["evidence"]}
            h = by_name["plan.json"]["hash"]
            self.assertTrue(h.startswith("sha256_16:"))
            self.assertEqual(len(h.split(":")[1]), 16)
            hm = by_name["manifest.json"]["hash"]
            self.assertEqual(hm, "sha256_16:not_computed:absent")

    def test_structure_gate_hash_poison_rejected(self) -> None:
        """结构门 hash 毒化拦钉：evidence 无 hash/裸 hash（无算法形前缀）→拦
        （五元组强制+算法形标注强制）。"""
        good = dict(StructureGateTest.GOOD)
        for poison_ev in (
            [{"stage_artifact": "p", "path": "p", "present": True}],
            [{"stage_artifact": "p", "path": "p", "present": True,
              "hash": "deadbeefdeadbeef"}],  # 裸 hash 无算法形=歧义违例
        ):
            bad = dict(good)
            bad["evidence"] = poison_ev
            errors = _structure_gate(bad)
            self.assertTrue(any("hash" in e for e in errors),
                            f"hash 毒化形未拦: {poison_ev}")


if __name__ == "__main__":
    unittest.main()


class WP7ManifestHeaderShapeTest(unittest.TestCase):
    """WP7 时点语义精化钉（ns2 拍实锚 2026-11-18·残面①）：链序时点 manifest=
    run_id 头形（无 run_state 键）→pending_manifest（非 malformed）·真污染形分立。"""

    def test_header_shape_manifest_is_pending_not_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir(parents=True)
            # 链自产头形（payload L11 形·无 run_state 键）
            (run / "manifest.json").write_text(
                json.dumps({"run_id": "r", "from_week": "W46",
                            "to_week": "W47"}), encoding="utf-8")
            code, c = run_close(_args(run_dir=str(run)))
            self.assertEqual(code, 0)
            self.assertEqual(c["run_state"], "pending_manifest")
            self.assertEqual(c["run_state_source"], "pending")

    def test_true_pollution_still_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir(parents=True)
            (run / "manifest.json").write_text('["not", "a", "dict"]',
                                               encoding="utf-8")
            code, c = run_close(_args(run_dir=str(run)))
            self.assertEqual(code, 0)
            self.assertEqual(c["run_state"], "manifest_malformed")
            self.assertEqual(c["run_state_source"], "manifest_polluted")
