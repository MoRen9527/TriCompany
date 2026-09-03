from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_cognition import build_ceo_chief_of_staff_kernel
from runtime.cognition.contracts.provider_contract import RecallQuery
from runtime.cognition.providers.repo_asset_provider import (
    RepoAssetSource,
    RepoBackedPrivateAssetProvider,
)


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
USER_CONTENT = "请把这轮经营判断写入 cognition"
ASSISTANT_CONTENT = "已桥接到 cognition durable memory"
SOURCE_AGENT_KIT_PARTS = ("TriCompany", "source-agents", "ceo-chief-of-staff")


def _write_asset(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")


class ChiefOfStaffBridgeValidationTest(unittest.TestCase):
    def test_repo_asset_provider_prefetches_durable_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_kit_root = root.joinpath(*SOURCE_AGENT_KIT_PARTS)
            memory_path = source_kit_root / "memory.agent.md"
            soul_path = source_kit_root / "ceo-chief-of-staff.soul.md"
            _write_asset(memory_path, "Memory", "项目级耐久记忆已经落仓库")
            _write_asset(soul_path, "Soul", "老板我在呢")

            provider = RepoBackedPrivateAssetProvider(
                actor_id=CHIEF_OF_STAFF_ID,
                asset_sources=(
                    RepoAssetSource("Memory", memory_path),
                    RepoAssetSource("Soul", soul_path),
                ),
            )

            results = list(
                provider.prefetch(
                    query=RecallQuery(
                        actor_id=CHIEF_OF_STAFF_ID,
                        namespaces=(f"employee/{CHIEF_OF_STAFF_ID}", "org/shared"),
                        text="请召回 durable memory",
                    )
                )
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].namespace, f"employee/{CHIEF_OF_STAFF_ID}")
            self.assertIn("项目级耐久记忆已经落仓库", results[0].content)
            self.assertIn("老板我在呢", results[0].content)

    def test_bootstrap_kernel_bridges_repo_assets_and_runtime_storage(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            source_kit_root = workspace_root.joinpath(*SOURCE_AGENT_KIT_PARTS)
            _write_asset(source_kit_root / "memory.agent.md", "Memory", "当前阶段总助耐久记忆")
            _write_asset(source_kit_root / "ceo-chief-of-staff.soul.md", "Soul", "自然、利落、有温度")
            _write_asset(source_kit_root / "ceo-chief-of-staff.colleagues.md", "Colleagues", "磨人是当前直接汇报对象")
            _write_asset(source_kit_root / "ceo-chief-of-staff.social.md", "Social", "非正式场景下优先叫磨人")

            kernel = build_ceo_chief_of_staff_kernel(
                storage_root=store_dir,
                workspace_root=workspace_root,
            )
            kernel.sync_turn(CHIEF_OF_STAFF_ID, USER_CONTENT, ASSISTANT_CONTENT)
            kernel.session_end(
                CHIEF_OF_STAFF_ID,
                [
                    {"role": "user", "content": USER_CONTENT},
                    {"role": "assistant", "content": ASSISTANT_CONTENT},
                ],
            )

            context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, "请召回小贾的 durable memory")

            self.assertIn("[repo-asset-bridge::employee/ceo-chief-of-staff]", context)
            self.assertIn("[builtin-markdown::employee/ceo-chief-of-staff]", context)
            self.assertIn("[org-shared::org/shared]", context)
            self.assertIn("当前阶段总助耐久记忆", context)
            self.assertIn("自然、利落、有温度", context)
            self.assertIn("磨人是当前直接汇报对象", context)
            self.assertIn("请把这轮经营判断写入 cognition", context)
            self.assertIn("已桥接到 cognition durable memory", context)


if __name__ == "__main__":
    unittest.main(verbosity=2)