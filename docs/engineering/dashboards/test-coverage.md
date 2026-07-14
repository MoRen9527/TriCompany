# 测试覆盖仪表盘 — W29 首版

- 状态：✅ 首版回填（CARRY-006-1）
- 快照日期：2026-07-14（W29）
- 维护归属：CTO（小狄）
- 上游依据：TriMC Phase 1+2 执行记录、TriModel provider 注册

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/dashboards/test-coverage.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-07-14

---

## 1. 总体概览

| 指标 | 当前值 | 目标 | 状态 |
|------|--------|------|------|
| 总测试数 | **70** | 100+ | 🟡 |
| TriMC 测试 | 55 | — | ✅ |
| TriModel 测试 | 15 | — | ✅ |
| 模块数 | 2（TriMC, TriModel） | 5+ | 🟡 |
| 覆盖类型 | 单元测试 + 集成测试 | + E2E | 🟡 |
| CI 集成 | ❌ 无 | GitHub Actions | 🔴 |

## 2. 模块明细

### 2.1 TriMC（55 测试，9 文件）

| 测试文件 | 类型 | 覆盖范围 | 状态 |
|----------|------|----------|------|
| `agent-tools.test.ts` | Unit + Integration | 6 tools（read/write/edit/glob/shell/task） | ✅ |
| `agent-sse.test.ts` | Integration | SSE streaming endpoint | ✅ |
| `chat-endpoint.test.ts` | Integration | `/internal/v1/chat` endpoint | ✅ |
| `contract-resolver.test.ts` | Unit | Agent contract resolver（17/17） | ✅ |
| `benchmarkGate.test.ts` | Unit | Benchmark gate logic | ✅ |
| `benchmarkSummary.test.ts` | Unit | Benchmark summary generation | ✅ |
| `observabilityMapper.test.ts` | Unit | Observability event mapping | ✅ |
| `timelineReplayApi.test.ts` | Integration | Timeline replay API | ✅ |
| `weeklyReportTemplate.test.ts` | Unit | Weekly report template | ✅ |

### 2.2 TriModel（15 测试，5 suites）

| Suite | 覆盖范围 | 状态 |
|-------|----------|------|
| Provider registry | DeepSeek + TriStaciss registration | ✅ |
| DeepSeekProvider | chat(), healthCheck(), timeout handling | ✅ |
| TriStacissProvider | TriStaciss API compatibility | ✅ |
| ModelClient | createModelClient(), model listing, fallback | ✅ |
| Config | readConfig() env parsing | ✅ |

## 3. 未覆盖区域（W29 识别）

| 缺口 | 优先级 | 负责人 | 说明 |
|------|--------|--------|------|
| `agent-loop` 核心无独立测试 | HIGH | 小全（FullStack） | Agent loop 仅通过 agent-tools 间接测试 |
| TaskController 无测试 | HIGH | 小全 | 当前仅 acceptPlaceholder() |
| E2E 测试 | MEDIUM | 小柯（TestEngineer） | 尚无端到端场景测试 |
| TriDeployment 无测试 | MEDIUM | — | 部署工具未纳入测试体系 |
| CI 集成 | MEDIUM | CTO | 无 GitHub Actions 自动运行 |
| PostgreSQL 集成测试 | LOW | 小全 | 需要 pg 实例 |
| 性能回归 | LOW | — | 无基准对比 |

## 4. 下一快照目标（W30）

- [ ] 补齐 agent-loop 独立单元测试（小全）
- [ ] 补齐 TaskController 测试（小全）
- [ ] 为 TriDeployment tools 添加基本单元测试
- [ ] 小柯完成首轮验证报告并回填

## 5. 历史快照

| 快照 | 日期 | TriMC | TriModel | 总计 | Delta |
|------|------|-------|----------|------|-------|
| W29 | 2026-07-14 | 55 | 15 | 70 | 基线 |
