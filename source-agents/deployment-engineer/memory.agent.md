# Memory Layer Contract

## 认知层契约

- **部署历史记忆**：每次部署的版本号、git commit、目标环境、执行时间、结果状态——按项目和时间线索引。
- **环境状态记忆**：各环境的当前版本、配置差异、已知问题——按环境分类维护。
- **回滚方案记忆**：每个项目的回滚步骤、验证时间、上次成功回滚记录。
- **CI/CD 配置记忆**：各项目的流水线配置、构建脚本路径、关键依赖版本。

## 写入边界

- 不写入环境密钥或敏感凭证——memory 层只记录部署事实，不存储 secrets。
- 不写入代码实现细节——那是各模块 Code Registry 的领域。
- 部署记录标注操作人和审批人，不可篡改。

## 运行资产落点

- 部署记录：`TriCompany/docs/execution/deployment-records/`
- 环境状态：`TriCompany/docs/registry/environment-state.md`（待初始化）
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/deployment-engineer/`
