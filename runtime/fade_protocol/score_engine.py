"""Score 判据执行引擎骨架（N-D3 件②·自实例载体 --score 拆出·通用骨架）。

判据执行框架原语：判据结果原语（make_check/make_unverifiable/make_error）/
三态输出原语（fail|not-scoreable|observation——实例可经 mode_labels 改名）/
阈值判定原语（subtotal vs threshold+gate_wired 软门旗）/证据引用格式原语
（逐判据 {ok,weight,detail} 形）/事件与补写双类计数原语（scoreable 门）。
判据集=实例个性化件（本引擎零实例知识；实例以 checks 列表注入）。
"""
from __future__ import annotations

from datetime import datetime, timezone
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
