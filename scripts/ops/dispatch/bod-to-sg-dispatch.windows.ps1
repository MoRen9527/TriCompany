# 用途：bod-to-sg-dispatch.ps1 真源化迁移件（原 .fade/bod-to-sg-dispatch.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/dispatch/bod-to-sg-dispatch.windows.ps1

﻿# bod-to-sg-dispatch.ps1 — BOD→sg 席位回链标准化（内容走文件+短指针+验证重发）
# 用法：bod-to-sg-dispatch.ps1 -Seat m-duty-cos -OrderFile <本地工单路径> [-Pointer "附加一句话"]
param(
  [Parameter(Mandatory=$true)][string]$Seat,
  [Parameter(Mandatory=$true)][string]$OrderFile,
  [string]$Pointer = "【BOD 工单】任务书已送达（scp），路径见通知历史，请读正身后按验收锚执行，收口回执经 LG-036 notify 回 BOD。"
)
$sgHost = "M-SG-47.245.122.61"
$remoteDir = "/srv/fleet/TriMetaverse/docs/workflow/operating-records/2026-W38"
$fname = Split-Path $OrderFile -Leaf

# ⓪设 M 面活跃 flag（轮询器切分钟级；COS 收口后清）
Set-Content -Path "D:\Codei\TriMetaverse\.fade\m-plane-active.flag" -Value (Get-Date -Format o) -Encoding UTF8

# ①scp 送达（内容走稳通道）
scp -o ConnectTimeout=15 $OrderFile "${sgHost}:$remoteDir/" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Output "RESULT: SCP-FAIL（工单未送达）"; exit 1 }
ssh -o ConnectTimeout=15 $sgHost "chown fleet:fleet $remoteDir/$fname" 2>$null
Write-Output "① scp OK: $remoteDir/$fname"

# ②tmux 短指针（一行，-l 字面+独立 Enter）——全部经 ssh 包裹
$ptr = "【BOD 工单】$fname 已送达 $remoteDir/，请读正身执行。$Pointer"
ssh -o ConnectTimeout=15 $sgHost "su - fleet -c 'tmux send-keys -t $Seat -l \"$ptr\"'" 2>$null
Start-Sleep -Seconds 1
ssh -o ConnectTimeout=15 $sgHost "su - fleet -c 'tmux send-keys -t $Seat Enter'" 2>$null

# ③验证（15 秒后 thinking/对话流增量）
Start-Sleep -Seconds 15
$cap = ssh -o ConnectTimeout=15 $sgHost "su - fleet -c 'tmux capture-pane -t $Seat -p -S -12'" 2>$null
$thinking = ($cap | Select-String -Pattern "thinking|Cru|Wan|Ide|Cook|Loll|queued messages" -Quiet)
if ($thinking) { Write-Output "RESULT: PICKED-UP（工单已拾取处理中）"; exit 0 }

# ④重发一次（独立 Enter 两连）
ssh -o ConnectTimeout=15 $sgHost "su - fleet -c 'tmux send-keys -t $Seat Enter'" 2>$null
Start-Sleep -Seconds 1
ssh -o ConnectTimeout=15 $sgHost "su - fleet -c 'tmux send-keys -t $Seat Enter'" 2>$null
Start-Sleep -Seconds 15
$cap2 = ssh -o ConnectTimeout=15 $sgHost "su - fleet -c 'tmux capture-pane -t $Seat -p -S -12'" 2>$null
$thinking2 = ($cap2 | Select-String -Pattern "thinking|Cru|Wan|Ide|Cook|Loll|queued messages" -Quiet)
if ($thinking2) { Write-Output "RESULT: PICKED-UP（重发后拾取）" } else { Write-Output "RESULT: QUEUED-OR-UNCONFIRMED（已入队或未验——busy 席排队属正常，人工复核 $Seat）" }
