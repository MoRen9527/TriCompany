# 用途：launch-m-cos.ps1 真源化迁移件（原 .fade/launch-m-cos.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/launch/launch-m-cos.windows.ps1

﻿# launch-m-cos.ps1 — COS 干净环境重启器（清 CLAUDE* 遗传变量后按正名形态拉起）
Remove-Item Env:CLAUDE_CODE_CHILD_SESSION -ErrorAction SilentlyContinue
Get-ChildItem Env: | Where-Object Name -like "CLAUDE*" | Remove-Item -ErrorAction SilentlyContinue
$env:CLAUDE_CODE_FORCE_SESSION_PERSISTENCE = "1"
Set-Location D:\Code\ai\TriMetaverse
# resume-by-title 去歧义（同名多命中弹会话选择器防线；fail-open 不挡启动——2026-10-05 CEO 令）
# 零历史容忍双形态（2026-11-01 CEO 令·与 launch-seat 同批）：候选 ≥1=原组合 --resume 零变化；
#   0=零历史/去歧义故障走纯 -n 注册形（--resume 零命中报 No sessions match 卡席——m-pm 实证）。
. "$PSScriptRoot\resume-disambig.ps1"
# 席位模型分工（CEO 令 2026-11-27 16:11）：m-cos=必用 glm-5.4 → --model opus（查同表·改分工只改表）
function Get-SeatModelTier([string]$SeatName) {
  # 基线=CEO 现行裁定（m-cos 必用 5.4→opus）——表不可读回落此值（cos 不向低档·与 launch-seat 基线同 commit 维护）。
  $tier = 'opus'
  try {
    $mapFile = Join-Path $PSScriptRoot 'seat-model-map.psd1'
    if (Test-Path $mapFile) {
      $map = Import-PowerShellDataFile -Path $mapFile
      $seats = $map['Seats']
      if ($seats -is [hashtable] -and $seats.ContainsKey($SeatName) -and $seats[$SeatName]) { $tier = [string]$seats[$SeatName] }
    } else {
      [Console]::Error.WriteLine("[launch-m-cos] 表不可读·回落基线：$SeatName=$tier")
    }
  } catch {
    [Console]::Error.WriteLine("[launch-m-cos] 表读失败·回落基线：$SeatName=$tier")
  }
  return $tier
}
$ModelTier = Get-SeatModelTier 'm-cos'
$sessionCount = Invoke-ResumeDisambig -Name 'm-cos' -WorkingDir 'D:\Code\ai\TriMetaverse'
if ($sessionCount -ge 1) {
  claude --resume m-cos -n m-cos --agent CEOChiefOfStaff --model $ModelTier --verbose --dangerously-skip-permissions --append-system-prompt-file D:/Code/ai/TriMetaverse/.claude/compass/ceo-chief-of-staff.session.md
} else {
  claude -n m-cos --agent CEOChiefOfStaff --model $ModelTier --verbose --dangerously-skip-permissions --append-system-prompt-file D:/Code/ai/TriMetaverse/.claude/compass/ceo-chief-of-staff.session.md
}
