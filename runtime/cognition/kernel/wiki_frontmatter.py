from __future__ import annotations


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    closing_marker = text.find("\n---\n", 4)
    if closing_marker == -1:
        return {}, text

    raw_frontmatter = text[4:closing_marker]
    body = text[closing_marker + 5 :]
    return parse_frontmatter(raw_frontmatter), body


def parse_frontmatter(raw_frontmatter: str) -> dict[str, object]:
    metadata: dict[str, object] = {}
    current_list_key: str | None = None

    for line in raw_frontmatter.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("- ") and current_list_key is not None:
            metadata.setdefault(current_list_key, [])
            items = metadata[current_list_key]
            if isinstance(items, list):
                items.append(stripped[2:].strip())
            continue

        current_list_key = None
        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not value:
            metadata[key] = []
            current_list_key = key
            continue

        metadata[key] = value

    return metadata


def metadata_string_tuple(metadata: dict[str, object], key: str) -> tuple[str, ...]:
    value = metadata.get(key)
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()