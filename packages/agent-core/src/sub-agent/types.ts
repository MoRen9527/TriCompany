// Sub-agent types — shared between TriMC and TriLC

import type { AgentTier } from '../permissions.js';
import type { PermissionMode, PermissionRule } from '../permissions-engine/index.js';

export type SubAgentStatus = 'idle' | 'running' | 'completed' | 'error' | 'cancelled';

export interface AgentDefinition {
  name: string;
  description: string;
  tools?: string[];
  systemPrompt?: string;
  model?: string;
  maxTurns?: number;
  /** Agent execution tier: 'main' (full), 'subagent' (restricted), 'coordinator' (task-only). */
  tier?: AgentTier;
}

export interface SpawnConfig {
  agent: AgentDefinition;
  task: string;
  context?: string;
  parentId?: string;
  timeout?: number;
  maxTurns?: number;
  /**
   * PA-2 / P0-4 permission transparency channel — optional, NO spawn-layer
   * defaults. All four fields are forwarded verbatim into AgentLoopOptions
   * by sub-agent/spawn.ts; `undefined` stays `undefined` on purpose so the
   * loop layer owns fallback policy (now fail-closed 'default', see
   * loop.ts Permission engine section).
   */
  /** Runtime permission mode forwarded to the loop's PermissionEngine. */
  permissionMode?: PermissionMode;
  /** Permission rules forwarded to the loop's PermissionEngine. */
  permissionRules?: PermissionRule[];
  /** Working directory for tool execution + acceptEdits/dontAsk boundary. */
  cwd?: string;
  /** Additional directories treated as inside-boundary (C9). */
  additionalDirectories?: string[];
}

export interface SubAgentEvent {
  type: 'start' | 'tool_call' | 'tool_result' | 'tool_blocked' | 'message' | 'done' | 'error';
  agentId: string;
  agentName: string;
  timestamp: number;
  data?: unknown;
}
