"""FADE-001 阶段 4 DCE 段序编排骨架单测（白盒·零生产触铁律机械面）。

案族对表（fsd-ten-stage-tech-collab §三 阶段 4 行+CPO 件预演形判读）：
  ①渲染面：四步序（pull→migrate→commit→push）+模板变量代入+rc_guard 值面
  ②dry-run 面：默认形态零执行（mode=dry_run·rc=None·verdict=pass）
  ③execute 面：rc_guard 拦停段（非零 rc→exit 2+failed_step+后续步骤零执行）
  ④execute 全绿面：mock 全零 rc→verdict=pass
  ⑤main 落卷面：dce.json+哑卷防线+默认无 --execute=dry-run（零生产触机械断言）
"""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cognition import dce_steps
from runtime.cognition.dce_steps import DCE_VERSION, render_steps, run_dce


def _args(**kw) -> argparse.Namespace:
    with tempfile.TemporaryDirectory() as td:
        pass  # 调用方自定路径——base 不持临时目录
    base = dict(
        tmv_root="D:/Code/ai/TriMetaverse",
        plan_file="D:/Code/ai/TriMetaverse/run/plan.json",
        run_dir="unused", run_id="shift-W46-20261115T160000Z",
        from_week="W46", to_week="W47",
        start_date="2026-11-16",
        operating_root="D:/Code/ai/TriMetaverse/docs/workflow/operating-records",
        execute=False, step_timeout=120,
    )
    base.update(kw)
    args = argparse.Namespace(**base)
    args.dry_run = not args.execute  # main 同款推导（run_dce 消费面）
    return args


class RenderStepsTest(unittest.TestCase):
    """渲染面：段序+模板代入+rc_guard 值面。"""

    def test_step_order_and_substitution(self) -> None:
        steps = render_steps(
            "T:/tmv", "T:/run/plan.json", "shift-X",
            from_week="W46", to_week="W47",
            start_date="2026-11-16",
            operating_root="T:/tmv/docs/workflow/operating-records",
        )
        self.assertEqual(
            [s["step"] for s in steps], ["pull", "migrate", "commit", "push"]
        )
        self.assertEqual(steps[0]["cmd"], "git -C T:/tmv pull --ff-only")
        self.assertIn("shift-X", steps[2]["cmd"])

    def test_migrate_cmd_matches_weekly_plane_shift_argparse(self) -> None:
        """migrate cmd 参数面=weekly_plane_shift argparse 实锚（L348-352 五参数）。

        生产形勘正锚（部署树窗 2026-11-13）：G3 骨架形 --plan-file 系 CLI 不识
        参数（--execute 必 SystemExit(2)）——本案钉死正形参数面防回退。
        """
        steps = render_steps(
            "T:/tmv", "T:/run/plan.json", "shift-X",
            from_week="W46", to_week="W47",
            start_date="2026-11-16",
            operating_root="T:/ops",
        )
        cmd = steps[1]["cmd"]
        self.assertIn("python3 -m runtime.cognition.weekly_plane_shift", cmd)
        self.assertIn("--from W46", cmd)
        self.assertIn("--to W47", cmd)
        self.assertIn("--start-date 2026-11-16", cmd)
        self.assertIn("--operating-root T:/ops", cmd)
        self.assertIn("--sync", cmd)
        self.assertNotIn("--plan-file", cmd)  # CLI 不识该参数（勘正面）

    def test_commit_cmd_exact_pathspec_not_add_a(self) -> None:
        """commit cmd=add 精确 pathspec 禁 -A（W47 残留/未跟踪件零卷入）+
        zero-diff 防线+vB 识别式消息形（grep RUN_ID 回滚识别锚）。"""
        steps = render_steps(
            "T:/tmv", "T:/run/plan.json", "shift-W46-X",
            from_week="W46", to_week="W47",
            start_date="2026-11-16", operating_root="T:/ops",
        )
        cmd = steps[2]["cmd"]
        self.assertIn("git -C T:/tmv add docs/workflow/operating-records", cmd)
        self.assertNotIn("add -A", cmd)  # 全仓 add 面禁（残留卷入防线）
        self.assertIn("git -C T:/tmv diff --cached --quiet", cmd)  # zero-diff 防线
        self.assertIn(
            "commit -m 'ops: weekly plane shift W46->W47 run=shift-W46-X'", cmd
        )  # vB 识别式原形（SDE §二回滚识别锚）

    def test_push_cmd_sg_bare_channel_with_retry(self) -> None:
        """push cmd=sg-bare 通道（河源 TMV remote 真值·V4 读数锚面）+
        vB 原形断通道 fetch/merge 重试面。"""
        steps = render_steps(
            "T:/tmv", "T:/run/plan.json", "shift-X",
            from_week="W46", to_week="W47",
            start_date="2026-11-16", operating_root="T:/ops",
        )
        cmd = steps[3]["cmd"]
        self.assertIn("git -C T:/tmv push sg-bare HEAD:dev", cmd)
        self.assertNotIn("push origin dev", cmd)  # 骨架形通道错位禁（勘正面）
        self.assertIn("fetch sg-bare dev", cmd)  # 断通道重试面（vB 原形）
        self.assertIn("merge --no-edit FETCH_HEAD", cmd)

    def test_rc_guard_values(self) -> None:
        """push=断通道降级面（rc_guard=False）·其余三步全 guard。"""
        steps = render_steps("T", "T/p", "r")
        guards = {s["step"]: s["rc_guard"] for s in steps}
        self.assertTrue(guards["pull"])
        self.assertTrue(guards["migrate"])
        self.assertTrue(guards["commit"])
        self.assertFalse(guards["push"])


