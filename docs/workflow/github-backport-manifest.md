# TriCompany GitHub Backport Manifest

版本：V0.1
日期：2026-04-18
状态：shadow-test 回迁已完成，并已转入本地正式接管；非 live runtime 复跑验证、会议闭环演练、中央 ceo-chief-of-staff 命名吸收，以及修复后的 Supermemory live smoke 复跑均已完成

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/github-backport-manifest.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/github-backport-manifest.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文用于定义 TriCompany 当前阶段的 .github 宿主资产如何安全回迁到 TriMetaverse/.github，并从 shadow-test 收口到本地正式接管。

phase-1 的起点不是覆盖式回迁，而是 shadow-test 平行回迁，以避免直接覆盖 TriMetaverse 里已经存在的中央总助资产；在 shadow-test 闭环后，再把同一套 Copilot-host 资产提升到本地正式接管。

当前支撑包路径为 TriMetaverse 根下的 TriCompany-copilot-host-assets，而不是 reference 目录。

当前生效的本地正式接管 agent、prompt 与 manifest 位于 TriMetaverse/.github；TriCompany-copilot-host-assets 负责支撑文档、runtime 与 vendor 参考副本。

## 2. 当前回迁模式

- 当前模式：本地正式接管（起点为 shadow-test 平行回迁）
- 当前目标：在 TriMetaverse/.github 中稳定承载当前 Copilot-host 的正式接管资产，同时保持与未来 TriMC 正式宿主切换分离
- 当前支撑包：TriCompany-copilot-host-assets/
- 当前禁止：直接声明 TriMC 正式宿主切换或把当前资产误写成最终正式宿主

## 3. 当前回迁范围

- ceo-chief-of-staff 套件
- TriCompany 的 registry agent
- 会议 prompt
- 维护说明
- 回迁 manifest 自身

## 4. 为什么先 shadow-test 再转正式接管

- TriMetaverse 已存在中央总助与中央 registry 资产
- 当前阶段先用 shadow-test 验证 TriCompany 宿主资产是否可用
- shadow-test 闭环完成后，再把同一套 Copilot-host 资产提升到当前阶段正式接管
- 若直接覆盖，测试失败时不利于回滚和定位差异

## 5. 机器可读清单

当前机器可读清单位于：

- .github/manifests/tricompany-copilot-host-backport.json

## 6. 回迁前置条件

1. TriCompany/.github 套件已稳定
2. 元认知层边界已文档化
3. runtime/cognition 与 .github 的依赖关系已写清
4. 已完成至少一次 TriCompany 内部 smoke test

## 7. 回迁后验证重点

1. agent 是否能正常发现与调用
2. prompt 入口是否可用
3. registry 路由是否仍然指向正确文档
4. 是否存在与 TriMetaverse 现有资产冲突的命名或语义

## 8. 本轮 smoke test 结果

