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
            ["A", "B", "C", "D", "E", "F", "G", "H"],
        )

    def test_repo_rubric_weights_snapshot_cpo_ruling(self) -> None:
        """权重快照=CPO 定谳值（A10/B10/C15/D10/E10/F15/G20/H10）。

        改卷窗义务机械面：任何权重变更须同窗升改本快照（防静默漂移）
        +红灯上限映射（C79/G59）在役值对表。
        """
        path = Path(score_rubric_mod.__file__).parent / "rubric-firstshoot.json"
        rubric = json.loads(path.read_text(encoding="utf-8"))
        weights = {r["family_id"]: r["weight"] for r in rubric}
        self.assertEqual(
            weights,
            {"A": 10, "B": 10, "C": 15, "D": 10,
             "E": 10, "F": 15, "G": 20, "H": 10},
        )
        self.assertEqual(redline_cap("C"), 79)
        self.assertEqual(redline_cap("G"), 59)


if __name__ == "__main__":
    unittest.main()
