#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""树挂载 CAO 批门（COS 面·一源三处同判据第三处·规范 v1.1）

判据真源：TriCompany/docs/standard-templates/taskcharter-check-spec-v1.1.md
（TC@e11f1e0·含 §六 裁定 B）——G0→G1→G2→G3·拒因四值·无宽容面·三处引用本件不各自复写。
对表件（规范附件·同仓）：指纹 10 向量 taskcharter-fingerprint-vectors.md·
门回归 16 案 taskcharter-gate-regress.py（输入+期望拒因码）。

判定序（前一关不过即出·拒因码取先命中者）：
- G0 工具/解析：读/解码/JSON 解析失败、参考实现不可载、计算失败、n≠2、指纹畸形
  → GATE_TOOL_FAIL（「取值失败≠空值」·任何工具失败一律拒·不得当作字段为空而放行）
- G1 准入：缺 cao_approval 块 / approved !== true → CAO_NOT_APPROVED
  （规范 §一/§三 条文·与 TriRMC 两处同；taskcharter-gate-ref.py 现把「缺块」判
  GATE_TOOL_FAIL·与条文差一·已报 CAO/CTO·回归 16 案未含缺块案）
- G2 指纹在位：content_sha256_16 缺/空/非字符串 → FINGERPRINT_MISSING
- G3 内容绑定：字段值 ≠ 当前文件指纹 → CONTENT_CHANGED

指纹=同一份参考实现（规范 §二「批准方与门用同一函数·不得各自实现两套」）：
  docs/standard-templates/taskcharter-fingerprint-ref.py::fingerprint_bytes
  （文本层置空两键值·禁 parse→dump·仅 CRLF→LF·sha256 前 16·n=命中键数·正常件 2）

BOM（§六 裁定 B·CTO 2026-11-27 22:59 裁）：解析层取字段前剥串首 U+FEFF·
指纹层对原字节算（BOM 计入）——带 BOM 件可挂·签后加/删 BOM 均 CONTENT_CHANGED。

效力边界（规范 §五）：指纹无密钥·防过失不防越权。

函数签名与 TriRMC 两处同源：
  check_cao_approval(doc, charter_path=None) ->
      {ok, reason, code, detail, expected, fix, note, fingerprint, n}
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REASON_NOT_APPROVED = "CAO 批缺失·拒挂任务书"
REASON_CHANGED = "批后内容变更·须重签"
REASON_FP_MISSING = "CAO 批指纹缺失·拒挂任务书"
REASON_TOOL_FAIL = "批门工具失败·拒挂任务书"
# 兼容旧名（v1.0 三处统一字串·已退役的锚验语境）
REASON_MISSING = REASON_NOT_APPROVED
REASON_ANCHOR = REASON_CHANGED

CODE_NOT_APPROVED = "CAO_NOT_APPROVED"
CODE_FP_MISSING = "FINGERPRINT_MISSING"
CODE_CONTENT_CHANGED = "CONTENT_CHANGED"
CODE_TOOL_FAIL = "GATE_TOOL_FAIL"

# §六 裁定 B：True=仅解析层剥 BOM·指纹层不剥（指纹函数吃原字节·本开关管不到它）
STRIP_BOM_AT_PARSE_ONLY = True
_REF_RELPATH = Path("docs") / "standard-templates" / "taskcharter-fingerprint-ref.py"
_HEX16 = re.compile(r"^[0-9a-f]{16}$")

_REASON = {
    CODE_NOT_APPROVED: REASON_NOT_APPROVED,
    CODE_FP_MISSING: REASON_FP_MISSING,
    CODE_CONTENT_CHANGED: REASON_CHANGED,
    CODE_TOOL_FAIL: REASON_TOOL_FAIL,
}
_EXPECTED = {
    CODE_NOT_APPROVED: "approved: true",
    CODE_FP_MISSING: "content_sha256_16 为 16 位小写 hex",
    CODE_CONTENT_CHANGED: "content_sha256_16 == 当前文件指纹（规范 v1.1 §二）",
    CODE_TOOL_FAIL: "文件可读·可解析·两键齐（n=2）·指纹形合法·参考实现可载",
}
_FIX = {
    CODE_NOT_APPROVED: "请 CAO 批后写 cao_approval 块（approved: true·余字段供核不供判）",
    CODE_FP_MISSING: "请 CAO 签时用参考实现算指纹并填入 content_sha256_16（16 位小写 hex）",
    CODE_CONTENT_CHANGED: "任务书内容批后已变·请 CAO 按现内容重签（重算指纹）",
    CODE_TOOL_FAIL: "修文件编码/语法/schema（两键须齐·指纹须 16 位小写 hex）·或修工具（参考实现须可载）",
}


class GateToolFail(Exception):
    """工具/解析失败（内部信号·出参一律转 GATE_TOOL_FAIL）。"""


def ref_path() -> Path:
    """参考实现路径（规范附件·与门同仓）。"""
    return Path(__file__).resolve().parents[2] / _REF_RELPATH


def _load_ref():
    import importlib.util

    p = ref_path()
    if not p.is_file():
        raise GateToolFail(f"参考实现缺失·{_REF_RELPATH.as_posix()}")
    spec = importlib.util.spec_from_file_location("taskcharter_fingerprint_ref", p)
    if spec is None or spec.loader is None:
        raise GateToolFail("参考实现不可载")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "fingerprint_bytes", None)
    if not callable(fn):
        raise GateToolFail("参考实现缺 fingerprint_bytes")
    return fn


