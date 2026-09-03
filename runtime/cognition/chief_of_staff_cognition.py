from __future__ import annotations

from pathlib import Path
from typing import Iterable

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_wiki_root
from runtime.cognition.contracts.provider_contract import CognitionProvider
from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.chief_of_staff_wiki import (
    ChiefOfStaffAllWikiProvider,
    ChiefOfStaffStableWikiProvider,
)
from runtime.cognition.providers.org_shared import OrgSharedProvider
from runtime.cognition.providers.repo_asset_provider import (
    RepoAssetSource,
    RepoBackedPrivateAssetProvider,
)

CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
CHIEF_OF_STAFF_ROLE_NAME = "ChiefOfStaff"
CHIEF_OF_STAFF_DISPLAY_NAME = "小贾"
CHIEF_OF_STAFF_MEMORY_FILE_NAME = "memory.agent.md"


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_ceo_chief_of_staff_asset_sources(
    workspace_root: str | Path | None = None,
) -> tuple[RepoAssetSource, ...]:
    root = Path(workspace_root) if workspace_root is not None else _workspace_root()
    source_kit_root = _source_agent_kit_root(root)
    return (
        RepoAssetSource(
            label="Chief-of-staff durable memory",
            path=source_kit_root / CHIEF_OF_STAFF_MEMORY_FILE_NAME,
        ),
        RepoAssetSource(
            label="Chief-of-staff personality",
            path=source_kit_root / "ceo-chief-of-staff.soul.md",
        ),
        RepoAssetSource(
            label="Chief-of-staff work relationships",
            path=source_kit_root / "ceo-chief-of-staff.colleagues.md",
        ),
        RepoAssetSource(
            label="Chief-of-staff social continuity",
            path=source_kit_root / "ceo-chief-of-staff.social.md",
        ),
    )


def _source_agent_kit_root(root: Path) -> Path:
    # 现役基准（新代）优先：TriCompany/source-agents/<id>；
    # 旧形态（.github/source-agents/<id>）降为兜底，旧代文件退役（M0f）后移除兜底段。
    candidates = (
        root / "TriCompany" / "source-agents" / CHIEF_OF_STAFF_ID,
        root / "source-agents" / CHIEF_OF_STAFF_ID,
        root.parent / "TriCompany" / "source-agents" / CHIEF_OF_STAFF_ID,
        root.parent.parent / "TriCompany" / "source-agents" / CHIEF_OF_STAFF_ID,
        root / ".github" / "source-agents" / CHIEF_OF_STAFF_ID,
        root / "TriCompany" / ".github" / "source-agents" / CHIEF_OF_STAFF_ID,
        root.parent / "TriCompany" / ".github" / "source-agents" / CHIEF_OF_STAFF_ID,
        root.parent.parent / "TriCompany" / ".github" / "source-agents" / CHIEF_OF_STAFF_ID,
    )
    for candidate in candidates:
        if (candidate / CHIEF_OF_STAFF_MEMORY_FILE_NAME).exists():
            return candidate
    return root / "TriCompany" / "source-agents" / CHIEF_OF_STAFF_ID


def build_ceo_chief_of_staff_kernel(
    *,
    storage_root: str | None = None,
    workspace_root: str | Path | None = None,
    include_repo_assets: bool = True,
    include_stable_wiki_recall: bool = False,
    include_all_wiki_recall: bool = False,
    extra_providers: Iterable[CognitionProvider] | None = None,
) -> MetaCognitionKernel:
    kernel = MetaCognitionKernel()
    kernel.register_actor(
        actor_id=CHIEF_OF_STAFF_ID,
        role_name=CHIEF_OF_STAFF_ROLE_NAME,
        display_name=CHIEF_OF_STAFF_DISPLAY_NAME,
    )
    kernel.register_provider(BuiltinMarkdownProvider(storage_root))
    kernel.register_provider(OrgSharedProvider(storage_root))

    if include_repo_assets:
        kernel.register_provider(
            RepoBackedPrivateAssetProvider(
                actor_id=CHIEF_OF_STAFF_ID,
                asset_sources=default_ceo_chief_of_staff_asset_sources(workspace_root),
            )
        )

    if include_all_wiki_recall:
        kernel.register_provider(
            ChiefOfStaffAllWikiProvider(
                actor_id=CHIEF_OF_STAFF_ID,
                wiki_root=chief_of_staff_wiki_root(workspace_root),
            )
        )
    elif include_stable_wiki_recall:
        kernel.register_provider(
            ChiefOfStaffStableWikiProvider(
                actor_id=CHIEF_OF_STAFF_ID,
                wiki_root=chief_of_staff_wiki_root(workspace_root),
            )
        )

    for provider in extra_providers or ():
        kernel.register_provider(provider)

    return kernel