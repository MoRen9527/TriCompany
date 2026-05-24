from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from runtime.cognition.contracts.provider_contract import ConsolidationWrite


def default_storage_root() -> Path:
    configured = os.environ.get("TRICOMPANY_COGNITION_HOME")
    if configured:
        return Path(configured)
    return Path.cwd() / ".tricompany-cognition"


class FileBackedCognitionStore:
    def __init__(self, storage_root: Path | str | None = None) -> None:
        self.storage_root = Path(storage_root) if storage_root is not None else default_storage_root()

    def path_for_namespace(self, namespace: str) -> Path:
        parts = namespace.split("/")
        return self.storage_root.joinpath(*parts).with_suffix(".md")

    def read_namespace(self, namespace: str) -> str:
        path = self.path_for_namespace(namespace)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def append_entry(
        self,
        namespace: str,
        *,
        title: str,
        body: str,
        provider_name: str,
    ) -> None:
        path = self.path_for_namespace(namespace)
        path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = (
            f"## {title}\n"
            f"- provider: {provider_name}\n"
            f"- timestamp: {timestamp}\n\n"
            f"{body.strip()}\n"
        )
        with path.open("a", encoding="utf-8") as handle:
            if path.stat().st_size > 0:
                handle.write("\n")
            handle.write(entry)

    def persist_consolidation_writes(
        self,
        writes: Iterable[ConsolidationWrite],
        *,
        provider_name: str,
    ) -> None:
        for write in writes:
            self.append_entry(
                write.namespace,
                title=write.reason,
                body=write.content,
                provider_name=provider_name,
            )