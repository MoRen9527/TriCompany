#!/usr/bin/env python3.11
"""cos_decision_audit — M 面两 COS（m-cos/m-duty-cos）每日裁决审计（LG-074 后续·CEO 2026-11-04 16:01 令）。

判定双错误+跨天派工域（对表 CEO 15:57 三条款+D-39+纪律册+第二令 2026-11-04 16:12 纠偏）：
  ①错误升级=COS 径裁面事项升级 CEO（三条款：原则合理就认不升级；升级面=原则本身存疑/CEO 三类=重大不可逆/系统硬约束/CEO 保留权）
  ②错误裁决=违 D-39 收口/三条款/现行纪律册条款（v1 规则面：越域裁决特征词+手改发布面特征）
  ③跨天派工形态=连续工作切成跨天多日阶梯排窗（非连续执行按一个 tree 做完）→扣分+知会 COO+知会 CEO
处置：发现→写 CEO 信箱信（notify-mailbox target=bod）+scoring 扣分建议行（audit 报告 JSON 留痕，CHO 当日复核落账）。

源面：
  - m-cos：本机 transcript ~/.claude/projects/-srv-fleet-TriMetaverse/*.jsonl（mtime 24h 内）
  - m-duty-cos（sg 值席）：本机可达兜底=operating-records git 面（fetch 后扫当前周 daily-progress+board 卷中两席裁决行）
用法：python3.11 cos_decision_audit.py --run [--hours 24]
"""
from __future__ import annotations
import argparse, datetime, json, pathlib, re, subprocess, sys

HOME = pathlib.Path.home()
TM = pathlib.Path('/srv/fleet/TriMetaverse')
MBOX = pathlib.Path('/srv/fleet/TriMC/notify-mailbox.json')
PROJECT_DIR = HOME / '.claude/projects/-srv-fleet-TriMetaverse'

# 错误升级特征：径裁面升级 CEO 语（排除三类合法升级语境词）
ESCALATION_PAT = re.compile(r'(呈报\s*CEO|候\s*CEO\s*裁|升级\s*CEO|呈\s*CEO\s*裁决|请示\s*CEO)')
LEGAL_CTX = re.compile(r'(重大不可逆|系统硬约束|保留权|原则.*存疑|三类|硬风险|额度.*尽|不可逆)')
# 错误裁决特征（v1）：手改发布面（D-16 禁）+席间越域裁决词
VIOLATION_PAT = re.compile(r'(直接改.{0,8}(发布位|\.claude/agents|\.github/agents)|绕过.{0,6}(管线|发布链)[^\n]{0,10}(改|写))')
COS_MARK = re.compile(r'@(m-cos|m-duty-cos)|\b(COS 小贾|m-cos|m-duty-cos)\b')
# 跨天派工形态（CEO 2026-11-04 16:12 纠偏·第二令追加审计域）：连续工作被切成跨天多日阶梯排窗
#   特征=一行内 ≥2 个「MM-DD~MM-DD」日期段，或「今日/当天…→…MM-DD~MM-DD」箭头链排窗
CROSS_DAY_PAT = re.compile(
    r'(?:\d{1,2}-\d{1,2}[~至到—-]\d{1,2}-\d{1,2}[^0-9][^\n]*?){2,}'
    r'|(?:今日|当天)[^\n→]{0,24}→[^\n]*\d{1,2}-\d{1,2}[~至到—-]\d{1,2}-\d{1,2}'
    r'|(?:勘定|代码|编码|部署|验证|测试)[^\n]{0,6}→[^\n]*\d{1,2}-\d{1,2}[~至到—-]\d{1,2}-\d{1,2}')
DISPATCH_CTX = re.compile(r'(派工|排窗|排程|计划|阶梯|等窗| rollout|rollout)')


def scan_transcripts(hours: int):
    """扫 m-cos transcript（24h 内 mtime jsonl），抽含裁决/升级/跨天派工特征行。"""
    now = datetime.datetime.now().timestamp()
    hits = []
    if not PROJECT_DIR.exists():
        return hits
    for f in PROJECT_DIR.glob('*.jsonl'):
        if now - f.stat().st_mtime > hours * 3600:
            continue
        try:
            for i, line in enumerate(f.read_text(encoding='utf-8', errors='ignore').splitlines()):
                if len(line) > 20000:
                    continue
                if CROSS_DAY_PAT.search(line) and DISPATCH_CTX.search(line):
                    hits.append({'source': 'm-cos-transcript', 'file': f.name, 'line': i + 1,
                                 'ctx': 'CROSS_DAY', 'snippet': line[:400]})
                elif ESCALATION_PAT.search(line) or VIOLATION_PAT.search(line):
                    ctx = 'LEGAL' if LEGAL_CTX.search(line) else 'CANDIDATE'
                    hits.append({'source': 'm-cos-transcript', 'file': f.name, 'line': i + 1,
                                 'ctx': ctx, 'snippet': line[:400]})
        except Exception:
            continue
    return hits


