"""loop_autoreview 单测（修 D-2 spawn env 注入面·2026-11-19·文件首建——旧态缺席承录）。"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    import importlib.util as _iu
    spec = _iu.spec_from_file_location(
        "lar_d2", "/srv/fleet/TriCompany/runtime/cognition/loop_autoreview.py")
    m = _iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class SpawnGlmEnvTest(unittest.TestCase):
    """修 D-2 供给切 GLM·spawn env 三键单测（notice-219 值席放行·零活体调用零值回显）。"""

    def _helper_with(self, tmpcfg, items, extra_env=None):
        m = _load_module()
        import json as _j
        cfg = Path(tmpcfg)
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "settings.json").write_text(
            _j.dumps({"updated_at": None, "items": items}), encoding="utf-8")
        env = {"TRIRMC_CONFIG_DIR": str(cfg)}
        env.update(extra_env or {})
        with mock.patch.dict(m.os.environ, env, clear=False):
            return m.read_glm_spawn_env()

    def test_trio_injected_when_token_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            env = self._helper_with(td, {"ANTHROPIC_AUTH_TOKEN": "tok-x",
                                         "ANTHROPIC_MODEL": "glm-5.3-flash"})
            self.assertIsNotNone(env)
            self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "tok-x")
            self.assertEqual(env["ANTHROPIC_MODEL"], "glm-5.3-flash")
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://open.bigmodel.cn/api/anthropic")

    def test_none_when_token_absent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            env = self._helper_with(td, {"ANTHROPIC_MODEL": "glm-5.3-flash"})
            self.assertIsNone(env)

    def test_none_when_settings_missing(self) -> None:
        m = _load_module()
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(m.os.environ, {"TRIRMC_CONFIG_DIR": td}, clear=False):
                self.assertIsNone(m.read_glm_spawn_env())

    def test_off_gate_escaping(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            env = self._helper_with(td, {"ANTHROPIC_AUTH_TOKEN": "tok-x"},
                                    extra_env={"TRICO_SPAWN_GLM": "off"})
            self.assertIsNone(env)

    def test_base_url_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            env = self._helper_with(td, {"ANTHROPIC_AUTH_TOKEN": "tok-x"},
                                    extra_env={"TRICO_GLM_BASE_URL": "https://proxy.example/anthropic"})
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://proxy.example/anthropic")

    def test_spawn_wiring_passes_env_to_subprocess(self) -> None:
        m = _load_module()
        captured = {}

        class FakeCompleted:
            returncode = 0
            stdout = "{}"
            stderr = ""

        def fake_run(cmd, capture_output, text, timeout, cwd, env=None):
            captured["env"] = env
            return FakeCompleted()

        with tempfile.TemporaryDirectory() as td:
            import json as _j
            cfg = Path(td) / "cfg"
            cfg.mkdir()
            (cfg / "settings.json").write_text(_j.dumps(
                {"items": {"ANTHROPIC_AUTH_TOKEN": "tok-y"}}), encoding="utf-8")
            env = {"TRIRMC_CONFIG_DIR": str(cfg), "DSH_BIN": "/bin/true"}
            with mock.patch.dict(m.os.environ, env, clear=False), \
                 mock.patch.object(m.os.path, "isfile", return_value=False), \
                 mock.patch.object(m.subprocess, "run", side_effect=fake_run):
                r = m.spawn_seat_session("cos", Path(td))
        self.assertEqual(r["rc"], 0)
        self.assertIsNotNone(captured["env"])
        self.assertEqual(captured["env"]["ANTHROPIC_AUTH_TOKEN"], "tok-y")
        self.assertIn("ANTHROPIC_BASE_URL", captured["env"])


if __name__ == "__main__":
    unittest.main()
