# 用途：launch-seat.ps1 真源化迁移件（原 .fade/launch-seat.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/launch/launch-seat.windows.ps1
# 参数：-WorkingDir 工作树根（可选，默认 D:\Code\ai\TriMetaverse 主仓；worktree 起席传该树根，手册路径跟随同树）

# launch-seat.ps1 — 单席干净环境启动器（清 CLAUDE* 遗传变量后按正名形态 resume）
param(
  [Parameter(Mandatory=$true)][string]$Name,      # 如 m-cao
  [Parameter(Mandatory=$true)][string]$Agent,     # PascalCase 正名，如 ChiefAdministrativeOfficer
  [Parameter(Mandatory=$true)][string]$Manual,    # kebab 手册名，如 chief-administrative-officer
  [string]$WorkingDir = "D:\Code\ai\TriMetaverse" # 可选：工作树根目录（默认=主仓，向后兼容）
)
Remove-Item Env:CLAUDE_CODE_CHILD_SESSION -ErrorAction SilentlyContinue
Get-ChildItem Env: | Where-Object Name -like "CLAUDE*" | Remove-Item -ErrorAction SilentlyContinue
$env:CLAUDE_CODE_FORCE_SESSION_PERSISTENCE = "1"
Set-Location $WorkingDir
claude --resume $Name -n $Name --agent $Agent --verbose --dangerously-skip-permissions --append-system-prompt-file "$WorkingDir/.claude/compass/$Manual.session.md"
