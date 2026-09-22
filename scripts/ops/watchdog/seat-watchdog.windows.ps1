# 用途：seat-watchdog.ps1 真源化迁移件（原 .fade/seat-watchdog.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/watchdog/seat-watchdog.windows.ps1
# 判定面根修（TASK-WATCHDOG-JUDGE-FIX-01，CEO 批 2026-09-22 19:31）：在岗判定由 --resume 单特征
#   扩为 (-n|--resume) 双参数特征（D-32 弃转录重生形态自此可见，根治盲拉）；超员检测补装（同席名
#   多实例仅日志告警，只警不杀）。D-30 一代一实现纪律适用（本件=watchdog 唯一现役实现代）。

﻿# seat-watchdog.ps1 — 12 席常驻看门狗（单一看门狗原则，CEO 令 2026-09-17）
# 用法：powershell -File seat-watchdog.ps1 [-Bootstrap]
#   -Bootstrap: 开机模式（拉起全部缺席席，单 wt 窗多 tab 最小化）
# 停止标志：.fade/seat-watchdog.stop 存在即本轮跳过（尊重人工停止）
param([switch]$Bootstrap)
$ErrorActionPreference = 'SilentlyContinue'
$repo = 'D:\Code\ai\TriMetaverse'
$stopFlag = "$repo/.fade/seat-watchdog.stop"
$log = "$repo/.fade/seat-watchdog.log"
$launcher = "$repo/.fade/launch-seat.ps1"

$seats = @(
  @('m-cao','ChiefAdministrativeOfficer','chief-administrative-officer'),
  @('m-cfo','ChiefFinancialOfficer','chief-financial-officer'),
  @('m-cho','ChiefHumanResourcesOfficer','chief-human-resources-officer'),
  @('m-cos','CEOChiefOfStaff','ceo-chief-of-staff'),
  @('m-cmo','ChiefMarketingOfficer','chief-marketing-officer'),
  @('m-coo','ChiefOperatingOfficer','chief-operating-officer'),
  @('m-cpo','ChiefProductOfficer','chief-product-officer'),
  @('m-cso','CustomerSuccessOfficer','customer-success-officer'),
  @('m-cto','ChiefTechnologyOfficer','chief-technology-officer'),
  @('m-sde','SeniorDeploymentEngineer','senior-deployment-engineer'),
  @('m-fsd','FSD','full-stack-developer'),
  @('m-rdt','RAndDTrainer','rd-trainer'),
  @('m-ste','STE','senior-test-engineer')
)

function Write-Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $m" | Add-Content "$repo/.fade/seat-watchdog.log" -Encoding UTF8 }
function Test-StopFlag { Test-Path $stopFlag }

if (Test-StopFlag) { Write-Log 'stop-flag 在位，本轮跳过'; exit }

$procs = Get-CimInstance Win32_Process -Filter "Name='claude.exe'" -ErrorAction SilentlyContinue
# 在岗判定（TASK-WATCHDOG-JUDGE-FIX-01 双特征版）：(-n|--resume) <席名>(\s|$) 任一命中即在岗
$missing = @()
foreach ($s in $seats) {
  $hits = @($procs | Where-Object { $_.CommandLine -match ("(-n|--resume) " + $s[0] + "(\s|$)") })
  if ($hits.Count -eq 0) {
    $missing += ,$s
  } elseif ($hits.Count -gt 1) {
    # 超员告警：只警不杀（归一动作走 BOD 明令单，如 LG-045 阶段二）
    Write-Log ("超员告警: {0} ×{1} [PID: {2}]" -f $s[0], $hits.Count, (($hits | ForEach-Object { $_.ProcessId }) -join ','))
  }
}

if ($missing.Count -eq 0) { Write-Log "全部 12 席在位，零动作"; exit }

$bootArgs = @()
foreach ($s in $missing) {
  Write-Log "拉起缺席席: $($s[0]) ($($s[1]))"
  $bootArgs += @('new-tab','--title',$s[0],'pwsh','-NoExit','-ExecutionPolicy','Bypass','-File',$launcher,'-Name',$s[0],'-Agent',$s[1],'-Manual',$s[2],';')
}
if ($bootArgs[-1] -eq ';') { $bootArgs = $bootArgs[0..($bootArgs.Count-2)] }
if ($Bootstrap) {
  # 开机模式：单窗多 tab 最小化
  Start-Process wt.exe -ArgumentList ($bootArgs | ForEach-Object { if ($_ -match ' ') { "`"$_`"" } else { $_ } }) -WindowStyle Minimized
  Write-Log "Bootstrap: 已最小化拉起 $($missing.Count) 席"
} else {
  # 看门狗模式：逐席独立最小化窗
  foreach ($s in $missing) {
    Start-Process wt.exe -ArgumentList @('new-tab','--title',$s[0],'pwsh','-NoExit','-ExecutionPolicy','Bypass','-File',$launcher,'-Name',$s[0],'-Agent',$s[1],'-Manual',$s[2]) -WindowStyle Minimized
    Start-Sleep -Milliseconds 300
  }
  Write-Log "Watchdog: 已拉起 $($missing.Count) 席（最小化）"
}
