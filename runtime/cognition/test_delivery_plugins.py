"""P0 registry 化白盒族（BOD 托转 138·CTO 门禁首闸绿 d54bda7af·方案卷 §3.1）。

覆盖面：
  · REGISTRY 三键=值域一致（mailbox=P2 候位不入册显式面）
  · 四件套契约面：name=旗标值/inject 服务声明（legacy 空+两 dsh 形）/apply 可调
  · validate_config 三形：legacy 零需绿/patch-runner 四参缺面点名/cli-adopt 三参面
  · run_deliver registry 查找+非法值 fail-visible 载值域
  · LegacyStagingPlugin.apply 端到端（双件落位+landed/staged 读数+dry 零落位）
  · re-export 等价面：loop_convene_auto 再出口=同对象（backward-compat 零漂移）
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cognition import delivery_plugins as dp
from runtime.cognition import loop_convene_auto as lca
from runtime.cognition.delivery_plugins import (
    DEFAULT_DELIVER_VIA,
    REGISTRY,
    VALID_DELIVER_VIA,
    CliAdoptPlugin,
    LegacyStagingPlugin,
    PatchRunnerPlugin,
    run_deliver,
)


class RegistryFace(unittest.TestCase):
    def test_registry_three_keys_equal_domain(self):
        self.assertEqual(set(REGISTRY), set(VALID_DELIVER_VIA))
        self.assertEqual(set(REGISTRY), {"legacy-staging", "patch-runner", "cli-adopt"})

    def test_mailbox_p2_not_registered(self):
        self.assertNotIn("mailbox", REGISTRY, "mailbox=P2 候位不入册（纳=加键零结构改）")

    def test_contract_quartet_face(self):
        for name, plugin in REGISTRY.items():
            self.assertEqual(plugin.name, name, f"{name}: name=旗标值一致")
            self.assertTrue(callable(plugin.apply), f"{name}: apply 可调")
            self.assertTrue(hasattr(plugin, "validate_config"), f"{name}: validate_config 在")
        self.assertEqual(LegacyStagingPlugin.inject, ())
        self.assertEqual(PatchRunnerPlugin.inject, ("dsh",))
        self.assertEqual(CliAdoptPlugin.inject, ("dsh",))


class ValidateConfigForms(unittest.TestCase):
    def test_legacy_zero_requirement(self):
        self.assertIsNone(LegacyStagingPlugin().validate_config(None))
        self.assertEqual(LegacyStagingPlugin().validate_config({"x": 1}), {"x": 1})

    def test_patch_runner_missing_key_named(self):
        with self.assertRaises(ValueError) as cm:
            PatchRunnerPlugin().validate_config({"dsh_bin": "b", "dsh_home": "h"})
        self.assertIn("runner_path", str(cm.exception))
        self.assertIn("dsh_install_anchor", str(cm.exception))

    def test_cli_adopt_three_key_face(self):
        cfg = {"dsh_bin": "b", "dsh_home": "h", "dsh_install_anchor": "a"}
        self.assertEqual(CliAdoptPlugin().validate_config(cfg), cfg, "cli-adopt 三参形零 runner_path 需")


class RunDeliverRegistry(unittest.TestCase):
    def test_invalid_value_fail_visible_with_domain(self):
        with self.assertRaises(ValueError) as cm:
            run_deliver(Path("/tmp"), [], "carrier-pigeon", {}, dry=False)
        self.assertIn("carrier-pigeon", str(cm.exception))

    def test_missing_config_message_shape_unchanged(self):
        with self.assertRaises(ValueError) as cm:
            run_deliver(Path("/tmp"), [], "patch-runner", None, dry=False)
        self.assertIn("deliver_config 缺席", str(cm.exception))
        self.assertIn("runner_path", str(cm.exception))


class LegacyStagingApply(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_stage_double_files_and_readout(self):
        dimb = {"verdict": "pending", "entries": []}
        out = LegacyStagingPlugin().apply({"run_dir": self.run_dir, "dimb": dimb}, [{"t": 1}], dry=False)
        self.assertTrue(out["staged"])
        self.assertEqual(len(out["landed"]), 2)
        for f in out["landed"]:
            self.assertTrue(Path(f).is_file())
        self.assertEqual(json.loads(Path(out["landed"][0]).read_text(encoding="utf-8")), [{"t": 1}])
        self.assertEqual(json.loads(Path(out["landed"][1]).read_text(encoding="utf-8")), dimb)
        self.assertEqual(out["form"], DEFAULT_DELIVER_VIA)

    def test_dry_zero_land(self):
        out = LegacyStagingPlugin().apply({"run_dir": self.run_dir, "dimb": {}}, [], dry=True)
        self.assertFalse(out["staged"])
        self.assertEqual(out["landed"], [])
        self.assertFalse((self.run_dir / "convene").exists(), "dry=零落位")


class ReexportIdentity(unittest.TestCase):
    def test_reexports_same_objects(self):
        # backward-compat：loop_convene_auto 再出口=同一对象（白盒 import 面零改保障）
        self.assertIs(lca.seat_session_id, dp.seat_session_id)
        self.assertIs(lca.build_patch_runner_overlay, dp.build_patch_runner_overlay)
        self.assertIs(lca.read_deliver_via, dp.read_deliver_via)
        self.assertIs(lca.run_deliver, dp.run_deliver)
        self.assertEqual(lca.DEFAULT_DELIVER_VIA, dp.DEFAULT_DELIVER_VIA)


if __name__ == "__main__":
    unittest.main()
