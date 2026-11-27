#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""树挂载 CAO 批门（COS 面·一源三处同判据第三处）

契约（CTO 2026-11-26T22:58 + BOD 23:08 判据对齐 + CAO 模板 v1.0.1 TC@d810416）：
- 唯一机器判据：`cao_approval.approved === true`
- checks/approver/commit **不解析**（供核不供判·再判=重复且越界）
- 块缺失 或 approved !== true → 拒（fail-closed）
- 报错行（三处统一字串）：
  - 无块/未批：`CAO 批缺失·拒挂任务书`
  - 锚不符：`批后内容变更·须重签`（本门不验锚·保留字串供未来可选层）

函数签名与 TriRMC 两处同源：check_cao_approval(doc, charter_path=None) -> {ok, reason, note}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REASON_MISSING = "CAO 批缺失·拒挂任务书"
REASON_ANCHOR = "批后内容变更·须重签"
CODE_NOT_APPROVED = "CAO_NOT_APPROVED"
CODE_ANCHOR_MISMATCH = "ANCHOR_MISMATCH"
CODE_CONTENT_CHANGED = "CONTENT_CHANGED"


def _file_sha256_16(path: Path | None) -> str | None:
    if path is None or not Path(path).is_file():
        return None
    import hashlib

    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def check_cao_approval(doc: dict[str, Any] | None, charter_path: Path | None = None) -> dict[str, Any]:
    """唯一强判据：cao_approval.approved is True。
    可选层（CAO v1.0.1 TC@ec83231 第 5 款）：若 cao_approval.content_sha256_16 非空 →
    比现文件 sha256_16，不等=拒（REASON_ANCHOR）；无值→跳过（宽松读）。
    """
    if not isinstance(doc, dict):
        return {"ok": False, "reason": REASON_MISSING, "code": CODE_NOT_APPROVED, "note": "doc 非 dict"}
    block = doc.get("cao_approval")
    if not isinstance(block, dict):
        return {"ok": False, "reason": REASON_MISSING, "code": CODE_NOT_APPROVED, "note": "cao_approval 块缺失"}
    if block.get("approved") is not True:
        return {"ok": False, "reason": REASON_MISSING, "code": CODE_NOT_APPROVED, "note": "approved !== true"}
    # 第二层·批的有效性：commit 锚（若可验）
    commit = block.get("commit")
    actual = _file_sha256_16(charter_path)
    if isinstance(commit, str) and commit.strip() and charter_path is not None and Path(charter_path).is_file():
        try:
            import subprocess

            repo = Path(charter_path).resolve().parent
            rel = Path(charter_path).resolve()
            out = subprocess.run(
                ["git", "-C", str(repo), "show", f"{commit.strip()}:{rel.name}"],
                capture_output=True, timeout=10,
            )
            if out.returncode == 0:
                import hashlib

                want = hashlib.sha256(out.stdout).hexdigest()[:16]
                if actual is not None and actual != want:
                    return {"ok": False, "reason": REASON_ANCHOR, "code": CODE_ANCHOR_MISMATCH,
                            "note": f"commit={commit.strip()} want={want} actual={actual}"}
            # git 不可验 → 宽容放行
        except Exception:
            pass  # binding_weak：宽容
    # 第二层·批的有效性：content_sha256_16（若声明）
    claim = block.get("content_sha256_16")
    if isinstance(claim, str) and claim.strip():
        if actual is None:
            return {"ok": True, "reason": None, "code": None, "note": "content_sha256_16 有值但现文件不可读·锚不可验·放行"}
        if actual != claim.strip():
            return {"ok": False, "reason": REASON_ANCHOR, "code": CODE_CONTENT_CHANGED,
                    "note": f"claim={claim.strip()} actual={actual}"}
        return {"ok": True, "reason": None, "code": None, "note": None}
    return {"ok": True, "reason": None, "code": None, "note": "无 content_sha256_16/commit 可验锚·跳过（可选层）"}


def gate_or_raise(doc: dict[str, Any] | None, charter_path: Path | None = None) -> None:
    """挂载/拾取前调用：不 ok 则抛 ValueError（拒挂）。"""
    res = check_cao_approval(doc, charter_path)
    if not res["ok"]:
        raise ValueError(res["reason"])


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="树挂载 CAO 批门校验（fail-closed）")
    ap.add_argument("charter", help="taskcharter json 或 md 的伴生 json 路径")
    args = ap.parse_args(argv)
    p = Path(args.charter)
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"{REASON_MISSING}（读取失败: {e}）")
        return 2
    res = check_cao_approval(doc, p)
    if res["ok"]:
        print("CAO 批门=通过")
        return 0
    print(res["reason"] or REASON_MISSING)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
