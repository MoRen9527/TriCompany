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
    "【patrol_plan 硬规格（CEO 6 分钟拍读令·不可改）】plan 必带 patrol_plan.cadence_layers："
    "{\"bod_patrol\": {\"cadence\": \"6m\"}, \"duty_patrol\": {\"cadence\": \"15m\"}, "
    "\"note\": \"两节律不混·H 判据按 seat 比同名层\"}（bod_patrol.cadence=\"6m\" 固定·缺=gate fail）\n"
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


# ── DP-20261123-020（CTO 裁·resume6 真因=max-tokens 16384 截断）──
# 拆分生成：plan-only / exam-only 两次 spawn 各半输出预算；env FADE_PLAN_EXAM_SPLIT=0 回退单 spawn 旧形。
# 输出精简：两 prompt 均要求「单 JSON·直出·极简（无缩进/无空行）·禁解释/禁长推理展开」
# （reasoning 系模型行为不可完全控=如实；JSON 精简=可控面）。
PLAN_EXAM_SPLIT = os.environ.get("FADE_PLAN_EXAM_SPLIT", "1") != "0"
_OUTPUT_FORM = ("\n【输出形态（DP-020）】输出必须为**单个 JSON 对象·直接给最终 JSON**——"
                "JSON 极简（无缩进/无空行/无注释/无冗余字段）；禁解释性叙述；禁长推理展开（reasoning 预算优先留给 JSON 本体）。\n")

_PLAN_ONLY_PROMPT = _PLAN_PROMPT_HEAD.split("【出题职能")[0].rstrip() + "\n" + _OUTPUT_FORM

_EXAM_PROMPT_HEAD = (
    "你是 TriCompany 出题席（%s席·考卷专产）。基于 run-dir 材料与 plan.json（可读全文·绝对路径）出考卷，"
    "同轮只产 exam 段 JSON：\n"
    "{\"exam\": {\"schema_version\": \"1.0.0\", \"objective\": [{\"id\": \"O1\", \"dimension\": \"<12类之一>\", \"assertion\": \"<机器可判断言>\", \"weight\": 5}], "
    "\"subjective\": [{\"id\": \"S1\", \"dimension\": \"<12类之一>\", \"question\": \"<主观题>\", \"rubric\": \"<判据>\", \"weight\": 10}]}}\n"
    "出题规则：objective=可程序判（断言须机器可验·供段 6 score_cli）；subjective=需 agent 判（供段 7 两席）；各 ≥3 题·weight 正整数·题目须贴本周实际工作形态；出卷≠改卷·轮内锁卷。\n"
    "【objective 断言硬规格（DP-20261123-010·CTO 裁 a 案）】objective[].assertion 必须以以下三式前缀之一开头（判分器仅识别这三式）：\n"
    "  1) path_exists:<相对 run-dir 的路径>   例：path_exists:plan.json\n"
    "  2) json_field:<file>::<dotted.path>::<op>:<value>   op ∈ eq|ne|exists|contains   例：json_field:plan.json::verdict::eq:pass\n"
    "  3) regex:<file>::<pattern>   例：regex:plan.json::\\\"families\\\"\n"
    "  反例（禁）：「plan.json 为 JSON 对象且含 verdict 字段」——自由文本→判分器 skipped→白出题。\n"
    "职责分野：**无法机判的检查项一律放 subjective（段 7 两席判）·不许塞 objective 自由文本**。\n"
    "出题自检：出完 objective 逐条核对三式前缀命中率（自检由调用方机械复核并 warn）。\n"
    "【读取面限定（DP-020 追补 a·CTO 裁 2026-11-23）】**只读 plan.json、score.json、verify.json 等 ≤5 个文件**；"
    "**禁读源码文件（score_engine.py 等）·禁运行代码/命令（python 探索等）**；**工具调用 ≤10 次**；尽快直出最终 JSON。\n"
    "纪律：只读材料零写入（**禁创建/修改/删除任何文件**——产物=回复 JSON·DP-019）·材料读取一律用 run_dir **绝对路径**（cwd 隔离沙盒·DP-019）。\n"
    + _OUTPUT_FORM
)


