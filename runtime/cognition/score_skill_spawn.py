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
import re as _re
import os
import subprocess
import sys
from pathlib import Path

# 2026-11-22 勘正批（CTO 勘定卷 43a6dfa08·CEO 勘正方向）：评分段回两席=默认正形
# （评分=cos/coo 两席·七席归联审段 future 批）。P2 七席保留为 env 可切（联审段用·非删）。
_DEFAULT_SEATS = ("cos", "coo")
SEATS = tuple(s.strip() for s in os.environ.get(
    "SCORE_SKILL_SEATS", ",".join(_DEFAULT_SEATS)).split(",") if s.strip())
_DSHPROMPT_HEAD = (
    "你是 TriCompany score skill 评主观分席之一（%s席）。对以下 loop 轮产出评 I 族主观分"
    "（只读材料，零写入零投递）。评分判据=I 族三判据（I1 搬移清单判断正确性满分14/"
    "I2 规划合理度满分11/I3 判断留痕质量满分10·notice-180 65/35 制）＋你的席角 checklist。\n"
    "评分对象域界定（notice-187）：对象域=本 run_dir 事务域件族——管理面施工树排除·"
    "evidence_ref 指 run_dir 外=无效卷。\n"
    "卷面纪律：rationale 必附禁裸分＋evidence_ref（引 run_dir 件路径）＋check_time。\n"
    "输出纪律（DP-042-A 修·DP-048 勘正·必守）：①**直接输出最终 JSON**·reasoning 保持精简（≤10 行）·禁长篇推演；若需思考，在 reasoning 内简短定稿即输出"
    "（b）**若 reasoning 超过 10 步仍未定稿，直接以现有结论输出 JSON（不得继续推演）**——"
    "resume17 实锚：长时间推演吃满输出预算致零输出（先推演=反作用）；"
    "②rationale 每项≤30 字·每条 improvement 的 change/verify/rollback 各≤120 字；"
    "③「scores」键必须出现在「improvements」之前（salvage 可取的保证）；"
    "④improvements 每席≤3 条；⑤临近输出上限时保 scores 与 improvements 五必填字段（title/target/change/verify/rollback）·可截短 rationale。\n"
    "只输出一个 JSON 对象（零多余文本）：{\"seat\": \"%s\", "
    "\"scores\": {\"I1\": <0-14>, \"I2\": <0-11>, \"I3\": <0-10>}, "
    "\"improvements\": [{\"title\": \"…\", \"target\": \"<run-dir 内路径>\", \"change\": \"…\", \"verify\": \"…\", \"rollback\": \"…\"}], "
    "\"rationale\": {\"I1\": \"…\", \"I2\": \"…\", \"I3\": \"…\"}, "
    "\"subjective_score\": {\"criterion\": [{\"id\": \"I1\", \"score\": <0-4>, \"rationale\": \"非空≤30 字\"}, {\"id\": \"I2\", \"score\": <0-3>, \"rationale\": \"非空\"}, {\"id\": \"I3\", \"score\": <0-3>, \"rationale\": \"非空\"}]}, "
    "（subjective_score=v3 卷形·COS f374595f9：I1≤4/I2≤3/I3≤3 总 10·**judge 不预换算权重**·rationale 非空·**无 evidence_ref**·落 <run_dir>/subjective-score.json）"
    "【wrong_order 判读（CEO 架构令 2026-11-25·A5·段 7 智能段）】输入=run_dir/dce.json 的 execution_diff.wrong_order 清单+条目族信息+文件落位（及本 prompt 末尾附的**上轮 rulings 上下文**）——请**判「要不要紧」**：封存类（W47 记录树·顺序不敏感）**不扣**；施工面顺序错**扣分或判 fail 依据**——输出给 G 族评分依据（rationale 注明哪条要紧/不要紧）。"
    "\"evidence_ref\": {\"I1\": \"…\", \"I2\": \"…\", \"I3\": \"…\"}, "
    "\"check_time\": \"<UTC ISO>\"}"
    "（improvements=可选·建议给至少一条改进建议·缺=合规范本；有则每项五字段齐·禁缺字段）"
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
    """DP-033 cfo-1: cost-log related fields auto-fill.

    Adds run_id/trigger/task_id/seat_count/cost_channel. Call sites untouched:
    env/run_dir derivation as fallback, explicit rec values win (meta.update).
    run_id+task_id make cost-log rows joinable with session-level transcript
    readout (CFO cfo-token-meter.py) by time window / run id.
    """
    import datetime as _dt
    import os as _os
    _trig = str(_os.environ.get("FADE_TRIGGER", "")).lower()
    if _trig in ("auto", "manual"):
        _trigger = _trig
    else:
        _autod = str(_os.environ.get("FADE_AUTO_DISPATCH", "")).lower() in ("1", "true", "yes")
        _trigger = "auto" if _autod else "manual"
    _task = _os.environ.get("FADE_TASK_ID", "").strip()
    if not _task:
        _mf = run_dir / "manifest.json"
        if _mf.is_file():
            try:
                _task = str((_json.loads(_mf.read_text(encoding="utf-8")) or {}).get("task_id") or "")
            except Exception:
                _task = ""
    _runid = _os.environ.get("FADE_RUN_ID", "").strip() or run_dir.name
    meta = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "run_id": _runid,
        "trigger": _trigger,
        "task_id": _task or _runid,
        "seat_count": len(rec.get("seats") or []),
        "cost_channel": "ok" if _os.environ.get("DEEPSEEK_API_KEY") else "unavailable",
    }
    meta.update(rec)
    rec = meta
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