def fingerprint(raw: bytes) -> tuple[str, int]:
    """规范指纹（经参考实现·对原字节算）——不可载/计算失败抛 GateToolFail。"""
    try:
        fn = _load_ref()
        out = fn(raw)
        return out[0], out[1]
    except GateToolFail:
        raise
    except Exception as e:  # noqa: BLE001
        raise GateToolFail(f"指纹计算失败·{type(e).__name__}") from e


def read_charter_bytes(charter_path: Path | str) -> bytes:
    """G0 读件+解码（解码失败即拒·不落任何放行分支）。"""
    try:
        raw = Path(charter_path).read_bytes()
    except OSError as e:
        raise GateToolFail(f"读件失败·{type(e).__name__}") from e
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise GateToolFail(f"非 UTF-8·解码失败（byte {e.start}）") from e
    return raw


def parse_charter_json(raw: bytes) -> dict[str, Any]:
    """G0 JSON 解析（CLI/调用方用·与指纹同源字节）。

    §六 裁定 B：仅此解析步剥串首 U+FEFF（只用于取字段·不得拿剥过 BOM 的文本去算指纹）。
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise GateToolFail(f"非 UTF-8·解码失败（byte {e.start}）") from e
    if STRIP_BOM_AT_PARSE_ONLY:
        text = text.lstrip("﻿")   # U+FEFF 以转义写法书写
    try:
        return json.loads(text)
    except ValueError as e:
        raise GateToolFail(f"JSON 解析失败·{type(e).__name__}") from e


def _reject(code: str, detail: str, fp: str | None = None, n: int | None = None) -> dict[str, Any]:
    return {"ok": False, "reason": _REASON[code], "code": code, "detail": detail,
            "expected": _EXPECTED[code], "fix": _FIX[code], "note": None,
            "fingerprint": fp, "n": n}


def _pass(fp: str, n: int) -> dict[str, Any]:
    return {"ok": True, "reason": None, "code": None, "detail": None, "expected": None,
            "fix": None, "note": None, "fingerprint": fp, "n": n}


def check_cao_approval(doc: dict[str, Any] | None, charter_path: Path | None = None) -> dict[str, Any]:
    """CAO 批门（fail-closed·无宽容面）。

    doc=调用方解析出的任务书对象（须自 charter_path 同一份字节解析）；
    charter_path=任务书文件本体（指纹按其原字节算·规范 §二「整份 charter 文件的文本」）。
    """
    # G0·读件+解码
    if charter_path is None:
        return _reject(CODE_TOOL_FAIL, "未提供 charter_path·无文件可算指纹")
    try:
        raw = read_charter_bytes(charter_path)
    except GateToolFail as e:
        return _reject(CODE_TOOL_FAIL, str(e))
    # G1·准入
    if not isinstance(doc, dict):
        return _reject(CODE_NOT_APPROVED, "doc 非 dict·缺 cao_approval 块")
    block = doc.get("cao_approval")
    if not isinstance(block, dict):
        return _reject(CODE_NOT_APPROVED, "cao_approval 块缺失")
    if block.get("approved") is not True:
        return _reject(CODE_NOT_APPROVED, f"approved={block.get('approved')!r}（需 true）")
    # G2·指纹在位
    claim = block.get("content_sha256_16")
    if not isinstance(claim, str) or claim == "":
        return _reject(CODE_FP_MISSING, f"content_sha256_16={claim!r}（缺/空）")
    malformed = not _HEX16.match(claim)
    # G3·内容绑定（计算失败/n≠2/指纹畸形=工具面拒）
    try:
        fp, n = fingerprint(raw)
    except GateToolFail as e:
        return _reject(CODE_TOOL_FAIL, str(e))
    if n != 2:
        return _reject(CODE_TOOL_FAIL, f"规范化命中键数 n={n}（须 2·缺键=schema 不全）", fp, n)
    if malformed:
        return _reject(CODE_TOOL_FAIL, f"指纹畸形·content_sha256_16={claim!r}（须 16 位小写 hex）", fp, n)
    if claim != fp:
        return _reject(CODE_CONTENT_CHANGED, f"content_sha256_16 冻结={claim} 现文件指纹={fp}", fp, n)
    return _pass(fp, n)


def gate_or_raise(doc: dict[str, Any] | None, charter_path: Path | None = None) -> None:
    """挂载/拾取前调用：不 ok 则抛 ValueError（拒挂）。"""
    res = check_cao_approval(doc, charter_path)
    if not res["ok"]:
        raise ValueError(res["reason"])


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="树挂载 CAO 批门校验（fail-closed·规范 v1.1）")
    ap.add_argument("charter", help="taskcharter json 或 md 的伴生 json 路径")
    args = ap.parse_args(argv)
    p = Path(args.charter)
    try:
        raw = read_charter_bytes(p)          # G0 读件+解码
        doc = parse_charter_json(raw)        # G0 JSON 解析（与指纹同源字节·解析层剥 BOM）
    except GateToolFail as e:
        res = _reject(CODE_TOOL_FAIL, str(e))
    else:
        res = check_cao_approval(doc, p)
    if res["ok"]:
        print(f"CAO 批门=通过（指纹={res['fingerprint']}·n={res['n']}）")
        return 0
    print(res["reason"] or REASON_TOOL_FAIL)
    print(f"code={res.get('code')} detail={res.get('detail')} expected={res.get('expected')} fix={res.get('fix')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
