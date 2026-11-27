# 用途：单席滚动重启件（席位模型分工·改档位/换档重启复用件·长期留仓——撤的是 flag 不是件）
# 目标机：本机（M 面本地）
# 触发方式：手动（**须 pwsh7**——powershell 5.1 入口=PSModulePath 污染族·头部自检拒跑）
# 真源位：TriCompany/scripts/ops/launch/restart-seat-tier.windows.ps1
#
# 用法：pwsh -File restart-seat-tier.windows.ps1 -Seat m-cao [-DryRun] [-AllowBaselineExpect] [-Force]
#   -Force=非空闲（LastAct<10min）硬杀放行（默认红退防断 mid-turn）。
#
# 单席流程（fail-closed 五步自检）：
#   ①杀前 pid 对表（argv 席名精确·恰 1）+时距线索行+宿主链记录
#   ②停旧（Stop-Process·验退出）
#   ②.5 关旧 tab（CEO 00:07 令·验退后拉起前）：
#       机制=TerminateProcess(宿主 pwsh, **退出码 0**)（CTO T1 实测=WT 必关充分条件；
#       注入 exit 探针 5/5 不退=机制不成立已弃）；双句柄（TERMINATE 终止+QUERY|SYNCHRONIZE 读码）；
#       判据=WT OpenConsole 子进程数 N→N−1（pwsh 消失只旁证）；
#       **fail-open**：任何失败=状态 failed+警告+照常④拉起（席绝不死于关窗步）；
#       **末尾统一判**：tabState=failed → 红行「席已拉起·旧 tab 残留·停滚候裁」+非零退出
#       （金丝雀失败=滚动循环停·两条件同时成立）
#   ③验退（零残留）
#   ④新形拉起（launcher 带 --model 档位+Ensure-SeatEnvToken）→轮询 120s
#       →Assert-NewArgvModel+期望档 source≠table 红退（-AllowBaselineExpect 放行）
#       +env-sync 日志行消费（该席·晚于拉起·match=true；缺失=红）
# 前置=stop-flag 在位（看门狗跳过·防抢先拉旧形）
param(
  [Parameter(Mandatory=$true)][string]$Seat,
  [switch]$DryRun,
  [switch]$AllowBaselineExpect,
  [switch]$Force                   # 非空闲（LastAct<10min）须显式 -Force 才准硬杀（CTO 应改④）
)
$ErrorActionPreference = 'Stop'
$repo = 'D:\Code\ai\TriMetaverse'
$launcher = "$repo\.fade\launch-seat.ps1"
$stopFlag = "$repo\.fade\seat-watchdog.stop"
# 修③(a)：PSEdition 自检（5.1/Desktop=PSModulePath 污染族入口·拒跑提示换 pwsh）
if ($PSVersionTable.PSEdition -eq 'Desktop') {
  Write-Error "[restart] 本件须 pwsh7 运行（当前=powershell 5.1/Desktop——PSModulePath 污染族：Import-PowerShellDataFile MISSING→期望档落基线）。用法：pwsh -File restart-seat-tier.windows.ps1 -Seat <席>"
  exit 2
}
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

