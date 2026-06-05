# TriCompany Published Copy Refresh SOP

版本：V0.1
日期：2026-04-27
状态：最小可执行版

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/published-copy-refresh-sop.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- lastSyncedAt: 2026-04-28
- supportPublishedCopy: 当前无同名 support 副本
- sourceScope: 当前作为 TriCompany workflow 真源，约束 source -> support bundle 的最小刷新动作

## 1. 文档定位

本文用于把 `TriCompany/` 真源、`TriCompany-copilot-host-assets/` 支撑包副本，以及 execution support-only 资产的更新动作写成一份最小可执行 SOP。

本文解决的是“文档更新后下一步该怎么做”，而不是再次定义 owner 本身。owner、边界和资产归类仍以以下文档为准：

- `TriMetaverse/docs/workflow/tricompany-copilot-host-assets-governance.md`
- `TriMetaverse/docs/workflow/tricompany-copilot-host-assets-migration-matrix.md`
- `TriCompany/.github/manifests/tricompany-published-copy-manifest.json`

本文不覆盖：

- `TriMetaverse/.github/` live 入口吸收动作
- runtime 源码发布流程
- runtime support fallback 副本与 `vendor/reference/**` 冻结参考副本的登记治理
- 当前宿主直接消费的 support-only knowledge object 目录与 schedule 对象集（例如 `TriCompany-copilot-host-assets/knowledge/roles/**`、`TriCompany-copilot-host-assets/knowledge/employees/**` 与 `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/schedules/*.json`）
- `TriMetaverse/.github/manifests/tricompany-copilot-host-backport.json` 这类 live/backport machine-readable 宿主清单
- 运行态数据落盘或清理流程

## 2. 触发条件

出现以下任一情况时，应执行本文：

1. `TriCompany/docs/` 真源发生稳定语义变化。
2. 当前 host 明确重新依赖某份 support 副本。
3. phase-1 execution 新增验证证据、回滚材料或 baseline 构成变化。
4. 当前需要做一次成批 published-copy 刷新。

## 3. 先判定资产类型

开始改文件前，先用 `tricompany-published-copy-manifest.json` 判断目标资产属于哪一类：

1. `activePublishedCopies`
2. `onDemandPublishedCopies`
3. `executionConclusionLinks`
4. `executionOperatorRunbooks`
5. `executionAuditEvidence`
6. `executionArchiveIndexes`

如果 manifest 里还没有该资产，再回看治理页和迁移矩阵，确认它是否应该被新增到清单，而不是直接开始双写。

如果目标属于 `runtime/cognition/**`、`vendor/reference/**`、`TriCompany-copilot-host-assets/knowledge/roles/**`、`TriCompany-copilot-host-assets/knowledge/employees/**`、`TriCompany-copilot-host-assets/knowledge/org/**`、`TriCompany-copilot-host-assets/knowledge/audit/**`、`TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/schedules/*.json` 或 `TriMetaverse/.github/manifests/tricompany-copilot-host-backport.json` 这类非 docs 宿主资产，则不要补进本文 manifest；应回到迁移矩阵、host-object-manifest 或对应 backport manifest 处理。只有在满足 `tricompany-copilot-host-assets-governance.md` 中 support-object-set 独立 manifest 的三条准入门槛后，才单独建立对应对象清单，而不是塞进 docs published-copy manifest。

如果目标其实是运行态或生成产物，则先按以下规则分流：

1. `.env`、`.env.*`、`.tricompany-cognition/**`、Python cache / coverage 产物，以及治理锚点之外的自定义 JSON / 日志 / 调试输出，按 `runtime-state` 本地化并忽略。
2. `TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/audit/**`、`knowledge/employees/ceo-chief-of-staff/workbench/{index.html,snapshot.json}` 与 `knowledge/employees/ceo-chief-of-staff/workbench/approval-report/{snapshot.json,summary.md}` 虽由 runtime 生成，但当前属于受治理的 `support-object-set`，继续跟踪，不按 runtime-state 忽略。
3. `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/SUPERMEMORY-LIVE-VALIDATION.latest.json` 这类固定 execution JSON 证据属于 `audit-record`，继续跟踪；只有当 `TRICOMPANY_SUPERMEMORY_LIVE_REPORT_PATH` 把文件落到治理锚点之外时，才先按 runtime-state 本地化。

