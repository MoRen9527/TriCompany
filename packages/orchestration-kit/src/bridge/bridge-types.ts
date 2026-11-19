// ── Session Bridge Types（orchestration-kit·P1 编排九件收编）──
// 收编源=TriMMC src/orchestration/session-bridge.ts 四接口（MMC 形=收敛基线版·
// CTO convergence-eval §二 漂移孪生实证承录）——接口面零改迁（原样保真）。
// daemon 耦合面（claude/dsh CLI 实装）=adapter-face：各 daemon 侧 driver 实现
// SessionBridgeDriver 接口（notice-232 增补·adapter-face 强化承面）。

export interface AgentSession {
  /** 短 id，如 ad45d07b（MMC claude --bg 形）或 seat 名（RMC dsh 形） */
  agentId: string;
  /** 完整 session id（UUID 或 driver 域 id 形） */
  sessionId: string;
  /** 会话显示名（= 员工名/员工 id） */
  name: string;
  /** 会话工作目录 */
  cwd: string;
  status: string;
  state: string;
  /** 注册表映射：name → employeeId（加载合同时注入） */
  employeeId?: string;
  lastSeenAt: string;
}

export interface SessionBridgeOptions {
  /** driver 可执行面（MMC=claude bin 形·RMC=dsh bin 形·driver 域自释） */
  bin?: string;
  /** MMC claude 形兼容别名（driver 域自释） */
  claudeBin?: string;
  /** 降权账号（如 'fleet'）；不设则以当前用户直接执行 */
  runAsUser?: string;
  /** 会话工作目录 */
  cwd?: string;
  /** 注册表采集超时（ms） */
  agentsJsonTimeoutMs?: number;
  /** 消息桥超时（ms） */
  messageTimeoutMs?: number;
  /** spawn 超时（ms） */
  spawnTimeoutMs?: number;
  /** driver 域扩展键（零约束透传·driver 自释） */
  [extra: string]: unknown;
}

export interface SpawnResult {
  ok: boolean;
  agentId?: string;
  name?: string;
  /** driver 域会话 id（RMC dsh 形等） */
  sessionId?: string;
  error?: string;
}

export interface SendMessageResult {
  ok: boolean;
  reply?: string;
  error?: string;
  timedOut?: boolean;
}
