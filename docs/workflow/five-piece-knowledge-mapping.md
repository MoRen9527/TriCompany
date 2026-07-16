# 员工五件套与四层记忆完整映射

版本：V0.1
日期：2026-07-12
状态：CEO 审阅
作者：CEOChiefOfStaff（小贾）
依赖：`employee-standard-capabilities.md` Section 4（本文为其详细展开）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/five-piece-knowledge-mapping.md
- syncMode: source-only
- publishTier: source-only
- supersedes: employee-standard-capabilities.md Section 4 的简版映射（本文为完整版）

---

## 1. 核心隐喻：类与实例

```
五件套（源侧定义）                      四层记忆 + 运行时（项目实例）
TriCompany/.github/source-agents/       TriCompany-copilot-host-assets/knowledge/

      "类"                                     "实例"
   永久属性与行为契约                         项目中的运行时状态
 跨所有项目一致                             每个项目独立
   低频变更                                   持续累积
```

**一句话**：五件套定义了"这个员工是谁、能做什么、怎么协作"，四层记忆记录了"这个员工在当前项目中学到了什么、做了什么决策、跟谁互动过"。

---

## 2. 五件套 → 四层记忆映射总表

| 五件套文件 | 定位 | 映射到 knowledge 层 | 映射方式 |
|-----------|------|-------------------|---------|
| `soul.md` | 人格定义（气质、口吻、表达风格） | ❌ 不直接映射到 knowledge | 由宿主在运行时解析并应用 |
| `memory.md` | 记忆结构（记住什么、怎么分类） | → `employees/<id>/wiki/` | 记忆结构 → wiki 页面分类与 page-specs 定义 |
| `colleagues.md` | 协作关系（与谁协作、怎么协作） | → `roles/<id>/` | 协作规则 → 角色协作模板 |
| `social.md` | 社交规则（礼节、称呼、偏好） | ❌ 不直接映射到 knowledge | 由宿主在运行时应用 |
| `agent.md` | 行为指令（职责、护栏、决策规则） | → `employees/<id>/workbench/` | 行为指令 → 工作台配置与执行边界 |

---

## 3. 四层记忆详解

### 3.1 knowledge/employees/（员工实例记忆）

这是每个员工的**个人知识空间**，记录"我做了什么、学到了什么"。

```
knowledge/employees/<employee-id>/
├── README.md              # 工作区元信息（objectSetId, workspaceKind, sourceRefs）
├── audit/                 # 审计追踪层
│   ├── README.md
│   ├── record-template.json   # 审计记录模板
│   └── wiki-refresh-*.json    # 运行时生成的吸收记录
├── inbox/                 # 原始输入层
│   ├── README.md
│   ├── source-template.md     # 资料来源模板
│   └── *.md / *.json          # 待吸收的原始资料
├── wiki/                  # 体系化知识层
│   ├── README.md
│   ├── page-specs.json        # 页面规格（定义哪些源合成哪些页）
│   ├── page-template.md       # wiki 页面模板
│   └── *.md                   # 编译后的体系化知识页
└── workbench/             # 工作台投影层
    ├── README.md
    └── *.html / *.json        # 工作台快照（待 TriMC 正式渲染）
```

#### 3.1.1 inbox/ —— 原始输入层

**定位**：放"还没整理的零散资料"，是 llm-wiki 管道的**入口**。

**与五件套的关系**：
- inbox 的内容来源由 `memory.md` 定义（员工需要追踪什么信息）
- inbox 的信任级别与过滤规则由 `agent.md` 定义（什么来源可信、什么应忽略）

**支持的文件格式**：`.md`、`.txt`、`.json`

**标准 frontmatter**：
```yaml
---
sourceId: <employee-id>-note-<date>-<seq>
title: <资料标题>
sourceType: meeting_note | research | decision | reference | handoff
topicHints: [标签1, 标签2]
trustLevel: confirmed | working | draft
receivedAt: <ISO datetime>
---
```

**当前状态**（2026-07-12）：
- CEOChiefOfStaff：5 份 inbox 资料（完整运行中）
- 其他 9 名员工：inbox 目录已创建，内容为空（待首次使用）

#### 3.1.2 wiki/ —— 体系化知识层

**定位**：inbox 中的原始资料经 page-specs 规则编译后的**结构化知识页**。这是 llm-wiki 管道的**出口**。

**与五件套的关系**：
- wiki 的页面分类体系由 `memory.md` 定义
- wiki 的编译规则由 page-specs.json 定义（核心 schema）
- page-specs.json 的字段结构由 llm-wiki-object-spec 定义

**核心对象：page-specs.json**

