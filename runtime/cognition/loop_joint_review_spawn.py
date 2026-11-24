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
    "评分依据=run-dir 材料（plan.json/exam.json/score.json/score-skill.json/close.json 等·只读；材料读取一律用 run_dir **绝对路径**·cwd 为隔离沙盒·相对路径不指向 run_dir·DP-019）。\n"
    "只输出一个 JSON 对象（零多余文本）：{\"seat\": \"%s\", "
    "\"dimensions\": [{\"object\": \"a|b\", \"dimension\": \"<部门维度名>\", \"score\": <0-100>, \"rationale\": \"…\"}], "
    "\"improvements\": [{\"title\": \"…\", \"target\": \"<run-dir 内路径>\"或\"<源码路径>\", \"change\": \"…\", \"verify\": \"…\", \"rollback\": \"…\"}]}\n"
    "纪律：dimensions ≥6 条（两对象各 ≥3）；improvements 是可执行改进建议（供下一轮任务书）；每项五字段齐·禁缺字段；禁裸分（rationale 必附）。**禁创建/修改/删除任何文件**（产物=回复 JSON·DP-019）。\n"
    "评分标尺（六档区间+要件法·必守·anchor-table-v1）：\n"
    "- 每维打分须对表落档：L1 0-29 结构性缺失（零要件）／L2 30-49 初步有但不完整／L3 50-69 基本可用（要件过半）／L4 70-84 要件齐／L5 85-94 要件齐+可复算实证锚／L6 95-100 标杆（L5+他席可复用或 CEO 批）\n"
    "- rationale 须写明：①落档依据（该维要件的存在/缺失证据）②档位（L1-L6）③为何非上/下一档\n"
    "- 要件未定义前的维度：按 L1/L2 从紧判（§5.6 规则·不虚高）\n"
    "- score 须落在所报档区间内（如报 L4→score ∈[70,84]）；越区间=评分不合规\n"
    "- L1（0-29 结构性缺失·零要件）与 L2（30-49 初步有但不完整）不得合并计分——零要件 vs 部分要件须可分辨\n"
    "- 六档→要件映射表随锚表同卷（anchor-table-v1）——落档判定以该表为准·不自行改档界\n"
    "- 禁自校准自审计：落档须依要件证据（run-dir 材料）·不得以本席历史分或直觉为档位依据；校准与审计分离（席不自审自席落档）\n"
)

# ── DP-20261123-017 维度冻结（CTO 规格 1b51e7eca）──────────────────────────
# 表件=同目录 fade001-dimensions-v1.json（env FADE001_DIM_TABLE 可覆）；表缺失=回落旧形
# （自创维度+comparability 照记·回滚锚）；表在但 status!=ready 或校验不过=占位期不放行联审（fail-closed skip）。
_DIM_TABLE_ENV = "FADE001_DIM_TABLE"
_DIM_TABLE_DEFAULT = "fade001-dimensions-v1.json"
_SEAT_SCOPES = ("A", "B", "both")


def _load_dimension_table() -> dict | None:
    p = Path(os.environ.get(_DIM_TABLE_ENV, Path(__file__).resolve().parent / _DIM_TABLE_DEFAULT))
    if not p.is_file():
        return None
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 坏表=fail-closed 由调用面拒
        return {"_load_error": f"{type(e).__name__}: {e}"}


def _validate_table(table: dict, seats: tuple) -> list[str]:
    """表 schema 校验（测试案①）：七席全·每席 ≥3 维·id 唯一·object_scope 合法。"""
    errs: list[str] = []
    if not isinstance(table, dict) or table.get("_load_error"):
        return [f"table unreadable: {(table or {}).get('_load_error', 'not a dict')}"]
    tseats = table.get("seats")
    if not isinstance(tseats, dict):
        return ["table.seats missing"]
    seen: set = set()
    for seat in seats:
        sd = tseats.get(seat)
        dims = (sd or {}).get("dimensions") if isinstance(sd, dict) else None
        if not isinstance(dims, list):
            errs.append(f"seat {seat}: dimensions missing")
            continue
        if len(dims) < 3:
            errs.append(f"seat {seat}: {len(dims)} dims (<3)")
        for d in dims:
            if not isinstance(d, dict):
                errs.append(f"seat {seat}: non-dict dimension")
                continue
            for k in ("id", "name", "definition", "object_scope"):
                if not str(d.get(k) or "").strip():
                    errs.append(f"seat {seat}: dim missing {k}")
            did = d.get("id")
            if did in seen:
                errs.append(f"duplicate dimension id: {did}")
            seen.add(did)
            if d.get("object_scope") not in _SEAT_SCOPES:
                errs.append(f"seat {seat} {did}: bad object_scope={d.get('object_scope')!r}")
    return errs


