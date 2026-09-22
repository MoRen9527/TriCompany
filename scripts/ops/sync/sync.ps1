# sync.ps1 — 运行脚本真源→部署位单向维护（LG-035 运行脚本真源化批 §3 自举件）
# 用途：把 TriCompany/scripts/ops/ 真源件单向拷贝至本机部署位（.fade/），
#       部署位头部自动注入生成标记；部署位被直写=diff 检测警告先发现再定性。
# 目标机：本机（M 面本地）
# 触发方式：手动/收口批触发（每日收口批节奏——BOD 裁 2026-09-20 攒批节奏）
# 真源位：TriCompany/scripts/ops/sync/sync.ps1（自举件）
# 用法：powershell -File sync.ps1 [-DryRun]

param([switch]$DryRun, [switch]$Force)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$fadeRoot = 'D:\Code\ai\TriMetaverse\.fade'
$marker = '# generated from TriCompany/scripts/ops — 禁直写（sync.ps1 单向维护）'

# 真源→部署位映射（<真源 rel> → <部署位名>）
$map = @(
    @{ src = 'watchdog/seat-watchdog.windows.ps1';        dst = 'seat-watchdog.ps1' },
    @{ src = 'watchdog/seat-watchdog.windows.vbs';        dst = 'seat-watchdog.vbs' },
    @{ src = 'notify/msg-alert-watch.windows.ps1';        dst = 'msg-alert-watch.ps1' },
    @{ src = 'notify/msg-alert-watch.windows.vbs';        dst = 'msg-alert-watch.vbs' },
    @{ src = 'notify/msg-work-watch.windows.cmd';         dst = 'msg-work-watch.cmd' },
    @{ src = 'notify/msg-work-watch.windows.vbs';         dst = 'msg-work-watch.vbs' },
    @{ src = 'notify/notify-poller.windows.ps1';          dst = 'notify-poller.ps1' },
    @{ src = 'notify/notify-poller.windows.vbs';          dst = 'notify-poller.vbs' },
    @{ src = 'notify/notify-track.windows.ps1';           dst = 'notify-track.ps1' },
    @{ src = 'sync/hourly-sync-alert.windows.ps1';        dst = 'hourly-sync-alert.ps1' },
    @{ src = 'sync/hourly-sync-alert.windows.vbs';        dst = 'hourly-sync-alert.vbs' },
    @{ src = 'launch/launch-m-cos.windows.ps1';           dst = 'launch-m-cos.ps1' },
    @{ src = 'launch/launch-seat.windows.ps1';            dst = 'launch-seat.ps1' },
    @{ src = 'launch/seat-boot.windows.vbs';              dst = 'seat-boot.vbs' },
    @{ src = 'dispatch/bod-to-sg-dispatch.windows.ps1';   dst = 'bod-to-sg-dispatch.ps1' },
    @{ src = 'admin/admin-fix.windows.ps1';               dst = 'admin-fix.ps1' },
    @{ src = 'admin/cleanup-narrative.windows.py';        dst = 'cleanup-narrative.py' }
)

$mode = if ($DryRun) { 'DRY-RUN' } else { 'EXECUTE' }
Write-Host "[sync] mode=$mode files=$($map.Count)"

foreach ($m in $map) {
    $srcPath = Join-Path $repoRoot ('scripts/ops/' + $m.src)
    $dstPath = Join-Path $fadeRoot $m.dst
    if (-not (Test-Path $srcPath)) { Write-Warning "[sync] 真源缺件: $($m.src)"; continue }
    $srcText = Get-Content $srcPath -Raw -Encoding UTF8
    # 生成标记注入（已注入=跳过）
    if (-not $srcText.Contains($marker)) {
        $srcText = $marker + "`r`n" + $srcText
    }
    if (Test-Path $dstPath) {
        $dstText = Get-Content $dstPath -Raw -Encoding UTF8
        # 归一比较（BOM/CRLF 差异不算漂移——幂等锚）
        $norm = { param($t) ($t -replace "^﻿", '') -replace "`r`n", "`n" }
        $a = & $norm $srcText
        $b = & $norm $dstText
        if ($a -eq $b) { Write-Host "[sync] identical: $($m.dst)"; continue }
        # 直写检测：部署位缺生成标记且与真源不一致=被直写嫌疑
        if (-not $dstText.Contains($marker) -and -not $Force) {
            Write-Warning "[sync] 部署位被直写嫌疑（缺生成标记）：$($m.dst) —— 先发现再定性，本轮跳不覆盖（首轮引导用 -Force）"
            continue
        }
    }
    if ($DryRun) { Write-Host "[sync] would update: $($m.dst)"; continue }
    Set-Content -Path $dstPath -Value $srcText -Encoding UTF8
    Write-Host "[sync] updated: $($m.dst)"
}
Write-Host '[sync] done'
