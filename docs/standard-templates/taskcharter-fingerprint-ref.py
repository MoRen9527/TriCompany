# 规范化指纹·参考实现（CAO 规范 taskcharter-check-spec v1.1）
#   定位=文本层（不 parse→dump）；置空=只动两键的字符串值；n=两键在文件中的出现次数（与值是否为空无关）
#   JSON 形：全文逐行、引号键；YAML/md 形：仅首个 cao_approval: 块内（防正文同名键被误抹）
#   严格 utf-8 解码（U+FEFF 计入）→ 置空 → 仅 CRLF→LF（孤立 CR 不动）→ sha256 前 16 hex；非 UTF-8：原字节 sha256 前 16（n=-1）
import hashlib
BS=chr(92); CR=chr(13); LF=chr(10)
KEYS=('content_sha256_16','commit')
def _find_key(ln, key, quoted):
    pat=('"'+key+'"') if quoted else key
    a=ln.find(pat)
    if a<0: return None
    if not quoted and a>0 and (ln[a-1].isalnum() or ln[a-1]=='_'): return None   # 防子串键
    c=ln.find(':',a+len(pat))
    if c<0: return None
    o=ln.find('"',c+1)
    if o<0: return None
    p=o+1
    while p<len(ln):
        if ln[p]==BS: p+=2; continue
        if ln[p]=='"': break
        p+=1
    if p>=len(ln): return None
    return o, p          # 值的（开引号下标, 闭引号下标）
def _blank_line(ln, quoted):
    """一行最多置空两键各一次·返回(新行, 命中键数)。每键只找首次出现。"""
    hits=0
    for key in KEYS:
        r=_find_key(ln, key, quoted)
        if r is None: continue
        o,p=r; ln=ln[:o+1]+ln[p:]; hits+=1
    return ln, hits
def _blank_json(text):
    """JSON 形：只从首个含键 "cao_approval" 的位置起置空（其后全文）——
    防排在块之前的字符串值里出现「"content_sha256_16": "…"」形文字被当成键（先占首次出现·致真键反而不被置空）。"""
    a=text.find('"cao_approval"')
    if a<0: return text, 0
    head, tail = text[:a], text[a:]
    lines=tail.split(LF); n=0
    for i in range(len(lines)):
        lines[i],h=_blank_line(lines[i],True); n+=h
    return head + LF.join(lines), n
def _blank_yaml(text):
    lines=text.split(LF); n=0
    for i,ln in enumerate(lines):
        if not ln.rstrip().endswith('cao_approval:'): continue
        ind=len(ln)-len(ln.lstrip())
        for k in range(i+1,len(lines)):
            l2=lines[k]
            if l2.strip()=='': continue
            if l2.strip()=='---' or (len(l2)-len(l2.lstrip()))<=ind: break
            lines[k],h=_blank_line(lines[k],False); n+=h
        break
    return LF.join(lines), n
def fingerprint_text(text):
    is_yaml=any(l.rstrip().endswith('cao_approval:') for l in text.split(LF)[:200])
    s,n=(_blank_yaml if is_yaml else _blank_json)(text)
    s=s.replace(CR+LF,LF)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16], n
def fingerprint_bytes(b):
    try: return fingerprint_text(b.decode('utf-8'))
    except UnicodeDecodeError: return hashlib.sha256(b).hexdigest()[:16], -1
if __name__=='__main__':
    import sys
    f,n=fingerprint_bytes(open(sys.argv[1],'rb').read()); print(f,n)
