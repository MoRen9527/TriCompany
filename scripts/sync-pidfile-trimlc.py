# -*- coding: utf-8 -*-
# 两仓 pidfile/paths 同源核（HEAD 版 vs TriMLC；GBK 规避=bytes 直读）
import subprocess, io

def git_show(repo, refpath):
    r = subprocess.run(['git', '-C', repo, 'show', refpath], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace').replace('\r\n', '\n').rstrip('\n')

def norm_path(p):
    return io.open(p, encoding='utf-8').read().replace('\r\n', '\n').rstrip('\n')

for f in ('src/pidfile.ts', 'src/paths.ts'):
    head = git_show(r'D:\Code\ai\TriRLC', 'HEAD:' + f)
    mlc = norm_path(r'D:\Code\ai\TriMLC' + '\\' + f.replace('/', '\\'))
    print(f, 'HEAD==TriMLC:', head == mlc)
