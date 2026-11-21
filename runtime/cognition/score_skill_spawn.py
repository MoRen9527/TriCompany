"""Score skill spawn 段（notice-207 件①·Score CLI→Skill 硬序改造·二款）。

硬序承录（notice-210 勘正对照面）：score 段=先 CLI 后 skill（本段=CLI 毕后的
skill 面·spawn COS+COO 两席评主观分 I 族三判据）——禁并行禁倒置：
  段前置硬序断言=score.json 在且 verdict 面（客观分先于主观分）——违=exit 2
  拒 spawn（替身禁令同族·不造主观分替身）。

产出：run_dir/score-skill.json（2.0.0 形·initial=COS 面＋joint=[COO 面]＋
final 候 COS 值席域）——两席 spawn 形照 loop_autoreview 基建（--patch 尾挂+
F4 上限+raw_out 存 absent·同源承）。

护栏：材料 run_dir 只读·prompt 零密钥（D-46）·spawn 败=缺席注不冒充（缺席
席=值席手工补面候·零替身）。
"""
from __future__ import annotations

import argparse
import json as _json
import os
import subprocess
import sys
from pathlib import Path

# P2 修形（2026-11-21 CEO 九点令②·CTO 定谳 7c389cac3 §二）：两席→七席。
# 形参化回滚形（CTO 定）：env SCORE_SKILL_SEATS 可切（回滚设 "cos,coo"）。
_DEFAULT_SEATS = ("cos", "coo", "cao", "cpo", "cto", "cho", "cfo")
SEATS = tuple(s.strip() for s in os.environ.get(
    "SCORE_SKILL_SEATS", ",".join(_DEFAULT_SEATS)).split(",") if s.strip())
_DSHPROMPT_HEAD = (
    "你是 TriCompany score skill 评主观分席之一（%s席）。对以下 loop 轮产出评 I 族主观分"
    "（只读材料，零写入零投递）。评分判据=I 族三判据（I1 搬移清单判断正确性满分14/"
    "I2 规划合理度满分11/I3 判断留痕质量满分10·notice-180 65/35 制）＋你的席角 checklist。\n"
    "评分对象域界定（notice-187）：对象域=本 run_dir 事务域件族——管理面施工树排除·"
    "evidence_ref 指 run_dir 外=无效卷。\n"
    "卷面纪律：rationale 必附禁裸分＋evidence_ref（引 run_dir 件路径）＋check_time。\n"
    "只输出一个 JSON 对象（零多余文本）：{\"seat\": \"%s\", "
    "\"scores\": {\"I1\": <0-14>, \"I2\": <0-11>, \"I3\": <0-10>}, "
    "\"rationale\": {\"I1\": \"…\", \"I2\": \"…\", \"I3\": \"…\"}, "
    "\"evidence_ref\": {\"I1\": \"…\", \"I2\": \"…\", \"I3\": \"…\"}, "
    "\"check_time\": \"<UTC ISO>\"}"
)


# ── CFO 成本护栏（2026-11-21 CFO 裁决①·COO 放行令四条·施工面内建）──
# ⓐ 轮级 <=1 元/轮超即查  ⓑ 8 轮封顶总 <=10 元触线报  ⓒ 余额硬下限 <20 CNY 暂停
# ⓓ 读数采集=轮级一行（余额差分形：dsh 不透传 API usage——token 三字段如实标不可得）
_DS_BALANCE_URL = "https://api.deepseek.com/user/balance"
_COST_LOG_NAME = "cost-log.jsonl"
_ROUND_CAP_CNY = 1.0
_TOTAL_CAP_CNY = 10.0
_BALANCE_FLOOR_CNY = 20.0


