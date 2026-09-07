# 任务书：FADE-002 event-watch 检测面生产接线（TriCompany 域）

- 任务书编号：task-20260907-TriCompany-event-watch
- 状态：**草案 v1**（2026-09-07，RDT 小吴起草；未成熟任务方案，落 docs/engineering 候审——成熟后移 docs/execution 并挂周工作平面，落点生命周期见《治理提案集 20260907》提案 A）
- 派单缘起：CEO 席直入定调（2026-09-06/07）：先接线检测半边攒数据，`--auto-sync` 写半边评审后另令
- 域：TriCompany（非跨模块）；执行域 owner 候 CTO 确认（D-15 路由）

## 一、目标

把 FADE-002 的 event-watch 检测面从"建成待接线"（代码在役、无排程）推到"现役检测排程"：

- **阶段一（本任务书全部范围）**：注册**不带** `--auto-sync` 的检测排程——cron 周期唤起单次扫描（`--event-watch`），纯只读链：扫描指纹→去重→派生 scope→dry-run 检查→建议→审计落 `.ade/event-watch/`。
- **阶段二（另令候选，本任务书只产出评审输入）**：攒 2-4 周批次数据后评审 `--auto-sync` 预授权——阈值/关键文件现值定稿、误报率读数、演练一次"判据满足→真写→复核"闭环、CTO 方案件+董事会知会。

## 二、范围边界

**做**：服务器侧 cron 注册检测排程；批次审计样本采集；建议质量周报机制。
**不做**：任何 `--auto-sync` 真写（阶段二另令）；project-docs 域任何自动写（协议 §2.4 焊死，永久边界）；宿主渲染面变更；event-watch 与业务 scope 旗标组合（互斥校验，架构不动）。

## 三、原材料指针（全部实勘锚）

| 材料 | 位置 | 用途 |
| --- | --- | --- |
| 执行体 | `runtime/cognition/source_publish_check.py` 触发面参数族（`--event-watch`/`--watch`/`--interval`/`--watch-dirs`/`--sync-threshold`/`--audit-dir`/`--state-file`） | 行为契约 |
| 协议 | `docs/engineering/fade-protocol-spec.md` §8.6 触发链两模式、§2.4 安全门 | 排程形态依据 |
| 判据现值 | sync-threshold 默认 5；关键文件=两份 manifest / `.agent.md` 后缀 | 阶段二评审基线 |
| 服务器 cron 运维 | TriMMC `docs/ops/trimc-cron-plane-shift-runbook.md`（cron add 语法、36 位全量 UUID、`cron update` 丢 tz 坑） | 注册操作手册 |
| 教程 | `docs/training/fade-002/02-product-guide.md` 旅程 C、`03-code-map.md` §九 | 实施者入门 |
| 登记 | `docs/engineering/fade-registry.md` FADE-002 补齐项（automation-backlog 裁决锚） | 治理依据 |

## 四、验收期望（Score 试卷素材源）

1. cron job 注册读数：API `GET /internal/v1/cron/jobs` 示 id/nextRun/lastRunStatus=ok（36 位全量 UUID 入账）。
2. 连续 2 周批次审计样本：`events.jsonl` + 批次 envelope 落盘齐备，建议判定可复算（变更数/关键文件命中可对照 git log 验证）。
3. 建议质量周报：误报/漏报读数（对照同期人工发布窗实际动作），含 deduped 防噪读数。
4. 阶段二评审输入包成稿：数据汇总+阈值/关键文件修订建议+预授权风险清单。

## 五、段-实现绑定（候挂平面形态）

事件触发=cron 周期唤起；登记=jobId+per-run 日志；DCE=`source_publish_check --event-watch`（只读形态）；Verify=job lastRunStatus 晨检断言（齿条③同款扩展）；Close=阶段一收官=审计样本齐+周报机制在役。挂平面形态（trees 任务书 vs 常驻 job）候联审定——本任务书当前以文档形态存在，若走 FADE-006 自动拾取需转 tree-op.json 并满足三重门（status=active/server-executable/pending 无时间门+face 路由）。

## 使用依据

- CLI 触发面参数族与互斥校验：2026-09-05/06 实读（build_parser L3033-3286）
- 判据/审计/防噪语义：`--auto-sync` help 原文、`test_project_docs_never_executes_with_auto_sync` 等负例、event-watch 测试族
- 两步走策略：CEO 席直入定调（2026-09-06 晚+2026-09-07 追问轮）
