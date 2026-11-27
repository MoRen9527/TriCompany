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

function Get-SeatModelTier {
  param(
    [Parameter(Mandatory=$true)][string]$SeatName,
    [string]$MapFile,              # 缺省=$PSScriptRoot\seat-model-map.psd1（调用方 $PSScriptRoot 同目录形）
    [switch]$FailToBaseline        # 缺省行为：表不可读/席缺回落基线+stderr 告警
  )
  $tier = 'sonnet'
  if ($script:SeatModelBaseline.ContainsKey($SeatName)) { $tier = $script:SeatModelBaseline[$SeatName] }
  if (-not $MapFile) { $MapFile = Join-Path $PSScriptRoot 'seat-model-map.psd1' }
  try {
    if (Test-Path $MapFile) {
      $map = Import-PowerShellDataFile -Path $MapFile
      $seats = $map['Seats']
      if ($seats -is [hashtable] -and $seats.ContainsKey($SeatName) -and $seats[$SeatName]) {
        $tier = [string]$seats[$SeatName]
      } elseif (-not $script:SeatModelBaseline.ContainsKey($SeatName) -and $map['Default']) {
        # 表可读+席缺：非基线席走 Default；基线席**保留基线档**（CTO 必改②漏径修——
        #   防「改分工只更基线没更表」时必用席被 Default 静默盖掉降档）
        $tier = [string]$map['Default']
      }
    } else {
      [Console]::Error.WriteLine("[seat-model-tier] 表不可读（缺 $MapFile）·回落基线：$SeatName=$tier")
    }
  } catch {
    [Console]::Error.WriteLine("[seat-model-tier] 表读失败（$($_.Exception.Message)）·回落基线：$SeatName=$tier")
  }
  return $tier
}

function Assert-NewArgvModel {
  # ④步断言（CTO 应改③·抽函数可桩测）：新进程 argv 档位对期望=✓/否=红。
  param([string]$Seat, [string]$ArgvModel, [string]$ExpectTier)
  if ([string]::IsNullOrWhiteSpace($ArgvModel) -or $ArgvModel -eq '(none)') {
    Write-Error "[restart] $Seat 新进程 argv 无 --model——钉档未入 fail-closed"; return $false
  }
  if ($ArgvModel -ne $ExpectTier) {
    Write-Error "[restart] $Seat argvModel=$ArgvModel ≠ 期望档=$ExpectTier——钉档失败 fail-closed"; return $false
  }
  Write-Output "[restart] $Seat argvModel=$ArgvModel == 期望档=$ExpectTier ✓"
  return $true
}
