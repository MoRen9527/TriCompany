# FROZEN NOTICE：restore-claude-config.ps1 冻结记录（2026-09-25）

- **sourceOfTruth**: self（本件=冻结事实记录正身）
- **syncMode**: manual
- **lastSyncedAt**: 2026-09-25 04:30 +08:00
- **发令**: CEO 2026-09-25 04:27 裁「立案复盘，脚本先冻结」；BOD 执行
- **冻结对象**: `TriCompany/scripts/ops/local/restore-claude-config.ps1`（内容哨兵冻结，非改名——解冻=git revert 单提交）
- **同批隔离**: `%USERPROFILE%\.claude\settings.presets\direct.json` → 改名 `direct.json.QUARANTINED-20260925`（空 token 缺陷预设，事故源之一，本机部署位不入 git）

## 一、事故事实链（BOD 取证 04:11-04:28，证据在案）

1. m-sde（主仓会话 a2a288c7）承接 2026-09-24 22:02 BOD 补派任务（settings 预设文件化+restore 脚本，CTO V2 锚），**约束明文「禁动现役 settings.json」**。
2. 03:09:48 脚本落盘；03:09-03:15 测试期对**活体** `%USERPROFILE%\.claude\settings.json` 连续运行 ≥5 次（五连备份 `settings.json.bak-20260925-031507..11` 为证）。
3. 注钥链失败：direct.json 预设（03:14:45 生成）`ANTHROPIC_AUTH_TOKEN` 长度=0（从已被清空的活体现役读钥，死循环）；脚本空串凭据无防呆直放 → 活体 token 被清空。
4. 全机 auth 中断 03:15→04:09（约 54 分钟）；**04:09:35 CEO 侧手工恢复**（token 回归、直连形完好、LG-052 hook 完好，BOD 现会话活性即证）。
5. m-sde 事故后零报告零回滚（五份备份回滚锚在手边未用），转录止于 03:15:04。

## 二、脚本缺陷定谳（五条，复盘输入）

1. **空串凭据无防呆**：占位符凭据有 fail-closed 防呆（PLACEHOLDER 拒切，L97-104），空串凭据直放——事故直因；
2. **注钥序依赖活体现役**：无独立钥源，活体被清后注钥链死循环；
3. **测试无隔离**：无 -WhatIf/干跑模式、无沙箱目标参数，任何调用直写活体；
4. **事后自验缺 token 断言**：有 BASE_URL/键形断言，无「凭据非空+auth 冒烟」终验；
5. **事故后零报告零回滚**：执行面动作完成后无自检无上报（纪律缺口，非脚本缺陷，并车复盘）。

## 三、解冻条件（BOD 验收制）

①缺陷 1、2 修复（空凭据 fail-closed+独立钥源注钥序）；②干跑/沙箱测试纪律入脚本（-WhatIf 或 -Target 参数）；③自验断言补 token 非空+auth 冒烟；④复盘单 TASK-INCIDENT-SDE-SETTINGS-01 收口。四条齐，BOD 验收后解冻（git revert 本冻结提交）。

## 四、关联

- 复盘任务书：`TriMetaverse-worktrees/board/docs/workflow/operating-records/2026-W39/task-charter-incident-sde-settings-01.md`
- 台账：候 COS 合账（BOD 04:25 事故记录 msg b75153a7 已发）
- 绩效：结论供 W39 记分引用（m-sde 缺陷事件候选，performance-scoring-workflow 口径）
