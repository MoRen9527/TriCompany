# TriCompany 宿主对象生成编排层技术方案 V1.0

**Author**: CTO 小狄
**Date**: 2026-07-14
**Status**: 初版（待与 CPO 对齐非 C-level 员工知识空间范围）
**Reference**: CTO-002 (W29, due 2026-07-17)，解除 BLOCK-003
**Dependencies**: `host_object_generation.py` V0.1、`host-object-publish-flow.md` V0.1、manifest V0.1（11 entries）

> **与 `TriMC/docs/engineering/employee-orchestration-design.md` 的区分**：
> TriMC 那份是**运行时 Agent 派发编排层**（EmployeeRegistry、CapabilityRouter、EmployeeScheduler、CostController、DispatchProxy），负责"任务来了找谁干"。
> 本文是**宿主对象生成管道编排层**，负责"员工上岗时，怎么把源侧五件套 + 岗位定义变成 support payload、binding profile 和 manifest 条目"。
> 两者是上下游关系：先有本文的生成管道产出可用的宿主对象，TriMC 的运行时编排层才能加载和派发。

---

## 1. 设计目标

为 TriCompany 员工宿主对象（host objects）的生成、发布和版本管理建立统一编排层，补齐当前 GENERATE-only 路径的三大缺口：

1. **路径缺口**：当前只有 GENERATE 一条路径。缺少 COPY（原样复制）和 SYMLINK（引用指针）两种轻量路径，导致 binding profiles 和跨仓引用只能手动处理。
2. **注册缺口**：TestEngineer（小柯）和 FullStackDeveloper（小全）已在 manifest JSON 中声明，但未在 Python 代码（`DECLARED_HOST_OBJECT_SETS`、`EMPLOYEE_GENERATORS`、`EMPLOYEE_CHOICES`）中注册，CLI 命令无法生成/发布其宿主对象。
3. **门禁缺口**：缺少从 source-declared-staging 到 current-copilot-host-live 的显式闸门和版本升级规则。

---

## 2. 三条生成路径

### 2.1 路径总览

```
源侧资产                         编排路径                    Support Root 落点
────────                         ────────                   ────────────────
source-agents/<id>/*.md   ──→   GENERATE   ──→   knowledge/{roles,employees}/<id>/**
binding-profiles/<id>.json ──→   COPY       ──→   binding-profiles/<id>.json（随 publish 写入）
contract.yaml              ──→   COPY       ──→   由 contract resolver 消费，不复制到 support root
跨仓文档引用               ──→   SYMLINK    ──→   manifest 中记录 sourceRef，消费侧按引用解析
live discovery entry       ──→   COPY       ──→   TriMetaverse/.github/agents/<id>.agent.md
host-object-manifest.json  ──→   GENERATE   ──→   TriCompany-copilot-host-assets/host-object-manifest.json
```

### 2.2 COPY 路径

**适用场景**：
- Binding profile JSON（源侧已手动编写或由 `write_host_binding_profiles` 生成）
- Live discovery entry（`TriMetaverse/.github/agents/<id>.agent.md`）
- 其他需要在 support root 中有精确副本的静态资产

**技术约束**：
- 不做内容变换，只做存在性 + 路径安全性验证
- 目标路径必须在 `SUPPORT_ROOT_REFERENCE` 范围内
- 源文件不存在时门禁阻断，不静默跳过

**门禁**：
```
Gate C1: 源文件存在性检查 → 源路径可读
Gate C2: 目标路径安全性 → 不越界 SUPPORT_ROOT_REFERENCE
Gate C3: 目标目录可写 → 自动创建父目录
Gate C4: 写入后校验 → 文件大小 > 0，非空
```

**当前实现状态**：
- `write_host_binding_profiles()` 已实现 binding profile 的 COPY 逻辑
- Live discovery entry 当前为手动创建，未纳入自动化编排

### 2.3 SYMLINK 路径

**适用场景**：
- 跨仓文档引用（如 TriMC 引用 TriCompany 源侧设计文档）
- Source-of-truth 文件不应被复制，消费侧应始终读取最新源侧版本

**技术约束**：
- 当前 Copilot-host 阶段不支持操作系统级 symlink（Windows 环境限制 + Copilot-host 非真实文件系统）
- 采用 **Reference Pointer** 语义：在 manifest 的 `sourceRefs` 字段记录引用路径，消费侧按引用解析，不物理复制
- 不产生循环引用（A → B → A 必须被检测并阻断）

