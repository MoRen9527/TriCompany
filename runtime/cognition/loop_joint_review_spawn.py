"""Loop 尾段·七席联审 spawn（CEO 任务书 v7·CTO ce26401a9 定形·2026-11-22）。

层级=loop 层（fade 十段全毕后自动发起·round_runner 轮末钩调用）——非 fade 段（无「段 11」）。

两评价对象（CEO 原话）：a) 周工作平面迁移质量　b) fade-001 本身工作质量。
每席对两对象各提 ≥3 个部门维度（各席按本部门负责人视角自定）→ improvements 五字段。
产物：run_dir/opinions.json（schema 2.0.0·七席 opinions·improvements 五字段→生成器）
      run_dir/joint-review.json（联审读数卷：每席维度+分+意见计数）。

CFO 护栏四件同族（余额门/累计门/读数行/告警+null 升级）。dsh 缺失/异常=absent 不崩溃（fail-closed）。
"""
from __future__ import annotations

import argparse
import json as _json
import os
import subprocess
import sys
from pathlib import Path

_DEFAULT_SEATS = ("cos", "coo", "cao", "cpo", "cto", "cho", "cfo")
SEATS = tuple(s.strip() for s in os.environ.get(
    "JOINT_REVIEW_SEATS", ",".join(_DEFAULT_SEATS)).split(",") if s.strip())

