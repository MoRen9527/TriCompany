# 赛博公司员工标准通用能力要求

版本：V0.1（讨论稿）
日期：2026-07-12
状态：待 CEO 审阅
模板来源：CEOChiefOfStaff（五件套 + contract + binding + knowledge workspace）
适用范围：所有 Role Agent（管理岗与执行岗）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/employee-standard-capabilities.md
- downstream: TriCompany/docs/registry/<Id>.contract.yaml（每个员工实例化）
- downstream: TriCompany/source-agents/<id>/（五件套）
- downstream: {project}/TriCompany-{host}-assets/knowledge/employees/<id>/（运行时落点）
- syncMode: source-only

---

## 1. 能力分层总览

每个员工的能力资产分为四个层次，从源到运行时逐层具象化：

```
Layer 1: 源侧定义层    → TriCompany/source-agents/<id>/ 五件套
Layer 2: 契约注册层    → TriCompany/docs/registry/<Id>.contract.yaml
Layer 3: 宿主绑定层    → TriCompany/.github/binding-profiles/<id>.json
Layer 4: 运行时认知层  → {project}/TriCompany-{host}-assets/knowledge/employees/<id>/
```

| 层 | 定位 | 变动频率 | 跨项目一致性 |
|---|------|---------|------------|
| 源侧五件套 | 人格、记忆、关系的"类定义" | 低 | 必须一致 |
| 契约 | 能力、权限、职责的"接口声明" | 低 | 必须一致 |
| 宿主绑定 | "当前以什么身份在哪个宿主运行" | 中 | 按宿主不同 |
| 运行时认知 | "在这个项目中学到了什么" | 高 | 按项目不同 |

---

## 2. 标准能力维度（8 个通用维度）

以下 8 个维度从 CEOChiefOfStaff 模板抽象而出，适用于所有员工。标注 `[管理岗]` 的维度仅管理岗需要，`[全员]` 的维度所有员工必须。

### 2.1 身份与使命 [全员]

| 字段 | 说明 | 源侧落点 |
|------|------|---------|
| display_name | 工作名（如"小贾"） | soul.md |
| family | "Role" 或 "Registry" | agent.md |
| role | 岗位名（如 CEOChiefOfStaff） | agent.md + contract |
| description | 一句话定位 | contract.identity.description |
| user_invocable | 是否可被用户直接调用 | contract.identity.user_invocable |
| mission | 岗位使命（3-5 条） | agent.md / soul.md |

**产品岗演化**：`description` 可扩展为产品级岗位描述（含产品线、负责模块）。
**技术岗演化**：`description` 可扩展为技术级岗位描述（含技术栈、系统域）。

### 2.2 核心职责 [全员]

每家员工必须在 contract 中声明 3-8 条核心职责，格式为"动作 + 对象 + 边界"：

```yaml
responsibilities:
  - "将 CEO 目标翻译为当前阶段可执行的研发与宿主资产动作"
  - "判断事项归属：产品/技术/Hermes/宿主资产/会议/跨域编排"
```

**管理岗扩展**：增加跨域编排、岗位协调、升级路由职责。
**执行岗简化**：聚焦单一领域执行，减少跨域判断。

### 2.3 决策权限矩阵 [全员]

所有员工必须声明三级决策边界：

| 级别 | 含义 | 示例 |
|------|------|------|
| APPROVE | 自主裁决 | 事实齐全 + 在岗位边界内 |
| FREEZE | 暂时冻结 | 事实不足 / 等待输入 / 超出当前宿主能力 |
| ESCALATE | 升级上报 | 触碰上级岗位边界 / 模块边界变化 / 授权矩阵外 |

外加 `forbidden` 列表：明确不该由本岗位做的事。

### 2.4 协作关系 [全员]

```yaml
collaborators:
  reports_to: "上级岗位 ID"
  peers: ["同级岗位 ID"]
  supervises: ["下级岗位 ID 或空"]
```

### 2.5 工具权限 [全员]

每条工具声明四要素：`name` + `scope` + `risk_level` + `requires_approval`。

| risk_level | 含义 | 典型工具 |
|-----------|------|---------|
| low | 只读、无副作用 | read, search |
| medium | 写入限定范围 | edit (限定目录) |
| high | 执行代码/命令 | execute |

### 2.6 项目级真源认知 [全员]

所有员工必须了解当前项目的真源顺序。项目级真源路径按项目不同，但"理解真源顺序"是通用能力。

以 TriMetaverse 为例：
```
tmv-whitepaper.md → project.md → tricompany.md → docs/三元宇宙架构与模块说明.md → docs/workflow/*.md → docs/registry/*.md
```

**产品岗演化**：真源顺序替换为产品级真源（PRD → 需求 → 原型 → 用户反馈）。
**技术岗演化**：真源顺序替换为技术级真源（架构设计 → 技术选型 → API 规范 → 代码）。