# ① 杀前 pid 对表（argv 精确·恰 1）+空闲线索+宿主链记录（杀前取·退后链仍在）
$hits = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
if ($hits.Count -ne 1) { Write-Error "[restart] $Seat pid 对表不恰 1（得 $($hits.Count)）——停手"; exit 2 }
$old = $hits[0]
$sid = $null; $sj = Join-Path $env:USERPROFILE (".claude\sessions\{0}.json" -f $old.ProcessId)
if (Test-Path $sj) { try { $sid = (Get-Content $sj -Raw | ConvertFrom-Json).sessionId } catch { } }
$lastAct = '-'; $gapMin = '?'
if ($sid) {
    $jl = Join-Path $env:USERPROFILE (".claude\projects\D--Code-ai-TriMetaverse\{0}.jsonl" -f $sid)
    if (Test-Path $jl) { $j = Get-Item $jl; $lastAct = $j.LastWriteTime.ToString('HH:mm:ss'); $gapMin = [math]::Round(((Get-Date) - $j.LastWriteTime).TotalMinutes, 1) }
}
# 宿主链记录（②关 tab 用·杀前取）：claude 父=pwsh（launch-seat -Name 席 **或 launch-m-cos.ps1**·CTO 应改）·pwsh 父=WT?
$hostPwsh = $null; $hostKind = 'unknown'; $hostInWt = $false
$pp = $old.ParentProcessId
$pw = Get-CimInstance Win32_Process -Filter "ProcessId=$pp" -ErrorAction SilentlyContinue
if ($pw -and $pw.Name -eq 'pwsh.exe' -and (([string]$pw.CommandLine) -match ('launch-seat\.ps1.*-Name\s+' + [regex]::Escape($Seat)) -or ($Seat -eq 'm-cos' -and ([string]$pw.CommandLine) -match 'launch-m-cos\.ps1'))) {
    $hostPwsh = $pw
    $gp = Get-CimInstance Win32_Process -Filter "ProcessId=$($pw.ParentProcessId)" -ErrorAction SilentlyContinue
    if ($gp -and $gp.Name -eq 'WindowsTerminal.exe') { $hostKind = 'wt-tab'; $hostInWt = $true } else { $hostKind = 'standalone-pwsh' }
} else { $hostKind = 'no-launcher-parent' }
"[restart] $Seat 旧 pid=$($old.ProcessId) start=$($old.CreationDate.ToString('HH:mm')) argvHasModel=$($old.CommandLine -match '--model') transcriptLastAct=$lastAct（${gapMin}min 前） host=$hostKind$(if ($hostPwsh) { '/pwsh=' + $hostPwsh.ProcessId })"
if ($DryRun) { '[restart] DRY-RUN 止于此'; exit 0 }
# 非空闲硬杀护栏（CTO 应改④·-Force 实现）：LastAct<10min 且无 -Force=红退（防断 mid-turn 半截施工）
if ($gapMin -ne '?' -and [double]$gapMin -lt 10 -and -not $Force) {
    Write-Error "[restart] $Seat 非空闲（LastAct ${gapMin}min 前<10min）——须显式 -Force 才准硬杀（防断 mid-turn）"; exit 2
}