_JOINT_PROMPT = (
    "你是 TriCompany loop 尾段七席联审席之一（%s席·本部门负责人视角）。本周 fade-001 十段全毕，"
    "请按你部门视角对**两个评价对象**各提 ≥3 个部门维度并打分（0-100）：\n"
    "  对象 a) 周工作平面迁移质量；对象 b) fade-001 本身工作质量。\n"
    "评分依据=run-dir 材料（plan.json/exam.json/score.json/score-skill.json/close.json 等·只读）。\n"
    "只输出一个 JSON 对象（零多余文本）：{\"seat\": \"%s\", "
    "\"dimensions\": [{\"object\": \"a|b\", \"dimension\": \"<部门维度名>\", \"score\": <0-100>, \"rationale\": \"…\"}], "
    "\"improvements\": [{\"title\": \"…\", \"target\": \"<run-dir 内路径>\"或\"<源码路径>\", \"change\": \"…\", \"verify\": \"…\", \"rollback\": \"…\"}]}\n"
    "纪律：dimensions ≥6 条（两对象各 ≥3）；improvements 是可执行改进建议（供下一轮任务书）；每项五字段齐·禁缺字段；禁裸分（rationale 必附）。\n"
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
    prompt = _JOINT_PROMPT % (seat.upper(), seat) + f"run_id={run_id} run_dir={run_dir}\n"
    dsh_bin = os.environ.get("DSH_BIN", "/srv/fleet/dsh/node_modules/.bin/dsh")
    overlay = os.environ.get(
        "DSH_PRESET_OVERLAY", "/home/fleet/.dsh/patches/headless-agentpresets-overlay.yml")
    cmd = [dsh_bin, "--profile", "headless"]
    if overlay and os.path.isfile(overlay):
        cmd += ["--patch", overlay]
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=str(run_dir))
        return {"rc": r.returncode, "out": (r.stdout or "")[-60000:], "err": (r.stderr or "")[:400]}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "out": "", "err": f"spawn timeout {timeout_s}s"}
    except (FileNotFoundError, OSError) as e:
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
    out: dict = {"loop_joint_review_version": "1.0.0", "run_id": args.run_id, "seats": list(SEATS)}

    import datetime as _dt
    t0 = _dt.datetime.now(_dt.timezone.utc)
    b0 = _deepseek_balance_cny()
    if b0 is not None and b0 < _BALANCE_FLOOR_CNY:
        out["cost_guard"] = {"paused": True, "balance_cny": b0,
                             "reason": "balance < %.0f CNY floor (CFO guard c)" % _BALANCE_FLOOR_CNY}
        return 3, out
    if _total_spent_cny(run_dir) >= _TOTAL_CAP_CNY:
        out["cost_guard"] = {"paused": True, "reason": "accumulated spend >= cap (CFO guard b)"}
        return 3, out

    faces: dict = {}
    for seat in SEATS:
        r = _spawn_seat(seat, run_dir, args.run_id, timeout_s=args.spawn_timeout)
        sheet = _extract_json(r["out"]) if r["rc"] == 0 else None
        if sheet and isinstance(sheet.get("dimensions"), list):
            faces[seat] = sheet
        else:
            faces[seat] = {"absent": True, "rc": r["rc"], "raw_out": r["out"][-60000:], "err": r["err"]}
    out["faces"] = faces

    # ── 联审读数卷 + opinions（schema 2.0.0·improvements 五字段→生成器）──
    dims_count = {"a": 0, "b": 0}
    ops = []
    for s, f in faces.items():
        if not isinstance(f, dict) or f.get("absent"):
            continue
        for d in (f.get("dimensions") or []):
            if isinstance(d, dict) and d.get("object") in ("a", "b"):
                dims_count[d["object"]] += 1
        imps = [i for i in (f.get("improvements") or [])
                if isinstance(i, dict) and all(isinstance(i.get(k), str) and i.get(k, "").strip()
                                               for k in ("title", "target", "change", "verify", "rollback"))]
        entry = {"opinion_id": f"{s}-1", "seat": s, "scores": {d.get("dimension"): d.get("score")
                 for d in (f.get("dimensions") or []) if isinstance(d, dict)},
                 "summary": " | ".join(f"{d.get('object')}:{d.get('dimension')}" for d in (f.get("dimensions") or [])[:3] if isinstance(d, dict)),
                 "check_time": None}
        if imps:
            for k in ("title", "target", "change", "verify", "rollback"):
                entry[k] = imps[0][k]
        ops.append(entry)

    (run_dir / "joint-review.json").write_text(_json.dumps(
        {"schema_version": "1.0.0", "run_id": args.run_id,
         "objects": {"a": "周工作平面迁移质量", "b": "fade-001 本身工作质量"},
         "dims_count": dims_count, "faces": faces}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["joint_review_written"] = str(run_dir / "joint-review.json")
    out["dims_count"] = dims_count

    if ops:
        (run_dir / "opinions.json").write_text(_json.dumps(
            {"schema_version": "2.0.0", "run_id": args.run_id, "source": "loop_joint_review",
             "opinions": ops}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out["opinions_written"] = str(run_dir / "opinions.json")

    # CFO ⓓ/ⓐ/null 升级
    t1 = _dt.datetime.now(_dt.timezone.utc)
    b1 = _deepseek_balance_cny()
    delta = (b0 - b1) if (b0 is not None and b1 is not None) else None
    _write_cost_line(run_dir, {
        "stage": "loop_joint_review", "seats": list(SEATS), "seat_count": len(SEATS),
        "started": t0.isoformat(), "finished": t1.isoformat(),
        "duration_s": round((t1 - t0).total_seconds(), 1),
        "balance_before_cny": b0, "balance_after_cny": b1, "delta_cny": delta,
        "delta_scope": "period_total_all_ds_consumption (CFO note: upper-bound only)",
        "token_fields": "unavailable: dsh headless does not project API usage",
    })
    if _consecutive_null_balance(run_dir) >= 3:
        _msg = ("[cost-guard][ESCALATE CFO+COO] balance unavailable for >=3 consecutive rounds")
        out["cost_guard_warning_balance"] = _msg
        print(_msg, file=sys.stderr)
    if delta is not None and delta > _ROUND_CAP_CNY:
        out["cost_guard_warning"] = "round cost %.2f > %.1f (CFO guard a)" % (delta, _ROUND_CAP_CNY)

    absent = [s for s, f in faces.items() if isinstance(f, dict) and f.get("absent")]
    out["absent_seats"] = absent
    if len(absent) == len(SEATS):
        out["verdict"] = "fail: all seats absent"
        return 2, out
    out["verdict"] = "pass"
    return 0, out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--spawn-timeout", type=int, default=900)
    args = ap.parse_args()
    rc, out = run(args)
    print(_json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