# ── P5 100 制派生（CTO §五·CEO 令⑥⑧）：每席 100 分制=现行 I 读数加权百分比化 ──
# 权重 14:11:10（满分 35）→ 100 制映射：I1×40/14 + I2×31.43/11 + I3×28.57/10（和=100）。
# 注（CTO 附注一 2026-11-21）：这组权重=**现役 I 族满分刻度（35 分母）归一化·非新权重决策**
# （14/35=40%·11/35=31.43%·10/35=28.57%）——防将来误读为权重变更。
_W_I1, _W_I2, _W_I3 = 100 * 14 / 35, 100 * 11 / 35, 100 * 10 / 35


def _seat_total_100(scores) -> float | None:
    """派生每席 100 制总分（LLM 不直接打 100 制·派生计算=格式稳）。"""
    try:
        return round(float(scores["I1"]) / 14 * _W_I1
                     + float(scores["I2"]) / 11 * _W_I2
                     + float(scores["I3"]) / 10 * _W_I3, 2)
    except Exception:
        return None


def _append_trend(run_dir: Path, run_id: str, seat_totals: dict) -> None:
    """P5 趋势线（CEO 令⑧可观测提升）：每轮每席 total_100 追加 trend.jsonl。"""
    import datetime as _dt
    rec = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(), "run_id": run_id,
           "seats": seat_totals}
    with (run_dir / "trend.jsonl").open("a", encoding="utf-8") as f:
        f.write(_json.dumps(rec, ensure_ascii=False) + "\n")


def _trend_rising(run_dir: Path, window: int = 8) -> dict:
    """P5 趋势判据（CTO §五）：debug 态 8 轮窗口滑动均值单调上升判定（读数形·零强制）。"""
    p = run_dir / "trend.jsonl"
    if not p.is_file():
        return {"available": False}
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(_json.loads(line))
        except Exception:
            continue
    if len(rows) < 2:
        return {"available": True, "rounds": len(rows), "rising": None}
    means = []
    for r in rows[-window:]:
        vals = [v for v in (r.get("seats") or {}).values() if isinstance(v, (int, float))]
        if vals:
            means.append(sum(vals) / len(vals))
    rising = all(b >= a for a, b in zip(means, means[1:])) if len(means) >= 2 else None
    return {"available": True, "rounds": len(rows), "window_means": [round(m, 2) for m in means],
            "rising": rising}


