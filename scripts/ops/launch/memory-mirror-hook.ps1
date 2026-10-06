# memory-mirror-hook.ps1 — Claude Code PostToolUse hook：项目记忆文件写入即触发镜像同步
# CEO 2026-10-06 20:42 令：触发形态=每小时 schtasks + 记忆新增时（本 hook）；登录自启退役
# stdin=PostToolUse JSON（tool_name / tool_input.file_path）；全程静默，内容零回显
$raw = [Console]::In.ReadToEnd()
try { $evt = $raw | ConvertFrom-Json } catch { exit 0 }
$fp = $evt.tool_input.file_path
if (-not $fp) { exit 0 }
# 精确段匹配主项目记忆目录（worktree 变体 D--Code-ai-TriMetaverse-worktrees-board 不命中：前缀后是 '-' 非 '\'）
if ($fp -like '*\.claude\projects\D--Code-ai-TriMetaverse\memory\*.md') {
  & 'D:\Code\ai\TriCompany\scripts\ops\launch\sync-memory-mirror.ps1'
}
exit 0
