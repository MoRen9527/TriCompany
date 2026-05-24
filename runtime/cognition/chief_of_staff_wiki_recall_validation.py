from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_cognition import build_ceo_chief_of_staff_kernel
from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_wiki_root


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"


class ChiefOfStaffWikiRecallValidationTest(unittest.TestCase):
    def test_only_stable_wiki_pages_enter_recall_context(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            wiki_root = chief_of_staff_wiki_root(workspace_root)
            wiki_root.mkdir(parents=True, exist_ok=True)

            self._write_page(
                wiki_root / "stable-page.md",
                page_id="stable-page",
                title="稳定页",
                page_status="stable",
                body="## 摘要\n\n稳定页可进入 recall。\n",
            )
            self._write_page(
                wiki_root / "working-page.md",
                page_id="working-page",
                title="工作页",
                page_status="working",
                body="## 摘要\n\n工作页当前不能进入 recall。\n",
            )

            kernel = build_ceo_chief_of_staff_kernel(
                storage_root=store_dir,
                workspace_root=workspace_root,
                include_repo_assets=False,
                include_stable_wiki_recall=True,
            )
            context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, "请召回总助稳定 wiki 页面")

            self.assertIn("[chief-of-staff-wiki::org/shared]", context)
            self.assertIn("稳定页可进入 recall", context)
            self.assertNotIn("工作页当前不能进入 recall", context)
            self.assertNotIn("working-page", context)

    def test_all_wiki_pages_enter_recall_context_when_all_page_policy_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            wiki_root = chief_of_staff_wiki_root(workspace_root)
            wiki_root.mkdir(parents=True, exist_ok=True)

            self._write_page(
                wiki_root / "stable-page.md",
                page_id="stable-page",
                title="稳定页",
                page_status="stable",
                body="## 摘要\n\n稳定页可进入 recall。\n",
            )
            self._write_page(
                wiki_root / "working-page.md",
                page_id="working-page",
                title="工作页",
                page_status="working",
                body="## 摘要\n\n工作页在全量 recall 模式下也应可见。\n",
            )

            kernel = build_ceo_chief_of_staff_kernel(
                storage_root=store_dir,
                workspace_root=workspace_root,
                include_repo_assets=False,
                include_all_wiki_recall=True,
            )
            context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, "请召回总助 wiki 页面")

            self.assertIn("稳定页可进入 recall", context)
            self.assertIn("工作页在全量 recall 模式下也应可见", context)
            self.assertIn("approval-status: draft", context)

    def test_stable_wiki_recall_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as store_dir:
            workspace_root = Path(workspace_dir)
            wiki_root = chief_of_staff_wiki_root(workspace_root)
            wiki_root.mkdir(parents=True, exist_ok=True)
            self._write_page(
                wiki_root / "stable-page.md",
                page_id="stable-page",
                title="稳定页",
                page_status="stable",
                body="## 摘要\n\n稳定页可进入 recall。\n",
            )

            kernel = build_ceo_chief_of_staff_kernel(
                storage_root=store_dir,
                workspace_root=workspace_root,
                include_repo_assets=False,
                include_stable_wiki_recall=False,
            )
            context = kernel.prefetch_context(CHIEF_OF_STAFF_ID, "请召回总助稳定 wiki 页面")
            self.assertNotIn("稳定页可进入 recall", context)

    def _write_page(
        self,
        path: Path,
        *,
        page_id: str,
        title: str,
        page_status: str,
        body: str,
    ) -> None:
        path.write_text(
            "---\n"
            f"pageId: {page_id}\n"
            f"title: {title}\n"
            "topicTags:\n"
            "  - chief-of-staff\n"
            f"pageStatus: {page_status}\n"
            "updatedAt: 2026-04-20T23:30:00+08:00\n"
            "approvalStatus: draft\n"
            "sourceRefs:\n"
            "  - test-source\n"
            "---\n\n"
            f"{body}",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)