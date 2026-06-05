# TriCompany Registry 说明

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/README.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-06-04

TriCompany 当前采用最小 registry 结构：

- business-state.md：记录模块的商业定位、默认职责、边界与阶段约束
- product-state.md：记录模块的产品事实、范围、当前进展和产品缺口
- code-state.md：记录模块的技术结构、仓库状态、质量风险和执行层纪律
- company-governance-state.md：记录公司治理、秘书处机制、组织制度、文档语言规则与治理文档归属

## 更新规则

- 只有在明确要求记录或更新时，registry 才写入新状态
- registry 不替代产品真源和技术真源，只做事实快照与缺口提示
- 若事实不足，registry 必须输出“待确认”，而不是编造进度

## 当前对应 agent

- TriCompanyBusinessStrategyRegistry
- TriCompanyProductRegistry
- TriCompanyCodeRegistry
