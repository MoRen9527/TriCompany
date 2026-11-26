"""FADE-001 阶段 6: score_engine 实弹引擎（2026-11-14 CEO 11:45:54 直令·BOD 托转·台账 591 笔）。

契约（score_cli probe_score_engine 探测面·CLI/payload/daemon/jobs.json 零触）：
    run_score(run_id: str, run_dir, from_week: str = "", to_week: str = "") -> dict
CLI 以 keyword 形调用（run_id/run_dir 原值 str/from_week/to_week）；engine 只
返回 dict 不落卷（score.json 落卷归 CLI main）。落仓即被探测实弹（import 成功
=probe "present"=engine_absent 态废止）。

判卷正身=本 engine（score_rubric=考卷结构门非判卷·两模块不混淆）。

考卷侧零改动承诺：族元数据（family_name/weight/reading_point/collection_cmd/
verdict_rule/special_clause）运行时读 rubric-firstshoot.json——engine 不复制
八族文案进代码，考卷改权重/文案 engine 读数自动随。

机判/人工两分（FSD 边界内裁决·CTO 授权「分母构成你在边界内定·裁决记录进
docstring」·裁决锚=本段）：
  机判域 B/C/D/E/G（权重和 65）——判据=T1 三断言（a2c246908）+段产物完备性：
    B 拍点形态  run_id 时戳段 HH:MM∈[23:50,23:59]（考卷 verdict_rule 窗断言）。
                预演白天拍如实出红——门不豁免哲学：零豁免开关·读数保真非缺陷
                （判读面在知情件勘正载明·值守看 families 明细知预演时点使然）。
    C run id    T1-1：run_id 正则 ^shift-W\\d+(-loop|-ignite|-official|-resume\\d*)?-\\d{8}T\\d{6}Z$（DP-016 四形）+ run_dir 段产物
                json 的 run_id 字段同串对表（可探面计数；生产面三处同串 grep=
                值守读数位·engine 可探面外如实注记不冒充）。
    D preflight T1-2 后半：preflight.json 存在+值面 verdict=="pass" 且
                exit_code==0（值面必读非仅存在性·拦截态文案如实入 reasons）。
    E qualify   T1-2 前半：qualify.json 存在+assertions 五键（identity/run_dir/
                git_identity/alert_credentials/disk_free）过态字段 "ok" 逐一非
                null 且全 True（假绿=漏报毒·值面必读）。
    G 迁移链    score 时点链上已应落五段产物齐性+值面：preflight/qualify/plan/
                dce/verify 五件 json 存在+各 verdict=="pass"+verify.json
                checks[] 内 migrate_vs_index items[] 逐项 status=="landed"
                （零 missing）。**裁决锚（链序）**：score.json/close.json/
                manifest.json=score 段后段产物（payload 序 score=段 6 在
                close=段 8/manifest 前）——判后段缺=错位误判，故不入齐性判据。
  manual 域 A/F/H（权重和 35）——采集源=TriRMC 生产面/值席面（A jobs.json md5
    活体探读/F alarm log+收件箱到达读数/H dive 预检+拍频）run_dir 不可得：
    state="manual"·score=null 不冒充机判；reasons 挂考卷 collection_cmd 原文
    （运行时引用非复制·值席采集后补判）。F2 免评（零触发满分）=考卷
    special_clause 承载·engine 不改写免评分母语义。

总分语义（docstring 裁决）：total_score=Σ(机判 pass 族 weight)/Σ(机判族
  weight)×100 归一化百分制。manual 35 分出分母——理由：manual 域不可机判，
  若不出分母则总分天花板恒 65=读数误导；归一化=「机判域全过→100」语义清晰，
  35 分 pending 如实在 families 明细（值守面补判后整体读数由人工面承接）。
  红灯族（C/G）state=="fail" → total_score=min(total, REDLINE_CAPS[族])——
  引 score_rubric.REDLINE_CAPS 零硬编码（同值同源令②别名）·多红灯取最严上限
  ·红灯不因其他族高分洗白（cap 应用前后值如实入 redline_caps_applied）。
verdict 集合={pass, fail}：任一族 fail → "fail"（不洗白）；全机判 pass+
  manual 存在 → "pass"（机判域全过·manual 如实标）；rubric 缺席/全降级 → "fail"。

降级面（缺件≠引擎坏=设计行为·engine 不外抛破链）：run_dir 缺/空、段产物缺、
  坏 json、单族判据异常一律捕获 → 该族 fail+reasons 载明细；rubric 文件缺席/
  坏 json → 全族降级 fail（verdict=fail）；外抛只剩未知异常=CLI executed_failed
  兜底（score_cli run_score 异常路径）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, time, timezone
from pathlib import Path

from runtime.cognition.score_rubric import REDLINE_CAPS

SCORE_ENGINE_VERSION = "2.0.0"  # 并盘 100 形：总分三域直加制（v1.0.0=机判域归一化·沿革）

# 考卷真源（运行时读·零文案复制）
_RUBRIC_FILE = Path(__file__).resolve().parent / "rubric-firstshoot.json"

# T1-1 run id 正则（a2c246908 原样；2026-11-21 P1 修形：接受 -loop 段——CEO 令⑤ D8 折算根因消除）
_RUN_ID_RE = re.compile(r"^shift-W\d+(-loop|-ignite|-official|-resume\d*)?-\d{8}T\d{6}Z$")
# B 族拍点窗（考卷 B verdict_rule 同源：23:50-23:59）
_SHOT_WINDOW_START = time(23, 50)
_SHOT_WINDOW_END = time(23, 59)

# 三域族集（并盘 100 形·CEO 直令 2026-11-15 16:23:35·CTO 门禁勘正卷 a3793c559）：
# 机判域 B/C/D/E/G=59 分（B9+C13+D9+E9+G19——机判域和 59 与 REDLINE G cap 59 数值偶合无关）
# 采集域 A/F/H=31 分（值席采集）·主观域 I=10 分（判卷面·subjective-score.json 供）
MACHINE_FAMILIES = ("B", "C", "D", "E", "G")
MANUAL_FAMILIES = ("A", "F", "H")
SUBJECTIVE_FAMILIES = ("I",)

# G 族齐性判据：score 时点链上已应落段产物（链序裁决锚见 docstring）
_CHAIN_ARTIFACTS = (
    "preflight.json", "qualify.json", "plan.json", "dce.json", "verify.json",
)

# E 族五断言键（qualify.py readings 构造 L184-196 实锚）
_QUALIFY_ASSERTION_KEYS = (
    "identity", "run_dir", "git_identity", "alert_credentials", "disk_free",
)


RUBRIC_VERSION = "2.2.0"   # rubric v2.2.0（CEO 定版 2026-11-25·与协议 v2.1.0 对表·权重 65+35）——旧轮按旧 rubric 冻结·新轮起用


def _rubric_sha16() -> str:
    try:
        return hashlib.sha256(_RUBRIC_FILE.read_bytes()).hexdigest()[:16]
    except Exception:
        return ""


def _load_rubric() -> tuple[dict, list[str]]:
    """读考卷元数据（族 id→{family_name, weight, collection_cmd, ...}）。

    缺席/坏 json → ({}, reasons)（全族降级 fail 面·verdict=fail）。
    """
    try:
        data = json.loads(_RUBRIC_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [f"rubric file not found: {_RUBRIC_FILE.name}（考卷缺席降级）"]
    except Exception as e:  # noqa: BLE001 — 坏 json 同降级面
        return {}, [f"rubric unparsable: {type(e).__name__}: {e}（考卷坏卷降级）"]
    # rubric-firstshoot.json 顶层=纯族列表（实锚）；dict 包壳形取 families 键兼容
    families = data.get("families") if isinstance(data, dict) else data
    if not isinstance(families, list):
        return {}, ["rubric families 结构非列表（考卷坏卷降级）"]
    meta = {}
    for f in families:
        fid = f.get("family_id")
        if isinstance(fid, str):
            meta[fid] = f
    if not meta:
        return {}, ["rubric families 零有效族（考卷坏卷降级）"]
    return meta, []


def _judge_b(run_id: str, run_dir: Path) -> tuple[str, list[str]]:
    """B 拍点形态：run_id 时戳段 ∈[23:50,23:59]。预演白天拍如实出红（零豁免）。

    loop 进化轮形态分支（2026-11-16 增补·CTO 46afd9bc3 §三裁 owner=STE·
    判据语义=STE 裁）：窗判面向 cron-sunday 真拍——loop-window 轮=控制面
    即时触发行态·形态锚=管线自证（run_dir/preflight.json 的
    assertions.week_math.mode=loop-window 值面 + loop_source∈cli/env/marker
    三源自证键）·拍点窗判不适用。fail-closed 不放松：T1-1 正则仍先决
    （任何轮 run_id 形坏=fail 零豁免）；mode 命中但 loop_source 值面
    缺失/未知=fail（自证链不完整读数保真）；mode 非 loop-window
    （cron-sunday/键缺失/未知值）→一切走现行窗判（零行为漂移）。
    """
    m = _RUN_ID_RE.match(run_id or "")
    if not m:
        return "fail", [f"run_id 不符 T1-1 正则（B 族时戳段不可得）: {run_id!r}"]
    ts = run_id[-7:-1]  # \d{6}Z 段（HHMMSS·Z 尾剥——[-7:]="235000Z" 剥 Z）
    try:
        shot = datetime.strptime(ts, "%H%M%S").time()
    except ValueError:
        return "fail", [f"run_id 时戳段解析败: {ts!r}"]
    # ── loop 进化轮自证分支（2026-11-16 B 族增补·锚面=preflight 卷形
    #    out{assertions.week_math}·preflight.py L305-312 实锚）──
    try:
        pfd = json.loads((run_dir / "preflight.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — 卷缺席/坏卷=无自证锚·走窗判（现行为）
        pfd = None
    wm = None
    if isinstance(pfd, dict):
        cand = pfd.get("assertions")
        if isinstance(cand, dict) and isinstance(cand.get("week_math"), dict):
            wm = cand["week_math"]
    if isinstance(wm, dict) and wm.get("mode") == "loop-window":
        src = wm.get("loop_source")
        if src in ("cli", "env", "marker"):
            return "pass", [
                f"loop 进化轮形态·拍点 {ts}（管线自证 week_math.mode=loop-window"
                f"·loop_source={src}·窗判不适用于控制面即时触发轮——"
                "46afd9bc3 §三/STE 判据裁 2026-11-16）"
            ]
        return "fail", [
            f"loop 轮自证链不完整：week_math.mode=loop-window 但 loop_source "
            f"值面缺失/未知: {src!r}（fail-closed 读数保真·零豁免）"
        ]
    # 分粒度窗判（考卷窗=23:50-23:59 分域·23:59:59 属窗内——秒面不卡界）
    hm = shot.hour * 60 + shot.minute
    if (_SHOT_WINDOW_START.hour * 60 + _SHOT_WINDOW_START.minute
            <= hm
            <= _SHOT_WINDOW_END.hour * 60 + _SHOT_WINDOW_END.minute):
        return "pass", [f"拍点时戳 {ts} 位于 [23:50,23:59] 窗内（分粒度）"]
    return "fail", [
        f"拍点时戳 {ts} 不在 [23:50,23:59] 窗内（读数保真·预演白天拍=如实出红非缺陷）",
    ]


def _judge_c(run_id: str, run_dir: Path) -> tuple[str, list[str]]:
    """C run id：T1-1 正则 + run_dir 段产物 run_id 同串对表（可探面）。"""
    reasons: list[str] = []
    if not _RUN_ID_RE.match(run_id or ""):
        reasons.append(f"run_id 不符 T1-1 正则: {run_id!r}")
        return "fail", reasons
    if not run_dir.is_dir():
        reasons.append("run_dir 不可达·同串对表零可探面（生产面三处同串=值守读数位）")
        return "fail", reasons
    hits, unparsable = 0, 0
    for jf in sorted(run_dir.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 坏卷跳过计数·C 族判据不因它翻
            unparsable += 1
            continue
        if isinstance(data, dict) and data.get("run_id") == run_id:
            hits += 1
    if hits == 0:
        reasons.append("run_dir 段产物 run_id 同串计数 0（T1-1 结构锚零在）")
        return "fail", reasons
    note = f"T1-1 正则过+段产物同串 {hits} 件（生产面三处同串 grep=值守读数位如实注）"
    if unparsable:
        note += f"·坏卷跳过 {unparsable} 件"
    return "pass", [note]


def _read_stage(run_dir: Path, name: str) -> tuple[dict | None, list[str]]:
    """读段产物值面：存在+json 可解析 → (dict, [])；缺/坏 → (None, reasons)。"""
    path = run_dir / name
    if not path.is_file():
        return None, [f"{name} 缺件"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 坏 json 降级面
        return None, [f"{name} 坏卷: {type(e).__name__}: {e}"]
    if not isinstance(data, dict):
        return None, [f"{name} 顶层非对象（结构面不符）"]
    return data, []


def _judge_d(run_id: str, run_dir: Path) -> tuple[str, list[str]]:
    """D preflight：T1-2 后半——存在+verdict=="pass"+exit_code==0（值面）。"""
    data, reasons = _read_stage(run_dir, "preflight.json")
    if data is None:
        return "fail", reasons
    v, rc = data.get("verdict"), data.get("exit_code")
    if v != "pass" or rc != 0:
        reasons.append(f"preflight 值面拦截态如实: verdict={v!r} exit_code={rc!r}")
        return "fail", reasons
    return "pass", [f"preflight verdict=pass exit_code=0（T1-2 后半过）"]


def _judge_e(run_id: str, run_dir: Path) -> tuple[str, list[str]]:
    """E qualify：T1-2 前半——五断言过态字段 "ok" 逐一非 null 且全 True（值面）。"""
    data, reasons = _read_stage(run_dir, "qualify.json")
    if data is None:
        return "fail", reasons
    assertions = data.get("assertions")
    if not isinstance(assertions, dict):
        reasons.append(f"qualify assertions 非对象: {type(assertions).__name__}")
        return "fail", reasons
    missing = [k for k in _QUALIFY_ASSERTION_KEYS if k not in assertions]
    if missing:
        reasons.append(f"qualify 五断言缺键: {missing}")
        return "fail", reasons
    nulls, falses = [], []
    for k in _QUALIFY_ASSERTION_KEYS:
        entry = assertions[k]
        if not isinstance(entry, dict) or entry.get("ok") is None:
            nulls.append(k)  # 过态字段 null=T1-2 红面
        elif entry.get("ok") is not True:
            falses.append(k)
    if nulls:
        reasons.append(f"qualify 过态字段 null（T1-2 红）: {nulls}")
        return "fail", reasons
    if falses:
        reasons.append(f"qualify 断言红（值面必读·假绿=漏报毒）: {falses}")
        return "fail", reasons
    return "pass", ["qualify 五断言 ok 全 True（T1-2 前半过）"]


def _judge_g(run_id: str, run_dir: Path) -> tuple[str, list[str]]:
    """G 迁移链：score 时点已应落五段产物齐性+值面+verify items 对表。

    链序裁决锚（docstring）：score/close/manifest=score 段后段产物不判缺——
    判后段缺=错位误判（payload 序 score=段 6 在 close=段 8/manifest 前）。
    """
    reasons: list[str] = []
    missing: list[str] = []
    fails: list[str] = []
    verify_data: dict | None = None
    for name in _CHAIN_ARTIFACTS:
        data, r = _read_stage(run_dir, name)
        if data is None:
            missing.append(name)
            reasons.extend(r)
            continue
        if data.get("verdict") != "pass":
            fails.append(f"{name}:verdict={data.get('verdict')!r}")
        if name == "verify.json":
            verify_data = data
    if missing:
        reasons.insert(0, f"段产物缺件: {missing}")
        return "fail", reasons
    if fails:
        reasons.insert(0, f"段产物 verdict 拦截面: {fails}")
        return "fail", reasons
    if verify_data is not None:
        items = []
        for chk in verify_data.get("checks", []) or []:
            if isinstance(chk, dict) and chk.get("check") == "migrate_vs_index":
                items = chk.get("items") or []
                break
        miss_entries = [
            i.get("entry") for i in items
            if isinstance(i, dict) and i.get("status") != "landed"
        ]
        if miss_entries:
            reasons.append(f"verify items 对表 missing: {miss_entries}")
            return "fail", reasons
        # S4b（r36 任务书·CTO 令 2026-11-25）：空证不得 pass——verify items 带 evidence_ref 字段却空=fail
        empty_ev = [i.get("entry") for i in items
                    if isinstance(i, dict) and "evidence_ref" in i
                    and not str(i.get("evidence_ref") or "").strip()]
        if empty_ev:
            reasons.append(f"verify items 空证（evidence_ref 空）: {empty_ev[:4]}")
            return "fail", reasons
    # A+C（CEO 架构令 2026-11-25）：wrong_order 只记 notes（不阻断·语义判归段 7）
    try:
        _wo_gate = _wrong_order_gate(Path(run_dir) if run_dir else None)
        reasons.extend(_wo_gate.get("notes") or [])
    except Exception:
        pass
    _pass_msg = f"五段产物齐性+值面全 pass（{len(_CHAIN_ARTIFACTS)} 件）+verify items 对表零 missing"
    return "pass", [_pass_msg] + [r for r in reasons if str(r).startswith("wrong_order")]


_JUDGES = {
    "B": _judge_b,
    "C": _judge_c,
    "D": _judge_d,
    "E": _judge_e,
    "G": _judge_g,
}


_COLLECT_FAMILIES = ("A", "F", "H")
_COLLECT_AXIS = "acceptance"   # 件④（COS 补①·CEO 批）：验收轴（§2.6 两轴对表·防混读）


def _collect_a(run_dir: Path) -> dict:
    """件① A 族 engine 采集：jobs.json md5 活体探读。
    路径优先级（CTO 令 2026-11-25）：$TRIRMC_JOBS ＞ /srv/fleet/TriRMC/data/cron/jobs.json（R-HY 真实位）
    ＞ run_dir/jobs.json（本机/测试同形 fallback）。"""
    _cands = []
    _env = os.environ.get("TRIRMC_JOBS")
    if _env:
        _cands.append(Path(_env))
    _cands.append(Path("/srv/fleet/TriRMC/data/cron/jobs.json"))
    _cands.append(run_dir / "jobs.json")
    fp = next((p for p in _cands if p.is_file()), _cands[0])
    if not fp.is_file():
        return {"family_id": "A", "verdict": "na",
                "rationale": f"jobs.json 不可得（{fp}·auto 采集探测失败→na）",
                "evidence_ref": "collection/collection-A.json#fallback"}
    try:
        raw = fp.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
        n = len(doc.get("jobs") or []) if isinstance(doc, dict) else 0
    except Exception as e:  # noqa: BLE001
        return {"family_id": "A", "verdict": "na",
                "rationale": f"jobs.json 坏卷（{type(e).__name__}）→na", "evidence_ref": str(fp)}
    md5 = hashlib.md5(raw).hexdigest()
    return {"family_id": "A", "verdict": "pass" if n > 0 else "na",
            "rationale": f"jobs.json md5={md5[:12]} jobs={n}（engine 采集·producer=engine）",
            "evidence_ref": str(fp)}


def _collect_f(run_dir: Path) -> dict:
    """F 族 engine 采集（有界扫描·文本匹配·CTO 追加令 2026-11-25）：
    真因=日志目录 21.8k 件→全域 glob=ARG_MAX 炸的假读数（非无日志）。
    改法：os.scandir 有界（mtime 24h 内·按 mtime desc ≤ TRIRMC_LOGS_MAX=500 件）——
    不用 glob；行级 regex 匹配（RUN_ID|trigger|ERROR·文本形「key: value」非 JSON parse）。
    路径：$TRIRMC_LOGS（dir|file）＞ /var/lib/trirmc/cron/logs ＞ run_dir/alerts.jsonl。"""
    import re as _re
    import time as _t
    _pat = _re.compile(r"RUN_ID|trigger|ERROR", _re.IGNORECASE)
    _dir: Path | None = None
    _single: list = []
    _env = os.environ.get("TRIRMC_LOGS")
    if _env:
        _p = Path(_env)
        if _p.is_dir():
            _dir = _p
        elif _p.is_file():
            _single = [_p]
    if _dir is None and not _single:
        _prod = Path("/var/lib/trirmc/cron/logs")
        if _prod.is_dir():
            _dir = _prod
    files: list = list(_single)
    if _dir is not None:
        _now = _t.time()
        _cut = _now - 86400
        _cap = int(os.environ.get("TRIRMC_LOGS_MAX", "500"))
        _recent = []
        try:
            with os.scandir(_dir) as it:
                for ent in it:
                    try:
                        if not ent.is_file():
                            continue
                        st = ent.stat()
                        if st.st_mtime >= _cut:
                            _recent.append((st.st_mtime, ent.path))
                    except OSError:
                        continue
        except OSError:
            _recent = []
        _recent.sort(reverse=True)
        files.extend(p for _m, p in _recent[:_cap])
    if files:
        matched = 0
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    for ln in fh:
                        if _pat.search(ln):
                            matched += 1
            except OSError:
                continue
        return {"family_id": "F", "verdict": "pass" if matched > 0 else "na",
                "rationale": (f"cron 日志 24h {len(files)} 件（有界扫描）·匹配行={matched}"
                              "（RUN_ID|trigger|ERROR·文本匹配非 JSON）"),
                "evidence_ref": ",".join(str(p) for p in files[:3])}
    if _dir is not None:
        return {"family_id": "F", "verdict": "na",
                "rationale": "cron 日志目录在·24h 内无文件（有界扫描·非 glob 假读数）",
                "evidence_ref": str(_dir)}
    fp = Path(os.environ.get("FADE_ALARM_LOG") or (run_dir / "alerts.jsonl"))
    if not fp.is_file():
        return {"family_id": "F", "verdict": "na",
                "rationale": "alarm log 无产出（auto 采集探测失败→na）",
                "evidence_ref": "collection/collection-F.json#fallback"}
    total = 0
    for line in fp.read_text(encoding="utf-8").splitlines():
        try:
            json.loads(line)
            total += 1
        except Exception:
            continue
    return {"family_id": "F", "verdict": "pass" if total > 0 else "na",
            "rationale": f"alarm log 记录={total}", "evidence_ref": str(fp)}


def _find_patrol_source() -> Path | None:
    """件③（CTO 定形+追加令 2026-11-25）：patrol-source.jsonl 解析面——
    优先级：ENV PATROL_SOURCE ＞ FADE_PATROL_SOURCE ＞
    `/srv/fleet/TriMetaverse/docs/workflow/operating-records/*/trees/bod-tick/patrol-source.jsonl`（glob 最新周·真实位）
    ＞ FADE_OPERATING_ROOT[/FADE_WEEK]/trees/bod-tick/。"""
    for _k in ("PATROL_SOURCE", "FADE_PATROL_SOURCE"):
        env = os.environ.get(_k)
        if env and Path(env).is_file():
            return Path(env)
    try:
        _tmv_cands = sorted(Path(
            "/srv/fleet/TriMetaverse/docs/workflow/operating-records"
        ).glob("*/trees/bod-tick/patrol-source.jsonl"))
        if _tmv_cands:
            return _tmv_cands[-1]
    except Exception:
        pass
    root_env = os.environ.get("FADE_OPERATING_ROOT")
    if not root_env or not Path(root_env).is_dir():
        return None
    root = Path(root_env)
    wk = os.environ.get("FADE_WEEK")
    cands = []
    try:
        dirs = [root / wk] if wk else sorted([d for d in root.iterdir() if d.is_dir()])
        for wd in dirs:
            f = wd / "trees" / "bod-tick" / "patrol-source.jsonl"
            if f.is_file():
                cands.append(f)
    except Exception:
        return None
    return cands[-1] if cands else None


def _collect_h(run_dir: Path) -> dict:
    """件③（CTO 定形+对象修 2026-11-25）：H 判据三态（同 seat 比对）——
    ① 源在：**仅取 seat=bod 的拍**（缺省视为 bod）·其中位 cadence_min vs plan.patrol_plan.**bod_patrol**（±1min）→pass/fail
    ② 源缺（plan 有声明）：**manual（异常·非 na）**
    ③ plan 无 patrol_plan 或**无 bod_patrol 声明**：**na（spec 缺失注·非 fail→weight）**。
    判读对象错位修正：**不与 duty 值席 15m 混比**（BOD 裁·今日）。"""
    declared = None
    try:
        plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        declared = plan.get("patrol_plan")
    except Exception:
        declared = None
    if not isinstance(declared, dict):
        return {"family_id": "H", "verdict": "na",
                "rationale": "plan 无 patrol_plan 声明（设计内不适用→na→weight）",
                "evidence_ref": "plan.json#/patrol_plan"}
    _layers = declared.get("cadence_layers")
    _bod = None
    if isinstance(_layers, dict):
        _bodc = _layers.get("bod_patrol")
        if isinstance(_bodc, dict):
            _bod = _bodc.get("cadence")
    if not _bod:
        return {"family_id": "H", "verdict": "na",
                "rationale": "plan 无 cadence_layers.bod_patrol 声明（旧形·spec 缺失注·非 fail→na→weight）",
                "evidence_ref": "plan.json#/patrol_plan/cadence_layers/bod_patrol"}
    src = _find_patrol_source()
    if src is None:
        return {"family_id": "H", "verdict": "manual",
                "rationale": "patrol-source.jsonl 缺（采集失败=异常→manual·非 na）",
                "evidence_ref": "patrol-source.jsonl#missing"}
    vals = []
    _ticks = 0
    for line in src.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue
        _seat = str(rec.get("seat") or "bod").strip().lower()
        if _seat != "bod":      # 同 seat 比对：非 bod 拍不计入
            continue
        _ticks += 1
        try:
            vals.append(float(rec.get("cadence_min")))
        except (TypeError, ValueError):
            continue
    if not vals:
        return {"family_id": "H", "verdict": "manual",
                "rationale": f"patrol-source 无有效 bod 拍 cadence_min（{src}·异常→manual）",
                "evidence_ref": str(src)}
    vals.sort()
    med = vals[len(vals) // 2]
    import re as _re
    m = _re.match(r"^(\d+)\s*m$", str(_bod))
    declared_min = float(m.group(1)) if m else None
    ok = declared_min is not None and abs(med - declared_min) <= 1.0
    return {"family_id": "H", "verdict": "pass" if ok else "fail",
            "rationale": (f"bod 拍中位={med}min vs 声明 bod_patrol={_bod}（bod tick={_ticks}·"
                          f"{'一致' if ok else '不一致'}·同 seat 比对）"),
            "evidence_ref": str(src)}


_COLLECTORS = {"A": _collect_a, "F": _collect_f, "H": _collect_h}


def _engine_collect_entry(run_dir: Path, run_id: str, fid: str) -> dict | None:
    """件① engine 自动采集：collector→落 collection-<fid>.json（producer=engine）→读回逐件 run_id 校验；
    采集探测失败→None（auto fallback=旧 collection-score.json 回读·历史轮冻结）。"""
    fp = run_dir / "collection" / f"collection-{fid}.json"
    if not fp.is_file():
        try:
            fp.parent.mkdir(parents=True, exist_ok=True)
            ent = _COLLECTORS[fid](run_dir)
            doc = {"schema_version": "1.0.0", "producer": "engine", "axis": _COLLECT_AXIS, "run_id": run_id,
                   "entries": [ent]}
            fp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        except Exception:  # noqa: BLE001
            return None
    try:
        doc = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None
    if doc.get("producer") != "engine":
        return None
    if doc.get("run_id") and run_id and doc["run_id"] != run_id:
        return None
    for e in doc.get("entries") or []:
        if isinstance(e, dict) and e.get("family_id") == fid:
            return e
    return None


_MANIFEST_STAGE_FILES = (
    "preflight.json", "qualify.json", "plan.json", "dce.json", "verify.json",
    "score.json", "score-skill.json", "close.json", "notify_done.json", "manifest.json",
)


def _artifacts_manifest(run_dir: Path | None, run_id: str) -> dict:
    """T3b（任务书 e0dfa6481）：manifest 全覆盖——stage 产物清单+collection 分离件+opinions 族，
    逐件 run_id 对表；缺件显式记（非静默）。"""
    items: list[dict] = []
    missing: list[str] = []
    mismatch: list[str] = []
    if run_dir is None or not Path(run_dir).is_dir():
        return {"items": [], "missing": ["<run_dir 不可得>"], "run_id_mismatch": [], "checked": False}
    rd = Path(run_dir)
    targets: list[Path] = [rd / f for f in _MANIFEST_STAGE_FILES]
    try:
        targets += sorted((rd / "collection").glob("collection-*.json"))
    except Exception:
        pass
    targets += [rd / "opinions.json"]
    targets += sorted(rd.glob("opinions-*.json"))
    import hashlib as _hl3c
    for fp in targets:
        ent = {"file": str(fp.relative_to(rd)).replace(chr(92), "/"), "present": fp.is_file()}
        if not ent["present"]:
            missing.append(ent["file"])
            items.append(ent)
            continue
        # T3c（B1·9 条 hash/manifest 家族）：逐件全量 sha256_16 + JSON 可解析断言
        try:
            _raw = fp.read_bytes()
            ent["sha256_16"] = _hl3c.sha256(_raw).hexdigest()[:16]
            ent["size"] = len(_raw)
        except Exception:
            ent["sha256_16"] = None
            ent["size"] = None
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
            ent["parse_ok"] = True
        except Exception:
            doc = None
            ent["parse_ok"] = False
        _rid = doc.get("run_id") if isinstance(doc, dict) else None
        ent["run_id"] = _rid
        if isinstance(_rid, str) and run_id:
            ent["run_id_match"] = _rid == run_id
            if not ent["run_id_match"]:
                mismatch.append(ent["file"])
        else:
            ent["run_id_match"] = None    # 无 run_id 面（非全件必有·记 null 不臆断）
        items.append(ent)
    return {"items": items, "missing": missing, "run_id_mismatch": mismatch,
            "checked": True, "run_id": run_id}


_STAGE_FACE_MAP = {
    # S7（r36 任务书·CFO 面）：stage→域面映射（成本三面归因）
    "preflight": "machine", "qualify": "machine", "dce": "machine", "verify": "machine",
    "score": "machine", "score_skill": "subjective", "close_skill": "subjective",
    "close": "subjective", "notify_done": "subjective", "plan_scope": "manual", "plan": "manual",
}


def _cost_attribution(run_dir: Path | None) -> dict:
    """S7a/b（CFO 面）：成本三面归因 + stage 分列——读 cost-log.jsonl
    （字段宽容：tokens_in/tokens_out 或 input_tokens/output_tokens 或 tokens）——
    machine/manual/subjective 三面聚合（缺=0）+ cost_by_stage 十段分列；**null 不进均值/和（记 null_skipped）**。"""
    faces = {"machine": {"in": 0, "out": 0}, "manual": {"in": 0, "out": 0},
             "subjective": {"in": 0, "out": 0}}
    by_stage: dict = {}
    null_skipped = 0
    if run_dir is None or not Path(run_dir).is_dir():
        return {"faces": faces, "cost_by_stage": by_stage, "checked": False}
    fp = Path(run_dir) / "cost-log.jsonl"
    if not fp.is_file():
        return {"faces": faces, "cost_by_stage": by_stage, "checked": False, "note": "cost-log 缺"}
    for line in fp.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue
        stage = str(rec.get("stage") or "unknown")
        def _num(*vals):
            nonlocal null_skipped
            for v in vals:
                if v is None:
                    continue
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
            null_skipped += 1              # 全缺/null=计入 skipped（不进和·非静默 0）
            return 0.0
        tin = _num(rec.get("tokens_in"), rec.get("input_tokens"), rec.get("tokens"))
        tout = _num(rec.get("tokens_out"), rec.get("output_tokens"))
        face = _STAGE_FACE_MAP.get(stage, "subjective")
        faces[face]["in"] += int(tin)
        faces[face]["out"] += int(tout)
        ent = by_stage.setdefault(stage, {"in": 0, "out": 0})
        ent["in"] += int(tin)
        ent["out"] += int(tout)
    _tot = sum(f["in"] + f["out"] for f in faces.values())
    _channel_ok = (_tot > 0) or (null_skipped == 0 and by_stage)
    # CFO4（B4）：轮级成本至少一通道可得——不可得=fail-closed 显式可见（channel_ok False）
    if not _channel_ok:
        return {"faces": faces, "cost_by_stage": by_stage, "checked": True,
                "null_skipped": null_skipped, "channel_ok": False,
                "fail_closed_note": "轮级成本不可得（全通道 null·≥1 通道须可得）"}
    # CFO1（B2）：残差升级台账——null/缺字段 stage 逐条记（升级 CFO 面·非静默）
    residual: list = []
    for st_name, ent in by_stage.items():
        if ent.get("in") == 0 and ent.get("out") == 0:
            residual.append({"stage": st_name, "reason": "cost 字段缺失/null（0 记录）",
                             "action": "escalate-cfo"})
    return {"faces": faces, "cost_by_stage": by_stage, "checked": True,
            "null_skipped": null_skipped, "channel_ok": True,
            "residual_ledger": residual[:12]}


def _wrong_order_gate(run_dir: Path | None) -> dict:
    """A+C（CEO 架构令 2026-11-25）：wrong_order **只列 notes 不阻断**（语义判断归段 7 智能段）——
    键名双形兼容：条目可为 str 或 {wrong_order_item|item: ...}。"""
    out: dict = {"notes": []}
    if run_dir is None or not Path(run_dir).is_dir():
        return out
    try:
        _dce = json.loads((Path(run_dir) / "dce.json").read_text(encoding="utf-8"))
    except Exception:
        return out
    wo = ((_dce.get("execution_diff") or {}).get("wrong_order") or []) if isinstance(_dce, dict) else []
    for item in wo:
        if isinstance(item, dict):
            name = item.get("wrong_order_item") or item.get("item") or "?"
        else:
            name = str(item)
        out["notes"].append(f"wrong_order 清单项：{name}（判要不要紧=段 7 score skill 语义判·本门不阻断）")
    return out


def _dim_means_from_jr(doc: dict) -> dict:
    """joint-review faces → {dimension_id: mean} 与 {seat: {dimension_id: score}}（A/B 双列合并均值）。"""
    per_dim: dict = {}
    per_seat: dict = {}
    try:
        for seat, f in (doc.get("faces") or {}).items():
            if not isinstance(f, dict) or f.get("absent"):
                continue
            m: dict = {}
            for d in (f.get("dimensions") or []):
                if not isinstance(d, dict):
                    continue
                did = str(d.get("dimension_id") or d.get("dimension") or "")
                sc = d.get("score")
                if did and isinstance(sc, (int, float)):
                    m.setdefault(did, []).append(float(sc))
                    per_dim.setdefault(did, []).append(float(sc))
            per_seat[seat] = {k: round(sum(v) / len(v), 2) for k, v in m.items()}
    except Exception:
        pass
    return {k: round(sum(v) / len(v), 2) for k, v in per_dim.items()}, per_seat


def _improvement_block(run_dir: Path | None) -> dict:
    """S2-2/3/4（CEO 三问方案 §二）：改进率（Δ/上轮）+逐席逐维表+双轨分。
    prev run=兄弟目录最新含 joint-review；参数化：IMPROVE_MIN_RATE（门槛·占位 None）/IMPROVE_K（k·占位 None）。"""
    out: dict = {"checked": False, "params": {
        # ②（CEO 定谳 2026-11-26）：min_rate 缺省 1.0（修复率 100% 门·env 可覆）
        "min_rate": os.environ.get("IMPROVE_MIN_RATE", "1.0"),
        "k": os.environ.get("IMPROVE_K")}}
    if run_dir is None or not Path(run_dir).is_dir():
        return out
    rd = Path(run_dir)
    try:
        cur_doc = json.loads((rd / "joint-review.json").read_text(encoding="utf-8"))
    except Exception:
        return out
    cur_per_dim, cur_per_seat = _dim_means_from_jr(cur_doc)
    prev_doc = None
    try:
        prevs = [d for d in rd.parent.iterdir()
                 if d.is_dir() and d.resolve() != rd.resolve() and (d / "joint-review.json").is_file()]
        if prevs:
            prevs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            prev_doc = json.loads((prevs[0] / "joint-review.json").read_text(encoding="utf-8"))
    except Exception:
        prev_doc = None
    if prev_doc is None:
        out.update({"note": "prev run 缺（改进率不可算·如实注）", "dual_track": None})
        return out
    prev_per_dim, prev_per_seat = _dim_means_from_jr(prev_doc)
    per_dim = []
    tot_delta = 0.0
    tot_prev = 0.0
    for did, cur in sorted(cur_per_dim.items()):
        prev = prev_per_dim.get(did)
        if prev is None:
            continue
        delta = round(cur - prev, 2)
        rate = round(delta / prev, 4) if prev else None
        per_dim.append({"dimension_id": did, "prev": prev, "cur": cur, "delta": delta, "rate": rate})
        tot_delta += delta
        tot_prev += prev
    total_rate = round(tot_delta / tot_prev, 4) if tot_prev else None
    by_seat = []
    for seat, dims in sorted(cur_per_seat.items()):
        for did, curv in sorted(dims.items()):
            prevv = (prev_per_seat.get(seat) or {}).get(did)
            if prevv is None:
                continue
            delta = round(curv - prevv, 2)
            by_seat.append({"seat": seat, "dimension_id": did, "prev": prevv, "cur": curv,
                            "delta": delta,
                            "rate": round(delta / prevv, 4) if prevv else None})
    min_rate = out["params"]["min_rate"]
    below = []
    if min_rate is not None:
        try:
            thr = float(min_rate)
            below = [x for x in by_seat if x["rate"] is not None and x["rate"] < thr]
        except ValueError:
            pass
    # ①修复率（CEO 定谳 2026-11-26·分子同口径交集修）：resolved = should_fix 集 ∩ 本轮 fixed 集
    _fixed_total = 0
    _resolved = 0
    _prev_pending = 0
    try:
        _cur_rf = (cur_doc.get("refill") or {}).get("items") or []
        _fixed_total = sum(1 for it in _cur_rf if isinstance(it, dict)
                           and str(it.get("status")) == "fixed")
        _prev_rf = ((prev_doc or {}).get("refill") or {}).get("items") or []
        _WHITELIST = ("external_dependency", "pending_approval", "out_of_scope")
        def _should_fix(it: dict) -> bool:
            # 「该修」= deferred∥carried 且非有效豁免（kind∈白名单且 kind_by 非空）
            if str(it.get("status")) not in ("deferred", "carried"):
                return False
            _kind = str(it.get("defer_kind") or "")
            _by = str(it.get("kind_by") or "").strip()
            if _kind in _WHITELIST and _by:
                return False
            return True
        _pending_src = _prev_rf if _prev_rf else _cur_rf
        _should_fix_ids = {str(it.get("prev_opinion_id")) for it in _pending_src
                           if isinstance(it, dict) and _should_fix(it)
                           and str(it.get("prev_opinion_id") or "").strip()}
        _prev_pending = len(_should_fix_ids)
        _fixed_ids = {str(it.get("prev_opinion_id")) for it in _cur_rf
                      if isinstance(it, dict) and str(it.get("status")) == "fixed"
                      and str(it.get("prev_opinion_id") or "").strip()}
        _resolved = len(_should_fix_ids & _fixed_ids)
    except Exception:
        pass
    _repair_rate = (round(min(_resolved / _prev_pending, 1.0), 4)
                    if _prev_pending else None)
    repair = {"fixed_prev_pending_resolved": _resolved,
              "fixed_this_round_total": _fixed_total,
              "fixed_count": _fixed_total,          # 旧名保留=total（参考面）
              "prev_pending": _prev_pending,
              "repair_rate": _repair_rate,
              "should_fix": _prev_pending,
              "whitelist": ["external_dependency", "pending_approval", "out_of_scope"],
              "source": "同口径交集：should_fix 集 ∩ 本轮 fixed 集（rate≤1.0）"}
    # ②min_rate 判对象=repair_rate（total_rate 仅参考·不作门槛）
    below_repair = None
    if min_rate is not None:
        try:
            thr2 = float(min_rate)
            if _repair_rate is not None:
                below_repair = {"repair_rate": _repair_rate, "min_rate": thr2,
                                "below": _repair_rate < thr2}
        except ValueError:
            pass
    exposure = ((cur_doc.get("seat_means") or {}).get("a"), (cur_doc.get("seat_means") or {}).get("b"))
    exp_vals = [v for v in exposure if isinstance(v, (int, float))]
    exp_mean = round(sum(exp_vals) / len(exp_vals), 2) if exp_vals else None
    k = out["params"]["k"]
    improvement = None
    combined = exp_mean
    if k is not None and total_rate is not None:
        try:
            improvement = round(float(k) * total_rate, 3)
            if exp_mean is not None:
                combined = round(exp_mean + improvement, 3)
        except ValueError:
            pass
    # E4-①（进化架构 2026-11-26）：threshold 独立字段（联审面单列表）——min_rate 实读+判结论+未达计数
    _below_count = None
    try:
        if min_rate is not None:
            _thr_ = float(min_rate)
            if _repair_rate is not None:
                _below_count = 1 if _repair_rate < _thr_ else 0
            elif below:
                _below_count = len(below)
    except ValueError:
        _below_count = None
    threshold = {"min_rate": (float(min_rate) if min_rate is not None and str(min_rate).strip() != "" else None),
                 "below": (None if below_repair is None else bool(below_repair.get("below"))),
                 "below_count": _below_count,
                 "note": "repair_rate < min_rate → below（低于 1.0 即 RED）"}
    out.update({"checked": True,
                "improvement_rate": {"per_dim": per_dim, "total_rate": total_rate,
                                     "prev_run": None},
                "by_seat": by_seat,
                "repair": repair,
                "below_threshold": below_repair,
                "threshold": threshold,
                "below_threshold_dims": below,
                "dual_track": {"exposure": {"a": exposure[0], "b": exposure[1]},
                               "improvement": improvement, "combined": combined,
                               "k": k, "note": "改进分=A/B+k×改进率（k 参数化·候 CEO 定值）"}})
    return out


def _cross_check_planes(run_dir: Path | None) -> dict:
    """E5（进化架构 2026-11-26）：两闭环字段边界——score 面（迁移质量/完整度=rubric families）
    与 joint 面（进化维度=jr dimension ids）**交集须为空**（禁混·落卷可判）。"""
    meta, _ = _load_rubric()
    score_dims = {str(k) for k in (meta or {}).keys()}
    joint_dims: set = set()
    if run_dir is not None and Path(run_dir).is_dir():
        try:
            jr = json.loads((Path(run_dir) / "joint-review.json").read_text(encoding="utf-8"))
            for f in (jr.get("faces") or {}).values():
                if not isinstance(f, dict):
                    continue
                for d in (f.get("dimensions") or []):
                    if isinstance(d, dict):
                        did = str(d.get("dimension_id") or d.get("dimension") or "")
                        if did:
                            joint_dims.add(did)
        except Exception:
            pass
    overlap = sorted(score_dims & joint_dims)
    return {"score_plane": sorted(score_dims), "joint_plane_count": len(joint_dims),
            "overlap": overlap, "ok": not overlap,
            "note": "score=迁移质量/完整度（families）·joint=进化维度·交集为空（E5 边界）"}


def _regime_check(run_dir: Path | None) -> dict:
    """S6a（r36 任务书·CTO 令 2026-11-25）：单一 100 制（65+35）为唯一制式——
    rubric 权和须=100；run 内旧制痕（weight_face 旧 basis/subjective 权重 10/14/11/10 形）=violation。"""
    meta, reasons = _load_rubric()
    total = sum(int((m or {}).get("weight") or 0) for m in (meta or {}).values())
    viol: list[str] = []
    if meta and total != 100:
        viol.append(f"rubric 权和 {total} != 100（双制/坏卷）")
    if run_dir is not None and Path(run_dir).is_dir():
        rd = Path(run_dir)
        for fn in ("score-skill.json", "score.json"):
            fp = rd / fn
            if not fp.is_file():
                continue
            try:
                doc = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            _wf = doc.get("weight_face") if isinstance(doc, dict) else None
            if isinstance(_wf, dict):
                _sub = _wf.get("subjective_i_family")
                _basis = _wf.get("total_basis")
                if _basis not in (None, 100):
                    viol.append(f"{fn} weight_face.total_basis={_basis}（非 100 制）")
                if isinstance(_sub, dict) and set(_sub.values()) == {14, 11, 10}:
                    viol.append(f"{fn} weight_face 旧 14/11/10 分值形（旧制并存）")
    return {"ok": not viol, "rubric_total": total, "rubric_version": RUBRIC_VERSION,
            "violations": viol[:6]}


def _counts_check(run_dir: Path | None) -> dict:
    """S6b：三面 counts 同口径——plan.counts/families items 数 vs opinions 数 vs close 面，
    读数不一=notes（注面不炸·violation 候选）。"""
    notes: list[str] = []
    faces: dict = {}
    if run_dir is None or not Path(run_dir).is_dir():
        return {"ok": True, "faces": faces, "notes": ["run_dir 不可得"]}
    rd = Path(run_dir)
    try:
        plan = json.loads((rd / "plan.json").read_text(encoding="utf-8"))
        fam_items = sum(len(f.get("items") or []) for f in (plan.get("families") or [])
                        if isinstance(f, dict))
        faces["plan_families_items"] = fam_items
        faces["plan_counts"] = {k: (plan.get("counts") or {}).get(k)
                                for k in ("migrate", "keep", "carry_over", "top_level")}
    except Exception:
        pass
    try:
        ops = json.loads((rd / "opinions.json").read_text(encoding="utf-8")).get("opinions") or []
        faces["opinions"] = len(ops)
    except Exception:
        pass
    try:
        cl = json.loads((rd / "close.json").read_text(encoding="utf-8"))
        faces["close_upgrade_list"] = len(cl.get("upgrade_list") or [])
    except Exception:
        pass
    if "plan_families_items" in faces and "opinions" in faces:
        if faces["opinions"] < faces["plan_families_items"]:
            notes.append(f"counts 口径差：opinions {faces['opinions']} < plan families items {faces['plan_families_items']}")
    return {"ok": not notes, "faces": faces, "notes": notes[:4]}


def _check_auto_label(score_doc: dict) -> list[str]:
    """S6c：禁归一化/补算冒充人工——auto 判语须显式标 auto。
    补算过的 I 族（reason 含「补算」）时，score.judge_faces.subjective 必须标 auto-backfill。"""
    viol: list[str] = []
    eng = score_doc.get("score") if isinstance(score_doc.get("score"), dict) else score_doc
    if not isinstance(eng, dict):
        return viol
    for f in eng.get("families") or []:
        if not isinstance(f, dict):
            continue
        _auto_marks = [r for r in (f.get("reasons") or []) if "补算" in str(r)]
        if _auto_marks:
            jf = eng.get("judge_faces") if isinstance(eng.get("judge_faces"), dict) else {}
            if jf.get("subjective") != "auto-backfill":
                viol.append(f"family {f.get('family_id')} 含补算判语但未标 auto（judge_faces.subjective 缺）")
    return viol


def _judge_collection(run_dir, run_id: str, fid: str, weight) -> tuple[str, int | None]:
    """采集域族判读消费（collection-score.json→二值分·并盘 100 形 v2.0.0）。

    卷面契约（值席采集件）：score_version/run_id/entries[{family_id, verdict,
    rationale, evidence_ref}]/check_time——verdict=pass→weight/fail→0（与机判
    二值同制·禁部分分）。卷缺席=pending（state=manual·score=null·不冒充）。
    """
    rd = Path(run_dir) if run_dir else None
    # 件①（CEO 批 a 案）：A/F/H engine 自动采集优先（na→weight·历史旧卷回读面见下保留）
    if rd is not None and fid in _COLLECT_FAMILIES:
        _auto = _engine_collect_entry(rd, run_id, fid)
        if _auto is not None:
            v = str(_auto.get("verdict") or "")
            if v in ("pass", "na"):
                return "manual", weight
            if v == "fail":
                return "manual", 0
            if v == "manual":
                return "manual", None   # 件③：源缺=采集失败异常（非 na·不冒充分）
    fp = rd / "collection-score.json" if rd else None
    if fp is None or not fp.exists():
        return "manual", None  # pending——采集窗未到·不冒充
    try:
        doc = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — 坏卷=pending（不破链）
        return "manual", None
    if doc.get("run_id") and run_id and doc["run_id"] != run_id:
        return "manual", None
    for e in doc.get("entries") or []:
        if e.get("family_id") != fid:
            continue
        if not e.get("rationale", "").strip():
            return "manual", None  # 裸判=不消费（禁裸分锚）
        return ("manual", weight) if e.get("verdict") == "pass" else ("manual", 0)
    return "manual", None  # 该族条目缺席=pending


def _judge_subjective(run_dir, run_id: str, weight: int | None = None) -> tuple[str, float | None]:
    """I 族判卷消费（v2.1.0：raw 卷分 0-10 → 按 weight 归一（35 权→卷满 10=35 分））（subjective-score.json→族分·并盘 100 形 v2.0.0）。

    卷面契约（主观题卷正形 §判卷规程）：score_version/run_id/entries[{criterion,
    score, rationale, evidence_ref}]/judge_faces/check_time——I1≤4/I2≤3/I3≤3 封顶
    （weight=10 全族上限）。三机判锚：①rationale 非空（禁裸分）②evidence_ref
    存在性（半机判·指针可达性 I3 同源）③run_id 对表。卷缺席=**partial**（v8 item8·run_state 联动）。
    """
    _w = float(weight if weight else 10)
    rd = Path(run_dir) if run_dir else None
    fp = rd / "subjective-score.json" if rd else None
    if fp is None or not fp.exists():
        # v8 item8（CEO 批·CTO 波2）：卷缺席→**partial**（非 pending——判卷面 fail-closed 可观测·
        # run_state 联动 partial·「不发 notify_done」语义与 cpo-1 同形由 run_state 承载）
        return "partial", None
    try:
        doc = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 坏卷=判卷缺席处理（不破链）
        return "subjective", None
    if doc.get("run_id") and run_id and doc["run_id"] != run_id:
        return "subjective", None  # run 错位=不消费（同值同源）
    entries = doc.get("entries") or []
    caps = {"I1": 4, "I2": 3, "I3": 3}
    total = 0
    for e in entries:
        c = e.get("criterion")
        if c not in caps:
            continue
        v = e.get("score")
        if not isinstance(v, (int, float)) or not e.get("rationale", "").strip():
            continue  # 裸分（rationale 空）或非数值=该判据不计（禁裸分锚）
        ev = e.get("evidence_ref")
        if ev and rd is not None and not (rd / str(ev)).exists():
            continue  # evidence_ref 指针断链=该判据不计（半机判锚）
        total += min(v, caps[c])
    if total <= 0:
        # S7c（CFO 面·CTO 令 2026-11-25）：auto 判卷失败=degraded（非静默 0）——卷在但零有效条目 →
        # 族态 manual（pending 面），不冒充分数；degraded 由消费面经 reason/判语面识别。
        return "manual", None
    return "subjective", round(min(total, 10) / 10.0 * _w, 1)


def run_score(run_id: str, run_dir, from_week: str = "", to_week: str = "") -> dict:
    """判卷主入口（score_cli keyword 四参契约·返回 dict 零落卷）。"""
    rd = Path(run_dir) if run_dir else None
    meta, rubric_reasons = _load_rubric()
    families_out: list[dict] = []
    # 族序：考卷在=考卷族序（A-H）·考卷缺席=骨架序（降级面同形结构）
    order = [f.get("family_id") for f in (meta or {}).values()] or list("ABCDEFGH")
    if not meta and not rubric_reasons:
        rubric_reasons = []

    for fid in order:
        m = meta.get(fid, {}) if meta else {}
        weight = m.get("weight")
        reasons: list[str] = list(rubric_reasons) if rubric_reasons else []
        if not meta:
            # rubric 缺席/坏卷 → 全族降级 fail（verdict=fail 面）
            state, score = "fail", 0
        elif fid in MACHINE_FAMILIES:
            judge = _JUDGES.get(fid)
            try:
                state, jreasons = judge(run_id, rd)
            except Exception as e:  # noqa: BLE001 — 单族判据异常降级（engine 不外抛破链）
                state = "fail"
                jreasons = [f"{fid} 族判据异常降级: {type(e).__name__}: {e}"]
            reasons.extend(jreasons)
            score = weight if state == "pass" else 0
        elif fid in SUBJECTIVE_FAMILIES:
            # 主观域：判卷面（subjective-score.json 供分——初判值席/联审/终判卷 COS 三段落卷后 engine 消费；
            # 卷面缺席=partial（score=null·v8 item8 run_state 联动·不冒充判卷）——禁裸分机判锚：rationale 非空断言+evidence_ref 存在性半机判）
            state, score = _judge_subjective(rd, run_id, weight)
            reasons.append(
                "主观判卷域（判卷面 subjective-score.json 供·卷缺席=pending）·判卷锚（考卷 verdict_rule 原文引用）: "
                + str(m.get("verdict_rule", ""))
            )
            if m.get("special_clause"):
                reasons.append(f"考卷 special_clause 引用: {m.get('special_clause')}")
        else:
            # manual 域：值席采集面（collection-score.json 供判·卷缺席=pending 不冒充；
            # 二值制贴考卷 verdict_rule：verdict=pass→weight/fail→0——与机判同制）
            state, score = _judge_collection(rd, run_id, fid, weight)
            reasons.append(
                "值席采集域（run_dir 不可得·不冒充机判）·采集锚（考卷 collection_cmd 原文引用）: "
                + str(m.get("collection_cmd", ""))
            )
            if m.get("special_clause"):
                reasons.append(f"考卷 special_clause 引用: {m.get('special_clause')}")
        families_out.append({
            "family_id": fid,
            "family_name": m.get("family_name"),
            "state": state,
            "score": score,
            "weight": weight,
            "reasons": reasons,
        })

    # 总分：三域直加制（并盘 100 形·v2.0.0——机判 59+采集 31+主观 10=满 100；
    # 现役 v1 归一化设计随并盘失效·61.5 形回退锚=git revert 改形笔）
    machine = [f for f in families_out if f["family_id"] in MACHINE_FAMILIES and meta]
    coll = [f for f in families_out if f["family_id"] in MANUAL_FAMILIES and meta]
    subj = [f for f in families_out if f["family_id"] in SUBJECTIVE_FAMILIES and meta]
    machine_scored = sum(f["weight"] or 0 for f in machine if f["state"] == "pass")
    collection_scored = sum(f["score"] or 0 for f in coll if f["state"] == "manual" and isinstance(f["score"], (int, float)))
    subjective_scored = sum(f["score"] or 0 for f in subj if f["state"] == "subjective" and isinstance(f["score"], (int, float)))
    pending_w = sum(
        (f["weight"] or 0) for f in families_out
        if meta and ((f["family_id"] in MANUAL_FAMILIES and not isinstance(f["score"], (int, float)))
                     or (f["family_id"] in SUBJECTIVE_FAMILIES and not isinstance(f["score"], (int, float))))
    )
    total = float(machine_scored + collection_scored + subjective_scored)
    # 红灯族 cap（REDLINE_CAPS 引用零硬编码·多红灯取最严·不洗白）
    caps_applied: list[dict] = []
    for f in families_out:
        cap = REDLINE_CAPS.get(f["family_id"]) if f["state"] == "fail" else None
        if cap is not None and total > cap:
            caps_applied.append(
                {"family_id": f["family_id"], "cap": cap, "before": total, "after": float(cap)}
            )
            total = float(cap)
    verdict = "fail" if any(f["state"] == "fail" for f in families_out) else "pass"

    return {
        "score_engine_version": SCORE_ENGINE_VERSION,
        "run_id": run_id,
        "from_week": from_week,
        "to_week": to_week,
        "rubric_file": _RUBRIC_FILE.name,
        "rubric_version": RUBRIC_VERSION,          # 判级 rubric_version 记件（协议 v2.1.0）
        "rubric_sha256_16": _rubric_sha16(),
        "artifacts_manifest": _artifacts_manifest(rd, run_id),   # T3b：manifest 全覆盖+run_id 对表
        "regime_check": _regime_check(rd),                       # S6a：单一 100 制
        "counts_check": _counts_check(rd),                       # S6b：三面 counts 同口径
        "cost_attribution": _cost_attribution(rd),               # S7a/b：成本三面归因+stage 分列
        # E2（进化架构 2026-11-26·CEO 批）：进化指标已迁联审面——score 只留迁移质量/完整度
        "improvement_block_ref": {"moved_to": "joint-review.json#/improvement_block",
                                  "note": "E2：improvement_block/dual_track/repair_rate 归 joint 面（进化闭环 B）"},
        "cross_check": _cross_check_planes(rd),                  # E5：两闭环边界（score∩joint=∅）
        "rubric_loaded": bool(meta),
        # v8 item8：run 状态可观测（subjective 判卷面缺席→partial·「不发 notify_done」查询面）
        "run_state": ("partial" if any(f["state"] == "partial" for f in families_out) else
                      ("failed" if verdict == "fail" else "succeeded")),
        "families": families_out,
        "machine_domain_weight": sum(f["weight"] or 0 for f in machine) if meta else 0,
        "manual_domain_weight": sum(
            (meta.get(f, {}).get("weight") or 0) for f in MANUAL_FAMILIES
        ) if meta else 0,
        "subjective_domain_weight": sum(
            (meta.get(f, {}).get("weight") or 0) for f in SUBJECTIVE_FAMILIES
        ) if meta else 0,
        "total_score": total,
        "total_pending_weight": pending_w if meta else 0,
        "total_projection": float(total + pending_w) if meta else 0.0,
        "domain_breakdown": {
            "machine": float(machine_scored),
            "collection": float(collection_scored),
            "subjective": float(subjective_scored),
        },
        # P5 rubric_defect 暴露形（CTO §四b·CEO 令⑤）：判据面缺陷显式标记——
        # 值表登记（CTO 附注二 2026-11-21·防枚举漂散）：
        #   T1-1_run_id_form = run_id 形不符 T1-1 正则（B/C 族拒判·判据缺陷非链失败）
        #   （后续新 case 在此登记后入枚举）
        # 账面分数不遮掩判据缺陷（B/C 族因 run_id 形不符 T1-1 正则拒判=判据缺陷非链失败）。
        "rubric_defect": sorted({d for f in families_out
                                 if f.get("state") == "fail"
                                 for r in (f.get("reasons") or [])
                                 for d in (["T1-1_run_id_form"] if "T1-1 正则" in str(r) else [])}),
        "redline_caps_applied": caps_applied,
        "verdict": verdict,
        "check_time": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    # 直跑探针面（payload 不经此路——payload 走 score_cli main·本入口仅手探）
    import argparse as _argparse

    p = _argparse.ArgumentParser(description="score_engine 直跑探针（score.json 落卷归 score_cli）")
    p.add_argument("--run-id", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--from-week", default="")
    p.add_argument("--to-week", default="")
    a = p.parse_args()
    print(json.dumps(run_score(a.run_id, a.run_dir, a.from_week, a.to_week),
                     ensure_ascii=False, indent=2))
