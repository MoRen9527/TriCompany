# 用途：notify-poller.ps1 真源化迁移件（原 .fade/notify-poller.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/notify/notify-poller.windows.ps1

﻿# notify-poller.ps1 — M 面 notify 轮询器（CEO 2026-09-21 19:54 批：Poller 式独立定时）
# 频率：计划任务每分钟触发本脚本；脚本内 flag 节流——
#   .fade/m-plane-active.flag 存在（M 面有任务书挂服务域执行中）→ 每次都干（分钟级）
#   不存在 → 内置半小时节流（距上次实际执行 <30min 则本轮退出）
# 动作：notify-track sync（TriMLC 信箱→台账自动登记）+新信 toast+pending 计数
$ErrorActionPreference = "Continue"
$repo = "D:\Code\ai\TriMetaverse"
$flag = "$repo/.fade/m-plane-active.flag"
$stamp = "$repo/.fade/notify-poller.last"
$log = "$repo/.fade/notify-poller.log"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# 半小时节流（无 flag 时）
if (-not (Test-Path $flag)) {
  if (Test-Path $stamp) {
    $last = Get-Item $stamp | Select-Object -ExpandProperty LastWriteTime
    if (((Get-Date) - $last).TotalMinutes -lt 30) { exit 0 }
  }
}
"exec" | Set-Content $stamp -Encoding UTF8

# sync（新信自动登记）
$syncOut = ""
try {
  $syncOut = powershell -NoProfile -File "$repo/.fade/notify-track.ps1" sync 2>$null
  "$ts | $syncOut" | Add-Content $log -Encoding UTF8
} catch {
  "$ts | sync ERR: $_" | Add-Content $log -Encoding UTF8
}

# 新信 toast（有新登记才弹）
if ($syncOut -match "sync: ([1-9]\d*) new") {
  $n = $Matches[1]
  try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $t.GetElementsByTagName("text").Item(0).AppendChild($t.CreateTextNode("M-SG 新 notify")) | Out-Null
    $t.GetElementsByTagName("text").Item(1).AppendChild($t.CreateTextNode("$n 笔新信已登记——notify-track list 查看")) | Out-Null
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("TriMetaverse.NotifyPoller").Show([Windows.UI.Notifications.ToastNotification]::new($t))
  } catch {}
}