_OWNER_PLACEHOLDERS = ("", "TBD", "TODO", "多席", "all", "ALL")
# b 案扩（CTO 令 2026-11-25）：显式缺省标记集（strip 小写比对）——命中=该字段 pass（两态）
_DEFAULT_MARKERS = {"", "unassigned", "tbd", "todo", "待定"}


_FAMILY_ITEM_FIELDS = ("owner", "due", "acceptance", "depends_on")


def _collect_unassigned(plan_doc: dict) -> list[dict]:
    """item3 b 案（CTO 令 2026-11-25）：owner=='unassigned'（显式）项收集落卷——
    plan.unassigned_items=[{item_id, family_id, target}]（run 内可查·候责任席认领）。"""
    out: list[dict] = []
    for f in plan_doc.get("families") or []:
        if not isinstance(f, dict):
            continue
        fid = f.get("family_id")
        for it in f.get("items") or []:
            if not isinstance(it, dict):
                continue
            if str(it.get("owner") or "").strip().lower() == "unassigned":
                out.append({"item_id": it.get("item_id"),
                            "family_id": fid,
                            "target": it.get("target") or it.get("item_id")})
    plan_doc["unassigned_items"] = out
    return out


def _validate_families_fields(plan_doc: dict) -> list[str]:
    """R12 item3（CEO 批·b 案扩 2026-11-25）：**四字段全两态**——
    显式缺省标记集 `{None,"","unassigned","TBD","tbd","todo","待定"}`（strip 小写）=该字段 pass；
    有值→须有效（owner/due/acceptance 非空且非扩展占位；depends_on 须 list）。"""
    bad: list[str] = []
    for f in plan_doc.get("families") or []:
        if not isinstance(f, dict):
            continue
        for it in f.get("items") or []:
            if not isinstance(it, dict):
                continue
            iid = it.get("item_id") or "?"
            for k in ("owner", "due", "acceptance"):
                v = it.get(k)
                if v is None:
                    continue                                   # 缺省态 pass
                sv = str(v).strip()
                if sv.lower() in _DEFAULT_MARKERS:
                    continue                                   # 显式缺省标记 pass
                if not sv or sv in ("多席", "all", "ALL"):
                    bad.append(f"item3: {iid} {k} 有值但无效（扩展占位 {v!r}）")
            dv = it.get("depends_on")
            if dv is None:
                continue                                       # 缺省态 pass
            if isinstance(dv, str) and dv.strip().lower() in _DEFAULT_MARKERS:
                continue                                       # 字符串缺省标记 pass
            if not isinstance(dv, list):
                bad.append(f"item3: {iid} depends_on 有值但非列表（{type(dv).__name__}）")
    return bad


def _r12_target_set(owner_map: dict) -> set:
    """R12 覆盖集（CTO 扩令 2026-11-25）：families_items_4fields/by_target/raci 串里的 target 集合。"""
    s: set = set()
    for k in (owner_map or {}).get("by_family_target") or {}:
        if ":" in str(k):
            s.add(str(k).split(":", 1)[1])
    for k in (owner_map or {}).get("by_target") or {}:
        s.add(str(k))
    for k in (owner_map or {}).get("by_target_meta") or {}:
        s.add(str(k))
    return s


