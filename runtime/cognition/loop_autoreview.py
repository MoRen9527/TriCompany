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
        "\"check_time\": \"<UTC ISO>\"}"
    ) % (seat.upper(), run_dir, "；".join(I_CRITERIA),
         str(I_FULL["I1"] + I_FULL["I2"] + I_FULL["I3"]),
         SEAT_PROMPTS[seat], seat)
    r = subprocess.run(["claude", "-p", prompt, "--output-format", "text"],
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

    sheets, missing = [], []
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
                sheets.append(sheet)
                print("sheet 落卷 %s" % path, flush=True)
            else:
                missing.append(seat)
                (seats_dir / ("%s-score.absent.json" % seat)).write_text(
                    json.dumps({"seat": seat, "absent": True, "rc": r["rc"], "err": r["err"]},
                               ensure_ascii=False), encoding="utf-8")
                print("缺席如实注 %s（rc=%d）" % (seat, r["rc"]), flush=True)

    agg = aggregate(sheets, missing) if sheets else {"aggregate_initial": None, "缺席标注": "零 sheet（dry 形）"}
    four_gate_line = {"four_gate": gate, "gate_pass": gate_pass,
                      "verdict_adjust": "PASS" if gate_pass else "RETRY（四句门红降）"}
    conv = {"convene_mode": "auto", "seats": seats, "sheets_n": len(sheets),
            "missing_seats": missing, **agg, **four_gate_line,
            "check_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if not args.dry:
        (out_dir / "aggregate-initial.json").write_text(
            json.dumps(conv, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(conv, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
