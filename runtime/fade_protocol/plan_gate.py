"""Plan 门骨架（N-D3 件④·通用骨架）：存在性门+模板 schema 四必答+复核仪式形。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 模板 schema 四必答（通用段名——实例 plan 正文按此四段自携内容）
REQUIRED_SECTIONS = ("trigger-criteria", "departure-window-precheck", "segment-order", "dynamic-situation")


def plan_existence_gate(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    """存在性门：无 plan 不开工（返回阻断原因串；None=有 plan 放行）。

    存在性=plan 键在场且非 None（任意值型含空体——内容完整性归 validate_template
    四必答面，两门分层不混判）。"""
    if payload is None or payload.get("plan") is None:
        return "plan gate: no plan present — work blocked (no-plan = dead work)"
    return None


def validate_template(plan_doc: Dict[str, Any]) -> List[str]:
    """模板 schema 四必答校验形：缺段清单（空=合规）。"""
    sections = plan_doc.get("sections", {}) if isinstance(plan_doc, dict) else {}
    if not isinstance(sections, dict):
        return ["sections must be a mapping"]
    return [s for s in REQUIRED_SECTIONS if not str(sections.get(s, "")).strip()]


def review_ritual(plan_doc: Dict[str, Any]) -> Dict[str, Any]:
    """复核仪式形：四必答齐备核+复核签字位（ ritual 结果返回，不落库）。"""
    missing = validate_template(plan_doc)
    return {"complete": not missing, "missing_sections": missing,
            "review_signed_by": None, "note": "复核签字位=仪式挂点（实例侧填）"}
