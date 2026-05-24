from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.contracts.wiki_source_contract import WikiPage, WikiSource


def compile_wiki_page(
    sources: list[WikiSource],
    *,
    page_id: str,
    title: str,
    page_path: Path,
    updated_at: str,
    page_status: str = "working",
    approval_status: str = "draft",
    reviewed_by: str = "",
    reviewed_at: str = "",
    approval_note: str = "",
    topic_tags: tuple[str, ...] | None = None,
    reviewer_route: tuple[str, ...] = (),
    primary_reviewer: str = "",
    approval_sla_hours: int | None = None,
    approval_due_at: str = "",
) -> WikiPage:
    if not sources:
        raise ValueError("At least one wiki source is required to compile a page.")

    ranked_sources = _rank_sources(sources)
    source_refs = tuple(source.source_id for source in ranked_sources)
    resolved_topic_tags = topic_tags or _collect_topic_tags(ranked_sources)
    extracted_points = _extract_points(ranked_sources)
    facts = tuple(extracted_points[:6]) or ("已接收首批总助原始资料，待继续补充。",)
    judgments = _extract_judgments(extracted_points)
    open_questions = _extract_open_questions(extracted_points)
    summary = (
        f"本页基于 {len(sources)} 份总助 inbox 资料整理而成，当前主题聚焦于 "
        f"{title} 的阶段推进情况。"
    )

    return WikiPage(
        page_id=page_id,
        title=title,
        topic_tags=resolved_topic_tags,
        page_path=page_path,
        page_status=page_status,
        updated_at=updated_at,
        source_refs=source_refs,
        summary=summary,
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        approval_status=approval_status or _default_approval_status(page_status),
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        approval_note=approval_note,
        reviewer_route=reviewer_route,
        primary_reviewer=primary_reviewer,
        approval_sla_hours=approval_sla_hours,
        approval_due_at=approval_due_at,
    )


def _default_approval_status(page_status: str) -> str:
    normalized = page_status.lower()
    if normalized == "stable":
        return "approved"
    if normalized == "reviewing":
        return "pending"
    return "draft"


def _collect_topic_tags(sources: list[WikiSource]) -> tuple[str, ...]:
    counter: Counter[str] = Counter()
    for source in sources:
        counter.update(tag for tag in source.topic_hints if tag)

    ordered_tags = [tag for tag, _ in counter.most_common()]
    if "chief-of-staff" not in ordered_tags:
        ordered_tags.insert(0, "chief-of-staff")
    return tuple(ordered_tags[:6])


def _extract_points(sources: list[WikiSource]) -> list[str]:
    points: list[str] = []
    seen: set[str] = set()
    for source in sources:
        for line in source.body.splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            if cleaned.startswith("- ") or cleaned.startswith("* "):
                cleaned = cleaned[2:].strip()
            if cleaned in seen:
                continue
            seen.add(cleaned)
            points.append(cleaned)
    return points


def _extract_judgments(points: list[str]) -> tuple[str, ...]:
    keywords = ("判断", "应", "需要", "目标", "优先", "当前")
    matches = [point for point in points if any(keyword in point for keyword in keywords)]
    if not matches:
        matches = points[:3]
    return tuple(matches[:4]) or ("当前仍处于首版 LLM wiki 整理闭环验证阶段。",)


def _extract_open_questions(points: list[str]) -> tuple[str, ...]:
    keywords = ("待确认", "问题", "?", "？")
    matches = [point for point in points if any(keyword in point for keyword in keywords)]
    if matches:
        return tuple(matches[:4])
    return (
        "下一步是把 stable 页面扩展到更多总助主题，而不是只停留在当前状态页。",
        "后续需要把 `reviewing -> stable` 的治理规则细化为更正式的审批语义与 stop conditions。",
    )


def _rank_sources(sources: list[WikiSource]) -> list[WikiSource]:
    return sorted(
        sources,
        key=lambda source: (
            _trust_rank(source.trust_level),
            _captured_at_rank(source.captured_at),
            source.source_id,
        ),
        reverse=True,
    )


def _trust_rank(trust_level: str) -> int:
    normalized = trust_level.strip().lower()
    if normalized == "approved":
        return 3
    if normalized == "curated":
        return 2
    if normalized == "raw":
        return 1
    return 0


def _captured_at_rank(value: str) -> float:
    text = value.strip()
    if not text:
        return 0.0
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()