from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.host_object_generation import write_host_binding_profiles


class EmployeeHostBindingProfileGenerationValidation(unittest.TestCase):
    def test_writes_rd_trainer_live_binding_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("rd-trainer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "rd-trainer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriCompany/.github/agents/rd-trainer.agent.md")
            self.assertEqual(profile["supportManifest"], "TriCompany-copilot-host-assets/host-object-manifest.json")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/rd-trainer")
            self.assertEqual(profile["runtimeNamespaces"][0]["namespace"], "employee/rd-trainer")

    def test_project_trainer_alias_writes_rd_trainer_binding_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("project-trainer",))

            self.assertEqual(len(profile_paths), 1)
            self.assertEqual(profile_paths[0].name, "rd-trainer.json")
            self.assertFalse((source_root / ".github" / "binding-profiles" / "project-trainer.json").exists())
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["employeeId"], "rd-trainer")
            self.assertEqual(profile["objectSetId"], "rd-trainer-knowledge-workspace-v0.1")

    def test_writes_cho_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-human-resources-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-human-resources-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-human-resources-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-human-resources-officer")
            notes = " ".join(profile["notes"])
            self.assertIn("enabled as an independent live host agent", notes)
            self.assertIn("handoff completion tracking", notes)

    def test_writes_cao_binding_profile_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(source_root, employee_ids=("chief-administrative-officer",))

            self.assertEqual(len(profile_paths), 1)
            profile = json.loads(profile_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(profile["bindingProfileId"], "chief-administrative-officer-host-binding-v0.1")
            self.assertEqual(profile["hostStage"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["status"], "current-copilot-host-live")
            self.assertEqual(profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-administrative-officer.agent.md")
            self.assertEqual(profile["supportObjects"][0]["path"], "TriCompany-copilot-host-assets/knowledge/roles/chief-administrative-officer")

    def test_writes_live_binding_profiles_for_current_employees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            profile_paths = write_host_binding_profiles(
                source_root,
                employee_ids=("ceo-chief-of-staff", "chief-product-officer", "chief-technology-officer"),
            )

            self.assertEqual(len(profile_paths), 3)

            ceo_profile = json.loads((source_root / ".github" / "binding-profiles" / "ceo-chief-of-staff.json").read_text(encoding="utf-8"))
            self.assertEqual(ceo_profile["liveEntry"]["path"], "TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md")
            self.assertEqual(ceo_profile["hostStage"], "current-copilot-host-live")
            self.assertIn("legacy-chief-of-staff-knowledge-object-set", [item["kind"] for item in ceo_profile["supportObjects"]])

            cpo_profile = json.loads((source_root / ".github" / "binding-profiles" / "chief-product-officer.json").read_text(encoding="utf-8"))
            self.assertEqual(cpo_profile["employeeDisplayName"], "小乔")
            self.assertEqual(cpo_profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-product-officer.agent.md")
            self.assertIn("layer contracts only", " ".join(cpo_profile["notes"]))

            cto_profile = json.loads((source_root / ".github" / "binding-profiles" / "chief-technology-officer.json").read_text(encoding="utf-8"))
            self.assertEqual(cto_profile["employeeDisplayName"], "小狄")
            self.assertEqual(cto_profile["liveEntry"]["path"], "TriMetaverse/.github/agents/chief-technology-officer.agent.md")


if __name__ == "__main__":
    unittest.main()