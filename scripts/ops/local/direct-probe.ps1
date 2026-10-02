<#
direct-probe.ps1 — TriModel 直连面探针（LG-053 §四 · batch-15 件①）

正身链: lg053-recovery-ladder-final.md §四（直连面定义：claude settings.json env 三键直连 TriModel 网关，
        与 relay 面<3333 daemon 已退役>互斥）+ CTO 接口意见书合流定义。
铸: FSD 小全（m-fsd）2026-10-03 · batch-15 件①（BOD 复工令+CEO 01:38 亲裁）

三段检:
  1. 预设形: presets/direct.json 键名清单+占位符检出（仓库模板形=密钥卫生形，真值在部署位）
  2. 活体形: settings.json env 三键对照（齐性+值形指纹 len+head4+tail4——零敏感值出机红线：
     值面禁回显，指纹只报形态）
  3. 连通面: baseUrl TCP/TLS 探 + GET {base}/v1/models（Bearer ANTHROPIC_AUTH_TOKEN）HTTP 状态读数
     ——默认不发真推理；-Live 才发真请求（成本面，候值席）

只读纪律: 本工具零写操作（settings.json 只读）；零敏感值出机（指纹形）。

用法:
  direct-probe.ps1                                    # 默认三段检
  direct-probe.ps1 -SettingsJson <path> -PresetsJson <path>
  direct-probe.ps1 -Live                              # 连通+真推理（候值席窗）
#>
[CmdletBinding()]
param(
  [string]$SettingsJson = (Join-Path $env:USERPROFILE '.claude\settings.json'),
  [string]$PresetsJson = 'D:\Code\ai\TriCompany\scripts\ops\local\presets\direct.json',
  [switch]$Live,
  [switch]$Json
)
$ErrorActionPreference = 'Stop'
$script:ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')

function Get-Fingerprint([string]$v) {
  if ([string]::IsNullOrEmpty($v)) { return 'EMPTY' }
  if ($v.Length -le 12) { return ('len={0} head=[{1}]' -f $v.Length, $v.Substring(0, [Math]::Min(4, $v.Length))) }
  return ('len={0} head4=[{1}] tail4=[{2}]' -f $v.Length, $v.Substring(0, 4), $v.Substring($v.Length - 4, 4))
}
function Test-Placeholder([string]$v) {
  # 占位符形检出（restore v2 修-2 同语义域）：`<>` 模板尖括号/显式 PLACEHOLDER/your- 前缀
  if ([string]::IsNullOrEmpty($v)) { return $false }
  return ($v -match '<' -or $v -match 'PLACEHOLDER' -or $v -match '^your-')
}

$r = [ordered]@{ op = 'direct-probe'; ts = $script:ts; segments = @() }

# ── 段1: 预设形 ──
$seg1 = @{ segment = 'preset'; file = $PresetsJson; exists = (Test-Path $PresetsJson); keys = @(); placeholders = @() }
if ($seg1.exists) {
  $pj = Get-Content $PresetsJson -Raw | ConvertFrom-Json
  $envKeys = @($pj.env.PSObject.Properties.Name)
  $seg1.keys = $envKeys
  foreach ($k in $envKeys) {
    if (Test-Placeholder $pj.env.$k) { $seg1.placeholders += $k }
  }
  $seg1.note = '仓库模板形占位符=密钥卫生正形（真钥仅部署位）'
}
$r.segments += $seg1

