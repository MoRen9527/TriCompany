# 用途：单席滚动重启件（席位模型分工·改档位/换档重启复用件·长期留仓——撤的是 flag 不是件）
# 目标机：本机（M 面本地）
# 触发方式：手动（powershell→pwsh·见用法行）
# 真源位：TriCompany/scripts/ops/launch/restart-seat-tier.windows.ps1
#
# 用法：pwsh -File restart-seat-tier.windows.ps1 -Seat m-cao [-DryRun] [-AllowBaselineExpect] [-Force]
#   ⚠须 pwsh7——powershell 5.1（Bash 工具链入口）PSModulePath 污染族：Import-PowerShellDataFile
#   MISSING→期望档落基线（修③·2026-11-28 实锚；头部自检拒跑）。
#
# 单席流程（fail-closed 五步自检）：
#   ①杀前 pid 对表（argv 席名精确·恰 1）+时距线索行
#   ②停旧（Stop-Process·验退出）→记录宿主链→关旧 tab（CEO 00:07 令·验退后拉起前）：
#       旧 claude 父=pwsh 且 cmdline 含 -File …launch-seat.ps1 -Name <席> ⇒
#         父=WindowsTerminal 子 ⇒ helper 子进程 AttachConsole 写 exit（正态退出=WT 必关·禁推定强杀）
#         否则 ⇒ Stop-Process 该 pwsh（独立窗/计划任务宿主）
#       禁杀 WT 主进程（pid 一个挂全部席）；护栏=该 pwsh 下除旧 claude 外有活子进程则不动窗如实报
#   ③验退（零残留）
#   ④新形拉起（launcher 带 --model 档位·Ensure-SeatEnvToken 日志行）→轮询 120s
#       →Assert-NewArgvModel（fail-closed）+期望档 source≠table 红退（-AllowBaselineExpect 放行）
#       +env-sync 日志行消费（该席·晚于拉起时刻·match=true；缺失=红）
# 前置=stop-flag 在位（看门狗跳过·防抢先拉旧形）
param(
  [Parameter(Mandatory=$true)][string]$Seat,
  [switch]$DryRun,
  [switch]$AllowBaselineExpect,
  [switch]$Force
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
# 宿主链记录（②关 tab 用·杀前取）：claude 父=pwsh（-File launch-seat -Name 席）·pwsh 父=WT?
$hostPwsh = $null; $hostKind = 'unknown'; $hostInWt = $false
$pp = $old.ParentProcessId
$pw = Get-CimInstance Win32_Process -Filter "ProcessId=$pp" -ErrorAction SilentlyContinue
if ($pw -and $pw.Name -eq 'pwsh.exe' -and ([string]$pw.CommandLine) -match ('launch-seat\.ps1.*-Name\s+' + [regex]::Escape($Seat))) {
    $hostPwsh = $pw
    $gp = Get-CimInstance Win32_Process -Filter "ProcessId=$($pw.ParentProcessId)" -ErrorAction SilentlyContinue
    if ($gp -and $gp.Name -eq 'WindowsTerminal.exe') { $hostKind = 'wt-tab'; $hostInWt = $true } else { $hostKind = 'standalone-pwsh' }
} else { $hostKind = 'no-launcher-parent' }
"[restart] $Seat 旧 pid=$($old.ProcessId) start=$($old.CreationDate.ToString('HH:mm')) argvHasModel=$($old.CommandLine -match '--model') transcriptLastAct=$lastAct（${gapMin}min 前） host=$hostKind$(if ($hostPwsh) { '/pwsh=' + $hostPwsh.ProcessId })"
if ($DryRun) { '[restart] DRY-RUN 止于此'; exit 0 }

# ② 停旧 + ③ 验退
Stop-Process -Id $old.ProcessId -Force
$deadline = (Get-Date).AddSeconds(10)
while ((Get-Date) -lt $deadline -and (Get-Process -Id $old.ProcessId -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 250 }
if (Get-Process -Id $old.ProcessId -ErrorAction SilentlyContinue) { Write-Error "[restart] $Seat 旧进程未退"; exit 2 }
Start-Sleep -Seconds 2
$left = @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | Where-Object { $_.CommandLine -match ("(?:-n|--resume)\s+" + [regex]::Escape($Seat) + "(\s|$)") })
if ($left.Count -ne 0) { Write-Error "[restart] $Seat 验退失败·残留 $($left.Count)"; exit 2 }
"[restart] $Seat 旧已退·零残留"

# ②.5 关旧 tab（CEO 00:07 令·CTO 派工②·2026-11-28）：位置=③验退后④拉起前
if ($hostPwsh) {
    # 护栏：该 pwsh 下除旧 claude 外的活子进程核（有=不动窗如实报）
    $others = @(Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $hostPwsh.ProcessId) | Where-Object { $_.ProcessId -ne $old.ProcessId -and $_.Name -notin @('OpenConsole.exe','conhost.exe') })
    if ($others.Count -gt 0) {
        Write-Warning "[restart] $Seat 宿主 pwsh($($hostPwsh.ProcessId)) 下有 $($others.Count) 个其他活子进程——不动窗·如实留"
        foreach ($o2 in $others) { Write-Warning ("  child: " + $o2.Name + " pid=" + $o2.ProcessId) }
    } elseif ($hostKind -eq 'wt-tab') {
        # WT tab 形：helper 子进程 FreeConsole→AttachConsole(pwshPid)→向 CONIN$ 写 exit+Enter
        #   （正态退出码 0=WT 默认 automatic 必关——强杀 leaf=非零退出码残留未验·CTO 令禁推定）
        $helper = @'
using System;
using System.Runtime.InteropServices;
public static class TabExit {
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool FreeConsole();
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AttachConsole(uint dwProcessId);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr CreateFileW([MarshalAs(UnmanagedType.LPWStr)] string name, uint access, uint share, IntPtr sec, uint disp, uint flags, IntPtr tmpl);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool WriteConsoleInputW(IntPtr h, INPUT_RECORD[] buf, uint n, out uint written);
  [StructLayout(LayoutKind.Explicit)] public struct INPUT_RECORD { [FieldOffset(0)] public ushort EventType; [FieldOffset(4)] public KeyEventRecord Key; [FieldOffset(4)] public uint dummy; }
  [StructLayout(LayoutKind.Sequential)] public struct KeyEventRecord { public bool KeyDown; public ushort Repeat; public ushort Vk; public ushort Vs; public UnicodeChar Char; public uint State; }
  [StructLayout(LayoutKind.Sequential)] public struct UnicodeChar { public char c; }
  public static bool SendExit(uint targetPid) {
    try {
      if (!FreeConsole()) return false;
      if (!AttachConsole(targetPid)) return false;
      IntPtr h = CreateFileW("CONIN$", 0xC0000000, 0x3, IntPtr.Zero, 3, 0, IntPtr.Zero);
      if (h == IntPtr.Zero || h == (IntPtr)(-1)) return false;
      // "exit" 四键 + Enter
      string s = "exit\r";
      foreach (char ch in s) {
        INPUT_RECORD[] rec = new INPUT_RECORD[1];
        rec[0].EventType = 1; // KEY_EVENT
        rec[0].Key.KeyDown = true; rec[0].Key.Repeat = 1; rec[0].Key.Vk = 0; rec[0].Key.Char.c = ch;
        uint w; if (!WriteConsoleInputW(h, rec, 1, out w)) return false;
        rec[0].Key.KeyDown = false; WriteConsoleInputW(h, rec, 1, out w);
      }
      return true;
    } catch { return false; }
  }
}
'@
        Add-Type -TypeDefinition $helper -ErrorAction SilentlyContinue
        $ok = [TabExit]::SendExit([uint32]$hostPwsh.ProcessId)
        Start-Sleep -Seconds 3
        $pwLeft = Get-CimInstance Win32_Process -Filter "ProcessId=$($hostPwsh.ProcessId)" -ErrorAction SilentlyContinue
        if ($ok -and -not $pwLeft) {
            "[restart] $Seat 旧 tab 已正态关（helper exit·pwsh $($hostPwsh.ProcessId) 消失）"
        } else {
            Write-Warning "[restart] $Seat 旧 tab 关闭未确证（helper=$ok pwshLeft=$([bool]$pwLeft)）——不动强杀·如实留（WT 残留 tab 候人工关）"
        }
    } elseif ($hostKind -eq 'standalone-pwsh') {
        Stop-Process -Id $hostPwsh.ProcessId -Force
        "[restart] $Seat 独立窗宿主 pwsh $($hostPwsh.ProcessId) 已停"
    } else {
        Write-Warning "[restart] $Seat 宿主形态=$hostKind——不动窗·如实留"
    }
} else {
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
# ①env 根修留证消费：seat-env-sync.log 该席·晚于本席拉起时刻·match=true（缺失=红）
Start-Sleep -Seconds 8
$syncLog = "$repo\.fade\seat-env-sync.log"
$ok2 = $false
if (Test-Path $syncLog) {
    $floor = $new[0].CreationDate.AddSeconds(-10)
    $hit = Get-Content $syncLog -Tail 40 | ForEach-Object { try { $_ | ConvertFrom-Json } catch { } } | Where-Object { }
    # 日志形="ts | seat | envSha8=.. srcSha8=.. match=.."（文本行·按 regex 解）
    $tailLines = Get-Content $syncLog -Tail 40
    foreach ($ln in $tailLines) {
        if ($ln -match ('^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| ' + [regex]::Escape($Seat) + ' \| .*match=true$')) {
            $ts = ($ln -split ' \| ')[0]
            try { if (([datetime]$ts) -ge $floor) { $ok2 = $true; break } } catch { }
        }
    }
}
if (-not $ok2) { Write-Error "[restart] $Seat env-sync 日志行缺失/未 match（①根修未生效·标读将静默失效）——红"; exit 2 }
"[restart] $Seat env-sync 日志行 match=true ✓（标读恢复面）"
"[restart] $Seat 新 pid=$($new[0].ProcessId) argvModel=$am  → 完工判据=该席下次请求 transcript model+下拍未读降（读数器另核）"
exit 0
