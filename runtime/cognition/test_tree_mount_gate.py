# -*- coding: utf-8 -*-
"""tree_mount_gate 单测（规范 v1.1·TC@e11f1e0）

对表件=规范附件（同仓·单一真源·不手抄）：
- 指纹 10 向量 docs/standard-templates/taskcharter-fingerprint-vectors.md
- 门回归 16 案 docs/standard-templates/taskcharter-gate-regress.py（输入+期望拒因码·直接 import 其 CASES）

夹具纪律（83b370f 教训）：批准块必须在被哈希的文件里·文件按字节写（不经文本模式换行翻译）。
"""
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STD = REPO / "docs" / "standard-templates"
sys.path.insert(0, str(HERE))
import tree_mount_gate as g  # noqa: E402


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, STD / fname)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FP_REF = _load("fp_ref", "taskcharter-fingerprint-ref.py")
REGRESS = _load("gate_regress", "taskcharter-gate-regress.py")

BOM = chr(0xFEFF)
M_CR, M_LF = chr(0x240D), chr(0x2424)   # 向量表记号 ␍ ␤


def _write(raw: bytes, name="charter.json") -> Path:
    f = Path(tempfile.mkdtemp()) / name
    f.write_bytes(raw)                  # 按字节写·杜绝文本模式 CRLF 翻译
    return f


def _code(raw: bytes) -> str:
    """门的全链（G0 读+解析→G1→G3）·返回 code·过=PASS。"""
    try:
        doc = g.parse_charter_json(raw)
    except g.GateToolFail:
        return "GATE_TOOL_FAIL"
    r = g.check_cao_approval(doc, _write(raw))
    return r["code"] or "PASS"


# ── 指纹·10 向量对表 ──

def _vectors():
    md = (STD / "taskcharter-fingerprint-vectors.md").read_text(encoding="utf-8")
    fence = chr(96) * 3
    exp = {m[0]: (m[1], int(m[2])) for m in
           re.findall(r"\| (V\d\d) \| \w+ \| [^|]* \| .([0-9a-f]{16}). \| (-?\d+) \|", md)}
    blocks = dict(re.findall(r"\*\*(V\d\d)\*\*(?:（[^）]*）)?" + fence + r"\n(.*?)\n" + fence, md, flags=re.S))
    return exp, blocks


def _rebuild(vid: str, text: str) -> bytes:
    """向量表记法→逐字节。记法按期望值反推核实：单行块行尾 ␤=物理行终止记号（不属输入）；
    多行块行尾记号属输入；V09 的 ␍␤␤=CRLF（多出的 ␤ 是渲染痕迹）。"""
    if vid == "V06":
        return bytes.fromhex(text.strip())
    out = []
    for line in text.split("\n"):
        if vid == "V09":
            line = line.replace(M_CR + M_LF + M_LF, "\r\n")
        out.append(line.replace(M_CR + M_LF, "\r\n").replace(M_LF, "\n"))
    s = "".join(out)
    if "\n" not in text and s.endswith("\n"):
        s = s[:-1]
    return s.encode("utf-8")


def test_vectors_table_complete():
    exp, blocks = _vectors()
    assert sorted(exp) == sorted(blocks) == ["V%02d" % i for i in range(1, 11)]


@pytest.mark.parametrize("vid", ["V%02d" % i for i in range(1, 11)])
def test_fingerprint_vector(vid):
    exp, blocks = _vectors()
    assert g.fingerprint(_rebuild(vid, blocks[vid])) == exp[vid]


def test_vector_equalities():
    exp, _ = _vectors()
    assert exp["V01"][0] == exp["V02"][0] == exp["V03"][0]
    assert exp["V04"][0] != exp["V01"][0]
    assert exp["V09"][0] == exp["V08"][0]
    assert exp["V10"][0] != exp["V08"][0] and exp["V07"][0] != exp["V01"][0]
    assert exp["V06"][1] == -1 and all(exp[v][1] == 2 for v in exp if v != "V06")


def test_gate_fingerprint_is_the_reference():
    raw = _rebuild("V05", _vectors()[1]["V05"])
    assert g.fingerprint(raw) == FP_REF.fingerprint_bytes(raw)
    assert g.ref_path().is_file() and g.ref_path().parent == STD


# ── 门回归·16 案（CAO 用例表·直接 import·连拒因码一起对） ──

def test_regress_table_has_16():
    assert len(REGRESS.CASES) == 16


@pytest.mark.parametrize("idx", range(16), ids=[c[0] for c in REGRESS.CASES])
def test_gate_regress_16(idx):
    name, text, want = REGRESS.CASES[idx]
    assert _code(text.encode("utf-8")) == want, name


# ── 语义补案（回归表外） ──

def _mk(**kw) -> str:
    return REGRESS.mk(**kw)


def _sign(text: str) -> str:
    return REGRESS.sign(text)


