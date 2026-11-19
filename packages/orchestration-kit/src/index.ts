// ── Employee Orchestration Layer ──
// Re-exports for TriMMC/src/orchestration/

export * from './types.js';
export { loadEmployeeRegistry } from './employee-registry.js';
export type { LoadResult } from './employee-registry.js';
export { route } from './capability-router.js';
export { transition, assign, escalate, isTimedOut, getConfig } from './employee-scheduler.js';
export { estimateCost, checkBudget, recordCost, getBudgetState, getModelTierPolicy, resetBudget } from './cost-controller.js';
export { dispatch, dispatchAsync } from './dispatch-proxy.js';
export type { DispatchDeps, AsyncDispatchDeps, DispatchExecutor, DispatchExecutorContext } from './dispatch-proxy.js';

// ── Session Bridge（adapter-face·P1 收编面）──
export type {
  AgentSession,
  SessionBridgeOptions,
  SpawnResult,
  SendMessageResult,
} from './bridge/bridge-types.js';
export type {
  SessionBridgeDriver,
  SessionBridge,
} from './bridge/session-bridge-core.js';
export type { AgentSession as BridgeAgentSession } from './bridge/bridge-types.js';
export {
  buildRegistry,
  createSessionBridge,
} from './bridge/session-bridge-core.js';
