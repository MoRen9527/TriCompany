// AgentContract Schema v1 — 死形状警示（2026-08-13，CTO 小狄 / O2-B）
//
// ⚠ 本 schema 建模 metadata/capabilities/instances/rules，与当前两代真实合同均不匹配：
//   - source-agents/*（v2，contract.version 2.0，TriLC 消费）：contract + paths + decision_rights + runtime_baseline
//   - docs/registry/*（v1，contract.version 1.0，TriMC 消费）：contract + identity + responsibilities +
//     decision_rights + collaborators + tools + io_contract
// 实测 safeParse 对两代合同全部失败（metadata: Required）。本模块零生产消费方；
// TriMC / TriLC 各自维护自己的 resolver。O2-A（合同真源统一，M3 前置）完成前勿用，
// 统一方向见 TriCompany/docs/engineering/trilc-trimc-runtime-parity.md §6.2。
import { z } from 'zod';

export const ContractMetadataSchema = z.object({
  name: z.string(),
  version: z.string(),
  description: z.string().optional(),
  author: z.string().optional(),
  tags: z.array(z.string()).optional(),
});

export const ContractCapabilitySchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  tools: z.array(z.string()).optional(),
  subAgents: z.array(z.string()).optional(),
  permissions: z.array(z.string()).optional(),
});

export const ContractInstanceSchema = z.object({
  id: z.string(),
  contractId: z.string(),
  capability: z.string(),
  config: z.record(z.unknown()).optional(),
  status: z.enum(['active', 'inactive', 'error']).optional(),
});

export const AgentContractSchema = z.object({
  metadata: ContractMetadataSchema,
  capabilities: z.array(ContractCapabilitySchema).optional(),
  instances: z.array(ContractInstanceSchema).optional(),
  rules: z.array(z.string()).optional(),
});

/** @deprecated 死形状 schema（O2-B），与两代真实合同均不匹配，O2-A 合同统一前勿用 */
export type ContractMetadata = z.infer<typeof ContractMetadataSchema>;
/** @deprecated 死形状 schema（O2-B），与两代真实合同均不匹配，O2-A 合同统一前勿用 */
export type ContractCapability = z.infer<typeof ContractCapabilitySchema>;
/** @deprecated 死形状 schema（O2-B），与两代真实合同均不匹配，O2-A 合同统一前勿用 */
export type ContractInstance = z.infer<typeof ContractInstanceSchema>;
/** @deprecated 死形状 schema（O2-B），与两代真实合同均不匹配，O2-A 合同统一前勿用 */
export type AgentContract = z.infer<typeof AgentContractSchema>;
