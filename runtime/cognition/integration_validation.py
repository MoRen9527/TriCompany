from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.org_shared import OrgSharedProvider


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
USER_CONTENT = "请把本轮验证结论沉淀为会议纪要"
ASSISTANT_CONTENT = "已整理为可回放的经营结论"


class ProviderBackedIntegrationValidationTest(unittest.TestCase):
    def test_private_shared_and_audit_storage_are_persisted_and_recalled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            kernel = MetaCognitionKernel()
            kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            kernel.register_provider(BuiltinMarkdownProvider(temp_dir))
            kernel.register_provider(OrgSharedProvider(temp_dir))

            kernel.sync_turn(
                actor_id=CHIEF_OF_STAFF_ID,
                user_content=USER_CONTENT,
                assistant_content=ASSISTANT_CONTENT,
            )
            messages = [
                {"role": "user", "content": USER_CONTENT},
                {"role": "assistant", "content": ASSISTANT_CONTENT},
            ]
            kernel.session_end(CHIEF_OF_STAFF_ID, messages)

            root = Path(temp_dir)
            private_path = root / "employee" / f"{CHIEF_OF_STAFF_ID}.md"
            shared_path = root / "org" / "shared.md"
            audit_path = root / "org" / "audit.md"

            self.assertTrue(private_path.exists())
            self.assertTrue(shared_path.exists())
            self.assertTrue(audit_path.exists())
            self.assertIn(USER_CONTENT, private_path.read_text(encoding="utf-8"))
            self.assertIn(ASSISTANT_CONTENT, shared_path.read_text(encoding="utf-8"))
            self.assertIn(CHIEF_OF_STAFF_ID, audit_path.read_text(encoding="utf-8"))

            reloaded_kernel = MetaCognitionKernel()
            reloaded_kernel.register_actor(
                actor_id=CHIEF_OF_STAFF_ID,
                role_name="ChiefOfStaff",
                display_name="小贾",
            )
            reloaded_kernel.register_provider(BuiltinMarkdownProvider(temp_dir))
            reloaded_kernel.register_provider(OrgSharedProvider(temp_dir))

            context = reloaded_kernel.prefetch_context(
                CHIEF_OF_STAFF_ID,
                "请召回本轮经营结论与会议纪要",
            )

            self.assertIn("<memory-context>", context)
            self.assertIn("[builtin-markdown::employee/ceo-chief-of-staff]", context)
            self.assertIn("[org-shared::org/shared]", context)
            self.assertIn(USER_CONTENT, context)
            self.assertIn(ASSISTANT_CONTENT, context)


if __name__ == "__main__":
    unittest.main(verbosity=2)