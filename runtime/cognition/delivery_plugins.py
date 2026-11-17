"""投递插件族 registry（DeliveryPlugin 契约 v1·方案卷 fd2fd57f0 §二正形·P0 registry 化）。

契约面（fsd-adopt-runner cordis 四件套同构·CTO 门禁首闸绿 d54bda7af 对表三点）：
  · name      = deliver_via 旗标值（registry 键）
  · apply(ctx, letters, dry) -> readout   # 批投递主步（fail-visible 单席记录不中断）
  · inject    = 服务声明类属性（零依赖=空表）
  · validate_config(cfg) = Config 手工校验形（缺省零需·dsh 触点形逐键点名）

REGISTRY 三键=值域 VALID_DELIVER_VIA（mailbox=P2 候位不入册——纳=加键零结构改）。
P0=现役核函数原样收拢（改形不改语义·白盒 31 件守护+缺省 legacy 零漂移双断言）。

v3 谱系承录：seat 形三形直通+overlay 零注释（346158a 修面①②）·版本检查源=
app-boot runtime 正源（TriModel b3934e6 三修①·runner 面）。

零回归护栏（方案卷 §五）：deliver_via 缺省=legacy-staging 零行为漂移·信箱消费链
零改·②③交互席世界零触·dry=零文件零子进程。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── 旗标与形族（现役常量原样迁移） ──────────────────────────────────

DEFAULT_DELIVER_VIA = "legacy-staging"
VALID_DELIVER_VIA = ("legacy-staging", "patch-runner", "cli-adopt")
_RUNNER_PLUGIN_ID = "fsd-adopt-runner"
_SEAT_SESSION_RE = re.compile(r"^r-duty-[a-z0-9][a-z0-9-]*$")
# 会话 id 形族（BOD 裁135 修①·两函数共享形判定器——产出形=校验形一致化）：
# r-duty-* 席名形 / session-<uuid> dsh 原生形 / 裸 <uuid> 河源实弹存量会话形
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_SESSION_PREFIX_RE = re.compile(r"^session-[A-Za-z0-9._-]+$")
_LETTER_ECHO_MARKER_LIMIT = 200


def is_session_id_form(sid: str) -> bool:
    """会话 id 三形共享判定（r-duty-*／session-*／裸 UUID）——seat_session_id
    产出校验与 build_patch_runner_overlay 守卫同源（同模块两函数一致化）。"""
    return bool(_SEAT_SESSION_RE.match(sid) or _SESSION_PREFIX_RE.match(sid) or _UUID_RE.match(sid))


def read_deliver_via(trigger_dir: Path) -> Tuple[str, Optional[str]]:
    """loop-convene.json deliver_via 读（fail-safe：缺席/坏值=缺省 legacy-staging）。"""
    path = Path(trigger_dir) / "loop-convene.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DEFAULT_DELIVER_VIA, None
    value = doc.get("deliver_via")
    if value is None:
        return DEFAULT_DELIVER_VIA, None
    if value not in VALID_DELIVER_VIA:
        return DEFAULT_DELIVER_VIA, f"deliver_via 非法值 {value!r}——降级缺省 {DEFAULT_DELIVER_VIA}"
    return str(value), None


def seat_session_id(target_seat: str) -> str:
    """席→dsh 会话寻址映射（T2 ④-1 映射表正形·三入形）：

    · 已形直通：r-duty-*/session-*/裸 UUID（实弹面显式会话 id 配置形·BOD 裁135
      修①席名直通——产出形对齐校验形）
    · m-duty-<suffix> → r-duty-<suffix>（信箱席名形）
    · 叙事席名 COS/COO/CAO/CPO/CTO/CHO/CFO（V2-1 召集件 target_seat 形）→
      r-duty-<lower>
    非映射表形=fail-visible（禁隐式猜测·映射确定性纪律）。
    """
    if is_session_id_form(target_seat):
        return target_seat
    m = re.match(r"^m-duty-([a-z0-9][a-z0-9-]*)$", target_seat)
    if m:
        sid = f"r-duty-{m.group(1)}"
    elif target_seat in ("COS", "COO", "CAO", "CPO", "CTO", "CHO", "CFO"):
        sid = f"r-duty-{target_seat.lower()}"
    else:
        raise ValueError(f"seat_session_id: 非映射表席形 {target_seat!r}（禁隐式猜测·T2 ④-1）")
    if not is_session_id_form(sid):
        raise ValueError(f"seat_session_id: 映射结果越形 {sid!r}")
    return sid


def build_patch_runner_overlay(runner_path: str, seat: str, mode: str, letter_file: str,
                               dsh_install_anchor: str, session_id: str) -> str:
    """v3 overlay 生成（--patch 调用级·零持久 patch 面）：disable headless-runner
    + insert fsd-adopt-runner（TriModel 编译物·path 形 name=loader :214-223 解析）。
    插值面全部受限字符集（seat 越形已 fail-visible·路径=配置/tmp 面）。
    BOD 裁135 修②：零注释行（dsh patch 解析器不支持注释形——首行注释=bad
    indentation 1:39 实锚）——产出首行即条目行（最简形）。"""
    if not is_session_id_form(session_id):
        raise ValueError(f"build_patch_runner_overlay: session_id 越形 {session_id!r}")
    extra = ""
    if session_id != seat:
        extra = f"\n        sessionId: {session_id}"
    return (
        "- id: headless-runner\n"
        "  disabled: true\n"
        "- insert:\n"
        f"    - id: {_RUNNER_PLUGIN_ID}\n"
        f"      name: {runner_path}\n"
        "      config:\n"
        f"        seat: {session_id}\n"
        f"        mode: {mode}{extra}\n"
        f"        letterFile: {letter_file}\n"
        f"        dshInstallAnchor: {dsh_install_anchor}\n"
    )


def _invoke_dsh(dsh_bin: str, args: List[str], dsh_home: str,
                stdin_text: Optional[str] = None, timeout_s: int = 120) -> "subprocess.CompletedProcess[str]":
    """dsh CLI 子进程（DSH_HOME 注入·fail-visible 由调用面读 rc）。"""
    env = dict(os.environ)
    env["DSH_HOME"] = dsh_home
    return subprocess.run(
        [str(dsh_bin)] + args,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
        check=False,
    )


def _parse_runner_readout(stdout: str, letter_body: str, seat: str) -> Dict[str, Any]:
    """runner 读数解析（零值面防御：letter 回显检出=失败记录·D-46 双道防线）。"""
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        raise ValueError(f"patch-runner[{seat}]: stdout 零读数行")
    line = lines[-1]
    if letter_body and letter_body in line:
        raise ValueError(f"patch-runner[{seat}]: 读数面 letter 回显检出（D-46 防御面）")
    try:
        doc = json.loads(line)
    except ValueError as err:
        raise ValueError(f"patch-runner[{seat}]: 读数非 JSON（fail-visible）: {line[:80]}") from err
    if doc.get("event") != _RUNNER_PLUGIN_ID:
        raise ValueError(f"patch-runner[{seat}]: 读数 event 面不符 {doc.get('event')!r}")
    return doc


def _deliver_letters(letters: List[Dict[str, Any]], form: str, cfg: Dict[str, Any],
                     dry: bool) -> Dict[str, Any]:
    """投递执行面（patch-runner/cli-adopt 两形共用骨架·per-seat 顺序）。

    fail-visible 形：单席失败=读数记录（stderr 尾段截断·零 letter 值）不中断
    他席；dry=全链渲染零文件零子进程（预演读数面）。
    """
    for key in ("dsh_bin", "dsh_home", "dsh_install_anchor"):
        if not cfg.get(key):
            raise ValueError(f"deliver_via={form}: deliver_config.{key} 缺席（fail-visible）")
    readings: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    previews: List[Dict[str, Any]] = []
    timeout_s = int(cfg.get("timeout_s", 120))
    with tempfile.TemporaryDirectory(prefix="v3-convene-deliver-") as tmp:
        for letter in letters:
            seat_raw = str(letter.get("target_seat", ""))
            try:
                sid = seat_session_id(seat_raw)
                body = str(letter.get("body", ""))
                letter_file = str(Path(tmp) / f"letter-{sid}.txt")
                if dry:
                    preview: Dict[str, Any] = {"seat": sid, "form": form, "mode": str(cfg.get("mode", "queue")),
                                               "letter_bytes": len(body.encode("utf-8"))}
                    if form == "patch-runner":
                        preview["overlay"] = build_patch_runner_overlay(
                            str(cfg.get("runner_path", "<runner-path>")), sid,
                            str(cfg.get("mode", "queue")), "<letter-file>",
                            str(cfg["dsh_install_anchor"]), sid)
                    previews.append(preview)
                    continue
                Path(letter_file).write_text(body, encoding="utf-8")
                if form == "patch-runner":
                    overlay_file = str(Path(tmp) / f"overlay-{sid}.yml")
                    Path(overlay_file).write_text(build_patch_runner_overlay(
                        str(cfg["runner_path"]), sid, str(cfg.get("mode", "queue")),
                        letter_file, str(cfg["dsh_install_anchor"]), sid), encoding="utf-8")
                    proc = _invoke_dsh(str(cfg["dsh_bin"]),
                                       ["--profile", "headless", "--patch", overlay_file],
                                       str(cfg["dsh_home"]), timeout_s=timeout_s)
                else:  # cli-adopt（stdin `-` 形·rc.2 原生 adopt 直用）
                    proc = _invoke_dsh(str(cfg["dsh_bin"]),
                                       ["--profile", "headless", "--session-id", sid, "-"],
                                       str(cfg["dsh_home"]), stdin_text=body, timeout_s=timeout_s)
                if proc.returncode != 0:
                    failures.append({"seat": sid, "form": form, "rc": proc.returncode,
                                     "stderr_tail": (proc.stderr or "")[-_LETTER_ECHO_MARKER_LIMIT:]})
                    continue
                doc = _parse_runner_readout(proc.stdout, body, sid)
                readings.append(doc)
            except (ValueError, OSError, subprocess.TimeoutExpired) as err:
                failures.append({"seat": seat_raw or "<unmapped>", "form": form,
                                 "error": str(err)[:_LETTER_ECHO_MARKER_LIMIT]})
    return {"form": form, "dry": dry, "delivered": readings, "failures": failures,
            "previews": previews, "letters_count": len(letters)}


# ── DeliveryPlugin 契约 v1（四件套·fsd-adopt-runner 先例同构） ─────────

class DeliveryPlugin:
    """投递插件契约正形（P0 registry 化·CTO 门禁首闸绿承面）。

    四件套：name=deliver_via 旗标值／apply=批投递主步／inject=服务声明面／
    validate_config=Config 手工校验形（fsd-adopt-runner validateConfig 先例）。
    """

    name: str = ""
    #: 服务声明面（零依赖=空表·dsh 触点形=('dsh',)·mailbox 候位=('mailbox_root',)）
    inject: Tuple[str, ...] = ()

    def validate_config(self, cfg: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Config 手工校验形（缺省零需·dsh 触点插件逐键点名覆写）。"""
        return cfg

    def apply(self, ctx: Dict[str, Any], letters: List[Dict[str, Any]], dry: bool) -> Dict[str, Any]:
        raise NotImplementedError(f"{type(self).__name__}: apply 未实装（契约面）")


