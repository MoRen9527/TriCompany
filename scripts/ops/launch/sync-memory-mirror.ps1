# sync-memory-mirror.ps1 — 项目记忆自动镜像回 TriMetaverse 仓（CEO 2026-10-06 20:27 令）
# 源=Claude 项目记忆（harness 自动加载）；目标=TMV docs/memory（随仓镜像，随 git 不丢失）
# 规则：只增改不删（删除面人工）；源缩量判卫；有变化且 staged 面干净时机器 commit
# 拉起：run-sync-memory-mirror.vbs 无窗包装（D-29），schtasks Sync-Memory-Mirror 每小时+登录时
$ErrorActionPreference = 'Stop'
$src = Join-Path $env:USERPROFILE '.claude\projects\D--Code-ai-TriMetaverse\memory'
$dst = 'D:\Code\ai\TriMetaverse\docs\memory'
$log = 'D:\Code\ai\TriCompany\scripts\ops\launch\memory-mirror-sync.log'  # log 禁放镜像目录（防误收 commit）
if (-not (Test-Path $src)) { exit 1 }
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$srcFiles = Get-ChildItem $src -Filter *.md -File
$before = @(Get-ChildItem $dst -Filter *.md -File).Count
foreach ($f in $srcFiles) { Copy-Item $f.FullName $dst -Force }
$after = @(Get-ChildItem $dst -Filter *.md -File).Count
if ($after -lt $before) {
  Add-Content -Path $log -Value "$(Get-Date -Format s) WARN mirror count dropped $before->$after, kept (deletion needs manual review)"
  exit 0
}
Push-Location 'D:\Code\ai\TriMetaverse'
try {
  $staged = @(git diff --cached --name-only)
  if ($staged.Count -gt 0) { exit 0 }  # 并行 staged 在途，跳过本轮 commit 只留文件
  $changed = @(git status --porcelain -- docs/memory)
  if ($changed.Count -gt 0) {
    git add docs/memory
    git commit -m 'docs(memory): 项目记忆镜像同步（自动·sync-memory-mirror）' | Out-Null
    Add-Content -Path $log -Value "$(Get-Date -Format s) synced $($srcFiles.Count) files, committed $($changed.Count) paths"
  }
} finally { Pop-Location }
