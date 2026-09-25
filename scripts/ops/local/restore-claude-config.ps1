<#
restore-claude-config.ps1 — Claude Code 配置一键恢复（3333 兜底·LG-041 ③）v2

设计正身: TriMetaverse docs/workflow/operating-records/2026-W39/trees/tri-model-3333-incident/bottleneck-architecture-plan-v2.md §三
修复正身: TASK-INCIDENT-SDE-SETTINGS-01 CTO 复盘报告 §六 修-1..6（2026-09-25）
紧要目标: 3333 挂时，配置恢复一条命令内完成（带外通道：零 3333/daemon/网络依赖，纯本地磁盘文件操作）。

v2 修复记录（2026-09-25，FSD 实施·BOD 裁二授权沙箱单）:
  修-1 空凭据 fail-closed——凭据健康门: PLACEHOLDER/空串/纯空白 三态全拒（事故直因 ②-1）
  修-2 独立钥源注钥序——-InjectKey: keyfile(.deploy-key) > 活体双键探测(AUTH_TOKEN/API_KEY 取非空者)
       +非空断言（空即 Fail 禁注入）+键形同形生成（②-2；CTO 方案原文落 README 一行式，本席实现判断
       升级为脚本模式：一行式嵌套转义脆且不可沙箱测——候验收裁决）
  修-3 干跑/沙箱——[CmdletBinding(SupportsShouldProcess)] 启用 -WhatIf 全路径干跑（键值 diff 零写动作）
       + -TargetDir 沙箱目标参数 + 活体路径醒目警告 + FROZEN-BACKUPS 轮换豁免（②-3/P-3 脚本级前置落法）
  修-4 写后回读断言（凭据键非空+值与预设一致+JSON 合法）+断言失败自动回滚（本次备份拷回）
       + -SmokeTest auth 冒烟（2xx=PASS / 401·403=Fail / 不可达=跳过不阻塞，增强非前置）（②-4）
  修-5 模板单键制（presets/direct.json 单占位符，双键同占位符形废止）+ 注入键形同形生成（②-6）
  修-6 结构化结果行 RESULT/FAIL（op/mode/target/backup/assert/smoke/rotation/ts——「完成即报」可粘贴载体）（②-5）
  事故档案: 同目录 FROZEN-NOTICE-restore-claude-config-20260925.md（冻结笔 TC dev 897b0da，解冻=BOD 验收 revert）
  测试钩子: -SelfTestBreakAssert（强制写后断言失败以验证自动回滚路径；仅沙箱回归用，生产禁用）

用法:
  restore-claude-config.ps1                              # 切 direct（缺省，安全侧默认）——活体路径打印警告
  restore-claude-config.ps1 -Mode relay                  # 切回 3333 中转现役形
  restore-claude-config.ps1 -WhatIf                      # 全路径干跑: 打印将写入的键值 diff（凭据脱敏），零写动作
  restore-claude-config.ps1 -TargetDir <沙箱目录>         # 沙箱目标——测试/锚验证必须用此，禁活体
  restore-claude-config.ps1 -InjectKey                   # 部署日注钥: keyfile > 活体双键探测 → 仓库模板生成部署位预设
  restore-claude-config.ps1 -CaptureRelay                # 部署日一次性: 现役 settings.json env 固化为 relay-3333.json
  restore-claude-config.ps1 -SmokeTest                   # 切换后 auth 冒烟（增强非前置，网络不可达自动跳过）

边界: 不装 cc-switch、不建 proxy、不动 3333/watchdog；只覆写预设 env 子集键，settings.json 其余键值级保留
      （最小侵入，与 TriModel claude-fallback 写形同语义）。
