"""Close 双段骨架（N-D3 件③·通用骨架）：时序法条+三态框架+收口载体 schema。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 时序法条：段位强制次序（违序=段位降档由调用方处置；本骨架只判序）
STAGE_ORDER = ["push", "verify", "score", "close-skill", "close-cli"]


def stage_in_order(prev: str, nxt: str) -> bool:
    """时序判原语：nxt 是否为 prev 的合法后继段位。"""
    if prev not in STAGE_ORDER or nxt not in STAGE_ORDER:
        return False
    return STAGE_ORDER.index(nxt) == STAGE_ORDER.index(prev) + 1


def sequence_violation(seen: List[str]) -> Optional[str]:
    """时序法条主原语：段位序列逐对核序，返回首个违序描述（无则 None）。"""
    for a, b in zip(seen, seen[1:]):
        if not stage_in_order(a, b):
            return "sequence violation: '{}' -> '{}' out of mandated order {}".format(a, b, STAGE_ORDER)
    return None


class CloseSkillOutcome:
    """Close Skill 三态框架：通过/RETRY/ESCALATED+评分证据引用接口。"""

    VALID = ("pass", "retry", "escalated")

    def __init__(self, outcome: str, evidence_refs: Optional[List[str]] = None, note: str = ""):
        if outcome not in self.VALID:
            raise ValueError("invalid close outcome: {} (valid={})".format(outcome, self.VALID))
        self.outcome = outcome
        self.evidence_refs = list(evidence_refs or [])
        self.note = note

    def to_dict(self) -> Dict[str, Any]:
        return {"outcome": self.outcome, "evidence_refs": self.evidence_refs, "note": self.note}


def close_carrier_row(run_ref: str, day_node: str, close_line: str, content_hash: str = "") -> Dict[str, Any]:
    """收口载体 schema（registry 台账行形/v2 schema 复用）：run 引用+当日节+收口行+内容 hash。"""
    return {"run_ref": run_ref, "day_node": day_node, "close_line": close_line, "content_hash": content_hash}


def validate_carrier_row(row: Dict[str, Any]) -> List[str]:
    """载体 schema 校验形：缺字段清单（空=合规）。"""
    required = ("run_ref", "day_node", "close_line")
    return [k for k in required if not row.get(k)]
