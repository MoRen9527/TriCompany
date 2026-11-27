# -*- coding: utf-8 -*-
"""tree_mount_gate 单测（六案·同 CTO 契约）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree_mount_gate import (check_cao_approval, gate_or_raise, REASON_MISSING, REASON_ANCHOR,  # noqa: E402
                             CODE_NOT_APPROVED, CODE_ANCHOR_MISMATCH, CODE_CONTENT_CHANGED)


def test_missing_block_rejected():
    assert check_cao_approval({})["ok"] is False
    assert check_cao_approval({})["reason"] == REASON_MISSING


def test_approved_true_passes():
    r = check_cao_approval({"cao_approval": {"approved": True, "approver": "CAO", "approved_at": "2026-11-26T23:00+0800", "commit": None, "checks": {}}})
    assert r["ok"] is True and r["reason"] is None


def test_approved_false_rejected():
    assert check_cao_approval({"cao_approval": {"approved": False}})["ok"] is False


def test_approved_string_true_rejected():
    # 只认布尔 True（`=== true` 语义）
    assert check_cao_approval({"cao_approval": {"approved": "true"}})["ok"] is False


def test_checks_not_parsed():
    # checks 全 false 但 approved True → 过（checks 供核不供判）
    r = check_cao_approval({"cao_approval": {"approved": True, "checks": {"naming": {"ok": False}}}})
    assert r["ok"] is True


def test_gate_or_raise():
    try:
        gate_or_raise({"cao_approval": {"approved": False}})
        raise AssertionError("should raise")
    except ValueError as e:
        assert str(e) == REASON_MISSING


def test_non_dict_rejected():
    assert check_cao_approval(None)["ok"] is False
    assert check_cao_approval([])["ok"] is False


def test_optional_anchor_match(tmp_path=None):
    import tempfile, hashlib, json
    from pathlib import Path as P
    f = P(tempfile.mkdtemp()) / "charter.json"
    payload = {"x": 1}
    f.write_text(json.dumps(payload), encoding="utf-8")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    r = check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": sha}}, f)
    assert r["ok"] is True


def test_optional_anchor_mismatch():
    import tempfile
    from pathlib import Path as P
    f = P(tempfile.mkdtemp()) / "charter.json"
    f.write_text("{}", encoding="utf-8")
    r = check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": "deadbeefdeadbeef"}}, f)
    assert r["ok"] is False and r["reason"] == REASON_ANCHOR


def test_optional_anchor_absent_passes():
    import tempfile
    from pathlib import Path as P
    f = P(tempfile.mkdtemp()) / "charter.json"
    f.write_text("{}", encoding="utf-8")
    r = check_cao_approval({"cao_approval": {"approved": True}}, f)
    assert r["ok"] is True


def test_code_not_approved():
    r = check_cao_approval({})
    assert r["ok"] is False and r["code"] == CODE_NOT_APPROVED


def test_code_anchor_mismatch():
    import tempfile, subprocess
    from pathlib import Path as P
    d = P(tempfile.mkdtemp())
    f = d / "charter.json"
    f.write_text("{}", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(d), check=True)
    subprocess.run(["git", "-C", str(d), "add", "charter.json"], check=True)
    subprocess.run(["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
    head = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    f.write_text('{"changed": 1}', encoding="utf-8")  # 批后改内容
    r = check_cao_approval({"cao_approval": {"approved": True, "commit": head}}, f)
    assert r["ok"] is False and r["code"] == CODE_ANCHOR_MISMATCH


def test_code_content_changed():
    import tempfile
    from pathlib import Path as P
    f = P(tempfile.mkdtemp()) / "charter.json"
    f.write_text("{}", encoding="utf-8")
    r = check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": "deadbeefdeadbeef"}}, f)
    assert r["ok"] is False and r["code"] == CODE_CONTENT_CHANGED