```json
{
  "specId": "<employee-id>-<page-name>",
  "pageId": "<page-id>",
  "title": "<页面标题>",
  "pageStatus": "working | stable",
  "topicTags": ["标签"],
  "sourceIds": ["匹配的 inbox source"],
  "reviewerRoles": ["审阅岗位"],
  "primaryReviewer": "主审人",
  "approvalSlaHours": 168,
  "maxSources": 20
}
```

**与五件套 memory.md 的映射示例**（以 CEOChiefOfStaff 为例）：

| memory.md 中的记忆分类 | → wiki/page-specs 中的页面 |
|------------------------|---------------------------|
| 治理路由记忆 | `governance-routing` |
| 员工能力记忆 | `employee-capability` |
| 经营记录记忆 | `operating-records` |
| 消费记录记忆 | `employee-consumption-records` |

**当前状态**：
- CEOChiefOfStaff：4 页 wiki（governance-routing、employee-capability、operating-records、consumption-records），page-specs 完整
- CPO/CTO：仅有 employee-consumption-records（消费记录，非 wiki 吸收产出）
- 其余 7 名员工：仅有 employee-consumption-records 或空

#### 3.1.3 audit/ —— 审计追踪层

**定位**：记录"谁、什么时候、用什么源、产出了什么页面"的**操作证据链**。

**与五件套的关系**：
- audit 的追踪粒度由 `memory.md` + `agent.md` 联合定义
- audit 记录的是五件套 → 知识工作区的"运行时操作痕迹"

**标准记录模板**：
```json
{
  "runId": "<uuid>",
  "triggerMode": "manual | scheduled | event_driven",
  "startedAt": "<ISO datetime>",
  "inputSources": ["<sourceId>"],
  "outputPages": ["<pageId>"],
  "status": "completed | partial | failed",
  "notes": "<备注>"
}
```

**与五件套 agent.md 的决策约束关系**：
- agent.md 定义"什么情况下应该冻结/升级"
- audit 记录"实际做了什么决策、基于什么源"

**当前状态**：
- CEOChiefOfStaff：33 条 audit 记录（完整运行中）
- 其他 9 名员工：audit 目录已创建，模板就绪，无运行记录

#### 3.1.4 workbench/ —— 工作台投影层

**定位**：将 wiki 中的结构化知识渲染为**可交互的知识工作台**。当前为占位，待 TriMC 正式宿主上线后激活。

**与五件套的关系**：
- workbench 的布局和交互由 `agent.md` 的行为指令决定
- workbench 的显示内容来源是 wiki/ 的页面

**当前状态**：所有 10 名员工 workbench/ 均为占位 README.md，待 TriMC 启动。

---

### 3.2 knowledge/roles/（角色模板记忆）

**定位**：记录"某个**岗位**（不是具体人）应该怎么做的模板知识"。跨项目可复用。

**与五件套的关系**：
- 由 `colleagues.md` 中的协作关系抽象而来
- 当多个项目中同一岗位的协作模式稳定后，沉淀为 roles 模板

**当前状态**：roles/ 目录存在但内容待填充。

**MVP baseline（当前单项目阶段）**：roles/ 无需等到 2-3 个项目才启动。当前阶段至少应承载以下最小三角关系：
- **CPO ↔ CTO ↔ 总助** 的岗位间协作模板
- 产品↔技术↔总调度的路由边界与交接契约
- employee-consumption-records 中已验证的跨岗协作模式（如本次路由审批流程）
- 其余 6 个管理岗的 roles 模板待 CEO 激活后从 `colleagues.md` 抽象补充

该层在 TriCompany 源侧由各员工的 `colleagues.md` 抽象而来，待积累更多项目后进一步泛化。

---

### 3.3 knowledge/org/（组织共享记忆）

**定位**：记录"公司级别的共享知识"，跨角色、跨员工、跨项目。

**与五件套的关系**：
- 不直接由单个员工的五件套映射
- 由 CompanyGovernanceRegistry 和 BusinessStrategy 的跨项目输出沉淀而来

**内容类型**：
- 公司制度模板
- 跨项目发布规则
- 宿主适配标准
- 术语表

**当前状态**：org/shared/ 已创建，内容待初始化。

---

### 3.4 knowledge/audit/（全局审计层）

**定位**：位于 knowledge 根目录的 `audit/`，记录**跨员工的系统级操作日志**（不同于 employee 层内的个人 audit）。

**与五件套的关系**：
- 由所有员工的 agent.md 共同触发生成
- 记录的是跨员工协同操作的证据链（如"CEO Chief Of Staff 分发任务 → CPO 接收 → CTO 执行"）

**与 employee audit 的区别**：