def _validate_raci(plan_doc: dict, r12_targets: set | None = None) -> list[str]:
    """R12 item6 覆盖率形（CTO 令 2026-11-25·删固定 36）：键数 ≥ families items 总 +
    每 item 有对应 RACI 键（覆盖断言·A/R 必填·C/I 列表形值合法）。"""
    bad: list[str] = []
    raci = ((plan_doc.get("staffing") or {}).get("raci")
            if isinstance(plan_doc.get("staffing"), dict) else None)
    items_total = 0
    need_keys: list[str] = []
    for f in plan_doc.get("families") or []:
        if not isinstance(f, dict):
            continue
        for it in f.get("items") or []:
            if not isinstance(it, dict):
                continue
            items_total += 1
            key = str(it.get("target") or it.get("item_id") or "")
            if key:
                need_keys.append(key)
    if not isinstance(raci, dict):
        return [f"item6: staffing.raci 缺席（items 总 {items_total}·覆盖断言不可判）"]
    if r12_targets is None and len(raci) < items_total:
        # 旧调用面（无 R12 集）：总数覆盖判据保留
        bad.append(f"item6: RACI 键数 {len(raci)} < items 总 {items_total}（覆盖不足=fail）")
    # 扩令（CTO 2026-11-25）：**R12 覆盖集内件须有键**（fail）；R12 外件→no-raci-mapping 注（非 fail）。
    # r12_targets=None（旧调用面）=全须有键（兼容旧测）。
    missing_cov: list[str] = []
    notes: list[str] = []
    # 扩令豁免形（CTO 2026-11-25·r35 六件真样对齐）：CARRY/OP/task-inventory/cfo-quota/顶层 .md 散件
    # ——R12 未映射件族 → no-raci-mapping 注（非 fail）；其余 R12 集内件仍须有键。
    import re as _re6b
    _exempt_re = _re6b.compile(
        r"^(CARRY-\d{8}-\d{3}|OP-\d{6}-.*|task-inventory-\d+|cfo-quota-daily-.+|.+[.]md)$")
    for k in need_keys:
        if k in raci:
            continue
        if _exempt_re.match(str(k)):
            notes.append(k)
        elif r12_targets is None or k in r12_targets:
            missing_cov.append(k)
        else:
            notes.append(k)
    if notes:
        plan_doc["no_raci_mapping"] = notes
        plan_doc["raci_scope"] = "r12-subset"
    if missing_cov:
        bad.append(f"item6: R12 覆盖缺口 {len(missing_cov)} 项无 RACI 键（示例 {missing_cov[:3]}）")
    for k, v in raci.items():
        if not isinstance(v, dict):
            bad.append(f"item6: {k} 值非对象")
            continue
        for role in ("accountable", "responsible"):
            rv = v.get(role)
            if not isinstance(rv, str) or not rv.strip():
                bad.append(f"item6: {k}.{role} 空/非法")
        for role in ("consulted", "informed"):
            if role in v and not isinstance(v.get(role), list):
                bad.append(f"item6: {k}.{role} 非列表")
    return bad


def _tree_name_set(tmv_root: str | None) -> set:
    """树面实扫（CTO 令 2026-11-25）：operating-records/*/trees/ 下目录名+文件名集合
    （plan families=LLM 扫树生成 → 树名必在树面；编造名=fail·动态检测力）。
    ENV FADE_OPERATING_ROOT 优先，其次 tmv_root/docs/workflow/operating-records。"""
    import os as _os
    root = None
    env = _os.environ.get("FADE_OPERATING_ROOT")
    if env and Path(env).is_dir():
        root = Path(env)
    elif tmv_root:
        cand = Path(tmv_root) / "docs" / "workflow" / "operating-records"
        if cand.is_dir():
            root = cand
    names: set = set()
    if root is None:
        return names
    try:
        for wk in root.iterdir():
            tdir = wk / "trees"
            if not (wk.is_dir() and tdir.is_dir()):
                continue
            for p in tdir.iterdir():
                names.add(p.name)
    except Exception:
        pass
    return names


