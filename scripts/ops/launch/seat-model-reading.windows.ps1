# 用途：席位实际模型读数器（CEO 令 2026-11-27 16:11 席位模型分工·完工判据件）
# 目标机：本机（M 面本地）
# 触发方式：手动/滚动重启施工时调用（只读·零副作用）
# 真源位：TriCompany/scripts/ops/launch/seat-model-reading.windows.ps1
#
# 读法链（三跳·每跳活体实读）：claude.exe pid --(argv 席名)--> 席
#   --(~/.claude/sessions/<pid>.json sessionId)--> transcript
#   --(jsonl 尾部 assistant 行 message.model)--> 该席最近一次请求的实际模型
# 完工判据（BOD 令）=「每席下一次请求的模型与档位一致」——非「进程在」。
# 档位→期望模型：opus=glm-5.4｜sonnet=glm-5.3-flash（跟 settings.json 别名映射·此处为读数对表面）
# 用法：powershell -File seat-model-reading.windows.ps1 [-TailLines 400]

param([int]$TailLines = 400)

$ErrorActionPreference = 'SilentlyContinue'
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$mapFile = Join-Path $repoRoot 'scripts/ops/launch/seat-model-map.psd1'
$sessDir = Join-Path $env:USERPROFILE '.claude\sessions'
$projDir = Join-Path $env:USERPROFILE '.claude\projects\D--Code-ai-TriMetaverse'

$tierModel = @{ opus = 'glm-5.4'; sonnet = 'glm-5.3-flash' }
# 对表面=独立于被测表（CTO 必改①·2026-11-27）：仪器与被测件共用同源=假绿（表缺/坏时被测席与期望同落
#   sonnet→假 MATCH）——期望档位内置 CEO 现行裁定（D-99 款 1）硬编码作对表面，禁读 psd1。
#   改分工时此处与 psd1 同 commit 更新（两处）。
$baseline = @{ 'm-cos'='opus'; 'm-cto'='opus'; 'm-cpo'='opus'; 'm-coo'='opus'; 'm-cao'='opus' }   # 必用 5.4 五席=opus·余=sonnet

$rows = @()
$procs = Get-CimInstance Win32_Process -Filter "Name='claude.exe'"
foreach ($p in $procs) {
    $c = [string]$p.CommandLine
    if ($c -notmatch '(?:-n|--resume)\s+(m-[a-z]+)') { continue }   # bod 不归本件（CEO 手动切）·非席进程跳过
    $seat = $Matches[1]
    $tier = if ($baseline.ContainsKey($seat)) { $baseline[$seat] } else { 'sonnet' }
    $expect = $tierModel[$tier]
    $argvModel = if ($c -match '--model\s+(\S+)') { $Matches[1] } else { '(none)' }
    $sid = $null; $model = $null; $lastTs = $null
    $sj = Join-Path $sessDir ("{0}.json" -f $p.ProcessId)
    if (Test-Path $sj) {
        try { $sid = (Get-Content $sj -Raw | ConvertFrom-Json).sessionId } catch { }
    }
    if ($sid) {
        $jl = Join-Path $projDir ("{0}.jsonl" -f $sid)
        if (Test-Path $jl) {
            $tail = Get-Content $jl -Tail $TailLines
            for ($i = $tail.Count - 1; $i -ge 0; $i--) {
                try { $o = $tail[$i] | ConvertFrom-Json } catch { continue }
                if ($o.type -eq 'assistant' -and $o.message.model) { $model = [string]$o.message.model; $lastTs = $o.timestamp; break }
            }
        }
    }
    $verdict = if (-not $model) { 'NO-READING' } else { 'MISMATCH' }
    # 时点闸（2026-11-27 首跑假读实锚）：--resume 复用旧 session（同 sid 追加写）——重启后席若尚未发请求，
    #   jsonl 尾行=旧进程的最后一条（model 是旧模型·时刻早于本进程启动）。完工判据=「重启后的请求」
    #   ⇒ LastReq < 进程启动 = 历史行不可判 → PENDING（重启后尚无请求·非 MISMATCH 亦非 MATCH）。
    if ($model -and $p.CreationDate) {
        $reqT = ([datetime]$lastTs).ToUniversalTime()
        if ($reqT -lt $p.CreationDate.ToUniversalTime()) { $verdict = 'PENDING' }
    }
    if ($model -eq $expect -and $verdict -ne 'PENDING') { $verdict = 'MATCH' }
    # ArgvModel 联判（CTO 应改③·2026-11-27）：旧启动器拉起（argv 无 --model）+会话默认恰好对=假 MATCH
    #   ——钉未入不判 MATCH；argvModel!=tier → ARGV-TIER-MISMATCH（独立红·不等席发话即见）。
    if ($verdict -ne 'PENDING' -and $argvModel -ne '(none)' -and $argvModel -ne $tier) { $verdict = 'ARGV-TIER-MISMATCH' }
    if ($verdict -eq 'MATCH' -and $argvModel -eq '(none)') { $verdict = 'ARGV-MISSING' }
    $rows += [PSCustomObject]@{
        Seat = $seat; Pid = $p.ProcessId; Tier = $tier; Expect = $expect
        ArgvModel = $argvModel; Actual = $(if ($model) { $model } else { '-' })
        LastReq = $(if ($lastTs) { ([datetime]$lastTs).ToString('HH:mm:ss') } else { '-' }); Verdict = $verdict
    }
}
$rows | Sort-Object Seat | Format-Table -AutoSize | Out-String -Width 160
$sum = $rows | Group-Object Verdict | ForEach-Object { "$($_.Name)=$($_.Count)" }
"[reading] " + ($sum -join ' ') + "  (ts=" + (Get-Date -Format 'HH:mm:ss') + ")"
