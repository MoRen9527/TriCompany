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
    "\"items\": [{\"item_id\": \"...\", \"desc\": \"...\", \"status\": \"planned\"}]}, ...], \"bidirectional_ok\": true, "
    "\"agent_readings\": [{\"agent\": \"...\", \"action\": \"...\", \"domain\": \"<tree|top_level|其它>\", "
    "\"disposition\": \"<migrate|keep|carry|pending_ledger|dead_letter>\", "
    "\"sanction\": \"<迁|留|封（domain=top_level 件必填）>\", "
    "\"rationale\": \"<非空理由>\", \"evidence_ref\": [\"plan.json\"]}, ...], \"check_time\": \"<UTC ISO>\"}\n"
    "（v7 契约注：verdict 必为 \"pass\"（verify 毒化拦）；counts 必为 dict 且 migrate/keep/carry_over/top_level 四键齐；三数组与 counts 对账一致。）\n"
    "【plan 契约硬规格（DP-20261123-013·从 plan_scope.py/verify.py 校验器反向提取·八条全集·prompt 即校验器镜像）】\n"
    " 1) agent_readings[].disposition ∈ {migrate, keep, carry, pending_ledger, dead_letter}（**五态·含 dead_letter**）；\n"
    " 2) agent_readings[] **非空**且每条 **domain 必填非空**、∈ {tree, top_level}（决定归属域·缺 domain=归不进任何域）；\n"
    " 3) domain=top_level 的件必带 sanction ∈ {迁, 留, 封}（三态红闸·缺/越域=红停）；\n"
    " 4) agent_readings[].**annotation/rationale 必须非空字符串** + **evidence_ref 必须非空数组**（如 [\"plan.json\"]·**字符串形亦红**）——三件套任一空/缺=WP1 毒化红停；\n"
    " 4b) 顶层键全集必含：plan_version/run_id/from_week/to_week/migrate/keep/carry_over/counts/**bidirectional_ok**/check_time，且 **bidirectional_ok 必为 true**（除非 verdict=\"fail\"）；\n"
    " 5) 【对账显式规则·R1】readings[].domain 决定归属域——counts.migrate + counts.keep 必须 == domain=tree 的 readings 条数；\n"
    " 6) 【对账显式规则·R2】counts.top_level 必须 == domain=top_level 的 readings 条数——逐域必须相等；\n"
    " 7) verdict 必为 \"pass\"；\n"
    " 8) counts.migrate == len(migrate) ∧ counts.keep == len(keep) ∧ counts.carry_over == len(carry_over)；counts 四键齐。\n"
    " 反例（禁）：disposition 写 \"pending_review\"/\"seal\" 等自创值 / top_level 件漏 sanction / counts 与数组长度不符 / "
    "对账差额（如 counts.migrate+keep=3 而 domain=tree 的 readings 只有 0 条）/ **readings 留空或 domain 缺失**（对账域缺位=绕账面·双条件拒）"
    "——任一命中=verify 毒化红停·白跑一整轮。\n"
    "纪律：只读材料零写入（**禁创建/修改/删除任何文件**——产物=回复 JSON 文本·由调用方落盘·DP-019）·evidence_ref 指 run-dir 内件（材料读取一律用 run_dir **绝对路径**·cwd 为隔离沙盒·DP-019）·families 非空·每族 items 非空；"
    "禁裸结论（rationale 必附）。\n"
    "【出题职能（CEO 任务书 v7·12 类语义依据）】同轮须产考卷 exam 段（顶层 key，与 plan 同 JSON 返回）：\n"    "{\"exam\": {\"schema_version\": \"1.0.0\", \"objective\": [{\"id\": \"O1\", \"dimension\": \"<12类之一>\", \"assertion\": \"<机器可判断言>\", \"weight\": 5}], \"subjective\": [{\"id\": \"S1\", \"dimension\": \"<12类之一>\", \"question\": \"<主观题>\", \"rubric\": \"<判据>\", \"weight\": 10}]}}\n"    "出题规则：objective=可程序判（断言须机器可验·供段 6 score_cli）；subjective=需 agent 判（供段 7 两席）；各 ≥3 题·weight 正整数·题目须贴本周实际工作形态；出卷≠改卷·轮内锁卷。\n"
    "【objective 断言硬规格（DP-20261123-010·CTO 裁 a 案）】objective[].assertion 必须以以下三式前缀之一开头（判分器仅识别这三式）：\n"
    "  1) path_exists:<相对 run-dir 的路径>   例：path_exists:plan.json\n"
    "  2) json_field:<file>::<dotted.path>::<op>:<value>   op ∈ eq|ne|exists|contains   例：json_field:plan.json::verdict::eq:pass\n"
    "  3) regex:<file>::<pattern>   例：regex:plan.json::\\\"families\\\"\n"
    "  反例（禁）：「plan.json 为 JSON 对象且含 verdict 字段」——自由文本→判分器 skipped→白出题。\n"
    "职责分野：**无法机判的检查项一律放 subjective（段 7 两席判）·不许塞 objective 自由文本**。\n"
    "出题自检：出完 objective 逐条核对三式前缀命中率——零命中必须在你的输出 JSON 之外不追加任何声明（自检由调用方机械复核并 warn）。\n"
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