def _wrong_order_context(run_dir: Path) -> str:
    """A3（CEO 架构令）：wrong_order 上下文入段 7 prompt——本 run 清单 + 上轮 rulings（继承降级为上下文输入）。"""
    lines: list[str] = []
    try:
        dce = _json.loads((run_dir / "dce.json").read_text(encoding="utf-8"))
        wo = ((dce.get("execution_diff") or {}).get("wrong_order") or []) if isinstance(dce, dict) else []
        if wo:
            names = [(x.get("wrong_order_item") or x.get("item")) if isinstance(x, dict) else x for x in wo]
            lines.append(f"【wrong_order 清单（本 run）】{names}")
    except Exception:
        pass
    try:
        parent = run_dir.parent
        prevs = [d for d in parent.iterdir()
                 if d.is_dir() and d.resolve() != run_dir.resolve() and (d / "dce.json").is_file()]
        if prevs:
            prevs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            pd = _json.loads((prevs[0] / "dce.json").read_text(encoding="utf-8"))
            rulings = pd.get("wrong_order_rulings") or []
            if rulings:
                lines.append(f"【上轮 rulings 上下文（{prevs[0].name}）】{_json.dumps(rulings[:8], ensure_ascii=False)}")
    except Exception:
        pass
    return (chr(10) + chr(10).join(lines)) if lines else ""


def _spawn_seat(seat: str, run_dir: Path, timeout_s: int = 900) -> dict:
    """单席 headless spawn（loop_autoreview 基建同源承——--patch/F4 上限/raw_out）。"""
    prompt = (_opinions_prefix(run_dir) + _DSHPROMPT_HEAD % (seat.upper(), seat)
              + _wrong_order_context(run_dir))
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
    # ── B 件 parse 加固（CEO 批 A+B 热修·CTO 详规 2026-11-24）：四步新形 ──
    # 1) 全串 parse（现形保留）
    try:
        return {"rc": rc, "sheet": _json.loads(out), "raw_out": out, "err": err}
    except Exception:
        pass
    # 2) 尾部反向配平：从最后一个 '}' 反向扫栈找配平起点→尝试 parse（能配平=正常 sheet）
    end = out.rfind("}")
    if end != -1:
        depth = 0
        start = -1
        for i in range(end, -1, -1):
            ch = out[i]
            if ch == "}":
                depth += 1
            elif ch == "{":
                depth -= 1
                if depth == 0:
                    start = i
                    break
        if start != -1:
            try:
                _cand = _json.loads(out[start:end + 1])
                # 配平产物须是意见卷形（含 scores/improvements/seat 键）——防内层 fragments 误当整卷
                if isinstance(_cand, dict) and any(
                        k in _cand for k in ("scores", "improvements", "seat")):
                    return {"rc": rc, "sheet": _cand, "raw_out": out, "err": err}
            except Exception:
                pass
    # 3) salvage：head 内完整 "scores":{...} 块 → 降级取 scores（partial=true·improvements 缺告警）
    m = _re.search(r'"scores"\s*:\s*\{[^{}]*\}', out)
    if m:
        try:
            scores = _json.loads("{" + m.group(0) + "}")["scores"]
            if isinstance(scores, dict) and scores:
                print(f"[score-skill][WARN] {seat} 输出截断——scores salvage 降级（improvements 缺·partial=true）",
                      file=sys.stderr)
                return {"rc": rc, "partial": True, "truncated": True, "scores": scores,
                        "raw_out": out, "err": "improvements 截断（scores salvage）"}
        except Exception:
            pass
    # 4) 显式 fail-loud：truncated_output 错类（不再静默判缺）
    return {"rc": rc, "absent": False, "truncated": True, "err_class": "truncated_output",
            "raw_out": out[-2000:], "err": err or "parse failed（截断/坏形·fail-loud）"}