def _constrained_prompt(seat: str, dims: list) -> str:
    lines = [
        f"你是 TriCompany loop 尾段七席联审席之一（{seat.upper()}席·本部门负责人视角）。",
        "本周 fade-001 十段全毕。**只对下列本席冻结维度打分（1-100）·禁止自创维度（越表=整席判废）**：",
    ]
    for d in dims:
        lines.append(f"  - {d['id']} | {d['name']} | {d['definition']} | scope={d['object_scope']}")
    _anchors_in = [d for d in dims if str(d.get("id", "")).startswith("anchor-")]
    if _anchors_in:
        lines.append("【共维锚（全席同评·锚分独立面板·T1/T7）】以下 3 锚亦逐条打分（不与他席互看）：")
        for d in _anchors_in:
            lines.append(f"  - {d['id']} | {d['name']} | {d['definition']} | scope={d['object_scope']}")
    lines.append("评价对象：A=周工作平面迁移质量；B=fade-001 本身工作质量。材料读取一律用 run_dir 绝对路径（cwd 为隔离沙盒·DP-019）。")
    lines.append("scope=both 的维度对 A、B 各打一分；scope=A/B 只打对应对象。")
    lines.append('只输出一个 JSON 对象（零多余文本）：{"seat": "%s", "dimensions": ['
                 '{"dimension_id": "<表内 id>", "object": "A|B", "score": <0-100>}], '
                 '"improvements": [{"title": "...", "dimension_id": "<对应维 id·低分维必填>", '
                 '"target": "<run-dir 内路径或源码路径>", '
                 '"change": "...", "verify": "...", "rollback": "..."}]}' % seat)
    lines.append("【低分维强制改进（CEO 批 2026-11-25·病根修）】**每维 score<70（L1-L3 档）必须产 ≥1 条对应 improvements"
                 "（dimension_id 指向该维·一维一条·逐维对应）**；**条数不限**（取消每席条数上限）——未覆盖低分维=门告警记 uncovered。")
    lines.append("【改进建议（DP-017 追补 2026-11-23·供下一轮任务书）】**improvements ≥1 条·五字段齐**"
                 "（title/target/change/verify/rollback·任一缺=生成器 fail-closed 不派任务书）——"
                 "可为可执行改进或如实写「本席无改进」条（title=no-improvement·change=无·其余指 run_dir 内件）。")
    lines.append("纪律：每条 dimension_id 必须取自本表；score 为 0-100 数字；禁裸分（可附 rationale 可选）。**禁创建/修改/删除任何文件**（产物=回复 JSON·DP-019）。")
    lines.append("评分标尺（六档区间+要件法·必守·anchor-table-v1）：")
    lines.append("- 每维打分须对表落档：L1 0-29 结构性缺失（零要件）／L2 30-49 初步有但不完整／L3 50-69 基本可用（要件过半）／L4 70-84 要件齐／L5 85-94 要件齐+可复算实证锚／L6 95-100 标杆（L5+他席可复用或 CEO 批）")
    lines.append("- rationale 须写明：①落档依据（该维要件的存在/缺失证据）②档位（L1-L6）③为何非上/下一档（dimensions 条目内附 rationale 字段）")
    lines.append("- 要件未定义前的维度：按 L1/L2 从紧判（§5.6 规则·不虚高）")
    lines.append("- score 须落在所报档区间内（如报 L4→score ∈[70,84]）；越区间=评分不合规")
    lines.append("- L1（0-29 结构性缺失·零要件）与 L2（30-49 初步有但不完整）不得合并计分——零要件 vs 部分要件须可分辨")
    lines.append("- 六档→要件映射表随锚表同卷（anchor-table-v1）——落档判定以该表为准·不自行改档界")
    lines.append("- 禁自校准自审计：落档须依要件证据（run-dir 材料）·不得以本席历史分或直觉为档位依据；校准与审计分离（席不自审自席落档）")
    return "\n".join(lines)


