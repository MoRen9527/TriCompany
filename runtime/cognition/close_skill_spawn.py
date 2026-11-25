"""Close skill spawn 段（P3·段 8 close_skill 的 spawn cos 化形·CTO 定谳 7c389cac3 §一·2026-11-21）。

形照 score_skill_spawn.py 模板：单席（cos）dsh headless spawn + overlay 同源 + F4 上限 +
absent 存 raw_out。**灰度形**：与 CLI 形 close_skill.py 并存——chain_runner 侧
env FADE_CLOSE_SPAWN=1 切换（回滚=去 flag 即回 CLI 形）。

产物：run_dir/close.json——spawn 败=exit 2 拒产替身（fail-closed）。

rc 语义表（CTO 附条一·2026-11-21）：
  0=pass（产物落卷）·2=spawn absent/schema invalid（零替身）·
  3=cost-guard 暂停（CFO 护栏 b/c）·-2=单席 spawn 不可执行（dsh 缺失/OSError·与 rc=2 全 absent 区分）。

CFO 护栏四件同 P2 形（余额门/累计门/轮级读数行/告警+null 三连升级）。
"""
from __future__ import annotations

import argparse
import json as _json
import os
import subprocess
import sys
from pathlib import Path

_DEFAULT_SEATS = ("cos",)
SEATS = tuple(s.strip() for s in os.environ.get(
    "CLOSE_SKILL_SEATS", ",".join(_DEFAULT_SEATS)).split(",") if s.strip())

_CLOSE_PROMPT_HEAD = (
    "你是 TriCompany close skill 席（%s席·轮收口）。对以下 run-dir 材料做收口归集，产出"
    "**一个 JSON 对象**（零多余文本）作为 close.json：\n"
    "{\"close_version\": \"1.0.0\", \"run_id\": \"<原样>\", \"from_week\": \"<W..>\", "
    "\"to_week\": \"<W..>\", \"upgrade_list_state\": \"extracted|none\", "
    "\"upgrade_list\": [{\"item\": \"...\", \"source\": \"<run-dir 内路径>\", \"kind\": \"...\"}], "
    "\"check_time\": \"<UTC ISO>\"}\n"
    "纪律：**run_state 由 TC 权威判定·席不输出该键**（六旗语义=TC 判非席自判·SDE 定谳）；**upgrade_list_state 必载显式二值**（extracted=有升级项；none=无·禁缺省禁第三值）；"
    "只读材料零写入（**禁创建/修改/删除任何文件**——产物=回复 JSON·DP-019）·source 指 run-dir 内件（材料读取一律用 run_dir **绝对路径**·cwd 为隔离沙盒·DP-019）·禁裸结论。\n"
)

_DS_BALANCE_URL = "https://api.deepseek.com/user/balance"
_COST_LOG_NAME = "cost-log.jsonl"
_ROUND_CAP_CNY = 1.0
_TOTAL_CAP_CNY = 10.0
_BALANCE_FLOOR_CNY = 20.0


def _deepseek_balance_cny():
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


def _count_trigger_runs(run_dir: Path, trigger: str) -> int:
    """v8 item7：统计 cost-log 中 trigger 匹配行数（auto fail-safe 判据：>=1 即已跑过一轮）。"""
    p = run_dir / _COST_LOG_NAME
    if not p.is_file():
        return 0
    n = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rec = _json.loads(line)
        except Exception:
            continue
        if str(rec.get("trigger") or "") == trigger:
            n += 1
    return n


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


_SEAT_SANDBOX_ROOT_ENV = "FADE_SEAT_SANDBOX_ROOT"


def _seat_sandbox() -> Path:
    """DP-20261123-019（CTO 规格①b·seat 工具面治理）：席进程 cwd 限 sandbox 目录——
    席侧任何写入不落链 run_dir（产物只由 stage 写·防自检件污染）。env 可指定根。"""
    import tempfile
    root = os.environ.get(_SEAT_SANDBOX_ROOT_ENV) or tempfile.gettempdir()
    return Path(tempfile.mkdtemp(prefix="fade-seat-sandbox-", dir=root))


def _spawn_seat(seat: str, run_dir: Path, run_id: str, timeout_s: int = 900,
                prompt_override: str | None = None) -> dict:
    prompt = (prompt_override if prompt_override
              else _CLOSE_PROMPT_HEAD % seat.upper() + f"run_id={run_id} run_dir={run_dir}\n")
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
        out = (r.stdout or "")[-60000:]
        return {"rc": r.returncode, "out": out, "err": (r.stderr or "")[:400]}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "out": "", "err": f"spawn timeout {timeout_s}s"}
    except (FileNotFoundError, OSError) as e:  # dsh 缺失/不可执行=absent 不崩溃（健壮性）
        return {"rc": -2, "out": "", "err": f"dsh spawn failed: {e}"}


def _extract_json(out: str):
    try:
        return _json.loads(out)
    except Exception:
        i, j = out.find("{"), out.rfind("}")
        if 0 <= i < j:
            try:
                return _json.loads(out[i:j + 1])
            except Exception:
                return None
    return None


