# TriCompany 技术状态

版本：V0.1
日期：2026-04-27
状态：已完成 Supermemory 官方 schema、SDK seam 与 live smoke 验证，并补回 chief-of-staff workflow / schedule source 入口

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/STATE.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/STATE.md
- supportSyncRule: 仅在成批发布或当前宿主重新显式依赖时追平 support 副本
- lastSyncedAt: 2026-04-28

## 当前实现阶段

- 当前是 docs-first + .github 宿主资产并行的研发阶段
- 当前承载的是试运行 Copilot 宿主资产，不是正式宿主部署

## 当前结构资产

- 产品文档基线已建立
- 技术文档基线已建立
- registry 状态文档已建立
- 总助 agent 套件已建立
- 会议 prompt 已建立
- 当前阶段 Copilot 宿主资产已收拢在 .github 下
- Hermes 核心 memory 代码已冻结到 vendor/reference
- runtime/cognition 的 contracts、kernel、providers 骨架已建立
- runtime/cognition 已补齐 smoke_test.py，并可在仓库根目录通过 python -m runtime.cognition.smoke_test 直接验证
- runtime/cognition 已补齐 contract_validation.py，并可在仓库根目录通过 python -m runtime.cognition.contract_validation 直接验证 Hermes 核心契约
- runtime/cognition 已补齐 integration_validation.py，并可在仓库根目录通过 python -m runtime.cognition.integration_validation 直接验证 provider-backed 落盘与跨实例 recall
- runtime/cognition 已补齐 backend_validation.py，并可在仓库根目录通过 python -m runtime.cognition.backend_validation 直接验证后端落盘与审计元数据
- runtime/cognition 已补齐 external_validation.py，并可在仓库根目录通过 python -m runtime.cognition.external_validation 直接验证模拟外部后端兼容性
- runtime/cognition 已补齐 http_backend_validation.py，并可在仓库根目录通过 python -m runtime.cognition.http_backend_validation 直接验证 HTTP 外部后端认证与网络行为
- runtime/cognition 已补齐 supermemory_validation.py，并可在仓库根目录通过 python -m runtime.cognition.supermemory_validation 直接验证 Supermemory 官方 schema、429 retry 与错误体解析
- runtime/cognition 已补齐 supermemory_sdk_validation.py，并可在仓库根目录通过 python -m runtime.cognition.supermemory_sdk_validation 直接验证 Supermemory 官方 SDK seam 的参数映射与 provider 生命周期联动
- runtime/cognition 已补齐 supermemory_live_validation.py，作为显式 opt-in 的 live smoke 入口；默认不执行，待真实 Supermemory API key 下启用
- runtime/cognition 已把 chief-of-staff approval report、task_resolver、cron_runner / resident_runner、knowledge workbench 回写到 source，并已形成 source 侧 schedule 执行链
- runtime/cognition 已补齐 chief_of_staff_schedule_staging.py 与 chief_of_staff_schedule_staging_validation.py，并可在仓库根目录通过 python -m runtime.cognition.chief_of_staff_schedule_staging --help 与 python -m unittest runtime.cognition.chief_of_staff_schedule_staging_validation 验证 resident runner -> cron runner -> task resolver -> approval report / workbench / closeout 链路
- runtime/cognition 已补齐 chief_of_staff_workflow_bridge.py 与 chief_of_staff_workflow_validation.py，并可在仓库根目录通过 python -m unittest runtime.cognition.chief_of_staff_workflow_validation 验证开始会议 / 结束会议 / 日常收口写回、repo memory 双向同步与 host hook 自动补一次 sync-memory 的模拟链路
- runtime/cognition 已补齐 chief_of_staff_workflow_sync_hook.py，把 workflow hook 的 command 识别、stdin 解析与 `sync-memory` 调度纯逻辑收回 source；TriMetaverse `.github/hooks/ceo-chief-of-staff-workflow-sync.py` 当前只保留宿主 thin wrapper，并已复跑 python -m unittest runtime.cognition.chief_of_staff_workflow_validation 继续通过
- runtime/cognition 已保留 chief_of_staff_bridge_validation.py，作为 repo-backed durable assets 与同一 cognition kernel 桥接的 source 侧回归入口
- runtime/cognition 已补齐 chief_of_staff_resident_runner.py 与 chief_of_staff_operating_review_closeout.py，并可在仓库根目录通过 python -m runtime.cognition.chief_of_staff_resident_runner --help 与 python -m runtime.cognition.chief_of_staff_operating_review_closeout --help 验证顶层 CLI 入口
- runtime/cognition 已补齐 chief_of_staff_registry_closeout_validation.py 与 chief_of_staff_operating_review_closeout_validation.py，并可在仓库根目录通过 python -m unittest runtime.cognition.chief_of_staff_registry_closeout_validation 与 python -m unittest runtime.cognition.chief_of_staff_operating_review_closeout_validation 验证 registry closeout 与 operating review closeout bridge 链路
- runtime/cognition 已补齐 chief_of_staff_wiki_batch_refresh.py，并可在仓库根目录通过 python -m runtime.cognition.chief_of_staff_wiki_batch_refresh --help 验证顶层 batch refresh CLI 入口；当前可见 top-level `chief_of_staff_*.py` 入口已与 support bundle 对齐

## 当前技术风险

- 记忆分层目前仍以 markdown 资产表达为主，尚未形成真正的运行时 Cognition 层
- 本地 provider-backed 集成、production 风格后端落盘/审计验证、模拟外部后端兼容性验证、HTTP 外部后端认证/网络验证，以及 Supermemory 官方 schema、SDK seam 与首轮 live smoke 验证已完成，但账号级限流/配额语义、持续稳定性与远端后端差异仍待验证
- 已完成首轮 live smoke 并生成结构化证据，但这仍不等于账号级限流/配额语义、持续稳定性和真实官方 SDK 包接入已全部验证
- 已提供 live 收口脚本，用于在真实 JSON 证据存在时预览或回写状态；未执行前仍不能据此宣称真实 provider 已验证
- CPO / CTO 已在当前 Copilot-host live 阶段上岗；技术真源长期 owner 已转向 CTO，但首轮接管输出和授权矩阵仍需继续验证
- 回迁 TriMetaverse/.github 前仍需完成 shadow-test manifest 与 smoke test

## 当前质量判断

- 当前适合作为研发与收口基线
- 当前不应被误判为“已完成正式宿主部署”或“已完成生产级 Hermes 集成”
- 当前已具备把 TriCompany/.github 以 shadow-test 方式回迁 TriMetaverse 的准备结构；其中 runtime/cognition 最小 smoke test、Hermes 核心契约验证、本地 provider-backed 集成验证、后端落盘/审计验证、模拟外部后端兼容性验证、HTTP 外部后端认证/网络验证，以及 Supermemory 官方 schema、SDK seam 与首轮 live smoke 验证均已通过
- 当前 runtime/cognition 的 chief-of-staff source 回迁已向上覆盖到 workflow / schedule 入口层，但这仍不等于支撑包已整体收敛为只读发布物，也不等于正式宿主切换完成

## 下一步

- 继续验证 TriCompany/.github 下的当前阶段宿主资产
- 继续处理剩余更高层 chief_of_staff_* 入口与必要的 engineering / workflow 文档回填，避免 source 与支撑包的状态认知继续漂移
- 使用真实 Supermemory API key 验证 live 调用、账号级 rate limit/配额语义，以及官方 SDK 集成
- 复核 live smoke 证据、账号级限流/配额语义与持续稳定性后，再决定是否允许升到 real provider validated
- 让 CTO 输出首轮技术接管判断并继续工程化