_DISPOSITIONS5 = ("migrate", "keep", "carry", "pending_ledger", "dead_letter")
_SANCTIONS3 = ("迁", "留", "封")


def _readings_violations(sheet: dict) -> list[str]:
    """DP-20261123-013 自纠检出（照校验器实锚 plan_scope.py L900）：返回非法值清单（空=合规）。
    只判显式错值；disposition/sanction 缺键=None 宽容（旧形容忍）。"""
    viol: list[str] = []
    readings = sheet.get("agent_readings")
    # CTO 双条件（2026-11-23·防「不产 readings」绕账——verify 缺位 skip 不红，故此处必须拦）：
    # readings 非空 + 每条 domain 非空且 ∈ {tree, top_level}
    if not isinstance(readings, list) or len(readings) == 0:
        return ["agent_readings missing/empty (reconciliation-domain absent = bypass attempt)"]
    for i, r in enumerate(readings):
        if not isinstance(r, dict):
            continue
        dm = r.get("domain")
        if not isinstance(dm, str) or not dm.strip():
            viol.append(f"agent_readings[{i}].domain empty (required for reconciliation)")
        elif dm not in ("tree", "top_level"):
            viol.append(f"agent_readings[{i}].domain={dm!r} not-in tree/top_level")
        d = r.get("disposition")
        if d is not None and d not in _DISPOSITIONS5:
            viol.append(f"agent_readings[{i}].disposition={d!r} non-five-state")
        # 零 null 面（#4·probe2 实锤：LLM 会留空 evidence_ref → WP1 毒化拦）
        # 09 扩（校验器全量对齐·_structure_gate 实锚）：annotation/rationale 非空 str +
        # evidence_ref 必须**非空列表**（str 形亦红·plan_scope 要求 list）
        for k in ("annotation", "rationale"):
            v = r.get(k)
            if not (isinstance(v, str) and v.strip()):
                viol.append(f"agent_readings[{i}].{k} empty (zero-null face)")
        ev = r.get("evidence_ref")
        if not (isinstance(ev, list) and ev):
            viol.append(f"agent_readings[{i}].evidence_ref not non-empty list (zero-null face)")
        if dm == "top_level":
            s = r.get("sanction")
            if s is not None and s not in _SANCTIONS3:
                viol.append(f"agent_readings[{i}].sanction={s!r} not-in 迁/留/封")
    return viol


_PLAN_REQUIRED_KEYS = (
    "plan_version", "run_id", "from_week", "to_week",
    "migrate", "keep", "carry_over", "counts",
    "bidirectional_ok", "check_time",
)


def _plan_level_violations(sheet: dict) -> list[str]:
    """顶层键+bidirectional_ok 自纠检出（DP-013 09 扩·_structure_gate 实锚）。"""
    viol: list[str] = [f"missing required key: {k}" for k in _PLAN_REQUIRED_KEYS if k not in sheet]
    if sheet.get("bidirectional_ok") is not True and sheet.get("verdict") != "fail":
        viol.append("bidirectional_ok!=true and verdict!=fail (contradiction)")
    return viol


