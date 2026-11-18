"""v3 deliver_via 投递面白盒族（BOD 托转 133·CTO 一审绿·V2-2 白盒族同构）。

覆盖面（方案卷 §六.2）：
  · deliver_via 门控：缺席=缺省 legacy（零行为漂移）/非法值=legacy+warn/三值域
  · seat 映射：m-duty-<suffix>→r-duty-<suffix>·非映射表形 fail-visible（禁隐式猜测）
  · overlay 生成：disable headless-runner+insert fsd-adopt-runner·插值面受限字符集
  · dry 面：零文件零子进程（预演读数=overlay 预览+letter 字节计数）
  · legacy 缺省零漂移：run_auto_segment 全链与 V2-2 形等价（staging 双件落位）
  · patch-runner 端到端：fake dsh bin（sh 脚本回 JSON 读数）——readout 收集+
    tmp 随毕清理
  · cli-adopt 端到端：stdin `-` 形（fake bin 读 stdin 回读数）
  · fail-visible：bin 非零 rc=读数记录不中断/D-46 防御=letter 回显检出/缺
    deliver_config=_ValueError/读数非 JSON
  · manual 形零投递
"""
from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from runtime.cognition.loop_convene_auto import (
    DEFAULT_DELIVER_VIA,
    VALID_DELIVER_VIA,
    build_patch_runner_overlay,
    read_deliver_via,
    run_auto_segment,
    run_deliver,
    seat_session_id,
)

FAKE_DSH_BIN = r"""#!/bin/sh
# fake dsh: patch-runner 形（--patch）回 fsd-adopt-runner 读数；cli-adopt 形
# （--session-id + stdin -）回读数。stdin 若有 letter 回显=零（D-46 承面）。
for a in "$@"; do
  case "$a" in
    --patch) FORM=patch ;;
    --session-id) FORM=adopt ;;
  esac
done
if [ "$FORM" = "patch" ]; then
  echo '{"event":"fsd-adopt-runner","seat":"x","sessionId":"x","outcome":"adopted","mode":"queue","flushed":true}'
  exit 0
fi
cat > /dev/null
echo '{"event":"fsd-adopt-runner","seat":"x","sessionId":"x","outcome":"created","mode":"queue","flushed":true}'
exit 0
"""

ECHO_DSH_BIN = r"""#!/bin/sh
# evil bin: 回显 stdin（D-46 防御面触发用）
cat
"""