**门禁**：
```
Gate S1: 引用目标存在性检查 → 目标路径可解析
Gate S2: 循环引用检测 → 引用链无环
Gate S3: 引用深度限制 → 最多 3 层间接引用
Gate S4: 引用持久化 → manifest sourceRefs 字段完整
```

**当前实现状态**：
- Manifest JSON 的 `sourceDefinitions` 字段已承担 reference pointer 角色
- 但缺少循环引用检测和深度限制
- 非 C-level 员工的 contract.yaml 引用已在 manifest 中声明

### 2.4 GENERATE 路径（当前唯一已实现路径）

**适用场景**：
- Role knowledge workspace（`knowledge/roles/<role-id>/`）目录骨架
- Employee knowledge workspace（`knowledge/employees/<employee-id>/`）目录骨架
- Org shared workspace + audit workspace
- Host object manifest（汇总所有已生成对象集的索引）

**生成器模式**：
```
HostObjectSetDefinition（声明式定义）
  → generate_host_object_set(support_root, definition)
    → KnowledgeWorkspace 四空间创建
    → GeneratedHostObjectSet（产出物句柄）
      → manifest_path
      → role_workspace / employee_workspace / org_shared_workspace / audit_workspace
```

**门禁**：
```
Gate G1: Source Kit Validation → 五件套 + contract.yaml 齐全性
Gate G2: Workspace Generation → 四个知识空间目录创建成功
Gate G3: Binding Profile → source_root 下 binding profile 写入成功
Gate G4: Manifest Consistency → source manifest ↔ support manifest 对称性校验
Gate G5: CHO Governance → 新员工上岗必须经 CHO 审批（见 §4.4）
```

**当前实现状态**：
- 9 个 C-level 员工已完整注册（`DECLARED_HOST_OBJECT_SETS`）
- `generate_host_object_set()` 通用函数可复用
- TestEngineer 和 FullStackDeveloper 的 `HostObjectSetDefinition` 待定义

---

## 3. 非 C-level 员工注册设计

### 3.1 当前 Gap

| 组件 | C-level（9人） | TestEngineer | FullStackDeveloper |
|------|--------------|-------------|-------------------|
| Source manifest entry | ✅ | ✅ | ✅ |
| Support manifest entry | ✅ | ✅ | ✅ |
| Source agent kit (5 files) | ✅ | ✅ | ✅ |
| Contract YAML | ✅ (部分) | ✅ | ✅ |
| Binding profile JSON | ✅ | ✅ | ✅ |
| Live discovery entry | ✅ | ✅ | ✅ |
| `HostObjectSetDefinition` | ✅ | ❌ | ❌ |
| `DECLARED_HOST_OBJECT_SETS` | ✅ | ❌ | ❌ |
| `EMPLOYEE_GENERATORS` | ✅ | ❌ | ❌ |
| `EMPLOYEE_CHOICES` | ✅ | ❌ | ❌ |
| Generator function | ✅ | ❌ | ❌ |

### 3.2 注册模板

非 C-level 员工遵循与 C-level 相同的 `HostObjectSetDefinition` 模式：

