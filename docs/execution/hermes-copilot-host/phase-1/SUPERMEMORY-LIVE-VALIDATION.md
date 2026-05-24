# Supermemory Live Validation Record

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/execution/hermes-copilot-host/phase-1/SUPERMEMORY-LIVE-VALIDATION.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- executionTier: stable-execution-summary
- linkedSupportEvidence: TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/SUPERMEMORY-LIVE-VALIDATION.md
- supportSyncRule: support 同名文档保留为 phase evidence，不执行 same-name published-copy 追平
- lastSyncedAt: 2026-04-28

日期：2026-04-17
状态：已完成首轮 live smoke；2026-04-18 修复后复跑通过

## 迁移说明

- 本记录形成时 support root 路径名为 `TriCompany-shadow-host`。
- 自 2026-04-18 起，当前生效目录已迁移为 `TriCompany-copilot-host-assets`。
- 为保留 phase-1 证据链，历史 support root 路径不做整体替换；源仓这里只回填稳定执行结论。

## 2026-04-18 复跑说明

- 后续已在当前 support root 下复跑两次 `python -m runtime.cognition.supermemory_live_validation`。
- 第一次按默认 `SUPERMEMORY_TIMEOUT_SECONDS=10` 执行，在真实 `/v3/documents` 调用阶段超时。
- 第二次将 `SUPERMEMORY_TIMEOUT_SECONDS` 放宽到 `30` 后再次执行，仍在真实 `/v3/documents` 调用阶段超时。
- 随后已补上 transport-timeout retry，并将 live 默认 timeout 提升到 `45` 秒后再次复跑；本次执行已通过。
- 当前应写成：phase-1 首轮 live smoke 历史证据有效；2026-04-18 中途曾出现真实 `/v3/documents` 长尾超时，但在提高 timeout 与补上 transport-timeout retry 后复跑恢复通过。
- 后续若继续推进真实 provider 稳定性验证，仍建议持续观察远端 `/v3/documents` 写入长尾。

## 目的

为 TriCompany runtime/cognition 的 Supermemory 真实账号验证保留固定证据位，避免把“脚本已存在”误写成“live provider 已验证”。

## 执行门禁

- 仅在明确授权后执行真实远端调用
- 必须显式设置 TRICOMPANY_ENABLE_SUPERMEMORY_LIVE_VALIDATION=1
- 必须提供 SUPERMEMORY_API_KEY
- 若使用非默认端点或鉴权方式，可额外设置 SUPERMEMORY_BASE_URL、SUPERMEMORY_USE_BEARER_AUTH、SUPERMEMORY_TIMEOUT_SECONDS

## 执行命令

- 在 TriCompany 仓库根目录执行 python -m runtime.cognition.supermemory_live_validation

## 预期产物

- 默认 JSON 产物路径：docs/execution/hermes-copilot-host/phase-1/SUPERMEMORY-LIVE-VALIDATION.latest.json
- 若需要自定义落档路径，可设置 TRICOMPANY_SUPERMEMORY_LIVE_REPORT_PATH
- 收口预览命令：python -m runtime.cognition.supermemory_live_finalize
- 收口回写命令：python -m runtime.cognition.supermemory_live_finalize --apply

## 升档规则

- 只有当 live smoke 成功执行并产出 JSON 证据后，才允许讨论是否将状态提升到 real provider validated
- 若仅存在 schema 验证、SDK seam 验证或 live smoke 脚本本身，均不得视为真实 provider 已验证

## 本次记录

- 最近一次执行时间：2026-04-17T14:04:08.945817+00:00
- JSON 证据路径：D:/OneDrive/Code/ai/TriCompany/docs/execution/hermes-copilot-host/phase-1/SUPERMEMORY-LIVE-VALIDATION.latest.json
- 召回命名空间：employee/ceo-chief-of-staff, org/audit, org/shared
- 远端端点：<https://api.supermemory.ai>
- 鉴权模式：bearer
- 结果计数：4