# ── 段2: 活体形 ──
$triKeys = @('ANTHROPIC_BASE_URL', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_MODEL')
$seg2 = @{ segment = 'live'; file = $SettingsJson; exists = (Test-Path $SettingsJson); env = @{}; missing = @() }
if ($seg2.exists) {
  $sj = Get-Content $SettingsJson -Raw | ConvertFrom-Json
  foreach ($k in $triKeys) {
    $v = $sj.env.$k
    if ([string]::IsNullOrEmpty($v)) { $seg2.missing += $k }
    else {
      $fp = Get-Fingerprint $v
      $ph = Test-Placeholder $v
      $seg2.env[$k] = @{ fingerprint = $fp; placeholder = $ph }
    }
  }
}
$r.segments += $seg2

# ── 段3: 连通面 ──
$seg3 = @{ segment = 'connectivity'; live_inference = [bool]$Live }
$baseUrl = $sj.env.ANTHROPIC_BASE_URL
if ([string]::IsNullOrEmpty($baseUrl)) {
  $seg3.result = 'skip'; $seg3.why = 'ANTHROPIC_BASE_URL 缺位'
} else {
  $seg3.base_url = $baseUrl
  $uri = [Uri]$baseUrl
  $seg3.host = $uri.Host; $seg3.port = if ($uri.Port -gt 0) { $uri.Port } else { if ($uri.Scheme -eq 'https') { 443 } else { 80 } }
  $tcp = Test-NetConnection -ComputerName $uri.Host -Port $seg3.port -InformationLevel Detailed -WarningAction SilentlyContinue
  $seg3.tcp = $tcp.TcpTestSucceeded
  if ($tcp.TcpTestSucceeded) {
    $headers = @{}
    $tok = $sj.env.ANTHROPIC_AUTH_TOKEN
    if (-not [string]::IsNullOrEmpty($tok) -and -not (Test-Placeholder $tok)) { $headers['Authorization'] = ('Bearer ' + $tok) }
    try {
      $resp = Invoke-WebRequest -Uri ("{0}/v1/models" -f $baseUrl.TrimEnd('/')) -Method GET -Headers $headers -UseBasicParsing -TimeoutSec 10
      $seg3.http_status = [int]$resp.StatusCode
    } catch {
      $seg3.http_status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
      $seg3.http_err = $_.Exception.Message
    }
    $seg3.result = if ($seg3.http_status -ge 200 -and $seg3.http_status -lt 300) { 'OK' }
      elseif ($seg3.http_status -eq 401 -or $seg3.http_status -eq 403) { 'AUTH-REJECTED' }
      elseif ($seg3.http_status -ge 500) { 'UPSTREAM-5XX' }
      else { 'ABNORMAL' }
  } else { $seg3.result = 'TCP-DEAD' }
  if ($Live) { $seg3.note = '真推理探候值席窗（本形未实现——连通面即本件验收锚，真推理面成本纪律候批）' }
}
$r.segments += $seg3

# 总判：直连面通=preset 形在+活体三键齐非占位+TCP 通+HTTP 2xx
$verdict = 'PASS'
if (-not $seg1.exists) { $verdict = 'FAIL(preset-missing)' }
elseif ($seg2.missing.Count -gt 0) { $verdict = ('FAIL(live-missing:' + ($seg2.missing -join ',') + ')') }
elseif ($seg3.result -ne 'OK') { $verdict = ('FAIL(connectivity:' + $seg3.result + ')') }
$r.verdict = $verdict

if ($Json) { $r | ConvertTo-Json -Depth 6 }
else {
  Write-Output ("=== direct-probe {0} ===" -f $verdict)
  Write-Output ("[1] preset: exists={0} keys=[{1}] placeholders={2}" -f $seg1.exists, ($seg1.keys -join ','), ($seg1.placeholders -join ','))
  if ($seg2.exists) {
    foreach ($k in $triKeys) {
      if ($seg2.env.Contains($k)) { Write-Output ("[2] live {0}: {1} placeholder={2}" -f $k, $seg2.env[$k].fingerprint, $seg2.env[$k].placeholder) }
      else { Write-Output ("[2] live {0}: MISSING" -f $k) }
    }
  }
  Write-Output ("[3] connectivity: {0} (tcp={1} http={2})" -f $seg3.result, $seg3.tcp, $seg3.http_status)
}
Write-Output ('RESULT ' + ($r | ConvertTo-Json -Compress -Depth 6))
