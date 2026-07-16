# Employee LLM Wiki 手动吸收操作指南

版本：V0.1
日期：2026-07-13
状态：首版草案（待 CEO / CPO / CTO 联审确认后推广给所有在岗员工）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/employee-llm-wiki-guide.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-07-13

---

## 1. 文档定位

本文定义所有在岗员工（Agent 角色）如何手动操作 LLM-wiki 吸收管道：将零散资料放入 `inbox/` → 编译成体系化 `wiki/` 页面 → 保留吸收痕迹到 `audit/` → 投影到 `workbench/` 知识工作台。

当前阶段仅 **总助（ceo-chief-of-staff）** 拥有完整运行中的 wiki 吸收管道（inbox 5 份资料、wiki 4 页、audit 33 条记录）。其他员工需按本文补齐基础设施后方可启用。

## 2. 前置条件

员工启用 wiki 吸收前，需满足以下最低条件：

1. **四目录存在**：`knowledge/employees/<employee-id>/inbox/`、`wiki/`、`audit/`、`workbench/` 已创建（含 README.md 与模板文件）。
2. **page-specs.json 已定义**：`wiki/page-specs.json` 包含至少一个页面规格（定义哪些 inbox source 归类到哪个 wiki 页）。
3. **llm-wiki-object-spec 已定义**：员工专属的 object spec，定义该员工的 inbox 字段、wiki 页面块结构、audit 记录类型与 promotion 规则。模板参考总助的 `chief-of-staff-llm-wiki-object-spec.md`。
4. **运行时已泛化**：`runtime/cognition/` 下的 wiki_paths、runner、task 已从硬编码 chief-of-staff 泛化为多员工支持。

当前状态：条件 1 已就绪（所有 employee 目录已创建），条件 2-4 待补齐。

### 2.1 当前员工 wiki 能力差距

| 员工 | inbox | wiki | audit | page-specs | llm-wiki-spec |
|------|-------|------|-------|-----------|---------------|
| ceo-chief-of-staff | ✅ 5 | ✅ 4 页 | ✅ 33 条 | ✅ | ✅ |
| chief-product-officer | 空 | 仅消费记录 | 空 | ❌ | ❌ |
| chief-technology-officer | 空 | 仅消费记录 | 空 | ❌ | ❌ |
| rd-trainer | 空 | 仅消费记录 | 空 | ❌ | ❌ |
| chief-administrative-officer | 空 | 空 | 空 | ❌ | ❌ |
| chief-financial-officer | 空 | 空 | 空 | ❌ | ❌ |
| chief-human-resources-officer | 空 | 空 | 空 | ❌ | ❌ |
| chief-marketing-officer | 空 | 空 | 空 | ❌ | ❌ |
| chief-operating-officer | 空 | 空 | 空 | ❌ | ❌ |

> 注：CPO / CTO / rd-trainer 的 `wiki/employee-consumption-records.md` 是员工消费记录（记录会议参与、决策接收等），不是 wiki 吸收产出的知识页。

## 3. 总助当前可用的手动操作命令

以下命令在 `TriCompany/` 根目录或项目根目录下执行，`runtime/cognition/` 模块会自动探测 source root 和 support root。

### 3.1 单页 wiki 刷新

```bash
# 进入 TriCompany 目录（或包含 TriCompany 的项目根）
cd TriCompany

# 刷新指定页面（从 inbox 吸收最新源 → 编译 wiki 页 → 写 audit 记录）
python -m runtime.cognition.chief_of_staff_llm_wiki_refresh \
  --page-id <page-id> \
  --title "页面标题"
```

**参数说明**：
- `--page-id`：page-specs.json 中定义的页面 ID（例如 `governance-routing`、`employee-capability`）
- `--title`：wiki 页面标题

**执行流程**：
1. 从 `inbox/` 读取所有源文件（.md、.txt、.json）
2. 根据 page-specs.json 的 source_filter 规则筛选匹配的源
3. LLM 编译：摘要 + 整理事实 + 判断 + 待确认 + 来源
4. 写入 `wiki/<page-id>.md`
5. 写入 `audit/wiki-refresh-*.json`（审计记录含 run_id、trigger_mode、sources、compile_rules）

### 3.2 批量 wiki 刷新

```bash
# 刷新所有 page-specs.json 定义的页面
python -m runtime.cognition.runners.wiki_batch_refresh_runner

# 只刷新指定页面
python -m runtime.cognition.runners.wiki_batch_refresh_runner --spec-ids page-id-1,page-id-2
```

### 3.3 查看当前 page-specs

```bash
# 查看总助的 page-specs.json 内容
python -c "
import json
from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_wiki_page_specs_path
with open(chief_of_staff_wiki_page_specs_path()) as f:
    specs = json.load(f)
for s in specs.get('pageSpecs', specs.get('pages', [])):
    print(f\"  {s.get('page_id','?')} : {s.get('title','?')}\")
"
```

## 4. Hermes Cron 触发说明

当前 Hermes 的 schedule registry 已配置定时触发规则（位于 `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/schedules/`），但 **Copilot-host 无 7×24 daemon**，定时任务仅在 Agent 处于活跃会话时才能被触发执行。

### 4.1 计划触发与手动触发的区别

| 维度 | 计划触发 (scheduled) | 手动触发 (manual) |
|------|---------------------|-------------------|
| 触发条件 | Hermes cron → schedule-run task | 员工在会话中主动执行 CLI 命令 |
| 执行前提 | Agent 处于活跃会话 | Agent 处于活跃会话（当前唯一方式） |
| audit 记录类型 | `schedule-run-*` | `wiki-refresh-*` |
| 适用场景 | 理想态：7×24 自动吸收 | 当前态：手动触发吸收 |