def _validate_seat_scores(entries, dims: list) -> tuple[list, list]:
    """输出强校验（测试案②·越表 fail-closed）：返回 (合规格 entries, violations)。
    合规格=dimension_id 在表内 + object 匹配 scope + score 数字 0-100。"""
    by_id = {d.get("id"): d for d in dims if isinstance(d, dict)}
    ok: list = []
    viol: list = []
    for e in entries if isinstance(entries, list) else []:
        if not isinstance(e, dict):
            viol.append("non-dict entry")
            continue
        did = e.get("dimension_id")
        d = by_id.get(did)
        obj = e.get("object")
        sc = e.get("score")
        if d is None:
            viol.append(f"out-of-table dimension_id={did!r}")
            continue
        if obj not in ("A", "B"):
            viol.append(f"{did}: object={obj!r} invalid")
            continue
        scopes = ("A", "B") if d.get("object_scope") == "both" else (d.get("object_scope"),)
        if obj not in scopes:
            viol.append(f"{did}: object={obj} outside scope={d.get('object_scope')}")
            continue
        if not isinstance(sc, (int, float)) or isinstance(sc, bool) or not (0 <= float(sc) <= 100):
            viol.append(f"{did}: score={sc!r} invalid")
            continue
        _entry = {"dimension_id": did, "object": obj, "dimension": d.get("name"), "score": float(sc)}
        # DP-049 勘正（CTO 2026-11-24·核证反转）：本函数**构造新 dict**（非 append 原条目）——
        # rationale 须在此随行携带，否则校验面即丢（两处同修实证）。
        _rat = e.get("rationale")
        if isinstance(_rat, str) and _rat.strip():
            _entry["rationale"] = _rat
        ok.append(_entry)
    return ok, viol


_LOW_DIM_THRESHOLD = 70


def _low_dim_coverage(faces: dict) -> dict:
    """件2（CEO 批）：低分维数 vs 意见数对表——每维<70 须有 dimension_id 对应 improvement。
    返回 {low_dim_count, opinion_count, mapped, uncovered[]}（聚合卷落卷·防再丢）。"""
    lows: list = []
    mapped: set = set()
    opinions = 0
    for seat, f in (faces or {}).items():
        if not isinstance(f, dict) or f.get("absent"):
            continue
        for d in (f.get("dimensions") or []):
            if not isinstance(d, dict):
                continue
            try:
                sc = float(d.get("score"))
            except (TypeError, ValueError):
                continue
            if sc < _LOW_DIM_THRESHOLD:
                lows.append({"seat": seat, "dimension_id": d.get("dimension_id"),
                             "object": d.get("object")})
        for i in (f.get("improvements") or []):
            if isinstance(i, dict):
                opinions += 1
                did = i.get("dimension_id")
                if isinstance(did, str) and did.strip():
                    mapped.add((seat, did.strip()))
    uncovered = [x for x in lows if (x["seat"], x["dimension_id"]) not in mapped]
    return {"low_dim_count": len(lows), "opinion_count": opinions,
            "mapped_low_dims": len(lows) - len(uncovered),
            "uncovered": uncovered[:12]}


