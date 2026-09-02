// ── LG-026-P2 门禁② 端点黑盒交叉验证脚本（ST/小柯 2026-09-02）──
// 方法学：不经仓内 test/server/letters-endpoints.test.ts，独立脚本直调 createTriLCApp
// 起临时端口实例（port 0 + 死端口 trimodel + X-Internal-Token 注入，非通道态无组长注册），
// HTTP 面自写断言五组：ACL 四格 / escalate 原子性 / wake 202 幂等 / token fail-closed /
// 寄信 201+seq 单调+since_seq 重放。
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const WORK = mkdtempSync(join(tmpdir(), 'lg026p2-blackbox-'));
const TOKEN = 'st-blackbox-internal-token';

process.env.TRILC_DATA_DIR = WORK;
process.env.TRILC_PORT = '0';
process.env.TRILC_PROJECT_ROOT = WORK;
delete process.env.TRILC_CHANNEL_MODE; // 非通道态：无组长注册（wake 空转无害面）
delete process.env.TRIMODEL_API_TOKEN;
process.env.TRILC_INTERNAL_TOKEN = TOKEN;

const { readEnv } = await import('file:///D:/Code/ai/TriRLC/src/config/env.ts');
const { createTriLCApp } = await import('file:///D:/Code/ai/TriRLC/src/server/app.ts');

const env = readEnv();
env.port = 0;
env.trimodelApiUrl = 'http://127.0.0.1:1';
const app = createTriLCApp(env);
await app.start();
const port = env.port;
if (!port) throw new Error('app did not bind a port');
console.log(`[bb] app up on 127.0.0.1:${port} (dataDir=${WORK})`);

