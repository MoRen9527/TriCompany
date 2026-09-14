## TriRLC/构建/健康检查命令族（域知识族·LG-028 迁入）

> D 类域知识族首例（LG-028 第一步②；内容源=TriMetaverse CLAUDE.md Common Commands 节；CTO session 面工程域知识）。本件先落本节，session-body 完整化随 LG-024 批 1 管线窗。

### TriRLC daemon（本地控制器）

```bash
trilc start              # Start daemon in background
trilc stop               # Stop daemon
trilc status             # Show daemon status (healthz + heartbeat + cron)
trilc daemon install     # Install as Windows scheduled task
trilc cron add/list/run  # Manage cron jobs
```

### 健康检查

```bash
curl http://127.0.0.1:8711/healthz
```

### Build pipeline（CI 触发）

Push `v*` tag 触发 `build-tricade.yml` → MSI + ZIP + GitHub Release。

### Install（统一脚本）

```powershell
.\scripts\install-tricade.ps1 -MsiPath <path> [-InstallService]
.\scripts\verify-trilc-24h.ps1 -DurationHours 1  # Quick stability test
```

## 开工前置核查

在给出技术判断、交付计划或发布决策前，按顺序核查：

1. 当前用户 / CEO 的最新明确输入。
2. 中央 `BusinessStrategy`，确认当前实验、模块边界和交付优先级。
3. `TriCompany/docs/engineering/DESIGN.md`、`metacognition-architecture.md`、`docs/registry/code-state.md`。
4. 相关模块的 Code Registry；涉及产品边界时补查 Product Registry。
5. 发布、测试或部署 readiness 重要时，优先检查 TriDev 的相关 registry / workflow truth；只有需要历史兼容资料时，才补查 TriTest 与 Trideployment registry。
6. 事项涉及岗位、授权或秘书处机制时，补查 `CompanyGovernanceRegistry`。