def _validate_patrol_layers(plan_doc: dict) -> list[str]:
    """H 合并令（CTO 2026-11-25·COS 形）：plan.patrol_plan.cadence_layers 必带两节律——
    bod_patrol.cadence 固定 "6m"（CEO 6 分钟拍读令）；duty_patrol.cadence 必在；缺=fail。"""
    bad: list[str] = []
    pp = plan_doc.get("patrol_plan")
    if not isinstance(pp, dict):
        return ["g) patrol_plan 缺（cadence_layers 两节律必带）"]
    layers = pp.get("cadence_layers")
    if not isinstance(layers, dict):
        return ["g) patrol_plan.cadence_layers 缺（旧形不收·两节律必带）"]
    bod = layers.get("bod_patrol")
    duty = layers.get("duty_patrol")
    if not isinstance(bod, dict) or str(bod.get("cadence") or "") != "6m":
        bad.append('g) cadence_layers.bod_patrol.cadence 必为 "6m"（CEO 拍读令固定）')
    if not isinstance(duty, dict) or not str(duty.get("cadence") or "").strip():
        bad.append("g) cadence_layers.duty_patrol.cadence 缺（值席守拍设计值）")
    return bad


def _validate_plan_assertions(plan_doc: dict, run_dir: Path,
                              tmv_root: str | None = None,
                              tree_names: set | None = None) -> list[str]:
    """件B（CEO 批·协议 v2.1.0）：规划 6 条断言 a-e（f=plan-freeze·item9）——
    a) 族点名（target ∈ 表枚举） b) 标签非兜底 c) carry 四字段 d) 考卷锁定 e) 双向断言。"""
    bad: list[str] = []
    fams = plan_doc.get("families") or []
    # a) family 归属 + 非空非占位（CTO 修正令 2026-11-25·弃件名 regex·实跑 0/10 证过苛）：
    # 判 family_id ∈ A-H（循环外 fid 检查）+ target 非空非占位（树名自由形·不判形）；
    # 树面实扫保留为非阻断参照（不参与 legal 判定）。
    _FAM_ENUM = {"A", "B", "C", "D", "E", "F", "G", "H"}
    _trees = tree_names if tree_names is not None else _tree_name_set(tmv_root)
    for f in fams:
        if not isinstance(f, dict):
            continue
        _fid = str(f.get("family_id") or "")
        if _fid not in _FAM_ENUM:
            bad.append(f"a) family 归属非法：family_id={_fid!r} 不在 A-H")
        for it in (f.get("items") or []):
            if not isinstance(it, dict):
                continue
            _raw = it.get("target")
            if _raw is None:
                _raw = it.get("item_id")
            tgt = str(_raw or "").strip()
            if (not tgt) or tgt in _OWNER_PLACEHOLDERS:
                bad.append(f"a) target 空/占位：{it.get('item_id')!r} target={tgt!r}")
            elif _trees and tgt not in _trees:
                # 非阻断参照面（树面不在=仅留观测注·不 fail）
                it.setdefault("_tree_scan_note", "not-in-tree-surface")
            owner = str(it.get("owner") or "").strip()
            if owner in _OWNER_PLACEHOLDERS:
                bad.append(f"b) 兜底标签：{it.get('item_id')} owner={owner!r}")
            if "covered_dims" in it:
                cd = it.get("covered_dims")
                if not (isinstance(cd, list) and cd):
                    bad.append(f"b) covered_dims 缺省/空：{it.get('item_id')}")
    for co in plan_doc.get("carry_over") or []:
        if not isinstance(co, dict):
            continue
        missing = [k for k in ("item_id", "owner", "accountable", "evidence_ref")
                   if not str(co.get(k) or "").strip()]
        if missing:
            bad.append(f"c) carry 四字段缺：{co.get('item_id') or '?'} 缺 {missing}")
    refs = plan_doc.get("references")
    refs = refs if isinstance(refs, list) else []
    ref_files = {str((r or {}).get("file")) for r in refs if isinstance(r, dict)}
    for fname in ("exam.json", "rubric-firstshoot.json"):
        if (run_dir / fname).is_file() and fname not in ref_files:
            bad.append(f"d) 考卷未锁定：{fname} hash 未入 references")
    tf = run_dir / "tree-facts.json"
    if tf.is_file():
        try:
            facts = _json.loads(tf.read_text(encoding="utf-8")).get("trees") or {}
        except Exception:
            facts = {}
        actual = len(facts)
        declared = len({it.get("item_id") for it in (plan_doc.get("keep") or [])
                        + (plan_doc.get("migrate") or []) if isinstance(it, dict)})
        if declared != actual:
            bad.append(f"e) 双向断言败：plan 声明 {declared} 树 vs 树面实测 {actual} 树")
    return bad


