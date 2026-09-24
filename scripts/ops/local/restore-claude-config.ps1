<#
restore-claude-config.ps1 — Claude Code 配置一键恢复（3333 兜底·LG-041 ③）

设计正身: TriMetaverse docs/workflow/operating-records/2026-W39/trees/tri-model-3333-incident/bottleneck-architecture-plan-v2.md §三
紧要目标: 3333 挂时，配置恢复一条命令内完成（带外通道：零 3333/daemon/网络依赖，纯本地磁盘文件操作）。

用法:
  restore-claude-config.ps1                 # 切 direct（缺省，安全侧默认）
  restore-claude-config.ps1 -Mode relay     # 切回 3333 中转现役形
  restore-claude-config.ps1 -CaptureRelay   # 部署日一次性：把现役 settings.json env 固化为 relay-3333.json

行为: 备份现 settings.json（.bak-<ts>，轮换保留近 5 份）→ 预设 env 子集原子覆写（temp+rename）→ 输出结果行。
边界: 不装 cc-switch、不建 proxy、不动 3333/watchdog；只覆写预设 env 子集键，settings.json 其余键值级保留（最小侵入；
      与 TriModel claude-fallback 写形同语义）。切换思想模型=预设拷贝二选一，落地取子集覆写以防误伤非 env 面。
回滚: 取最新 settings.json.bak-* 拷回 settings.json；或再跑一次对侧切换（direct↔relay 互为回滚）。
依赖: 仅 PowerShell 5.1 内置能力（Windows 出厂自含）——断网、3333 挂、watchdog 死场景均可运行。
#>
param(
  [ValidateSet('direct','relay')]
  [string]$Mode = 'direct',
  [switch]$CaptureRelay
)

$ErrorActionPreference = 'Stop'

$claudeDir    = Join-Path $HOME '.claude'
$settingsPath = Join-Path $claudeDir 'settings.json'
$presetsDir   = Join-Path $claudeDir 'settings.presets'
$bundledDir   = Join-Path $PSScriptRoot 'presets'
$keepBackups  = 5

function Fail([int]$code, [string]$msg) {
  Write-Host "[restore-claude-config] 失败：$msg" -ForegroundColor Red
  exit $code
}

function Ensure-Dir([string]$p) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

function Read-JsonFile([string]$path) {
  # 统一读取+解析；解析失败抛错由调用方 fail-closed
  return Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Get-EnvProp($obj, [string]$name) {
  $prop = $obj.PSObject.Properties[$name]
  if ($prop) { return $prop.Value } else { return $null }
}

function Set-EnvProp($envObj, [string]$name, $value) {
  if ($envObj.PSObject.Properties[$name]) { $envObj.$name = $value }
  else { $envObj | Add-Member -MemberType NoteProperty -Name $name -Value $value }
}

function Write-Utf8NoBom([string]$path, [string]$text) {
  $tmp = "$path.tmp-$PID"
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($tmp, $text, $enc)
  Move-Item -Force $tmp $path
}

Ensure-Dir $claudeDir
Ensure-Dir $presetsDir

# ── CaptureRelay：现役 env 形固化（部署日 3333 健康时执行一次；cc-switch「首启收编」思想吸收）──
if ($CaptureRelay) {
  if (-not (Test-Path $settingsPath)) { Fail 2 "未找到现役 $settingsPath ，无法固化 relay 形" }
  try { $cur = Read-JsonFile $settingsPath } catch { Fail 2 "现役 settings.json 非法 JSON，拒固化：$_" }
  $curEnv = Get-EnvProp $cur 'env'
  if (-not $curEnv) { Fail 2 "现役 settings.json 无 env 块，无法固化" }
  $snap = [pscustomobject]@{ env = $curEnv }
  Write-Utf8NoBom (Join-Path $presetsDir 'relay-3333.json') ($snap | ConvertTo-Json -Depth 20)
  Write-Output "已固化现役 env 形 → $(Join-Path $presetsDir 'relay-3333.json')"
  exit 0
}

# ── 预设定位：~/.claude/settings.presets 优先，缺位回退脚本同目录 presets\ 补装 ──
$presetName = "$Mode.json"
$presetPath = Join-Path $presetsDir $presetName
if (-not (Test-Path $presetPath)) {
  $bundled = Join-Path $bundledDir $presetName
  if (Test-Path $bundled) {
    Copy-Item $bundled $presetPath
    Write-Output "预设缺位，已从真源化域补装：$presetPath"
  }
}
if (-not (Test-Path $presetPath)) {
  Fail 2 "预设不存在：$presetPath （relay 形请先在 3333 健康日执行 -CaptureRelay 固化）"
}

# ── 预设合法性与 env 块校验（fail-closed，禁半写）──
try { $preset = Read-JsonFile $presetPath } catch { Fail 2 "预设非法 JSON：$presetPath" }
$presetEnv = Get-EnvProp $preset 'env'
if (-not $presetEnv) { Fail 2 "预设缺 env 块：$presetPath" }

# ── 占位符凭据防呆（密钥卫生红线：真钥预设永不入 git）──
# 仓库侧预设以 *_PLACEHOLDER__DEPLOY_INJECT 形在位；未注入真钥前拒切，
# 防止占位符被写进现役 settings.json 造成「切了但起不来」的静默故障。
foreach ($prop in $presetEnv.PSObject.Properties) {
  if (($prop.Value -is [string]) -and ($prop.Value -match 'PLACEHOLDER')) {
    Fail 2 "预设含占位符凭据（真钥未注入），拒切：$presetPath —— 请先按 README 完成部署日语钥注入"
  }
}

# ── 备份（存在才备份；同目录 .bak-<ts>；轮换保留近 5 份）──
$backupNote = '无（原 settings.json 不存在，视为新建）'
if (Test-Path $settingsPath) {
  $ts  = Get-Date -Format 'yyyyMMdd-HHmmss'
  $bak = "$settingsPath.bak-$ts"
  Copy-Item $settingsPath $bak
  $backupNote = $bak
  $oldBaks = @(Get-ChildItem -Path $claudeDir -Filter 'settings.json.bak-*' -File | Sort-Object Name -Descending)
  if ($oldBaks.Count -gt $keepBackups) {
    $oldBaks | Select-Object -Skip $keepBackups | Remove-Item -Force
  }
}

# ── env 子集覆写（settings.json 其余键值级保留）+ 原子写（temp+rename）──
if (Test-Path $settingsPath) {
  try { $doc = Read-JsonFile $settingsPath } catch { Fail 1 "现役 settings.json 非法 JSON，拒改（请先从 settings.json.bak-* 排查恢复）：$_" }
} else {
  $doc = [pscustomobject]@{}
}
$docEnv = Get-EnvProp $doc 'env'
if (-not $docEnv) {
  if ($doc.PSObject.Properties['env']) {
    # env 键在但为空值（null）——重建空 env 块防写坏
    $doc.env = [pscustomobject]@{}
  } else {
    $doc | Add-Member -MemberType NoteProperty -Name env -Value ([pscustomobject]@{})
  }
  $docEnv = Get-EnvProp $doc 'env'
}
foreach ($prop in $presetEnv.PSObject.Properties) {
  Set-EnvProp $docEnv $prop.Name $prop.Value
}
Write-Utf8NoBom $settingsPath ($doc | ConvertTo-Json -Depth 20)

Write-Output ("已切换至 {0}，备份于 {1}" -f $Mode, $backupNote)
exit 0
