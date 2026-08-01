# 员工能力同步审计报告

版本：v0.1
日期：2026-07-12
状态：CEO 审阅
审计人：CEOChiefOfStaff（小贾）

## 审计范围

逐项核查以下三条链路的完整性：

| 链路 | 源 | 目标 | 说明 |
|------|---|------|------|
| 源侧五件套 | TriCompany/source-agents/ | — | 员工定义真源 |
| 源侧绑定 | TriCompany/.github/binding-profiles/ | — | 宿主绑定登记 |
| 项目发布 | TriCompany 源侧 | TriMetaverse/.github/agents/ | 项目 live agent |
| 运行时支持 | TriCompany 源侧 | TriCompany-copilot-host-assets/knowledge/employees/ | 知识工作区 |
| 工具权限对齐 | TriMetaverse/.github/agents/（live tools） | TriCompany/source-agents/（source tools） | live agent tools 与 source agent tools 一致性检查 |

## 审计结果：员工 Agent（Role Agent）

共 11 个知识工作区，9 名活跃员工，2 个 legacy alias。

| # | 员工 ID | 源侧五件套 | 绑定 profile | Live agent | 知识工作区 | 状态 |
|---|---------|-----------|-------------|-----------|-----------|------|
| 1 | ceo-chief-of-staff | ✅ | ✅ | ✅ | ✅ | 正常 |
| 2 | chief-administrative-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 3 | chief-financial-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 4 | chief-human-resources-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 5 | chief-marketing-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 6 | chief-operating-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 7 | chief-product-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 8 | chief-technology-officer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 9 | rd-trainer | ✅ | ✅ | ✅ | ✅ | 正常 |
| 10 | project-trainer | ❌（有意不创建） | ❌（有意不创建） | ❌（有意不发布） | ✅（legacy alias） | 设计如此 |
| 11 | randd-trainer | ❌（有意不创建） | ❌（有意不创建） | ❌（有意不发布） | ✅（legacy alias） | 设计如此 |

### Project Trainer / RandD Trainer 说明

`project-trainer` 与 `randd-trainer` 是明确标注的 **deprecated legacy alias**。其知识工作区 README 记载：

- `liveEntryStatus: not-published`
- "legacy compatibility object set"
- "current canonical employee/source kit is `rd-trainer`"
- 所有 Source Refs 指向 `rd-trainer`

**结论**：project-trainer 与 randd-trainer 不创建源侧五件套、绑定 profile、或 live agent 是正确设计，不是缺口。两个知识工作区仅在 `rd-trainer` 正式发布前作为历史消费记录的迁移落点存在，不应进一步扩展。待 TriMC 正式宿主上线后评估是否可以归档/清理。

## 审计结果：Registry Agent（非人格 Agent）

TriCompany 源侧 registries 目录包含所有模块的三层 registry（BusinessStrategy + Product + Code）。

TriMetaverse live 仅发布 TriMetaverse 项目相关 registry：
- `business-strategy.agent.md`
- `CompanyGovernanceRegistry.agent.md`
- `TriMetaverseBusinessStrategyRegistry.agent.md`
- `TriMetaverseCodeRegistry.agent.md`
- `TriMetaverseProductRegistry.agent.md`

**结论**：项目级发布策略正确——只发布项目相关的 registry，不发布全公司所有模块的 registry。

## 发现的缺口

### 无缺口

经逐项核查，当前 9 名活跃员工的四条链路（源侧五件套 → 绑定 profile → live agent → 知识工作区）全部完整。

### 已知待确认项

| # | 事项 | 状态 | 建议 |
|---|------|------|------|
| 1 | CAO/CFO/CHO/CMO/COO 五件套内容为占位/模板级 | 源侧已创建，内容待 CEO 填充 | 等待 CEO 对五个管理岗的正式角色定义 |
| 2 | project-trainer / randd-trainer 知识工作区是否需要清理 | legacy alias，保留兼容 | 待 TriMC 正式宿主上线后评估是否归档 |
| 3 | registries 目录中其他模块 registry（TriSkill、TriMC 等）是否应在项目发布 | 当前不发布，正确 | 当 TriMetaverse 依赖这些模块时再评估 |

## 审计方法论

本审计采用"逐员工、逐链路"的核查方式，不使用自动化脚本生成。每条记录均通过对以下目录的实际文件列举验证：

- `TriCompany/source-agents/` — 10 个目录
- `TriCompany/.github/binding-profiles/` — 9 个 JSON
- `TriMetaverse/.github/agents/` — 14 个 agent 文件（9 员工 + 5 registry）
- `TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/` — 11 个目录

审计日期：2026-07-12
下次审计：当员工新增/离职/角色变更时触发，或按季度定期执行。

## 自动化审计储备

`runtime/cognition/employee_source_kit.py` 与 `runtime/cognition/employee_host_publish.py` 已具备自动化同步校验能力。下季度审计应从当前手工基线迁移至管线集成，将四条链路 + 工具权限对齐检查纳入 `employee_host_publish.py` 的发布验证步骤。当前 V0.1 手工审计作为自动化管线的需求规格基准。

## 变更记录

- 2026-07-12：初始审计，确认 9 名活跃员工全链路完整，project-trainer / randd-trainer 为 legacy alias 不视为缺口。
- 2026-07-12（CTO 路由审批后修订）：新增工具权限对齐检查维度（第 5 条链路）；补充 randd-trainer 知识工作区状态；新增自动化审计储备说明（employee_source_kit.py / employee_host_publish.py）。