def _seat_means(faces: dict) -> dict:
    """mean-of-seat-means（聚合口径·测试案④确定性）：先席内均值·再跨席均值。"""
    a_seat, b_seat = [], []
    for f in faces.values():
        if not isinstance(f, dict) or f.get("absent"):
            continue
        da = [x["score"] for x in (f.get("dimensions") or [])
              if isinstance(x, dict) and x.get("object") == "a"]
        db = [x["score"] for x in (f.get("dimensions") or [])
              if isinstance(x, dict) and x.get("object") == "b"]
        if da:
            a_seat.append(sum(da) / len(da))
        if db:
            b_seat.append(sum(db) / len(db))
    return {"a": round(sum(a_seat) / len(a_seat), 2) if a_seat else None,
            "b": round(sum(b_seat) / len(b_seat), 2) if b_seat else None,
            "seats_a": len(a_seat), "seats_b": len(b_seat)}


# ── DP-036（DP-028 并入·CEO 批 2026-11-23 23:17:50）：联审并行化五项 ──
# ①各席独立产物 opinions-<seat>.json（写面隔离）②joint-review.json 聚合器单写
# ③席对 run_dir 只读（prompt 约定照役）④并发分批 4+3（避 429）⑤FADE_JOINT_PARALLEL=0 回退串行
_JOINT_PARALLEL = os.environ.get("FADE_JOINT_PARALLEL", "1") != "0"
_JOINT_BATCHES = ((0, 4), (4, 7))   # SEATS[0:4] / SEATS[4:7]

# ── v8 item13（CPO spec 7afd95a2a·CTO 令 2026-11-25）：lite 直提模式（态分档审-用配对）──
# 切换点=入口 spawn 读态（round_runner hook 传 --review-mode）·一轮一模式·prod→lite（A/B 达标态由 prod 前置保证）。
# lite：七席各一直提 prompt（条数不限·DCA 差距形优先）·**无维分不进聚合**·锚面板不跑·charter 全纳（item12 律）。
# 回滚：LOOP_JOINT_REVIEW_LITE=0 强制 full（与 LOOP_JOINT_REVIEW 同族）。
_LITE_PROMPT = """你是 TriCompany loop 尾段七席联审席之一（%s席·本部门负责人视角·lite 直提模式）。
本周 fade-001 十段全毕（prod 态·A/B 已达标）。请直接提出改进意见（条数不限·DCA 差距形优先）：

只输出一个 JSON 对象（零多余文本）：{"seat": "%s", "items": [{"claim": "<改进主张>",
  "gap_type": "<未实现|漂移|改进>", "evidence_ref": "<run-dir 内路径>", "fix": "<建议修法>",
  "dimension_id": "<可选·部门维度名>"}]}

纪律：禁输出 dimensions/score 字段（lite 无维分·模式隔离 fail-closed）；每条 claim 与 evidence_ref 非空（双锚）；
材料读取一律用 run_dir 绝对路径（cwd 隔离沙盒·DP-019）；禁创建/修改/删除任何文件（产物=回复 JSON·DP-019）。
"""

_LITE_ITEM_KEYS = ("claim", "gap_type", "evidence_ref", "fix")

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
    base = prompt_override if prompt_override else (_JOINT_PROMPT % (seat.upper(), seat))
    prompt = base + f"run_id={run_id} run_dir={run_dir}\n"
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


def _dimension_sets(jr: dict) -> dict:
    """per-object 维度名集合（可比性系数原料）。"""
    out: dict = {"a": set(), "b": set()}
    for _s, f in (jr.get("faces") or {}).items():
        if not isinstance(f, dict) or f.get("absent"):
            continue
        for x in (f.get("dimensions") or []):
            if isinstance(x, dict) and x.get("object") in ("a", "b"):
                out[x["object"]].add(str(x.get("dimension")))
    return out


