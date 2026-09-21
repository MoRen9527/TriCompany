# Memory Layer Contract

源侧认知层契约（DE 合并件形态席；boundary marker 按本件实文承载）。

## 认知层契约

- **部署历史记忆**：每次部署的版本号、git commit、目标环境、执行时间、结果状态——按项目和时间线索引。
- **环境状态记忆**：各环境的当前版本、配置差异、已知问题——按环境分类维护。
- **回滚方案记忆**：每个项目的回滚步骤、验证时间、上次成功回滚记录。
- **CI/CD 配置记忆**：各项目的流水线配置、构建脚本路径、关键依赖版本。

## 写入边界

- 不写入环境密钥或敏感凭证——memory 层只记录部署事实，不存储 secrets。
- 不写入代码实现细节——那是各模块 Code Registry 的领域。
- 部署记录标注操作人和审批人，不可篡改。

## 当前原则

- 源码侧只保留记忆层的通用规则和边界，不写运行消费数据。
- 部署事实按下方落点分流，运行态机器写入与策展资产分层，不混记录。
- 涉及环境凭证、审批链与回滚责任的事实，以部署记录真源为准，memory 只留索引。

## 运行资产落点

- 部署记录：`TriCompany/docs/execution/deployment-records/`
- 环境状态：`TriCompany/docs/registry/environment-state.md`（待初始化）
- 学习腿（Employee workspace）：`TriCompany-copilot-host-assets/knowledge/employees/senior-deployment-engineer/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）
- 运行腿：`TRICOMPANY_COGNITION_HOME`（.tricompany-cognition：employee 私域运行态/org 运行共享记忆/org 运行审计——机器写入，runtime cognition backend 驱动，复活时初始化）

## 层契约

- employee id 固定为 `deployment-engineer`；该 id 只用于路径和 manifest，不代表 live 已启用。
- 双腿分流：策展资产入学习腿，运行态入运行腿；两腿不得互写。
