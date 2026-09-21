# 用途：notify-track.ps1 真源化迁移件（原 .fade/notify-track.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/notify/notify-track.windows.ps1

﻿# notify-track.ps1 — M-SG NOTIFY 处理状态追踪（BOD 2026-09-21 立面）
# 用法：
#   notify-track.ps1 add    -Title "标题" [-Source "来源"]        # 手动登记 pending
#   notify-track.ps1 done   -Id <序号> [-Note "处理摘要"]         # 标记已处理
#   notify-track.ps1 list   [-All]                                # 列 pending（默认）/全部
#   notify-track.ps1 sync                                         # 从 TriMLC 信箱自动登记新 notify
param(
  [Parameter(Position=0)][string]$Cmd = "list",
  [string]$Title,
  [string]$Source = "m-duty-cos",
  [string]$Id,
  [string]$Note,
  [switch]$All
)
$ErrorActionPreference = "Stop"
$ledger = "D:\Code\ai\TriMetaverse\.fade\notify-ledger.jsonl"
$mailbox = "D:/Code/ai/TriMLC/notify-mailbox.json"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Load-Ledger {
  if (-not (Test-Path $ledger)) { return @() }
  Get-Content $ledger -Encoding UTF8 | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json }
}

function New-Id([object[]]$items) {
  $max = ($items | Measure-Object -Property id -Maximum).Maximum
  $id = 1; if ($max) { $id = [int]$max + 1 }
  return $id
}

switch ($Cmd) {
  "add" {
    $items = @(Load-Ledger)
    $id = New-Id $items
    $rec = [ordered]@{ id = $id; ts = $ts; source = $Source; message_id = ""; title = $Title; status = "pending"; done_ts = ""; note = "" }
    ($rec | ConvertTo-Json -Compress) | Add-Content $ledger -Encoding UTF8
    Write-Output "registered: #$id pending — $Title"
  }
  "done" {
    $items = @(Load-Ledger)
    $hit = $items | Where-Object { $_.id -eq [int]$Id }
    if (-not $hit) { Write-Output "not found: #$Id"; exit 1 }
    $hit.status = "done"; $hit.done_ts = $ts; if ($Note) { $hit.note = $Note }
    $items | ForEach-Object { $_ | ConvertTo-Json -Compress } | Set-Content $ledger -Encoding UTF8
    Write-Output "done: #$Id — $($hit.title)"
  }
  "sync" {
    if (-not (Test-Path $mailbox)) { Write-Output "mailbox not found: $mailbox"; exit 1 }
    $doc = Get-Content $mailbox -Raw -Encoding UTF8 | ConvertFrom-Json
    $letters = @($doc.letters)
    $items = @(Load-Ledger)
    $known = @($items | ForEach-Object { $_.message_id } | Where-Object { $_ })
    $new = 0
    foreach ($l in $letters) {
      if ($known -notcontains $l.message_id) {
        $id = New-Id $items
        $rec = [ordered]@{ id = $id; ts = $ts; source = $l.source_seat; message_id = $l.message_id; title = $l.title; status = "pending"; done_ts = ""; note = "" }
        ($rec | ConvertTo-Json -Compress) | Add-Content $ledger -Encoding UTF8
        $items = @(Load-Ledger)
        $new++
      }
    }
    Write-Output "sync: $new new registered（信箱共 $($letters.Count) 封）"
  }
  "list" {
    $items = @(Load-Ledger)
    if (-not $All) { $items = $items | Where-Object { $_.status -eq "pending" } }
    if (-not $items -or $items.Count -eq 0) { Write-Output "（空——无未处理 notify）"; exit 0 }
    $items | ForEach-Object { Write-Output ("#{0} [{1}] {2} | {3} | {4}" -f $_.id, $_.status, $_.ts, $_.source, $_.title) }
  }
  default { Write-Output "用法: add/done/list/sync"; exit 1 }
}
