# 用途：席→模型档位查表共享件（CTO 复核 2026-11-27 修③·单一基线+单一查表逻辑——
#   launch-seat / launch-m-cos / restart-seat-tier 三处 dot-source 本件·漂移面合一）
# 目标机：本机（M 面本地）
# 触发方式：启动器/重启件运行时 dot-source
# 真源位：TriCompany/scripts/ops/launch/seat-model-tier.ps1
#
# ⚠改分工须「seat-model-map.psd1 + 本件 $SeatModelBaseline + 读数器对表面」同 commit 更新。
#   读数器（seat-model-reading.windows.ps1）**不共享本件**——仪器与被测分离（CTO 必改①判线），
#   其内置对表面独立维护。

# 基线=CEO 现行裁定硬编码（D-99 款 1）：必用 5.4 五席=opus·余=sonnet——
#   表不可读/席缺时回落此基线（必用席禁静默降档·失败方向=必用席不落 flash）。
$script:SeatModelBaseline = @{ 'm-cos'='opus'; 'm-cto'='opus'; 'm-cpo'='opus'; 'm-coo'='opus'; 'm-cao'='opus' }

function Get-SeatModelTierEx {
  # CTO 修③（2026-11-28）：返回 @{tier; source}——source∈table|baseline|default。
  #   restart 件期望档 fail-closed 用（source≠table=红·防「基线回落≠查表命中」分叉静默错判）；
  #   launch 两处经 Get-SeatModelTier 包装（fail-open 语义不变）。
  param(
    [Parameter(Mandatory=$true)][string]$SeatName,
    [string]$MapFile
  )
  $tier = 'sonnet'; $source = 'baseline'
  if ($script:SeatModelBaseline.ContainsKey($SeatName)) { $tier = $script:SeatModelBaseline[$SeatName] }
  if (-not $MapFile) { $MapFile = Join-Path $PSScriptRoot 'seat-model-map.psd1' }
  try {
    if (Test-Path $MapFile) {
      $map = Import-PowerShellDataFile -Path $MapFile
      $seats = $map['Seats']
      if ($seats -is [hashtable] -and $seats.ContainsKey($SeatName) -and $seats[$SeatName]) {
        $tier = [string]$seats[$SeatName]; $source = 'table'
      } elseif (-not $script:SeatModelBaseline.ContainsKey($SeatName) -and $map['Default']) {
        $tier = [string]$map['Default']; $source = 'default'
      }
    } else {
      [Console]::Error.WriteLine("[seat-model-tier] 表不可读（缺 $MapFile）·回落基线：$SeatName=$tier")
    }
  } catch {
    [Console]::Error.WriteLine("[seat-model-tier] 表读失败（$($_.Exception.Message)）·回落基线：$SeatName=$tier")
  }
  return @{ tier = $tier; source = $source }
}

function Get-SeatModelTier {
  # 兼容包装（launch 两处用·fail-open）——restart 期望档面请用 Ex 形（fail-closed）。
  param(
    [Parameter(Mandatory=$true)][string]$SeatName,
    [string]$MapFile
  )
  $r = Get-SeatModelTierEx -SeatName $SeatName -MapFile $MapFile
  return $r.tier
}

function Assert-NewArgvModel {
  # ④步断言（CTO 应改③·抽函数可桩测）：新进程 argv 档位对期望=✓/否=红。
  #   nit(a)（CTO 终核 2026-11-27）：失败走 [Console]::Error.WriteLine——Write-Error 在调用方
  #   EAP=Stop 下会越过 return $false 直接终止（退出码靠 EAP 偶然·非设计）。
  param([string]$Seat, [string]$ArgvModel, [string]$ExpectTier)
  if ([string]::IsNullOrWhiteSpace($ArgvModel) -or $ArgvModel -eq '(none)') {
    [Console]::Error.WriteLine("[restart] $Seat 新进程 argv 无 --model——钉档未入 fail-closed"); return $false
  }
  if ($ArgvModel -ne $ExpectTier) {
    [Console]::Error.WriteLine("[restart] $Seat argvModel=$ArgvModel ≠ 期望档=$ExpectTier——钉档失败 fail-closed"); return $false
  }
  Write-Output "[restart] $Seat argvModel=$ArgvModel == 期望档=$ExpectTier ✓"
  return $true
}

function Ensure-SeatEnvToken {
  # ①env 继承根修（CTO 派工 2026-11-28 00:10·标读失效真因=新进程 env 取自父链旧 env 不重读注册表）：
  #   显式从权威源（HKCU 用户注册表·env 同步清单载入位）读 TRILC_INTERNAL_TOKEN 写 $env:——
  #   直读注册表不走进程 env·单一权威源不新增拷贝·须与 daemon 现役值同值（channel.cmd 值源）。
  #   读空/读失败=fail-open 照常起席（不挡席）·stderr+日志行明告「标读将静默失效」。
  #   留证（D-46 零值面）：落一行 .fade\seat-env-sync.log（席位·时刻·envSha8·srcSha8·match）——
  #   restart 件④步消费该行（该席·晚于拉起时刻·match=true；缺失=红）。
  param([Parameter(Mandatory=$true)][string]$SeatName)
  $logLine = $null
  try {
    $src = [Environment]::GetEnvironmentVariable('TRILC_INTERNAL_TOKEN', 'User')
    if ([string]::IsNullOrWhiteSpace($src)) {
      [Console]::Error.WriteLine("[seat-env] 注册表读空——标读将静默失效（fail-open 照常起席）")
      $logLine = "{0} | {1} | srcSha8=EMPTY match=False" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $SeatName
      Add-Content 'D:\Code\ai\TriMetaverse\.fade\seat-env-sync.log' $logLine -Encoding UTF8
      return $false
    }
    $srcSha8 = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($src))) -replace '-', '').Substring(0, 8).ToLower()
    $cur = $env:TRILC_INTERNAL_TOKEN
    $curSha8 = if ($cur) { ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($cur))) -replace '-', '').Substring(0, 8).ToLower() } else { 'EMPTY' }
    $env:TRILC_INTERNAL_TOKEN = $src
    $match = ($curSha8 -eq $srcSha8)
    $logLine = "{0} | {1} | envSha8={2} srcSha8={3} match={4}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $SeatName, $curSha8, $srcSha8, ($match.ToString().ToLower())
    Add-Content 'D:\Code\ai\TriMetaverse\.fade\seat-env-sync.log' $logLine -Encoding UTF8
    if (-not $match) {
      [Console]::Error.WriteLine("[seat-env] $SeatName 进程原 env≠权威源（已重写 $curSha8→$srcSha8）")
    }
    return $true
  } catch {
    [Console]::Error.WriteLine("[seat-env] 读权威源失败（$($_.Exception.Message)）——标读将静默失效（fail-open 照常起席）")
    try {
      Add-Content 'D:\Code\ai\TriMetaverse\.fade\seat-env-sync.log' ("{0} | {1} | read-error match=False" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $SeatName) -Encoding UTF8
    } catch { }
    return $false
  }
}