def _comparability_coefficient(run_dir: Path, jr: dict) -> dict:
    """可比性系数（CTO 裁 2026-11-23·附卷不并入判级）：本轮 vs 最近一轮的 per-object
    维度名 Jaccard（交集/并集）。LLM 每轮自创维度名 ⇒ 系数低=跨轮绝对值近乎不可比，
    判级读档位/趋势；系数=分析材料，不入评分。"""
    try:
        parent = run_dir.resolve().parent
        cands = [p for p in parent.iterdir()
                 if p.is_dir() and p.resolve() != run_dir.resolve()
                 and (p / "joint-review.json").is_file()]
        if not cands:
            return {"prev_run": None, "note": "no previous round to compare"}
        # 前轮取序（CTO 建议 2026-11-23·当日外部件 mtime 污染教训应用）：
        # 优先按目录名内 runId 时戳（不可外写伪造的时序锚）·不可解析才回落 mtime。
        import re as _re
        from datetime import datetime as _dtm

        def _round_order_key(pp: Path):
            m = _re.search(r"(\d{8}T\d{6}Z)$", pp.name)
            if m:
                try:
                    return (1, _dtm.strptime(m.group(1), "%Y%m%dT%H%M%SZ").timestamp())
                except ValueError:
                    pass
            return (0, (pp / "joint-review.json").stat().st_mtime)

        prev = max(cands, key=_round_order_key)
        prev_jr = _json.loads((prev / "joint-review.json").read_text(encoding="utf-8"))
        # DP-20261123-017：同表版本 comparability 恒 1.0（维度冻结后尺子同源·工具自动证实）
        cur_ver = jr.get("dimension_table_version") or "legacy"
        prev_ver = prev_jr.get("dimension_table_version") or "legacy"
        if cur_ver != "legacy" and cur_ver == prev_ver:
            return {"prev_run": prev.name, "jaccard_a": 1.0, "jaccard_b": 1.0,
                    "dimension_table_version": cur_ver,
                    "note": "same dimension-table version => comparability 1.0 by construction"}
        cur, old = _dimension_sets(jr), _dimension_sets(prev_jr)

        def _jac(x: set, y: set):
            if not x or not y:
                return None
            return round(len(x & y) / len(x | y), 4)

        return {"prev_run": prev.name,
                "jaccard_a": _jac(cur["a"], old["a"]),
                "jaccard_b": _jac(cur["b"], old["b"]),
                "note": "dimension-name Jaccard vs previous round; analysis only, not in scoring"}
    except Exception as e:  # noqa: BLE001 — 附卷面零阻断
        return {"error": f"{type(e).__name__}: {e}"}


