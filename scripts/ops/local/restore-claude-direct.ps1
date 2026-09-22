# restore-claude-direct.ps1 — L1 独立恢复脚本（不经 3333，直写 settings.json env 子集）
# 真源位：TriCompany/scripts/ops/local/（脚本真源化命题域）；部署位=任意机器可跑
# 场景：TriModel 3333 挂时恢复 Claude 直连（known-good 模板回拷或三值手填）
# 用法：powershell -File restore-claude-direct.ps1            # 模板回拷（known-good）
#       powershell -File restore-claude-direct.ps1 -BaseUrl <url> -Token <tk> -Model <m>  # 三值手填
param(
  [string]$BaseUrl,
  [string]$Token,
  [string]$Model,
  [switch]$UseKnownGood
)
$settings = Join-Path $env:USERPROFILE '.claude\settings.json'
$knownGood = Join-Path $env:USERPROFILE '.claude\settings.json.known-good'

if ($UseKnownGood -or (-not $BaseUrl)) {
  if (-not (Test-Path $knownGood)) { Write-Error 'known-good 模板不存在（~/.claude/settings.json.known-good）'; exit 1 }
  Copy-Item $knownGood $settings -Force
  Write-Output '已从 known-good 模板恢复 settings.json。重启 Claude 会话后生效。'
  exit 0
}
# 三值手填路径：先读 known-good 做基底（保底其余字段），覆写三值
if (-not (Test-Path $knownGood)) { Write-Error 'known-good 模板不存在，三值手填需先建模板'; exit 1 }
$doc = Get-Content $knownGood -Raw | ConvertFrom-Json
$doc.env.ANTHROPIC_BASE_URL = $BaseUrl
$doc.env.ANTHROPIC_AUTH_TOKEN = $Token
if ($Model) { $doc.env.ANTHROPIC_MODEL = $Model }
$doc | ConvertTo-Json -Depth 10 | Set-Content $settings -Encoding UTF8
Write-Output "已写直连配置（$BaseUrl）。重启 Claude 会话后生效。"