```python
TEST_ENGINEER_OBJECT_SET_ID = "test-engineer-knowledge-workspace-v0.1"
FULL_STACK_DEVELOPER_OBJECT_SET_ID = "full-stack-developer-knowledge-workspace-v0.1"

TEST_ENGINEER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=TEST_ENGINEER_OBJECT_SET_ID,
    role_id="TestEngineer",
    employee_id="test-engineer",
    owner_role="TestEngineer",
    source_refs=(
        *source_agent_kit_refs("test-engineer"),
        "TriCompany/docs/registry/TestEngineer.contract.yaml",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
    ),
    role_description="Role-level reusable test engineering knowledge for the TestEngineer role.",
    employee_description="Employee-instance working knowledge for the current test-engineer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee test-engineer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "TestEngineer is current Copilot-host live enabled and owns test design, test execution, and quality gate enforcement.",
        "TestEngineer live discovery target is TriMetaverse/.github/agents/test-engineer.agent.md.",
        "TestEngineer reports to CPO (product quality direction) and CTO (technical quality standards).",
        "This is current Copilot-host live enablement plus TriCompany source-side handoff, not a TriMC formal host switch.",
    ),
    employee_display_name="小柯",
    live_entry_ref="TriMetaverse/.github/agents/test-engineer.agent.md",
)

FULL_STACK_DEVELOPER_HOST_OBJECT_SET = HostObjectSetDefinition(
    object_set_id=FULL_STACK_DEVELOPER_OBJECT_SET_ID,
    role_id="FullStackDeveloper",
    employee_id="full-stack-developer",
    owner_role="FullStackDeveloper",
    source_refs=(
        *source_agent_kit_refs("full-stack-developer"),
        "TriCompany/docs/registry/FullStackDeveloper.contract.yaml",
        "TriCompany/docs/engineering/role-employee-knowledge-workspace.md",
    ),
    role_description="Role-level reusable full-stack development knowledge for the FullStackDeveloper role.",
    employee_description="Employee-instance working knowledge for the current full-stack-developer live employee.",
    generator="python -m runtime.cognition.employee_host_object_generation --employee full-stack-developer",
    live_entry_status="current-copilot-host-live",
    host_stage="current-copilot-host-live",
    notes=(
        "FullStackDeveloper is current Copilot-host live enabled and reports to CTO.",
        "FullStackDeveloper live discovery target is TriMetaverse/.github/agents/full-stack-developer.agent.md.",
        "FullStackDeveloper handles concrete coding tasks delegated by CTO; TestEngineer validates deliverables.",
        "This is current Copilot-host live enablement plus TriCompany source-side handoff, not a TriMC formal host switch.",
    ),
    employee_display_name="小全",
    live_entry_ref="TriMetaverse/.github/agents/full-stack-developer.agent.md",
)
```

### 3.3 注册后的影响范围

加入 `DECLARED_HOST_OBJECT_SETS` 后自动获得：
- `employee_host_object_generation.py --employee test-engineer` CLI 可用
- `employee_host_publish.py --employee test-engineer` CLI 可用
- `generate_all_declared_employee_host_objects()` 全量生成覆盖
- `DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE` 查询可用
- Manifest 一致性校验覆盖

---

## 4. 本地宿主生成闸门（5-Gate Pipeline）

### 4.1 闸门总览

```
Source Kit        Gate 1        Gate 2         Gate 3        Gate 4         Gate 5
  (五件套)    →  Source     →  Generation  →  Binding    →  Manifest    →  Governance
                 Check         Check          Check         Check          Check
                 
  状态:          source-       generated-     binding-      manifest-      current-
                 declared      staging        verified      consistent     copilot-host-live
```

### 4.2 Gate 1: Source Check

| 检查项 | 方法 | 阻断级别 |
|--------|------|---------|
| 五件套齐全性 | `source_agent_kit_refs()` 返回 5 个路径，逐一 `Path.exists()` | 🔴 阻断 |
| Contract YAML 可解析 | Contract resolver 加载不抛异常 | 🔴 阻断 |
| Soul/memory/colleagues/social 不含运行消费记录 | 文本扫描不含 runtime path 写入 | 🟡 警告 |
| 五件套在 `source-agents/` 不在 `agents/` | 路径前缀校验 | 🔴 阻断 |
| 无越界引用 | source_refs 全部在 TriCompany 仓库内 | 🟡 警告 |

### 4.3 Gate 2: Generation Check

| 检查项 | 方法 | 阻断级别 |
|--------|------|---------|
| 四空间目录创建成功 | `KnowledgeWorkspace` 四空间 Path.is_dir() | 🔴 阻断 |
| Workspace 骨架文件齐全 | inbox/wiki/audit/workbench 子目录存在 | 🟡 警告 |
| Object set ID 唯一 | 不与已有 objectSetId 冲突 | 🔴 阻断 |
| 生成产物非空 | GeneratedHostObjectSet 所有 Path 非 None | 🔴 阻断 |

### 4.4 Gate 3: Binding Check

| 检查项 | 方法 | 阻断级别 |
|--------|------|---------|
| Binding profile JSON 写入成功 | Path.exists() + JSON 可解析 | 🔴 阻断 |
| employee_id 与 manifest 一致 | JSON.employeeId == definition.employee_id | 🔴 阻断 |
| display_name 非空 | JSON.displayName is not None | 🟡 警告 |
| live_entry_ref 指向正确路径 | 路径存在且为 .agent.md 文件 | 🟡 警告 |

### 4.5 Gate 4: Manifest Check

