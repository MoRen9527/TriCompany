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
# 席位模型分工（CEO 令 2026-11-27 16:11）：--model 按席钉档位——查表逻辑+基线在共享件
#   seat-model-tier.ps1（CTO 复核修③·三调用方 dot-source 同一件防漂移）；档位=别名非字面模型名
#   （opus=glm-5.4 / sonnet=glm-5.3-flash·settings.json 集中映射）。表不可读/基线席缺=回落基线
#   （必用席禁静默降档）；非基线席缺=Default(sonnet)。会话模型是会话级——改配置不改运行中会话，
#   故档位须在启动时钉入。
. "$PSScriptRoot\seat-model-tier.ps1"
$ModelTier = Get-SeatModelTier -SeatName $Name -MapFile (Join-Path $PSScriptRoot 'seat-model-map.psd1')
# ①env 继承根修（CTO 派工 2026-11-28）：claude 调用前从注册表权威源重写 $env:TRILC_INTERNAL_TOKEN
#   （父链旧 env 不重读注册表=标读静默失效真因）——日志行落 .fade\seat-env-sync.log（restart ④消费）。
$null = Ensure-SeatEnvToken -SeatName $Name
Remove-Item Env:CLAUDE_CODE_CHILD_SESSION -ErrorAction SilentlyContinue
Get-ChildItem Env: | Where-Object Name -like "CLAUDE*" | Remove-Item -ErrorAction SilentlyContinue
$env:CLAUDE_CODE_FORCE_SESSION_PERSISTENCE = "1"
# D-102 observe 轮闸日志归席（CTO 派工 2026-11-28 02:30·闸 v1.4 12502f1）：TRI_SEAT_NAME 注入——
#   闸日志席位字段 env 优先（hook 继承 claude 进程 env·启动器显式注入=子进程可依赖确定值）。
$env:TRI_SEAT_NAME = $Name
Set-Location $WorkingDir
# resume-by-title 去歧义（同名多命中弹会话选择器防线；fail-open 不挡启动——2026-10-05 CEO 令）
# 零历史容忍双形态（2026-11-01 CEO 令·14 席全支持无历史启动）：Invoke-ResumeDisambig 返回剩余
#   唯一候选数——≥1=有历史走原组合 --resume（行为零变化）；0=零历史或去歧义故障走纯 -n 注册形
#   （--resume 零命中报「No sessions match」卡席——m-pm 2026-11-01 实证；-n 永远能起）。
. "$PSScriptRoot\resume-disambig.ps1"
$sessionCount = Invoke-ResumeDisambig -Name $Name -WorkingDir $WorkingDir
if ($sessionCount -ge 1) {
  claude --resume $Name -n $Name --agent $Agent --model $ModelTier --verbose --dangerously-skip-permissions --append-system-prompt-file "$WorkingDir/.claude/compass/$Manual.session.md"
} else {
  claude -n $Name --agent $Agent --model $ModelTier --verbose --dangerously-skip-permissions --append-system-prompt-file "$WorkingDir/.claude/compass/$Manual.session.md"
}
