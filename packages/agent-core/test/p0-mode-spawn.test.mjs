// p0-mode-spawn.test.mjs — PA-2 adversarial regression suite
// tick 20260827T044800Z · tree p0fix1-agent-core-perm · 角色 FullStackDeveloper（小全）
//
// 覆盖审计报告 rmc-agent-core.md 的两个 P0：
//   P0-2  checkAcceptEditsMode 曾对一切非 ['write_file','edit_file'] 工具提前
//         返回 allow（decidedBy=mode_accept_edits），shell_exec、任意 MCP、
//         自定义变更工具全部免确认，步骤 9/10 在该模式下不可达。
//         修复后：acceptEdits 仅对「界内写入类工具」短路 allow；非写清单成员
//         return null 落入步骤 9（allow 规则）→ 步骤 10（default-deny）；
//         写清单成员的界内 allow / 界外 deny 判定权保持原状（PA-1 成果零触碰，
//         其回归套件断言的界外写 decidedBy=mode_accept_edits 不变）。
//   P0-4  SpawnConfig 无权限/cwd 承载通道 + loop 层缺省 'bypassPermissions'
//         fail-open。修复后：SpawnConfig 四字段逐字透传，loop 缺省改 'default'。
//
// 驱动面：
//   ../dist/index.js                      → PermissionEngine.decide（= loop.ts
//                                           实际接线面，内部走完整 10 步管线）
//   ../dist/permissions-engine/index.js   → runDecisionPipeline（管线函数直驱，
//                                           rootDir src→dist 目录结构镜像，
//                                           深路径导出可用）
// 运行前提：编排层先重建 dist（npm run build）再执行本套件。
//
// ── 残余验证残差清单（诚实声明，随套件存续，勿删）─────────────────────
// P0-4 spawn 整链 = spawnAgent → agentLoop → createModelClient().stream 模型流，
// 本实例无 Bash 无凭据无法整链驱动。各环节守护方式如下：
//   [tsc --noEmit 类型门禁可证]
//     T1 sub-agent/types.ts 新增字段与 AgentLoopOptions 字段同名同型——
//        spawn.ts 将 config.permissionMode/permissionRules/cwd/
//        additionalDirectories 逐字写入 loopOptions 对象字面量，任何字段名
//        拼写或类型不匹配都在编译期报错（AgentLoopOptions 为具名 interface，
//        strict 模式拒绝多余属性）；
//     T2 types.ts 对 ../permissions-engine/index.js 的 import type 可解析
//        （PermissionMode/PermissionRule 导出存在性由编译裁决）。
//   [仅源码 trace 可证——本套件不为它们写假断言]
//     S1 spawn.ts 未给四个新字段注入任何默认值/coercion（undefined 原样透传，
//        与既有 tier 的 ?? 'subagent' 不同，此处有意不加兜底）；
//     S2 loop.ts 缺省字面量已改为 'default' 且 options.permissionEngine 短路
//        优先分支未被触碰；
//     S3 agentLoop 工具执行前 permissionEngine.decide 门控与 loop_start 回读
//        getMode()/getRules() 的接线未被本节点改动；
//     S4 spawnAgent 超时检查与 adaptEvent 事件适配逻辑未动。
//   动态整链验证交编排层在具备模型凭据的环境执行。
// ────────────────────────────────────────────────────────────────────

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

import { PermissionEngine, parseRule } from '../dist/index.js';
import { runDecisionPipeline } from '../dist/permissions-engine/index.js';

const REPO_CWD = '/srv/fleet/TriCompany';