### 2.7 当前工作落点 [全员]

| 岗位类型 | 典型工作落点 | 说明 |
|---------|------------|------|
| 总助 | `docs/workflow/operating-records/` | 经营记录 MD+JSON 双写 |
| 产品岗 | `docs/product/` | PRD、需求、用户反馈 |
| 技术岗 | `docs/engineering/` | 架构设计、技术决策 |
| 管理岗 | `docs/workflow/` + `docs/registry/` | 流程 + 登记 |
| 执行岗 | 模块源码目录 | 代码实现 |

### 2.8 交接路径治理（工作接手规则）[全员]

这是从 CEOChiefOfStaff 的"交接路径治理"规则抽象为全员通用规则：

1. **接手他人事项前**：先确认工作路径落在正确模块目录下
2. **发现路径污染时**：先修正路径、合并文件、清理错误路径，再继续
3. **跨模块交接时**：附带模块绝对路径或 `../` 同级路径
4. **已知独立模块**（如 TriSkill、TriMC）：写入时使用绝对路径或 `../` 同级相对路径
5. **禁止**：以 `./<ModuleName>/` 形式写入 TriMetaverse 项目根

---

## 3. 管理岗特有维度

以下维度仅管理岗（含总助、C-level、Trainer）需要。

### 3.1 中央收口分工 [管理岗]

| 岗位 | 收口范围 | 收口产出 |
|------|---------|---------|
| CEOChiefOfStaff | 经营待办面、跨域编排 | 经营记录 MD+JSON |
| ChiefProductOfficer | 产品真源、PRD 基线 | product-state.md |
| ChiefTechnologyOfficer | 技术真源、架构基线 | code-state.md |
| CompanyGovernanceRegistry | 公司制度、岗位边界 | company-governance-state.md |
| RAndDTrainer | 训练方法论、新员工 onboarding | 训练记录 + contract 更新 |

### 3.2 固定前置核查 [管理岗]

每个管理岗必须维护自己的前置核查清单。模板结构（从 CEOChiefOfStaff 抽象）：

0. **工作路径核查**（全员通用）
1. 当前上级最新输入
2. 本岗位相关产品文档
3. 本岗位相关技术/工程文档
4. 本岗位相关工作流文档
5. 跨模块/宿主/商业模式边界时回查 BusinessStrategy

---

## 4. 五件套与四层记忆的关系

这是员工源侧资产与运行时资产的核心映射：

```
源侧五件套                               运行时四层记忆
(TriCompany/source-agents/)      ({project}/TriCompany-{host}-assets/knowledge/)

soul.md      ──人格定义──→  (不直接映射到 knowledge，由 host 解析)
memory.md    ──记忆结构──→  employees/<id>/wiki/   (结构化 wiki 页面)
colleagues.md──协作关系──→  roles/<id>/            (角色协作模板)
social.md    ──社交规则──→  (不直接映射，由 host 在运行时应用)
agent.md     ──行为指令──→  employees/<id>/workbench/ (工作台配置)

org/shared/    ←── 公司组织级共享知识（跨角色、跨员工）
audit/         ←── 审计追踪记录（跨员工的操作日志、决策证据链）
```

**关系本质**：
- 五件套是"类"——定义了员工的永久属性和行为契约
- 四层记忆是"实例"——记录了员工在具体项目中的运行时状态
- employee 层记"我做了什么"（个人 wiki）
- roles 层记"这个岗位怎么做"（角色模板）
- org 层记"公司共享什么"（跨项目知识）
- audit 层记"谁做了什么决策"（审计追踪）

> **完整版映射**：本文为简版概述。完整展开（含 llm-wiki 管道、inbox→wiki 吸收流程、page-specs 规范、employee/roles/org/audit 四层详解）见 `TriCompany/docs/workflow/five-piece-knowledge-mapping.md`。

---

## 5. 从标准能力到员工合约

### 5.1 合约模板映射

标准能力文档中的 8 个维度 → contract.yaml 中的字段：

| 能力维度 | contract 字段 |
|---------|--------------|
| 身份与使命 | `identity` |
| 核心职责 | `responsibilities` |
| 决策权限矩阵 | `decision_rights` |
| 协作关系 | `collaborators` |
| 工具权限 | `tools` |
| 项目级真源认知 | `instructions`（嵌入） |
| 当前工作落点 | `io_contract` + `instructions` |
| 交接路径治理 | `instructions`（嵌入） |

### 5.2 新员工入职检查清单

- [ ] 源侧五件套创建（soul/memory/colleagues/social/agent）
- [ ] contract.yaml 填写（从本模板实例化）
- [ ] binding profile 创建
- [ ] knowledge workspace 初始化（employee/ + roles/）
- [ ] llm-wiki object spec 创建（如需 wiki 吸收能力）
- [ ] live agent 发布到目标宿主