# ② 停旧 + ③ 验退
Stop-Process -Id $old.ProcessId -Force
$deadline = (Get-Date).AddSeconds(10)
while ((Get-Date) -lt $deadline -and (Get-Process -Id $old.ProcessId -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 250 }
if (Get-Process -Id $old.ProcessId -ErrorAction SilentlyContinue) { Write-Error "[restart] $Seat 旧进程未退"; exit 2 }
Start-Sleep -Seconds 2
$left = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
if ($left.Count -ne 0) { Write-Error "[restart] $Seat 验退失败·残留 $($left.Count)"; exit 2 }
"[restart] $Seat 旧已退·零残留"

# ②.5 关旧 tab（CEO 00:07 令·位置=③验退后④拉起前）——**必改②③④+A 重写（CTO 审 2026-11-28 00:41）**：
#   机制=TerminateProcess(宿主 pwsh, **退出码 0**)（注入 exit 探针 5/5 不退=机制不成立·CTO 实测已弃；
#   退出码 0=WT 默认 automatic 必关充分条件·CTO T1 实测 ✓）。
#   **双句柄**（必改 B1）：TERMINATE(0x0001) 终止 + QUERY_LIMITED|SYNCHRONIZE(0x1000|0x100000) 读码
#   （单 TERMINATE 句柄调 GetExitCodeProcess=ACCESS_DENIED 假读·lastErr=5——首跑自领）
#   +WaitForSingleObject 后读=真退出码。
#   **fail-open + 状态变量形（必改③+A）**：整段 try/catch·**try 内零 Write-Error·只置 $tabState**
#   （closed|failed|skipped）——**照常走④拉起**（席绝不死于关窗步）·**文件末尾统一判**：
#   failed=红行「席已拉起·旧 tab 残留·停滚候裁」+非零退出（金丝雀停滚与席不死两条件同时成立——
#   try 内 Write-Error 会被自家 catch 接住→rc=0 假绿·停滚不可达·CTO 实锚）。
if ($hostPwsh) {
    $tabState = 'skipped'; $tabDetail = ''
    try {
        $others = @(Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $hostPwsh.ProcessId) | Where-Object { $_.ProcessId -ne $old.ProcessId -and $_.Name -notin @('OpenConsole.exe','conhost.exe') })
        if ($others.Count -gt 0) {
            $tabState = 'skipped'; $tabDetail = "宿主 pwsh($($hostPwsh.ProcessId)) 下有 $($others.Count) 个其他活子进程——不动窗"
            foreach ($o2 in $others) { Write-Warning ("  child: " + $o2.Name + " pid=" + $o2.ProcessId) }
        } else {
            $wtMain = $null
            if ($hostInWt) { $wtMain = Get-CimInstance Win32_Process -Filter "ProcessId=$($hostPwsh.ParentProcessId)" -ErrorAction SilentlyContinue }
            $openBefore = 0
            if ($wtMain) { $openBefore = @(Get-CimInstance Win32_Process -Filter "Name='OpenConsole.exe'" | Where-Object { $_.ParentProcessId -eq $wtMain.ProcessId }).Count }
            Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class TabKill {
  [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint a, bool b, int pid);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool TerminateProcess(IntPtr h, uint code);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GetExitCodeProcess(IntPtr h, out uint code);
}
'@ -ErrorAction SilentlyContinue
            $hT = [TabKill]::OpenProcess(0x0001, $false, [int]$hostPwsh.ProcessId)                 # PROCESS_TERMINATE
            if ($hT -eq [IntPtr]::Zero) { throw ("OpenProcess(TERMINATE) 失败 pid=" + $hostPwsh.ProcessId) }
            $hQ = [TabKill]::OpenProcess(0x1000 -bor 0x100000, $false, [int]$hostPwsh.ProcessId)   # QUERY_LIMITED|SYNCHRONIZE（必改 B1 双句柄）
            $tk = [TabKill]::TerminateProcess($hT, 0)                                              # 退出码 0=WT 必关
            if (-not $tk) { throw "TerminateProcess 失败" }
            $ec = $null
            if ($hQ -ne [IntPtr]::Zero) {
                [TabKill]::WaitForSingleObject($hQ, 5000) | Out-Null
                $ec = [uint32]4294967295
                [TabKill]::GetExitCodeProcess($hQ, [ref]$ec)
                [TabKill]::CloseHandle($hQ) | Out-Null
            }
            [TabKill]::CloseHandle($hT) | Out-Null
            Start-Sleep -Seconds 5
            $pwLeft = Get-CimInstance Win32_Process -Filter "ProcessId=$($hostPwsh.ProcessId)" -ErrorAction SilentlyContinue
            if ($wtMain) {
                $openAfter = @(Get-CimInstance Win32_Process -Filter "Name='OpenConsole.exe'" | Where-Object { $_.ParentProcessId -eq $wtMain.ProcessId }).Count
                "[restart] $Seat 旧 tab：OpenConsole $openBefore→$openAfter（exitCode=$ec）"
                if ($openAfter -eq ($openBefore - 1)) { $tabState = 'closed' } else { $tabState = 'failed'; $tabDetail = "OpenConsole $openBefore→$openAfter（期望 −1）" }
            } else {
                $tabState = if (-not $pwLeft) { 'closed' } else { 'failed'; $tabDetail = '非 WT 形 pwsh 未消失' }
            }
        }
    } catch {
        # 必改③ fail-open：任何失败=failed+警告·**照常④**（席已杀·绝不升级席死·try 内零 Write-Error）
        $tabState = 'failed'; $tabDetail = "异常：$($_.Exception.Message)"
    }
    if ($tabState -ne 'closed') { Write-Warning "[restart] $Seat 关 tab 状态=$tabState（$tabDetail）——照常④拉起·末尾统一判" }
} else {
    $tabState = 'skipped'; $tabDetail = '无 launcher 父链（外部拉起源）——不动窗'
    Write-Warning "[restart] $Seat 无 launcher 父链（外部拉起源）——不动窗"
}

