# sync.ps1 — 运行脚本真源→部署位单向维护（LG-035 运行脚本真源化批 §3 自举件）
# 用途：把 TriCompany/scripts/ops/ 真源件单向拷贝至本机部署位（.fade/），
#       部署位头部自动注入生成标记；部署位被直写=diff 检测警告先发现再定性。
# 目标机：本机（M 面本地）
# 触发方式：手动/收口批触发（每日收口批节奏——BOD 裁 2026-09-20 攒批节奏）
# 真源位：TriCompany/scripts/ops/sync/sync.ps1（自举件）
# 用法：powershell -File sync.ps1 [-DryRun]
#
# 谱系注记（TASK-SYNC-CONSOLIDATE-01；CTO 判 2026-09-22 14:02「淘汰 py 保 ps1」）：
#   前代 sync.py 三笔功绩谱系——f60106f（LG-035 立件·幂等三跑实测达标）→ e2ff079（VBS 毒化根修·
#   标记类型感知首立）→ 7ceab65（BOM 归一批随件）；本笔已 git rm 下架（git 史即档）。
#   防线遗产承接：29158d0（标记类型感知+VBS 无 BOM 写入）+ 1f78619（WriteAllText 字节精确幂等）。
#   淘汰四条：①ps1=现役实证代（三笔修复+17×identical 真幂等），py 无剩余独有防线；
#             ②部署位=Windows 本机，ps1 零运行时依赖，与守卫/watchdog ps1 生态同族；
#             ③双代并存=损害发生器（py 修过的雷 ps1 重写丢过一次，e2ff079→29158d0 自证）；
#             ④淘汰≠删除：git rm+本注记归档，功绩谱系留痕。
#   通用化候选=D-30「脚本资产一代一实现」（候选文案见 TMV W39 task-sync-consolidate-01-readings）。

param([switch]$DryRun, [switch]$Force)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$fadeRoot = 'D:\Code\ai\TriMetaverse\.fade'
# 生成标记按部署件类型取前缀（.vbs 用 ' 注释形——# 形对 VBS 是语法错误；承 sync.py e2ff079 毒化根修同款教训）

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
    # 生成标记注入（已注入=跳过；前缀按部署件类型）
    $marker = if ([IO.Path]::GetExtension($m.dst) -ieq '.vbs') { "' generated from TriCompany/scripts/ops — 禁直写（sync.ps1 单向维护）" } else { '# generated from TriCompany/scripts/ops — 禁直写（sync.ps1 单向维护）' }
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
    # 统一 WriteAllText 字节精确写入（Set-Content 追加行终止符致写入件「永不 identical」空转——幂等锚修复）；
    # 编码按型：.vbs 无 BOM（wscript 毒化防线），其余 UTF-8 带 BOM（D-09 友好，维持现部署位字节形）
    $enc = if ([IO.Path]::GetExtension($m.dst) -ieq '.vbs') { [Text.UTF8Encoding]::new($false) } else { [Text.UTF8Encoding]::new($true) }
    [IO.File]::WriteAllText($dstPath, $srcText, $enc)
    Write-Host "[sync] updated: $($m.dst)"
}
Write-Host '[sync] done'
