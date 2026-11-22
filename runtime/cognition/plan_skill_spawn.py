"""Plan skill spawn 段（P3·段 3 plan_scope 的 spawn cos 化形·CTO 定谳 7c389cac3 §一·2026-11-21）。

形照 score_skill_spawn.py 模板：单席（cos）dsh headless spawn + overlay 同源 + F4 上限 +
absent 存 raw_out。**灰度形**：本脚本与 CLI 形 plan_scope.py 并存——chain_runner 侧
env FADE_PLAN_SPAWN=1 切换（回滚=去 flag 即回 CLI 形）。

产物：run_dir/plan.json——spawn 败=exit 2 拒产替身（fail-closed）。

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

# P3 形参化（回滚=env PLAN_SKILL_SEATS="cos" 不变·多席候选留形）
_DEFAULT_SEATS = ("cos",)
SEATS = tuple(s.strip() for s in os.environ.get(
    "PLAN_SKILL_SEATS", ",".join(_DEFAULT_SEATS)).split(",") if s.strip())

_PLAN_PROMPT_HEAD = (
    "你是 TriCompany plan skill 席（%s席·周迁移规划+考卷分产出）。对以下 run-dir 材料做"
    "周迁移规划，产出**一个 JSON 对象**（零多余文本）作为 plan.json：\n"
    "{\"plan_version\": \"1.0.0\", \"run_id\": \"<原样>\", \"from_week\": \"<W..>\", "
    "\"to_week\": \"<W..>\", \"verdict\": \"pass\", \"counts\": {\"migrate\": <n>, \"keep\": <n>, \"carry_over\": <n>, \"top_level\": <n>}, "
    "\"migrate\": [], \"keep\": [], \"carry_over\": [], "
    "\"families\": [{\"family_id\": \"A\", \"family_name\": \"...\", "
    "\"items\": [{\"item_id\": \"...\", \"desc\": \"...\", \"status\": \"planned\"}]}, ...], "
    "\"agent_readings\": [{\"agent\": \"...\", \"action\": \"...\", \"rationale\": \"...\", "
    "\"evidence_ref\": \"<run-dir 内路径>\"}, ...], \"check_time\": \"<UTC ISO>\"}\n"
    "（v7 契约注：verdict 必为 \"pass\"（verify 毒化拦）；counts 必为 dict 且 migrate/keep/carry_over/top_level 四键齐；三数组与 counts 对账一致。）\n"
    "纪律：只读材料零写入·evidence_ref 指 run-dir 内件·families 非空·每族 items 非空；"
    "禁裸结论（rationale 必附）。\n"
    "【出题职能（CEO 任务书 v7·12 类语义依据）】同轮须产考卷 exam 段（顶层 key，与 plan 同 JSON 返回）：\n"    "{\"exam\": {\"schema_version\": \"1.0.0\", \"objective\": [{\"id\": \"O1\", \"dimension\": \"<12类之一>\", \"assertion\": \"<机器可判断言>\", \"weight\": 5}], \"subjective\": [{\"id\": \"S1\", \"dimension\": \"<12类之一>\", \"question\": \"<主观题>\", \"rubric\": \"<判据>\", \"weight\": 10}]}}\n"    "出题规则：objective=可程序判（断言须机器可验·供段 6 score_cli）；subjective=需 agent 判（供段 7 两席）；各 ≥3 题·weight 正整数·题目须贴本周实际工作形态；出卷≠改卷·轮内锁卷。\n"
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


def _spawn_seat(seat: str, run_dir: Path, run_id: str, timeout_s: int = 900) -> dict:
    prompt = _PLAN_PROMPT_HEAD % seat.upper() + f"run_id={run_id} run_dir={run_dir}\n"
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
    out: dict = {"plan_skill_spawn_version": "1.0.0", "run_id": args.run_id, "seats": list(SEATS)}

    # ── CFO 护栏 ⓒ/ⓑ ──
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

    # ── 产物校验（schema 关键护栏·fail-closed 零替身）──
    ok = (
        sheet is not None
        and isinstance(sheet.get("families"), list) and len(sheet["families"]) > 0
        and isinstance(sheet.get("agent_readings"), list) and len(sheet["agent_readings"]) > 0
    )
    out["spawn"] = {"seat": seat, "rc": r["rc"],
                    "schema_ok": ok, "err": r["err"],
                    **({"raw_out": r["out"][-60000:]} if not ok else {})}

    # ── CFO ⓓ 读数行+ⓐ 告警+null 升级 ──
    t1 = _dt.datetime.now(_dt.timezone.utc)
    b1 = _deepseek_balance_cny()
    delta = (b0 - b1) if (b0 is not None and b1 is not None) else None
    _write_cost_line(run_dir, {
        "stage": "plan_skill", "seats": list(SEATS), "seat_count": len(SEATS),
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
        out["verdict"] = "fail: spawn absent or schema invalid (no substitute artifact)"
        return 2, out

    # ── 落产物（下游契约 schema 不变）──
    # v7 职责分离（CTO ce26401a9）：exam 段独立落 exam.json（objective→段6·subjective→段7）；plan.json 剥 exam 段
    plan_doc = dict(sheet)
    exam = plan_doc.pop("exam", None)
    plan_path = run_dir / "plan.json"
    plan_path.write_text(_json.dumps(plan_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["written"] = str(plan_path)
    if isinstance(exam, dict) and (exam.get("objective") or exam.get("subjective")):
        exam.setdefault("schema_version", "1.0.0")
        (run_dir / "exam.json").write_text(_json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out["exam_written"] = str(run_dir / "exam.json")
        out["exam_counts"] = {"objective": len(exam.get("objective") or []), "subjective": len(exam.get("subjective") or [])}
    else:
        # 零 exam=派生兜底最小卷（不造假题：仅显式空卷标记，候值席补面）
        (run_dir / "exam.json").write_text(_json.dumps(
            {"schema_version": "1.0.0", "objective": [], "subjective": [], "note": "spawn 未产 exam 段（候值席补面·不造假题）"},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out["exam_written"] = str(run_dir / "exam.json")
        out["exam_counts"] = {"objective": 0, "subjective": 0}
    out["verdict"] = "pass"
    return 0, out


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