describe('PA-2 / P0-2 acceptEdits mode × tool decision matrix', () => {
  /** acceptEdits 引擎工厂（无规则基线）。 */
  const engineIn = (overrides = {}) =>
    new PermissionEngine({
      mode: 'acceptEdits',
      cwd: REPO_CWD,
      rules: [],
      ...overrides,
    });

  it('write_file in-boundary short-circuits to mode allow', () => {
    const d = engineIn().decide('write_file', {
      file_path: '/srv/fleet/TriCompany/src/pa2-write.ts',
    });
    assert.equal(d.allowed, true);
    assert.equal(d.behavior, 'allow');
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  it('write_file out-of-boundary still denied by the mode (PA-1 verdict shape preserved)', () => {
    const d = engineIn().decide('write_file', {
      file_path: '/srv/fleet/TriCompany-evil/x.txt',
    });
    assert.equal(d.allowed, false);
    assert.equal(d.behavior, 'deny');
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  it('edit_file in-boundary allowed', () => {
    const d = engineIn().decide('edit_file', {
      file_path: '/srv/fleet/TriCompany/src/pa2-edit.ts',
    });
    assert.equal(d.allowed, true);
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  it('replace_in_file (newly classified write tool) in-boundary allowed', () => {
    // permissions.ts:49-51 明列 replace_in_file 为写工具，旧两元清单遗漏。
    const d = engineIn().decide('replace_in_file', {
      file_path: '/srv/fleet/TriCompany/src/pa2-replace.ts',
    });
    assert.equal(d.allowed, true);
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  it('replace_in_file classification enforces the boundary both ways (out-of-boundary denied)', () => {
    const d = engineIn().decide('replace_in_file', {
      file_path: '/srv/fleet/TriCompany-sibling/c.ts',
    });
    assert.equal(d.allowed, false);
    assert.equal(d.behavior, 'deny');
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  it('shell_exec is no longer free-passed: falls through to default-deny', () => {
    // 审计主向量反转点：旧实现此处 allowed:true / decidedBy=mode_accept_edits。
    const d = engineIn().decide('shell_exec', { command: 'ls -la' });
    assert.equal(d.allowed, false);
    assert.equal(d.behavior, 'deny');
    assert.equal(d.decidedBy, 'default_deny');
  });

  it('custom MCP mutating tool name also lands on default-deny', () => {
    const d = engineIn().decide('mcp__db__execute', {
      sql: 'DELETE FROM users WHERE id = 1',
    });
    assert.equal(d.allowed, false);
    assert.equal(d.behavior, 'deny');
    assert.equal(d.decidedBy, 'default_deny');
  });

  it('read_file lost its implicit pass: now requires an explicit allow rule or default-deny (CT0 notice-a)', () => {
    const d = engineIn().decide('read_file', {
      path: '/srv/fleet/TriCompany/src/some-module.ts',
    });
    assert.equal(d.allowed, false);
    assert.equal(d.decidedBy, 'default_deny');
  });

  it('write tool without an extractable path stays mode-denied (fail-closed kept)', () => {
    const d = engineIn().decide('write_file', {});
    assert.equal(d.allowed, false);
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  it('dontAsk × shell_exec ban unchanged (regression pin)', () => {
    const d = engineIn({ mode: 'dontAsk' }).decide('shell_exec', { command: 'ls' });
    assert.equal(d.allowed, false);
    assert.equal(d.behavior, 'deny');
    assert.equal(d.decidedBy, 'mode_dont_ask');
  });

  it('plan × write tool deny unchanged (zero-touch pin)', () => {
    const d = engineIn({ mode: 'plan' }).decide('edit_file', {
      file_path: '/srv/fleet/TriCompany/src/a.ts',
    });
    assert.equal(d.allowed, false);
    assert.equal(d.decidedBy, 'mode_plan');
  });

  it('bypassPermissions × shell_exec still allowed (zero-touch pin)', () => {
    const d = engineIn({ mode: 'bypassPermissions' }).decide('shell_exec', {
      command: 'ls -la',
    });
    assert.equal(d.allowed, true);
    assert.equal(d.decidedBy, 'mode_bypass');
  });
});

describe('PA-2 / P0-2 allow-rule channel under acceptEdits', () => {
  // 词表事实教训（同 PA-1 套件）：matchesTool 是字面等值 + "*" 后缀，
  // 规则词表与 shell_exec 无别名映射 —— 规则必须用 'shell_exec(...)' 原词。
  /** acceptEdits 引擎工厂（带 parseRule 构造的规则）。 */
  const engineWithRules = (...specs) =>
    new PermissionEngine({
      mode: 'acceptEdits',
      cwd: REPO_CWD,
      rules: specs.map(([raw, behavior]) => parseRule(raw, behavior, 'userSettings')),
    });

  it('explicit shell_exec allow rule admits matching command in acceptEdits (rule channel unblocked)', () => {
    // 证明收口后步骤 9 仍可达：规则是 acceptEdits 下放行 shell 的唯一通道。
    const eng = engineWithRules(['shell_exec(ls -la)', 'allow']);
    const d = eng.decide('shell_exec', { command: 'ls -la' });
    assert.equal(d.allowed, true);
    assert.equal(d.behavior, 'allow');
    assert.equal(d.decidedBy, 'always_allow');
  });

  it('same rule does not admit a different command (anchored exact match still holds)', () => {
    const eng = engineWithRules(['shell_exec(ls -la)', 'allow']);
    const d = eng.decide('shell_exec', { command: 'cat /etc/hostname' });
    assert.equal(d.allowed, false);
    assert.equal(d.decidedBy, 'default_deny');
  });

  it('vocabulary gap pinned: Bash(...) rule never unlocks shell_exec under acceptEdits', () => {
    // 若未来引入跨词表别名，本例翻红即须先补壳命令锚定对抗用例。
    const eng = engineWithRules(['Bash(git push)', 'allow']);
    const d = eng.decide('shell_exec', { command: 'git push' });
    assert.equal(d.allowed, false);
    assert.equal(d.decidedBy, 'default_deny');
  });
});

describe('PA-2 / P0-4 statically-pinnable contracts', () => {
  it('bare PermissionEngine defaults to failure-closed default mode (parity with new loop fallback literal)', () => {
    const eng = new PermissionEngine({});
    assert.equal(eng.getMode(), 'default');
    const d = eng.decide('shell_exec', { command: 'ls' });
    assert.equal(d.allowed, false);
    assert.equal(d.decidedBy, 'default_deny');
  });

  it('runDecisionPipeline direct drive: acceptEdits × shell_exec → default_deny (pipeline-level parity)', () => {
    const d = runDecisionPipeline('shell_exec', { command: 'whoami' }, 'acceptEdits', [], REPO_CWD);
    assert.equal(d.allowed, false);
    assert.equal(d.behavior, 'deny');
    assert.equal(d.decidedBy, 'default_deny');
  });

  it('runDecisionPipeline direct drive: acceptEdits × in-boundary replace_in_file → mode allow (cross-surface parity)', () => {
    const d = runDecisionPipeline(
      'replace_in_file',
      { file_path: '/srv/fleet/TriCompany/src/direct.ts' },
      'acceptEdits',
      [],
      REPO_CWD,
    );
    assert.equal(d.allowed, true);
    assert.equal(d.decidedBy, 'mode_accept_edits');
  });

  // 其余 spawn 链路 wiring 见文件头部「残余验证残差清单」：
  // T1/T2 由 tsc --noEmit 类型门禁守护，S1–S4 仅源码 trace 可证，
  // 此处不落恒真断言伪装覆盖。
});