| 检查项 | 方法 | 阻断级别 |
|--------|------|---------|
| Source manifest 包含该 objectSetId | 在 tricompany-host-object-generation-manifest.json 中存在 | 🔴 阻断 |
| Support manifest 包含该 objectSetId | 在 host-object-manifest.json 中存在 | 🔴 阻断 |
| 双 manifest 字段对称 | objectSetId/status/supportObjects 一致 | 🔴 阻断 |
| Generator 命令可执行 | CLI --help 返回 0 | 🟡 警告 |

### 4.6 Gate 5: Governance Check（CHO 审批门）

| 检查项 | 方法 | 阻断级别 |
|--------|------|---------|
| 新员工上岗经 CHO 审批 | CHO approval record 存在于 governance log | 🔴 阻断 |
| 上岗流水线全绿 | unresolved-items.md 上岗状态表全部 ✅ | 🔴 阻断 |
| Display name 已分配 | employeeDisplayName 非空且不与现有冲突 | 🔴 阻断 |
| 汇报链明确 | contract.yaml reports_to 字段非空 | 🟡 警告 |

**CHO 审批门说明**：
- 新员工首次上岗（source-declared-staging → current-copilot-host-live 首次转换）必须经 CHO 审批
- 现有员工职责变更（五件套内容更新但 objectSetId 不变）不需要重新审批，但需要 Gate 1-4 重新通过
- 版本升级（v0.1 → v0.2）需要 CHO 知会但不需要重新审批
- 下岗/挂起操作由直属上级或 CHO 发起，不在本生成管道范围内

---

## 5. 版本策略

### 5.1 objectSetId 版本号规则

格式：`<employee-id>-knowledge-workspace-v<MAJOR>.<MINOR>`

| 变更类型 | 版本动作 | 示例 |
|---------|---------|------|
| 源侧定义变更，对象结构不变（如 notes 更新、source_refs 追加） | 不升级版本号，仅更新 `updatedAt` | `v0.1` 保持不变 |
| 源侧定义变更，对象结构变化（如新增 workspace 类型、改变目录布局） | 升 MINOR：`v0.1` → `v0.2` | 新增 runtimeNamespaces |
| 岗位职责重大变更（如 employee_id 变化、owner_role 迁移） | 升 MAJOR：`v0.1` → `v1.0` | 岗位重构 |
| 对象集废弃（被新 objectSetId 替代） | 旧版标记 `deprecated`，`replaces_object_set_ids` 指向新版 | `rd-trainer` 替代 `project-trainer` |

### 5.2 Support Root 版本留存策略

- Support root 只保留当前 active 版本的 payload
- 旧版本 payload 在升级时**归档**到 `TriCompany-copilot-host-assets/archive/<objectSetId>/` 而非直接删除
- 归档保留期：3 个版本或 90 天，取较长者
- `replaces_object_set_ids` 记录的旧 objectSetId 的 support payload 在升级时清理

### 5.3 版本升级流程

```
1. 在 source manifest 中新增新版 objectSetId entry（保留旧版标记 deprecated）
2. 在 host_object_generation.py 中新增新版 HostObjectSetDefinition
3. 运行 generate → 新版 support payload 落盘
4. 运行 Gate 1-5 → 全部通过
5. 旧版 support payload 归档
6. 更新 support manifest：新版 status=current-copilot-host-live，旧版 status=deprecated
7. 更新 DECLARED_HOST_OBJECT_SETS：新定义 replaces_object_set_ids 指向旧版
```

---

## 6. 实现计划

### Phase A（CTO-002 交付，due 7/17）：补齐注册 + 闸门框架

| 任务 | 产出 | 验证 |
|------|------|------|
| A1. 注册 TestEngineer HostObjectSetDefinition | `host_object_generation.py` 新增 ~40 行 | `--employee test-engineer` CLI 可执行 |
| A2. 注册 FullStackDeveloper HostObjectSetDefinition | `host_object_generation.py` 新增 ~40 行 | `--employee full-stack-developer` CLI 可执行 |
| A3. 加入 DECLARED_HOST_OBJECT_SETS | 9 → 11 条目 | `generate_all_declared_employee_host_objects()` 覆盖 11 人 |
| A4. 注册 EMPLOYEE_GENERATORS | `employee_host_object_generation.py` 新增 2 条目 | CLI --employee choices 包含 test-engineer + full-stack-developer |
| A5. EMPLOYEE_CHOICES 自动扩展 | `DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE` 自动填充 | `--employee test-engineer` publish 可用 |
| A6. Gate 1 Source Check 脚本化 | `runtime/cognition/host_object_generation_gates.py` | 独立脚本验证五件套齐全性 |