### 4.2 总助定期手动吸收建议

在 TriMC daemon 模式上线前，建议：

1. **每会话结束时**：运行单页刷新，将本会话积压的 inbox 资料吸收到 wiki。
2. **周度收口时**：运行批量刷新，确保所有 wiki 页面与最新 inbox 同步。
3. **发现 inbox 资料积压超过 3 天**：主动运行批量刷新。

## 5. 扩展其他员工 wiki 吸收的操作步骤

### 5.1 代码泛化（CTO 主导）

当前 `runtime/cognition/chief_of_staff_wiki_paths.py` 硬编码了 `CEO_CHIEF_OF_STAFF_EMPLOYEE_ID`。需要泛化为通用的 `employee_wiki_paths.py`：

```python
# 从硬编码
CEO_CHIEF_OF_STAFF_EMPLOYEE_ID = "ceo-chief-of-staff"

# 泛化为
def employee_knowledge_root(employee_id: str, workspace_root=None) -> Path:
    return support_root(workspace_root) / "knowledge" / "employees" / employee_id
```

同步泛化的模块：
- `runtime/cognition/chief_of_staff_wiki_paths.py` → `runtime/cognition/employee_wiki_paths.py`
- `runtime/cognition/runners/wiki_refresh_runner.py`（`run_chief_of_staff_wiki_refresh` → `run_employee_wiki_refresh`）
- `runtime/cognition/runners/wiki_batch_refresh_runner.py`
- `runtime/cognition/tasks/wiki_ingest_task.py`
- `runtime/cognition/tasks/wiki_compile_task.py`
- `runtime/cognition/kernel/wiki_page_spec_registry.py`

### 5.2 员工专属 llm-wiki-object-spec 创建

以总助的 `chief-of-staff-llm-wiki-object-spec.md` 为模板，每位员工创建自己的 object spec：

- 文件位置：`TriCompany/docs/workflow/<employee-id>-llm-wiki-object-spec.md`
- 关键差异：inbox 字段集（不同岗位关注不同信息类型）、wiki 页面块结构（可调整"判断"→"产品决策"/"技术决策"等）、promotion 规则（不同岗位对 pageStatus: stable 的通过条件不同）

最少需定义的内容：
- inbox 源格式与必填字段
- wiki 页面结构（至少包含：摘要、整理事实、判断/决策、待确认、来源）
- audit 记录类型（至少包含：wiki-refresh、source-ingest、page-promotion）
- 页面 promotion 链：working → reviewing → stable

### 5.3 page-specs.json 初始化

每位员工在 `wiki/page-specs.json` 中定义初始页面规格。最小示例：

```json
{
  "employeeId": "chief-product-officer",
  "pageSpecs": [
    {
      "specId": "product-decisions",
      "pageId": "product-decisions",
      "title": "产品决策记录",
      "description": "CPO 产品判断与决策的持续积累",
      "sourceFilter": { "tags": ["product", "decision", "roadmap"] }
    }
  ]
}
```

### 5.4 员工四目录模板初始化

```bash
# 以 CPO 为例
for dir in inbox wiki audit workbench; do
    mkdir -p "TriCompany-copilot-host-assets/knowledge/employees/chief-product-officer/$dir"
done
```

### 5.5 泛化后 CLI 使用

```bash
# 单员工单页刷新
python -m runtime.cognition.employee_llm_wiki_refresh \
  --employee-id chief-product-officer \
  --page-id product-decisions \
  --title "产品决策记录"

# 单员工批量刷新
python -m runtime.cognition.runners.employee_wiki_batch_refresh_runner \
  --employee-id chief-product-officer
```

## 6. 吸收效果验证

每次刷新后检查：

1. **wiki 页面更新**：`wiki/<page-id>.md` 的 frontmatter 中 `updatedAt` 已刷新、`approvalStatus` 如达条件则晋升
2. **audit 记录落盘**：`audit/wiki-refresh-*.json` 记录了完整的 run_id、sources、compile_rules、output 路径
3. **workbench 快照**：`workbench/index.html` 投影了最新 wiki 页面列表与状态

## 7. 常见问题

**Q: 为什么不能全自动吸收？**
A: Hermes cron 已配置但 Copilot-host 无 7×24 daemon。Cron 任务仅在 Agent 处于活跃会话时才能执行底层 LLM 吸收工作。TriMC daemon 模式上线后将实现全自动吸收。详见 `TriMC/docs/engineering/wiki-absorption-integration-plan.md`。

**Q: 其他员工现在能用吗？**
A: 当前不能。其他员工的 wiki 管道基础设施（泛化 runner、page-specs、llm-wiki-spec）均未就绪。预计在代码泛化（5.1）完成后按优先级逐步开放 CPO → CTO → rd-trainer → 其他岗位。

**Q: 和 employee-consumption-records.md 的区别？**
A: `employee-consumption-records.md` 是员工消费记录（本员工参加了哪些会议、接收了哪些决策、被路由了哪些事项），属于工作台账。wiki 吸收产出的是从 inbox 零散资料中体系化整理的知识页，属于可复用的 LLM 资产。

## 8. 下一步

1. CTO 主导 `runtime/cognition/` 泛化改造（从 chief-of-staff 到通用 employee）
2. CPO / CTO 优先创建各自的 llm-wiki-object-spec（以总助版为模板）
3. CPO / CTO 初始化各自的 page-specs.json
4. 总助在周度收口时将本指南纳入 employee capability contract 的"知识吸收能力"考核项
5. 待 TriMC daemon 模式上线后，本指南的"手动操作"部分降级为备用方案，正式吸收流程由 TriMC task-controller 自动调度