def run(args: argparse.Namespace) -> tuple[int, dict]:
    run_dir = Path(args.run_dir).resolve()
    out: dict = {"close_skill_spawn_version": "1.0.0", "run_id": args.run_id, "seats": list(SEATS)}

    import datetime as _dt
    t0 = _dt.datetime.now(_dt.timezone.utc)
    b0 = _deepseek_balance_cny()
    if b0 is not None and b0 < _BALANCE_FLOOR_CNY:
        out["cost_guard"] = {"paused": True, "balance_cny": b0, "guard": "c",
                             "reason": "balance < %.0f CNY floor (CFO guard c)" % _BALANCE_FLOOR_CNY}
        return 3, out
    if b0 is None:
        # v8 item7（CEO 批）：余额不可得场景分流——auto=无人值守 fail-safe（跑过 1 轮即停）·manual=fail-open 保留
        _trig7 = str(os.environ.get("FADE_TRIGGER", "")).lower()
        if _trig7 not in ("auto", "manual"):
            _trig7 = "auto" if str(os.environ.get("FADE_AUTO_DISPATCH", "")).lower() in ("1", "true", "yes") else "manual"
        if _trig7 == "auto" and _count_trigger_runs(run_dir, "auto") >= 1:
            out["cost_guard"] = {"paused": True, "guard": "c",
                                 "reason": ("v8 item7 fail-safe: balance unavailable (no DEEPSEEK_API_KEY) "
                                            "+ auto trigger with >=1 prior auto round -> stop (manual would fail-open)")}
            return 3, out
    spent = _total_spent_cny(run_dir)
    if spent >= _TOTAL_CAP_CNY:
        out["cost_guard"] = {"paused": True, "total_cny": spent, "guard": "b",
                             "reason": "accumulated spend >= %.0f CNY cap (CFO guard b)" % _TOTAL_CAP_CNY}
        return 3, out

    seat = SEATS[0]
    r = _spawn_seat(seat, run_dir, args.run_id, timeout_s=args.spawn_timeout)
    sheet = _extract_json(r["out"]) if r["rc"] == 0 else None

    # ── 产物校验（upgrade_list_state 契约硬项·fail-closed 零替身）──
    ok = (
        sheet is not None
        and sheet.get("upgrade_list_state") in ("extracted", "none")
        and isinstance(sheet.get("upgrade_list"), list)
    )
    out["spawn"] = {"seat": seat, "rc": r["rc"],
                    "schema_ok": ok, "err": r["err"],
                    **({"raw_out": r["out"][-60000:]} if not ok else {})}

    # ── CFO ⓓ 读数行+ⓐ 告警+null 升级 ──
    t1 = _dt.datetime.now(_dt.timezone.utc)
    b1 = _deepseek_balance_cny()
    delta = (b0 - b1) if (b0 is not None and b1 is not None) else None
    _write_cost_line(run_dir, {
        "stage": "close_skill", "seats": list(SEATS), "seat_count": len(SEATS),
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
                                     "(CFO guard a)" % (delta, _ROUND_CAP_CNY))

    if not ok:
        out["verdict"] = "fail: spawn absent or upgrade_list_state invalid (no substitute artifact)"
        return 2, out

    close_path = run_dir / "close.json"
    close_path.write_text(_json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["written"] = str(close_path)
    # DP-20261123-018 item7（CFO·charter-060521Z）：close.json 增可结算 cost_settlement 块
    try:
        sheet["cost_settlement"] = _build_cost_settlement(run_dir, out)
        out["cost_settlement"] = sheet["cost_settlement"]
    except Exception as e:  # noqa: BLE001 — 结算面零阻断（fail-open·读数缺不拦 close）
        out["cost_settlement_error"] = f"{type(e).__name__}: {e}"
    # v8 item4（CEO 批）：close 前七席强制——缺一席 run_state=partial（chain 不发 notify_done）
    try:
        _ss = _check_seven_seats(run_dir)
        sheet["seven_seats"] = _ss
        out["seven_seats"] = _ss
        # CPO10（B3）：七席作用域可观测——本轮优先（current）／prev 降级（BOD 裁 e0a2f32）
        _srcv = str(_ss.get("source") or "")
        sheet["seven_seat_scope"] = ("current" if _srcv == "current"
                                     else ("prev-degraded" if _srcv else "unavailable"))
        if _ss.get("degraded"):
            # v8 item4 根修：时序错位降级——WARN 留痕·不判施工件失败
            print(f"[close][WARN] 七席门降级（{_ss.get('reason')}）", file=sys.stderr)
        # v8 run_state 权威化（①）：TC 判定覆盖席自判（degraded 亦 ok·覆盖 partial/failed）
        _apply_run_state_authority(sheet, out, _ss)
        if not _ss["ok"]:
            print(f"[close][WARN] 七席未齐（{_ss['detail']}）→ run_state=partial·不发 notify_done",
                  file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        out["seven_seats_error"] = f"{type(e).__name__}: {e}"
    # B4（CAO1/CFO6/CHO2）：升级项三件套 + 消费台账
    try:
        _ul = _enrich_upgrade_list(sheet, args.run_id)
        sheet["upgrade_ledger"] = _ul["upgrade_ledger"]
        sheet["upgrade_missing"] = _ul["upgrade_missing"]
        out["upgrade_ledger_count"] = _ul["count"]
    except Exception as e:  # noqa: BLE001
        out["upgrade_ledger_error"] = f"{type(e).__name__}: {e}"
    # 四件②（CTO 令 2026-11-26）：refill 摘要真值 + divergence 明细（|Δ|≥2 席对）
    try:
        _jr = {}
        try:
            _jr = _json.loads((run_dir / "joint-review.json").read_text(encoding="utf-8"))
        except Exception:
            _jr = {}
        _rf = _jr.get("refill") or {}
        _items = _rf.get("items") or []
        _by = {}
        for _it in _items:
            if isinstance(_it, dict):
                _by[str(_it.get("status"))] = _by.get(str(_it.get("status")), 0) + 1
        _consumed = sum(v for k, v in _by.items() if k in ("done", "deferred", "dropped", "fixed"))
        _tot = len(_items)
        sheet["refill_summary"] = {"total": _tot, "by_status": _by,
                                   "items_consumed": _consumed,
                                   "digest_rate": round(_consumed / _tot, 3) if _tot else None,
                                   "items_ok": _rf.get("items_ok"), "missing": _rf.get("missing") or []}
        # divergence 明细：每席 A/B 均值对·|Δ|≥2 列（非仅 seats=2 泛注）
        _ab2 = _jr.get("ab_columns") or {}
        _pairs: list = []
        _seats2 = sorted(_ab2.keys())
        for i_ in range(len(_seats2)):
            for j_ in range(i_ + 1, len(_seats2)):
                s1, s2 = _seats2[i_], _seats2[j_]
                for _ob in ("a", "b"):
                    v1 = (_ab2.get(s1) or {}).get(_ob)
                    v2 = (_ab2.get(s2) or {}).get(_ob)
                    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)) and abs(v1 - v2) >= 2:
                        _pairs.append({"pair": [s1, s2], "object": _ob, "delta": round(abs(v1 - v2), 2)})
        sheet["divergence_detail"] = {"pairs_ge2": _pairs[:12], "count": len(_pairs)}
        out["refill_summary"] = sheet["refill_summary"]
        out["divergence_detail"] = sheet["divergence_detail"]
    except Exception as e:  # noqa: BLE001
        out["refill_summary_error"] = f"{type(e).__name__}: {e}"
    # A6（CEO 架构令）：close 引用段 7 的 wrong_order 判读（评分依据面）
    try:
        _wov = {"ref": "score-skill.json", "present": (run_dir / "score-skill.json").is_file()}
        try:
            _dce6 = _json.loads((run_dir / "dce.json").read_text(encoding="utf-8"))
            _wo6 = ((_dce6.get("execution_diff") or {}).get("wrong_order") or []) if isinstance(_dce6, dict) else []
            _wov["wrong_order_count"] = len(_wo6)
        except Exception:
            _wov["wrong_order_count"] = None
        sheet["wrong_order_verdict_ref"] = _wov
        out["wrong_order_verdict_ref"] = _wov
    except Exception as e:  # noqa: BLE001
        out["wrong_order_verdict_ref_error"] = f"{type(e).__name__}: {e}"
    # B5 批：closure_rate/closure_chain/anchor/dispositions/requirement_trace/evidence_hashes/round_count
    try:
        _b5 = _build_b5_bundle(run_dir, args.run_id, sheet)
        sheet.update(_b5)
        out["b5_bundle"] = {k: (v if not isinstance(v, dict) else "…") for k, v in _b5.items()}
        _unf = (_b5.get("requirement_trace") or {}).get("unfulfilled") or []
        if _unf and os.environ.get("REQ_TRACE_STRICT", "0") == "1":
            sheet["run_state"] = "failed"
            out["verdict"] = f"fail: requirement_trace 未兑现 {len(_unf)} 条（CPO2 strict）"
            return 2, out
    except Exception as e:  # noqa: BLE001
        out["b5_bundle_error"] = f"{type(e).__name__}: {e}"
    # S5（r36 任务书·CTO 令 2026-11-25）：交接清单 + FUSE 三态逐轮变化面
    try:
        _ho = _build_handoff(run_dir, args.run_id)
        sheet["handoff_items"] = _ho
        out["handoff_items"] = len(_ho)
    except Exception as e:  # noqa: BLE001
        out["handoff_error"] = f"{type(e).__name__}: {e}"
    try:
        _ft = _build_fuse_trace(run_dir)
        sheet["fuse_trace"] = _ft
        out["fuse_trace"] = _ft
    except Exception as e:  # noqa: BLE001
        out["fuse_trace_error"] = f"{type(e).__name__}: {e}"
    # CFO8（B2）：收口三件+审批链证据束（close_fields 三引 + chain-journal approval_chain）
    try:
        _cf = sheet.get("runid_origin") or sheet.get("charter_ref") or {}
        _ac = None
        try:
            for _ln in (run_dir / "chain-journal.jsonl").read_text(encoding="utf-8").splitlines():
                _r = _json.loads(_ln)
                if _r.get("event") == "approval_chain":
                    _ac = _r
        except Exception:
            _ac = None
        sheet["close_evidence_bundle"] = {
            "runid_origin": sheet.get("runid_origin"),
            "charter_ref": sheet.get("charter_ref"),
            "opinions_in": sheet.get("opinions_in"),
            "approval_chain": _ac,
            "three_pieces_ok": bool(sheet.get("runid_origin") is not None),
        }
        out["close_evidence_bundle"] = sheet["close_evidence_bundle"]
    except Exception as e:  # noqa: BLE001
        out["close_evidence_error"] = f"{type(e).__name__}: {e}"
    # S4（r36 任务书 df3e2d419·CTO 令 2026-11-25）：红面即停/空证不得 pass/run_state 与 contract 同源
    try:
        _man = {}
        _mp = run_dir / "manifest.json"
        if _mp.is_file():
            try:
                _man = _json.loads(_mp.read_text(encoding="utf-8"))
            except Exception:
                _man = {}
        _cc = _man.get("close_contract") if isinstance(_man.get("close_contract"), dict) else None
        _reds: list[str] = []
        if _cc is not None and _cc.get("ok") is False:
            _bad = [c.get("check") for c in (_cc.get("checks") or [])
                    if isinstance(c, dict) and c.get("ok") is False]
            _reds.append(f"close_contract.ok=False（fail checks={_bad[:4]}）")
        _ul = sheet.get("upgrade_list") or []
        _no_src = [i.get("item") for i in _ul if isinstance(i, dict)
                   and not str(i.get("source") or "").strip()]
        if _no_src:
            _reds.append(f"空证 upgrade_list {len(_no_src)} 条无 source（示例 {_no_src[:2]}）")
        try:
            _vfy = _json.loads((run_dir / "verify.json").read_text(encoding="utf-8"))
            _ve = [i for i in (_vfy.get("items") or []) if isinstance(i, dict)]
            _no_ev = [i.get("entry") for i in _ve if "evidence_ref" in i
                      and not str(i.get("evidence_ref") or "").strip()]
            if _no_ev:
                _reds.append(f"空证 verify items {len(_no_ev)} 条 evidence_ref 空（示例 {_no_ev[:2]}）")
        except Exception:
            pass
        _sync = {"contract_ok": (None if _cc is None else bool(_cc.get("ok"))),
                 "reds": _reds, "ok": not _reds}
        sheet["contract_sync"] = _sync
        out["contract_sync"] = _sync
        if _reds:
            sheet["run_state"] = "failed"
            # COS4（B2）：升级链——reds→六项回呈字段+BOD→CEO 升级位（notify 失败零阻断）
            _esc = {"to": "CEO(via BOD)", "items": _reds[:6],
                    "six_piece_back": {"run_state": "failed", "reds": _reds[:6],
                                       "contract": _sync.get("contract_ok")}}
            try:
                from runtime.cognition.weekly_plane_shift import _notify_blocking as _np
                _esc["notify_failures"] = _np(subject="[close] S4 红面升级 CEO",
                                              body="；".join(_reds[:3]), to=["BOD"])
            except Exception as e:  # noqa: BLE001
                _esc["notify_error"] = f"{type(e).__name__}: {e}"
            sheet["escalation"] = _esc
            out["escalation"] = _esc
            out["verdict"] = "fail: S4 红面（" + "；".join(_reds[:2]) + "）"
            print("[close][S4] 红面即停：" + "；".join(_reds[:2]), file=sys.stderr)
            return 2, out
        elif _cc is not None and _cc.get("ok") is True and str(sheet.get("run_state") or "") != "succeeded":
            # 同源：contract 绿 → run_state 随 contract（authority 面之后仍一致）
            sheet["run_state"] = "succeeded"
    except Exception as e:  # noqa: BLE001
        out["contract_sync_error"] = f"{type(e).__name__}: {e}"
    # I 族判卷卷链内化（CTO 令 ②c·段 8 前置）：缺卷→spawn 补判；失败=WARN 降级非 fail
    try:
        _jud = _ensure_subjective_score(run_dir, args.run_id)
        out["subjective_judge"] = _jud
        if not _jud.get("ok"):
            print("[close][WARN] I 族判卷兜底降级：" + str(_jud.get("reason")), file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        out["subjective_judge_error"] = f"{type(e).__name__}: {e}"
    # v8 item10/11（CEO 批·CTO 字段底线）：close-acceptance 复算 + 值守计划对表——fail-closed
    _v8_gate_fail = []
    try:
        if os.environ.get("FADE_CLOSE_ACCEPTANCE", "1") != "0":
            _ca = _build_close_acceptance(run_dir)
            sheet["close_acceptance"] = _ca
            _ca_v = _verify_close_acceptance(run_dir)
            sheet["close_acceptance_check"] = _ca_v
            if not _ca_v.get("ok"):
                _v8_gate_fail.append(f"close-acceptance 复算拒：{_ca_v.get('reason')}")
    except Exception as e:  # noqa: BLE001
        _v8_gate_fail.append(f"close-acceptance 面异常：{type(e).__name__}: {e}")
    try:
        if os.environ.get("FADE_PATROL_CHECK", "1") != "0":
            _pc = _check_patrol_plan(run_dir, sheet)
            if not _pc.get("ok"):
                _v8_gate_fail.append(f"值守计划对表拒：{_pc.get('reason')}")
    except Exception as e:  # noqa: BLE001
        _v8_gate_fail.append(f"patrol 面异常：{type(e).__name__}: {e}")
    if _v8_gate_fail:
        out["v8_gate_fail"] = _v8_gate_fail[:4]
    # T1③（CTO 裁落点 b）：结构出口门（upgrade_list 复用·双机械形+1/2 上限+债务表）
    try:
        sheet["structure_export"] = _apply_structure_export_gate(sheet, run_dir)
        out["structure_export"] = sheet["structure_export"]
    except Exception as e:  # noqa: BLE001
        out["structure_export_error"] = f"{type(e).__name__}: {e}"
    # R10-COS-01/CHO-02（CEO 批讫 2026-11-23 19:51:38）：runid_origin/charter_ref + 意见消化率
    try:
        _cf = _build_close_fields(run_dir, args.run_id)
        sheet.update(_cf)
        out["close_fields"] = _cf
    except Exception as e:  # noqa: BLE001
        out["close_fields_error"] = f"{type(e).__name__}: {e}"
    try:
        close_path.write_text(_json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        out["close_write_error"] = f"{type(e).__name__}: {e}"
    if _v8_gate_fail:
        out["verdict"] = "fail: v8 close gate（" + "；".join(_v8_gate_fail[:2]) + "）"
        return 2, out
    out["verdict"] = "pass"
    return 0, out


_STRUCT_KINDS = ("structural_defect", "architecture_gap", "protocol_defect")   # 白名单（双机械形①·语义判读禁入）
_STRUCT_EVIDENCE_PREFIXES = ("tree-facts.json", "plan.json", "joint-review.json",
                             "verify.json", "score.json", "score-skill.json")     # 锚共识机械证据②


def _apply_structure_export_gate(sheet: dict, run_dir: Path) -> dict:
    """T1③/DP-040（CTO 裁落点 b·2026-11-24）：结构缺陷出口=**复用 upgrade_list**（零新机制）。
    双机械形：①kind 白名单②evidence 指机械证据（语义判读禁入）·标注值「结构性缺陷·非单条改进可解」
    上限=每轮 structural ≤ 总条目 1/2（超出标 rejected）·债务表<run_dir>/structure-export-debt.json
    （前两轮均挂出口且无 action_taken→escalate 升级）。"""
    upl = sheet.get("upgrade_list")
    if not isinstance(upl, list):
        return {"checked": False, "detail": "upgrade_list 缺/非数组"}
    struct: list = []
    for it in upl:
        if not isinstance(it, dict):
            continue
        kind = str(it.get("kind") or "")
        if not (it.get("structural") is True or kind in _STRUCT_KINDS):
            continue
        ev = str(it.get("source") or it.get("evidence_ref") or "")
        it["structural"] = True
        it["structure_label"] = "结构性缺陷·非单条改进可解"
        it["evidence_mechanical"] = any(ev.startswith(pf) for pf in _STRUCT_EVIDENCE_PREFIXES)
        struct.append(it)
    total = len(upl)
    cap = max(1, total // 2) if total else 0
    for extra in struct[cap:]:
        extra["structure_export_rejected"] = "cap_exceeded(1/2)"
    debt: dict = {"structural_count": len(struct), "cap": cap,
                  "cap_ok": len(struct) <= cap, "escalate": False,
                  "entries": [str(x.get("item") or x.get("title") or "")[:80] for x in struct]}
    try:
        import glob as _glob
        prevs = sorted(_glob.glob(str(run_dir.parent / "*" / "structure-export-debt.json")))[-2:]
        carried = 0
        for pf in prevs:
            try:
                d = _json.loads(Path(pf).read_text(encoding="utf-8"))
            except Exception:
                continue
            if int(d.get("structural_count") or 0) > 0 and not d.get("action_taken"):
                carried += 1
        debt["prev_carry_rounds"] = carried
        debt["escalate"] = carried >= 2
    except Exception:
        pass
    try:
        (run_dir / "structure-export-debt.json").write_text(
            _json.dumps(debt, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        debt["write_error"] = f"{type(e).__name__}: {e}"
    if debt.get("escalate"):
        print("[close][WARN] structure-export debt：连续≥2 轮挂结构出口无动作 → 升级（T1③ 债务表）",
              file=sys.stderr)
    return debt


_SEVEN_SEATS = ("cos", "coo", "cao", "cpo", "cto", "cho", "cfo")


def _seats_in_dir(d: Path) -> set:
    """目录内联审席位集：opinions.json seats ∪ joint-review.json faces keys。"""
    seats: set = set()
    op = d / "opinions.json"
    if op.is_file():
        try:
            for o in (_json.loads(op.read_text(encoding="utf-8")).get("opinions") or []):
                if isinstance(o, dict):
                    s = o.get("seat") or o.get("owner_seat")
                    if isinstance(s, str) and s.strip():
                        seats.add(s.strip().lower())
        except Exception:
            pass
    jr = d / "joint-review.json"
    if jr.is_file():
        try:
            faces = _json.loads(jr.read_text(encoding="utf-8")).get("faces") or {}
            for k in faces:
                if isinstance(k, str) and k.strip():
                    seats.add(k.strip().lower())
        except Exception:
            pass
    # 四件①（CTO 令）：本轮 per-seat 卷 opinions-*.json 亦为 joint 读源
    try:
        for pf_ in d.glob("opinions-*.json"):
            try:
                _sd = _json.loads(pf_.read_text(encoding="utf-8"))
                _s = str(_sd.get("seat") or "").strip().lower()
                if _s:
                    seats.add(_s)
            except Exception:
                continue
    except Exception:
        pass
    return seats


def _find_prev_run(run_dir: Path) -> Path | None:
    """prev run 解析面（与 item9/10/11 同源策略）：env FADE_PREV_RUN_DIR 优先；
    否则 run_dir 父目录兄弟 dir 按 mtime 降序，取首个含 joint-review/opinions 的（≠当前）。"""
    env = os.environ.get("FADE_PREV_RUN_DIR")
    if env and Path(env).is_dir() and Path(env).resolve() != run_dir.resolve():
        return Path(env)
    parent = run_dir.parent
    try:
        cands = [d for d in parent.iterdir()
                 if d.is_dir() and d.resolve() != run_dir.resolve()
                 and ((d / "joint-review.json").is_file() or (d / "opinions.json").is_file())]
        if not cands:
            return None
        cands.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        return cands[0]
    except Exception:
        return None


def _check_seven_seats(run_dir: Path) -> dict:
    """v8 item4 根修 + 四件①（CTO 令 2026-11-26）：close 读源改 joint——
    **本轮 joint-review.json / opinions-*.json 七席齐 → ok(source="joint")**；
    仅 joint 缺时才降级：prev 借=source=prev-borrow（degraded 显式）/ 全无=joint-missing。"""
    cur = _seats_in_dir(run_dir)
    missing_cur = [s for s in _SEVEN_SEATS if s not in cur]
    if not missing_cur:
        return {"ok": True, "present": sorted(cur), "missing": [], "source": "joint",
                "detail": "七席齐（本轮 joint-review/opinions-*）"}
    prev = _find_prev_run(run_dir)
    if prev is not None:
        ps = _seats_in_dir(prev)
        missing_prev = [s for s in _SEVEN_SEATS if s not in ps]
        if not missing_prev:
            return {"ok": True, "present": sorted(ps), "missing": [], "source": "prev-borrow",
                    "degraded": True,
                    "reason": ("本轮 joint 缺（close 早于链后联审〔轮末钩〕）·借 prev 联审："
                               f"{prev.name}（joint-missing→prev-borrow）")}
        return {"ok": True, "degraded": True, "present": sorted(ps), "missing": missing_prev,
                "source": "prev-borrow",
                "reason": (f"本轮 joint 缺·prev({prev.name}) 七席未齐 {','.join(missing_prev)}"
                           "·门降级留痕（WARN·非施工失败）")}
    return {"ok": True, "degraded": True, "present": sorted(cur), "missing": missing_cur,
            "source": "joint-missing",
            "reason": "本轮 joint 缺且 prev 不可得（joint-missing·门降级留痕 WARN·非施工失败）"}


_ALERT_LOG_NAME = "alerts.jsonl"


def _build_close_acceptance(run_dir: Path) -> dict:
    """v8 item10（F→close-acceptance·CTO 字段底线）：对过程数据验收（非重采）——
    读告警日志复算 {total, by_family, max_latency}·落 close-acceptance.json。"""
    import datetime as _dt
    log = run_dir / _ALERT_LOG_NAME
    total = 0
    by_family: dict = {}
    max_latency = 0.0
    if log.is_file():
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                rec = _json.loads(line)
            except Exception:
                continue
            total += 1
            fam = str(rec.get("family") or "unknown")
            by_family[fam] = by_family.get(fam, 0) + 1
            try:
                max_latency = max(max_latency, float(rec.get("latency_s") or 0))
            except Exception:
                pass
    doc = {"schema_version": "1.0.0",
           "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
           "source": str(log) if log.is_file() else None,
           "total": total, "by_family": by_family, "max_latency": max_latency}
    (run_dir / "close-acceptance.json").write_text(
        _json.dumps(doc, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    return doc


def _verify_close_acceptance(run_dir: Path) -> dict:
    """v8 item10 复算：重读告警日志复算三值对表声明——不一致=fail（两侧值入 reason）；声明缺席=fail-closed。"""
    fp = run_dir / "close-acceptance.json"
    if not fp.is_file():
        return {"ok": False, "reason": "close-acceptance.json 缺席（fail-closed·v8 item10）"}
    try:
        doc = _json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"close-acceptance.json unparsable: {e}"}
    fresh = _build_close_acceptance(run_dir)   # 复算（同源重建·对表两侧）
    bad = []
    for k in ("total", "by_family", "max_latency"):
        if doc.get(k) != fresh.get(k):
            bad.append(f"{k}: 声明={doc.get(k)!r} vs 复算={fresh.get(k)!r}")
    return {"ok": not bad, "reason": "; ".join(bad[:4]) if bad else "复算一致"}


_JUDGE_I_PROMPT = """你是 TriCompany I 族判卷席（cos）。按 COS 形面（cos-judging-prompt-shape-20261125·f374595f9）评 I 族三判据。

【§一 输入三段】①判卷对象=本 run_dir 事务域 ②锚文=36bf14a1d L44 ②读卷：I1←plan.json+r12 数据件+区台账／I2←dce.json+ignite.log+manifest.json／I3←collection/collection-*.json+close.json+plan-freeze.json。
【§二 分制】I1 满分 **4**／I2 满分 **3**／I3 满分 **3**（总 10）——**judge 不自行换算 35 权**（engine 消费时等比例换算）。
【§三 输出形】只输出一个 JSON 对象（零多余文本）：{"run_id": "%s", "criterion": [{"id": "I1", "score": <0-4>, "rationale": "非空≤30字"}, {"id": "I2", "score": <0-3>, "rationale": "非空"}, {"id": "I3", "score": <0-3>, "rationale": "非空"}], "judge_notes": {"anchor_read": "…", "missing_cases": "…", "dual_role_faces": "…", "weight_note": "未预换算"}}（**无 evidence_ref**）
【§四 四注意】①锚文判读先行 ②**缺件不判 0**（collection 缺=pending 非 0）③一人两角留痕 ④权重勿预换算。
纪律：只读材料零写入·禁创建/修改/删除任何文件（DP-019）。
run_dir=%s
"""


def _extract_json(text: str):
    """从回复文本提取首个 JSON 对象（尾截断容忍：取首 { 至末 }）。"""
    if not isinstance(text, str):
        return None
    i = text.find("{")
    j = text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return _json.loads(text[i:j + 1])
    except Exception:
        return None


def _build_b5_bundle(run_dir: Path, run_id: str, sheet: dict) -> dict:
    """B5 四件（COO3/COO4/COS1/COS2/CPO1/CPO2/CPO3/CFO12/CHO12）的卷面装配面：
    closure_rate / closure_chain / verification_anchor / dispositions / requirement_trace / evidence_hashes + round_count。"""
    import hashlib as _hl
    out: dict = {}
    plan: dict = {}
    try:
        plan = _json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    except Exception:
        plan = {}
    # CFO12：round_count（runner-state 读）+三引在位
    _rc = None
    try:
        _st = _json.loads((run_dir.parent / "state" / "runner-state.json").read_text(encoding="utf-8"))
        _rc = _st.get("round_count")
    except Exception:
        _rc = None
    out["round_count"] = _rc
    # CHO12：evidence hashes（close/opinions/verify 逐件 sha16 + run_id）
    _evh: dict = {}
    for _fn in ("close.json", "opinions.json", "verify.json"):
        _fp = run_dir / _fn
        if _fp.is_file():
            try:
                _raw = _fp.read_bytes()
                _rid = (_json.loads(_raw.decode("utf-8")).get("run_id")
                        if _fn != "close.json" else sheet.get("run_id"))
                _evh[_fn] = {"sha256_16": _hl.sha256(_raw).hexdigest()[:16],
                             "run_id": _rid, "run_id_match": (str(_rid or "") == run_id) if _rid else None}
            except Exception:
                continue
    out["evidence_hashes"] = _evh
    # COO3：恢复承诺闭环率（plan.carry_over 承诺 vs close 处置）
    _committed = len([c for c in (plan.get("carry_over") or []) if isinstance(c, dict)])
    _closed = len([c for c in (sheet.get("upgrade_ledger") or [])
                   if isinstance(c, dict) and c.get("consumed")])
    out["closure_rate"] = {"committed": _committed, "closed": min(_closed, _committed) if _committed else _closed,
                           "rate": round((min(_closed, _committed) / _committed), 3) if _committed else None}
    # COS1：order→ledger 五段闭链（件在位面）
    out["closure_chain"] = {k: {"present": (run_dir / fn).is_file(), "ref": fn} for k, fn in (
        ("order", "plan.json"), ("dispatch", "opinions.json"), ("score", "score.json"),
        ("close", "close.json"), ("handoff", "close.json#handoff_items"))}
    # COS2：四账同源 verification_anchor（composite sha16）
    _h = _hl.sha256()
    for _fn in ("plan.json", "score.json", "opinions.json", "close.json"):
        _fp = run_dir / _fn
        if _fp.is_file():
            _h.update(_fp.read_bytes())
    out["verification_anchor"] = {"composite_sha256_16": _h.hexdigest()[:16],
                                  "ordering": "plan→score→opinions→close"}
    # CPO1：dispositions 全集+双域计数
    _disp: dict = {}
    _dual = {"a": 0, "b": 0}
    for o in (_json.loads((run_dir / "opinions.json").read_text(encoding="utf-8")).get("opinions") or [])             if (run_dir / "opinions.json").is_file() else []:
        if isinstance(o, dict):
            _s = str(o.get("disposition") or "open")
            _disp[_s] = _disp.get(_s, 0) + 1
            for _d in ("a", "b"):
                if isinstance(o.get("scores"), dict) and any(True for _k in o["scores"]):
                    pass
    for c in (sheet.get("upgrade_ledger") or []):
        if isinstance(c, dict):
            _disp[c.get("disposition") or "open"] = _disp.get(c.get("disposition") or "open", 0) + 1
    out["dispositions"] = {"by_status": _disp, "dual_domain": _dual}
    # CPO2：requirement_trace（逐条兑现 + 未兑现显式）
    rt: list = []
    for c in (sheet.get("upgrade_ledger") or []):
        if isinstance(c, dict):
            rt.append({"requirement": c.get("item"), "fulfilled": bool(c.get("consumed")),
                       "evidence": c.get("clause_no")})
    out["requirement_trace"] = {"items": rt,
                                "unfulfilled": [x["requirement"] for x in rt if not x["fulfilled"]]}
    return out


def _enrich_upgrade_list(sheet: dict, run_id: str) -> dict:
    """CAO1+CFO6+CHO2（B4）：升级项三件套补全（条款号/入册 commit/生效时点）+ 消费台账
    （逐条主责席/责任面/处置态）——缺字段显式标 missing（非静默）。"""
    import datetime as _dt
    _now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    ul = sheet.get("upgrade_list") or []
    ledger: list = []
    missing: list = []
    for i, it in enumerate(ul):
        if not isinstance(it, dict):
            continue
        it.setdefault("clause_no", f"U-{i + 1:02d}")
        it.setdefault("landed_commit", os.environ.get("FADE_LANDED_COMMIT", "pending"))
        it.setdefault("effective_at", _now)
        _owner = str(it.get("owner") or it.get("owner_seat") or "unassigned")
        _face = str(it.get("responsibility_face") or "close")
        _disp = str(it.get("disposition") or ("consumed" if str(it.get("source") or "").strip() else "open"))
        ledger.append({"item": it.get("item"), "clause_no": it["clause_no"],
                       "owner": _owner, "responsibility_face": _face,
                       "consumed": bool(str(it.get("source") or "").strip()), "disposition": _disp,
                       "effective_at": it["effective_at"]})
        _miss = [k for k in ("clause_no", "landed_commit", "effective_at")
                 if not str(it.get(k) or "").strip()]
        if _miss:
            missing.append({"item": it.get("item"), "missing": _miss})
    return {"upgrade_ledger": ledger, "upgrade_missing": missing, "count": len(ledger)}


def _build_handoff(run_dir: Path, run_id: str) -> list[dict]:
    """S5（r36 任务书 df3e2d419·CTO 令 2026-11-25）：交接清单——本轮产物责任交接面
    {item, target, owner_seat, receipt}：charter items owner_seat 优先（T1a 溯源衔接）→
    opinions owner_seat 兜底；plan.unassigned_items 以 owner='unassigned' 列（候认领）。"""
    items: list[dict] = []
    charter = None
    try:
        cands = sorted(run_dir.glob("charter-*.json"))
        if cands:
            charter = _json.loads(cands[-1].read_text(encoding="utf-8"))
    except Exception:
        charter = None
    if isinstance(charter, dict) and charter.get("items"):
        for it in charter["items"]:
            if isinstance(it, dict):
                items.append({"item": it.get("title") or it.get("opinion_id"),
                              "target": it.get("target"),
                              "owner_seat": it.get("owner_seat"),
                              "receipt": f"charter:{charter.get('charter_id')}"})
    else:
        try:
            ops = _json.loads((run_dir / "opinions.json").read_text(encoding="utf-8")).get("opinions") or []
        except Exception:
            ops = []
        for o in ops:
            if isinstance(o, dict) and o.get("title"):
                items.append({"item": o.get("title"), "target": o.get("target"),
                              "owner_seat": o.get("owner_seat") or o.get("seat"),
                              "receipt": "opinions"})
    try:
        plan = _json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        for u in plan.get("unassigned_items") or []:
            if isinstance(u, dict):
                items.append({"item": u.get("item_id"), "target": u.get("target"),
                              "owner_seat": "unassigned", "receipt": "plan.unassigned_items（候认领）"})
    except Exception:
        pass
    return items


def _fuse_state_of(run_dir: Path) -> str | None:
    """读 run 的 chain-journal 首行 chain_start.d91_marker.state（absent/running/stale/unknown）。"""
    try:
        jp = run_dir / "chain-journal.jsonl"
        if not jp.is_file():
            return None
        for line in jp.read_text(encoding="utf-8").splitlines():
            try:
                rec = _json.loads(line)
            except Exception:
                continue
            if rec.get("event") == "chain_start":
                d = rec.get("d91_marker") or {}
                return d.get("state")
        return None
    except Exception:
        return None


def _build_fuse_trace(run_dir: Path) -> dict:
    """S5：FUSE（D-91）三态逐轮变化面——本 run vs 上一 run 的 chain_start.d91_marker.state。"""
    cur = _fuse_state_of(run_dir)
    prev_state = None
    prev_run = None
    try:
        parent = run_dir.parent
        cands = [d for d in parent.iterdir()
                 if d.is_dir() and d.resolve() != run_dir.resolve()
                 and (d / "chain-journal.jsonl").is_file()]
        if cands:
            cands.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            prev_run = cands[0].name
            prev_state = _fuse_state_of(cands[0])
    except Exception:
        pass
    return {"cur": cur, "prev": prev_state, "prev_run": prev_run,
            "changed": (prev_state is not None and cur is not None and prev_state != cur)}


def _ensure_subjective_score(run_dir: Path, run_id: str) -> dict:
    """I 族判卷卷链内化（CTO 令 2026-11-25·②c 兜底·段 8 前置·COS 形面 f374595f9）：
    subjective-score.json 缺→spawn 一次判卷（COS 形 prompt·I1≤4/I2≤3/I3≤3·无 evidence_ref）→解析落卷；
    spawn/解析失败=**门降级 WARN（非 fail）**。卷在（entries 有效）→present 直过。"""
    fp = run_dir / "subjective-score.json"
    if fp.is_file():
        try:
            doc = _json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and doc.get("entries"):
                return {"ok": True, "state": "present"}
        except Exception:
            pass
    prompt = _JUDGE_I_PROMPT % (run_id, run_dir)
    try:
        r = _spawn_seat("cos", run_dir, run_id, timeout_s=int(
            os.environ.get("FADE_JUDGE_TIMEOUT_S", "600")))
        sheet = _extract_json(r["out"]) if r.get("rc") == 0 else None
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "state": "degraded-warn",
                "reason": f"判卷 spawn 异常（{type(e).__name__}: {e}）→ WARN 降级"}
    crit = (sheet or {}).get("criterion") if isinstance(sheet, dict) else None
    _caps = {"I1": 4.0, "I2": 3.0, "I3": 3.0}
    entries = []
    for c in crit or []:
        if not isinstance(c, dict):
            continue
        _id = str(c.get("id") or "")
        if _id not in _caps:
            continue
        try:
            _sc = float(c.get("score"))
        except (TypeError, ValueError):
            continue
        _rat = str(c.get("rationale") or "").strip()
        if not _rat:
            continue
        entries.append({"criterion": _id, "score": min(max(_sc, 0), _caps[_id]), "rationale": _rat})
    if not entries:
        return {"ok": False, "state": "degraded-warn",
                "reason": "判卷 spawn 无有效 criterion（WARN 降级·非 fail）"}
    import datetime as _dt
    fp.write_text(_json.dumps({
        "score_version": "1.0.0", "run_id": run_id, "entries": entries,
        "judge_faces": {"fallback": "close-stage8_inline"},
        "check_time": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    return {"ok": True, "state": "spawned", "entries": len(entries)}


def _check_patrol_plan(run_dir: Path, sheet: dict) -> dict:
    """v8 item11（close 侧·CTO 字段底线）：读 patrol log 重数拍频对表计划 {who,cadence,window}——
    缺 plan.patrol_plan 或 patrol log=fail-closed；拍频偏差>1min=不一致。"""
    import re as _re
    plan_p = run_dir / "plan.json"
    declared = None
    try:
        plan_doc = _json.loads(plan_p.read_text(encoding="utf-8"))
        declared = plan_doc.get("patrol_plan")
    except Exception:
        declared = None
    # 两形漂移双修（CTO 令 2026-11-25）：旧形 {who,cadence,window} 照过；新形 cadence_layers
    # 无顶层 cadence → 取 cadence_layers.duty_patrol.cadence 兜底（H 的 bod 层归 judge 面·此处对表为 duty）。
    if isinstance(declared, dict) and not declared.get("cadence"):
        _layers = declared.get("cadence_layers")
        if isinstance(_layers, dict):
            for _k in ("duty_patrol", "bod_patrol"):
                _lv = _layers.get(_k)
                if isinstance(_lv, dict) and _lv.get("cadence"):
                    declared = {**declared, "cadence": _lv["cadence"]}
                    break
    if not isinstance(declared, dict) or not all(declared.get(k) for k in ("who", "cadence", "window")):
        return {"ok": False,
                "reason": "plan.patrol_plan 缺/不齐（{who,cadence|cadence_layers,window}·fail-closed）"}
    log = Path(os.environ.get("FADE_PATROL_LOG") or (run_dir / "patrol-log.jsonl"))
    if not log.is_file():
        # BOD 裁准（CTO 令 2026-11-25）：patrol-log 无产出机制=设计缺口 → 门降级 WARN 非 fail·留痕不静默
        _w = {"ok": True, "degraded": True,
              "reason": "patrol-log 无产出机制（设计缺口）·门降级留痕（WARN·非施工失败）"}
        sheet["patrol_check"] = _w
        print("[close][WARN] patrol-log 缺（设计缺口·门降级留痕·BOD 裁准）：" + str(log),
              file=sys.stderr)
        return _w
    ts: list = []
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            rec = _json.loads(line)
        except Exception:
            continue
        v = rec.get("ts") or rec.get("time")
        if isinstance(v, str):
            ts.append(v)
    ticks = len(ts)
    measured = None
    if ticks >= 2:
        try:
            from datetime import datetime as _dtm
            parsed = sorted(_dtm.fromisoformat(x.replace("Z", "+00:00")) for x in ts)
            gaps = [(b - a).total_seconds() / 60 for a, b in zip(parsed, parsed[1:])]
            gaps.sort()
            measured = round(gaps[len(gaps) // 2], 1)
        except Exception:
            measured = None
    m = _re.match(r"^(\d+)\s*m$", str(declared.get("cadence")))
    declared_min = float(m.group(1)) if m else None
    ok = (declared_min is not None and measured is not None and abs(measured - declared_min) <= 1.0)
    res = {"ok": bool(ok), "declared": declared, "ticks": ticks,
           "measured_median_min": measured,
           "reason": "对表一致" if ok else
           (f"拍频对表败：声明={declared.get('cadence')!r} 实测中位={measured}min ticks={ticks}" if measured is not None
            else "patrol log 有效拍<2（不可重数）")}
    sheet["patrol_check"] = res
    return res


def _apply_run_state_authority(sheet: dict, out: dict, seven: dict) -> dict:
    """v8 run_state 权威化（SDE 定谳·CTO 令 2026-11-25）：六旗语义=TC 判非席自判——
    seven_seats.ok（含 degraded）→ **覆盖席输出为 succeeded**；ok=False→partial（真缺场景·chain 停）。"""
    if seven.get("ok"):
        sheet["run_state"] = "succeeded"
        out["run_state_authority"] = "tc_override_ok"
    elif os.environ.get("FADE_CLOSE_SEVEN_SEATS", "1") != "0":
        sheet["run_state"] = "partial"
        out["seven_seats_partial"] = True
    return sheet


def _runid_origin(run_id: str) -> str:
    """R10-COS-01（CEO 批讫 19:51:38）：run_id 形→来源分类（号类型贯通）。"""
    import re as _re
    rid = run_id or ""
    m = _re.search(r"-resume(\d*)-", rid)
    if m:
        return "resume" + (m.group(1) or "")
    for k in ("loop", "ignite", "official"):
        if f"-{k}-" in rid:
            return k
    return "bare"


def _build_opinion_dispositions(run_dir: Path, ops: list, consumed_ids: dict) -> list:
    """DP-033 cho-1（CEO 批 2026-11-23T22:21:43）：意见逐条处置表，堵 FUSE 静默丢弃。
    优先级：run_dir/opinion_dispositions.json 覆盖 > charter 收录(consumed) > 默认 deferred。
    """
    override = {}
    o_path = run_dir / "opinion_dispositions.json"
    if o_path.is_file():
        try:
            doc = _json.loads(o_path.read_text(encoding="utf-8"))
            for d in (doc.get("dispositions") or []):
                if isinstance(d, dict) and d.get("opinion_id"):
                    override[str(d["opinion_id"])] = d
        except Exception:
            pass
    rows = []
    for o in ops:
        oid = str(o.get("opinion_id") or "")
        seat = str(o.get("seat") or "")
        row = {"opinion_id": oid, "seat": seat}
        if oid and oid in consumed_ids:
            it = consumed_ids[oid]
            row.update({"state": "consumed",
                        "owner_seat": str(it.get("owner_seat") or seat),
                        "reason": "charter 收录·item=" + oid,
                        "evidence_ref": str(it.get("__evidence__") or "")})
        elif oid and oid in override:
            d = override[oid]
            row.update({"state": str(d.get("state") or "deferred"),
                        "owner_seat": str(d.get("owner_seat") or seat),
                        "reason": str(d.get("reason") or ""),
                        "evidence_ref": str(d.get("evidence_ref") or "opinion_dispositions.json")})
        else:
            row.update({"state": "deferred",
                        "owner_seat": seat,
                        "reason": "未入本轮 charter（候补件·五字段缺口面见 charter-hook 回退记录）",
                        "evidence_ref": "opinions.json"})
        rows.append(row)
    return rows


def _build_close_fields(run_dir: Path, run_id: str) -> dict:
    """R10-COS-01/CHO-02 + DP-033 cho-1：runid_origin/charter_ref + 意见消化率 + 逐条处置表。"""
    import glob as _glob
    origin = _runid_origin(run_id)
    charters = sorted(_glob.glob(str(run_dir / "charter-*.json")))
    charter_ref = charters[-1] if charters else None
    opinions_in = 0
    titles: list = []
    ops: list = []
    p = run_dir / "opinions.json"
    if p.is_file():
        try:
            doc = _json.loads(p.read_text(encoding="utf-8"))
            ops = [o for o in (doc.get("opinions") or []) if isinstance(o, dict)]
            opinions_in = len(ops)
            titles = [str(o.get("title") or "")[:40] for o in ops]
        except Exception:
            pass
    consumed_ids: dict = {}
    items_total = 0
    if charter_ref:
        try:
            ch = _json.loads(Path(charter_ref).read_text(encoding="utf-8"))
            items = [i for i in (ch.get("items") or []) if isinstance(i, dict)]
            items_total = len(items)
            for idx, it in enumerate(items):
                oid = str(it.get("opinion_id") or "")
                if oid:
                    consumed_ids[oid] = {
                        "owner_seat": it.get("owner_seat"),
                        "__evidence__": "%s#items[%d]" % (Path(charter_ref).name, idx),
                    }
        except Exception:
            pass
    dispositions: list = []
    if ops and any(o.get("opinion_id") for o in ops):
        dispositions = _build_opinion_dispositions(run_dir, ops, consumed_ids)
        items_consumed = sum(1 for r in dispositions if r.get("state") == "consumed")
    else:
        items_consumed = items_total
    digest_rate = round(items_consumed / opinions_in, 3) if opinions_in else None
    res = {"runid_origin": origin, "charter_ref": charter_ref,
           "opinions_in": opinions_in, "items_consumed": items_consumed,
           "digest_rate": digest_rate}
    if dispositions:
        res["opinion_dispositions"] = dispositions
    if opinions_in and items_consumed < opinions_in:
        res["undigested_note"] = ("未消化意见见 opinions.json：" +
                                  "; ".join(t for t in titles[items_consumed:items_consumed + 5] if t))
    return res


def _build_cost_settlement(run_dir: Path, out: dict) -> dict:
    """DP-018 item7：从 run_dir/cost-log.jsonl 汇可结算读数（CFO 口径·delta null 强制 unavailable_reason）。"""
    import datetime as _dt
    stages: list = []
    p = run_dir / _COST_LOG_NAME
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = _json.loads(line)
            except Exception:
                continue
            delta = rec.get("delta_cny")
            stages.append({
                "stage": rec.get("stage"),
                "duration_s": rec.get("duration_s"),
                "seats": rec.get("seats"),
                "delta_cny": delta,
                "status": "settled" if delta is not None else "unavailable",
            })
    total_duration = round(sum((s.get("duration_s") or 0) for s in stages), 1) if stages else 0.0
    deltas = [s["delta_cny"] for s in stages if s.get("delta_cny") is not None]
    total_delta = round(sum(deltas), 4) if deltas else None
    null_n = sum(1 for s in stages if s.get("delta_cny") is None)
    unavailable_reason = None
    if total_delta is None or null_n:
        unavailable_reason = (f"delta_cny unavailable for {null_n}/{len(stages)} stage(s): "
                              "balance probe missing (DEEPSEEK_API_KEY/env face) — token level not projected by dsh")
    # DP-040-03 T3: guard_hits 四键语义分立（旧件无 "guard" 字段时从 reason 解析·向后兼容）
    _cg = out.get("cost_guard") or {}
    _reason = str(_cg.get("reason") or "")
    _which = _cg.get("guard") or ("c" if "(CFO guard c)" in _reason
                                  else ("b" if "(CFO guard b)" in _reason else ""))
    guard_hits = {
        "a": int(bool(out.get("cost_guard_warning"))),                  # (a) round-cap warning
        "b": int(bool(_cg.get("paused") and _which == "b")),            # (b) total-cap gate
        "c": int(bool(_cg.get("paused") and _which == "c")),            # (c) balance-floor gate
        "d": int(bool(out.get("cost_guard_warning_balance"))),          # (d) readout degraded/null-escalate
    }
    return {
        "stages": stages,
        "total_duration_s": total_duration,
        "total_delta_cny": total_delta,
        "unavailable_reason": unavailable_reason,
        "guard_hits": guard_hits,
        "transcript_readout": {
            "channel": "cfo-token-meter.py",
            "query": "--from <run_start_iso> --to <run_end_iso> [--runid <run_id>]",
            "status": "deferred",
            "note": ("session-level transcript readout is machine-local face only; "
                     "cash face = platform balance deduction, not substitutable"),
        },
        "settled_by": "CFO",
        "settled_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--from-week", default="")
    ap.add_argument("--to-week", default="")
    ap.add_argument("--spawn-timeout", type=int, default=900)
    args = ap.parse_args()
    rc, out = run(args)
    print(_json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