let passCount = 0;
let failCount = 0;
const failures: string[] = [];
function check(name: string, cond: boolean, detail = ''): void {
  if (cond) { passCount++; console.log(`  PASS ${name}`); }
  else { failCount++; failures.push(name + (detail ? ` :: ${detail}` : '')); console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`); }
}

async function req(method: string, path: string, body?: unknown, headers: Record<string, string> = {}): Promise<{ status: number; json: any }> {
  const res = await fetch(`http://127.0.0.1:${port}${path}`, {
    method,
    headers: { 'content-type': 'application/json', 'x-internal-token': TOKEN, ...headers },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { json = { raw: text }; }
  return { status: res.status, json };
}
async function reqNoToken(method: string, path: string, body?: unknown, badToken?: string): Promise<{ status: number; json: any }> {
  const res = await fetch(`http://127.0.0.1:${port}${path}`, {
    method,
    headers: { 'content-type': 'application/json', ...(badToken ? { 'x-internal-token': badToken } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { json = { raw: text }; }
  return { status: res.status, json };
}

async function sendLetter(over: Record<string, unknown> = {}): Promise<{ id: string; seq: number }> {
  const r = await req('POST', '/internal/v1/letters', { from: 'alice', to: 'bob', priority: '常规', payload: { n: 1 }, ...over });
  if (r.status !== 201) throw new Error(`sendLetter 非201: ${JSON.stringify(r)}`);
  return { id: r.json.letter_id, seq: r.json.seq_no };
}

// ── G1 X-Internal-Token fail-closed 401 面（信件五端点全覆盖）──
console.log('== G1 token fail-closed ==');
{
  const cases: Array<[string, () => Promise<{ status: number }>, string]> = [
    ['G1a POST letters 无token', () => reqNoToken('POST', '/internal/v1/letters', { from: 'a', to: 'b' }), 'POST'],
    ['G1b GET letters 无token', () => reqNoToken('GET', '/internal/v1/letters'), 'GET'],
    ['G1c POST state 无token', () => reqNoToken('POST', '/internal/v1/letters/LT-x/state', { action: 'deliver', actor: '组长' }), 'state'],
    ['G1d GET ledger 无token', () => reqNoToken('GET', '/internal/v1/ledger'), 'ledger'],
    ['G1e POST wake 无token', () => reqNoToken('POST', '/internal/v1/letters/wake'), 'wake'],
    ['G1f POST letters 错token', () => reqNoToken('POST', '/internal/v1/letters', { from: 'a', to: 'b' }, 'wrong-token'), 'POST错token'],
  ];
  for (const [name, fn] of cases) {
    const r = await fn();
    check(`${name} → 401`, r.status === 401, `实际${r.status}`);
  }
}

// ── G2 寄信 201 + seq 单调 + since_seq 重放 ──
console.log('== G2 寄信/seq/重放 ==');
{
  const l1 = await sendLetter();
  const l2 = await sendLetter({ to: 'carol', priority: '急件', payload: { n: 2 } });
  const l3 = await sendLetter({ to: 'bob', payload: null });
  check('G2a 寄信201返回letter_id+seq_no', !!l1.id && typeof l1.seq === 'number');
  check('G2b seq 全局单调 1→2→3', l1.seq === 1 && l2.seq === 2 && l3.seq === 3, `实际${l1.seq},${l2.seq},${l3.seq}`);
  const rep0 = await req('GET', '/internal/v1/letters?since_seq=0');
  check('G2c since_seq=0 → 全量3封+count字段', rep0.status === 200 && rep0.json.count === 3);
  const rep1 = await req('GET', '/internal/v1/letters?since_seq=1');
  check('G2d since_seq=1 → 后继2封 seqNo[2,3]', JSON.stringify(rep1.json.letters.map((l: any) => l.seqNo)) === '[2,3]', `实际${JSON.stringify(rep1.json.letters.map((l: any) => l.seqNo ?? l.seq_no))}`);
  const repBad = await req('GET', '/internal/v1/letters?since_seq=999');
  check('G2e since_seq 超界 → 0封', repBad.json.count === 0);
  const boxIn = await req('GET', '/internal/v1/letters?box=in&to=bob');
  check('G2f box=in 收信箱 to 过滤 → 2封', boxIn.json.count === 2);
  const boxInNoTo = await req('GET', '/internal/v1/letters?box=in');
  check('G2g box=in 缺 to → 400', boxInNoTo.status === 400);
}

// ── G3 escalate ACL 四格矩阵 ──
console.log('== G3 ACL 四格（白名单=组长,COS）==');
{
  // 格1：白名单外 + 有 envelope → 403 + escalate_denied 留痕 + 原信仍 pending
  const c1 = await sendLetter({ to: 'acl1' });
  const r1 = await req('POST', `/internal/v1/letters/${c1.id}/state`, { action: 'escalate', actor: 'bob', envelope: { to: 'COS' } });
  const t1 = (await req('GET', `/internal/v1/ledger?letter_id=${c1.id}`)).json.entries ?? (await req('GET', '/internal/v1/ledger')).json.entries.filter((e: any) => e.letterId === c1.id || e.letter_id === c1.id);
  const s1 = (await req('GET', `/internal/v1/letters?box=in&to=acl1`)).json.letters[0];
  check('G3-1a 白名单外+envelope → 403', r1.status === 403, `实际${r1.status}`);
  check('G3-1b 403 留痕 escalate_denied', JSON.stringify(t1.map((e: any) => e.action ?? e.action)).includes('escalate_denied'), `台账=${JSON.stringify(t1)}`);
  check('G3-1c 原信仍 pending（拒绝未触状态机）', s1?.status === 'pending', `实际${s1?.status}`);
  // 格2：白名单外 + 无 envelope → 仍 403（ACL 先于 envelope 校验）+ 留痕
  const c2 = await sendLetter({ to: 'acl2' });
  const r2 = await req('POST', `/internal/v1/letters/${c2.id}/state`, { action: 'escalate', actor: 'bob' });
  check('G3-2a 白名单外+无envelope → 403（ACL先行）', r2.status === 403, `实际${r2.status}`);
  const ledgerAll2 = (await req('GET', '/internal/v1/ledger')).json.entries;
  const den2 = ledgerAll2.filter((e: any) => (e.letterId ?? e.letter_id) === c2.id);
  check('G3-2b 格2 亦留痕 escalate_denied', den2.some((e: any) => e.action === 'escalate_denied'));
  // 格3：白名单内（COS）+ 无 envelope → 400 + 不触库
  const c3 = await sendLetter({ to: 'acl3' });
  const r3 = await req('POST', `/internal/v1/letters/${c3.id}/state`, { action: 'escalate', actor: 'COS' });
  const s3 = (await req('GET', `/internal/v1/letters?box=in&to=acl3`)).json.letters[0];
  const led3 = (await req('GET', '/internal/v1/ledger')).json.entries.filter((e: any) => (e.letterId ?? e.letter_id) === c3.id);
  check('G3-3a 白名单内+无envelope → 400 invalid_envelope', r3.status === 400 && r3.json.error === 'invalid_envelope', `实际${r3.status} ${r3.json.error}`);
  check('G3-3b 400 不触库：原信仍 pending', s3?.status === 'pending', `实际${s3?.status}`);
  check('G3-3c 400 不触库：台账无 escalate/escalate_denied 残留', led3.every((e: any) => e.action === 'send'), `台账=${JSON.stringify(led3.map((e: any) => e.action))}`);
  // 格3b：白名单内（组长）+ 无 envelope → 400（白名单另一员同径）
  const c3b = await sendLetter({ to: 'acl3b' });
  const r3b = await req('POST', `/internal/v1/letters/${c3b.id}/state`, { action: 'escalate', actor: '组长' });
  check('G3-3d 白名单内(组长)+无envelope → 400', r3b.status === 400);
  // 格4：白名单内 + 有 envelope → 200（原子版，详见 G4）
  const c4 = await sendLetter({ to: 'acl4' });
  const r4 = await req('POST', `/internal/v1/letters/${c4.id}/state`, { action: 'escalate', actor: '组长', envelope: { to: 'COS', payload: { reason: 'acl-g4' } } });
  check('G3-4a 白名单内+envelope → 200', r4.status === 200, `实际${r4.status} ${JSON.stringify(r4.json)}`);
  check('G3-4b 返回 original+envelope 双件', !!r4.json.original?.letterId && !!r4.json.envelope?.letterId);
}

// ── G4 escalate 强制原子版断言 ──
console.log('== G4 原子性 ==');
{
  const orig = await sendLetter({ to: 'atom1', from: 'dave' });
  const r = await req('POST', `/internal/v1/letters/${orig.id}/state`, { action: 'escalate', actor: 'COS', envelope: { to: 'COS', priority: '急件', payload: { reason: '超时未读' } } });
  check('G4a 原信 escalated', r.json.original?.status === 'escalated');
  check('G4b 新信封 pending + refLetterId=原信', r.json.envelope?.status === 'pending' && r.json.envelope?.refLetterId === orig.id);
  check('G4c 新信封 seq > 原信 seq', r.json.envelope?.seqNo > orig.seq);
  // 原信冻结：后续流转全 409
  for (const action of ['deliver', 'read', 'escalate', 'done']) {
    const rr = await req('POST', `/internal/v1/letters/${orig.id}/state`, { action, actor: action === 'read' ? 'atom1' : 'COS', envelope: { to: 'COS' } });
    check(`G4d 冻结后 ${action} → 409`, rr.status === 409, `实际${rr.status}`);
  }
  // 台账：原信 send+escalate 恰两行；新信封 send 起
  const allLedger = (await req('GET', '/internal/v1/ledger')).json.entries;
  const origTrail = allLedger.filter((e: any) => (e.letterId ?? e.letter_id) === orig.id);
  const envTrail = allLedger.filter((e: any) => (e.letterId ?? e.letter_id) === r.json.envelope.letterId);
  check('G4e 原信台账恰 send+escalate 两行', JSON.stringify(origTrail.map((e: any) => e.action)) === '["send","escalate"]', `实际${JSON.stringify(origTrail.map((e: any) => e.action))}`);
  check('G4f 新信封台账 send 起', envTrail.length === 1 && envTrail[0].action === 'send');
  // escalate 目标不存在 → 404
  const r404 = await req('POST', '/internal/v1/letters/LT-ghost-xxx/state', { action: 'escalate', actor: 'COS', envelope: { to: 'COS' } });
  check('G4g escalate 不存在信 → 404', r404.status === 404, `实际${r404.status}`);
}

// ── G5 wake 202 幂等 + 无组长注册无害 ──
console.log('== G5 wake ==');
{
  const w1 = await req('POST', '/internal/v1/letters/wake');
  const w2 = await req('POST', '/internal/v1/letters/wake');
  check('G5a wake → 202 + woken:true', w1.status === 202 && w1.json.woken === true, `实际${w1.status}`);
  check('G5b wake 幂等（连发两次同 202）', w2.status === 202 && w2.json.woken === true);
  check('G5c 非通道态无组长注册 wake 无害（响应仍规整）', w1.json.reason === 'action');
  // 寄信内联唤醒路径（B4）在非通道态同样空转无害
  const l = await sendLetter({ to: 'wake-path' });
  check('G5d 寄信内联 wake 后信仍可查（无副作用）', (await req('GET', `/internal/v1/letters?box=in&to=wake-path`)).json.count === 1 && !!l.id);
}

console.log(`\n== 端点黑盒汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
try { await app.stop(); } catch { /* swallow */ }
try { rmSync(WORK, { recursive: true, force: true }); } catch { /* swallow */ }
process.exit(failCount ? 1 : 0);
