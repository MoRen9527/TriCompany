# 用途：msg-alert-watch.ps1 真源化迁移件（原 .fade/msg-alert-watch.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/notify/msg-alert-watch.windows.ps1

﻿# msg-alert-watch.ps1 — M-SG 常驻告警监控（OS 级，CEO 令 2026-09-17 04:2x）
# 采样：sg 通道 / 双仓 HEAD / 429 态；事件→Windows 通知弹窗 + .fade/msg-alert.log
# 去重：.fade/alert-state.json 存上轮状态，仅变化时弹（心跳巡检补写不弹）
# 用法：powershell -File msg-alert-watch.ps1 [-TestToast]
param([switch]$TestToast)

$ErrorActionPreference = 'SilentlyContinue'
$repo = 'D:/Code/ai/TriMetaverse'
$stateFile = "$repo/.fade/alert-state.json"
$logFile = "$repo/.fade/msg-alert.log"

function Write-Log($msg) {
  "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $msg" | Add-Content -Path $logFile -Encoding UTF8
}

function Show-Toast($title, $msg) {
  try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $texts = $tpl.GetElementsByTagName('text')
    $texts.Item(0).AppendChild($tpl.CreateTextNode($title)) | Out-Null
    $texts.Item(1).AppendChild($tpl.CreateTextNode($msg)) | Out-Null
    $toast = New-Object Windows.UI.Notifications.ToastNotification $tpl
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe').Show($toast)
    return $true
  } catch { Write-Log "toast 失败: $_"; return $false }
}

if ($TestToast) { $r = Show-Toast 'M-SG 监控' '弹窗测试——收到即通道正常'; Write-Log "test toast: $r"; exit }

# ── 采样 ──
$sample = & bash "$repo/docs/workflow/operating-records/2026-W38/ops-msg-work-watch.sh" --once 2>$null
$line = ($sample | Select-Object -First 1)
if (-not $line) { Write-Log '采样失败（无输出）'; exit }
$tmv = if ($line -match 'TMV@(\S+)') { $Matches[1] } else { '' }
$tc = if ($line -match 'TC@(\S+)') { $Matches[1] } else { '' }
$blocked = ($line -match '配额挡')

# 心跳过滤：HEAD 变化时查 commit 主题，巡检补写不算业务动作
$headSubject = ''
if ($tmv) {
  $headSubject = ssh -o ConnectTimeout=10 -o BatchMode=yes fleet@sg-ecs-server "git -C /srv/fleet/TriMetaverse log -1 --format=%s" 2>$null
}
$isHeartbeat = ($headSubject -match '巡检兜底补写')

# ── 读旧状态 ──
$prev = $null
if (Test-Path $stateFile) { try { $prev = Get-Content $stateFile -Raw | ConvertFrom-Json } catch {} }

# ── 判定事件 ──
$alerts = @()
if ($prev) {
  if ($prev.blocked -eq $false -and $blocked) { $alerts += ,@('warn', 'M-SG 配额挡再现', '429 复现——席位 AI 响应受阻，shell 级不受影响') }
  if ($prev.blocked -eq $true -and -not $blocked) { $alerts += ,@('info', 'M-SG 配额已恢复', '429 解除——席位可正常响应') }
  if ($tmv -and $prev.tmv -and $prev.tmv -ne $tmv -and -not $isHeartbeat) { $alerts += ,@('info', "M-SG 仓推进 TMV→$tmv", "主题：$headSubject") }
  if ($tc -and $prev.tc -and $prev.tc -ne $tc) { $alerts += ,@('info', "M-SG 仓推进 TC→$tc", '') }
} else {
  Write-Log '首轮=基线建立，不告警'
}

# ── 落地 ──
foreach ($a in $alerts) {
  $r = Show-Toast $a[1] $a[2]
  Write-Log "ALERT[$($a[0])] $($a[1]) | $($a[2]) | toast=$r"
}
@{ tmv = $tmv; tc = $tc; blocked = $blocked; updated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') } |
  ConvertTo-Json | Set-Content -Path $stateFile -Encoding UTF8
Write-Log "采样：TMV=$tmv TC=$tc blocked=$blocked alerts=$($alerts.Count)"