def _verify_plan_freeze(run_dir: Path) -> dict:
    """v8 item9 复算判据（CTO 裁）：plan-freeze.json 缺席=fail-closed；
    逐树程序重算 md5/size/counts 对表声明——不一致=fail（声明 vs 实测两侧值入 reason）。"""
    fp = run_dir / "plan-freeze.json"
    if not fp.is_file():
        return {"ok": False, "reason": "plan-freeze.json 缺席（fail-closed·v8 item9）"}
    try:
        doc = _json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"plan-freeze.json unparsable: {e}"}
    from runtime.cognition.plan_enricher import _tree_md5_counts
    bad: list[str] = []
    # T3a：artifacts 前后对表（冻结戳记录的 plan/exam hash vs 现值）
    _arts = doc.get("artifacts") or {}
    if isinstance(_arts, dict):
        import hashlib as _hl3
        for _fn, _h in _arts.items():
            _fp3 = run_dir / str(_fn)
            if not _fp3.is_file():
                bad.append(f"{_fn}: artifacts 记录在但现文件缺（前后对表败）")
                continue
            _now = _hl3.sha256(_fp3.read_bytes()).hexdigest()[:16]
            if _now != _h:
                bad.append(f"{_fn}: hash 前后不一致（冻结={_h} 现={_now}·防漂移）")
    # T3a：families_trees 记录面（逐件 md5 冻结；复算源待 source_path 同形扩展——技术债见毕报）
    for ent in (doc.get("trees") or []):
        try:
            tid = ent.get("tree_id")
            sp = ent.get("source_path")
            if not sp:
                bad.append(f"{tid}: source_path 缺（无法重算）")
                continue
            td = Path(str(sp))
            if not td.is_dir():
                bad.append(f"{tid}: 树目录不可达 {sp}")
                continue
            md5, size, counts = _tree_md5_counts(td)
            if (md5 != ent.get("md5") or size != ent.get("size")
                    or counts != ent.get("counts")):
                bad.append(f"{tid}: 声明(md5={str(ent.get('md5'))[:8]},size={ent.get('size')},"
                           f"counts={ent.get('counts')}) vs 实测(md5={md5[:8]},size={size},counts={counts})")
        except Exception as e:  # noqa: BLE001
            bad.append(f"{ent.get('tree_id')}: {type(e).__name__}: {e}")
    return {"ok": not bad, "reason": "; ".join(bad[:6]) if bad else "复算一致"}


def _budget_remaining(deadline_ts: float) -> int:
    """DP-020 追补 c（CTO 裁·结构缺陷修）：子 spawn 超时=min(spawn_timeout, 段剩余)——
    防「子超时>父超时→必先父杀」。剩余 <30s 时调用面应跳过 spawn 走兜底。"""
    import time as _t
    return max(5, int(deadline_ts - _t.time()))