def _write_bin(dirpath: str, content: str) -> str:
    p = Path(dirpath) / "fake-dsh.sh"
    p.write_text(content, encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _cfg(bin_path: str, **over):
    cfg = {
        "dsh_bin": bin_path,
        "dsh_home": "/tmp/fake-dsh-home",
        "dsh_install_anchor": "/srv/fleet/dsh",
        "runner_path": "/srv/fleet/TriModel/dist/src/dsh-adopt/runner.js",
        "mode": "queue",
    }
    cfg.update(over)
    return cfg


def _trigger_doc(d: Path, **fields):
    d.mkdir(parents=True, exist_ok=True)
    (d / "loop-convene.json").write_text(json.dumps(fields), encoding="utf-8")


class DeliverViaGate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_absent_failsafe_default(self):
        via, warn = read_deliver_via(self.d / "no-such-dir")
        self.assertEqual(via, DEFAULT_DELIVER_VIA)
        self.assertIsNone(warn)

    def test_invalid_value_failsafe_with_warn(self):
        _trigger_doc(self.d, convene_mode="auto", deliver_via="carrier-pigeon")
        via, warn = read_deliver_via(self.d)
        self.assertEqual(via, DEFAULT_DELIVER_VIA)
        self.assertIn("carrier-pigeon", warn or "")

    def test_three_valid_values(self):
        for v in VALID_DELIVER_VIA:
            _trigger_doc(self.d, convene_mode="auto", deliver_via=v)
            via, warn = read_deliver_via(self.d)
            self.assertEqual(via, v)
            self.assertIsNone(warn)


class SeatMapping(unittest.TestCase):
    def test_mapping_table_form(self):
        self.assertEqual(seat_session_id("m-duty-cto"), "r-duty-cto")
        self.assertEqual(seat_session_id("m-duty-cos"), "r-duty-cos")

    def test_narrative_seat_form(self):
        # V2-1 召集件 target_seat=叙事席名形（SEATS 元组）
        self.assertEqual(seat_session_id("CTO"), "r-duty-cto")
        self.assertEqual(seat_session_id("COS"), "r-duty-cos")

    def test_passthrough_forms_bod135_fix(self):
        # BOD 裁135 修①：已形直通（产出形对齐校验形·两函数一致化）
        self.assertEqual(seat_session_id("r-duty-cto"), "r-duty-cto", "席名形直通")
        self.assertEqual(
            seat_session_id("b38ba22d-9f06-4443-b295-c5825026404a"),
            "b38ba22d-9f06-4443-b295-c5825026404a", "裸 UUID 直通（河源实弹存量会话形）")
        self.assertEqual(
            seat_session_id("session-b38ba22d-9f06-4443-b295-c5825026404a"),
            "session-b38ba22d-9f06-4443-b295-c5825026404a", "session-<uuid> 原生形直通")

    def test_unknown_prefix_fail_visible(self):
        with self.assertRaises(ValueError):
            seat_session_id("bod")
        with self.assertRaises(ValueError):
            seat_session_id("x-duty-cto")

    def test_mapped_result_in_shape(self):
        sid = seat_session_id("m-duty-cto")
        import re
        self.assertTrue(re.match(r"^r-duty-[a-z0-9][a-z0-9-]*$", sid))


class Overlay(unittest.TestCase):
    def test_overlay_shape(self):
        yml = build_patch_runner_overlay("/srv/fleet/TriModel/dist/src/dsh-adopt/runner.js",
                                         "r-duty-cto", "queue", "/tmp/l.txt", "/srv/fleet/dsh", "r-duty-cto")
        self.assertIn("id: headless-runner", yml)
        self.assertIn("disabled: true", yml)
        self.assertIn("id: fsd-adopt-runner", yml)
        self.assertIn("name: /srv/fleet/TriModel/dist/src/dsh-adopt/runner.js", yml)
        self.assertIn("letterFile: /tmp/l.txt", yml)
        self.assertIn("dshInstallAnchor: /srv/fleet/dsh", yml)

    def test_first_line_is_entry_not_comment_bod135_fix(self):
        # BOD 裁135 修②：零注释行——产出首行即条目行（dsh patch 解析器不支持注释形）
        yml = build_patch_runner_overlay("/x/runner.js", "r-duty-cto", "queue", "/tmp/l.txt",
                                         "/srv/fleet/dsh", "r-duty-cto")
        first = yml.splitlines()[0]
        self.assertTrue(first.startswith("- id:"), f"首行必须为条目行: {first!r}")
        self.assertNotIn("#", yml, "全件零注释（最简形）")

    def test_overlay_uuid_session_id_accepted_bod135_fix(self):
        # 修①联动：UUID 形 session id 入 overlay 守卫（河源实弹存量会话形）
        yml = build_patch_runner_overlay("/x/runner.js", "b38ba22d-9f06-4443-b295-c5825026404a",
                                         "queue", "/tmp/l.txt", "/srv/fleet/dsh",
                                         "b38ba22d-9f06-4443-b295-c5825026404a")
        self.assertIn("seat: b38ba22d", yml)

    def test_overlay_session_id_explicit(self):
        yml = build_patch_runner_overlay("/x/runner.js", "r-duty-cto", "steer", "/tmp/l.txt",
                                         "/srv/fleet/dsh", "session-abc")
        self.assertIn("seat: session-abc", yml)
        self.assertIn("sessionId: session-abc", yml)
        self.assertIn("mode: steer", yml)
        # r-duty 形=seat 与 sessionId 同值零 extra
        yml2 = build_patch_runner_overlay("/x/runner.js", "r-duty-cto", "queue", "/tmp/l.txt",
                                          "/srv/fleet/dsh", "r-duty-cto")
        self.assertNotIn("sessionId:", yml2)

    def test_overlay_session_id_shape_guard(self):
        with self.assertRaises(ValueError):
            build_patch_runner_overlay("/x/runner.js", "seat", "queue", "/tmp/l.txt",
                                       "/srv/fleet/dsh", "bad id;rm -rf")


class DryFace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_dry_zero_files_zero_subprocess(self):
        out = run_auto_segment(self.d, self.d, dry=True, deliver_config=_cfg("/bin/true"))
        self.assertEqual(out["mode"], "manual")  # 无 trigger=manual——零投递零子进程
        self.assertEqual(out["delivery"], {})

    def test_dry_patch_runner_preview_contains_overlay(self):
        _trigger_doc(self.d, convene_mode="auto", deliver_via="patch-runner")
        out = run_auto_segment(self.d, self.d, dry=True, deliver_config=_cfg("/bin/true"))
        self.assertEqual(out["delivery"]["dry"], True)
        self.assertEqual(len(out["delivery"]["previews"]), 7, "七席预演")
        self.assertIn("overlay", out["delivery"]["previews"][0])
        self.assertEqual(out["delivery"]["failures"], [])


class LegacyDefaultZeroDrift(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_default_full_chain_v22_equivalent(self):
        _trigger_doc(self.d, convene_mode="auto")
        out = run_auto_segment(self.d, self.d, dry=False)
        self.assertEqual(out["deliver_via"], DEFAULT_DELIVER_VIA)
        self.assertEqual(out["delivery"]["form"], DEFAULT_DELIVER_VIA)
        self.assertEqual(out["compare"]["staged"], True)
        self.assertEqual(len(out["landed"]), 2, "V2-2 staging 双件族")
        for f in out["landed"]:
            self.assertTrue(Path(f).is_file())

    def test_manual_zero_delivery(self):
        _trigger_doc(self.d, convene_mode="manual", deliver_via="patch-runner")
        out = run_auto_segment(self.d, self.d, dry=False, deliver_config=_cfg("/bin/true"))
        self.assertEqual(out["mode"], "manual")
        self.assertEqual(out["delivery"], {}, "manual 形零投递（零自动件产出）")
        self.assertEqual(len(out["letters"]), 0)


class PatchRunnerEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)
        self.bin = _write_bin(self._tmp.name, FAKE_DSH_BIN)

    def tearDown(self):
        self._tmp.cleanup()

    def test_seven_seat_readouts_collected(self):
        _trigger_doc(self.d, convene_mode="auto", deliver_via="patch-runner")
        out = run_auto_segment(self.d, self.d, dry=False, deliver_config=_cfg(self.bin))
        delivery = out["delivery"]
        self.assertEqual(delivery["form"], "patch-runner")
        self.assertEqual(len(delivery["delivered"]), 7)
        self.assertEqual(delivery["failures"], [])
        self.assertEqual(delivery["delivered"][0]["event"], "fsd-adopt-runner")

    def test_fail_visible_nonzero_rc_recorded_not_raised(self):
        binp = _write_bin(self._tmp.name, "#!/bin/sh\nexit 3\n")
        letters = [{"target_seat": "m-duty-cto", "body": "hello"}]
        res = run_deliver(self.d, letters, "patch-runner", _cfg(binp), dry=False)
        self.assertEqual(res["delivered"], [])
        self.assertEqual(len(res["failures"]), 1)
        self.assertEqual(res["failures"][0]["rc"], 3)
        self.assertEqual(res["failures"][0]["seat"], "r-duty-cto")

    def test_d46_defense_letter_echo_detected(self):
        # cli-adopt 形=stdin 真回显路径（evil bin cat stdin→stdout·D-46 防御检出）
        binp = _write_bin(self._tmp.name, ECHO_DSH_BIN)
        letters = [{"target_seat": "m-duty-cto", "body": "SECRET-LETTER-MARKER-abc"}]
        res = run_deliver(self.d, letters, "cli-adopt", _cfg(binp), dry=False)
        self.assertEqual(res["delivered"], [])
        self.assertTrue(any("回显检出" in f.get("error", "") for f in res["failures"]))

    def test_missing_config_fail_visible(self):
        letters = [{"target_seat": "m-duty-cto", "body": "b"}]
        with self.assertRaises(ValueError):
            run_deliver(self.d, letters, "patch-runner", {"dsh_bin": self.bin}, dry=False)
        with self.assertRaises(ValueError):
            run_deliver(self.d, letters, "patch-runner", None, dry=False)

    def test_unmappable_seat_fail_visible_recorded(self):
        letters = [{"target_seat": "bod", "body": "b"}]
        res = run_deliver(self.d, letters, "patch-runner", _cfg(self.bin), dry=False)
        self.assertEqual(res["delivered"], [])
        self.assertTrue(any("非映射表席形" in f.get("error", "") for f in res["failures"]))


class CliAdoptEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)
        self.bin = _write_bin(self._tmp.name, FAKE_DSH_BIN)

    def tearDown(self):
        self._tmp.cleanup()

    def test_stdin_form_readout(self):
        _trigger_doc(self.d, convene_mode="auto", deliver_via="cli-adopt")
        out = run_auto_segment(self.d, self.d, dry=False, deliver_config=_cfg(self.bin))
        delivery = out["delivery"]
        self.assertEqual(delivery["form"], "cli-adopt")
        self.assertEqual(len(delivery["delivered"]), 7)
        self.assertEqual(delivery["delivered"][0]["outcome"], "created")


