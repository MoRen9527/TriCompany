// Contracts v3.0 — re-exports（收敛权威 schema，r13-contract-convergence / r13-1）
export type {
  AgentContractV3,
  Identity,
  Paths,
  Responsibility,
  DecisionRights,
  Collaborators,
  ToolSpec,
  IOEntry,
  IOContract,
} from './agent-contract.js';
export {
  AgentContractV3Schema,
  CONTRACT_V3_VERSION,
  CONTRACT_V3_SUPPORTED_VERSIONS,
  CONTRACT_V3_TYPE,
} from './agent-contract.js';
export { loadContractV3, resolveContractsV3, ContractV3Error } from './resolver.js';