def _load_r12_owner_map(tmv_root: str | None = None) -> dict:
    """R12 数据面映射（COS 定稿件 r12-item3-6-data-*.json）：
    families_items_4fields → {(family_id,target): owner}；raci by_family items_9/8_filled
    （"target:OWNER" 串）→ {target: owner}。ENV FADE_R12_DATA 优先，否则 tmv_root 下最新件。"""
    cands: list[Path] = []
    env = os.environ.get("FADE_R12_DATA")
    if env and Path(env).is_file():
        cands.append(Path(env))
    elif tmv_root:
        try:
            base = Path(tmv_root) / "docs" / "workflow" / "operating-records"
            cands = sorted(base.glob("*/trees/cos-dispatch-ledger/r12-item3-6-data-*.json"))
        except Exception:
            cands = []
    out = {"by_family_target": {}, "by_target": {}, "by_target_meta": {}, "source": None}
    if not cands:
        return out
    try:
        doc = _json.loads(cands[-1].read_text(encoding="utf-8"))
    except Exception:
        return out
    out["source"] = str(cands[-1])
    for ent in doc.get("families_items_4fields") or []:
        if not isinstance(ent, dict) or not ent.get("target"):
            continue
        _meta = {}
        if ent.get("owner"):
            _meta["owner"] = str(ent["owner"])
        if ent.get("due"):
            _meta["due"] = str(ent["due"])
        if _meta:
            out["by_target_meta"][str(ent["target"])] = _meta
        if ent.get("family_id") and ent.get("owner"):
            out["by_family_target"][f"{ent['family_id']}:{ent['target']}"] = str(ent["owner"])
        elif ent.get("owner"):
            # a) 兜底修（CTO 令 2026-11-25）：无 family_id 但 has target → by_target[target]=owner
            out["by_target"].setdefault(str(ent["target"]), str(ent["owner"]))
    raci = (doc.get("raci_36") or {}).get("by_family") or {}
    for fam, blk in raci.items():
        if not isinstance(blk, dict):
            continue
        for lk in ("items_9_filled", "items_8_full"):
            for s in blk.get(lk) or []:
                if isinstance(s, str) and ":" in s:
                    tgt, _, owner = s.rpartition(":")
                    if tgt and owner:
                        out["by_target"][tgt] = owner
    return out


def _owner_map_prompt_block(owner_map: dict) -> str:
    """R12 主修（prompt 注入）：owner 映射表段——LLM 生成 families 时按表填 owner。"""
    if not owner_map or not (owner_map.get("by_family_target") or owner_map.get("by_target")):
        return ""
    lines = ["【owner 映射表（R12 定稿·families items owner 必按表填·缺=gate fail）】"]
    for k, v in sorted((owner_map.get("by_family_target") or {}).items()):
        lines.append(f"  - {k} → {v}")
    for k, v in sorted((owner_map.get("by_target") or {}).items()):
        lines.append(f"  - {k} → {v}")
    return chr(10).join(lines) + chr(10)


def _fill_owner_from_r12(plan_doc: dict, owner_map: dict) -> int:
    """R12 兜底（后处理）：families items owner 空/占位→按映射填（不依赖 LLM 执行力）。返回填充数。"""
    if not owner_map:
        return 0
    filled = 0
    bt = owner_map.get("by_family_target") or {}
    tg = owner_map.get("by_target") or {}
    for f in plan_doc.get("families") or []:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("family_id") or "")
        for it in f.get("items") or []:
            if not isinstance(it, dict):
                continue
            tgt = str(it.get("target") or it.get("item_id") or "")
            _meta = (owner_map.get("by_target_meta") or {}).get(tgt) or {}
            cur = str(it.get("owner") or "").strip()
            if not cur or cur in _OWNER_PLACEHOLDERS:
                owner = bt.get(f"{fid}:{tgt}") or tg.get(tgt) or _meta.get("owner")
                if owner:
                    it["owner"] = owner
                    filled += 1
            # b) due 填充（CTO 令 2026-11-25）：due 空/占位→按 R12 映射填
            cur_due = str(it.get("due") or "").strip()
            if (not cur_due or cur_due in _OWNER_PLACEHOLDERS) and _meta.get("due"):
                it["due"] = _meta["due"]
                filled += 1
    return filled


def _build_plan_prompt(seat: str, run_id: str, run_dir, extra_hint: str = "",
                       prompt_head: str | None = None,
                       owner_map: dict | None = None) -> str:
    """plan prompt 构造单一源（R12：owner 映射段注入——可测面）。"""
    base = prompt_head if prompt_head else _PLAN_PROMPT_HEAD
    return (base % seat.upper() + f"run_id={run_id} run_dir={run_dir}\n"
            + (_owner_map_prompt_block(owner_map) if owner_map else "")
            + extra_hint)


