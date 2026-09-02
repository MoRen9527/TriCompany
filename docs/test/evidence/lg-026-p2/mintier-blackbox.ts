// ── LG-026-P2 门禁③ minTier 跨仓黑盒（ST/小柯 2026-09-02）──
// 方法学：TriRLC 侧 import @tricompany/agent-core（node_modules symlink →
// TriCompany/packages/agent-core dist，跨仓直调），叠加 TriRLC 真实 lead-tools
// registerLeadTools 注册路径，直调 getToolDefinitions 验四点：
// 缺省行为不变 / 显式声明优先 / 组长 heartbeat 清单恰五工具无 file 系无 shell_exec /
// subagent 不可见。
import { register, unregister, getToolDefinitions, canUseTool } from '@tricompany/agent-core';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// TriRLC 真实组长注册路径（同 app.ts 通道态接线）
import { createLetterStore } from 'file:///D:/Code/ai/TriRLC/src/letter-store/store.ts';
import { registerLeadTools } from 'file:///D:/Code/ai/TriRLC/src/letter-store/lead-tools.ts';

let passCount = 0;
let failCount = 0;
const failures: string[] = [];
function check(name: string, cond: boolean, detail = ''): void {
  if (cond) { passCount++; console.log(`  PASS ${name}`); }
  else { failCount++; failures.push(name + (detail ? ` :: ${detail}` : '')); console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`); }
}
function makeDef(name: string) {
  return { type: 'function' as const, function: { name, description: `bb probe ${name}`, parameters: { type: 'object', properties: {} } } };
}
const noop = async () => '{}';

const LEAD_FIVE = ['letter_list_pending', 'letter_deliver', 'letter_escalate', 'send_letter', 'ledger_read'].sort();

// 组长真实注册路径
const store = createLetterStore(join(tmpdir(), 'lg026p3-mintier.db'), { leaderId: '组长' });
registerLeadTools(store);

const namesOf = (tier?: string): string[] => (getToolDefinitions(tier as never) as { function: { name: string } }[]).map((d) => d.function.name).sort();
const heart = namesOf('heartbeat');
const sub = namesOf('subagent');
const mainT = namesOf('main');
const coord = namesOf('coordinator');
const all = namesOf();

console.log('== M 组长清单（真实 registerLeadTools 路径）==');
check('M1 heartbeat 清单恰五工具且名单精确', heart.length === 5 && JSON.stringify(heart) === JSON.stringify(LEAD_FIVE), `实际${JSON.stringify(heart)}`);
const FILE_FAMILY = ['read_file', 'write_file', 'edit_file', 'replace_in_file', 'list_directory', 'search_code', 'glob_search', 'read_lints'];
check('M2 无 file 系八件', FILE_FAMILY.every((f) => !heart.includes(f)), `命中${JSON.stringify(FILE_FAMILY.filter((f) => heart.includes(f)))}`);
check('M3 无 shell_exec 无 task', !heart.includes('shell_exec') && !heart.includes('task'));
check('M4 subagent 清单不可见（minTier=heartbeat > subagent）', sub.length === 0, `实际${JSON.stringify(sub)}`);
check('M5 coordinator 清单不可见', coord.length === 0);
check('M6 main 清单可见（heartbeat ≤ main）', mainT.length === 5 && JSON.stringify(mainT) === JSON.stringify(LEAD_FIVE));
check('M7 无参全量=5', all.length === 5);

console.log('== M 缺省行为不变（g1-1 口径）==');
register(makeDef('bb_undeclared_probe'), noop); // 无声明：查表无 → main 缺省
check('M8a 无声明自定义工具 subagent 不可见（default-safe）', !namesOf('subagent').includes('bb_undeclared_probe'));
check('M8b 无声明自定义工具 main 可见', namesOf('main').includes('bb_undeclared_probe'));
check('M8c 无声明自定义工具 heartbeat 不可见', !namesOf('heartbeat').includes('bb_undeclared_probe'));
unregister('bb_undeclared_probe');
// allowlist 表内既有工具名不传声明 → 照表（read_file=subagent）
register(makeDef('read_file'), noop);
check('M9a 表内名无声明照表：subagent 可见', namesOf('subagent').includes('read_file'));
check('M9b 表内名无声明照表：heartbeat 可见（subagent≤heartbeat）', namesOf('heartbeat').includes('read_file'));
unregister('read_file');

console.log('== M 显式声明优先（g1-2 口径）==');
register(makeDef('bb_decl_sub_probe'), noop, { minTier: 'subagent' });
check('M10 声明 subagent 覆盖 main 缺省：subagent 可见', namesOf('subagent').includes('bb_decl_sub_probe'));
unregister('bb_decl_sub_probe');
register(makeDef('bb_decl_heart_probe'), noop, { minTier: 'heartbeat' });
check('M11 声明 heartbeat：heartbeat 可见 / subagent 不可见', namesOf('heartbeat').includes('bb_decl_heart_probe') && !namesOf('subagent').includes('bb_decl_heart_probe'));
unregister('bb_decl_heart_probe');

console.log('== M 观察项：二参 canUseTool 导出面 ==');
const cuLetter = canUseTool('letter_deliver', 'heartbeat' as never);
check('M12(观察) canUseTool 二参（无声明上下文）对 letter_* 走查表→main 缺省→heartbeat 拒', cuLetter.allowed === false, `allowed=${cuLetter.allowed}（执行路径 loop.ts 不逐工具复查，清单即边界；仅外部导出面口径，报告单列）`);

store.close();
console.log(`\n== minTier 黑盒汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
process.exit(failCount ? 1 : 0);
