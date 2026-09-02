// tools-min-tier-declaration.test.mjs — LG-026-P2-B3 register() minTier 声明（BOD 裁甲 2026-09-02）
// 角色 FullStackDeveloper（小全）· CTO 跨仓管治条件 g1 两用例
//
// 覆盖：
//   g1-1  缺省行为不变——不传 minTier 的注册照走 TOOL_TIER_ALLOWLIST 查表
//         （未列名自定义工具=main-only，既有 tier 语义零变化）
//   g1-2  显式 minTier 优先于查表——声明 minTier:'heartbeat' 的自定义工具
//         对 heartbeat tier 清单可见、subagent 不可见（allow-list 声明式注册）
// 驱动面：仅经 ../dist/index.js 公开导出（register/unregister/getToolDefinitions/canUseTool）。
// 运行前提：npm test 先 npm run build 再执行本套件。

import { describe, it, afterEach } from 'node:test';
import assert from 'node:assert/strict';

import { register, unregister, getToolDefinitions, canUseTool } from '../dist/index.js';

function makeToolDef(name) {
  return {
    type: 'function',
    function: { name, description: `test tool ${name}`, parameters: { type: 'object', properties: {} } },
  };
}

async function noopHandler() {
  return '{}';
}

describe('register() minTier declaration (LG-026-P2-B3 裁甲)', () => {
  afterEach(() => {
    unregister('custom_undeclared_tool');
    unregister('letter_pending_list');
  });

  it('g1-1 default behavior unchanged: undeclared custom tool stays main-only', () => {
    register(makeToolDef('custom_undeclared_tool'), noopHandler);
    try {
      const mainDefs = getToolDefinitions('main').map((d) => d.function.name);
      const heartbeatDefs = getToolDefinitions('heartbeat').map((d) => d.function.name);
      const subagentDefs = getToolDefinitions('subagent').map((d) => d.function.name);
      assert.ok(mainDefs.includes('custom_undeclared_tool'));
      assert.ok(!heartbeatDefs.includes('custom_undeclared_tool'));
      assert.ok(!subagentDefs.includes('custom_undeclared_tool'));
      // canUseTool 查表路径行为同步不变
      assert.equal(canUseTool('custom_undeclared_tool', 'main').allowed, true);
      assert.equal(canUseTool('custom_undeclared_tool', 'heartbeat').allowed, false);
    } finally {
      unregister('custom_undeclared_tool');
    }
  });

  it('g1-2 explicit minTier takes precedence over allowlist table', () => {
    register(makeToolDef('letter_pending_list'), noopHandler, { minTier: 'heartbeat' });
    try {
      const heartbeatDefs = getToolDefinitions('heartbeat').map((d) => d.function.name);
      const subagentDefs = getToolDefinitions('subagent').map((d) => d.function.name);
      const coordinatorDefs = getToolDefinitions('coordinator').map((d) => d.function.name);
      // heartbeat tier 清单可见（组长工具面达成）
      assert.ok(heartbeatDefs.includes('letter_pending_list'));
      // 低 tier 不可见（声明式 allow-list）
      assert.ok(!subagentDefs.includes('letter_pending_list'));
      assert.ok(!coordinatorDefs.includes('letter_pending_list'));
      // main 全量可见
      assert.ok(getToolDefinitions('main').map((d) => d.function.name).includes('letter_pending_list'));
      // 该名不在查表内——无声明时不可见，可见性只能来自显式声明
      assert.equal(canUseTool('letter_pending_list', 'heartbeat').allowed, false);
    } finally {
      unregister('letter_pending_list');
    }
  });
});
