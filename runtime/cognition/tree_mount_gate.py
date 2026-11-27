#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""树挂载 CAO 批门（COS 面·一源三处同判据第三处）

判据真源（三处引用·不各自复写）：CAO 检查规范 §三/§三A/§三B
（TriCompany/docs/standard-templates/taskcharter-check-spec-v1.0.md）
+ 批模板 v1.0.1 §⓪ cao_approval 块。

两层语义（两层任一不过皆拒·拒因 code 必须不同）：
- 第一层·准入：缺 cao_approval 块 或 approved !== true → code=CAO_NOT_APPROVED
  （checks/approver/approved_at 不解析·供核不供判）
- 第二层·批的有效性：
  - commit 非空：`git show <commit>:<仓内相对路径>` 的 sha256_16 ≠ 现文件
    → code=ANCHOR_MISMATCH
  - content_sha256_16 有值：≠ 现文件 sha256_16 → code=CONTENT_CHANGED
- 宽容面（§三B 四条·放行）：commit 空／commit 锚不可验／content 无值／现文件不可读
  → 有记名的宽容：note 必写；弱绑定件带 binding_weak=true + mount_form="b"

报错行（三处统一字串）：`CAO 批缺失·拒挂任务书`／`批后内容变更·须重签`
拒因三要素（§三B）：每 code 附 detail/expected/fix（非空）。

函数签名与 TriRMC 两处同源：
  check_cao_approval(doc, charter_path=None) ->
      {ok, reason, code, note, detail, expected, fix, binding_weak, mount_form}
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

_FIX_APPROVE = "请 CAO 批后写 cao_approval 块（approved: true·余字段供核不供判）"
_FIX_RESIGN = "任务书内容批后已变·请 CAO 按现内容重签（commit 锚/content_sha256_16 重算）"


def _file_sha256_16(path: Path | None) -> str | None:
    if path is None or not Path(path).is_file():
        return None
    import hashlib

    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def _reject(code: str, detail: str) -> dict[str, Any]:
    """拒返回：code + 拒因三要素（detail/expected/fix·非空）。"""
    if code == CODE_NOT_APPROVED:
        reason, expected, fix = REASON_MISSING, "approved: true", _FIX_APPROVE
    else:
        reason, expected, fix = REASON_ANCHOR, "现文件内容 == CAO 批时所见内容", _FIX_RESIGN
    return {"ok": False, "reason": reason, "code": code, "detail": detail,
            "expected": expected, "fix": fix, "note": None,
            "binding_weak": False, "mount_form": None}


def _committed_sha256_16(charter_path: Path, commit: str) -> tuple[str | None, str | None]:
    """`git show <commit>:<仓内相对路径>` 的 sha256 前 16 位。

    路径按仓根相对取（非 basename）——嵌套目录件（如 docs/.../charter.json）亦可验；
    用 basename 会让非仓根件一律 git show 失败→静默落宽容面（假通过）。
    返回 (sha16, None)；不可验返回 (None, 原因)。
    """
    import hashlib
    import subprocess

    try:
        p = Path(charter_path).resolve()
        top = subprocess.run(["git", "-C", str(p.parent), "rev-parse", "--show-toplevel"],
                             capture_output=True, timeout=10)
        toplevel = top.stdout.decode("utf-8", "replace").strip()
        if top.returncode != 0 or not toplevel:
            return None, "非 git 工作区"
        try:
            rel = p.relative_to(Path(toplevel)).as_posix()
        except ValueError:
            return None, "不在仓内"
        out = subprocess.run(["git", "-C", toplevel, "show", f"{commit}:{rel}"],
                             capture_output=True, timeout=10)
        if out.returncode != 0:
            return None, "git show 失败·commit 或路径不存在"
        return hashlib.sha256(out.stdout).hexdigest()[:16], None
    except Exception as e:  # noqa: BLE001
        return None, f"不可验·{type(e).__name__}"


def check_cao_approval(doc: dict[str, Any] | None, charter_path: Path | None = None) -> dict[str, Any]:
    """CAO 批门（fail-closed）。第一层准入 → 第二层批的有效性 → 宽容面留痕。"""
    if not isinstance(doc, dict):
        return _reject(CODE_NOT_APPROVED, "doc 非 dict")
    block = doc.get("cao_approval")
    if not isinstance(block, dict):
        return _reject(CODE_NOT_APPROVED, "cao_approval 块缺失")
    if block.get("approved") is not True:
        return _reject(CODE_NOT_APPROVED, f"approved={block.get('approved')!r}（需 true）")

    raw_commit = block.get("commit")
    commit = raw_commit.strip() if isinstance(raw_commit, str) else ""
    raw_claim = block.get("content_sha256_16")
    claim = raw_claim.strip() if isinstance(raw_claim, str) else ""
    actual = _file_sha256_16(charter_path)
    notes: list[str] = []
    weak = False

    # 第二层·批的有效性：commit 锚（(a) 形态·可验则比对·不可验=记名宽容）
    if commit:
        if charter_path is None:
            want, why = None, "未提供 charter_path"
        else:
            want, why = _committed_sha256_16(charter_path, commit)
        if want is None:
            weak = True
            notes.append(f"commit 锚不可验（{why}）·内容绑定弱")
        elif actual is None:
            notes.append("现文件不可读·commit 锚不可比·内容不可复核")
        elif actual != want:
            return _reject(CODE_ANCHOR_MISMATCH, f"commit={commit} 冻结={want} 现={actual}")
    else:
        weak = True
        notes.append("commit 锚空·内容绑定弱")

    # 第二层·批的有效性：content_sha256_16（有值才比·不等=拒）
    if claim:
        if actual is None:
            notes.append("现文件不可读·content_sha256_16 锚不可验·内容不可复核")
        elif actual != claim:
            return _reject(CODE_CONTENT_CHANGED, f"content_sha256_16 冻结={claim} 现={actual}")
        else:
            notes.append("按 content_sha256_16 比对通过")

    return {"ok": True, "reason": None, "code": None,
            "detail": None, "expected": None, "fix": None,
            "binding_weak": weak, "mount_form": "b" if weak else "a",
            "note": "·".join(notes) if notes else None}


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
        print("CAO 批门=通过" + (f"（{res['note']}）" if res.get("note") else ""))
        return 0
    print(res["reason"] or REASON_MISSING)
    print(f"code={res.get('code')} detail={res.get('detail')} expected={res.get('expected')} fix={res.get('fix')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
