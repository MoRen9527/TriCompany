#!/usr/bin/env python3.11
"""fade_instance_audit — FADE 实例审计线（CEO 2026-11-04 16:21 第三令·并入 00:01 审计 job 同频·TriMMC 8712）。

①每日：全部 FADE 实例执行审计——触发量/五节点链成率/verdict 分布/白跑与异常（fade011 event-watch 系为主+registry 在册实例）。
②每周（--weekly）：FADE 执行 vs 无 FADE 基线对比报告（效率/质量/成本三面）→呈 CEO+归档。
③过程审计：FADE 优化过程追踪（其他实例向 fade011 看齐+fade011 自身完善=registry diff/补齐项变动）每日读数，每周评估结论。
"""
from __future__ import annotations
import argparse, datetime, json, pathlib, re, subprocess, sys

TM = pathlib.Path('/srv/fleet/TriMetaverse')
MBOX = pathlib.Path('/srv/fleet/TriMC/notify-mailbox.json')
REGISTRY = pathlib.Path('/srv/fleet/TriCompany/docs/engineering/fade-registry.md')
VERDICTS = ('APPROVED', 'FROZEN', 'ESCALATED', 'RETRY')


def last_week_dir() -> pathlib.Path:
    weeks = sorted(d for d in (TM / 'docs/workflow/operating-records').glob('2026-W*') if d.is_dir())
    return weeks[-1] if weeks else TM / 'docs/workflow/operating-records'


def read_watch_state():
    f = TM / '.fade/sg-watchlist-state.json'
    try:
        return json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        return {}


def registry_snapshot():
    return {'mtime': REGISTRY.stat().st_mtime, 'instances': len(re.findall(r'^## FADE-', REGISTRY.read_text(encoding='utf-8'), re.M)),
            'sha': subprocess.run(['git', '-C', '/srv/fleet/TriCompany', 'log', '-1', '--format=%h', '--', 'docs/engineering/fade-registry.md'],
                                  capture_output=True, text=True).stdout.strip()}


def scan_week_fade_lines():
    """当周卷 FADE 行：verdict 分布/链成/白跑/异常特征读数。"""
    week = last_week_dir()
    counts = {'verdict': {v: 0 for v in VERDICTS}, 'chain_events': 0, 'blank_runs': 0, 'anomalies': 0, 'optimization_events': []}
    pat_v = re.compile(r'\b(' + '|'.join(VERDICTS) + r')\b')
    pat_blank = re.compile(r'(白跑|空跑|无实质产出|no[- ]op)')
    pat_anom = re.compile(r'(FADE[^\n]{0,30}(失败|异常|超时|error|fail))', re.I)
    pat_opt = re.compile(r'(看齐|完善|升格|补齐项|入册|立册|彩排|收官|开跑)')
    files = list(week.glob('daily-progress.md')) + list(week.glob('cos-decision-audit-latest.json'))
    for f in files:
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if not f.name.endswith('.md'):
            continue
        for line in text.splitlines():
            if 'FADE' not in line and 'fade' not in line:
                continue
            for v in VERDICTS:
                counts['verdict'][v] += len(pat_v.findall(line)) if v in line else 0
            if '链成' in line or '五节点' in line or '链' in line and '成率' in line:
                counts['chain_events'] += 1
            if pat_blank.search(line):
                counts['blank_runs'] += 1
            if pat_anom.search(line):
                counts['anomalies'] += 1
            if pat_opt.search(line) and len(line) > 60:
                counts['optimization_events'].append(line[:200])
    return counts


def daily_run():
    state = read_watch_state()
    reg = registry_snapshot()
    counts = scan_week_fade_lines()
    watches = state.get('watches', state if isinstance(state, list) else [])
    report = {
        'run_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'trigger_volume': len(watches) if isinstance(watches, list) else 'n/a',
        'watch_state_note': 'fade011 开跑前 watch 全关（彩排收官候开跑令）' if isinstance(watches, list) and not watches else '',
        'verdict_dist': counts['verdict'],
        'chain_events_mentions': counts['chain_events'],
        'blank_runs': counts['blank_runs'],
        'anomalies': counts['anomalies'],
        'optimization_process_events': counts['optimization_events'][-5:],
        'registry': reg,
    }
    out = last_week_dir() / 'fade-audit-latest.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return out, report


def weekly_run():
    out, daily = daily_run()
    week = last_week_dir()
    rpt = week / f'fade-weekly-report-{datetime.date.today().strftime("%Y%m%d")}.md'
    rpt.write_text(f'''# FADE 实例周报（{datetime.date.today()}·LG 审计线 CEO 2026-11-04 16:21 令）

## ① 执行审计读数
- 触发量：{daily['trigger_volume']}（{daily['watch_state_note'] or 'watch 在册'}）
- verdict 分布：{json.dumps(daily['verdict_dist'], ensure_ascii=False)}
- 链成相关事件：{daily['chain_events_mentions']}｜白跑：{daily['blank_runs']}｜异常：{daily['anomalies']}

## ② FADE vs 无 FADE 基线对比（三面）
| 面 | FADE 化后读数 | 无 FADE 基线 | 结论 |
|---|---|---|---|
| 效率 | 候积累（周执行时长读数） | 基线读数候补录（FADE 化前同任务历史） | 首期=框架就绪，数据两轮后出结论 |
| 质量 | score 读数（fade011 彩排 S1=14.5/15 在卷） | 手工执行合格率历史 | 同上 |
| 成本 | 消耗读数（CFO 四元键同源） | FADE 化前 token 消耗历史 | 同上 |

## ③ 优化过程追踪与评估结论
- 本周优化事件：{len(daily['optimization_process_events'])} 条（registry sha={daily['registry']['sha']}·在册实例 {daily['registry']['instances']}）
- 事件摘样：{'；'.join(daily['optimization_process_events'][-3:])}
- CHO 评估结论：fade011 彩排收官候开跑令——开跑后基线数据进入收集窗，两轮后本节升实质结论。

（呈 CEO 信箱随附；归档=本件当周卷留痕）
''', encoding='utf-8')
    # 呈 CEO 信箱
    if MBOX.exists():
        d = json.loads(MBOX.read_text(encoding='utf-8'))
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        d['letters'].append({
            "message_id": f"fade-weekly-{now.replace(':','').replace('-','')}",
            "source_seat": "m-duty-cho", "target_seat": "board", "urgent": "normal",
            "title": "[FADE 周报]实例执行 vs 基线对比+优化过程评估（归档在卷）",
            "body": f"FADE 审计线周报（{rpt.name}）已归档 {week.name}。摘要：触发量 {daily['trigger_volume']}｜verdict {json.dumps(daily['verdict_dist'], ensure_ascii=False)}｜白跑 {daily['blank_runs']}｜异常 {daily['anomalies']}｜优化事件 {len(daily['optimization_process_events'])} 条。基线对比三面（效率/质量/成本）首期框架就绪，数据两轮后出实质结论。@m-duty-cho",
            "delivery": "mailbox", "received_at": now, "delivered_at": now, "read": False})
        MBOX.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    return rpt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--weekly', action='store_true')
    a = ap.parse_args()
    if a.weekly:
        print('weekly report:', weekly_run())
    else:
        out, r = daily_run()
        print(f'fade audit done: triggers={r["trigger_volume"]} verdicts={r["verdict_dist"]} report={out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
