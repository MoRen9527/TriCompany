"""FADE-001 阶段 7: score skill 考卷面骨架（fsd-ten-stage-tech-collab §三路线框架·PM §一段 7 行）。

**考卷侧零改动遵行**（PM §一 段 7 行·08f135f16 建议 C 原样）：首拍评分清单正身=
pm-firstshoot-reading-checklist-20261113.md（八族八列·A-H 权重合计 100·CPO 裁
76c9fa287×STE 判据 d14f3f527×PM 格式面三方零冲突并卷）——**零改动·本模块不复制
八族内容**（复制=卷面漂移风险·改卷制=件⑥候选窗）。

本骨架=十阶段形候换形的**结构承载**（候部署树授权窗 payload 换形时点·清单卷
§判据换形注「随换形勘注升版」位的机械面）：
  ①rubric schema+结构门（八列字段族/族号 A-H 键集/权重合计=100 断言）
  ②红灯定性上限映射（族 C 红=79 上限·族 G 红=59 上限·红灯不因其他族高分洗白）
  ③F2 免评分母过渡标注（CPO 口径 2·F3 族规：零触发+标记正常=满分不因无告警扣分）
  ④T1 三断言候选注记位——**内容位空·指针如实**（候选断言内容=STE/CPO 域输入·
    本席不编造；preflight+到岗并入注=候选内容构成方向·候 CTO 枢纽派工单带约束）

退出码同族：0 校验过；2 结构门拦。
"""

from __future__ import annotations

import argparse
import sys
import json as _json
from pathlib import Path

RUBRIC_VERSION = "1.0.0"

# 卷面列族（PM §一 八列形·族名正形=STE 原样采认）
RUBRIC_COLUMNS = (
    "family_id",    # 族号（A-H 机械键）
    "family_name",  # 族名（STE 原样正名·任务语言别名不入正名列）
    "reading_point",   # 读数点
    "collection_cmd",  # 采集源+命令形（STE 面）
    "verdict_rule",    # 判定面（绿灯/红灯读数）
    "weight",          # 权重（CPO 裁值）
    "close_layer",     # 收口层标注（两层锚显标）
    "special_clause",  # 免评/特款挂钩
)
_FAMILY_IDS = tuple("ABCDEFGH")
_REDLINE_CAPS = {"C": 79, "G": 59}  # 红灯定性上限（§三.4·红灯不洗白）
# 消费面公开别名（score_engine 实弹装配令②·2026-11-14 CEO 11:45 直令）——
# 同值同源零复制：engine 引 REDLINE_CAPS 不硬编码上限值·改值即两处同动·零删私有名。
REDLINE_CAPS = _REDLINE_CAPS
# F2 免评分母过渡标注（08f135f16 建议 C 原样·CPO 口径 2）
F2_ZERO_TRIGGER_FULL_SCORE = True