def _backfill_score_subjective(run_dir: Path, run_id: str) -> dict | None:
    """r34 时序修（CTO 令 2026-11-25）：段 7 产 subjective-score.json 后，回头重算 score 的 I 族——
    score.json 的 family I 若 partial/manual(null)→读卷按权重补算（raw 总/10×weight），更新
    score.json（families I / domain_breakdown.subjective / total_score / pending / projection / run_state）。
    返回 {score, weight, total} 或 None（无可补面）。"""
    sp = run_dir / "score.json"
    vp = run_dir / "subjective-score.json"
    if not (sp.is_file() and vp.is_file()):
        return None
    try:
        top = _json.loads(sp.read_text(encoding="utf-8"))
        vol = _json.loads(vp.read_text(encoding="utf-8"))
    except Exception:
        return None
    eng = top.get("score") if isinstance(top.get("score"), dict) else None
    if not isinstance(eng, dict):
        return None
    fams = eng.get("families") or []
    fi = next((f for f in fams if isinstance(f, dict) and f.get("family_id") == "I"), None)
    if fi is None or fi.get("score") is not None:
        return None      # 已计分或该族不在卷=无可补
    raw = 0.0
    for e in (vol.get("entries") or []):
        if isinstance(e, dict):
            try:
                raw += float(e.get("score") or 0)
            except (TypeError, ValueError):
                continue
    raw = min(raw, 10.0)                     # 卷面 10 分制（COS 形 I1≤4/I2≤3/I3≤3）
    w = float(fi.get("weight") or 35)
    val = round(raw / 10.0 * w, 1)
    fi["state"] = "subjective"
    fi["score"] = val
    fi.setdefault("reasons", []).append(f"r34 时序补算：subjective-score 卷（raw={raw}/10×{int(w)}={val}）")
    # S6c（CTO 令）：禁冒充——补算判语必须显式标 auto
    _jf = eng.setdefault("judge_faces", {})
    _jf["subjective"] = "auto-backfill"
    _db = eng.setdefault("domain_breakdown", {})
    _db["subjective"] = float(_db.get("subjective") or 0) + val
    eng["total_score"] = float(eng.get("total_score") or 0) + val
    _pw = float(eng.get("total_pending_weight") or 0)
    eng["total_pending_weight"] = max(_pw - w, 0)
    eng["total_projection"] = float(eng["total_score"]) + float(eng["total_pending_weight"])
    caps = eng.get("redline_caps_applied") or []
    if caps:
        try:
            _cap = min(float(c.get("cap")) for c in caps if isinstance(c, dict) and c.get("cap") is not None)
            if eng["total_score"] > _cap:
                eng["total_score"] = _cap
        except Exception:
            pass
    if not any(isinstance(f, dict) and f.get("state") == "partial" for f in fams):
        eng["run_state"] = "succeeded"
    sp.write_text(_json.dumps(top, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    return {"score": val, "weight": w, "total": eng["total_score"]}


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
        if r.get("sheet") and isinstance(r["sheet"].get("scores"), dict):
            faces[seat] = r["sheet"]
        elif r.get("partial") and isinstance(r.get("scores"), dict):
            # B 件 salvage 支：判级面可用 scores·但 partial/truncated 明标（flag 不洗白）
            faces[seat] = {"scores": r["scores"], "partial": True, "truncated": True,
                           "rc": r.get("rc")}
        else:
            faces[seat] = {"absent": True, "err_class": r.get("err_class"),
                           "rc": r.get("rc"), "raw_out": r.get("raw_out", ""),
                           "err": r.get("err")}
    out["faces"] = faces

    # ── P5 100 制派生 + 趋势线（CEO 令⑧）──
    seat_totals = {}
    for _s, _f in faces.items():
        if isinstance(_f, dict) and not _f.get("absent"):
            _t = _seat_total_100(_f.get("scores") or {})
            if _t is not None:
                _f["total_100"] = _t
                seat_totals[_s] = _t
    if seat_totals:
        _append_trend(run_dir, args.run_id, seat_totals)
        out["trend"] = _trend_rising(run_dir)


    # ── P4 opinions.json 产出（CTO 7c389cac3 §三b·双下游共享件：a=下轮注入 本脚本消费 /
    # b=派生任务书走自动拾取链（生成器=COS/CTO 面·非本脚本·启用时点=P6 收口后））──
    try:
        ops = []
        for s, f in faces.items():
            if isinstance(f, dict) and not f.get("absent"):
                rat = f.get("rationale") or {}
                summary = " | ".join(str(rat.get(k, ""))[:120] for k in ("I1", "I2", "I3"))
                entry = {"opinion_id": f"{s}-1", "seat": s, "scores": f.get("scores"),
                         "summary": summary, "check_time": f.get("check_time")}
                # CTO 裁 A 优化形：improvements（可选）透传→生成器五字段面（title/target/change/verify/rollback）
                imps = f.get("improvements")
                if isinstance(imps, list) and imps:
                    five = [i for i in imps if isinstance(i, dict)
                            and all(isinstance(i.get(k), str) and i.get(k).strip()
                                    for k in ("title", "target", "change", "verify", "rollback"))]
                    if five:
                        entry["title"] = five[0]["title"]
                        entry["target"] = five[0]["target"]
                        entry["change"] = five[0]["change"]
                        entry["verify"] = five[0]["verify"]
                        entry["rollback"] = five[0]["rollback"]
                ops.append(entry)
        if ops:
            (run_dir / "opinions.json").write_text(
                _json.dumps({"schema_version": "2.0.0", "run_id": args.run_id,
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
        # CFO10（B4）：final_scores_basis/divergence_review/trend 口径
        "final_scores_basis": {"source": "engine+joint-review",
                               "a": None, "b": None,
                               "note": "以 score.json/joint-review 为准（本卷只记口径）"},
        "divergence_review": {"seats": len([f for f in faces.values() if isinstance(f, dict) and not f.get("absent")]),
                              "note": "七席维度分差见 joint-review"},
        "trend": {"prev_run": None, "baseline": "n/a（本次无上轮 score.json 引用）"},
        "weight_face": {"objective_machine": 65,
                        "subjective_i_family": {"I1": 14, "I2": 11, "I3": 10},
                        "total_basis": 100,
                        "anchor": "notice-180 裁①"},
        "check_time": args.check_time or "",
    }
    # I 族判卷卷链内化（CTO 令 2026-11-25·①a 主修）：聚合七席 subjective_score → 落 subjective-score.json
    try:
        _crit: dict = {}
        for _s, _f in faces.items():
            if not isinstance(_f, dict) or _f.get("absent"):
                continue
            _sub = _f.get("subjective_score")
            if not isinstance(_sub, dict):
                continue
            for c in (_sub.get("criterion") or []):
                if not isinstance(c, dict):
                    continue
                _id = str(c.get("id") or "")
                if _id not in ("I1", "I2", "I3"):
                    continue
                try:
                    _sc = float(c.get("score"))
                except (TypeError, ValueError):
                    continue
                _rat = str(c.get("rationale") or "").strip()
                if not _rat:
                    continue
                _crit.setdefault(_id, []).append((_sc, _rat))
        if _crit:
            import datetime as _dt
            _entries = []
            for _id in ("I1", "I2", "I3"):
                _vals = sorted(x[0] for x in _crit.get(_id, []))
                if not _vals:
                    continue
                _med = _vals[len(_vals) // 2]
                _entries.append({"criterion": _id, "score": min(max(_med, 0), 10),
                                 "rationale": f"七席中位聚合（n={len(_vals)}）"})
            if _entries:
                (run_dir / "subjective-score.json").write_text(_json.dumps({
                    "score_version": "1.0.0", "run_id": args.run_id,
                    "entries": _entries,
                    "judge_faces": {"initial": "score_skill_seats_aggregate"},
                    "check_time": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
                out["subjective_score_written"] = str(run_dir / "subjective-score.json")
    except Exception as e:  # noqa: BLE001 — 判卷卷链内化零炸段
        out["subjective_score_error"] = f"{type(e).__name__}: {e}"
    (run_dir / "score-skill.json").write_text(
        _json.dumps(skill, ensure_ascii=False, indent=1), encoding="utf-8")
    out["written"] = str(run_dir / "score-skill.json")
    # r34 时序修：卷写后回头补算 score 的 I 族（段 6 先/段 7 后也能落 35）
    try:
        _bf = _backfill_score_subjective(run_dir, args.run_id)
        if _bf:
            out["subjective_backfill"] = _bf
    except Exception as e:  # noqa: BLE001 — 补算面零阻断
        out["subjective_backfill_error"] = f"{type(e).__name__}: {e}"
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