def scan_operating_records(hours: int):
    """m-duty-cos 兜底：fetch operating-records 后扫当前周卷中两席裁决行。"""
    hits = []
    try:
        subprocess.run(['git', 'fetch', 'origin', 'dev'], cwd=str(TM), capture_output=True, timeout=60)
        subprocess.run(['git', 'merge', '--ff-only', 'origin/dev'], cwd=str(TM), capture_output=True, timeout=60)
    except Exception:
        pass
    weeks = sorted(d for d in (TM / 'docs/workflow/operating-records').glob('2026-W*') if d.is_dir())
    if not weeks:
        return hits
    week = weeks[-1]
    since = (datetime.datetime.now() - datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H')
    for f in list(week.glob('daily-progress.md')) + list(week.glob('*unresolved*')) + list((week / 'trees').rglob('*board*.md') if (week / 'trees').exists() else []):
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for i, line in enumerate(text.splitlines()):
            if CROSS_DAY_PAT.search(line) and DISPATCH_CTX.search(line):
                hits.append({'source': 'op-records(跨天派工域·COO 面)', 'file': str(f.relative_to(TM)),
                             'line': i + 1, 'ctx': 'CROSS_DAY', 'snippet': line[:400]})
            if not COS_MARK.search(line):
                continue
            if ESCALATION_PAT.search(line) and not LEGAL_CTX.search(line):
                hits.append({'source': 'op-records(m-duty-cos 兜底)', 'file': str(f.relative_to(TM)),
                             'line': i + 1, 'ctx': 'CANDIDATE', 'snippet': line[:400]})
    return hits


def notify_coo_crossday(cands, rpt_path):
    """跨天派工候选→知会 COO+知会 CEO（第二令处置面；增量去重沿 prev_items）。"""
    cross = [c for c in cands if c['ctx'] == 'CROSS_DAY']
    if not MBOX.exists() or not cross:
        return
    prev = set()
    try:
        prev = {f"{i['file']}:{i['line']}:{i['snippet'][:100]}" for i in json.loads(rpt_path.read_text(encoding='utf-8')).get('prev_items', []) if i.get('ctx') == 'CROSS_DAY'}
    except Exception:
        pass
    new = [c for c in cross if f"{c['file']}:{c['line']}:{c['snippet'][:100]}" not in prev]
    if not new:
        return
    d = json.loads(MBOX.read_text(encoding='utf-8'))
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    items = '\n'.join(f"- {c['source']} {c['file']}:{c['line']} …{c['snippet'][:160]}" for c in new[:10])
    common = f"跨天派工形态审计（CEO 2026-11-04 16:12 纠偏口径：少做跨天派工·直接连续执行按一个 tree 做完·COS 头尾监控）新增候选 {len(new)} 项：\n{items}\n判定=发现即扣分（performance-scoring-workflow·CHO 当日复核落账）；候选系规则面初筛。"
    for seat in ('coo', 'board'):
        d['letters'].append({
            "message_id": f"crossday-audit-{seat}-{now.replace(':','').replace('-','')}",
            "source_seat": "m-duty-cho", "target_seat": seat, "urgent": "normal",
            "title": f"[跨天派工审计告警]候选 {len(new)} 项（{'知会 COO 面' if seat=='coo' else '知会 CEO 面'}）",
            "body": common, "delivery": "mailbox", "received_at": now, "delivered_at": now, "read": False})
    MBOX.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')


def write_report(cands, prev_items):
    out = TM / 'docs/workflow/operating-records'
    weeks = sorted(d for d in out.glob('2026-W*') if d.is_dir())
    week = weeks[-1] if weeks else out
    rpt = week / 'cos-decision-audit-latest.json'
    rpt.write_text(json.dumps({'run_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               'candidates': len(cands), 'items': cands}, ensure_ascii=False, indent=1),
                   encoding='utf-8')
    # 追写 prev_items 供次日增量比对
    d = json.loads(rpt.read_text(encoding='utf-8'))
    d['prev_items'] = cands
    rpt.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    return rpt


def notify_ceo(cands, rpt_path):
    """发现**新增**候选→CEO 信箱信（增量告警，防重放轰炸；CHO 当日复核落账）。"""
    if not MBOX.exists() or not cands:
        return
    prev = set()
    try:
        prev = {f"{i['file']}:{i['line']}:{i['snippet'][:100]}" for i in json.loads(rpt_path.read_text(encoding='utf-8')).get('prev_items', [])}
    except Exception:
        pass
    new = [c for c in cands if f"{c['file']}:{c['line']}:{c['snippet'][:100]}" not in prev]
    if not new:
        return
    cands = new
    d = json.loads(MBOX.read_text(encoding='utf-8'))
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    items = '\n'.join(f"- [{c['ctx']}] {c['source']} {c['file']}:{c['line']} …{c['snippet'][:160]}" for c in cands[:10])
    d['letters'].append({
        "message_id": f"cos-audit-alert-{now.replace(':','').replace('-','')}",
        "source_seat": "m-duty-cho", "target_seat": "bod", "urgent": "urgent",
        "title": f"[裁决审计告警]两 COS 24h 候选 {len(cands)} 项（双错误判定）",
        "body": f"每日 00:01 裁决审计（CEO 2026-11-04 16:01 令）发现新增候选：\n{items}\n判定细则：错误升级=径裁面升级 CEO（三条款：原则合理就认；升级面=原则存疑/三类）；错误裁决=违 D-39/三条款/纪律册。以上为规则面初筛，CHO 当日复核定谳后按 performance-scoring-workflow 扣分落账。",
        "delivery": "mailbox", "received_at": now, "delivered_at": now, "read": False})
    MBOX.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--hours', type=int, default=24)
    a = ap.parse_args()
    prev_path = sorted((TM / 'docs/workflow/operating-records').glob('2026-W*/cos-decision-audit-latest.json'))
    prev_items = []
    if prev_path:
        try:
            prev_items = json.loads(prev_path[-1].read_text(encoding='utf-8')).get('items', [])
        except Exception:
            pass
    all_hits = scan_transcripts(a.hours) + scan_operating_records(a.hours)
    cands = [h for h in all_hits if h['ctx'] == 'CANDIDATE']
    cross = [h for h in all_hits if h['ctx'] == 'CROSS_DAY']
    rpt = write_report(cands + cross, prev_items)
    notify_ceo(cands, rpt)
    notify_coo_crossday(cross, rpt)
    print(f'audit done: candidates={len(cands)} cross_day={len(cross)} report={rpt}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
