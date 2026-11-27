# -*- coding: utf-8 -*-
"""tree_mount_gate 单测（COS 第三处·判据真源=CAO 检查规范 §三/§三A/§三B·与 TriRMC 两处同构）"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree_mount_gate import (check_cao_approval, gate_or_raise, main,  # noqa: E402
                             REASON_MISSING, REASON_ANCHOR, CODE_NOT_APPROVED,
                             CODE_ANCHOR_MISMATCH, CODE_CONTENT_CHANGED)


def _file(body: str = "{}") -> Path:
    f = Path(tempfile.mkdtemp()) / "charter.json"
    f.write_text(body, encoding="utf-8")
    return f


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def _git_repo_charter() -> tuple[Path, str]:
    """建真 git 仓·charter 放嵌套目录 docs/tree/（非仓根·验相对路径取法）。"""
    d = Path(tempfile.mkdtemp())
    f = d / "docs" / "tree" / "charter.json"
    f.parent.mkdir(parents=True)
    f.write_text('{"a": 1}', encoding="utf-8")
    g = ["git", "-C", str(d)]
    subprocess.run(g + ["init", "-q"], check=True)
    subprocess.run(g + ["add", "."], check=True)
    subprocess.run(g + ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
    head = subprocess.run(g + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return f, head


# ── 第一层·准入 ──

def test_missing_block_rejected_with_three_elements():
    r = check_cao_approval({})
    assert r["ok"] is False and r["reason"] == REASON_MISSING and r["code"] == CODE_NOT_APPROVED
    assert r["detail"] and r["expected"] and r["fix"]  # 拒因三要素非空


def test_approved_true_passes_as_b_form():
    r = check_cao_approval({"cao_approval": {"approved": True, "approver": "CAO",
                                             "approved_at": "2026-11-26T23:00+0800", "commit": None, "checks": {}}})
    assert r["ok"] is True and r["reason"] is None
    assert r["binding_weak"] is True and r["mount_form"] == "b" and r["note"]  # commit 空=(b)·留痕


def test_approved_false_rejected():
    assert check_cao_approval({"cao_approval": {"approved": False}})["code"] == CODE_NOT_APPROVED


def test_approved_string_true_rejected():
    # 只认布尔 True（`=== true` 语义）
    assert check_cao_approval({"cao_approval": {"approved": "true"}})["ok"] is False


def test_checks_not_parsed():
    # checks 全 false 但 approved True → 过（checks 供核不供判）
    assert check_cao_approval({"cao_approval": {"approved": True, "checks": {"naming": {"ok": False}}}})["ok"] is True


def test_gate_or_raise():
    try:
        gate_or_raise({"cao_approval": {"approved": False}})
        raise AssertionError("should raise")
    except ValueError as e:
        assert str(e) == REASON_MISSING


def test_non_dict_rejected():
    assert check_cao_approval(None)["code"] == CODE_NOT_APPROVED
    assert check_cao_approval([])["code"] == CODE_NOT_APPROVED


# ── 第二层·content_sha256_16（(b) 形态主路径） ──

def test_b_form_content_match_passes_with_note():
    f = _file()
    r = check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": _sha(f)}}, f)
    assert r["ok"] is True and r["binding_weak"] is True and r["mount_form"] == "b"
    assert "通过" in r["note"] and "commit 锚空" in r["note"]


def test_b_form_content_mismatch_rejected():
    f = _file()
    r = check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": "deadbeefdeadbeef"}}, f)
    assert r["ok"] is False and r["code"] == CODE_CONTENT_CHANGED and r["reason"] == REASON_ANCHOR
    assert "deadbeefdeadbeef" in r["detail"] and r["expected"] and r["fix"]


def test_b_form_no_anchor_passes_weak():
    f = _file()
    r = check_cao_approval({"cao_approval": {"approved": True}}, f)
    assert r["ok"] is True and r["binding_weak"] is True and "commit 锚空" in r["note"]


# ── 第二层·commit 锚（(a) 形态·嵌套目录件） ──

def test_a_form_commit_anchor_match_nested_file():
    f, head = _git_repo_charter()
    r = check_cao_approval({"cao_approval": {"approved": True, "commit": head}}, f)
    assert r["ok"] is True and r["binding_weak"] is False and r["mount_form"] == "a"


def test_a_form_anchor_mismatch_after_edit():
    f, head = _git_repo_charter()
    f.write_text('{"changed": 1}', encoding="utf-8")  # 批后改内容
    r = check_cao_approval({"cao_approval": {"approved": True, "commit": head}}, f)
    assert r["ok"] is False and r["code"] == CODE_ANCHOR_MISMATCH and r["reason"] == REASON_ANCHOR


def test_commit_ok_but_content_changed_rejected():
    # §三B 表：content_sha256_16 有值且不符=拒（不限形态）
    f, head = _git_repo_charter()
    r = check_cao_approval({"cao_approval": {"approved": True, "commit": head,
                                             "content_sha256_16": "deadbeefdeadbeef"}}, f)
    assert r["ok"] is False and r["code"] == CODE_CONTENT_CHANGED


def test_unverifiable_commit_passes_weak_with_note():
    # commit 填了但验不了（对象不存在）=记名宽容·非静默
    f, _ = _git_repo_charter()
    r = check_cao_approval({"cao_approval": {"approved": True, "commit": "deadbeef"}}, f)
    assert r["ok"] is True and r["binding_weak"] is True and "不可验" in r["note"]


# ── 宽容面·现文件不可读 ──

def test_unreadable_file_passes_with_note():
    missing = Path(tempfile.mkdtemp()) / "gone.json"
    r = check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": "deadbeefdeadbeef"}}, missing)
    assert r["ok"] is True and "不可读" in r["note"]


# ── CLI 壳 ──

def test_cli_exit_codes():
    f = _file(json.dumps({"cao_approval": {"approved": False}}))
    assert main([str(f)]) == 1
    f.write_text(json.dumps({"cao_approval": {"approved": True}}), encoding="utf-8")
    assert main([str(f)]) == 0