def _spawn_seat(seat: str, run_dir: Path, run_id: str, timeout_s: int = 900,
                extra_hint: str = "", prompt_head: str | None = None,
                owner_map: dict | None = None) -> dict:
    prompt = _build_plan_prompt(seat, run_id, run_dir, extra_hint=extra_hint,
                                prompt_head=prompt_head, owner_map=owner_map)
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
    # DP-020 追补 c：段预算与 deadline（子 spawn 超时=min(spawn_timeout, 剩余)）
    import time as _time_mod
    _stage_budget = int(getattr(args, "stage_budget", None) or
                        os.environ.get("FADE_STAGE_BUDGET_S", "300"))
    _deadline = _time_mod.time() + _stage_budget
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
    out["split_mode"] = bool(PLAN_EXAM_SPLIT)
    # R12 接入（BOD 判对：数据面≠生成器）——主修=prompt 注入映射段·兜底=后处理填 owner
    _omap = _load_r12_owner_map(getattr(args, "tmv_root", "") or None)
    out["r12_owner_map"] = {"source": _omap.get("source"),
                            "family_target_pairs": len(_omap.get("by_family_target") or {}),
                            "target_pairs": len(_omap.get("by_target") or {})}
    r = _spawn_seat(seat, run_dir, args.run_id, timeout_s=min(args.spawn_timeout, _budget_remaining(_deadline)),
                    prompt_head=(_PLAN_ONLY_PROMPT if PLAN_EXAM_SPLIT else None),
                    owner_map=_omap)
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
            # v8 item1/item5：retry 编号隔离主键——spawn 标识用 retry_seq 字段（不改 run_id 主键）
            r = _spawn_seat(seat, run_dir, args.run_id,
                            timeout_s=min(args.spawn_timeout, _budget_remaining(_deadline)), extra_hint=_hint,
                            prompt_head=(_PLAN_ONLY_PROMPT if PLAN_EXAM_SPLIT else None),
                            owner_map=_omap)
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
    if PLAN_EXAM_SPLIT:
        # DP-020 拆分生成：exam 单独 spawn（输入可读 plan.json 全文——输入非瓶颈·输出各半预算）
        plan_doc.pop("exam", None)
        if _budget_remaining(_deadline) < 30:
            # 追补 c：段剩余不足 → 跳过 exam spawn 走空卷兜底（防必被父杀）
            exam = None
            out["exam_spawn"] = {"rc": None, "parsed": False,
                                 "skipped": "stage budget exhausted (<30s remaining)"}
        else:
            re_ = _spawn_seat(seat, run_dir, args.run_id + "-exam",
                              timeout_s=min(args.spawn_timeout, _budget_remaining(_deadline)),
                              prompt_head=_EXAM_PROMPT_HEAD)
            exam_sheet = _extract_json(re_["out"]) if re_["rc"] == 0 else None
            exam = exam_sheet.get("exam") if isinstance(exam_sheet, dict) else None
            out["exam_spawn"] = {"rc": re_["rc"], "parsed": isinstance(exam, dict)}
    else:
        exam = plan_doc.pop("exam", None)
    # DP-20261123-018 item1-4/6（CTO 认可泛化形）：plan 增强（fail-open 零阻断）
    try:
        from runtime.cognition.plan_enricher import enrich_plan as _enrich
        out["enrich"] = _enrich(plan_doc, run_dir, (getattr(args, "tmv_root", "") or None))
    except Exception as _e:  # noqa: BLE001
        out["enrich"] = {"error": f"{type(_e).__name__}: {_e}"}
    plan_path = run_dir / "plan.json"
    # item3 b 案（CTO 令）：unassigned 显式态收集落卷（候责任席认领）
    try:
        out["unassigned_items"] = len(_collect_unassigned(plan_doc))
    except Exception as e:  # noqa: BLE001
        out["unassigned_collect_error"] = f"{type(e).__name__}: {e}"
    # R12 兜底（后处理）：owner 空/占位按映射填（不依赖 LLM 执行力）
    try:
        _filled = _fill_owner_from_r12(plan_doc, _omap)
        out["r12_owner_filled"] = _filled
    except Exception as e:  # noqa: BLE001
        out["r12_owner_fill_error"] = f"{type(e).__name__}: {e}"
    # 件B-d：考卷锁定——exam/rubric hash 入 references（幂等）
    try:
        import hashlib as _hl
        _refs = []
        _exam_p = run_dir / "exam.json"
        if _exam_p.is_file():
            _refs.append({"file": "exam.json", "sha256_16": _hl.sha256(_exam_p.read_bytes()).hexdigest()[:16]})
        from runtime.cognition import score_engine as _se
        _rb = Path(_se.__file__).parent / "rubric-firstshoot.json"
        if _rb.is_file():
            _refs.append({"file": "rubric-firstshoot.json", "sha256_16": _hl.sha256(_rb.read_bytes()).hexdigest()[:16]})
        plan_doc.setdefault("references", []).extend(_refs)
    except Exception:
        pass
    plan_path.write_text(_json.dumps(plan_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["written"] = str(plan_path)
    # T3a（任务书 e0dfa6481）：冻结戳——plan.json/exam.json hash 入 plan-freeze.artifacts（前后对表面）
    try:
        import hashlib as _hl3
        _fz = run_dir / "plan-freeze.json"
        if _fz.is_file():
            _fzd = _json.loads(_fz.read_text(encoding="utf-8"))
            _arts = {}
            for _fn in ("plan.json", "exam.json"):
                _fp3 = run_dir / _fn
                if _fp3.is_file():
                    _arts[_fn] = _hl3.sha256(_fp3.read_bytes()).hexdigest()[:16]
            _fzd["artifacts"] = _arts
            _fz.write_text(_json.dumps(_fzd, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
            out["plan_freeze_artifacts"] = _arts
    except Exception as e:  # noqa: BLE001
        out["plan_freeze_artifact_error"] = f"{type(e).__name__}: {e}"
    # 件B（协议 v2.1.0）：规划 6 断言 a-e（f=freeze 下段）——strict fail-closed
    if os.environ.get("FADE_PLAN_ASSERT", "1") != "0":
        _asserts = (_validate_plan_assertions(plan_doc, run_dir,
                                             tmv_root=(getattr(args, "tmv_root", "") or None))
                    + _validate_families_fields(plan_doc)      # R12 item3
                    + _validate_raci(plan_doc, _r12_target_set(_omap))   # R12 item6（R12 集内须有键）
                    + _validate_patrol_layers(plan_doc))       # H 合并令 g) 两节律
        out["plan_assertions"] = {"ok": not _asserts, "violations": _asserts[:10]}
        if _asserts:
            out["verdict"] = "fail: 规划 6 断言（a-e）拒（" + _asserts[0] + " 等 " + str(len(_asserts)) + " 项）"
            return 2, out
    # v8 item9 复算门（CTO 裁·CEO 批）：freeze 缺席/不一致=fail（fail-closed·不回退替身）
    if os.environ.get("FADE_PLAN_FREEZE", "1") != "0":
        _pf = _verify_plan_freeze(run_dir)
        out["plan_freeze_check"] = _pf
        if not _pf.get("ok"):
            out["verdict"] = f"fail: plan-freeze 复算门拒（{_pf.get('reason')}）"
            return 2, out
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
    ap.add_argument("--tmv-root", default="", help="TMV 检出根（DP-018 增强器读 operating-records 用）")
    ap.add_argument("--stage-budget", type=int, default=None,
                    help="段总预算秒（DP-020 追补 c·子 spawn 超时=min(spawn, 段剩余)）")
    args = ap.parse_args()
    rc, out = run(args)
    print(_json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
