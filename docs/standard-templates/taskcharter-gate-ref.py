# 任务书挂载门·参考实现（检查规范 v1.1·裁定 B）
#   判定序：G0 工具/解析 → G1 准入 → G2 指纹在位 → G3 内容绑定。C1–C6（形检查）不在本件。
#   fail-closed：任何读/解码/解析/计算失败一律 GATE_TOOL_FAIL——「取值失败≠空值」。
#   BOM（§六 裁定 B）：解析层取字段前剥去串首 U+FEFF；指纹层对原字节算（BOM 计入）。两步勿混。
import sys, json, importlib.util, os
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('fp_ref', os.path.join(_here, 'taskcharter-fingerprint-ref.py'))
_fp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_fp)
HEX = set('0123456789abcdef')

def gate(raw):
    """raw: charter 文件的原始字节。返回 (code, detail)。code=='PASS' 即可挂载。"""
    try: text = raw.decode('utf-8')                       # 指纹层口径：严格·U+FEFF 保留
    except UnicodeDecodeError: return 'GATE_TOOL_FAIL', 'not UTF-8'
    try: d = json.loads(text.lstrip(chr(0xFEFF)))         # 解析层：仅此一步剥 BOM
    except ValueError as e: return 'GATE_TOOL_FAIL', 'parse ' + type(e).__name__
    # G1 准入（规范 §一/§三·2026-11-27 COS 对表勘正）：
    #   文件已能解析·但 cao_approval 缺 / 非对象 / approved 非 true —— 一律 CAO_NOT_APPROVED。
    #   理由：这是「这份任务书没经 CAO 批」·修复动作=去找 CAO 批；不是工具故障。
    #   GATE_TOOL_FAIL 只留给「文件读不了 / 解析不了」。
    ca = d.get('cao_approval') if isinstance(d, dict) else None
    if not isinstance(ca, dict):
        return 'CAO_NOT_APPROVED', 'cao_approval missing or not an object'
    if ca.get('approved') is not True:
        return 'CAO_NOT_APPROVED', 'approved=%r' % (ca.get('approved'),)
    fpv = ca.get('content_sha256_16')
    if not isinstance(fpv, str) or fpv == '':
        return 'FINGERPRINT_MISSING', 'content_sha256_16=%r' % (fpv,)
    # R-c（CTO 2026-11-27 23:11 裁）：指纹值畸形=内容层问题·修复动作=重签 → FINGERPRINT_MISSING（非工具故障）
    if len(fpv) != 16 or any(c not in HEX for c in fpv):
        return 'FINGERPRINT_MISSING', 'malformed fingerprint %r' % (fpv,)
    try: now, n = _fp.fingerprint_bytes(raw)              # 原字节·含 BOM
    except Exception as e: return 'GATE_TOOL_FAIL', 'fingerprint ' + type(e).__name__
    if n < 1:
        # R-b（CTO 23:11 裁）：commit 键可缺（信息字段·不判）——故不再要求 n==2。
        #   n<1 = 两个键都没命中（指纹键缺失会先被 G2 拦；到此仍 n<1 = 文件里根本没有这两键的文本形）
        #   或 n==-1（非 UTF-8·原字节分支）——两者门都无从对表指纹 = 门无法评估。
        return 'GATE_TOOL_FAIL', 'fingerprint keys not locatable (n=%d)' % n
    if fpv != now:
        return 'CONTENT_CHANGED', 'file=%s signed=%s' % (now, fpv)
    return 'PASS', 'commit_info=%r' % (ca.get('commit', ''),)

if __name__ == '__main__':
    code, detail = gate(open(sys.argv[1], 'rb').read())
    print('%s | detail=%s' % (code, detail)); sys.exit(0 if code == 'PASS' else 1)
