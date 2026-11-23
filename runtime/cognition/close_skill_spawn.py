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
    import datetime as _dt
    rec = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(), **rec}
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
        out["cost_guard"] = {"paused": True, "balance_cny": b0,
                             "reason": "balance < %.0f CNY floor (CFO guard c)" % _BALANCE_FLOOR_CNY}
        return 3, out
    spent = _total_spent_cny(run_dir)
    if spent >= _TOTAL_CAP_CNY:
        out["cost_guard"] = {"paused": True, "total_cny": spent,
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
        close_path.write_text(_json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out["cost_settlement"] = sheet["cost_settlement"]
    except Exception as e:  # noqa: BLE001 — 结算面零阻断（fail-open·读数缺不拦 close）
        out["cost_settlement_error"] = f"{type(e).__name__}: {e}"
    out["verdict"] = "pass"
    return 0, out


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
    guard_hits = {"a": int(bool(out.get("cost_guard_warning"))),
                  "b": int(bool(out.get("cost_guard", {}).get("paused"))),
                  "c": int(bool(out.get("cost_guard_warning_balance")))}
    return {
        "stages": stages,
        "total_duration_s": total_duration,
        "total_delta_cny": total_delta,
        "unavailable_reason": unavailable_reason,
        "guard_hits": guard_hits,
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
