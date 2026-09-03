# -*- coding: utf-8 -*-
"""LG-025 M0e graft 波（2026-09-03，COS 派工；D-15 双席裁决 §四=工序合同）。

按件型分流 graft：soul=旧代语义主源+新代认知分层段并入保留；
memory/colleagues/social=新代既有内容为基底+旧代 graft 三节框架；
冲突三层：结构/标记旧代赢、内容新代赢（禁删句）、原则冲突以新代改写。
只读旧代、禁 --overwrite（本工具只做定向原位补全，不整件重写）。

残项②③修复批（2026-09-03 FD 后备窗，COS 裁）：
- 同名 `## ` 多节归并：连续两节头病态（graft 插入点 × _split_sections 边界，
  validator dict 语义取最后同名节）收敛为单节头，幂等复跑不再残留。
- 词形校准规则族：既有「CEO 磨人→CEO 本人」+ 宿主 Employee workspace 路径行
  改写为源侧合法形态（消 FORBIDDEN_HOST_BINDING_MARKERS 命中），增量复跑生效。
- 「运行资产落点」节实例化：通用句节（=模板桩同款行集）追加 <id> 专属行破 V2 判桩。

残项①校准族扩员批（2026-09-03 FD spawn 后备窗，CHO 轮裁）：
- 词形校准规则族纳入 `宿主绑定说明：` binding-profiles 路径行改写（→
  「宿主 binding 事实由 binding profile 承载，不入本件」无路径指针形态）；
  FORBIDDEN_HOST_BINDING_MARKERS 未含 binding-profiles 故 validator 不拦，
  按 LG-023「binding 事实不入源侧五件套」口径校准出件；与既有 Employee-
  workspace 行改写词形互斥（去重已核，无重复覆盖）。

用法：
  python -m runtime.cognition.lg025_m0e_graft --employee-id <id> [--dry-run] [--report-out <path>]
产出：原位更新 <id>.{memory,colleagues,social,soul}.agent.md + 双向 diff 摘要
（stdout；--report-out 同时落 evidence/<seat>-diff.md）。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from runtime.cognition.employee_source_kit import (
    EMPTY_SECTION_MIN_CHARS,
    EMPTY_SECTION_MIN_LINES,
    FORBIDDEN_CONSUMPTION_MARKERS,
    FORBIDDEN_HOST_BINDING_MARKERS,
    _split_sections,
)

REQUIRED_SECTIONS = ("当前原则", "运行资产落点", "层契约")
COGNITION_MARKER = "TRICOMPANY_COGNITION_HOME"

# ── 词形校准规则族（幂等全量应用；残项③ COS 裁 + 残项① CHO 轮裁扩员）─────
# 词对规则：旧词→新词全文替换（M0a 既有词形基线）。
WORDING_PAIRS: tuple[tuple[str, str], ...] = (("CEO 磨人", "CEO 本人"),)
# 行改写规则一（二窗既有）：宿主 Employee workspace 路径行→源侧合法形态。原行含
# `TriCompany-copilot-host-assets/knowledge/employees/`（validator
# FORBIDDEN_HOST_BINDING_MARKERS 成员，memory/colleagues/social 全文必 fail），
# 裁定形态=改写为 runtime cognition 私域表述（消 marker，不删句位语义）。
EMPLOYEE_WORKSPACE_LINE_RE = re.compile(
    r"^-\s*Employee workspace[：:]\s*.*TriCompany-copilot-host-assets/knowledge/employees/.*$",
    re.MULTILINE,
)
KNOWLEDGE_WORKSPACE_LINE = "- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）"
# 行改写规则二（残项① CHO 轮裁扩员）：`宿主绑定说明：` binding-profiles 路径行
# →无路径指针形态。binding-profiles 路径不在 FORBIDDEN_HOST_BINDING_MARKERS
# （validator 不拦），但按 LG-023 已验收口径「binding 事实由 binding profile
# 承载，不在源侧五件套内固化」同族校准出件。去重已核：与规则一前缀词形
# （Employee workspace × copilot-host-assets）互斥，无重复覆盖；改写后行不再
# 命中本规则（幂等复跑稳定）。
HOST_BINDING_PATH_LINE_RE = re.compile(
    r"^-\s*宿主绑定说明[：:].*binding-profiles.*$",
    re.MULTILINE,
)
HOST_BINDING_FACT_LINE = "- 宿主 binding 事实由 binding profile 承载，不入本件"
# 「运行资产落点」节实例化判据前缀：节内已有任一前缀行 = 已含席位专属行（V2 破桩）。
SEAT_INSTANCE_LINE_PREFIXES = ("- 知识工作区：", "- 员工实例资产：")

COGNITIVE_SECTION_RE = re.compile(r"^##\s*认知分层约束\s*$", re.MULTILINE)
_DUP_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$")


def _extract_section(text: str, title: str) -> str | None:
    """提取 `## <title>` 节原文（含节头行，至下一节头/EOF）。"""
    for header, body in _split_sections(text):
        if header.strip().lstrip("#").strip() == title:
            return (header + "\n" + body).strip("\n")
    return None


def _section_titles(text: str) -> list[str]:
    return [header.strip().lstrip("#").strip() for header, _ in _split_sections(text)]


def _apply_wording_updates(text: str) -> tuple[str, list[str]]:
    """词形校准规则族（幂等全量应用）：词对 replace + 宿主绑定路径行改写。

    残项③ COS 裁：宿主 Employee workspace 路径行属宿主绑定事实，不得固化进
    源侧认知层五件套（validator FORBIDDEN_HOST_BINDING_MARKERS 必 fail），
    统一改写为源侧合法的 runtime cognition 私域表述。
    残项① CHO 轮裁：`宿主绑定说明：` binding-profiles 路径行 validator 不拦，
    但同属宿主绑定事实，按 LG-023 口径改写无路径指针形态（规则二）。
    """
    changed: list[str] = []
    for old, new in WORDING_PAIRS:
        if old in text:
            text = text.replace(old, new)
            changed.append(f"{old}→{new}")
    if EMPLOYEE_WORKSPACE_LINE_RE.search(text):
        text, count = EMPLOYEE_WORKSPACE_LINE_RE.subn(KNOWLEDGE_WORKSPACE_LINE, text)
        changed.append(f"Employee workspace 宿主路径行→知识工作区 runtime cognition 形态（{count} 处）")
    if HOST_BINDING_PATH_LINE_RE.search(text):
        text, count = HOST_BINDING_PATH_LINE_RE.subn(HOST_BINDING_FACT_LINE, text)
        changed.append(f"宿主绑定说明 binding-profiles 路径行→无路径指针形态（{count} 处）")
    return text, changed


def _collapse_duplicate_sections(text: str) -> tuple[str, list[str]]:
    """同名 `## ` 多节归并（残项②修复：连续两节头病态收敛，幂等复跑不再残留）。

    病态根因=graft 插入点与 _split_sections 边界错位：validator `dict(_split_sections)`
    语义只消费**最后**一个同名节，前置同名节成为不可见死区（空体或仅 graft 声明行）。
    归并规则（禁删句：行只移动/去重，不丢弃语义行）：
    - 前置同名节 body 无非空行 → 仅删该节头及其后空行。
    - 前置同名节 body 有非空行 → 按原序并入最后一个同名节尾（与保留节已有行
      strip 相同则跳过），删其节头。
    前提：boundary 三件现盘无 frontmatter（agent 件不经本函数）。
    """
    lines = text.splitlines(keepends=True)
    header_indices: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = _DUP_HEADER_RE.match(line)
        if m:
            header_indices.append((i, m.group(1)))
    if not header_indices:
        return text, []
    segments: list[tuple[str | None, int, int]] = [(None, 0, header_indices[0][0])]
    for j, (idx, title) in enumerate(header_indices):
        end = header_indices[j + 1][0] if j + 1 < len(header_indices) else len(lines)
        segments.append((title, idx, end))
    groups: dict[str, list[int]] = {}
    for k, (title, _, _) in enumerate(segments):
        if title is not None:
            groups.setdefault(title, []).append(k)
    dup_titles = {title for title, ks in groups.items() if len(ks) > 1}
    if not dup_titles:
        return text, []
    keep_of = {title: ks[-1] for title, ks in groups.items()}
    seen_lines: dict[int, set[str]] = {}
    merged_extra: dict[int, list[str]] = {}
    notes: list[str] = []
    out_parts: list[str] = []
    for k, (title, start, end) in enumerate(segments):
        if title is None:
            out_parts.extend(lines[start:end])
            continue
        if title in dup_titles:
            if k == keep_of[title]:
                seen_lines[k] = {line.strip() for line in lines[start + 1 : end] if line.strip()}
            else:
                extra = merged_extra.setdefault(keep_of[title], [])
                seen = seen_lines.setdefault(keep_of[title], set())
                moved = 0
                for line in lines[start + 1 : end]:
                    if not line.strip():
                        continue
                    if line.strip() in seen:
                        continue
                    extra.append(line)
                    seen.add(line.strip())
                    moved += 1
                notes.append(
                    f"同名节『{title}』×{len(groups[title])} 归并：前置节头移除，"
                    f"{moved} 实质行并入保留节尾（残项②收敛）"
                )
                continue
        out_parts.append(lines[start])
        out_parts.extend(lines[start + 1 : end])
        if k in merged_extra:
            out_parts.extend(merged_extra[k])
    result = "".join(out_parts)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result, notes


def _section_has_substance(section: str) -> bool:
    """V1 阈值同源判节实质：非标题非空行 ≥EMPTY_SECTION_MIN_LINES 且合计 ≥EMPTY_SECTION_MIN_CHARS。"""
    body = [
        line.strip()
        for line in section.splitlines()
        if line.strip() and not line.startswith("## ")
    ]
    return (
        len(body) >= EMPTY_SECTION_MIN_LINES
        and sum(len(line) for line in body) >= EMPTY_SECTION_MIN_CHARS
    )


def _ensure_runtime_asset_instantiation(text: str, employee_id: str) -> tuple[str, list[str]]:
    """任务 3（V2 张力处置）：「运行资产落点」节若为通用句（=模板桩同款行集，
    桩常量即 `- 宿主绑定说明：<binding>` + `- runtime cognition 私域：…或当前
    runtime cognition backend`），V2 判桩 fail。graft 时实例化席位专属行
    （含 <id> cognition 路径），使节必含非桩行 → 破桩。
    幂等判据：节内已有任一 SEAT_INSTANCE_LINE_PREFIXES 前缀行即跳过。"""
    notes: list[str] = []
    idx = text.rfind("## 运行资产落点")
    if idx < 0:
        return text, notes
    nxt = text.find("\n## ", idx + 1)
    end = len(text) if nxt < 0 else nxt + 1
    section = text[idx:end]
    if any(prefix in section for prefix in SEAT_INSTANCE_LINE_PREFIXES):
        return text, notes
    line = (
        f"- 员工实例资产：runtime cognition 私域下 `{employee_id}/` "
        "员工实例目录（阶段记忆、关系与社交连续性的落点）\n"
    )
    text = text[:end].rstrip("\n") + "\n" + line + "\n" + text[end:]
    notes.append("「运行资产落点」节实例化席位专属行（V2 破桩：<id> cognition 路径）")
    return text, notes


def _patch_section_lines(updated: str, old_text: str, title: str) -> tuple[str, int]:
    """V3 保真行级补差：节『title』新代已在时，旧代同节中新代没有的非空行
    原样并入新代节尾（内容新代赢=不覆盖既有行；补差不过词形校准——V3 比对
    的是旧代原文行 containment）。返回（新文本, 补差行数）。"""
    old_section = _extract_section(old_text, title)
    if old_section is None:
        return updated, 0
    idx = updated.rfind(f"## {title}")
    if idx < 0:
        return updated, 0
    nxt = updated.find("\n## ", idx + 1)
    end = len(updated) if nxt < 0 else nxt + 1
    existing = {line.strip() for line in updated[idx:end].splitlines() if line.strip()}
    add_lines = [
        line.rstrip()
        for line in old_section.splitlines()
        if line.strip() and not line.strip().startswith("## ") and line.strip() not in existing
    ]
    if not add_lines:
        return updated, 0
    block = "".join(f"{line}\n" for line in add_lines)
    updated = updated[:end].rstrip("\n") + "\n" + block + "\n" + updated[end:]
    return updated, len(add_lines)


def graft_boundary_piece(new_text: str, old_text: str, *, employee_id: str) -> tuple[str, list[str]]:
    """boundary 三件型（memory/colleagues/social）：新代为基底，缺的节从旧代 graft。"""
    notes: list[str] = []
    updated, wording = _apply_wording_updates(new_text)
    if wording:
        notes.append(f"新代词形校准: {'; '.join(wording)}")
    updated, merged = _collapse_duplicate_sections(updated)
    notes.extend(merged)
    for title in REQUIRED_SECTIONS:
        if title in _section_titles(updated):
            updated, patched = _patch_section_lines(updated, old_text, title)
            if patched:
                notes.append(f"节『{title}』新代已在（内容新代赢）；旧代行级补差 {patched} 行并入节尾（V3 保真）")
            else:
                notes.append(f"节『{title}』新代已在（内容新代赢，不覆盖）")
            continue
        old_section = _extract_section(old_text, title)
        if old_section is None:
            notes.append(f"节『{title}』旧代亦缺——标注候 CHO 人工灌注（勿擅断）")
            continue
        if not _section_has_substance(old_section):
            notes.append(f"节『{title}』旧代实质低于 V1 阈值——不 graft 弱节/空节，候 CHO 人工灌注")
            continue
        old_section, w = _apply_wording_updates(old_section)
        if w:
            notes.append(f"节『{title}』旧代词形校准: {'; '.join(w)}")
        updated = updated.rstrip("\n") + "\n\n" + old_section + "\n"
        notes.append(f"节『{title}』自旧代 graft（{len(old_section.splitlines())} 行）")
    # V4 双标记（boundary 三件统一）：TRICOMPANY_COGNITION_HOME 落「运行资产落点」
    # 节内 + 「源侧认知层契约」来源声明落「层契约」节内（通用结构句，非席位语义）。
    # 锚点取 rfind（最后同名节）——与 validator dict 消费语义一致，防多节残留期插错节。
    anchor = "## 运行资产落点"
    idx = updated.rfind(anchor)
    if COGNITION_MARKER not in updated and idx >= 0:
        line_end = updated.find("\n", idx)
        insert_at = len(updated) if line_end < 0 else line_end + 1
        updated = updated[:insert_at] + f"\n- runtime cognition 私域：`{COGNITION_MARKER}`（认知层状态与派生资产落点）\n" + updated[insert_at:]
        notes.append("TRICOMPANY_COGNITION_HOME 标记插入「运行资产落点」节内")
    elif COGNITION_MARKER not in updated:
        notes.append("标注：标记未落——「运行资产落点」节缺失，候 CHO 人工灌注")
    if "源侧认知层契约" not in updated:
        anchor = "## 层契约"
        idx = updated.rfind(anchor)
        if idx >= 0:
            line_end = updated.find("\n## ", idx + 1)
            insert_at = len(updated.rstrip("\n")) if line_end < 0 else line_end
            contract_line = "\n- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。\n"
            updated = updated[:insert_at].rstrip("\n") + "\n" + contract_line + updated[insert_at:].lstrip("\n")
            notes.append("「源侧认知层契约」来源声明插入层契约节内")
        else:
            notes.append("标注：「源侧认知层契约」未落——层契约节缺失，候 CHO 人工灌注")
    updated, inst = _ensure_runtime_asset_instantiation(updated, employee_id)
    notes.extend(inst)
    # 只读自检：forbidden marker 残留告警（禁删句不擅删，命中标 CHO；词形校准族
    # 未覆盖的「类行」变体由此兜底暴露）。
    for marker in FORBIDDEN_HOST_BINDING_MARKERS:
        if marker in updated:
            notes.append(f"标注：forbidden host-binding marker 残留：{marker}——候 CHO 人工处置（不擅删）")
    for marker in FORBIDDEN_CONSUMPTION_MARKERS:
        if marker in updated:
            notes.append(f"标注：forbidden consumption marker 残留：{marker}——候 CHO 人工处置（不擅删）")
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
    for suffix in ("memory", "colleagues", "social", "soul"):
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
            merged, notes = graft_boundary_piece(new_text, old_text, employee_id=employee_id)
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
    parser.add_argument(
        "--report-out",
        default=None,
        help="双向 diff 清单落盘路径（约定 docs/test/evidence/lg-025-m0e-graft/<seat>-diff.md）；缺省仅 stdout",
    )
    args = parser.parse_args()
    report = graft_employee(Path(args.source_root), args.employee_id, args.dry_run)
    text = "\n".join(report)
    print(text, end="" if text.endswith("\n") else "\n")
    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8", newline="\n")
        print(f"[report-out] {out_path}")


if __name__ == "__main__":
    main()
