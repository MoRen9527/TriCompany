from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from runtime.cognition.contracts.wiki_source_contract import WikiSource
from runtime.cognition.kernel.wiki_frontmatter import split_frontmatter


class WikiSourceRegistry:
    _SUPPORTED_SUFFIXES = {".md", ".txt", ".json"}
    _IGNORED_NAMES = {"README.md", "source-template.md"}

    def __init__(self, inbox_root: str | Path) -> None:
        self.inbox_root = Path(inbox_root)

    def list_sources(self) -> list[WikiSource]:
        if not self.inbox_root.exists():
            return []

        sources: list[WikiSource] = []
        for path in sorted(self.inbox_root.iterdir()):
            if not path.is_file() or path.suffix.lower() not in self._SUPPORTED_SUFFIXES:
                continue
            if path.name in self._IGNORED_NAMES:
                continue
            sources.append(self._read_source(path))
        return sources

    def _read_source(self, path: Path) -> WikiSource:
        if path.suffix.lower() == ".json":
            return self._read_json_source(path)
        if path.suffix.lower() == ".md":
            return self._read_markdown_source(path)
        return self._read_text_source(path)

    def _read_markdown_source(self, path: Path) -> WikiSource:
        raw_text = path.read_text(encoding="utf-8")
        metadata, body = split_frontmatter(raw_text)
        return WikiSource(
            source_id=str(metadata.get("sourceId") or path.name),
            title=str(metadata.get("title") or _default_title(path)),
            source_type=str(metadata.get("sourceType") or "markdown-note"),
            source_path=path,
            topic_hints=_as_topics(metadata.get("topicHints")),
            trust_level=str(metadata.get("trustLevel") or "raw"),
            captured_at=str(metadata.get("capturedAt") or ""),
            body=body.strip(),
        )

    def _read_text_source(self, path: Path) -> WikiSource:
        return WikiSource(
            source_id=path.name,
            title=_default_title(path),
            source_type="text-note",
            source_path=path,
            topic_hints=(),
            trust_level="raw",
            captured_at="",
            body=path.read_text(encoding="utf-8").strip(),
        )

    def _read_json_source(self, path: Path) -> WikiSource:
        payload = json.loads(path.read_text(encoding="utf-8"))
        facts = payload.get("facts") or []
        if isinstance(facts, list):
            body = "\n".join(f"- {item}" for item in facts)
        else:
            body = json.dumps(payload, ensure_ascii=False, indent=2)
        return WikiSource(
            source_id=str(payload.get("sourceId") or path.name),
            title=str(payload.get("title") or _default_title(path)),
            source_type=str(payload.get("sourceType") or "json-record"),
            source_path=path,
            topic_hints=_as_topics(payload.get("topicHints")),
            trust_level=str(payload.get("trustLevel") or "raw"),
            captured_at=str(payload.get("capturedAt") or ""),
            body=body.strip(),
        )


def _default_title(path: Path) -> str:
    return path.stem.replace("-", " ").strip() or path.name


def _as_topics(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Iterable):
        topics: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                topics.append(text)
        return tuple(topics)
    return ()