回滚: 写后断言失败自动回滚（本次备份拷回）；手动=取最新 settings.json.bak-* 拷回；或对侧切换（direct↔relay 互为回滚）。
依赖: 仅 PowerShell 5.1 内置能力（Windows 出厂自含）——断网、3333 挂、watchdog 死场景均可运行。
#>
[CmdletBinding(SupportsShouldProcess)]
param(
  [ValidateSet('direct','relay')]
  [string]$Mode = 'direct',
  [switch]$CaptureRelay,
  [switch]$InjectKey,
  [switch]$SmokeTest,
  [string]$TargetDir = (Join-Path $HOME '.claude'),
  [switch]$SelfTestBreakAssert
)

$ErrorActionPreference = 'Stop'

$claudeDir      = $TargetDir
$settingsPath   = Join-Path $claudeDir 'settings.json'
$presetsDir     = Join-Path $claudeDir 'settings.presets'
$bundledDir     = Join-Path $PSScriptRoot 'presets'
$keepBackups    = 5
$credentialKeys = @('ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY')

# ── 修-3: 活体路径识别与醒目警告（沙箱纪律前置提示）──
$liveNorm   = ([System.IO.Path]::GetFullPath((Join-Path $HOME '.claude'))).TrimEnd('\','/')
$targetNorm = ([System.IO.Path]::GetFullPath($claudeDir)).TrimEnd('\','/')
if ([string]::Equals($liveNorm, $targetNorm, [StringComparison]::OrdinalIgnoreCase)) {
  Write-Host "[restore-claude-config] ⚠ 警告：目标=活体路径（$settingsPath）。本次运行为真环境写入；测试/锚验证请加 -TargetDir <沙箱目录>（2026-09-25 事故教训）。" -ForegroundColor Yellow
}

function Fail([int]$code, [string]$msg) {
  Write-Host "[restore-claude-config] 失败：$msg" -ForegroundColor Red
  # 修-6: 失败路径同样出结构化行（| 防断裂转义）
  $safeMsg = $msg -replace '\|', '/'
  Write-Output ("FAIL | code={0} | msg={1} | ts={2}" -f $code, $safeMsg, (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'))
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

function Format-ValueForLog([string]$key, $value) {
  # 日志/干跑 diff 值脱敏：凭据键只出长度，钥值全程不经输出（README 密钥卫生红线）
  if ($null -eq $value) { return '<absent>' }
  $s = [string]$value
  if (($key -match 'TOKEN') -or ($key -match 'KEY')) {
    if ([string]::IsNullOrWhiteSpace($s)) { return '<empty>' }
    return ("len={0}" -f $s.Length)
  }
  return $s
}

# ── 模式互斥（混沌拒绝）──
if ($CaptureRelay -and $InjectKey) { Fail 2 "-CaptureRelay 与 -InjectKey 互斥，单次单模式" }

# ═══ CaptureRelay：现役 env 形固化（部署日 3333 健康时执行一次；跟随 -TargetDir）═══
if ($CaptureRelay) {
  if (-not (Test-Path $settingsPath)) { Fail 2 "未找到现役 $settingsPath ，无法固化 relay 形" }
  try { $cur = Read-JsonFile $settingsPath } catch { Fail 2 "现役 settings.json 非法 JSON，拒固化：$_" }
  $curEnv = Get-EnvProp $cur 'env'
  if (-not $curEnv) { Fail 2 "现役 settings.json 无 env 块，无法固化" }
  $snap = [pscustomobject]@{ env = $curEnv }
  $capOut = Join-Path $presetsDir 'relay-3333.json'
  if (-not $PSCmdlet.ShouldProcess($capOut, "固化现役 env 形为 relay-3333.json")) {
    Write-Output "[WhatIf] CaptureRelay 干跑完成，零写动作。目标=$capOut"
    exit 0
  }
  Ensure-Dir $presetsDir
  Write-Utf8NoBom $capOut ($snap | ConvertTo-Json -Depth 20)
  Write-Output "已固化现役 env 形 → $capOut"
  Write-Output ("RESULT | op=capture-relay | target={0} | ts={1}" -f $capOut, (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'))
  exit 0
}

# ═══ InjectKey：独立钥源注钥（修-2；修-5 键形同形生成；跟随 -TargetDir）═══
if ($InjectKey) {
  # 钥源优先级: ①独立 keyfile（$presetsDir\.deploy-key，部署日 BOD/CEO 供钥落位）
  #             ②活体现役 fallback（$settingsPath 双键探测: AUTH_TOKEN/API_KEY 取非空者）
  # 键形策略(修-5): 以活体非空键名同形生成预设（活体 known-good 键形=权威形）;
  #                活体双键全空（灾备态）时缺省 ANTHROPIC_AUTH_TOKEN 并在结果行标注 keyshape=default。
  Ensure-Dir $presetsDir
  $bundledTpl = Join-Path $bundledDir "$Mode.json"
  if (-not (Test-Path $bundledTpl)) { Fail 2 "仓库模板不存在：$bundledTpl" }
  try { $tpl = Read-JsonFile $bundledTpl } catch { Fail 2 "仓库模板非法 JSON：$bundledTpl" }
  $tplEnv = Get-EnvProp $tpl 'env'
  if (-not $tplEnv) { Fail 2 "仓库模板缺 env 块：$bundledTpl" }

  # 键形探测（独立于钥源）：活体首非空凭据键名
  $keyShape = 'ANTHROPIC_AUTH_TOKEN'
  $liveKeyValues = @{}
  if (Test-Path $settingsPath) {
    try { $live = Read-JsonFile $settingsPath } catch { Fail 2 "活体 settings.json 非法 JSON，注钥拒读：$_" }
    $liveEnv = Get-EnvProp $live 'env'
    if ($liveEnv) {
      foreach ($key in $credentialKeys) {
        $lv = Get-EnvProp $liveEnv $key
        $liveKeyValues[$key] = [string]$lv
        if (($keyShape -eq 'ANTHROPIC_AUTH_TOKEN') -and ($key -eq 'ANTHROPIC_API_KEY') -and (-not [string]::IsNullOrWhiteSpace([string]$lv)) -and [string]::IsNullOrWhiteSpace($liveKeyValues['ANTHROPIC_AUTH_TOKEN'])) {
          $keyShape = 'ANTHROPIC_API_KEY'
        }
      }
    }
  }

  # 钥源：keyfile 优先，活体双键 fallback
  $k = $null; $kSource = ''
  $keyfile = Join-Path $presetsDir '.deploy-key'
  if (Test-Path $keyfile) {
    $k = ((Get-Content $keyfile -Raw) -replace "`r", '').Trim()
    $kSource = "keyfile:$keyfile"
  }
  if ([string]::IsNullOrWhiteSpace($k)) {
    foreach ($key in $credentialKeys) {
      if (-not [string]::IsNullOrWhiteSpace($liveKeyValues[$key])) {
        $k = $liveKeyValues[$key]
        $kSource = "live:$settingsPath#$key"
        break
      }
    }
  }
  if ([string]::IsNullOrWhiteSpace($k)) {
    Fail 2 ("注钥 fail-closed: 钥源全空（keyfile 缺位且活体双键 {0} 均无非空值）——空钥禁注入（事故 2026-09-25 ②-2）" -f ($credentialKeys -join '/'))
  }

  # 生成部署位预设: 模板单键形改造（AUTH_TOKEN→keyShape 同形）+占位符→真钥（仅内存，写前断言）
  $outEnv = [pscustomobject]@{}
  foreach ($prop in $tplEnv.PSObject.Properties) {
    $outKey = $prop.Name
    if (($outKey -eq 'ANTHROPIC_AUTH_TOKEN') -and ($keyShape -eq 'ANTHROPIC_API_KEY')) { $outKey = 'ANTHROPIC_API_KEY' }
    Set-EnvProp $outEnv $outKey ([string]$prop.Value)
  }
  foreach ($prop in $outEnv.PSObject.Properties) {
    if (($prop.Value -is [string]) -and ($prop.Value -match 'PLACEHOLDER')) { Set-EnvProp $outEnv $prop.Name $k }
  }

  # 注入自断言（写盘前，内存面）：凭据键非空+无占位符残留
  $injAssert = $true; $injWhy = @()
  $credVal = [string](Get-EnvProp $outEnv $keyShape)
  if ([string]::IsNullOrWhiteSpace($credVal)) { $injAssert = $false; $injWhy += "凭据键 $keyShape 为空" }
  foreach ($prop in $outEnv.PSObject.Properties) {
    if (($prop.Value -is [string]) -and ($prop.Value -match 'PLACEHOLDER')) { $injAssert = $false; $injWhy += "占位符残留 $($prop.Name)" }
  }
  if (-not $injAssert) { Fail 2 "注钥自断言失败（未写盘）: $($injWhy -join '; ')" }

  $outDoc  = [pscustomobject]@{ env = $outEnv }
  $outPath = Join-Path $presetsDir "$Mode.json"
  if (-not $PSCmdlet.ShouldProcess($outPath, "写入注入预设（keyshape=$keyShape, keysrc=$kSource, keylen=$($k.Length)）")) {
    Write-Output "[WhatIf] 注钥干跑完成，零写动作。目标=$outPath 键形=$keyShape"
    exit 0
  }
  Write-Utf8NoBom $outPath ($outDoc | ConvertTo-Json -Depth 20)

  # 写后回读复断言（值面）
  try { $chk = Read-JsonFile $outPath } catch { Fail 1 "注钥写后回读 JSON 非法：$_" }
  $chkEnv = Get-EnvProp $chk 'env'
  $chkV = [string](Get-EnvProp $chkEnv $keyShape)
  if ([string]::IsNullOrWhiteSpace($chkV) -or ($chkV -ne $k)) { Fail 1 "注钥写后回读断言失败（值面不符）" }

  Write-Output "已注入（钥源=$kSource 键形=$keyShape 钥长=$($k.Length)）→ $outPath"
  Write-Output ("RESULT | op=inject-key | mode={0} | target={1} | keyshape={2} | assert=pass | ts={3}" -f $Mode, $outPath, $keyShape, (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'))
  exit 0
}

# ═══ 主切换流程 ═══

# ── 预设定位：~<target>/settings.presets 优先，缺位回退脚本同目录 presets\ 补装 ──
$presetName = "$Mode.json"
$presetPath = Join-Path $presetsDir $presetName
$bundled    = Join-Path $bundledDir $presetName
$effectivePresetPath = $presetPath
$presetNeedsInstall  = $false
if (-not (Test-Path $presetPath)) {
  if (Test-Path $bundled) {
    $effectivePresetPath = $bundled
    $presetNeedsInstall  = $true
  } else {
    Fail 2 "预设不存在：$presetPath （relay 形请先在 3333 健康日执行 -CaptureRelay 固化；direct 形可先 -InjectKey 注钥生成）"
  }
}

# ── 预设合法性与 env 块校验（fail-closed，禁半写）──
try { $preset = Read-JsonFile $effectivePresetPath } catch { Fail 2 "预设非法 JSON：$effectivePresetPath" }
$presetEnv = Get-EnvProp $preset 'env'
if (-not $presetEnv) { Fail 2 "预设缺 env 块：$effectivePresetPath" }

# ── 修-1: 凭据健康门（fail-closed）——PLACEHOLDER/空串/纯空白 三态全拒 ──
# 事故教训(②-1): -replace 空串穿透占位符防呆 → 空钥覆写活体。占位符防呆(全键扫描)与
# 凭据族值面校验(AUTH_TOKEN/API_KEY IsNullOrWhiteSpace)合并为单层健康门。
foreach ($prop in $presetEnv.PSObject.Properties) {
  if (($prop.Value -is [string]) -and ($prop.Value -match 'PLACEHOLDER')) {
    Fail 2 "凭据健康门: 预设含占位符凭据（真钥未注入），拒切：$effectivePresetPath —— 请先 -InjectKey 完成钥注入"
  }
}
foreach ($key in $credentialKeys) {
  $cv = Get-EnvProp $presetEnv $key
  if (($null -ne $cv) -and [string]::IsNullOrWhiteSpace([string]$cv)) {
    Fail 2 ("凭据健康门: 预设凭据键 {0} 为空/纯空白（空凭据 fail-closed，2026-09-25 事故 ②-1 同形拦截），拒切：{1}" -f $key, $effectivePresetPath)
  }
}

# ── 修-3: 主 ShouldProcess 门（-WhatIf 全路径干跑：键值 diff 零写动作）──
if (-not $PSCmdlet.ShouldProcess($settingsPath, "备份+env 子集覆写（mode=$Mode, preset=$effectivePresetPath$(if ($presetNeedsInstall) { ', 补装预设' })）")) {
  $curDoc = $null
  if (Test-Path $settingsPath) {
    try { $curDoc = Read-JsonFile $settingsPath } catch { $curDoc = $null }
  }
  $curEnv = if ($curDoc) { Get-EnvProp $curDoc 'env' } else { $null }
  Write-Output "── WhatIf 干跑 diff（目标 $settingsPath，mode=$Mode）──"
  foreach ($prop in $presetEnv.PSObject.Properties) {
    $cur = Get-EnvProp $curEnv $prop.Name
    $newV = Format-ValueForLog $prop.Name $prop.Value
    if ($null -eq $cur) { Write-Output ("  + {0} = {1}（新增）" -f $prop.Name, $newV) }
    elseif ([string]$cur -ne [string]$prop.Value) { Write-Output ("  ~ {0}: {1} → {2}" -f $prop.Name, (Format-ValueForLog $prop.Name $cur), $newV) }
    else { Write-Output ("  = {0} 不变（{1}）" -f $prop.Name, $newV) }
  }
  Write-Output "[WhatIf] 干跑完成，零写动作。"
  exit 0
}

# ── 目录就位（真写路径才建）──
Ensure-Dir $claudeDir
Ensure-Dir $presetsDir
if ($presetNeedsInstall) {
  Copy-Item $bundled $presetPath
  Write-Output "预设缺位，已从真源化域补装：$presetPath"
}

# ── 备份（存在才备份；同目录 .bak-<ts>；轮换保留近 5 份；FROZEN-BACKUPS 哨兵豁免）──
$backupNote = '无（原 settings.json 不存在，视为新建）'
$rotationNote = 'n/a'
if (Test-Path $settingsPath) {
  $tsFmt = Get-Date -Format 'yyyyMMdd-HHmmss'
  $bak = "$settingsPath.bak-$tsFmt"
  Copy-Item $settingsPath $bak
  $backupNote = $bak
  $frozenBackups = Join-Path $claudeDir 'FROZEN-BACKUPS'
  if (Test-Path $frozenBackups) {
    # 修-3/P-3: 轮换豁免——事故嫌疑时段备份自动冻结（防回滚锚自毁，2026-09-25 ②-3 教训）
    $rotationNote = '轮换跳过（FROZEN-BACKUPS 哨兵在位）'
  } else {
    $oldBaks = @(Get-ChildItem -Path $claudeDir -Filter 'settings.json.bak-*' -File | Sort-Object Name -Descending)
    if ($oldBaks.Count -gt $keepBackups) {
      $oldBaks | Select-Object -Skip $keepBackups | Remove-Item -Force
    }
    $rotationNote = "轮换执行（保留近 $keepBackups 份）"
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

# ── 修-4: 写后回读断言（JSON 合法+值与预设一致+凭据键非空）——失败自动回滚并 Fail ──
$assertOk = $true; $assertWhy = @()
try {
  $post = Read-JsonFile $settingsPath
  $postEnv = Get-EnvProp $post 'env'
  if (-not $postEnv) { $assertOk = $false; $assertWhy += '写后 env 块缺失' }
  else {
    foreach ($prop in $presetEnv.PSObject.Properties) {
      $pv = [string](Get-EnvProp $postEnv $prop.Name)
      if ($pv -ne [string]$prop.Value) { $assertOk = $false; $assertWhy += ("键 {0} 写后值与预设不符" -f $prop.Name) }
    }
    foreach ($key in $credentialKeys) {
      $cv = Get-EnvProp $postEnv $key
      if (($null -ne $cv) -and [string]::IsNullOrWhiteSpace([string]$cv)) { $assertOk = $false; $assertWhy += ("凭据键 {0} 写后为空" -f $key) }
    }
  }
} catch {
  $assertOk = $false; $assertWhy += "写后回读异常: $($_.Exception.Message)"
}
if ($SelfTestBreakAssert) { $assertOk = $false; $assertWhy += 'selftest 注入断言失败（-SelfTestBreakAssert，仅沙箱回归用）' }
if (-not $assertOk) {
  $rb = '无备份可回滚'
  if (($backupNote -ne '无（原 settings.json 不存在，视为新建）') -and (Test-Path $backupNote)) {
    Copy-Item $backupNote $settingsPath -Force
    $rb = "已自动回滚自 $backupNote"
  } elseif (Test-Path $settingsPath) {
    Remove-Item $settingsPath -Force
    $rb = '新建态回滚（删除半成品）'
  }
  Fail 1 "写后断言失败（$rb）：$($assertWhy -join '; ')"
}

# ── 修-4: -SmokeTest auth 冒烟（增强非前置；2xx=PASS / 401·403=Fail / 不可达=跳过不阻塞）──
$smokeNote = '未启用'
if ($SmokeTest) {
  $baseUrl = [string](Get-EnvProp $postEnv 'ANTHROPIC_BASE_URL')
  $smokeToken = $null
  foreach ($key in $credentialKeys) {
    $tv = [string](Get-EnvProp $postEnv $key)
    if (-not [string]::IsNullOrWhiteSpace($tv)) { $smokeToken = $tv; break }
  }
  if (-not $baseUrl) { $smokeNote = '跳过（写后 env 无 ANTHROPIC_BASE_URL）' }
  elseif (-not $smokeToken) { $smokeNote = '跳过（写后 env 无非空凭据键）' }
  else {
    $uri = ($baseUrl.TrimEnd('/')) + '/v1/models'
    try {
      $resp = Invoke-WebRequest -Uri $uri -Method GET -TimeoutSec 5 -UseBasicParsing -Headers @{ 'x-api-key' = $smokeToken; 'Authorization' = "Bearer $smokeToken" } -ErrorAction Stop
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { $smokeNote = "PASS（HTTP $($resp.StatusCode)）" }
      else { $smokeNote = "WARN（HTTP $($resp.StatusCode) 语义未定，不阻塞）" }
    } catch {
      $r = $null
      try { $r = $_.Exception.Response } catch { $r = $null }
      if ($null -ne $r) {
        $sc = [int]$r.StatusCode
        if ($sc -eq 401 -or $sc -eq 403) {
          Fail 1 "auth 冒烟 FAIL（HTTP $sc 凭据被拒）——切换已写入但 auth 不通，请核查钥值/键形；回滚=取最新 settings.json.bak-* 拷回"
        } else { $smokeNote = "跳过（端点 HTTP $sc，非 401/403 不阻塞）" }
      } else { $smokeNote = "跳过（网络不可达: $($_.Exception.Message)）——不阻塞" }
    }
  }
}

# ── 修-6: 结构化结果行（完成即报可粘贴载体）──
Write-Output ("已切换至 {0}，备份于 {1}" -f $Mode, $backupNote)
Write-Output ("RESULT | op=switch | mode={0} | target={1} | backup={2} | assert=pass | smoke={3} | rotation={4} | ts={5}" -f $Mode, $settingsPath, $backupNote, $smokeNote, $rotationNote, (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'))
exit 0
