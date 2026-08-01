# CTO 经营节奏 — 技术经营收口

- 版本：V0.1
- 日期：2026-07-24（W30）
- 状态：Phase D B1 — CTO 经营节奏定义
- 维护归属：CTO（小狄）
- 与 COS 的关系：本文件定义 CTO 向 CEOChiefOfStaff 提交的技术经营 input 的结构与节奏，不替代 COS 的经营记录系统

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/operating-review-cycle.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-07-24

---

## 1. 定位

本文档定义 **CTO 的周度技术经营节奏**。它不是经营记录本身（经营记录归属 CEOChiefOfStaff 的 `operating-records/`），而是 CTO 在每轮经营收口时应当提交的结构化 input。

核心原则：
- **收口触发**：每周至少一次，由 COS 的经营节奏驱动（而非 CTO 自行决定收口时机）
- **输入方向**：CTO → COS（技术事实 + 质量判断 + 风险升级）
- **不替代**：本文档不替代 COS 的经营记录系统，不创建平行的经营流

---

## 2. 周度检查项（Engineering Quality Gate）

CTO 每周必须对以下四项门禁做结构化的通过/失败/告警判断。每项门禁的具体实现由 `runtime/cognition/dispatch/dispatch_scheduler.py` 的 `run_quality_gate()` 提供自动化执行入口。

### 2.1 测试门禁

| 维度 | 说明 |
|------|------|
| 检查内容 | 全部现役模块的测试套件通过率 |
| 数据源 | pytest（TriCompany）、`npm test`（TriMC、TriModel） |
| 目标 | 100% pass，0 skip（可接受已标注的 CONDITIONAL_PASS） |
| 门禁 | fail < 1 → PASS；fail ≥ 1 → FAIL；skip > 允许阈值 → WARN |

### 2.2 管线门禁

| 维度 | 说明 |
|------|------|
| 检查内容 | CTO-002 Publish Pipeline 完整性 + TriMC `tsc` 类型检查 |
| 数据源 | `host_object_generation.py publish` 输出 + `tsc --noEmit` 结果 |
| 目标 | 11/11 host objects 生成成功，类型检查零错误 |
| 门禁 | 全部通过 → PASS；任一失败 → FAIL；结果陈旧（>7 天） → WARN |

### 2.3 CodeGraph 门禁

| 维度 | 说明 |
|------|------|
| 检查内容 | CodeGraph 索引新鲜度 |
| 数据源 | `codegraph_status` / `.codegraph/codegraph.db` 时间戳 vs HEAD |
| 目标 | 索引领先于或等于最新 commit |
| 门禁 | 新鲜 → PASS；stale（>5 commits behind） → WARN；无索引 → FAIL |

### 2.4 Registry Drift 门禁

| 维度 | 说明 |
|------|------|
| 检查内容 | CodeRegistry 与 CodeGraph 是否一致；source publish check 状态 |
| 数据源 | `source_publish_check --check --format json` 输出 |
| 目标 | out_of_sync = 0（全部 in_sync） |
| 门禁 | out_of_sync = 0 → PASS；out_of_sync > 0 → FAIL；gaps_only → WARN |

---

## 3. 周度输出物（CTO → COS）

CTO 在每轮经营收口时，应向 COS 提交以下结构化 input：

| 序号 | 输出物 | 内容 | 格式 |
|------|--------|------|------|
| E1 | 质量门禁快照 | 四项门禁的 PASS/FAIL/WARN + 关键数据 | JSON blob（由 `run_quality_gate()` 生成） |
| E2 | 管线成熟度变更 | pipeline-maturity.md 的 delta（如有变更） | 简要 diff 摘要 |
| E3 | 测试覆盖变更 | test-coverage.md 的 delta（如有变更） | 简要 diff 摘要 |
| E4 | CTO 经营判断 | 当前技术风险、blocker、是否需要缩范围/升级 | 纯文本摘要 |

---

## 4. 与 COS 经营收口的流程衔接

```
COS 启动经营收口
  │
  ├─→ CTO 执行 run_quality_gate()           ← dispatch_scheduler.py
  │     ├─ 测试门禁
  │     ├─ 管线门禁
  │     ├─ CodeGraph 门禁
  │     └─ Registry Drift 门禁
  │
  ├─→ CTO 生成结构化 input（E1-E4）
  │
  └─→ COS 收入 operating-records/
        └─ 标注 CTO input 已纳入本周经营记录
```

CTO 不直接写入 COS 的 `operating-records/`。CTO 提交 input 后，由 COS 决定如何纳入经营记录、是否需要补充裁决或升级到 CEO。

---

## 5. 经营升级规则

CTO 在以下情况应将技术判断升级到 COS/CEO：

| 触发条件 | 升级级别 | 说明 |
|----------|----------|------|
| 任一模块测试 fail > 0 且非 CONDITIONAL_PASS | ESCALATE | 阻塞交付 |
| CTO-002 Publish Pipeline 失败 | ESCALATE | 宿主资产不同步 |
| CodeGraph 索引缺失（非 stale） | ESCALATE | 无法做结构分析 |
| Registry drift out_of_sync > 3 | FREEZE → ESCALATE | 先冻结交付，评估是否需要紧急 sync |
| 连续两周同一门禁 WARN | FREEZE | 先解决再继续 |

---

## 6. 自动化执行入口（Phase D B1→B2）

| 阶段 | 内容 | 状态 |
|------|------|------|
| B1 | `dispatch_scheduler.py` shell + 门禁定义 + no-op 质量检查表 | 本周 |
| B2 | 接真实数据源（pytest、tsc、codegraph、source_publish_check） | 下周 |

B1 的 `dispatch_scheduler.py` 提供：
- `QualityGateResult` dataclass（pass/fail/warn + data）
- 四个独立的 `check_*()` 函数（B1 期返回占位结果）
- `run_quality_gate()` 聚合入口（B1 期调用四个 check 并返回结构化报告）
- `--help` 可执行，无参数调用输出当前 no-op 质量快照

B2 将：
- 把每个 `check_*()` 接入真实数据源
- 增加 `--ci` 模式（适合 GitHub Actions）
- 增加 `--output` 选项（写入 JSON 文件供 COS 消费）

---

## 7. 历史快照

| 快照 | 日期 | 测试 | 管线 | CodeGraph | Drift | 备注 |
|------|------|------|------|-----------|-------|------|
| W30-B1 | 2026-07-24 | no-op | no-op | no-op | no-op | 门禁定义完成，B2 接真实数据 |