def _deepseek_balance_cny():
    """GET /user/balance（零 token·key 自 env）；不可得=None（如实降级不阻塞）。"""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(_DS_BALANCE_URL, headers={"authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = _json.loads(r.read().decode())
        for b in d.get("balance_infos", []):
            if b.get("currency") == "CNY":
                return float(b.get("total_balance", "0"))
    except Exception:
        return None
    return None


def _total_spent_cny(run_dir: Path) -> float:
    p = run_dir / _COST_LOG_NAME
    if not p.is_file():
        return 0.0
    tot = 0.0
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            tot += float(_json.loads(line).get("delta_cny") or 0)
        except Exception:
            continue
    return tot


def _consecutive_null_balance(run_dir: Path) -> int:
    """COO 附条（2026-11-21）：连续 null 余额轮数（含本轮·防长期静默 fail-open）。"""
    p = run_dir / _COST_LOG_NAME
    if not p.is_file():
        return 0
    n = 0
    for line in reversed(p.read_text(encoding="utf-8").splitlines()):
        try:
            rec = _json.loads(line)
        except Exception:
            break
        if rec.get("balance_before_cny") is None:
            n += 1
        else:
            break
    return n


def _write_cost_line(run_dir: Path, rec: dict) -> None:
    import datetime as _dt
    rec = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(), **rec}
    with (run_dir / _COST_LOG_NAME).open("a", encoding="utf-8") as f:
        f.write(_json.dumps(rec, ensure_ascii=False) + "\n")


def _opinions_prefix(run_dir: Path) -> str:
    """P4 opinions 注入（a 出口·CEO 令⑦·CTO 7c389cac3 §三b）：上轮联审意见带入本轮 spawn context。"""
    p = run_dir / "opinions.json"
    if not p.is_file():
        return ""
    try:
        d = _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return ""
    ops = d.get("opinions") or []
    if not ops:
        return ""
    lines = ["【上轮联审意见（P4·请结合改进本轮评分）】"]
    for o in ops[:12]:
        lines.append(f"- {o.get('seat','?')}席: {str(o.get('summary',''))[:200]}")
    return "\n".join(lines) + "\n\n"


def _spawn_seat(seat: str, run_dir: Path, timeout_s: int = 900) -> dict:
    """单席 headless spawn（loop_autoreview 基建同源承——--patch/F4 上限/raw_out）。"""
    prompt = _opinions_prefix(run_dir) + _DSHPROMPT_HEAD % (seat.upper(), seat)
    dsh_bin = os.environ.get("DSH_BIN", "/srv/fleet/dsh/node_modules/.bin/dsh")
    overlay = os.environ.get(
        "DSH_PRESET_OVERLAY", "/home/fleet/.dsh/patches/headless-agentpresets-overlay.yml")
    cmd = [dsh_bin, "--profile", "headless"]
    if overlay and os.path.isfile(overlay):
        cmd += ["--patch", overlay]
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout_s, cwd=str(run_dir))
        out = (r.stdout or "")[-60000:]  # F4 上限承
        rc = r.returncode
        err = (r.stderr or "")[:400]
    except subprocess.TimeoutExpired:
        return {"rc": -1, "out": "", "err": f"spawn timeout {timeout_s}s"}
    sheet = None
    try:
        sheet = _json.loads(out)
    except Exception:
        i, j = out.find("{"), out.rfind("}")
        if 0 <= i < j:
            try:
                sheet = _json.loads(out[i:j + 1])
            except Exception:
                sheet = None
    return {"rc": rc, "sheet": sheet, "raw_out": out, "err": err}


