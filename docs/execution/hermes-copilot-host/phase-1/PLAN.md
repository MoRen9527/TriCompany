# Hermes Copilot Host Phase 1 Plan

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/execution/hermes-copilot-host/phase-1/PLAN.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- executionTier: stable-execution-summary
- linkedSupportEvidence: TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/PLAN.md
- supportSyncRule: support 同名文档保留为 phase evidence，不执行 same-name published-copy 追平
- lastSyncedAt: 2026-04-28

日期：2026-04-16
状态：已启动

## 目标

在 TriCompany 内完成当前阶段的 Hermes 融合与 Copilot 宿主迁移口径收拢。

## 本阶段范围

- 重置 TriCompany 路线文案
- 补齐 Hermes 融合设计
- 建立 vendor/reference 的 Hermes 冻结参考副本
- 建立 runtime/cognition 的元认知原型骨架
- 把当前阶段 Copilot 宿主资产统一收拢到 .github
- 设计回迁 TriMetaverse/.github 的 shadow-test manifest
- 同步 registry 状态到新口径

## 输入

- 用户最新确认的新路线
- TriCompany 当前文档与总助套件
- Hermes 研究结论

## 输出

- 更新后的 README、产品路线和技术路线
- 更新后的总助套件与 registry 状态
- 当前阶段 Hermes 融合与宿主迁移规则文档
- vendor/reference/hermes-agent-memory/ 冻结参考副本
- runtime/cognition/ 元认知 contracts、kernel、providers 骨架
- .github/manifests/tri-metaverse-backport.json

## 验收方式

- 核对当前路线是否统一改为“先 TriCompany 融 Hermes，再 .github 宿主迁移”
- 核对 .github 宿主资产是否在文档里被写清
- 核对元认知层是否已明确为“统一内核 + 员工私域 + 组织共享”
- 核对回迁清单是否采用 shadow-test 而非直接覆盖
- 核对没有把试运行口径误写成正式宿主切换