if __name__ == "__main__":
    unittest.main()


class F4OutTruncationParseTest(unittest.TestCase):
    """F4 截断面上限修钉（ns4 第二拍 raw_out 勘凭首读定性·2026-11-19）：
    dimA 形长 JSON（>4000 字）→旧尾截 parse 必败·新 60000 上限 parse 正形。"""

    def test_long_dima_json_parse_with_new_cap(self) -> None:
        import json as _json
        from runtime.cognition.loop_autoreview import parse_sheet
        sheet = {
            "seat": "cos", "run_id": "r",
            "scores": {"I1": 2, "I2": 2, "I3": 2},
            "rationale": {"I1": "长 rationale " * 200, "I2": "x", "I3": "y"},
            "evidence_ref": {"I1": "run_dir 长锚 " * 200, "I2": "e", "I3": "e"},
            "improvement_opinions": [
                {"topic": "周迁移质量", "rationale": "r" * 500,
                 "evidence_ref": "plan.json#/x", "check_time": "2026-11-19T00:00:00Z"},
                {"topic": "fade-001 自身完善度", "rationale": "r" * 500,
                 "evidence_ref": "close.json#/y", "check_time": "2026-11-19T00:00:00Z"},
            ],
            "check_time": "2026-11-19T00:00:00Z",
        }
        raw = _json.dumps(sheet, ensure_ascii=False)
        self.assertGreater(len(raw), 4000)  # dimA 形爆长直证
        parsed = parse_sheet("cos", raw)    # 全量形 parse 正形
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["seat"], "cos")

    def test_truncated_4000_form_was_broken(self) -> None:
        """旧形直证（[-4000:] 尾截→JSON 头丢→parse 败——根因复现钉防回退）。"""
        import json as _json
        from runtime.cognition.loop_autoreview import parse_sheet
        sheet = {"seat": "cos", "scores": {"I1": 2},
                 "rationale": {"I1": "长 rationale " * 400}}
        raw = _json.dumps(sheet, ensure_ascii=False)
        self.assertGreater(len(raw), 4000)
        self.assertIsNone(parse_sheet("cos", raw[-4000:]))  # 旧尾截形 parse 败