def run(args: argparse.Namespace) -> tuple[int, dict]:
    run_dir = Path(args.run_dir).resolve()
    out: dict = {"score_skill_spawn_version": "1.0.0",
                 "run_id": args.run_id, "seats": list(SEATS), "faces": {}}

    # 硬序断言（禁并行禁倒置·替身禁令同族）：score.json 客观分面先在
    score_path = run_dir / "score.json"
    if not score_path.is_file():
        out["hard_order_gate"] = {"ok": False,
                                  "reason": "score.json 缺（客观分未落·禁主观分 spawn——硬序拒）"}
        return 2, out
    try:
        score = _json.loads(score_path.read_text(encoding="utf-8"))
        sv = score.get("verdict")
    except Exception as e:  # noqa: BLE001
        out["hard_order_gate"] = {"ok": False,
                                  "reason": f"score.json unparsable: {e}（硬序拒）"}
        return 2, out
    out["hard_order_gate"] = {"ok": True, "score_verdict": sv,
                              "note": "客观分先于主观分（score CLI 毕→score skill spawn·硬序闭合）"}

    # ── CFO 护栏 ⓒ 余额门 / ⓑ 总累计门（spawn 前）──
    import datetime as _dt
    t0 = _dt.datetime.now(_dt.timezone.utc)
    b0 = _deepseek_balance_cny()
    if b0 is not None and b0 < _BALANCE_FLOOR_CNY:
        out["cost_guard"] = {"paused": True, "balance_cny": b0,
                             "reason": "balance < %.0f CNY floor (CFO guard c)" % _BALANCE_FLOOR_CNY}
        return 3, out
    spent = _total_spent_cny(run_dir)
    if spent >= _TOTAL_CAP_CNY:
        out["cost_guard"] = {"paused": True, "total_cny": spent,
                             "reason": "accumulated spend >= %.0f CNY cap (CFO guard b)" % _TOTAL_CAP_CNY}
        return 3, out

    faces = {}
    for seat in SEATS:
        r = _spawn_seat(seat, run_dir, timeout_s=args.spawn_timeout)
        if r["sheet"] and isinstance(r["sheet"].get("scores"), dict):
            faces[seat] = r["sheet"]
        else:
            faces[seat] = {"absent": True, "rc": r["rc"],
                           "raw_out": r["raw_out"][-60000:], "err": r["err"]}
    out["faces"] = faces

    # ── P4 opinions.json 产出（CTO 7c389cac3 §三b·双下游共享件：a=下轮注入 本脚本消费 /
    # b=派生任务书走自动拾取链（生成器=COS/CTO 面·非本脚本·启用时点=P6 收口后））──
    try:
        ops = []
        for s, f in faces.items():
            if isinstance(f, dict) and not f.get("absent"):
                rat = f.get("rationale") or {}
                summary = " | ".join(str(rat.get(k, ""))[:120] for k in ("I1", "I2", "I3"))
                ops.append({"seat": s, "scores": f.get("scores"), "summary": summary,
                            "check_time": f.get("check_time")})
        if ops:
            (run_dir / "opinions.json").write_text(
                _json.dumps({"schema_version": "1.0.0", "run_id": args.run_id,
                             "opinions": ops}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
    except Exception as e:  # opinions 产出 best-effort（不阻主观分主链）
        out["opinions_warn"] = str(e)

    # ── CFO 护栏 ⓓ 轮级读数行 + ⓐ 轮级成本告警 ──
    t1 = _dt.datetime.now(_dt.timezone.utc)
    b1 = _deepseek_balance_cny()
    delta = (b0 - b1) if (b0 is not None and b1 is not None) else None
    _write_cost_line(run_dir, {
        "seats": list(SEATS), "seat_count": len(SEATS),
        "started": t0.isoformat(), "finished": t1.isoformat(),
        "duration_s": round((t1 - t0).total_seconds(), 1),
        "balance_before_cny": b0, "balance_after_cny": b1, "delta_cny": delta,
        "delta_scope": "period_total_all_ds_consumption (CFO note: upper-bound only, NOT pure review cost)",
        "token_fields": "unavailable: dsh headless does not project API usage",
    })
    if _consecutive_null_balance(run_dir) >= 3:
        _msg = ("[cost-guard][ESCALATE CFO+COO] balance unavailable for >=3 consecutive rounds - "
                "fail-open persisted (investigate DEEPSEEK_API_KEY/env in spawn face)")
        out["cost_guard_warning_balance"] = _msg
        print(_msg, file=sys.stderr)
    if delta is not None and delta > _ROUND_CAP_CNY:
        out["cost_guard_warning"] = ("round cost %.2f CNY > %.1f cap - investigate "
                                     "seat-count/material anomaly (CFO guard a)" % (delta, _ROUND_CAP_CNY))

    # score-skill.json 组装（initial=COS＋joint=[COO]·final 候 COS 值席域）
    skill = {
        "score_version": "2.0.0-ns6",
        "run_id": args.run_id,
        "stage_face": "score-skill",
        "spawn_form": "notice-207 件①程序化 spawn（硬序承·禁并行禁倒置）",
        "entries": [],
        "judge_faces": {
            "initial": faces.get("cos", {"absent": True}),
            "joint": [faces.get("coo", {"absent": True})],
            "final": "候 COS 值席域（final_scores_basis/divergence_review 面值席工序）",
        },
        "weight_face": {"objective_machine": 65,
                        "subjective_i_family": {"I1": 14, "I2": 11, "I3": 10},
                        "total_basis": 100,
                        "anchor": "notice-180 裁①"},
        "check_time": args.check_time or "",
    }
    (run_dir / "score-skill.json").write_text(
        _json.dumps(skill, ensure_ascii=False, indent=1), encoding="utf-8")
    out["written"] = str(run_dir / "score-skill.json")
    absent = [s for s in SEATS if faces[s].get("absent")]
    out["absent_seats"] = absent
    return (2 if len(absent) == len(SEATS) else 0), out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Score skill spawn 段（notice-207 件①硬序形）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", default="")
    p.add_argument("--spawn-timeout", type=int, default=900)
    p.add_argument("--check-time", default=None, help="payload 传入时点（缺省空）")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code, out = run(args)
    print(_json.dumps(out, ensure_ascii=False, indent=1)[:4000])
    return code


if __name__ == "__main__":
    sys.exit(main())