def _run_lite(args: argparse.Namespace, run_dir: Path, out: dict) -> tuple[int, dict]:
    """v8 item13 lite 直提（CPO spec）：七席各一直提·无维分不进聚合·双锚 fail-closed·全纳映射 opinions.json。"""
    def _one(seat: str):
        r = _spawn_seat(seat, run_dir, args.run_id, timeout_s=args.spawn_timeout,
                        prompt_override=_LITE_PROMPT % (seat.upper(), seat))
        sheet = _extract_json(r["out"]) if r["rc"] == 0 else None
        if not isinstance(sheet, dict):
            return seat, {"absent": True, "rc": r["rc"], "err": r.get("err")}
        # 断言1（模式隔离）：lite 产物含 dimensions/score=fail-closed 拒
        if "dimensions" in sheet or "score" in sheet:
            return seat, {"absent": True, "reason": "lite 产物含 dimensions/score（模式隔离拒）"}
        items = [i for i in (sheet.get("items") or []) if isinstance(i, dict)]
        ok_items = []
        for i in items:
            # 断言2（双锚）：claim+evidence_ref 非空
            if all(isinstance(i.get(k), str) and i.get(k, "").strip()
                   for k in ("claim", "evidence_ref")):
                ok_items.append(i)
        if not ok_items:
            return seat, {"absent": True, "reason": "双锚缺（claim/evidence_ref 空）·fail-closed"}
        return seat, {"items": ok_items}

    faces: dict = {}
    if _JOINT_PARALLEL:
        from concurrent.futures import ThreadPoolExecutor
        for lo, hi in _JOINT_BATCHES:
            batch = [s for s in SEATS[lo:hi]]
            if not batch:
                continue
            with ThreadPoolExecutor(max_workers=len(batch)) as ex:
                for seat, face in ex.map(lambda s: _one(s), batch):
                    faces[seat] = face
    else:
        for seat in SEATS:
            s_, f_ = _one(seat)
            faces[seat] = f_
    out["faces"] = faces

    # opinions-lite.json + 全纳映射 opinions.json（schema 2.0.0·charter 直取）
    import datetime as _dt13
    lite_doc = {"schema_version": "1.0.0", "run_id": args.run_id,
                "seats": {s: (f.get("items") if isinstance(f, dict) else []) for s, f in faces.items()}}
    (run_dir / "opinions-lite.json").write_text(
        _json.dumps(lite_doc, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    ops = []
    total = 0
    for seat, f in faces.items():
        if not isinstance(f, dict) or f.get("absent"):
            continue
        for idx, it in enumerate(f.get("items") or []):
            total += 1
            ops.append({
                "opinion_id": f"{seat}-{idx}", "seat": seat, "owner_seat": seat,
                "title": it.get("claim"),
                "target": it.get("evidence_ref"),
                "change": it.get("fix") or "（lite 未附具体修法）",
                "verify": f"gap_type={it.get('gap_type')}; evidence={it.get('evidence_ref')}",
                "rollback": "不适用（lite 直提·非施工令）",
                "check_time": _dt13.datetime.now(_dt13.timezone.utc).isoformat(),
            })
    if ops:
        (run_dir / "opinions.json").write_text(_json.dumps(
            {"schema_version": "2.0.0", "run_id": args.run_id, "source": "loop_joint_review_lite",
             "opinions": ops}, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        out["opinions_written"] = str(run_dir / "opinions.json")

    jr_doc = {"schema_version": "1.0.0", "run_id": args.run_id,
              "objects": {"a": "周工作平面迁移质量", "b": "fade-001 本身工作质量"},
              "review_mode": "lite", "opinions_total": total,
              "dims_count": {"a": 0, "b": 0},
              "faces": faces,
              "low_dim_coverage": _low_dim_coverage(faces),
        "anchor_dimensions": {"agg_version": "1.0.0", "dim_ids": [], "per_seat": {},
                                    "spread": {}, "note": "lite 模式不跑锚面板（spec §五）"},
              "comparability": {"prev_run": None, "note": "lite: no dimension scores (not comparable)"},
              "check_time": _dt13.datetime.now(_dt13.timezone.utc).isoformat()}
    (run_dir / "joint-review.json").write_text(
        _json.dumps(jr_doc, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    out["joint_review_written"] = str(run_dir / "joint-review.json")
    out["opinions_total"] = total
    absent = [s for s, f in faces.items() if isinstance(f, dict) and f.get("absent")]
    out["absent_seats"] = absent
    if len(absent) == len(SEATS):
        out["verdict"] = "fail: lite all seats absent"
        return 2, out
    out["verdict"] = "pass"
    return 0, out


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

    # DP-20261123-017 维度冻结：表载入+校验；表在但非 ready/校验不过=占位期不放行联审（fail-closed）
    table = _load_dimension_table()
    table_dims: dict = {}
    anchor_by_id: dict = {}
    table_version = "legacy"
    if table is not None:
        tbl_errs = _validate_table(table, SEATS)
        tbl_status = str(table.get("status") or "")
        table_version = str(table.get("table_version") or table.get("version") or "unknown")
        out["dimension_table"] = {"version": table_version, "status": tbl_status,
                                  "errors": tbl_errs[:10]}
        if tbl_errs or tbl_status != "ready":
            out["verdict"] = ("skipped: dimension table not ready "
                              f"(status={tbl_status!r}, errors={len(tbl_errs)}) — review not released")
            return 3, out
        _anchors = [a for a in (table.get("anchor_dimensions") or []) if isinstance(a, dict)]
        out["anchor_table"] = {"dim_ids": [a.get("id") for a in _anchors], "count": len(_anchors)}
        for seat in SEATS:
            table_dims[seat] = ([d for d in (table.get("seats", {}).get(seat, {}).get("dimensions") or [])
                                 if isinstance(d, dict)] + _anchors)
        anchor_by_id = {a.get("id"): a for a in _anchors}
    out["dimension_table_version"] = table_version
    # v8 item13：lite 直提模式早分派（switch点=入口·一轮一模式·LOOP_JOINT_REVIEW_LITE=0 强制 full）
    _mode = (getattr(args, "review_mode", "full") if os.environ.get("LOOP_JOINT_REVIEW_LITE", "1") != "0" else "full")
    out["review_mode"] = _mode
    if _mode == "lite":
        return _run_lite(args, run_dir, out)

    def _run_one(seat: str) -> tuple[str, dict]:
        dims = table_dims.get(seat)
        r = _spawn_seat(seat, run_dir, args.run_id, timeout_s=args.spawn_timeout,
                        prompt_override=(_constrained_prompt(seat, dims) if dims else None))
        sheet = _extract_json(r["out"]) if r["rc"] == 0 else None
        if dims is not None:
            # 冻结表形：强校验（越表 fail-closed·零合规条目=整席判废）
            ok_entries, viol = (_validate_seat_scores(sheet.get("dimensions"), dims)
                                if sheet else ([], ["unparsable"]))
            _aid = set(anchor_by_id.keys())
            # DP-049（CTO 令 2026-11-24）：rationale 聚合透传——席面 rationale（非空 str）随条目入
            # joint-review dims（_seat_means/AB 聚合不读 rationale=零影响·SDE 已核）
            def _extra(e: dict) -> dict:
                r = e.get("rationale")
                return {"rationale": r} if isinstance(r, str) and r.strip() else {}
            norm = [{**{"object": e["object"].lower(), "dimension": e["dimension"],
                        "score": e["score"], "dimension_id": e["dimension_id"]}, **_extra(e)}
                    for e in ok_entries if e["dimension_id"] not in _aid]
            anchor_norm = [{**{"object": e["object"].lower(), "dimension_id": e["dimension_id"],
                               "score": e["score"]}, **_extra(e)}
                           for e in ok_entries if e["dimension_id"] in _aid]
            # R10 追补：constrained 路径须携带 improvements（生成器输入契约）
            imps = [i for i in (sheet.get("improvements") or []) if isinstance(i, dict)] if sheet else []
            face: dict = {"dimensions": norm, "anchor_scores": anchor_norm,
                          "violations": viol[:20], "improvements": imps}
            if not norm:
                face["absent"] = True
                face["reason"] = "no valid in-table scores (fail-closed)"
            return seat, face
        if sheet and isinstance(sheet.get("dimensions"), list):
            return seat, sheet
        return seat, {"absent": True, "rc": r["rc"], "raw_out": r["out"][-60000:], "err": r["err"]}

    # ── DP-036 ④并发分批（4+3·避 429）／⑤FADE_JOINT_PARALLEL=0 串行回退 ──
    faces: dict = {}
    if _JOINT_PARALLEL:
        from concurrent.futures import ThreadPoolExecutor
        for lo, hi in _JOINT_BATCHES:
            batch = [s for s in SEATS[lo:hi]]
            if not batch:
                continue
            with ThreadPoolExecutor(max_workers=len(batch)) as ex:
                for seat, face in ex.map(lambda s: _run_one(s), batch):
                    faces[seat] = face
    else:
        for seat in SEATS:
            seat_, face = _run_one(seat)
            faces[seat_] = face
    out["parallel"] = bool(_JOINT_PARALLEL)
    out["faces"] = faces

    # ── DP-036 ①各席独立产物 opinions-<seat>.json（写面隔离·joint-review 聚合器单写②）──
    for seat, face in faces.items():
        try:
            (run_dir / f"opinions-{seat}.json").write_text(_json.dumps(
                {"schema_version": "2.0.0", "seat": seat,
                 "face": face if not isinstance(face, dict) or face.get("absent") else
                 {"dimensions": face.get("dimensions") or [],
                  "improvements": face.get("improvements") or [],
                  "violations": face.get("violations") or []}},
                ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — 单席产物失败不阻聚合
            print(f"[joint-review][WARN] opinions-{seat}.json write failed: {type(e).__name__}: {e}",
                  file=sys.stderr)

    # ── 联审读数卷 + opinions（schema 2.0.0·improvements 五字段→生成器）──
    dims_count = {"a": 0, "b": 0}
    ops = []
    for s, f in faces.items():
        if not isinstance(f, dict) or f.get("absent"):
            continue
        for d in (f.get("dimensions") or []):
            if isinstance(d, dict) and d.get("object") in ("a", "b"):
                dims_count[d["object"]] += 1
        # DP-035（COS 2026-11-23）：improvements 逐条补 owner_seat（五→六字段·生成器透传位）
        imps = [{**i, "owner_seat": s} for i in (f.get("improvements") or [])
                if isinstance(i, dict) and all(isinstance(i.get(k), str) and i.get(k, "").strip()
                                               for k in ("title", "target", "change", "verify", "rollback"))]
        entry = {"opinion_id": f"{s}-1", "seat": s, "owner_seat": s,   # R10-CHO-01：owner_seat 枚举席位面
                 "scores": {d.get("dimension"): d.get("score")
                 for d in (f.get("dimensions") or []) if isinstance(d, dict)},
                 "summary": " | ".join(f"{d.get('object')}:{d.get('dimension')}" for d in (f.get("dimensions") or [])[:3] if isinstance(d, dict)),
                 "check_time": None}
        if imps:
            for k in ("title", "target", "change", "verify", "rollback", "owner_seat"):
                if k in imps[0]:
                    entry[k] = imps[0][k]
            if isinstance(imps[0].get("covered_dims"), list):   # T1② 覆盖校验原料透传
                entry["covered_dims"] = imps[0]["covered_dims"]
        ops.append(entry)

    jr_doc = {"schema_version": "1.0.0", "run_id": args.run_id,
              "objects": {"a": "周工作平面迁移质量", "b": "fade-001 本身工作质量"},
              "review_mode": "full", "opinions_total": len(ops),
              "dims_count": dims_count, "faces": faces,
              "low_dim_coverage": _low_dim_coverage(faces),   # 件2：低分维数 vs 意见数对表
              # DP-20261123-017：表版本入卷（同版本 comparability 恒 1.0·v1→v2 历史标版本）
              "dimension_table_version": table_version,
              "seat_means": _seat_means(faces)}
    # ── T1/T7（任务书 v2·CTO 技术形 02:06）：锚维独立面板（main 聚合零动·不入判级）──
    _anchor_dim_ids = [a.get("id") for a in (anchor_by_id.values() if anchor_by_id else [])]
    per_seat_anchor: dict = {}
    _spread: dict = {}
    if _anchor_dim_ids:
        for seat, face in faces.items():
            if not isinstance(face, dict) or face.get("absent"):
                continue
            for e in (face.get("anchor_scores") or []):
                per_seat_anchor.setdefault(seat, {}).setdefault(e["dimension_id"], {})[e["object"]] = e["score"]
        for aid in _anchor_dim_ids:
            vals = {ob: [v[aid][ob] for v in per_seat_anchor.values()
                         if aid in v and ob in v[aid]]
                    for ob in ("a", "b")}
            spreads = [max(xs) - min(xs) for xs in vals.values() if xs]
            if spreads:
                _spread[aid] = max(spreads)
        for aid, sp in _spread.items():
            if sp > 30:
                print(f"[joint-review][WARN] anchor spread>30: {aid} spread={sp}（校准信号·零阻断·T1/T7）", file=sys.stderr)
    jr_doc["anchor_dimensions"] = {
        "agg_version": "1.0.0",
        "dim_ids": _anchor_dim_ids,
        "per_seat": per_seat_anchor,
        "spread": _spread,
        "note": "anchor panel independent from main aggregation (not in scoring)",
    }
    # CTO 裁 2026-11-23：可比性系数随卷落（附卷不并入判级）
    jr_doc["comparability"] = _comparability_coefficient(run_dir, jr_doc)
    (run_dir / "joint-review.json").write_text(
        _json.dumps(jr_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["joint_review_written"] = str(run_dir / "joint-review.json")
    out["dims_count"] = dims_count
    out["comparability"] = jr_doc["comparability"]

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
    ap.add_argument("--review-mode", choices=("full", "lite"), default="full",
                    help="v8 item13：full=七席全维（默认）·lite=直提模式（prod·hook 传态）")
    args = ap.parse_args()
    rc, out = run(args)
    print(_json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