class DryRunTest(unittest.TestCase):
    """dry-run 面：默认形态零执行（零生产触铁律机械面）。"""

    def test_dry_run_no_subprocess_called(self) -> None:
        """dry-run 下 subprocess.run 零调用=零生产触（机械断言）。"""
        with tempfile.TemporaryDirectory() as td:
            args = _args(run_dir=td)
            with mock.patch.object(dce_steps.subprocess, "run") as m:
                code, d = run_dce(args)
                m.assert_not_called()  # 铁律：渲染面零执行
        self.assertEqual(code, 0)
        self.assertEqual(d["mode"], "dry_run")
        self.assertEqual(d["verdict"], "pass")
        self.assertEqual(len(d["steps"]), 4)
        self.assertTrue(all(s["rc"] is None and s["mode"] == "dry_run"
                            for s in d["steps"]))
        self.assertEqual(d["dce_version"], DCE_VERSION)
        # 零外溢对表三处判据位（PM §一 段 4 行必填·aca95877c 口径原样）
        oc = d["overflow_checks"]
        self.assertEqual(
            [c["check"] for c in oc],
            ["week_dir_structure", "carry_over_semantics", "commit_message_shape"],
        )
        self.assertTrue(all(c["basis"] and not c["checked"] for c in oc))


class ExecuteGuardTest(unittest.TestCase):
    """execute 面：rc_guard 拦停段。"""

    def test_guard_step_fail_stops_chain(self) -> None:
        """pull（rc_guard 步）非零 rc → exit 2+failed_step=pull+后续步骤零执行。"""
        with tempfile.TemporaryDirectory() as td:
            args = _args(run_dir=td, execute=True)
            proc = mock.Mock(returncode=128, stderr="not a git repo")
            with mock.patch.object(dce_steps.subprocess, "run", return_value=proc):
                code, d = run_dce(args)
        self.assertEqual(code, 2)
        self.assertEqual(d["verdict"], "fail")
        self.assertEqual(d["failed_step"], "pull")
        self.assertEqual(len(d["steps"]), 1)  # 拦=停段（后续零执行）

    def test_guard_step_pass_then_non_guard_fail_continues(self) -> None:
        """push（非 guard 步）非零 rc → 如实落 rc 但不拦链（exit 0·降级注记面）。"""
        with tempfile.TemporaryDirectory() as td:
            args = _args(run_dir=td, execute=True)
            # 按调用序四步各一调：pull/migrate/commit 全绿·push 非零
            # （禁 cmd 特征匹配——migrate cmd 不含字面 step 名·特征映射=脆弱面）
            proc_ok = mock.Mock(returncode=0, stderr="")
            proc_push_fail = mock.Mock(returncode=1, stderr="push rejected")
            with mock.patch.object(dce_steps.subprocess, "run",
                                   side_effect=[proc_ok, proc_ok, proc_ok, proc_push_fail]):
                code, d = run_dce(args)
        self.assertEqual(code, 0)
        self.assertEqual(d["verdict"], "pass")
        push = next(s for s in d["steps"] if s["step"] == "push")
        self.assertEqual(push["rc"], 1)  # 非零如实落卷（不静默）

    def test_execute_exception_counts_as_fail(self) -> None:
        """执行异常（如 timeout）=rc 非 0 同拦（防线一致面）。"""
        with tempfile.TemporaryDirectory() as td:
            args = _args(run_dir=td, execute=True)
            with mock.patch.object(
                dce_steps.subprocess, "run",
                side_effect=dce_steps.subprocess.TimeoutExpired(cmd="x", timeout=1),
            ):
                code, d = run_dce(args)
        self.assertEqual(code, 2)
        self.assertEqual(d["failed_step"], "pull")


class MainWriteTest(unittest.TestCase):
    """main 层：dce.json 落卷+哑卷防线+默认形态=dry-run。"""

    def test_main_default_is_dry_run(self) -> None:
        """不带 --execute → dry-run（零生产触机械断言·落卷 mode=dry_run）。"""
        from runtime.cognition.dce_steps import main
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            argv = [
                "--tmv-root", str(td),
                "--plan-file", str(run / "plan.json"),
                "--run-dir", str(run),
                "--run-id", "shift-W46-test",
            ]
            self.assertEqual(main(argv), 0)
            d = json.loads((run / "dce.json").read_text(encoding="utf-8"))
            self.assertEqual(d["mode"], "dry_run")
            self.assertEqual(d["verdict"], "pass")

    def test_unwritable_run_dir_is_exit2(self) -> None:
        from runtime.cognition.dce_steps import main
        with tempfile.TemporaryDirectory() as td:
            blocker = Path(td) / "blocked"
            blocker.write_text("file not dir", encoding="utf-8")
            argv = [
                "--tmv-root", str(td),
                "--plan-file", str(Path(td) / "plan.json"),
                "--run-dir", str(blocker),
            ]
            self.assertEqual(main(argv), 2)


if __name__ == "__main__":
    unittest.main()
