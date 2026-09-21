# -*- coding: utf-8 -*-
# sync.py — 运行脚本真源→部署位单向维护（LG-035 运行脚本真源化批 §3 自举件）
# 用途：TriCompany/scripts/ops/ 真源件单向拷贝至本机部署位（.fade/），
#       部署位头部自动注入生成标记；部署位被直写=diff 检测警告先发现再定性。
# 目标机：本机（M 面本地）
# 触发方式：手动/收口批触发（每日收口批节奏——BOD 裁 2026-09-20 攒批节奏）
# 真源位：TriCompany/scripts/ops/sync/sync.py（自举件）
# 用法：python sync.py [--dry-run] [--force]（--force=首轮引导覆盖原生件）
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FADE_ROOT = r'D:\Code\ai\TriMetaverse\.fade'
MARKER = '# generated from TriCompany/scripts/ops — 禁直写（sync.ps1 单向维护）'

MAP = [
    ('watchdog/seat-watchdog.windows.ps1', 'seat-watchdog.ps1'),
    ('watchdog/seat-watchdog.windows.vbs', 'seat-watchdog.vbs'),
    ('notify/msg-alert-watch.windows.ps1', 'msg-alert-watch.ps1'),
    ('notify/msg-alert-watch.windows.vbs', 'msg-alert-watch.vbs'),
    ('notify/msg-work-watch.windows.cmd', 'msg-work-watch.cmd'),
    ('notify/msg-work-watch.windows.vbs', 'msg-work-watch.vbs'),
    ('notify/notify-poller.windows.ps1', 'notify-poller.ps1'),
    ('notify/notify-poller.windows.vbs', 'notify-poller.vbs'),
    ('notify/notify-track.windows.ps1', 'notify-track.ps1'),
    ('sync/hourly-sync-alert.windows.ps1', 'hourly-sync-alert.ps1'),
    ('sync/hourly-sync-alert.windows.vbs', 'hourly-sync-alert.vbs'),
    ('launch/launch-m-cos.windows.ps1', 'launch-m-cos.ps1'),
    ('launch/launch-seat.windows.ps1', 'launch-seat.ps1'),
    ('launch/seat-boot.windows.vbs', 'seat-boot.vbs'),
    ('dispatch/bod-to-sg-dispatch.windows.ps1', 'bod-to-sg-dispatch.ps1'),
    ('admin/admin-fix.windows.ps1', 'admin-fix.ps1'),
    ('admin/cleanup-narrative.windows.py', 'cleanup-narrative.py'),
]


def main():
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    mode = 'DRY-RUN' if dry_run else 'EXECUTE'
    if force:
        mode += '+FORCE'
    print(f'[sync] mode={mode} files={len(MAP)}')
    updated = identical = skipped = 0
    for src_rel, dst_name in MAP:
        src = os.path.join(REPO_ROOT, 'scripts', 'ops', src_rel.replace('/', os.sep))
        dst = os.path.join(FADE_ROOT, dst_name)
        if not os.path.exists(src):
            print(f'[sync] WARN 真源缺件: {src_rel}')
            continue
        with open(src, encoding='utf-8-sig') as f:
            src_text = f.read()
        # 生成标记注入（已注入=跳过）
        if MARKER not in src_text:
            src_text = MARKER + '\n' + src_text
        if not os.path.exists(dst):
            if dry_run:
                print(f'[sync] would create: {dst_name}')
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'w', encoding='utf-8', newline='') as f:
                f.write(src_text)
            updated += 1
            print(f'[sync] created: {dst_name}')
            continue
        with open(dst, encoding='utf-8-sig') as f:
            dst_text = f.read()
        # 归一比较（BOM/CRLF 差异不算漂移——幂等锚）
        norm = lambda t: t.replace('\ufeff', '').replace('\r\n', '\n')
        if norm(src_text) == norm(dst_text):
            print(f'[sync] identical: {dst_name}')
            identical += 1
            continue
        # 直写检测：部署位缺生成标记且与真源不一致=被直写嫌疑
        if MARKER not in dst_text and not force:
            print(f'[sync] WARN 部署位被直写嫌疑（缺生成标记）：{dst_name} —— 先发现再定性，本轮跳不覆盖（首轮引导用 --force）')
            skipped += 1
            continue
        if dry_run:
            print(f'[sync] would update: {dst_name}')
            continue
        with open(dst, 'w', encoding='utf-8', newline='') as f:
            f.write(src_text)
        updated += 1
        print(f'[sync] updated: {dst_name}')
    print(f'[sync] done — updated={updated} identical={identical} skipped={skipped}')


if __name__ == '__main__':
    main()
