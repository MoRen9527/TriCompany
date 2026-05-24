from __future__ import annotations

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_inbox_root
from runtime.cognition.contracts.wiki_source_contract import WikiSource
from runtime.cognition.kernel.wiki_source_registry import WikiSourceRegistry


def ingest_chief_of_staff_sources(
    *,
    workspace_root: str | None = None,
) -> list[WikiSource]:
    registry = WikiSourceRegistry(chief_of_staff_inbox_root(workspace_root))
    return registry.list_sources()