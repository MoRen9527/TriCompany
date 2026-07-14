# 员工编排仪表盘 — W29 首版

- 状态：✅ 首版回填（CARRY-006-3）
- 快照日期：2026-07-14（W29）
- 维护归属：CTO（小狄）
- 上游依据：CTO-002 宿主对象生成编排、CHO 上岗审批记录、TriCompany source-agents

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/dashboards/employee-orchestration.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-07-14

---

## 1. 员工总览

| 指标 | 当前值 | 说明 |
|------|--------|------|
| 定义岗位总数 | **11** | DECLARED_HOST_OBJECT_SETS |
| 员工生成器总数 | **13** | EMPLOYEE_GENERATORS（含 2 个 alias） |
| Binding Profiles | **11** | `.github/binding-profiles/*.json` |
| Live Agent 入口 | **11** | `.github/agents/*.agent.md` |
| 已上岗员工 | **3** | CPO(小乔)、CTO(小狄)、FullStack(小全) |
| 部分上岗 | **1** | TestEngineer(小柯)—CTO-007 smoke test 通过，待 CHO 正式上岗确认 |
| 待上岗 C-Level | **5** | CMO/COO/CFO/CAO/CHRO — 无 display_name |
| 待上岗其他 | **2** | ProjectTrainer、ObservabilityAgent |

## 2. 员工明细

### 2.1 已上岗（3 人）

| 员工 | 昵称 | 岗位 | 汇报线 | 上岗日期 | 审批 |
|------|------|------|--------|----------|------|
| ChiefProductOfficer | 小乔 | CPO | CEO | 2026-07-08 | CEO |
| ChiefTechnologyOfficer | 小狄 | CTO | CEO | 2026-07-08 | CEO |
| FullStackDeveloper | 小全 | 全栈开发 | CTO | 2026-07-14 | CHO ✅ |

### 2.2 合同已上线，首次 smoke test 完成（1 人）

| 员工 | 昵称 | 岗位 | 汇报线 | 合同状态 | 说明 |
|------|------|------|--------|----------|------|
| TestEngineer | 小柯 | 测试工程师 | CTO | ✅ 17/17 pass | CTO-007 smoke test 通过（validate.mjs PASS） |

### 2.3 待上岗 — C-Level（5 人）

| 员工 | display_name | 岗位 | 状态 | 阻塞原因 |
|------|-------------|------|------|----------|
| ChiefMarketingOfficer | 待命名 | CMO | 合同未建立 | 等 CEO 命名决策 |
| ChiefOperatingOfficer | 待命名 | COO | 合同未建立 | 等 CEO 命名决策 |
| ChiefFinancialOfficer | 待命名 | CFO | 合同未建立 | 等 CEO 命名决策 |
| ChiefAnalyticsOfficer | 待命名 | CAO | 合同未建立 | 等 CEO 命名决策 |
| ChiefHumanResourcesOfficer | 待命名 | CHRO | 合同未建立 | 等 CEO 命名决策 |

### 2.4 待上岗 — 其他（2 人）

| 员工 | 岗位 | 状态 | 说明 |
|------|------|------|------|
| ProjectTrainer | 项目培训师 | 框架就绪 | 生成器已注册，无 binding |
| ObservabilityAgent | 可观察性代理 | 框架就绪 | 生成器已注册，无 binding |

## 3. CTO 直辖团队结构

```
                         CTO（小狄）
                      审查两人工作质量与效率
                    ┌─────────┴─────────┐
                    ▼                   ▼
              小全（FullStack）     小柯（TestEngineer）
              具体编码积木           验证器
              ┌─────┬─────┐        测试编写 + 执行
              ▼     ▼     ▼
           TriMC  TriWeb4 TriStaciss
           TriDev TriTest TriDeployment
```

## 4. 宿主对象生成管道（CTO-002）

| 指标 | 值 |
|------|-----|
| DECLARED_HOST_OBJECT_SETS | 11 |
| EMPLOYEE_GENERATORS | 13（含 alias） |
| Host Object Set ID 常量 | 11 |
| CLI 模式 | `test-engineer`, `full-stack-developer`, `all`, `publish` |
| 生成器补全 | EMPLOYEE_GENERATORS 7→13（补 CMO/COO/CFO + 小柯 + 小全） |
| Publish 验证 | 11/11 agent.md + 11/11 binding profiles ✅ |

## 5. 上岗流水线（新规）

```
JD定义 → 源侧五件套 → contract.yaml → binding profile → CHO审批 → 激活 → governance回填
(CTO)     (CTO)         (CTO)           (CTO)             (CHO)     (CTO)    (COS)
```

**审批门**：CHO 签字为正式上岗前提（CEO 2026-07-14 裁决，已写入 company-governance-state.md）。

## 6. 下一快照目标（W30）

- [x] 小柯首次 smoke test 完成 → 状态变更为「已上岗」（CTO-007 已完成，待 CHO 正式确认）
- [ ] 小全 first commit 通过 CTO review
- [ ] 至少 1 个 C-Level 获得 display_name 命名
- [ ] ProjectTrainer 或 ObservabilityAgent 合同建立

## 7. 历史快照

| 快照 | 日期 | 上岗 | 部分上岗 | 待上岗 | HostObjectSets | Generators |
|------|------|------|----------|--------|----------------|------------|
| W29 | 2026-07-14 | 3 | 1 | 7 | 11 | 13 |
