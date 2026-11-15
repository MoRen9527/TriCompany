"""Score 判据执行引擎（N-D3 件②·自实例载体 --score 拆出·通用骨架）。

判据执行框架原语：判据结果原语（make_check/make_unverifiable/make_error）/
三态输出原语（fail|not-scoreable|observation——实例可经 mode_labels 改名）/
阈值判定原语（subtotal vs threshold+gate_wired 软门旗）/证据引用格式原语
（逐判据 {ok,weight,detail} 形）/事件与补写双类计数原语（scoreable 门）。
判据集=实例个性化件（本引擎零实例知识；实例以 checks 列表注入）。

主观题判分面扩形（CEO 直令线 2 16:23·两级判分承载）：值席初判→COS 终判
两级判分原语——初判三件套（rationale 必附/evidence_ref 可复核/判卷时点打戳）/
分差触发器（档差 ≥2 强制复核）/终判卷装配/独立落卷原语/并盘原语（客观+主观
=100 合盘）。判据语义=实例个性化件；本面只承载判分结构。
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

# 三态默认标签（实例可经 mode_labels 覆盖改名；语义不变：硬失败/不可评/观测态）
DEFAULT_MODE_LABELS = {"fail": "fail", "not-scoreable": "not-scoreable", "observation": "observation"}


def make_check(cid: str, weight: int, ok: bool, **detail) -> Dict[str, Any]:
    """判据结果原语：单判据 {ok,weight,detail} 证据引用形。"""
    entry: Dict[str, Any] = {"id": cid, "ok": bool(ok), "weight": int(weight)}
    entry.update(detail)
    return entry


def make_unverifiable(cid: str, weight: int, note: str) -> Dict[str, Any]:
    """不可验原语：离线/未收敛/外依赖缺席=「不可验」非 FAIL（判据执行框架原语）。"""
    entry = make_check(cid, weight, True)
    entry["verifiable"] = False
    entry["note"] = note
    return entry


def make_error(cid: str, message: str) -> Dict[str, Any]:
    """收集失败原语：判据采集本身失败（≠判据 FAIL，计入 errors 面）。"""
    return {"id": cid, "error": message}


def derive_status(scoreable: bool, error_count: int, mode_labels: Optional[Dict[str, str]] = None) -> str:
    """三态输出原语：硬失败>不可评>观测态（labels 供实例改名）。"""
    labels = dict(DEFAULT_MODE_LABELS)
    if mode_labels:
        labels.update(mode_labels)
    if error_count > 0:
        return labels["fail"]
    if not scoreable:
        return labels["not-scoreable"]
    return labels["observation"]


def scoreable_gate(event_writes: int, backfill_writes: int) -> Tuple[bool, str]:
    """双类计数原语：可评=自然日含事件驱动写与巡检补写各≥1（双类齐备门）。"""
    ok = event_writes >= 1 and backfill_writes >= 1
    reason = None if ok else "scoreable=需事件驱动写与巡检补写各≥1；skip-only/单类不可评（event={} backfill={})".format(event_writes, backfill_writes)
    return ok, reason


def threshold_verdict(checks: List[Dict[str, Any]], threshold: int, gate_wired: bool = False) -> Dict[str, Any]:
    """阈值判定原语：ok 判据权重小计 vs 门限；gate_wired=False=软门（只读数不拦截）。"""
    subtotal = sum(int(c.get("weight", 0)) for c in checks if c.get("ok"))
    return {"subtotal": subtotal, "subtotal_max": sum(int(c.get("weight", 0)) for c in checks),
            "threshold": int(threshold), "gate_wired": bool(gate_wired)}


def build_envelope(protocol: str, version: str, mode_label: str, date_iso: str,
                   scoreable: bool, status: str, reason: Optional[str],
                   checks: List[Dict[str, Any]], errors: List[str],
                   summary: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """评分 envelope 装配原语（统一外壳：协议/版本/时刻/判据/汇总/错误面）。"""
    env: Dict[str, Any] = {
        "protocol": protocol,
        "version": version,
        "mode": mode_label,
        "check_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date": date_iso,
        "scoreable": scoreable,
        "status": status,
        "reason": reason,
        "summary": summary,
        "checks": checks,
        "errors": errors,
    }
    if extra:
        env.update(extra)
    return env


# ── 主观题判分面扩形（CEO 直令线 2·两级判分：值席初判→COS 终判）──────────────

SUBJECTIVE_SCORE_VERSION = "1.0"
DIVERGENCE_REVIEW_THRESHOLD = 2  # 分差触发器：档位差 ≥2 强制复核（阈值候裁量定谳）


def initial_judgment(criterion: str, score: float, max_score: float,
                     rationale: str, evidence_ref: str, judge: str,
                     judged_at: Optional[str] = None) -> Dict[str, Any]:
    """初判三件套原语：rationale 必附（禁裸分）+evidence_ref 可复核+判卷时点打戳。"""
    if not str(rationale or "").strip():
        raise ValueError("initial judgment rationale required (裸分禁令)")
    if not str(evidence_ref or "").strip():
        raise ValueError("initial judgment evidence_ref required (可复核锚)")
    stamp = judged_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"criterion": criterion, "score": float(score), "max_score": float(max_score),
            "rationale": rationale, "evidence_ref": evidence_ref, "judge": judge,
            "judged_at": stamp, "level": "initial"}


def divergence_gap(score_a: float, score_b: float) -> float:
    """分差触发器原语：原始分差绝对值（分）。"""
    return abs(float(score_a) - float(score_b))


def final_verdict_volume(run_id: str, initials: List[Dict[str, Any]],
                         joint_opinions: Optional[List[Dict[str, Any]]] = None,
                         final_judge: str = "COS",
                         note: str = "") -> Dict[str, Any]:
    """COS 终判卷装配原语：汇总初判+联审意见+分差触发复核标注。

    分差触发器：联审意见与值席初判同判据分差 ≥DIVERGENCE_REVIEW_THRESHOLD
    档（归一化）→ divergence_review=True（强制复核标注）。
    """
    joint = list(joint_opinions or [])
    divergence_review = False
    divergences: List[Dict[str, Any]] = []
    for j in joint:
        for i in initials:
            if i.get("criterion") == j.get("criterion"):
                gap = abs(float(i.get("score", 0)) - float(j.get("score", 0)))
                if gap >= DIVERGENCE_REVIEW_THRESHOLD:  # 原始分差 ≥2 分（STE 定谳形：分差≥2 分档强制复核）
                    divergence_review = True
                    divergences.append({"criterion": i.get("criterion"),
                                        "initial": i.get("score"), "joint": j.get("score"),
                                        "gap": gap})
    return {
        "score_version": SUBJECTIVE_SCORE_VERSION,
        "run_id": run_id,
        "judge_faces": {"initial": initials, "joint": joint,
                        "final": {"final_judge": final_judge, "note": note}},
        "divergence_review": divergence_review,
        "divergences": divergences,
    }


def write_subjective_score(run_dir: str, volume: Dict[str, Any],
                           filename: str = "subjective-score.json") -> str:
    """独立落卷原语：主观评分卷写 run_dir（与 engine 机判 score.json 分立）。"""
    import os
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(volume, fh, ensure_ascii=False, indent=2)
    return path


def merge_rubric(objective: Dict[str, Any], subjective: Dict[str, Any],
                 merged_total: float = 100, machine: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """并盘原语：rubric 合盘（总量断言防漂）。

    两域形：objective（值席采集面）+subjective（人工判卷面）。
    三域直加形（CTO 门禁勘正现值 59/31/10）：machine（机判域 B9+C13+D9+E9+G19=59）
    +objective 31（采集 A/F/H）+subjective 10（I 族判卷）=100。
    勘混淆注：机判域 59 与 REDLINE G cap 59 数值偶合无关（两义两用，禁互推）。
    """
    domains: List[Tuple[str, Dict[str, Any]]] = [("objective", objective), ("subjective", subjective)]
    if machine is not None:
        domains.insert(0, ("machine", machine))
    total = sum(float(d.get("total", 0)) for _, d in domains)
    if abs(total - merged_total) > 1e-9:
        raise ValueError("rubric merge total mismatch: {} != {} ({})".format(
            " + ".join(str(float(d.get("total", 0))) for _, d in domains), merged_total,
            " + ".join(k for k, _ in domains)))
    return {"merged_total": merged_total,
            "domains": {k: d for k, d in domains},
            "families": {k: d.get("families", []) for k, d in domains}}
