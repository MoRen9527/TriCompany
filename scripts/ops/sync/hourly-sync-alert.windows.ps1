# 用途：hourly-sync-alert.ps1 真源化迁移件（原 .fade/hourly-sync-alert.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/sync/hourly-sync-alert.windows.ps1

﻿# hourly-sync-alert.ps1 — 本地↔GitHub 落后告警（只读零改写；落后弹 toast 人择时机 pull）
$repo = 'D:\Code\ai\TriMetaverse'
$log = "$repo\.fade\sync-alert.log"
try {
  # notify 处理状态追踪（§12.4 同族）：自动登记新 notify + pending 提醒
  try {
    & powershell -NoProfile -File "D:/Code/ai/TriMetaverse/.fade/notify-track.ps1" sync 2>$null
    $pend = @(powershell -NoProfile -File "D:/Code/ai/TriMetaverse/.fade/notify-track.ps1" list)
    if ($pend.Count -gt 0 -and $pend[0] -notmatch "空") {
      "$ts NOTIFY-PENDING=$($pend.Count)" | Add-Content $log -Encoding UTF8
    }
  } catch {}

  git -C $repo fetch --quiet origin 2>$null
  $behind = [int](git -C $repo rev-list --count HEAD..origin/dev 2>$null)
  $ahead = [int](git -C $repo rev-list --count origin/dev..HEAD 2>$null)
  $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  $autoPushNote = ""
  if ($ahead -gt 0) {
    $pushOut = git -C $repo push origin dev 2>&1
    if ($LASTEXITCODE -eq 0) {
      $autoPushNote = "；挂账 $ahead 笔已自动补推"
      "$ts AUTO-PUSH OK ($ahead 笔)" | Add-Content $log -Encoding UTF8
      $ahead = 0
    } else {
      $autoPushNote = "；挂账 $ahead 笔候窗（网未开）"
      "$ts AUTO-PUSH FAIL（网窗未开）" | Add-Content $log -Encoding UTF8
    }
  }
  if ($behind -gt 0 -or $autoPushNote -match "候窗") {
    "$ts BEHIND=$behind AHEAD=$ahead" | Add-Content $log -Encoding UTF8
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $t.GetElementsByTagName('text').Item(0).AppendChild($t.CreateTextNode('TriMetaverse 同步告警')) | Out-Null
    $msg = ""
    if ($behind -gt 0) { $msg += "落后 GitHub $behind 笔 — 择无人编辑窗口 git pull --ff-only" }
    if ($autoPushNote) { $msg += $autoPushNote }
    $t.GetElementsByTagName('text').Item(1).AppendChild($t.CreateTextNode($msg)) | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($t)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('TriMetaverse.SyncAlert').Show($toast)
  } else {
    "$ts CLEAN behind=0 ahead=0" | Add-Content $log -Encoding UTF8
  }
} catch {
  "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ERR: $_" | Add-Content $log -Encoding UTF8
}
