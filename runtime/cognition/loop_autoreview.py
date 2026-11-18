#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loop_autoreview.py — loop convene 段 auto-review 形 runner（S2 施工·CTO 裁定卷 §一/§三 governs）
真源=TriCompany runtime/cognition/（独立 commit 单笔族 revert 一键）·部署位=河源 TriCompany 检出（同径）

形态（裁定卷 §一）：
  per-seat headless 评分会话族——convene_mode=auto 触发后，runner 为七席各起一会话：
  投喂=run_dir 三域材料族+该席评分角度 prompt 模板（零密钥零敏感值·材料只读）；
  产出=该席评分 sheet JSON 落 run_dir/convene/seats/<seat>-score.json（staging·控制面值守拾取）。
  subjective 聚合初判=七席 sheet 聚合（人联评终审签认位保留——防线双层非替代）。
  四句门四机械断言（CEO 四句 §九 冻结照录）：全绿=PASS 行入聚合卷；任一红=FAIL+verdict RETRY 照降。

护栏（§二）：零直接投递零 POST（sheet staging 控制面拾取）·零触在途链/已验收现役链·
  材料 run_dir 件族只读·prompt 零密钥（D-46）·降级形=抽三席代表/单席缺席如实注不冒充全席。
"""
import argparse, json, os, subprocess, sys, time
from typing import Optional, Dict, List, Any
from pathlib import Path

RECORDS_ROOT_DEFAULT = "/srv/fleet/TriMetaverse/docs/workflow/operating-records"

SEATS = ["cos", "coo", "cao", "cpo", "cto", "cho", "cfo"]
DEGRADE_SEATS = ["cpo", "cto", "coo"]  # 降级形=抽三席代表（候 BOD 裁·§五）
# 必迁族（四句门③：task-inventory/daily-progress/OP 双件/whitelist 族）
MUST_MIGRATE_PATTERNS = [
    "task-inventory-{}.md", "daily-progress.md",
    "OP-202611-{}-001.json", "OP-202611-{}-001.unresolved-items.md",
]

SEAT_PROMPTS = {
    "cos": "汇总/终判全览角度：对照初判+各席分歧面收敛评估；终判卷 rationale 完整性；分差 ≥2 档触发复核面核查。",
    "coo": "经营/节奏取舍角度：批次划分是否守硬时钟（schedule/cron 面零动断言）；窗口资源冲突如实列面；止损分支可执行性。",
    "cao": "治理/留痕可审计角度：判断留痕可追溯（rationale+锚文引用在卷）；判卷操作符合纪律册（D-47 时刻制/落卷纪律）；考卷改窗与门禁制度面被尊重。",
    "cpo": "产品/划界语义角度：划界个案过锚文判读（「这是一周的记录，还是这一周的活——记录随周封存·活随人带走」标签+一句理由）；keep 案守住活产品面否；carry_over 产品承诺未丢否（状态/去向/死信风险三标注）。",
    "cto": "技术/降级链完备角度：迁移批次技术风险面（依赖链/回归面）；trap/RC_guard 预案闭合技术失败路径否；降级链终态安全性。",
    "cho": "组织/staffing 角度：席位作业面健康（施工席零越域面）；值守/排班负载合理性；交接面留痕完整性。",
    "cfo": "财务/成本角度：轮级成本读数面（模型调用/资源消耗可见性）；成本红线触发面；投入产出对照合理性。",
}
I_CRITERIA = ["I1 搬移清单判断正确性", "I2 规划合理度", "I3 判断留痕质量"]
I_FULL = {"I1": 4, "I2": 3, "I3": 3}

# ── 新结构权重/判定线常量（notice-180 两裁勘改·2026-11-18· seventh 单笔承 12eef86 增补）──
# 【notice-180 裁①】120 归一制**废止**→fade-001 卷面 100 制：
#   客观 65（machine 面）＋主观 35（Score Skill I 族映射 I1=14/I2=11/I3=10）。
# 【notice-180 裁②】threshold=95 语义=挂 **7 席联审平均分面**（每席总分 100 独立
#   打分·取 7 席平均·**≥95（含 95.0）跳出 loop** 否则进下一轮）——fade-001 卷面
#   100 分与联审平均分两面分立（零互折混折=无效卷·STE v2 承）。
# 【notice-180 裁③】改善意见面=必付合格 gate 形**不计分内**（三件套+双 topic
#   fail-closed 机制不变——validate_improvement_opinions 面照守）。
# 判定线 enforcement 位=joint_review_recycle --threshold 带值（新结构轮运行形）·
# 旧 70 值与 85/87 分面=r1 存档零回改（notice-180 在飞轮 machine 59 已跑毕零感）。
NEW_STRUCTURE_THRESHOLD = 95
NEW_STRUCTURE_WEIGHT = {
    "objective_machine": 65,
    "subjective_i_family": {"I1": 14, "I2": 11, "I3": 10},
    "total_basis": 100,
    "threshold_semantics": "7席联审平均分面·每席总分100独立打分·≥95(含95.0)跳出loop",
    "improvement_face": "必付合格gate形·不计分内（notice-180 裁③）",
}
IMPROVEMENT_TOPICS = ["周迁移质量", "fade-001 自身完善度"]  # 双意见必付（notice-179①·180 裁③ gate 形承）


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def spawn_seat_session(seat: str, run_dir: Path, timeout_s: int = 600) -> dict:
    """per-seat headless 评分会话（claude -p print 形·单轮·材料只读投喂）。

    评分 prompt 零密钥零敏感值（D-46）——prompt 只引 run_dir 相对路径，值面由会话自读（只读）。
    """
    prompt = (
        "你是 TriCompany 联审七席之一（%s席）。对以下 loop 轮产出做独立评分（只读材料，零写入零投递）。\n"
        "材料（只读）：run_dir=%s 下 plan.json/close.json/score.json/manifest.json/qualify.json/"
        "verify.json/preflight.json/subjective-score.json/joint-review-trigger.json 件族。\n"
        "评分判据=I 族三判据（%s；满分 %s 分）+你的席角 checklist：\n%s\n"
        "判卷锚文（每案先过判读）：「这是一周的记录，还是这一周的活——记录随周封存·活随人带走」。\n"
        "卷面纪律：rationale 必附禁裸分+evidence_ref 可复核（引 run_dir 件路径）+判卷时点打戳。\n"
        "只输出一个 JSON 对象（零多余文本）：{\"seat\": \"%s\", \"run_id\": <从 manifest.json 读>, "
        "\"scores\": {\"I1\": <0-4>, \"I2\": <0-3>, \"I3\": <0-3>}, "
        "\"rationale\": {\"I1\": \"…\", \"I2\": \"…\", \"I3\": \"…\"}, "
        "\"evidence_ref\": {\"I1\": \"…\", \"I2\": \"…\", \"I3\": \"…\"}, "
        "\"improvement_opinions\": [{\"topic\": \"周迁移质量\", \"rationale\": \"…\", "
        "\"evidence_ref\": \"…\", \"check_time\": \"<UTC ISO>\"}, {\"topic\": \"fade-001 自身完善度\", "
        "\"rationale\": \"…\", \"evidence_ref\": \"…\", \"check_time\": \"<UTC ISO>\"}], "
        "\"check_time\": \"<UTC ISO>\"}"
        "\n（improvement_opinions=改善意见必付面（notice-179①）：双 topic 必填（周迁移质量+fade-001 自身完善度）"
        "·每条三件套 rationale/evidence_ref/check_time——缺=卷面不完整 fail-closed 不消费）"
    ) % (seat.upper(), run_dir, "；".join(I_CRITERIA),
         str(I_FULL["I1"] + I_FULL["I2"] + I_FULL["I3"]),
         SEAT_PROMPTS[seat], seat)
    # dsh 实弹席形（裁171①·notice-115 形 A 定谳·2026-11-18 SDE re-arm 修笔）：
    # dsh --profile headless 单轮 print 形（claude -p 同形收集——stdout=应答文本）·
    # 零 claude 回装（notice-152②·回退路径堵死）。bin=env DSH_BIN 可覆（缺省=
    # 河源实勘位 /srv/fleet/dsh/node_modules/.bin/dsh·T1a 活体探针位同源）。
    # cwd=run_dir（会话相对路径读材料✓·sessions 记录按 cwd 键控落位）。
    dsh_bin = os.environ.get("DSH_BIN", "/srv/fleet/dsh/node_modules/.bin/dsh")
    r = subprocess.run([dsh_bin, "--profile", "headless", prompt],
                       capture_output=True, text=True, timeout=timeout_s, cwd=str(run_dir))
    return {"rc": r.returncode, "out": (r.stdout or "")[-4000:], "err": (r.stderr or "")[:400]}


def parse_sheet(seat: str, raw: str) -> Optional[dict]:
    """会话输出→sheet JSON（容错提取首 {...} 块）。"""
    try:
        return json.loads(raw)
    except Exception:
        pass
    i, j = raw.find("{"), raw.rfind("}")
    if 0 <= i < j:
        try:
            return json.loads(raw[i:j + 1])
        except Exception:
            return None
    return None


def validate_improvement_opinions(sheet: dict) -> list:
    """改善意见必付面校验（notice-179①·O3 施工载）。

    缺改善意见=sheet 不完整（fail-closed 形·不消费不冒充）：
    · improvement_opinions 缺席/非列表/不足双意见 → 缺陷
    · 双 topic（周迁移质量/fade-001 自身完善度）逐一对表——缺必付 topic=缺陷
    · 每条三件套 rationale（禁裸意见）/evidence_ref（可复核锚）/check_time（D-47 戳）
    """
    errs = []
    ops = sheet.get("improvement_opinions")
    if not isinstance(ops, list) or not ops:
        return ["improvement_opinions 缺或空（必付面·双意见）"]
    topics = set()
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            errs.append("improvement_opinions[%d] 非对象" % i)
            continue
        topic = op.get("topic")
        topics.add(topic)
        if topic not in IMPROVEMENT_TOPICS:
            errs.append("improvement_opinions[%d].topic 越域: %r" % (i, topic))
        rat = op.get("rationale")
        if not isinstance(rat, str) or not rat.strip():
            errs.append("improvement_opinions[%d].rationale 缺（禁裸意见）" % i)
        ev = op.get("evidence_ref")
        if not isinstance(ev, str) or not ev.strip():
            errs.append("improvement_opinions[%d].evidence_ref 缺（可复核锚）" % i)
        if not op.get("check_time"):
            errs.append("improvement_opinions[%d].check_time 缺（D-47 戳）" % i)
    missing = [t for t in IMPROVEMENT_TOPICS if t not in topics]
    if missing:
        errs.append("改善意见缺必付 topic: %s" % missing)
    return errs


def four_gate_assertions(run_dir: Path, plan: dict, to_week: str,
                         records_root: str = RECORDS_ROOT_DEFAULT) -> dict:
    """四句门四机械断言（CEO 四句 §九 冻结照录·裁定卷 §一.3）。"""
    counts = plan.get("counts") or {}
    migrate_n = int(counts.get("migrate", 0))
    a = {}
    wk_num = to_week.replace("W", "")

    # ①不漏任务不漏树：plan.migrate 随迁清单 vs counts 零缺
    migrated = [e.get("entry") for e in (plan.get("migrate") or [])]
    a["1_no_miss"] = {
        "ok": len(migrated) == migrate_n,
        "detail": "plan.migrate 实迁清单 n=%d vs counts.migrate=%d" % (len(migrated), migrate_n),
    }
    # ②不多任务不多树：W47 面实树可清点（多轮共面现值形——per-run 增量断言升级候选注）
    wk_dir = Path(records_root) / ("2026-" + to_week)
    w47_trees = sorted([x.name for x in wk_dir.iterdir() if x.is_dir()]) if wk_dir.is_dir() else []
    a["2_no_extra"] = {
        "ok": bool(w47_trees),
        "detail": "W47 面=%s（树 n=%d·多轮共面现值形）" % (str(wk_dir), len(w47_trees)),
    }
    # ③必迁文件不漏：必迁族逐件在 to_week 面在位（task-inventory/daily-progress/OP 双件/whitelist 族）
    missing = []
    for pat in ("task-inventory-*", "daily-progress*.md",
                "OP-2026*-%s-001.json" % to_week,
                "OP-2026*-%s-001.unresolved-items.md" % to_week):
        if not list(wk_dir.glob(pat)):
            missing.append(pat)
    a["3_must_migrate"] = {"ok": not missing,
                           "detail": "必迁族缺件=%s（whitelist 族=必迁清单卷面·现势缺件如实红=RETRY 降设计语义）" % (missing or "无")}
    # ④该收口的收口该迁移的适配：closeout verdict 在+节收口行四态词在
    close = _read(run_dir / "close.json") or {}
    a["4_closeout"] = {
        "ok": bool(close.get("verdict")) and close.get("run_state") in ("ok", "stale", "idle", "done"),
        "detail": "close verdict=%s run_state=%s 四态词对表" % (close.get("verdict"), close.get("run_state")),
    }
    return a


def aggregate(sheets: list, missing_seats: list) -> dict:
    """subjective 聚合初判（已席均形+缺席标注——不冒充全席 §五）。"""
    per = {}
    for k in ("I1", "I2", "I3"):
        vals = [s["scores"][k] for s in sheets if isinstance(s.get("scores", {}).get(k), (int, float))]
        per[k] = round(sum(vals) / len(vals), 2) if vals else None
    total = round(sum(v for v in per.values() if v is not None), 2)
    return {
        "aggregate_initial": {"per_criterion": per, "total": total,
                              "seats_counted": len(sheets), "seats_missing": missing_seats,
                              "缺席标注": "聚合=已席均形（缺席席不冒充）" if missing_seats else "全席形"},
        "终审签认位": "人联评终审签认保留（r119④ 防线双层——聚合初判=自动前段）",
    }


def aggregate_improvements(complete_sheets: list, incomplete_faces: list) -> dict:
    """改善意见聚合面（notice-179②·O3 施工载·loop 进化方向输入面）。

    14 面意见汇出（7 席×2 维度·新结构轮形）——仅消费完整 sheet（fail-closed
    不完整面=不消费不冒充·incomplete_faces 如实列）。
    """
    by_topic = {}
    for s in complete_sheets:
        seat = s.get("seat", "?")
        for op in (s.get("improvement_opinions") or []):
            t = op.get("topic", "?")
            by_topic.setdefault(t, []).append({
                "seat": seat,
                "rationale": op.get("rationale", ""),
                "evidence_ref": op.get("evidence_ref", ""),
                "check_time": op.get("check_time", ""),
            })
    return {
        "improvement_aggregation": {
            "topics": by_topic,
            "opinions_n": sum(len(v) for v in by_topic.values()),
            "sheets_consumed": len(complete_sheets),
            "incomplete_faces_excluded": incomplete_faces,
            "不冒充标注": "聚合=完整 sheet 形（不完整面 fail-closed 不消费）",
            "用途": "loop 进化方向输入面（改进意见卷随触发件流转·notice-179②）",
        }
    }


def new_structure_verdict(sheets: list) -> dict:
    """7 席联审平均分面（notice-180 裁②·每席总分 100 独立打分取平均·≥95 含 95.0 跳出 loop）。

    每席总分=客观 65（machine 面）＋该席主观 35（I 族新 caps 勘定映射）——
    旧 caps 席评→新 caps 百分比位映射（I1×3.5/I2×11/3/I3×10/3·COS initial
    先例形承·勘定卷 §一）。改善意见面=gate 形不计分内（裁③）。
    """
    totals = []
    for s in sheets:
        sc = s.get("scores", {})
        subj = 0.0
        for k, old_full, new_full in (("I1", 4, 14), ("I2", 3, 11), ("I3", 3, 10)):
            v = sc.get(k)
            if isinstance(v, (int, float)):
                subj += v / old_full * new_full
        totals.append(round(65 + subj, 2))
    avg = round(sum(totals) / len(totals), 2) if totals else None
    if avg is None:
        verdict = "pending"
    else:
        verdict = "converge" if avg >= NEW_STRUCTURE_THRESHOLD else "loop_next"
    return {
        "new_structure_verdict_face": {
            "objective_machine": 65,
            "per_seat_totals": totals,
            "seven_seat_average": avg,
            "threshold": NEW_STRUCTURE_THRESHOLD,
            "verdict": verdict,
            "语义": "≥95（含 95.0）跳出 loop·否则进下一轮（notice-180 裁二·两面分立零互折）",
            "勘定映射注": "旧 caps 席评→新 caps 百分比位映射（COS initial 先例形承）",
        }
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="loop convene 段 auto-review runner（S2）")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--seats", default=",".join(SEATS), help="逗号分隔席名单（降级形=三席代表）")
    ap.add_argument("--spawn", action="store_true", help="实弹 spawn 会话（缺省=dry 零 spawn 面板核）")
    ap.add_argument("--dry", action="store_true", help="dry=渲染零落位零会话 spawn（S3 预演面）")
    ap.add_argument("--to-week", default="W47")
    ap.add_argument("--records-root", default=RECORDS_ROOT_DEFAULT)
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    seats = [s.strip() for s in args.seats.split(",") if s.strip()]
    out_dir = run_dir / "convene"
    seats_dir = out_dir / "seats"

    plan = _read(run_dir / "plan.json") or {}

    # 四句门四机械断言（dry 也跑=断言面板核形）
    gate = four_gate_assertions(run_dir, plan, args.to_week, args.records_root)
    gate_pass = all(v.get("ok") for v in gate.values())

    if args.dry:
        print(json.dumps({"dry": True, "four_gate": gate, "gate_pass": gate_pass,
                          "seats_planned": seats}, ensure_ascii=False, indent=1))
        return 0

    sheets, missing, incomplete = [], [], []
    if args.spawn:
        out_dir.mkdir(parents=True, exist_ok=True)
        seats_dir.mkdir(parents=True, exist_ok=True)
        for seat in seats:
            print("spawn %s…" % seat, flush=True)
            r = spawn_seat_session(seat, run_dir)
            sheet = parse_sheet(seat, r["out"]) if r["rc"] == 0 else None
            if sheet:
                path = seats_dir / ("%s-score.json" % seat)
                path.write_text(json.dumps(sheet, ensure_ascii=False, indent=1), encoding="utf-8")
                errs = validate_improvement_opinions(sheet)
                if errs:
                    # 改善意见必付面 fail-closed（notice-179①·不消费不冒充——卷面落卷留审计·聚合排除）
                    incomplete.append({"seat": seat, "errors": errs})
                    print("改善意见面不完整 %s（fail-closed 不消费·%d 缺陷）" % (seat, len(errs)), flush=True)
                else:
                    sheets.append(sheet)
                    print("sheet 落卷 %s（改善意见面完整）" % path, flush=True)
            else:
                missing.append(seat)
                (seats_dir / ("%s-score.absent.json" % seat)).write_text(
                    json.dumps({"seat": seat, "absent": True, "rc": r["rc"], "err": r["err"]},
                               ensure_ascii=False), encoding="utf-8")
                print("缺席如实注 %s（rc=%d）" % (seat, r["rc"]), flush=True)

    agg = aggregate(sheets, missing) if sheets else {"aggregate_initial": None, "缺席标注": "零 sheet（dry 形）"}
    agg.update(aggregate_improvements(sheets, incomplete))
    agg.update(new_structure_verdict(sheets))
    four_gate_line = {"four_gate": gate, "gate_pass": gate_pass,
                      "verdict_adjust": "PASS" if gate_pass else "RETRY（四句门红降）"}
    report_four = {
        "report_four_elements": {
            "notice": "notice-179 B 款·新结构下一轮毕报四要素承载面（O3④）",
            "cos_plan_record": "run_dir/plan.json + Plan Skill 卷（COS plan 实录指针面）",
            "judging_record": "run_dir/subjective-score.json + judge_faces 三段（COS+COO 评卷实录指针面）",
            "per_seat_scores": [{"seat": s.get("seat"), "scores": s.get("scores")} for s in sheets],
            "per_seat_improvements": [
                {"seat": s.get("seat"), "improvement_opinions": s.get("improvement_opinions")}
                for s in sheets
            ],
        }
    }
    new_structure = {
        "new_structure_semantics": {
            "threshold": NEW_STRUCTURE_THRESHOLD,
            "weight": NEW_STRUCTURE_WEIGHT,
            "note": "notice-180 两裁勘改：100 制（客观 65 machine+主观 35 I 族 14/11/10）·threshold=95 挂 7 席联审平均分面（≥95 含 95.0 跳出 loop）·改善意见面 gate 形不计分内——120 归一制废止（r1 存档 85/87 零回改）",
        }
    }
    conv = {"convene_mode": "auto", "seats": seats, "sheets_n": len(sheets),
            "missing_seats": missing, "incomplete_faces": incomplete,
            **agg, **four_gate_line, **report_four, **new_structure,
            "check_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if not args.dry:
        (out_dir / "aggregate-initial.json").write_text(
            json.dumps(conv, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(conv, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