def test_missing_block_is_not_approved():
    # 规范 §一/§三 条文：缺 cao_approval 块=CAO_NOT_APPROVED（gate-ref.py 现判 GATE_TOOL_FAIL·差一已报）
    assert _code(json.dumps({"task_id": "T"}).encode("utf-8")) == "CAO_NOT_APPROVED"


def test_non_dict_json_is_not_approved():
    assert _code(b"[1, 2]") == "CAO_NOT_APPROVED"
    assert g.check_cao_approval(None, None)["code"] == "GATE_TOOL_FAIL"   # 无文件=工具面拒（先于准入）


def test_true_non_utf8_bytes_is_tool_fail():
    assert _code("任务书".encode("gbk")) == "GATE_TOOL_FAIL"


def test_missing_file_and_no_path_are_tool_fail():
    missing = Path(tempfile.mkdtemp()) / "gone.json"
    r = g.check_cao_approval({"cao_approval": {"approved": True, "content_sha256_16": "0" * 16}}, missing)
    assert r["code"] == "GATE_TOOL_FAIL" and r["detail"] and r["expected"] and r["fix"]
    assert g.check_cao_approval({"cao_approval": {"approved": True}})["code"] == "GATE_TOOL_FAIL"


def test_fingerprint_missing_vs_malformed():
    base = json.loads(_mk())
    for bad in ("", None, 123):
        d = json.loads(json.dumps(base)); d["cao_approval"]["content_sha256_16"] = bad
        assert _code(json.dumps(d).encode("utf-8")) == "FINGERPRINT_MISSING"
    for bad in ("ABCDEFGHIJKLMNO", "abc", "0" * 17, "g" * 16):
        d = json.loads(json.dumps(base)); d["cao_approval"]["content_sha256_16"] = bad
        assert _code(json.dumps(d).encode("utf-8")) == "GATE_TOOL_FAIL"


def test_reject_carries_three_elements_and_computed_fp():
    signed = _sign(_mk())
    r = g.check_cao_approval(json.loads(signed), _write(signed.replace("construction", "ignition", 1).encode("utf-8")))
    assert r["code"] == "CONTENT_CHANGED" and r["reason"] == g.REASON_CHANGED
    assert r["detail"] and r["expected"] and r["fix"] and len(r["fingerprint"]) == 16 and r["n"] == 2


def test_bom_signed_file_passes_cli_and_bom_edit_detected():
    signed_bom = _sign(BOM + _mk())
    assert g.main([str(_write(signed_bom.encode("utf-8")))]) == 0            # 带 BOM 件·解析层剥·指纹含 BOM·过
    doc = g.parse_charter_json(signed_bom.encode("utf-8"))                                   # 取字段的解析层剥 BOM
    r = g.check_cao_approval(doc, _write(signed_bom[1:].encode("utf-8")))   # 签后删 BOM
    assert r["code"] == "CONTENT_CHANGED"


def test_cli_exit_codes():
    assert g.main([str(_write(_sign(_mk()).encode("utf-8")))]) == 0
    assert g.main([str(_write(_mk().encode("utf-8")))]) == 1                  # 缺指纹
    assert g.main([str(_write(b"{ not json"))]) == 1                          # 解析失败
    assert g.main([str(_write(_sign(_mk(approved=False)).encode("utf-8")))]) == 1


def test_gate_or_raise_message():
    try:
        g.gate_or_raise(json.loads(_mk(approved=False)), _write(_mk(approved=False).encode("utf-8")))
        raise AssertionError("should raise")
    except ValueError as e:
        assert str(e) == g.REASON_NOT_APPROVED


def test_yaml_md_form_end_to_end():
    y = ("---\ntask_id: TC-20261127-001\nform: inline\ncao_approval:\n  approved: true\n"
         '  commit: ""\n  content_sha256_16: ""\nverify:\n  - "x -> EXIT=0"\n---\n\n正文。\n')
    fp, n = g.fingerprint(y.encode("utf-8"))
    assert n == 2
    signed = y.replace('content_sha256_16: ""', f'content_sha256_16: "{fp}"', 1)
    doc = {"cao_approval": {"approved": True, "commit": "", "content_sha256_16": fp}}
    assert g.check_cao_approval(doc, _write(signed.encode("utf-8"), "charter.md"))["ok"] is True
    backfilled = signed.replace('commit: ""', 'commit: "0123456789abcdef"', 1)          # 信息字段回填·不改指纹
    assert g.check_cao_approval(doc, _write(backfilled.encode("utf-8"), "charter.md"))["ok"] is True
    body_edit = signed.replace("正文。", '正文。例 content_sha256_16: "d"', 1)            # 正文同名键示例=内容·改它须检出
    assert g.check_cao_approval(doc, _write(body_edit.encode("utf-8"), "charter.md"))["code"] == "CONTENT_CHANGED"
    crlf = signed.replace("\n", "\r\n")                                                  # CRLF 重检出·过
    assert g.check_cao_approval(doc, _write(crlf.encode("utf-8"), "charter.md"))["ok"] is True
