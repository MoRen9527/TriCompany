"""联审召集自动段自动化脚本面（V2-2 基座+v3 投递面扩展·基于 V2-1 交付谱系）。

全链自动段：trigger convene_mode 读 → deliver_via 门控 → dimB 初判（机判可验
族草卷）→ 召集件渲染（七席信箱 dispatch payload 形）→ 投递/落位。

deliver_via 三形（v3 形·BOD 托转 133·方案卷 §2.3/§9.2 双兜底通道）：
  · legacy-staging（缺省·V2-2 现役形）：convene staging 落位（run_dir/convene/
    面·控制面 m-duty-cos 值守拾取发送——零直接投递零 POST）——缺省零行为漂移
  · patch-runner（v3 主形）：--patch overlay 注入 fsd-adopt-runner 插件
    （TriModel src/dsh-adopt/runner.mjs 编译物）——dsh profile boot 内
    adopt-or-create+三模式注入 in-process 真通道
  · cli-adopt（兜底形）：rc.2 原生 CLI `--session-id` adopt 直用（stdin `-`
    形投 letter·上游公共面·插件契约断裂时零自定义码兜底）

manual 形对照（过渡形对照跑面）：convene_mode=manual → 零召集件产出零投递·
输出值守 SOP 对照读数（新旧两形读数并出供对照跑）。

隔离纪律（§六 v2 照走+v3）：TC 面脚本·dry=全链渲染零落位零子进程（预演面）；
投递两形仅 deliver_via 显式声明时触 dsh 面（缺省=legacy 零 dsh 触）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from runtime.cognition.loop_convene import (
    build_convene_letters,
    dimb_initial_judge,
    read_convene_mode,
)

# ── v3 deliver_via 门控面 ────────────────────────────────────────────

DEFAULT_DELIVER_VIA = "legacy-staging"
VALID_DELIVER_VIA = ("legacy-staging", "patch-runner", "cli-adopt")
_RUNNER_PLUGIN_ID = "fsd-adopt-runner"
_SEAT_SESSION_RE = re.compile(r"^r-duty-[a-z0-9][a-z0-9-]*$")
_LETTER_ECHO_MARKER_LIMIT = 200


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
    """席→dsh 会话寻址映射（T2 ④-1 映射表正形·双入形）：

    · m-duty-<suffix> → r-duty-<suffix>（信箱席名形）
    · 叙事席名 COS/COO/CAO/CPO/CTO/CHO/CFO（V2-1 召集件 target_seat 形）→
      r-duty-<lower>
    非映射表形=fail-visible（禁隐式猜测·映射确定性纪律）。
    """
    m = re.match(r"^m-duty-([a-z0-9][a-z0-9-]*)$", target_seat)
    if m:
        sid = f"r-duty-{m.group(1)}"
    elif target_seat in ("COS", "COO", "CAO", "CPO", "CTO", "CHO", "CFO"):
        sid = f"r-duty-{target_seat.lower()}"
    else:
        raise ValueError(f"seat_session_id: 非映射表席形 {target_seat!r}（禁隐式猜测·T2 ④-1）")
    if not _SEAT_SESSION_RE.match(sid):
        raise ValueError(f"seat_session_id: 映射结果越形 {sid!r}")
    return sid


def build_patch_runner_overlay(runner_path: str, seat: str, mode: str, letter_file: str,
                               dsh_install_anchor: str, session_id: str) -> str:
    """v3 overlay 生成（--patch 调用级·零持久 patch 面）：disable headless-runner
    + insert fsd-adopt-runner（TriModel 编译物·path 形 name=loader :214-223 解析）。
    插值面全部受限字符集（seat 越形已 fail-visible·路径=配置/tmp 面）。"""
    if not (_SEAT_SESSION_RE.match(session_id) or re.match(r"^session-[A-Za-z0-9._-]+$", session_id)):
        raise ValueError(f"build_patch_runner_overlay: session_id 越形 {session_id!r}")
    extra = ""
    if session_id != seat:
        extra = f"\n        sessionId: {session_id}"
    return (
        "# v3 fsd-adopt-runner overlay（调用级生成·随毕清理·零持久 patch 面）\n"
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


def run_deliver(run_dir: Path, letters: List[Dict[str, Any]], deliver_via: str,
                deliver_config: Optional[Dict[str, Any]], dry: bool) -> Dict[str, Any]:
    """v3 投递面入口（deliver_via 门控派发·legacy-staging=零投递返回占位读数）。"""
    if deliver_via == DEFAULT_DELIVER_VIA:
        return {"form": DEFAULT_DELIVER_VIA, "note": "V2-2 现役 staging 拾取形（零直接投递·控制面拾取发送）"}
    if deliver_via not in VALID_DELIVER_VIA:
        raise ValueError(f"run_deliver: deliver_via 非法 {deliver_via!r}")
    if not deliver_config:
        raise ValueError(f"deliver_via={deliver_via}: deliver_config 缺席（fail-visible·dsh_bin/dsh_home/"
                         f"dsh_install_anchor{'/runner_path' if deliver_via == 'patch-runner' else ''} 必载）")
    return _deliver_letters(letters, deliver_via, deliver_config, dry)


def run_auto_segment(run_dir: Path, trigger_dir: Optional[Path] = None,
                     dry: bool = False,
                     deliver_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """联审召集自动段主步：mode 门→deliver_via 门→dimB 初判→召集件渲染→投递/落位。

    返回读数卷（mode/deliver_via/letters/dimb/landed/delivery/compare——对照跑
    读数面）。deliver_via 缺省=legacy-staging（V2-2 形零行为漂移）。
    """
    run_dir = Path(run_dir)
    trigger_dir = Path(trigger_dir) if trigger_dir else run_dir
    mode, warn = read_convene_mode(trigger_dir)
    deliver_via, dv_warn = read_deliver_via(trigger_dir)
    warns = [w for w in (warn, dv_warn) if w]

    dimb = dimb_initial_judge(run_dir)
    # mode 门控：manual=值守循环 SOP 召集形（零自动件产出零投递）；auto=召集件渲染。
    letters = (build_convene_letters(
        run_dir.name, 0, dimb.get("verdict", "unknown"),
        {"entries": len(dimb.get("entries", []))}) if mode == "auto" else [])

    landed: List[str] = []
    delivery: Dict[str, Any] = {}
    compare: Dict[str, Any] = {}
    if mode == "auto":
        # v3 投递面（deliver_via 门控·缺省 legacy-staging 零 dsh 触零行为漂移）
        delivery = run_deliver(run_dir, letters, deliver_via, deliver_config, dry)
        if deliver_via == DEFAULT_DELIVER_VIA:
            if not dry:
                stage = run_dir / "convene"
                stage.mkdir(parents=True, exist_ok=True)
                (stage / "convene-letters.json").write_text(
                    json.dumps(letters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                (stage / "dimb-initial.json").write_text(
                    json.dumps(dimb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                landed.append(str(stage / "convene-letters.json"))
                landed.append(str(stage / "dimb-initial.json"))
        compare = {"form": "auto", "letters": len(letters), "dimb_entries": len(dimb.get("entries", [])),
                   "staged": bool(landed) and not dry}
    else:
        # manual 形对照读数（过渡形对照跑面）：召集动作=值守循环 SOP 面（值席手
        # 动召集·零自动件产出零投递）——读数并出供新旧形对照跑。
        compare = {"form": "manual", "note": "值守循环 SOP 召集形（零自动件产出·对照跑读数面）"}

    return {"mode": mode, "warn": warns, "deliver_via": deliver_via, "letters": letters,
            "dimb": dimb, "landed": landed, "delivery": delivery, "compare": compare,
            "readings": {"letters_count": len(letters),
                         "dimb_entries": len(dimb.get("entries", []))}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="联审召集自动段自动化脚本面（V2-2+v3 投递面）")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--trigger-dir", default=None)
    parser.add_argument("--dry", action="store_true", help="dry 预演：全链渲染零落位零子进程")
    parser.add_argument("--deliver-config", default=None,
                        help="deliver_via 投递配置 JSON（dsh_bin/dsh_home/dsh_install_anchor[/runner_path]）")
    args = parser.parse_args(argv)
    deliver_config = json.loads(args.deliver_config) if args.deliver_config else None
    out = run_auto_segment(Path(args.run_dir), Path(args.trigger_dir) if args.trigger_dir else None,
                           args.dry, deliver_config)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
