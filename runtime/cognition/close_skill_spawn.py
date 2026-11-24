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
    "\"run_state\": \"<succeeded|failed|partial>\", \"check_time\": \"<UTC ISO>\"}\n"
    "纪律：**upgrade_list_state 必载显式二值**（extracted=有升级项；none=无·禁缺省禁第三值）；"
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


def _spawn_seat(seat: str, run_dir: Path, run_id: str, timeout_s: int = 900) -> dict:
    prompt = _CLOSE_PROMPT_HEAD % seat.upper() + f"run_id={run_id} run_dir={run_dir}\n"
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
        if not _ss["ok"] and (os.environ.get("FADE_CLOSE_SEVEN_SEATS", "1") != "0"):
            sheet["run_state"] = "partial"
            out["seven_seats_partial"] = True
            print(f"[close][WARN] 七席未齐（{_ss['detail']}）→ run_state=partial·不发 notify_done",
                  file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        out["seven_seats_error"] = f"{type(e).__name__}: {e}"
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


def _check_seven_seats(run_dir: Path) -> dict:
    """v8 item4（CEO 批）：close 前强制七席——opinions.json 席位集须齐 7。
    缺一席→ok=False（调用面 run_state=partial·chain 不发 notify_done·cpo-1 同形）。"""
    p = run_dir / "opinions.json"
    if not p.is_file():
        return {"ok": False, "present": [], "missing": list(_SEVEN_SEATS),
                "detail": "opinions.json 缺（七席联审未产）"}
    try:
        doc = _json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "present": [], "missing": list(_SEVEN_SEATS),
                "detail": f"opinions.json unparsable: {e}"}
    seats = set()
    for o in (doc.get("opinions") or []):
        if isinstance(o, dict):
            s = o.get("seat") or o.get("owner_seat")
            if isinstance(s, str) and s.strip():
                seats.add(s.strip().lower())
    missing = [s for s in _SEVEN_SEATS if s not in seats]
    return {"ok": not missing, "present": sorted(seats), "missing": missing,
            "detail": "七席齐" if not missing else f"缺席: {','.join(missing)}"}


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
    if not isinstance(declared, dict) or not all(declared.get(k) for k in ("who", "cadence", "window")):
        return {"ok": False, "reason": "plan.patrol_plan 缺/不齐（{who,cadence,window}·fail-closed）"}
    log = Path(os.environ.get("FADE_PATROL_LOG") or (run_dir / "patrol-log.jsonl"))
    if not log.is_file():
        return {"ok": False, "reason": f"patrol log 缺（{log}·fail-closed·v8 item11）"}
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