# ④ 新形拉起（launcher 带 --model 档位+env 根修日志行）
$s = $seats[$Seat]
$wtArgs = @('new-tab','--title',$Seat,'pwsh','-NoExit','-ExecutionPolicy','Bypass','-File',$launcher,'-Name',$Seat,'-Agent',$s[0],'-Manual',$s[1])
Start-Process wt.exe -ArgumentList ($wtArgs | ForEach-Object { if ($_ -match ' ') { "`"$_`"" } else { $_ } }) -WindowStyle Normal
# 新进程等待=轮询至 120s（假红两实锚：m-cao 冷启 >12s·m-pm 壳→claude 73s——固定 sleep/60s 窗均致假「数=0」红）
$new = @(); $deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
    $new = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
    if ($new.Count -ge 1) { break }
}
# ④argvModel fail-closed 判（CTO 应改③）：新进程 argv 档位≠期望=红。
#   期望档=Get-SeatModelTierEx（修③：source≠table=红退·-AllowBaselineExpect 显式放行——
#   防「基线回落≠查表命中」分叉静默错判·完工行印 expectSource=table）
if ($new.Count -ge 1) {
    . "$PSScriptRoot\seat-model-tier.ps1"
    $ex = Get-SeatModelTierEx -SeatName $Seat -MapFile (Join-Path $PSScriptRoot 'seat-model-map.psd1')
    $expect = $ex.tier
    $am = if ($new[0].CommandLine -match '--model\s+(\S+)') { $Matches[1] } else { '(none)' }
    if (-not (Assert-NewArgvModel -Seat $Seat -ArgvModel $am -ExpectTier $expect)) { exit 2 }
    if ($ex.source -ne 'table' -and -not $AllowBaselineExpect) {
        Write-Error "[restart] $Seat 期望档来源=$($ex.source)（非 table）——查表未命中 fail-closed（表坏/席缺·-AllowBaselineExpect 才放行）"; exit 2
    }
    "[restart] $Seat argvModel=$am == 期望档=$expect ✓ expectSource=$($ex.source)"
}
if ($new.Count -ne 1) { Write-Error "[restart] $Seat 新进程数=$($new.Count)（应 1）"; exit 2 }
# ①env 根修留证消费：seat-env-sync.log 该席·晚于本席拉起时刻·match=true（写入后==源·缺失/False=红）
Start-Sleep -Seconds 8
$syncLog = "$repo\.fade\seat-env-sync.log"
$ok2 = $false
if (Test-Path $syncLog) {
    $floor = $new[0].CreationDate.AddSeconds(-10)
    $tailLines = Get-Content $syncLog -Tail 40
    foreach ($ln in $tailLines) {
        if ($ln -match ('^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| ' + [regex]::Escape($Seat) + ' \| .*match=true')) {
            $ts = ($ln -split ' \| ')[0]
            try { if (([datetime]$ts) -ge $floor) { $ok2 = $true; break } } catch { }
        }
    }
}
if (-not $ok2) { Write-Error "[restart] $Seat env-sync 日志行缺失/未 match（①根修未生效·标读将静默失效）——红"; exit 2 }
"[restart] $Seat env-sync 日志行 match=true ✓（标读恢复面）"
"[restart] $Seat 新 pid=$($new[0].ProcessId) argvModel=$am  → 完工判据=该席下次请求 transcript model+下拍未读降（读数器另核）"
# 末尾统一判（CTO 必改 A·2026-11-28 00:41）：tabState=failed → 红行+非零退出
#   （席已拉起=席不死 ✓ + 非零退出=金丝雀/滚动循环停 ✓ 两条件同时成立）
if ($tabState -eq 'failed') {
    [Console]::Error.WriteLine("[restart] 🔴 $Seat 旧 tab 未关·席已拉起·旧 tab 残留——停滚候裁（$tabDetail）")
    exit 3
}
exit 0
