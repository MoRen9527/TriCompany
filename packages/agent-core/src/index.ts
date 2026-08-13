// @trimetaverse/agent-core — Shared agent-loop foundation
// Extracted from TriMC Phase 2 (70/70 tests pass)
// See: docs/engineering/cto-008-C-shared-core-proposal.md

// Agent Loop
export {
  agentLoop,
  runAgentLoop,
  type AgentLoopOptions,
  type AgentLoopDeps,
  type AgentEvent,
  type ContextSources,
  type CacheState,
  type CacheMetrics,
  type ToolSpec,
} from './loop.js';

// Tools (registry only — concrete tools live in TriMC / TriLC)
export {
  register,
  unregister,
  getToolDefinitions,
  executeTool,
  hasTool,
  listTools,
  clearRegistry,
  type ToolHandler,
  type ToolContext,
} from './tools.js';

// Permissions
export {
  filterToolsForTier,
  getTierSummary,
  getTierToolCounts,
  canUseTool,
  TOOL_TIER_ALLOWLIST,
  type AgentTier,
  type PermissionResult,
} from './permissions.js';

// Permission Engine
export {
  PermissionEngine,
  type PermissionEngineOptions,
} from './permissions-engine/index.js';
export type {
  PermissionMode,
  PermissionRule,
  PermissionBehavior,
  DecisionResult,
  DecisionStep,
  RuleSource,
  SafetyCheckResult,
} from './permissions-engine/types.js';
export { RULE_SOURCE_PRIORITY } from './permissions-engine/types.js';
export { parseRule, parseRules } from './permissions-engine/index.js';
export { runSafetyCheck } from './permissions-engine/index.js';

// Sub-agent
export {
  spawnAgent,
  spawnAgentComplete,
  getBuiltInAgent,
  listBuiltInAgents,
} from './sub-agent/index.js';
export type {
  AgentDefinition,
  SpawnConfig,
  SubAgentEvent,
  SubAgentStatus,
} from './sub-agent/types.js';

// Contracts v3.0 — 收敛权威 schema（r13-contract-convergence / r13-1）
// 双域共用解析入口：TriLC / TriMC 的合同解析与校验统一走本模块。
// 只接受 v3.0；规格与迁移序列见 TriCompany/docs/engineering/agent-contract-v3-spec.md。
export type {
  AgentContractV3,
  Identity,
  Paths,
  Responsibility,
  DecisionRights,
  Collaborators,
  IOEntry,
  IOContract,
} from './contracts/agent-contract.js';
export type { ToolSpec as ContractToolSpec } from './contracts/agent-contract.js';
export {
  AgentContractV3Schema,
  CONTRACT_V3_VERSION,
  CONTRACT_V3_TYPE,
} from './contracts/agent-contract.js';
export { loadContractV3, resolveContractsV3, ContractV3Error } from './contracts/resolver.js';

// Message Guard
export {
  validateMessage,
  validateMessageBatch,
  isStreamComplete,
  sanitizeForPersistence,
  compressMessage,
} from './message-guard/index.js';
export type { GuardResult, RejectReason } from './message-guard/index.js';

// Process Supervisor
export {
  createProcessSupervisor,
  createRunRegistry,
} from './process-supervisor/index.js';
export type {
  LogicalRunFinalizeInput,
  ManagedRun,
  ManagedRunStdin,
  ProcessSupervisor,
  RegisterLogicalRunInput,
  RunExit,
  RunRecord,
  RunRegistry,
  RunState,
  SpawnInput,
  TerminationReason,
} from './process-supervisor/index.js';

// Scheduler
export type {
  CronSchedule,
  CronJobState,
  CronJob,
  CronJobCreate,
  CronJobPatch,
  CronStoreFile,
} from './scheduler/types.js';
export {
  newCronJobState,
  CRON_STORE_SCHEMA,
  CRON_STORE_VERSION,
} from './scheduler/types.js';
export {
  computeNextRunAtMs,
  computePreviousRunAtMs,
  computeInitialNextRunAtMs,
  validateCronExpression,
  coerceFiniteScheduleNumber,
  clearCronerCache,
} from './scheduler/cron-engine.js';
export {
  resolveJobStaggerMs,
  resolveDefaultCronStagger,
  DEFAULT_STAGGER_MS,
} from './scheduler/stagger.js';
export {
  loadJobStore,
  saveJobStore,
  invalidateJobStoreCache,
  overrideConfigDir,
  resetConfigDir,
  buildJob,
  applyJobPatch,
  patchJobState,
} from './scheduler/job-store.js';
export { JobExecutor } from './scheduler/job-executor.js';
export type { JobHandler, JobExecutorOptions } from './scheduler/job-executor.js';
export {
  computeBackoff,
  sleepWithAbort,
  withRetry,
  DEFAULT_BACKOFF_POLICY,
  FAST_RETRY_POLICY,
} from './scheduler/backoff.js';
export type { BackoffPolicy } from './scheduler/backoff.js';
export {
  evaluateHeartbeat,
  stripHeartbeatSummary,
} from './scheduler/heartbeat-policy.js';
export type {
  HeartbeatResult,
  HeartbeatPolicyOptions,
} from './scheduler/heartbeat-policy.js';
