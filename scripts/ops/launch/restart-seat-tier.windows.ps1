# 用途：单席滚动重启件（CEO 令 2026-11-27 16:11 席位模型分工·滚动重启 14 席施工）
# 目标机：本机（M 面本地）
# 触发方式：手动（改档位/换档重启复用件·长期留仓——施工毕撤的是 .fade/seat-watchdog.stop flag·本件不撤）
# 真源位：TriCompany/scripts/ops/launch/restart-seat-tier.windows.ps1
#
# 单席流程（fail-closed·四步自检）：①杀前 pid 对表（argv 席名精确匹配·恰 1）→ ②停旧（Stop-Process·
#   验退出≤10s·树内 pwsh 包装壳不杀=其自然退出）→ ③验退（零残留）→ ④以 .fade/launch-seat.ps1 新形拉起
#   （wt new-tab·带 --model 档位·读 seat-model-map.psd1）。前置=stop-flag 在位（看门狗跳过·防抢先拉旧形）。
# 用法：powershell -File restart-seat-tier.windows.ps1 -Seat m-cao [-DryRun]

param(
  [Parameter(Mandatory=$true)][string]$Seat,     # 如 m-cao
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$repo = 'D:\Code\ai\TriMetaverse'
$launcher = "$repo\.fade\launch-seat.ps1"
$stopFlag = "$repo\.fade\seat-watchdog.stop"
$seats = @{
  'm-cao' = @('ChiefAdministrativeOfficer','chief-administrative-officer')
  'm-cfo' = @('ChiefFinancialOfficer','chief-financial-officer')
  'm-cho' = @('ChiefHumanResourcesOfficer','chief-human-resources-officer')
  'm-cos' = @('CEOChiefOfStaff','ceo-chief-of-staff')
  'm-cmo' = @('ChiefMarketingOfficer','chief-marketing-officer')
  'm-coo' = @('ChiefOperatingOfficer','chief-operating-officer')
  'm-cpo' = @('ChiefProductOfficer','chief-product-officer')
  'm-pm'  = @('ProductManager','product-manager')
  'm-cso' = @('CustomerSuccessOfficer','customer-success-officer')
  'm-cto' = @('ChiefTechnologyOfficer','chief-technology-officer')
  'm-sde' = @('SeniorDeploymentEngineer','senior-deployment-engineer')
  'm-fsd' = @('FSD','full-stack-developer')
  'm-rdt' = @('RAndDTrainer','rd-trainer')
  'm-ste' = @('STE','senior-test-engineer')
}
if (-not $seats.ContainsKey($Seat)) { Write-Error "[restart] 未知席: $Seat（bod 不归本件）"; exit 2 }
if (-not (Test-Path $stopFlag)) { Write-Error "[restart] stop-flag 缺——看门狗会抢先拉旧形·先置位"; exit 2 }
if (-not (Test-Path $launcher)) { Write-Error "[restart] launcher 缺: $launcher"; exit 2 }

# ① 杀前 pid 对表（argv 精确·恰 1）
$hits = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
if ($hits.Count -ne 1) { Write-Error "[restart] $Seat pid 对表不恰 1（得 $($hits.Count)）——停手"; exit 2 }
$old = $hits[0]
# 空闲线索（CTO 建议④）：transcript mtime 时距——远=空闲·近=mid-turn 疑（硬杀断半截·须显式判断）
$sid = $null; $sj = Join-Path $env:USERPROFILE (".claude\sessions\{0}.json" -f $old.ProcessId)
if (Test-Path $sj) { try { $sid = (Get-Content $sj -Raw | ConvertFrom-Json).sessionId } catch { } }
$lastAct = '-'; $gapMin = '?'
if ($sid) {
    $jl = Join-Path $env:USERPROFILE (".claude\projects\D--Code-ai-TriMetaverse\{0}.jsonl" -f $sid)
    if (Test-Path $jl) { $j = Get-Item $jl; $lastAct = $j.LastWriteTime.ToString('HH:mm:ss'); $gapMin = [math]::Round(((Get-Date) - $j.LastWriteTime).TotalMinutes, 1) }
}
"[restart] $Seat 旧 pid=$($old.ProcessId) start=$($old.CreationDate.ToString('HH:mm')) argvHasModel=$($old.CommandLine -match '--model') transcriptLastAct=$lastAct（${gapMin}min 前）"
if ($DryRun) { '[restart] DRY-RUN 止于此'; exit 0 }

# ② 停旧 + ③ 验退
Stop-Process -Id $old.ProcessId -Force
$deadline = (Get-Date).AddSeconds(10)
while ((Get-Date) -lt $deadline -and (Get-Process -Id $old.ProcessId -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 250 }
if (Get-Process -Id $old.ProcessId -ErrorAction SilentlyContinue) { Write-Error "[restart] $Seat 旧进程未退"; exit 2 }
Start-Sleep -Seconds 2
$left = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
if ($left.Count -ne 0) { Write-Error "[restart] $Seat 验退失败·残留 $($left.Count)"; exit 2 }
# 空闲前置打印（CTO 建议④·2026-11-27）：拉起前若须硬杀 mid-turn 席· DryRun 行已印 pid/argv；
#   本行实跑面补印杀前 transcript 时距线索（静默分钟由读数器/看门狗 log 侧证——非空闲须 -Force 再跑）。
"[restart] $Seat 旧已退·零残留"

# ④ 新形拉起（wt new-tab·launcher 带 --model 档位）
$s = $seats[$Seat]
$wtArgs = @('new-tab','--title',$Seat,'pwsh','-NoExit','-ExecutionPolicy','Bypass','-File',$launcher,'-Name',$Seat,'-Agent',$s[0],'-Manual',$s[1])
Start-Process wt.exe -ArgumentList ($wtArgs | ForEach-Object { if ($_ -match ' ') { "`"$_`"" } else { $_ } }) -WindowStyle Normal
# 新进程等待=轮询至 120s（假红两实锚：m-cao 冷启 >12s·m-pm 壳→claude 73s〔16:32:48→16:34:01〕——
#   固定 sleep/60s 窗均致假「数=0」红·红即停守住了未二次硬试·实为时序非故障）
$new = @(); $deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
    $new = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
    if ($new.Count -ge 1) { break }
}
# ④argvModel fail-closed 判（CTO 应改③·2026-11-27）：新进程 argv 档位≠期望=红（最直接完工断言·
#   不必等席发话——transcript 层由读数器另判「重启后请求」）
if ($new.Count -ge 1) {
    $am = if ($new[0].CommandLine -match '--model\s+(\S+)') { $Matches[1] } else { '(none)' }
    $expect = & "$PSScriptRoot\launch-seat.ps1" -GetSeatModelTierProbe $Seat 2>$null
    if (-not $expect) {
        # launcher 无探针参数（兼容形）：内置基线同源判（必用 5.4 五席=opus·余=sonnet）
        $expect = if ($Seat -in @('m-cos','m-cto','m-cpo','m-coo','m-cao')) { 'opus' } else { 'sonnet' }
    }
    if ($am -ne $expect) { Write-Error "[restart] $Seat argvModel=$am ≠ 期望档=$expect——钉档失败 fail-closed"; exit 2 }
    "[restart] $Seat argvModel=$am == 期望档=$expect ✓"
}
if ($new.Count -ne 1) { Write-Error "[restart] $Seat 新进程数=$($new.Count)（应 1）"; exit 2 }
$am = if ($new[0].CommandLine -match '--model\s+(\S+)') { $Matches[1] } else { '(none)' }
"[restart] $Seat 新 pid=$($new[0].ProcessId) argvModel=$am  → 完工判据=该席下次请求 transcript model（另读）"
exit 0