## 4. 分类后的标准动作

### 4.1 active published-copy

适用对象：当前 live 宿主固定前置核查、当前 host operator runbook 或当前发布验证链会直接读取的 support 副本。

动作：

1. 先改 `TriCompany/` 真源。
2. 同轮或下一轮追平 support 副本。
3. 更新 support 副本的 `lastSyncedAt` 或等价同步元信息。
4. 如果资产首次进入 active 清单，再补 manifest、治理页和迁移矩阵。

### 4.2 on-demand published-copy

适用对象：保留在 support bundle 作为参考发布物，但当前 host 不要求每轮立即追平的副本。

动作：

1. 默认只改 `TriCompany/` 真源。
2. 只有在明确 batch publish 或当前 host 重新显式依赖时，才刷新 support 副本。
3. support 副本允许暂时落后，但不得在 support bundle 独立演化。

### 4.3 stable execution summary

适用对象：`executionConclusionLinks` 里的 source 稳定执行结论文档。

动作：

1. 稳定阶段结论只先回写 `TriCompany/docs/execution/` 真源。
2. support 同名页只在新增 phase 证据、迁移说明或 operator 审计需要时更新。
3. 不把 source/support 这对同名文件当成 active published-copy 处理。

### 4.4 operator-runbook

适用对象：当前 support root 下 host operator 会直接翻阅的 support-only 操作页。

动作：

1. 当前 host 的步骤、边界口径或回滚条件变化时，直接更新 support runbook。
2. 如果其中规则已经稳定到应上升为模块 workflow、中央协议或组织规则，再额外回写对应真源。
3. 不要求在 `TriCompany/docs/` 维护同名文件。

### 4.5 phase-evidence

适用对象：读审、演练、验证、补证和执行证据页。

动作：

1. 新证据只写 support execution。
2. 真正稳定的阶段结论再提炼回 `TriCompany/docs/execution/` 或相关 workflow / registry 真源。
3. 不把证据页当 published-copy 逐文件追平。

### 4.6 archive-index

适用对象：baseline / archive 目录下的 README 索引页。

动作：

1. 仅在 baseline 构成、回滚说明或 live 入口说明变化时更新。
2. 保持它作为 support-only 审计入口，不要求同名回源。
3. 如果新增 baseline 目录，补对应 README，并把它登记进 manifest。
4. baseline / archive 目录内的快照载荷文件默认视为冻结 archive payload，不单独补元信息，也不参与 published-copy 刷新或同名同步。

## 5. 最小执行顺序

1. 先确认资产类型，而不是先写 support。
2. 先改 source 真源，除非该资产本来就是 support-only runbook / evidence / archive index。
3. 如果需要 support 更新，再改 support 副本。
4. 如果资产分类或清单发生变化，再补 governance、migration matrix 和 manifest。
5. 最后做 focused validation。

## 6. 最小验证要求

文档更新后，至少做以下校验：

1. 对改动文件跑静态错误检查。
2. 对 manifest 新增条目做 grep 确认，避免只改正文没改清单。
3. 若本轮牵涉 active published-copy，确认 source 与 support 元信息一致。
4. 若本轮牵涉 execution 证据，确认没有把 evidence 误升级成 published-copy。

## 7. 禁止事项

1. 不先在 support bundle 写长期真源，再指望以后“有空再回源”。
2. 不把 phase-evidence、archive-index 或 operator-runbook 误写成 active published-copy。
3. 不把当前 Copilot-host support root 的专用步骤直接写成未来 `TriMC` 正式宿主规则。
4. 不因为 support 副本存在，就默认它应与 source 永久双写。

## 8. 关联入口

- `TriCompany/.github/manifests/tricompany-published-copy-manifest.json`
- `TriMetaverse/docs/workflow/tricompany-copilot-host-assets-governance.md`
- `TriMetaverse/docs/workflow/tricompany-copilot-host-assets-migration-matrix.md`
- `TriCompany/docs/workflow/github-backport-manifest.md`