### Phase B（W30）：闸门自动化 + 版本升级工具

| 任务 | 产出 |
|------|------|
| B1. Gate 2-5 自动化 | `host_object_generation_gates.py` 扩展 |
| B2. 版本升级 CLI | `--upgrade-version <old> <new>` 子命令 |
| B3. Archive 机制 | 旧版 support payload 归档脚本 |

### Phase C（W31+）：CI 集成 + 仪表盘

| 任务 | 产出 |
|------|------|
| C1. GitHub Actions workflow | 新员工上岗自动触发 Gate 1-5 |
| C2. 仪表盘数据源 | 员工上岗状态实时查询 API |

---

## 7. 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 非 C-level 员工是否独立定义 | 是，使用相同 `HostObjectSetDefinition` 模式 | 保持一致性，复用 `generate_host_object_set()` |
| SYMLINK 用 reference pointer 而非 OS symlink | Reference pointer | Copilot-host 无真实文件系统，Windows 不支持 symlink |
| 版本号粒度 | MAJOR.MINOR（岗位重构.结构变化） | 足够区分，不引入 PATCH 过度粒度 |
| 归档 vs 删除 | 归档保留 3 版本/90 天 | 可回滚，不永久堆积 |
| CHO 审批是闸门还是旁路 | 闸门（Gate 5，阻断级） | CEO 明确要求"新员工上岗应该 CHO 审批才算正式上岗" |
| Generator 函数是否自动生成 | Phase A 手动定义，Phase C 模板化 | 当前只有 2 个非 C-level，手动定义成本低 |
| EMPLOYEE_CHOICES 是否手动维护 | 从 DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE 自动派生 | 消除手动同步负担 |

---

## 8. 风险与缓解

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| TestEngineer/FullStackDeveloper 的 contract.yaml 可能不完整 | 🟡 Medium | Gate 1 包含 contract 可解析性检查，不通过则阻断 |
| 非 C-level 员工的 source-agents 五件套可能缺少某些文件 | 🔴 High | Phase A 先检查齐全性，缺失则先补齐再注册 |
| EMPLOYEE_GENERATORS 手动同步可能遗漏 | 🟡 Medium | Phase B 改为从 DECLARED_HOST_OBJECT_SETS 自动派生 |
| 版本归档占用磁盘 | 🟢 Low | 90 天自动清理 + 3 版本上限 |
| CHO 审批可能成为瓶颈 | 🟡 Medium | 上岗审批是 CEO 明确要求的安全门，不可绕过；通过自动化 Gate 5 脚本减少人工检查成本 |

---

## 9. 使用依据

- `TriCompany/docs/workflow/host-object-publish-flow.md` — 11 步发布流程
- `TriCompany/runtime/cognition/host_object_generation.py` — HostObjectSetDefinition、DECLARED_HOST_OBJECT_SETS（9 条目）
- `TriCompany/runtime/cognition/employee_host_object_generation.py` — EMPLOYEE_GENERATORS（9 条目）
- `TriCompany/runtime/cognition/employee_host_publish.py` — EMPLOYEE_CHOICES + publish 流程
- `TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json` — Source manifest（11 entries）
- `TriCompany-copilot-host-assets/host-object-manifest.json` — Support manifest（11 entries）
- `TriCompany/.github/source-agents/test-engineer/` — TestEngineer 五件套
- `TriCompany/.github/source-agents/full-stack-developer/` — FullStackDeveloper 五件套
- `TriCompany/docs/registry/TestEngineer.contract.yaml` — TestEngineer 岗位契约
- `TriCompany/docs/registry/FullStackDeveloper.contract.yaml` — FullStackDeveloper 岗位契约
- `TriMC/docs/engineering/employee-orchestration-design.md` — 运行时派发编排层（区分 scope）
- `TriCompany/docs/engineering/DESIGN.md` — TriCompany 技术设计
- `docs/workflow/operating-records/2026-W29/OP-202607-W29-001.unresolved-items.md` — BLOCK-003 定义
- CEO 指示："新员工上岗应该 CHO 审批才算正式上岗"
