from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.org_shared import OrgSharedProvider


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
FIRST_USER_CONTENT = "请记录第一次经营复盘"
FIRST_ASSISTANT_CONTENT = "第一次经营复盘已归档"
SECOND_USER_CONTENT = "请记录第二次经营复盘"
SECOND_ASSISTANT_CONTENT = "第二次经营复盘已归档"
AUDIT_USER_CONTENT = "请归档本轮审计信息"
AUDIT_ASSISTANT_CONTENT = "本轮审计信息已归档"


def build_kernel() -> MetaCognitionKernel:
    kernel = MetaCognitionKernel()
    kernel.register_actor(
        actor_id=CHIEF_OF_STAFF_ID,
        role_name="ChiefOfStaff",
        display_name="小贾",
    )
    kernel.register_provider(BuiltinMarkdownProvider())
    kernel.register_provider(OrgSharedProvider())
    return kernel


class ProductionBackendValidationTest(unittest.TestCase):
    def test_env_configured_backend_persists_private_shared_and_audit_across_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"TRICOMPANY_COGNITION_HOME": temp_dir}, clear=False):
                first_kernel = build_kernel()
                first_kernel.sync_turn(
                    CHIEF_OF_STAFF_ID,
                    FIRST_USER_CONTENT,
                    FIRST_ASSISTANT_CONTENT,
                )
                first_kernel.session_end(
                    CHIEF_OF_STAFF_ID,
                    [
                        {"role": "user", "content": FIRST_USER_CONTENT},
                        {"role": "assistant", "content": FIRST_ASSISTANT_CONTENT},
                    ],
                )

                second_kernel = build_kernel()
                second_kernel.sync_turn(
                    CHIEF_OF_STAFF_ID,
                    SECOND_USER_CONTENT,
                    SECOND_ASSISTANT_CONTENT,
                )
                second_kernel.session_end(
                    CHIEF_OF_STAFF_ID,
                    [
                        {"role": "user", "content": SECOND_USER_CONTENT},
                        {"role": "assistant", "content": SECOND_ASSISTANT_CONTENT},
                    ],
                )

                root = Path(temp_dir)
                private_path = root / "employee" / f"{CHIEF_OF_STAFF_ID}.md"
                shared_path = root / "org" / "shared.md"
                audit_path = root / "org" / "audit.md"

                self.assertTrue(private_path.exists())
                self.assertTrue(shared_path.exists())
                self.assertTrue(audit_path.exists())

                private_text = private_path.read_text(encoding="utf-8")
                shared_text = shared_path.read_text(encoding="utf-8")
                audit_text = audit_path.read_text(encoding="utf-8")

                self.assertIn(FIRST_USER_CONTENT, private_text)
                self.assertIn(SECOND_USER_CONTENT, private_text)
                self.assertIn(FIRST_ASSISTANT_CONTENT, shared_text)
                self.assertIn(SECOND_ASSISTANT_CONTENT, shared_text)
                self.assertEqual(audit_text.count("## session-audit-trace"), 2)
                self.assertEqual(audit_text.count("- provider: org-shared"), 2)

                third_kernel = build_kernel()
                context = third_kernel.prefetch_context(
                    CHIEF_OF_STAFF_ID,
                    "请召回两次经营复盘的结论",
                )
                self.assertIn(FIRST_USER_CONTENT, context)
                self.assertIn(SECOND_USER_CONTENT, context)
                self.assertIn(FIRST_ASSISTANT_CONTENT, context)
                self.assertIn(SECOND_ASSISTANT_CONTENT, context)

    def test_audit_backend_records_namespace_metadata_and_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"TRICOMPANY_COGNITION_HOME": temp_dir}, clear=False):
                kernel = build_kernel()
                kernel.session_end(
                    CHIEF_OF_STAFF_ID,
                    [
                        {"role": "user", "content": AUDIT_USER_CONTENT},
                        {"role": "assistant", "content": AUDIT_ASSISTANT_CONTENT},
                    ],
                )

                audit_text = (Path(temp_dir) / "org" / "audit.md").read_text(encoding="utf-8")
                self.assertIn("- timestamp:", audit_text)
                self.assertIn("- actor: ceo-chief-of-staff", audit_text)
                self.assertIn("- private-namespace: employee/ceo-chief-of-staff", audit_text)
                self.assertIn("- org-shared-namespace: org/shared", audit_text)
                self.assertIn("- audit-namespace: org/audit", audit_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)