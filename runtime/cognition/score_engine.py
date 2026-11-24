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

import json
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


RUBRIC_VERSION = "2.1.0"   # 协议 v2.1.0（CEO 批 2026-11-25·权重 65+35）——旧轮按旧 rubric 冻结·新轮起用


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
    return "pass", [f"五段产物齐性+值面全 pass（{len(_CHAIN_ARTIFACTS)} 件）+verify items 对表零 missing"]


_JUDGES = {
    "B": _judge_b,
    "C": _judge_c,
    "D": _judge_d,
    "E": _judge_e,
    "G": _judge_g,
}


def _judge_collection(run_dir, run_id: str, fid: str, weight) -> tuple[str, int | None]:
    """采集域族判读消费（collection-score.json→二值分·并盘 100 形 v2.0.0）。

    卷面契约（值席采集件）：score_version/run_id/entries[{family_id, verdict,
    rationale, evidence_ref}]/check_time——verdict=pass→weight/fail→0（与机判
    二值同制·禁部分分）。卷缺席=pending（state=manual·score=null·不冒充）。
    """
    rd = Path(run_dir) if run_dir else None
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
