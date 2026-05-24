from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.cognition.contracts.wiki_page_spec_contract import WikiPageSpec
from runtime.cognition.contracts.wiki_source_contract import WikiSource


class WikiPageSpecRegistry:
    def __init__(self, spec_path: str | Path) -> None:
        self.spec_path = Path(spec_path)

    def list_specs(self) -> list[WikiPageSpec]:
        if not self.spec_path.exists():
            return []
        payload = json.loads(self.spec_path.read_text(encoding="utf-8"))
        raw_specs = payload if isinstance(payload, list) else payload.get("pageSpecs") or []
        specs: list[WikiPageSpec] = []
        for raw_item in raw_specs:
            if not isinstance(raw_item, dict):
                continue
            spec = _load_spec(raw_item)
            if spec is not None:
                specs.append(spec)
        return specs

    def load_spec(self, spec_id: str) -> WikiPageSpec | None:
        normalized = spec_id.strip()
        if not normalized:
            return None
        for spec in self.list_specs():
            if spec.spec_id == normalized:
                return spec
        return None

    def find_by_page_id(self, page_id: str) -> WikiPageSpec | None:
        normalized = page_id.strip()
        if not normalized:
            return None
        for spec in self.list_specs():
            if spec.page_id == normalized:
                return spec
        return None


def select_sources_for_page_spec(sources: list[WikiSource], spec: WikiPageSpec) -> list[WikiSource]:
    include_topics = {_normalize_topic(item) for item in spec.include_topics if _normalize_topic(item)}
    exclude_topics = {_normalize_topic(item) for item in spec.exclude_topics if _normalize_topic(item)}
    source_ids = {item.strip() for item in spec.source_ids if item.strip()}
    keyword_hints = tuple(item.strip().lower() for item in spec.keyword_hints if item.strip())

    if not include_topics and not exclude_topics and not source_ids and not keyword_hints:
        return list(sources)

    scored: list[tuple[int, float, WikiSource]] = []
    for source in sources:
        normalized_topics = {_normalize_topic(item) for item in source.topic_hints if _normalize_topic(item)}
        if exclude_topics and normalized_topics & exclude_topics:
            continue

        haystack = "\n".join(
            [
                source.source_id,
                source.title,
                source.source_type,
                source.body,
                " ".join(source.topic_hints),
            ]
        ).lower()
        topic_matches = include_topics & normalized_topics
        keyword_matches = tuple(keyword for keyword in keyword_hints if keyword in haystack)
        source_id_match = source.source_id in source_ids

        if include_topics or source_ids or keyword_hints:
            if not topic_matches and not source_id_match and not keyword_matches:
                continue

        score = 0
        if source_id_match:
            score += 100
        score += len(topic_matches) * 10
        score += len(keyword_matches) * 4
        score += _trust_rank(source.trust_level)
        scored.append((score, _captured_at_rank(source.captured_at), source))

    ranked = [item[2] for item in sorted(scored, key=lambda item: (item[0], item[1], item[2].source_id), reverse=True)]
    if spec.max_sources is not None:
        return ranked[: spec.max_sources]
    return ranked


def _load_spec(payload: dict[str, Any]) -> WikiPageSpec | None:
    spec_id = str(payload.get("specId") or "").strip()
    page_id = str(payload.get("pageId") or "").strip()
    title = str(payload.get("title") or "").strip()
    if not spec_id or not page_id or not title:
        return None
    max_sources = _maybe_int(payload.get("maxSources"))
    approval_sla_hours = _maybe_int(payload.get("approvalSlaHours"))
    return WikiPageSpec(
        spec_id=spec_id,
        page_id=page_id,
        title=title,
        page_status=str(payload.get("pageStatus") or "working"),
        topic_tags=_string_tuple(payload.get("topicTags")),
        include_topics=_string_tuple(payload.get("includeTopics")),
        exclude_topics=_string_tuple(payload.get("excludeTopics")),
        keyword_hints=_string_tuple(payload.get("keywordHints")),
        source_ids=_string_tuple(payload.get("sourceIds")),
        reviewer_roles=_string_tuple(payload.get("reviewerRoles")),
        primary_reviewer=str(payload.get("primaryReviewer") or "").strip(),
        approval_sla_hours=approval_sla_hours,
        max_sources=max_sources,
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                items.append(text)
        return tuple(items)
    return ()


def _maybe_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _normalize_topic(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _trust_rank(trust_level: str) -> int:
    normalized = trust_level.strip().lower()
    if normalized == "approved":
        return 30
    if normalized == "curated":
        return 20
    if normalized == "raw":
        return 10
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