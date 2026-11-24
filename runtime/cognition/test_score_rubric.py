"""FADE-001 阶段 7 score skill 考卷面骨架单测（结构门+注记位·考卷侧零改动遵行面）。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition import score_rubric as score_rubric_mod
from runtime.cognition.score_rubric import (
    F2_ZERO_TRIGGER_FULL_SCORE,
    RUBRIC_COLUMNS,
    T1_CANDIDATE_NOTES,
    redline_cap,
    validate_rubric,
)


def _row(fid: str, w: int) -> dict:
    return {
        "family_id": fid, "family_name": f"族{fid}", "reading_point": "x",
        "collection_cmd": "ssh ...", "verdict_rule": "绿=x", "weight": w,
        "close_layer": "生产面=首拍", "special_clause": "",
    }


class RubricSchemaTest(unittest.TestCase):
    """卷面结构门。"""

    def test_valid_eight_families_pass(self) -> None:
        rubric = [_row(f, 1) for f in "ABCDEFGH"]
        # 权重合计补到 100（93+7×1=100）
        rubric[0]["weight"] = 93
        self.assertEqual(validate_rubric(rubric), [])

    def test_weight_total_must_be_100(self) -> None:
        rubric = [_row(f, 1) for f in "ABCDEFGH"]  # 合计 8
        errors = validate_rubric(rubric)
        self.assertTrue(any("!= 100" in e for e in errors))

    def test_missing_column_rejected(self) -> None:
        rubric = [_row("A", 100)]
        del rubric[0]["weight"]
        errors = validate_rubric(rubric)
        self.assertTrue(any("missing column: weight" in e for e in errors))

    def test_illegal_family_id_rejected(self) -> None:
        rubric = [_row("Z", 100)]
        errors = validate_rubric(rubric)
        self.assertTrue(any("非法" in e for e in errors))

    def test_duplicate_family_id_rejected(self) -> None:
        rubric = [_row("A", 50), _row("A", 50)]
        errors = validate_rubric(rubric)
        self.assertTrue(any("duplicates" in e for e in errors))


class RedlineCapTest(unittest.TestCase):
    """红灯定性上限（§三.4：C 红上限 79·G 红上限 59·红灯不洗白）。"""

    def test_caps(self) -> None:
        self.assertEqual(redline_cap("C"), 79)
        self.assertEqual(redline_cap("G"), 59)
        self.assertIsNone(redline_cap("A"))
        self.assertIsNone(redline_cap("F"))


class F2AndT1Test(unittest.TestCase):
    """F2 免评分母过渡标注+T1 注记位（内容位空·指针如实·禁编造）。"""

    def test_f2_zero_trigger_full_score(self) -> None:
        """CPO 口径 2：零触发+标记正常=满分·不因无告警读数扣分（F3 族规）。"""
        self.assertTrue(F2_ZERO_TRIGGER_FULL_SCORE)

    def test_t1_ruling_filled_with_effective_pend_mark(self) -> None:
        """定谳形填位（CTO 19:43 令·a2c246908 原样零修订）：三断言在+候施工验收毕
        生效标注在（CPO 裁③：落位≠改卷生效）+零权重条款+联合覆盖语义注（19:44 补注）。"""
        a = T1_CANDIDATE_NOTES["assertions"]
        self.assertEqual([x["id"] for x in a], ["T1-1", "T1-2", "T1-3"])
        self.assertTrue(all(x["assertion"] and x["mechanical_check"]
                            and x["two_layer_anchor"] and x["fail_direction"]
                            for x in a))
        self.assertIn("候施工验收毕生效", T1_CANDIDATE_NOTES["status"])
        self.assertIn("落位≠改卷生效", T1_CANDIDATE_NOTES["status"])
        self.assertIn("零权重", T1_CANDIDATE_NOTES["zero_weight_clause"])
        self.assertIn("联合覆盖", T1_CANDIDATE_NOTES["coverage_note"])
        self.assertIn("拦截态有 T1-3 承载", T1_CANDIDATE_NOTES["coverage_note"])
        self.assertTrue(T1_CANDIDATE_NOTES["pointers"])


class MainTest(unittest.TestCase):
    def test_main_pass_and_report_shape(self) -> None:
        from runtime.cognition.score_rubric import main
        with tempfile.TemporaryDirectory() as td:
            rf = Path(td) / "rubric.json"
            rubric = [_row(f, 1) for f in "ABCDEFGH"]
            rubric[0]["weight"] = 93
            rf.write_text(json.dumps(rubric), encoding="utf-8")
            out = Path(td) / "report.json"
            self.assertEqual(main(["--rubric-file", str(rf), "--out", str(out)]), 0)
            rep = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(rep["verdict"], "pass")
            self.assertEqual(rep["redline_caps"], {"C": 79, "G": 59})
            self.assertTrue(rep["f2_zero_trigger_full_score"])

    def test_main_missing_file_exit2(self) -> None:
        from runtime.cognition.score_rubric import main
        self.assertEqual(main(["--rubric-file", "no-such.json"]), 2)


class RepoRubricArtifactTest(unittest.TestCase):
    """仓内实件锚定案（review 日栏一⑦·2026-11-14 落）。

    rubric-firstshoot.json=FADE-001 首拍考卷在役件（payload 段 7
    --rubric-file 指向位·部署树窗 2026-11-13 落仓 e938db317 关联
    TriCompany 0f1fa1f）——既有 12 案全 fixture 自构·实件零锚=考卷
    被误改/破结构/权重漂移回归全绿假阴性。本案每轮回归机械复验实件
    结构门+定谳值快照（改卷窗同窗升版义务的机械化：改卷须同窗升改
    本案快照·静默漂移直接红）。

    投影件属性：md 清单卷=正身·两源对表锚=CPO 定谳注 0c780b4b6+
    STE 采集卷 a5ec899db。
    """

    def test_repo_rubric_firstshoot_artifact_passes_validate(self) -> None:
        path = Path(score_rubric_mod.__file__).parent / "rubric-firstshoot.json"
        rubric = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_rubric(rubric), [])
        # 值面复验（键存在性抽验≠值面验证·合计与族号集独立断言）
        self.assertEqual(sum(r["weight"] for r in rubric), 100)
        self.assertEqual(
            sorted(r["family_id"] for r in rubric),
            ["A", "B", "C", "D", "E", "F", "G", "H", "I"],  # 并盘形 I 族入卷
        )

    def test_repo_rubric_weights_snapshot_cpo_ruling(self) -> None:
        """权重快照=并盘 100 形九族（CEO 直令 2026-11-15 16:23:35 乙 v2：A9/B9/C13/D9/E9/F13/G19/H9+I10=100·CTO 勘正卷 a3793c559——原 CPO 定谳 A10..H10 八族沿革留痕）。

        改卷窗义务机械面：任何权重变更须同窗升改本快照（防静默漂移）
        +红灯上限映射（C79/G59）在役值对表。
        """
        path = Path(score_rubric_mod.__file__).parent / "rubric-firstshoot.json"
        rubric = json.loads(path.read_text(encoding="utf-8"))
        weights = {r["family_id"]: r["weight"] for r in rubric}
        self.assertEqual(
            weights,
            {"A": 6, "B": 6, "C": 9, "D": 6,
             "E": 6, "F": 9, "G": 14, "H": 9, "I": 35},  # v2.1.0（CEO 批 2026-11-25·65+35）
        )
        self.assertEqual(redline_cap("C"), 79)
        self.assertEqual(redline_cap("G"), 59)


if __name__ == "__main__":
    unittest.main()


class MergeRubricGuardTest(unittest.TestCase):
    """勘修改动面新案③（3bcd372 复验席补位）：63 勘误值拒收·字面守卫活体。

    CTO 门禁勘正①：63 禁入代码/测试面（机判域实算 59=B9+C13+D9+E9+G19）——
    拒收面=两域 score_engine 源面 63 勘误值零现势守卫（值面守卫·非仅存在性）。"""

    def test_fade_protocol_engine_no_erroneous_63(self) -> None:
        """fade_protocol 域：三域形 docstring 59/31/10 在·63 勘误值零现势。"""
        import re
        from pathlib import Path
        src = (Path(score_rubric_mod.__file__).parent.parent / "fade_protocol" / "score_engine.py").read_text(encoding="utf-8")
        self.assertIn("59/31/10", src, "三域直加现值注在卷")
        self.assertNotIn("63", src, "勘误值 63 拒收（CTO 勘正①·禁入代码面）")

    def test_cognition_engine_weights_not_63(self) -> None:
        """cognition 域：机判域和=59 活体（39 案勾稽同源·63 零现势守卫）。"""
        from pathlib import Path
        from runtime.cognition import score_engine as se
        src = Path(se.__file__).read_text(encoding="utf-8")
        self.assertNotIn("63", src.replace("L63", "").replace(":63", ""), "勘误值 63 拒收")
        import json
        rubric = json.loads((Path(se.__file__).parent / "rubric-firstshoot.json").read_text(encoding="utf-8"))
        machine = sum(r["weight"] for r in rubric if r["family_id"] in ("B", "C", "D", "E", "G"))
        self.assertEqual(machine, 41, "三域勾稽 v2.1.0：机判 41+采集 24+主观 35=100")
