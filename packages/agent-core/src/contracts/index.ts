// Contracts — re-exports
// ⚠ 死形状警示（2026-08-13，CTO 小狄 / O2-B）：本目录 schema 与两代真实合同
// （source-agents v2 / docs/registry v1）均不匹配，零生产消费方。
// O2-A（合同真源统一，M3 前置）完成前勿用，详见 agent-contract.ts 头注释。
export type {
  AgentContract,
  ContractMetadata,
  ContractCapability,
  ContractInstance,
} from './agent-contract.js';

export { ContractResolver } from './resolver.js';
export type { ContractResolveResult } from './resolver.js';