# T1 三断言注记位（CTO 定谳令 19:43 填位·3d5b7dc3f 技术稿 §三.6·CPO 追裁裁 (b) STE 形
# 维持——按 STE 草案 a2c246908 三断言形**原样零修订**落。程序位钉子（CPO 裁③原样）：
# **候选内容落位≠改卷生效**——本注记带「候施工验收毕生效」标注·生效动作锚施工验收毕
# 时点（工序序：施工毕→段门验收毕→改卷生效→23:50 首拍）。零权重零分值维持——
# 结构门二值判据·红=对应八族族红走红灯定性条款（C/G 上限 79/59 衔接）·断言级权重
# 不入卷（违同值同源）。
T1_CANDIDATE_NOTES = {
    "status": (
        "定谳已落（CTO 19:43 填位指令·3d5b7dc3f·CPO 追裁裁(b) STE 形维持）·"
        "a2c246908 原样零修订落位·【候施工验收毕生效】（CPO 裁③：落位≠改卷生效·"
        "生效动作锚施工验收毕时点）"
    ),
    "direction_note": "评分对象=产物非过程（过程判据在八族采集清单·两面对表不重叠·STE §二原样）",
    "coverage_note": (
        "T1-2 与 T1-3=两断言联合覆盖两形态（CTO 19:44 补注·PM 卷 §六候采件采认）："
        "首拍若拦截态则 T1-2 红（preflight 退出码非 0）+T1-3 触发分支接管（告警文案"
        "带 run id=可观测性增益得分面·非静默拦截零分形）——防把 T1-2 读成「任何形态"
        "都必须退出码 0」的误读（拦截态有 T1-3 承载）。T1=结构门通过态形（非分值形）。"
    ),
    "zero_weight_clause": "零权重零分值维持——断言级权重不入卷（违同值同源）·红=族红走红灯定性条款",
    "pointers": [
        "ste-t1-assertion-draft-20261113.md（a2c246908·定谳正身）",
        "CTO 技术稿 §三.6（3d5b7dc3f·定谳笔）",
        "pm-stages4-10-product-segment-20261113.md §一段 7 行",
        "08f135f16（F2 子项免评分母过渡·建议 C）",
        "pm-firstshoot-reading-checklist-20261113.md §判据换形注",
    ],
    # 三断言原样（a2c246908 §一 零修订·CTO 定谳精化标注随行）
    "assertions": [
        {
            "id": "T1-1",
            "family": "C 族倒排（验收锚①同源）",
            "name": "run 身份结构断言",
            "assertion": (
                "首拍 run id 三处同串（per-run log 目录名/聚合文件名/close 记录引用）"
                "+格式正则 ^shift-W\\d+-\\d{8}T\\d{6}Z$（照 STE §四 C 族已对表正形原样"
                "继承·零新增收紧）全过"
            ),
            "mechanical_check": "ls /var/lib/trirmc/cron/runs | grep '^shift-W' 取首拍 RUN_ID→三处 grep 同串计数=3+正则匹配计数=3",
            "two_layer_anchor": "单测面=格式正则金值案（已有谱可扩）·生产面收口点=首拍",
            "fail_direction": "三处不同串=溯源断链（漏报方向毒·traceability 丢失）——fail-closed 显红",
            "ruling_note": "CTO 定谳前置定位注：无三处同串则产物落位无从定位=验收锚①正身",
        },
        {
            "id": "T1-2",
            "family": "D+E 族倒排（阶段 2 锚 1 生产面收口同件）",
            "name": "qualify 资格面结构断言",
            "assertion": (
                "runs/<RUN_ID>/qualify.json 存在+五断言全过态字段（零误拦）+"
                "runs/<RUN_ID>/preflight.json 存在+退出码 0——双 json 落位=到岗资格面"
                "结构完整"
            ),
            "mechanical_check": "两 json 存在性断言（python json.load 成功+状态字段值读）+qualify 五断言过态字段逐一非 null",
            "two_layer_anchor": "单测面=五断言五案 19/19 已实锚·生产面收口点=首拍（生产面 qualify 首读数）",
            "fail_direction": "误拦=首拍炸（fail-closed 安全方向如实显红）；假绿（json 在但状态字段空）=漏报——值面字段必读非仅存在性（键存在性抽验≠值面验证纪律正形承载）",
            "ruling_note": "CTO 定谳精化：D+E 族双 json 落位+值面字段必读非仅存在性+退出码 0",
        },
        {
            "id": "T1-3",
            "family": "F 族倒排（锚②③收口同窗）",
            "name": "告警链结构断言",
            "assertion": (
                "首拍成跑形态下 alarm 零触发（满分免评分母形·CPO 口径 2）+若触发分支"
                "（漏拍/败跑窗）告警文案含 RUN_ID（traceable·trap 兜底语义实装形）+"
                "到达时延≤N（N 对表 CPO-011 ≤2h 同值同源·grace 35min⊂2h 合规在卷）"
            ),
            "mechanical_check": "alarm 日志（healthz logPath 投影）触发行计数+文案 RUN_ID grep+到达时戳差值计算（COS/CEO 收件箱到达读数=值席面采集）",
            "two_layer_anchor": "单测面=alarm 25/25+47/47 判定矩阵已实锚（不含生产链）·生产面收口点=首拍+00:25 窗",
            "fail_direction": "零触发+应触发未触发=漏报（毒）；误触发=误报（方向安全如实显红）",
            "ruling_note": "CTO 定谳精化：N=2h·35min=alarm 触发窗岗位不跨界",
        },
    ],
}


def validate_rubric(rubric: list[dict]) -> list[str]:
    """卷面结构门：列族/族号键集/权重合计=100/红灯映射在。"""
    errors: list[str] = []
    if not isinstance(rubric, list) or not rubric:
        return ["rubric not a non-empty list"]
    for i, row in enumerate(rubric):
        for col in RUBRIC_COLUMNS:
            if col not in row:
                errors.append(f"row[{i}] missing column: {col}")
        fid = row.get("family_id")
        if fid not in _FAMILY_IDS:
            errors.append(f"row[{i}] family_id={fid!r} 非法（A-H 机械键）")
        w = row.get("weight")
        if not isinstance(w, (int, float)):
            errors.append(f"row[{i}] weight={w!r} 非数值")
    ids = [r.get("family_id") for r in rubric]
    if len(set(ids)) != len(ids):
        errors.append("family_id duplicates（族号唯一）")
    weights = [r.get("weight") for r in rubric if isinstance(r.get("weight"), (int, float))]
    if sum(weights) != 100:
        errors.append(f"weight total={sum(weights)} != 100（合计断言·§二合计 100 分制）")
    for fid, cap in _REDLINE_CAPS.items():
        if not isinstance(cap, int):
            errors.append(f"redline cap {fid}={cap!r} 非法")
    return errors


def redline_cap(family_id: str) -> int | None:
    """红灯族上限查（族 C 红=79·族 G 红=59·其余族无上限=None）。"""
    return _REDLINE_CAPS.get(family_id)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 7 考卷面骨架（结构门+注记位）")
    p.add_argument("--rubric-file", required=True, help="考卷 JSON（行族=§一 八列）")
    p.add_argument("--out", default=None, help="校验报告落卷位（缺省只打印）")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    rf = Path(args.rubric_file)
    if not rf.is_file():
        print(f"rubric file not found: {rf}（NOT_FOUND·不造替身）")
        return 2
    try:
        rubric = _json.loads(rf.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"rubric unreadable: {type(e).__name__}: {e}")
        return 2
    errors = validate_rubric(rubric)
    report = {
        "rubric_version": RUBRIC_VERSION,
        "verdict": "fail" if errors else "pass",
        "reasons": errors,
        "redline_caps": _REDLINE_CAPS,
        "f2_zero_trigger_full_score": F2_ZERO_TRIGGER_FULL_SCORE,
        "t1_candidate_notes": T1_CANDIDATE_NOTES,
    }
    out = _json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # 非 UTF-8 宿主输出面兜底（GBK 炸 ⊂ 实锚）
    except Exception:  # noqa: BLE001 — 老宿主无 reconfigure 时维持默认
        pass
    print(out)
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
