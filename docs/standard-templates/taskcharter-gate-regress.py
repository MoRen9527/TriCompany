# 任务书挂载门·回归用例（检查规范 v1.1·含 §六 裁定 B·G1 边界 2026-11-27 COS 对表后定）——三处实现移植本脚本的「输入+期望拒因码」做合流抽验。
#   跑法：python taskcharter-gate-regress.py   →  末行 TOTAL n/n·全过 rc=0
#   签法约定：指纹对「将来要成为文件的那段文本」整体算（签时带 BOM 的·指纹就含 BOM）·再把值填入。
import sys, json, os, importlib.util
_here = os.path.dirname(os.path.abspath(__file__))
def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_here, fname))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
ref = _load('fp_ref', 'taskcharter-fingerprint-ref.py'); G = _load('gate_ref', 'taskcharter-gate-ref.py')
LF = chr(10); CR = chr(13); BOM = chr(0xFEFF); E = '"content_sha256_16": ""'
def mk(approved=True, commit='', note=None):
    d = {"task_id": "T", "authorization": {"scope": "construction"},
         "cao_approval": {"approved": approved, "approver": "CAO", "approved_at": "t", "commit": commit, "content_sha256_16": ""}}
    if note is not None: d["note"] = note
    return json.dumps(d, ensure_ascii=False, indent=1) + LF
def sign(text):                                   # 对整段文本算·再填
    f, _ = ref.fingerprint_bytes(text.encode('utf-8')); return text.replace(E, '"content_sha256_16": "' + f + '"', 1)
def malformed(s):                                 # 把 16hex 改成大写字母
    a = s.split('"content_sha256_16": "')[1][:16]; return s.replace(a, 'ABCDEFGHIJKLMNO', 1)
def mk_nocommit():                                # 签时就没有 commit 键（R-b：信息字段可缺）
    d = json.loads(mk()); del d['cao_approval']['commit']
    return json.dumps(d, ensure_ascii=False, indent=1) + LF
s_nc = sign(mk_nocommit())
d_signed = sign(mk()); d_del = json.loads(d_signed); del d_del['cao_approval']['commit']; s_delcommit = json.dumps(d_del, ensure_ascii=False, indent=1) + LF
s_nb = sign(mk()); s_b = sign(BOM + mk())
CASES = [
 ('① 真签真指纹',                         sign(mk()),                                         'PASS'),
 ('② 指纹缺',                             mk(),                                               'FINGERPRINT_MISSING'),
 ('③ 内容改',                             sign(mk()).replace('"construction"', '"ignition"', 1), 'CONTENT_CHANGED'),
 ('④ commit 回填（信息字段·不判）',         sign(mk(commit='f' * 40)),                          'PASS'),
 ('⑤ 解析失败',                           '{ not json',                                        'GATE_TOOL_FAIL'),
 ("⑤a 合法 UTF-8 但非 JSON 文本",         '任务书'.encode('gbk').decode('latin-1'),            'GATE_TOOL_FAIL'),   # 注：此件经 latin-1 转写后已是合法 UTF-8·测的是解析失败
 ("⑤b 真非 UTF-8 字节（GBK）→ 解码失败",   '任务书'.encode('gbk'),                             'GATE_TOOL_FAIL'),   # 真 GBK 字节·不走文本路径
 ("⑤c 空文件",                          b'',                                                 'GATE_TOOL_FAIL'),
 ("⑤d 顶层数组（合法 JSON 非对象）",       '[1,2,3]',                                          'CAO_NOT_APPROVED'),
 ('G1-a 缺 cao_approval 块',              '{"task_id":"T"}',                               'CAO_NOT_APPROVED'),
 ('G1-b cao_approval 为字符串',           '{"cao_approval":"yes"}',                        'CAO_NOT_APPROVED'),
 ('G1-c cao_approval 为 null',           '{"cao_approval":null}',                          'CAO_NOT_APPROVED'),
 ('G1-d approved 键缺',                  '{"cao_approval":{"approver":"CAO"}}',          'CAO_NOT_APPROVED'),
 ('G1-e approved 为字符串 "true"（非布尔）', '{"cao_approval":{"approved":"true"}}',          'CAO_NOT_APPROVED'),
 ('⑦ CRLF 重检出',                        sign(mk()).replace(LF, CR + LF),                    'PASS'),
 ('⑨ approved=false（先于指纹判）',         mk(approved=False),                                  'CAO_NOT_APPROVED'),
 ('⑪ 块前伪键·原文',                      sign(mk(note='例 content_sha256_16: "AAAA"')),        'PASS'),
 ('⑪ 块前伪键·签后只改伪键值',             sign(mk(note='例 content_sha256_16: "AAAA"')).replace('AAAA', 'ZZZZ'), 'CONTENT_CHANGED'),
 ('B1 带 BOM 件（签时即带·指纹含 BOM）',    s_b,                                                 'PASS'),
 ('B2 无 BOM 签·签后加 BOM',               BOM + s_nb,                                          'CONTENT_CHANGED'),
 ('B3 带 BOM 签·签后删 BOM',               s_b[1:],                                             'CONTENT_CHANGED'),
 ('B4 带 BOM·未批',                       BOM + mk(approved=False),                            'CAO_NOT_APPROVED'),
 ('R-b 签时即无 commit 键（信息字段可缺）→ 挂', s_nc,                                              'PASS'),
 ('R-b2 签时有 commit 键·签后把整键删掉 → 拒', s_delcommit,                                         'CONTENT_CHANGED'),
 ('R-b3 签后给 commit 回填值 → 不影响',      d_signed.replace('"commit": ""', '"commit": "' + 'f' * 40 + '"', 1), 'PASS'),
 ('R-c 指纹畸形（非小写 hex）→ 重签',       malformed(sign(mk())),                               'FINGERPRINT_MISSING'),
 ('R-c2 指纹长度 15',                      sign(mk()).replace(sign(mk()).split('"content_sha256_16": "')[1][:16], sign(mk()).split('"content_sha256_16": "')[1][:15], 1), 'FINGERPRINT_MISSING'),
 ('R-c3 指纹含非 hex 字符 g',               sign(mk()).replace(sign(mk()).split('"content_sha256_16": "')[1][:16], 'gggggggggggggggg', 1), 'FINGERPRINT_MISSING'),

]
def run():
    ok = 0
    for name, data, want in CASES:
        raw = data if isinstance(data, bytes) else data.encode('utf-8')   # 允许 bytes 案（真非 UTF-8 字节）
        code = G.gate(raw)[0]; good = code == want; ok += good
        print(('  PASS  ' if good else '  FAIL  ') + '%-36s → %s%s' % (name, code, '' if good else '   (期望 %s)' % want))
    print('  TOTAL %d/%d' % (ok, len(CASES))); return ok == len(CASES)
if __name__ == '__main__':
    sys.exit(0 if run() else 1)
