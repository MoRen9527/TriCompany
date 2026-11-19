// ── Session Bridge Core（orchestration-kit·P1 收编·adapter-face 工厂）──
// SessionBridgeDriver=daemon 耦合面接口（三 API·各 daemon adapter 实装：
//   TriMMC=claude CLI driver / TriRMC=dsh CLI driver——漂移孪生正解=接口统一
//   +adapter 各侧实现·漂移面收敛为 adapter 内部语义）。
// createSessionBridge(driver)=编排面工厂（app.ts 消费三 API 函数形零改承载）
// +buildRegistry 纯函数随包（零 driver 面）。
// 收编源=TriMMC src/orchestration/session-bridge.ts（MMC 形=收敛基线版）。
import type {
  AgentSession,
  SessionBridgeOptions,
  SendMessageResult,
  SpawnResult,
} from './bridge-types.js';

/** daemon 耦合面 driver 接口：三 API 方法形（签名=现役函数形零改迁）。 */
export interface SessionBridgeDriver {
  spawnSession(
    employeeId: string,
    task: string,
    opts?: SessionBridgeOptions,
  ): Promise<SpawnResult>;
  listAgents(opts?: SessionBridgeOptions): Promise<AgentSession[]>;
  sendMessage(
    sessionId: string,
    message: string,
    opts?: SessionBridgeOptions,
  ): Promise<SendMessageResult>;
}

export interface SessionBridge {
  spawnSession: SessionBridgeDriver['spawnSession'];
  listAgents: SessionBridgeDriver['listAgents'];
  sendMessage: SessionBridgeDriver['sendMessage'];
  buildRegistry: (sessions: AgentSession[], employeeNames?: string[]) => AgentSession[];
}

/** 注册表解析：按 name（= employeeId）注入映射，供 /internal/v1/agents 使用。 */
export function buildRegistry(
  sessions: AgentSession[],
  employeeNames: string[] = [],
): AgentSession[] {
  const nameSet = new Set(employeeNames);
  return sessions.map((s) => ({
    ...s,
    employeeId: nameSet.has(s.name) ? s.name : undefined,
  }));
}

/** 编排面工厂：driver 注入→三 API 函数形（app.ts 消费形零改承载）。 */
export function createSessionBridge(driver: SessionBridgeDriver): SessionBridge {
  return {
    spawnSession: (employeeId, task, opts) => driver.spawnSession(employeeId, task, opts),
    listAgents: (opts) => driver.listAgents(opts),
    sendMessage: (sessionId, message, opts) => driver.sendMessage(sessionId, message, opts),
    buildRegistry,
  };
}