class LegacyStagingPlugin(DeliveryPlugin):
    """④staging 拾取形（V2-2 现役缺省·零 dsh 依赖零行为变）。

    apply=run_dir/convene 双件族落位（控制面值守拾取发送——本插件零直接投递）。
    """

    name = DEFAULT_DELIVER_VIA
    inject: Tuple[str, ...] = ()

    def apply(self, ctx: Dict[str, Any], letters: List[Dict[str, Any]], dry: bool) -> Dict[str, Any]:
        run_dir = Path(ctx["run_dir"])
        dimb = ctx.get("dimb", {})
        landed: List[str] = []
        if not dry:
            stage = run_dir / "convene"
            stage.mkdir(parents=True, exist_ok=True)
            (stage / "convene-letters.json").write_text(
                json.dumps(letters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (stage / "dimb-initial.json").write_text(
                json.dumps(dimb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            landed.append(str(stage / "convene-letters.json"))
            landed.append(str(stage / "dimb-initial.json"))
        return {"form": self.name, "note": "V2-2 现役 staging 拾取形（零直接投递·控制面拾取发送）",
                "staged": bool(landed) and not dry, "landed": landed}


class PatchRunnerPlugin(DeliveryPlugin):
    """⑥patch-runner 主形（v3 in-process adopt 真通道·dsh 触点插件）。"""

    name = "patch-runner"
    inject: Tuple[str, ...] = ("dsh",)
    REQUIRED_CONFIG = ("dsh_bin", "dsh_home", "dsh_install_anchor", "runner_path")

    def validate_config(self, cfg: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        cfg = cfg or {}
        missing = [k for k in self.REQUIRED_CONFIG if not cfg.get(k)]
        if missing:
            raise ValueError(f"deliver_via={self.name}: deliver_config 缺席面 {missing}（fail-visible）")
        return cfg

    def apply(self, ctx: Dict[str, Any], letters: List[Dict[str, Any]], dry: bool) -> Dict[str, Any]:
        return _deliver_letters(letters, self.name, ctx["deliver_config"], dry)


class CliAdoptPlugin(DeliveryPlugin):
    """⑥族内兜底形（rc.2 原生 CLI --session-id adopt 直用·stdin `-` 形）。"""

    name = "cli-adopt"
    inject: Tuple[str, ...] = ("dsh",)
    REQUIRED_CONFIG = ("dsh_bin", "dsh_home", "dsh_install_anchor")

    def validate_config(self, cfg: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        cfg = cfg or {}
        missing = [k for k in self.REQUIRED_CONFIG if not cfg.get(k)]
        if missing:
            raise ValueError(f"deliver_via={self.name}: deliver_config 缺席面 {missing}（fail-visible）")
        return cfg

    def apply(self, ctx: Dict[str, Any], letters: List[Dict[str, Any]], dry: bool) -> Dict[str, Any]:
        return _deliver_letters(letters, self.name, ctx["deliver_config"], dry)


# ── registry 面（三键=值域·mailbox=P2 候位不入册——纳=加键零结构改） ────

REGISTRY: Dict[str, DeliveryPlugin] = {
    p.name: p for p in (LegacyStagingPlugin(), PatchRunnerPlugin(), CliAdoptPlugin())
}


def run_deliver(run_dir: Path, letters: List[Dict[str, Any]], deliver_via: str,
                deliver_config: Optional[Dict[str, Any]], dry: bool) -> Dict[str, Any]:
    """投递面入口（registry 查找派发·读数/消息面照现役 byte-level）。"""
    if deliver_via == DEFAULT_DELIVER_VIA:
        return REGISTRY[DEFAULT_DELIVER_VIA].apply(
            {"run_dir": Path(run_dir), "deliver_config": {}}, letters, dry)
    if deliver_via not in VALID_DELIVER_VIA:
        raise ValueError(f"run_deliver: deliver_via 非法 {deliver_via!r}")
    if not deliver_config:
        raise ValueError(f"deliver_via={deliver_via}: deliver_config 缺席（fail-visible·dsh_bin/dsh_home/"
                         f"dsh_install_anchor{'/runner_path' if deliver_via == 'patch-runner' else ''} 必载）")
    plugin = REGISTRY[deliver_via]
    plugin.validate_config(deliver_config)
    return plugin.apply({"run_dir": Path(run_dir), "deliver_config": deliver_config}, letters, dry)
