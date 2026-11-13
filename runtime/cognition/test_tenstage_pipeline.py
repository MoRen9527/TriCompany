"""FADE-001 G4 集成段：十段管线端到端集成案（段 3-10 仓内域·COO 20:20 G4 即开跑裁）。

集成域=段 3 plan_scope → 4 dce_steps(dry-run 默认·零生产触) → 5 verify(--strict 生产形
深化面) → 6 score_cli(现役域 engine_absent 如实) → 7 score_rubric(结构门独立面) →
8 close_skill(升级条目提取) → 9 close_cli(run_state 终态) → 10 notify_done
(--dry-run-only=render_only 零发送面·零外溢防真 SMTP)。

段 1 触发/段 2 qualify 属 TriRLC 生产面（非本仓承载）——集成案域=本仓八段全链。
run_id 同串贯穿全部段产物=T1-1 结构断言的单测面预演（生产面收口点=首拍·两层锚显标）。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

RUN_ID = "shift-W47-20261116T000000Z"  # 正则形自洽（T1-1 格式族单测面预演值）


class _FakeEngine:
    """engine 已部署形态模拟（部署后形态预演·run_score 契约=返回 dict）。"""

    @staticmethod
    def run_score(run_id: str, run_dir: str, from_week: str, to_week: str) -> dict:
        return {"total": 100, "run_id": run_id}


def _iso(ymd: str) -> tuple[int, int]:
    y, m, d = map(int, ymd.split("-"))
    iso = date(y, m, d).isocalendar()
    return iso[0], iso[1]


class TestTenStageGreenPipeline(unittest.TestCase):
    """全链绿路：段 3→10 顺序跑·同 run dir·run_id 同串贯穿（T1-1 单测面预演）。"""

    def test_full_chain_green(self) -> None:
        from runtime.cognition import (
            close_cli, close_skill, dce_steps, notify_done, plan_scope,
            score_cli, verify,
        )

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # 动态周锚（禁手算）：from=2026-11-09 → to=2026-11-16（ISO 周自洽）
            fy, fw = _iso("2026-11-09")
            ty, tw = _iso("2026-11-16")
            from_week, to_week = f"W{fw:02d}", f"W{tw:02d}"
            start_date = "2026-11-16"

            ops = tmp / "ops"
            from_dir = ops / f"{fy}-{from_week}"
            to_dir = ops / f"{ty}-{to_week}"
            (from_dir / "trees" / "tree-a").mkdir(parents=True)   # status=active → migrate
            ((from_dir / "trees" / "tree-a" / "tree-op.json").write_text(
                json.dumps({"status": "active"}), encoding="utf-8"))
            (from_dir / "trees" / "tree-b").mkdir()               # 空 → keep 默认
            # 注：done∈_KEEP_STATUS（归档保留面）——migrate 判据=非 keep 系 status
            to_dir.mkdir(parents=True)
            (to_dir / "OP-0001.json").write_text(
                json.dumps({"activeTrees": [{"name": "tree-a"}]}), encoding="utf-8")

            run_dir = tmp / "run"
            run_dir.mkdir()
            # 段 1/2 产物=上游 TriRLC 生产面交棒模拟卷（本仓集成域外·derive_run_state
            # absent=stale 判据须六段产物齐才得 ok/failed 真值）
            for upstream in ("preflight.json", "qualify.json"):
                (run_dir / upstream).write_text(
                    json.dumps({"verdict": "pass"}), encoding="utf-8")
            common = ["--run-dir", str(run_dir), "--run-id", RUN_ID,
                      "--from-week", from_week, "--to-week", to_week]

            # 段 3：plan（绿路）
            rc = plan_scope.main(["--operating-root", str(ops),
                                  "--start-date", start_date, *common])
            self.assertEqual(rc, 0, "段 3 plan 应绿")
            plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["verdict"], "pass")
            self.assertEqual([m["entry"] for m in plan["migrate"]], ["tree-a"])

            # 段 4：DCE（dry-run 默认·零生产触·parser 面=tmv-root/plan-file/run-dir/run-id）
            rc = dce_steps.main(["--tmv-root", str(tmp),
                                 "--plan-file", str(run_dir / "plan.json"),
                                 "--run-dir", str(run_dir), "--run-id", RUN_ID])
            self.assertEqual(rc, 0, "段 4 DCE dry-run 应绿")
            dce = json.loads((run_dir / "dce.json").read_text(encoding="utf-8"))
            self.assertEqual(dce["mode"], "dry_run")
            self.assertEqual(dce["verdict"], "pass")
            self.assertEqual([s["step"] for s in dce["steps"]],
                             ["pull", "migrate", "commit", "push"])

            # 段 5：verify（--strict 生产形深化面·tree-a 在 to 周 index=landed）
            rc = verify.main(["--plan-file", str(run_dir / "plan.json"),
                              "--operating-root", str(ops),
                              "--start-date", start_date, "--strict", *common])
            self.assertEqual(rc, 0, "段 5 verify strict 应绿")
            vf = json.loads((run_dir / "verify.json").read_text(encoding="utf-8"))
            self.assertEqual(vf["verdict"], "pass")
            strict_entry = next(c for c in vf["checks"] if c["check"] == "migrate_vs_index")
            self.assertEqual(strict_entry["items"],
                             [{"entry": "tree-a", "status": "landed"}])

            # 段 6：score cli（engine 已部署形态预演=mock 探测点·executed_ok 全绿分支；
            # 现役域 engine_absent=rc 2+J7 升级面如实——负面链域已含，两分支联合覆盖）
            with patch("runtime.cognition.score_cli.probe_score_engine",
                       return_value=(_FakeEngine(), "present")):
                rc = score_cli.main([*common])
            self.assertEqual(rc, 0, "段 6 score（engine present 预演）应绿")
            score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
            self.assertEqual(score["engine_state"], "executed_ok")
            self.assertEqual(score["verdict"], "pass")

            # 段 7：score_rubric 结构门（独立面·fixture 八族权重合计 100）
            rubric = [{"family_id": f, "family_name": f"族{f}", "reading_point": "x",
                       "collection_cmd": "ssh", "verdict_rule": "绿", "weight": 1,
                       "close_layer": "生产面", "special_clause": ""} for f in "ABCDEFGH"]
            rubric[0]["weight"] = 93
            rf = tmp / "rubric.json"
            rf.write_text(json.dumps(rubric), encoding="utf-8")
            from runtime.cognition import score_rubric
            rc = score_rubric.main(["--rubric-file", str(rf)])
            self.assertEqual(rc, 0, "段 7 结构门应绿")

            # 段 8：close skill（扫段产物·绿路=零升级条目+state=extracted 显式）
            rc = close_skill.main([*common])
            self.assertEqual(rc, 0, "段 8 close 应绿")
            close = json.loads((run_dir / "close.json").read_text(encoding="utf-8"))
            self.assertEqual(close["upgrade_list_state"], "extracted")
            self.assertEqual(close["upgrade_list"], [])
            self.assertEqual(close["notify_target"], "COS")

            # 段 9：close cli（run_state 终态落 manifest.json）
            rc = close_cli.main([*common])
            self.assertEqual(rc, 0, "段 9 close_cli 应绿")
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest.get("run_state"), "ok",
                             "六段产物齐+全 pass → ok（stale=缺件族·fail=败族）")

            # 段 10：notify done（--dry-run-only=render_only 零发送·零外溢）
            rc = notify_done.main(["--dry-run-only", *common])
            self.assertEqual(rc, 0, "段 10 notify_done 应绿")
            done = json.loads((run_dir / "notify_done.json").read_text(encoding="utf-8"))
            self.assertEqual(done["notify_result"]["status"], "render_only")

            # T1-1 单测面预演：run_id 同串贯穿全部段产物
            artifacts = ["plan.json", "dce.json", "verify.json", "score.json",
                         "close.json", "manifest.json", "notify_done.json"]
            for name in artifacts:
                data = json.loads((run_dir / name).read_text(encoding="utf-8"))
                self.assertEqual(data.get("run_id"), RUN_ID,
                                 f"{name} run_id 应同串贯穿（T1-1 预演）")


class TestTenStageFailChain(unittest.TestCase):
    """负面拦截链：毒化 plan → verify 拦 exit 2 → close 升级条目五字段 → notify 失败告警面。"""

    def test_fail_chain_upgrade_entry_and_alarm_route(self) -> None:
        from runtime.cognition import close_cli, close_skill, notify_done, score_cli, verify

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fy, fw = _iso("2026-11-09")
            ty, tw = _iso("2026-11-16")
            from_week, to_week = f"W{fw:02d}", f"W{tw:02d}"

            run_dir = tmp / "run"
            run_dir.mkdir()
            # 段 1/2 上游交棒模拟卷（同绿路·derive stale=absent 判据须六段齐）
            for upstream in ("preflight.json", "qualify.json"):
                (run_dir / upstream).write_text(
                    json.dumps({"verdict": "pass"}), encoding="utf-8")
            # 毒化 plan（verdict=fail+counts 毒化）手工落卷
            (run_dir / "plan.json").write_text(json.dumps({
                "verdict": "fail", "migrate": [], "keep": [], "carry_over": [],
                "counts": {"migrate": 3, "keep": 0, "carry_over": 0},
            }), encoding="utf-8")
            common = ["--run-dir", str(run_dir), "--run-id", RUN_ID,
                      "--from-week", from_week, "--to-week", to_week]

            # 段 5：verify 拦（plan_baseline 毒化拦·exit 2）
            rc = verify.main(["--plan-file", str(run_dir / "plan.json"),
                              "--operating-root", str(tmp / "no-such-ops"), *common])
            self.assertEqual(rc, 2, "段 5 verify 应拦毒化 plan")
            vf = json.loads((run_dir / "verify.json").read_text(encoding="utf-8"))
            self.assertEqual(vf["verdict"], "fail")

            # 段 6：score 落卷（engine_absent 如实·六段齐面）
            score_cli.main([*common])

            # 段 8：close 提取升级条目（五字段 spec 值面断言）
            rc = close_skill.main([*common])
            self.assertEqual(rc, 0)  # 结构门绿≠零升级——升级条目如实提取
            close = json.loads((run_dir / "close.json").read_text(encoding="utf-8"))
            self.assertEqual(close["upgrade_list_state"], "extracted")
            self.assertTrue(close["upgrade_list"], "verify fail 应产出升级条目")
            entry = close["upgrade_list"][0]
            self.assertEqual(entry["run_id"], RUN_ID)
            self.assertEqual(entry["trigger"], "stage_artifact_fail")
            self.assertIn(entry["routing"], ("候 COS", "候 CEO"))
            self.assertTrue(entry["evidence"])  # 段产物路径指针·禁零锚
            self.assertEqual(entry["state"], "open")

            # 段 9+10：终态 failed → 失败告警路由面（--dry-run-only 零发送）
            close_cli.main([*common])
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest.get("run_state"), "failed")
            rc = notify_done.main(["--dry-run-only", *common])
            self.assertEqual(rc, 0)
            done = json.loads((run_dir / "notify_done.json").read_text(encoding="utf-8"))
            self.assertEqual(done["route"]["subject_prefix"], "失败告警")
            self.assertEqual(done["run_state"], "failed")  # 文案带 run id=可观测性面


if __name__ == "__main__":
    unittest.main()
