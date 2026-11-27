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
$map = $null
try { $map = Import-PowerShellDataFile -Path $mapFile } catch { }

$rows = @()
$procs = Get-CimInstance Win32_Process -Filter "Name='claude.exe'"
foreach ($p in $procs) {
    $c = [string]$p.CommandLine
    if ($c -notmatch '(?:-n|--resume)\s+(m-[a-z]+)') { continue }   # bod 不归本件（CEO 手动切）·非席进程跳过
    $seat = $Matches[1]
    $tier = 'sonnet'; $src = 'default'
    if ($map -and $map['Seats'] -is [hashtable] -and $map['Seats'].ContainsKey($seat)) { $tier = [string]$map['Seats'][$seat]; $src = 'table' }
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
    $rows += [PSCustomObject]@{
        Seat = $seat; Pid = $p.ProcessId; Tier = $tier; Expect = $expect
        ArgvModel = $argvModel; Actual = $(if ($model) { $model } else { '-' })
        LastReq = $(if ($lastTs) { ([datetime]$lastTs).ToString('HH:mm:ss') } else { '-' }); Verdict = $verdict
    }
}
$rows | Sort-Object Seat | Format-Table -AutoSize | Out-String -Width 160
$sum = $rows | Group-Object Verdict | ForEach-Object { "$($_.Name)=$($_.Count)" }
"[reading] " + ($sum -join ' ') + "  (ts=" + (Get-Date -Format 'HH:mm:ss') + ")"