- TriCompanyProductRegistry 已确认 support root 为 TriCompany-copilot-host-assets
- TriCompanyCodeRegistry 已确认 support root 为 TriCompany-copilot-host-assets
- TriCompanyCEOChiefOfStaff 已确认固定前置核查与元认知结构均指向 TriCompany-copilot-host-assets
- 三者都明确当前不是 TriMC 正式宿主切换
- tricompany-开始会议 prompt 已完成结构化开始会议 smoke test
- tricompany-结束会议 prompt 已完成结构化结束会议 smoke test
- 已完成一轮完整会议生命周期演练，覆盖开始会议、产品汇报、技术汇报与结束会议，并保持 shadow-test 边界稳定
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.smoke_test 跑通 runtime/cognition 最小 smoke test
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.contract_validation 跑通 Hermes 核心契约验证
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.integration_validation 跑通 provider-backed 集成验证
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.backend_validation 跑通 production 风格后端落盘与审计验证
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.chief_of_staff_bridge_validation 验证中央 `ceo-chief-of-staff.memory/soul/colleagues/social` 已可桥接进同一 cognition kernel
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.chief_of_staff_workflow_validation 验证开始会议 / 结束会议 / 日常收口已可写入同一 cognition kernel，验证 `ceo-chief-of-staff.memory.md` 与 `TRICOMPANY_COGNITION_HOME` 的双向同步策略，并模拟宿主 Python hook 在对应 workflow 命令后自动补一次 `sync-memory`
- 2026-04-27 已在 TriCompany 根目录补回 source 侧 `chief_of_staff_workflow_bridge.py` 与 `chief_of_staff_workflow_validation.py`，并通过 `python -m unittest runtime.cognition.chief_of_staff_workflow_validation` 验证 workflow writeback、`ceo-chief-of-staff.memory.md` 与 repo-backed cognition storage 的双向同步，以及复用中央 hook 脚本模拟宿主自动补一次 `sync-memory`
- 2026-04-27 已把 workflow hook 的 command 识别、stdin 解析与 `sync-memory` 调度纯逻辑提炼到 source 侧 `chief_of_staff_workflow_sync_hook.py`；`TriMetaverse/.github/hooks/ceo-chief-of-staff-workflow-sync.py` 现仅保留 thin wrapper，并复跑 `python -m unittest runtime.cognition.chief_of_staff_workflow_validation` 继续通过
- 2026-04-27 已在 TriCompany 根目录补回 source 侧 `chief_of_staff_schedule_staging.py` 与 `chief_of_staff_schedule_staging_validation.py`，并通过 `python -m runtime.cognition.chief_of_staff_schedule_staging --help` 与 `python -m unittest runtime.cognition.chief_of_staff_schedule_staging_validation` 验证 resident runner -> cron runner -> task resolver -> approval report / workbench / closeout 链路
- 2026-04-27 已在 TriCompany 根目录补回 source 侧 `chief_of_staff_resident_runner.py`、`chief_of_staff_operating_review_closeout.py`、`chief_of_staff_registry_closeout_validation.py` 与 `chief_of_staff_operating_review_closeout_validation.py`，并通过 `python -m runtime.cognition.chief_of_staff_resident_runner --help`、`python -m runtime.cognition.chief_of_staff_operating_review_closeout --help`、`python -m unittest runtime.cognition.chief_of_staff_registry_closeout_validation`、`python -m unittest runtime.cognition.chief_of_staff_operating_review_closeout_validation` 验证 resident 顶层 CLI、operating review closeout 顶层 CLI，以及 registry / operating review closeout bridge 链路
- 2026-04-27 已在 TriCompany 根目录补回 source 侧 `chief_of_staff_wiki_batch_refresh.py`，并通过 `python -m runtime.cognition.chief_of_staff_wiki_batch_refresh --help` 验证最后一个缺失的 top-level chief-of-staff CLI 入口；当前可见 `chief_of_staff_*.py` 顶层入口已与 support bundle 对齐
- 当前生效的中央 `.github/prompts/开始会议.prompt.md`、`结束会议.prompt.md`、`日常收口.prompt.md` 已接入 workflow bridge 自动写回口径；workspace `.github/hooks/ceo-chief-of-staff-workflow-sync.json` 会在对应 bridge 命令后自动补一次 `sync-memory`，且 live hook Python 脚本当前只保留宿主 wrapper，纯逻辑以 source 侧 `chief_of_staff_workflow_sync_hook.py` 为准
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.external_validation 跑通模拟外部后端兼容性验证
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.http_backend_validation 跑通 HTTP 外部后端认证与网络验证
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.supermemory_validation 跑通 Supermemory 官方 schema 验证
- 已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.supermemory_sdk_validation 跑通 Supermemory 官方 SDK seam 验证
- phase-1 首轮已在 TriCompany-copilot-host-assets 根目录通过 python -m runtime.cognition.supermemory_live_validation 基于真实 Supermemory 账号跑通 live smoke，并生成 JSON 证据与固定记录页
- 2026-04-18 已复跑 python -m runtime.cognition.smoke_test、contract_validation、integration_validation、backend_validation、external_validation、http_backend_validation、supermemory_validation、supermemory_sdk_validation，全部继续通过
- 2026-04-18 已在真实 live 环境下复跑 python -m runtime.cognition.supermemory_live_validation：前两次分别在默认 10 秒和放宽到 30 秒时于 `/v3/documents` 调用阶段超时；补上 transport-timeout retry 并将默认 timeout 提升到 45 秒后，再次复跑已通过
- 已为中央 ceo-chief-of-staff 套件保留 baseline 快照：TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/baselines/central-ceo-chief-of-staff-2026-04-18/
- 已完成中央 ceo-chief-of-staff 五件套命名吸收，并保持共享开始会议 / 结束会议 prompt 不变
- 已在同一 support root 下补齐开始会议补问、正式开始、会中 APPROVE、事实不足即 FREEZE 与结束会议收口的连续会议链路，并确认当前可统一写成“本地 Copilot-host 已完成 shadow-test，现进入正式接管；该结论不等于正式宿主切换。”

## 9. 下一轮验证入口

- 当前阶段总助本地正式接管验证已完成，后续如需继续验证，优先转入账号级限流/配额语义、持续稳定性与真实官方 SDK 包接入
- CPO / CTO 已完成当前 live entry 绑定；协作验证下一步单列
- 后续若继续开展会议类验证，仍以 TriCompany-copilot-host-assets 作为唯一 support root

## 9.1 中央命名吸收执行结果

- 本轮已完成中央 `ceo-chief-of-staff` 总助五件套命名吸收，不包含 `开始会议`、`结束会议` 两个公司级共享 prompt。
- 当前已完成 support root 目录重命名：从 `TriCompany-shadow-host` 迁移到 `TriCompany-copilot-host-assets`。
- 当前已保留中央总助套件 baseline 备份与回滚参考，确保覆盖失败时可直接恢复中央 `ceo-chief-of-staff`。
- 2026-04-26 已补建 `tricompany-ceo-chief-of-staff` 套件 archive baseline：`docs/execution/hermes-copilot-host/phase-1/baselines/tricompany-ceo-chief-of-staff-archive-2026-04-26/`。
- `tricompany-ceo-chief-of-staff.*` 的 live 文件已删除；当前迁移源与回滚参考统一由 archive baseline 承接，不再保留 live 副本。
- `tricompany-开始会议.prompt.md` 与 `tricompany-结束会议.prompt.md` 的 live 文件已删除；相关 phase-1 会议入口仅保留 archive baseline 副本与历史说明，不再存在 live prompt 入口。
- 当前建议把未来 `TriMC` 新宿主的 agent 文档视为平行新资产包，而不是继续复用 Copilot-host support root 的物理命名。

## 10. 当前不能写成已完成的事项

- 正式宿主切换完成
- 生产级 Hermes 接入完成
- TriCompany 已升级为正式主控宿主