_SEAT_SANDBOX_ROOT_ENV = "FADE_SEAT_SANDBOX_ROOT"


def _seat_sandbox() -> Path:
    """DP-20261123-019（CTO 规格①b·seat 工具面治理）：席进程 cwd 限 sandbox 目录——
    席侧任何写入不落链 run_dir（产物只由 stage 写·防自检件污染）。env 可指定根。"""
    import tempfile
    root = os.environ.get(_SEAT_SANDBOX_ROOT_ENV) or tempfile.gettempdir()
    return Path(tempfile.mkdtemp(prefix="fade-seat-sandbox-", dir=root))


def _spawn_seat(seat: str, run_dir: Path, run_id: str, timeout_s: int = 900,
                extra_hint: str = "") -> dict:
    prompt = _PLAN_PROMPT_HEAD % seat.upper() + f"run_id={run_id} run_dir={run_dir}\n" + extra_hint
    dsh_bin = os.environ.get("DSH_BIN", "/srv/fleet/dsh/node_modules/.bin/dsh")
    overlay = os.environ.get(
        "DSH_PRESET_OVERLAY", "/home/fleet/.dsh/patches/headless-agentpresets-overlay.yml")
    cmd = [dsh_bin, "--profile", "headless"]
    if overlay and os.path.isfile(overlay):
        cmd += ["--patch", overlay]
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout_s, cwd=str(_seat_sandbox()))
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
    # DP-20261123-013 自纠重试一层（CTO 裁②·COO 派工）：非法值→带纠正提示重试一次；
    # 第二次仍非法=fail 如实（fail-closed 不造假·段 3 早停省整轮白跑）。
    out["self_correct"] = {"retried": False}
    if sheet is not None:
        _viol = _plan_level_violations(sheet) + _readings_violations(sheet)
        if _viol:
            _hint = ("\n【自纠重试】上次输出存在非法值：" + "; ".join(_viol[:6])
                     + "。disposition 必须 ∈ {migrate,keep,carry,pending_ledger,dead_letter}；"
                       "domain=top_level 件 sanction 必须 ∈ {迁,留,封}。"
                       "请重新输出完整 JSON（plan+exam），不得沿用非法值。\n")
            r = _spawn_seat(seat, run_dir, args.run_id + "-retry1",
                            timeout_s=args.spawn_timeout, extra_hint=_hint)
            sheet2 = _extract_json(r["out"]) if r["rc"] == 0 else None
            out["self_correct"] = {"retried": True, "violations_first": _viol[:6]}
            if sheet2 is not None:
                sheet = sheet2
            _viol2 = (_plan_level_violations(sheet) + _readings_violations(sheet)) \
                if sheet is not None else ["retry_unparsable"]
            if _viol2:
                out["self_correct"]["violations_after"] = _viol2[:6]
                out["verdict"] = "fail: self-correct retry exhausted (violations remain)"
                return 2, out

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
    # DP-20261123-010 出题自检（CTO 裁 a 案 ④）：objective 三式前缀命中率——零命中 stderr warn（不改行为）
    try:
        import re as _re
        _objs = (exam.get("objective") or []) if isinstance(exam, dict) else []
        _hits = sum(1 for it in _objs
                    if isinstance(it, dict)
                    and _re.match(r"^(path_exists:|json_field:|regex:)",
                                  str(it.get("assertion") or "").strip()))
        out["exam_prefix_hits"] = {"hits": _hits, "total": len(_objs)}
        if _objs and _hits == 0:
            print(f"[plan-skill][WARN] objective 三式前缀命中 0/{len(_objs)}"
                  " —— 判分器将全 skipped（DP-010 自检）", file=sys.stderr)
    except Exception as _e:  # noqa: BLE001 — 自检面零阻断
        print(f"[plan-skill][WARN] prefix self-check failed: {type(_e).__name__}: {_e}", file=sys.stderr)
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
