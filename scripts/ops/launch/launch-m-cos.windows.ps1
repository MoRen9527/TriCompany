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
. "$PSScriptRoot\resume-disambig.ps1"
Invoke-ResumeDisambig -Name 'm-cos' -WorkingDir 'D:\Code\ai\TriMetaverse'
claude --resume m-cos -n m-cos --agent CEOChiefOfStaff --verbose --dangerously-skip-permissions --append-system-prompt-file D:/Code/ai/TriMetaverse/.claude/compass/ceo-chief-of-staff.session.md
