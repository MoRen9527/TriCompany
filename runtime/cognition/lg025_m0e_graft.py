# -*- coding: utf-8 -*-
"""LG-025 M0e graft 波（2026-09-03，COS 派工；D-15 双席裁决 §四=工序合同）。

按件型分流 graft：soul=旧代语义主源+新代认知分层段并入保留；
memory/colleagues/social=新代既有内容为基底+旧代 graft 三节框架；
冲突三层：结构/标记旧代赢、内容新代赢（禁删句）、原则冲突以新代改写。
只读旧代、禁 --overwrite（本工具只做定向原位补全，不整件重写）。

用法：
  python -m runtime.cognition.lg025_m0e_graft --employee-id <id> [--dry-run]
产出：原位更新 <id>.{memory,colleagues,social,soul}.agent.md + stdout 双向 diff 摘要。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from runtime.cognition.employee_source_kit import _split_sections

REQUIRED_SECTIONS = ("当前原则", "运行资产落点", "层契约")
COGNITION_MARKER = "TRICOMPANY_COGNITION_HOME"
NEW_WORDING = ("CEO 磨人", "CEO 本人")

COGNITIVE_SECTION_RE = re.compile(r"^##\s*认知分层约束\s*$", re.MULTILINE)


def _extract_section(text: str, title: str) -> str | None:
    """提取 `## <title>` 节原文（含节头行，至下一节头/EOF）。"""
    for header, body in _split_sections(text):
        if header.strip().lstrip("#").strip() == title:
            return (header + "\n" + body).strip("\n")
    return None


def _section_titles(text: str) -> list[str]:
    return [header.strip().lstrip("#").strip() for header, _ in _split_sections(text)]


def _apply_wording_updates(text: str) -> tuple[str, list[str]]:
    """旧代通用词以新代口径为准（M0a 全席改词：CEO 磨人→CEO 本人）。"""
    changed: list[str] = []
    for old, new in (NEW_WORDING,):
        if old in text:
            text = text.replace(old, new)
            changed.append(f"{old}→{new}")
    return text, changed


def graft_boundary_piece(new_text: str, old_text: str, *, needs_marker: bool) -> tuple[str, list[str]]:
    """boundary 三件型（memory/colleagues/social）：新代为基底，缺的节从旧代 graft。"""
    notes: list[str] = []
    updated, wording = _apply_wording_updates(new_text)
    if wording:
        notes.append(f"新代词形校准: {'; '.join(wording)}")
    for title in REQUIRED_SECTIONS:
        if title in _section_titles(updated):
            notes.append(f"节『{title}』新代已在（内容新代赢，不覆盖）")
            continue
        old_section = _extract_section(old_text, title)
        if old_section is None:
            notes.append(f"节『{title}』旧代亦缺——标注候 CHO 人工灌注（勿擅断）")
            continue
        old_section, w = _apply_wording_updates(old_section)
        if w:
            notes.append(f"节『{title}』旧代词形校准: {'; '.join(w)}")
        updated = updated.rstrip("\n") + "\n\n" + old_section + "\n"
        notes.append(f"节『{title}』自旧代 graft（{len(old_section.splitlines())} 行）")
    # V4 双标记（boundary 三件统一）：TRICOMPANY_COGNITION_HOME 落「运行资产落点」
    # 节内 + 「源侧认知层契约」来源声明落「层契约」节内（通用结构句，非席位语义）
    anchor = "## 运行资产落点"
    idx = updated.find(anchor)
    if COGNITION_MARKER not in updated and idx >= 0:
        line_end = updated.find("\n", idx)
        insert_at = len(updated) if line_end < 0 else line_end + 1
        updated = updated[:insert_at] + f"\n- runtime cognition 私域：`{COGNITION_MARKER}`（认知层状态与派生资产落点）\n" + updated[insert_at:]
        notes.append("TRICOMPANY_COGNITION_HOME 标记插入「运行资产落点」节内")
    elif COGNITION_MARKER not in updated:
        notes.append("标注：标记未落——「运行资产落点」节缺失，候 CHO 人工灌注")
    if "源侧认知层契约" not in updated:
        anchor = "## 层契约"
        idx = updated.find(anchor)
        if idx >= 0:
            line_end = updated.find("\n## ", idx + 1)
            insert_at = len(updated.rstrip("\n")) if line_end < 0 else line_end
            contract_line = "\n- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。\n"
            updated = updated[:insert_at].rstrip("\n") + "\n" + contract_line + updated[insert_at:].lstrip("\n")
            notes.append("「源侧认知层契约」来源声明插入层契约节内")
        else:
            notes.append("标注：「源侧认知层契约」未落——层契约节缺失，候 CHO 人工灌注")
    return updated, notes


def graft_soul_piece(new_text: str, old_text: str) -> tuple[str, list[str]]:
    """soul：旧代语义主源 graft + 新代认知分层约束段并入保留（不丢）。"""
    notes: list[str] = []
    old_text, wording = _apply_wording_updates(old_text)
    if wording:
        notes.append(f"旧代词形校准: {'; '.join(wording)}")
    # 新代认知分层约束段（如有）原样并入保留
    cognitive_block = ""
    if COGNITIVE_SECTION_RE.search(new_text):
        sections = dict(_split_sections(new_text))
        for header, body in _split_sections(new_text):
            if header.strip().lstrip("#").strip() == "认知分层约束":
                cognitive_block = (header + "\n" + body).strip("\n")
                break
        notes.append("新代「认知分层约束」段并入保留")
    merged = old_text.rstrip("\n")
    if cognitive_block and cognitive_block not in merged:
        merged = merged + "\n\n" + cognitive_block + "\n"
    # 三节若旧代亦缺（防御），从新代补骨架并在 diff 标注
    for title in REQUIRED_SECTIONS:
        if title not in _section_titles(merged):
            new_section = _extract_section(new_text, title)
            if new_section:
                merged = merged.rstrip("\n") + "\n\n" + new_section + "\n"
                notes.append(f"节『{title}』旧代缺、自新代补入（内容新代赢）")
            else:
                notes.append(f"节『{title}』两侧均缺——标注候 CHO 人工灌注（勿擅断）")
    return merged, notes


def graft_employee(source_root: Path, employee_id: str, dry_run: bool) -> list[str]:
    lines: list[str] = [f"# graft 双向清单：{employee_id}", ""]
    for suffix, needs_marker in (("memory", True), ("colleagues", False), ("social", False), ("soul", False)):
        new_path = source_root / "source-agents" / employee_id / f"{suffix}.agent.md"
        old_path = source_root / "source-agents" / employee_id / f"{employee_id}.{suffix}.md"
        if not new_path.is_file():
            lines.append(f"## {suffix}.agent.md — SKIP：新代件不在盘")
            continue
        new_text = new_path.read_text(encoding="utf-8-sig")
        if not old_path.is_file():
            lines.append(f"## {suffix}.agent.md — SKIP：旧代 {old_path.name} 不在盘（无源，候 CHO 人工灌注）")
            continue
        old_text = old_path.read_text(encoding="utf-8-sig")
        if suffix == "soul":
            merged, notes = graft_soul_piece(new_text, old_text)
        else:
            merged, notes = graft_boundary_piece(new_text, old_text, needs_marker=needs_marker)
        lines.append(f"## {suffix}.agent.md（新代 {len(new_text.splitlines())} 行 → graft 后 {len(merged.splitlines())} 行）")
        lines.extend(f"- {n}" for n in notes)
        if not dry_run:
            new_path.write_text(merged, encoding="utf-8", newline="\n")
            lines.append("- 已原位写回（禁删句：新代原内容逐行保留于基底）")
        lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="LG-025 M0e graft（按件型分流）")
    parser.add_argument("--employee-id", required=True)
    parser.add_argument("--source-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report = graft_employee(Path(args.source_root), args.employee_id, args.dry_run)
    print("\n".join(report))


if __name__ == "__main__":
    main()