| 维度 | knowledge/audit/（全局） | knowledge/employees/<id>/audit/（个人） |
|------|------------------------|----------------------------------------|
| 范围 | 跨员工、跨岗位 | 单个员工 |
| 记录内容 | 系统级协同操作 | 个人 wiki 吸收操作 |
| 触发者 | 多人 | 单人 |

**当前状态**：audit/ 目录存在于 knowledge 根，内容待初始化。

---

## 4. LLM-Wiki 吸收管道

### 4.1 管道架构

```
inbox/ 原始资料
   ↓
page-specs.json（schema：匹配规则、编译规则）
   ↓
LLM 编译（摘要 + 事实 + 判断 + 待确认 + 来源）
   ↓
wiki/ 体系化知识页
   ↓
audit/ 审计记录（操作证据链）
   ↓
workbench/ 工作台快照（待 TriMC）
```

### 4.2 Hermes 吸收与 Cron 定时

**已吸收的 Hermes 能力**：
- Hermes cron 调度机制已纳入 `runtime/cognition/` 模块
- 但当前阶段 **不支持自动定时吸收**，原因：
  1. 所有员工（除 CEOChiefOfStaff）的 inbox 为空，无内容可吸收
  2. page-specs.json 除 CEOChiefOfStaff 外未定义，无吸收规则
  3. 当前 Copilot-host 阶段无持久化 cron 进程运行环境
  4. CEO 明确要求"先手动确认质量，再讨论自动化"

**当前手动操作方法**：
```bash
cd TriCompany
python -m runtime.cognition.chief_of_staff_llm_wiki_refresh --page-id <id> --title "标题"
```

**接入 TriMC 方案**：
- 已记录为待办：`TriMC/wiki-absorption-cron` 计划在 TriMC 练兵场启动后试验 cron 驱动自动吸收
- 详见 `TriCompany/docs/workflow/employee-llm-wiki-guide.md`

### 4.3 员工启用 wiki 吸收的前置条件

| 条件 | CEOChiefOfStaff | CPO | CTO | R&D Trainer | CAO/CFO/CHO/CMO/COO |
|------|:---:|:---:|:---:|:---:|:---:|
| 四目录存在 | ✅ | ✅ | ✅ | ✅ | ✅ |
| page-specs.json | ✅ | ❌ | ❌ | ❌ | ❌ |
| llm-wiki-object-spec | ✅ | ✅（cpo-llm-wiki-object-spec） | ✅（cto-llm-wiki-object-spec） | ❌ | ❌ |
| inbox 有内容 | ✅ 5 | ❌ | ❌ | ❌ | ❌ |
| runtime 泛化 | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 5. 与公司-项目架构的关系

```
TriCompany（公司侧）                         TriMetaverse（项目侧）
├── .github/source-agents/                   ├── .github/agents/
│   └── <employee>/ 五件套（源侧定义）         │   └── <employee>.agent.md（live 入口）
├── docs/registry/                           ├── docs/
│   └── <Id>.contract.yaml（合约）             │   ├── registry/（项目级登记）
├── .github/binding-profiles/                │   └── 三元宇宙架构与模块说明.md
│   └── <id>.json（宿主绑定）                  ├── TriCompany-copilot-host-assets/
├── docs/workflow/（公司流程）                  │   └── knowledge/（四层记忆运行时）
└── runtime/cognition/（公司 CLI）             └── ...
```

**发布流向**：
1. 公司侧在 TriCompany 制定治理规则模板 + 员工标准五件套
2. 通过 host-object-publish-flow 发布到项目的 `.github/` 和 `TriCompany-copilot-host-assets/`
3. 项目侧根据宿主类型（Copilot / TriMC / CLI）选择发布策略
4. 项目级治理规则（docs/、README、白皮书等）从公司模板实例化

---

## 6. 与 employee-standard-capabilities.md 的关系

| 维度 | employee-standard-capabilities.md | 本文 |
|------|----------------------------------|------|
| 定位 | 员工通用能力要求（8 维度） | 五件套与四层记忆的映射关系 |
| 读者 | 所有在岗员工 | 治理层 + 技术实现者 |
| 更新频率 | 低（能力维度变化时） | 中（knowledge 层变化时） |
| 关系 | 上游（Section 4 基础版） | 下游（完整展开版） |

当两文档冲突时，以 `employee-standard-capabilities.md` 为准。

---

## 7. 变更记录

- 2026-07-12：V0.1 初版，完整展开五件套↔四层记忆映射，含 llm-wiki 管道、roles/org/audit 全局层说明
- 2026-07-12（CPO/CTO 路由审批后修订）：§3.2 roles/ 新增 MVP baseline——当前单项目阶段至少承载 CPO↔CTO↔总助 三角岗位协作模板与路由边界契约
