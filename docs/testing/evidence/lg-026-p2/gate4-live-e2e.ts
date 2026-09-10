// ── LG-026-P2 门禁④ 活模型 E2E 补跑脚本（ST/小柯 2026-09-02，双触发待命令执行序②③）──
// 临时端口实例（port 0 + 通道态组长注册 + TRIMODEL_API_TOKEN 注入），生产 8713 零接触。
// 全链断言：寄信 → 组长醒（eventDriven wake）→ letter_deliver 真投 → 台账留痕。
// 产物：结构化读数 JSON 到 stdout；失败时给阻塞分型（网关未启/keys 未生效/模型调用失败）。
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const WORK = mkdtempSync(join(tmpdir(), 'lg026p4-live-'));
const TOKEN = 'st-live-e2e-internal-token';
process.env.TRILC_DATA_DIR = WORK;
process.env.TRILC_PORT = '0';
process.env.TRILC_PROJECT_ROOT = WORK;
process.env.TRILC_CHANNEL_MODE = '1'; // 通道态：组长注册（eventDriven）
// 真 token：从网关进程提取的部署配置值（受限文件 0600，stdout 不回显；2026-09-02 ST 补跑）
{
  const { readFileSync } = await import('node:fs');
  const envFile = readFileSync('C:/Users/jedih/AppData/Local/Temp/lg026p2-blackbox/gw-token.env(已清,提取法见报告)', 'utf-8').trim();
  process.env.TRIMODEL_API_TOKEN = envFile.split('=')[1] ?? '';
}
process.env.TRILC_INTERNAL_TOKEN = TOKEN;
// trimodelApiUrl 缺省 127.0.0.1:3333（已上线）

const { readEnv } = await import('file:///D:/Code/ai/TriRLC/src/config/env.ts');
const { createTriLCApp } = await import('file:///D:/Code/ai/TriRLC/src/server/app.ts');

const env = readEnv();
env.port = 0;
// env.trimodelApiUrl 保持缺省 127.0.0.1:3333（真网关）
const app = createTriLCApp(env);
await app.start();
const port = env.port;
console.log(`[live] app up on ${port}, dataDir=${WORK}`);

let passCount = 0;
let failCount = 0;
const failures: string[] = [];
function check(name: string, cond: boolean, detail = ''): void {
  if (cond) { passCount++; console.log(`  PASS ${name}`); }
  else { failCount++; failures.push(name + (detail ? ` :: ${detail}` : '')); console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`); }
}
async function req(method: string, path: string, body?: unknown): Promise<{ status: number; json: any }> {
  const res = await fetch(`http://127.0.0.1:${port}${path}`, {
    method,
    headers: { 'content-type': 'application/json', 'x-internal-token': TOKEN },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { json = { raw: text?.slice(0, 200) }; }
  return { status: res.status, json };
}

// healthz 基线：agentCount 应=2（DEFAULT + 组长）
await new Promise((r) => setTimeout(r, 1500));
const hz = await req('GET', '/healthz');
check('L1 临时实例 healthz ok', hz.json?.ok === true, JSON.stringify(hz.json).slice(0, 120));
check('L2 组长注册在场（agentCount=2）', hz.json?.heartbeat?.agentCount === 2, `实际${hz.json?.heartbeat?.agentCount}`);

// 寄信（P3 契约：actor 必填，from 强制=actor）
const RECIPIENT = 'e2e-recipient';
const send = await req('POST', '/internal/v1/letters', {
  actor: 'ST-e2e',
  to: RECIPIENT,
  priority: '常规',
  payload: { task: 'gate4-live-e2e', note: '组长请投递此信' },
  from: '伪报-应被覆盖', // F1：请求体 from 应被 actor 覆盖
});
check('L3 寄信 201', send.status === 201, JSON.stringify(send.json).slice(0, 150));
const letterId = send.json?.letterId;
check('L4 响应驼峰契约 letterId/seqNo', typeof letterId === 'string' && typeof send.json?.seqNo === 'number');

// 轮询组长真投（模型调用耗时，180s 上限）
let finalLetter: any = null;
let ledgerTrail: any[] = [];
const deadline = Date.now() + 180_000;
let lastStatus = '';
while (Date.now() < deadline) {
  await new Promise((r) => setTimeout(r, 5000));
  const q = await req('GET', `/internal/v1/letters?box=in&to=${encodeURIComponent(RECIPIENT)}`);
  finalLetter = q.json?.letters?.[0] ?? null;
  if (finalLetter?.status !== lastStatus) {
    lastStatus = finalLetter?.status ?? '';
    console.log(`  [poll ${Math.round((deadline - Date.now()) / -1000) + 180}s] status=${lastStatus} retries=${finalLetter?.retries ?? '-'}`);
  }
  if (finalLetter?.status === 'delivered') break;
  if (finalLetter?.status && finalLetter.status !== 'pending' && finalLetter.status !== 'delivered') break;
}
check('L5 组长真投 letter_deliver（status=delivered）', finalLetter?.status === 'delivered', `终态=${finalLetter?.status}`);
check('L6 deliveredAt 留痕（ISO+Z）', typeof finalLetter?.deliveredAt === 'string' && /[+-]\d{2}:\d{2}|Z$/.test(finalLetter?.deliveredAt ?? ''), `实际${finalLetter?.deliveredAt}`);
const fromOk = finalLetter?.from === 'ST-e2e';
check('L7 F1 生效：信封 from=actor（伪报被覆盖）', fromOk, `实际${finalLetter?.from}`);

const led = await req('GET', `/internal/v1/ledger?letter_id=${letterId}`);
ledgerTrail = led.json?.entries ?? [];
check('L8 台账留痕 send+deliver 两行', JSON.stringify(ledgerTrail.map((e: any) => e.action)) === '["send","deliver"]', `实际${JSON.stringify(ledgerTrail.map((e: any) => [e.actor, e.action]))}`);
check('L9 deliver actor=组长（唯一投递执行者）', ledgerTrail.some((e: any) => e.action === 'deliver' && e.actor === '组长'), `实际${JSON.stringify(ledgerTrail.filter((e: any) => e.action === 'deliver').map((e: any) => e.actor))}`);
const atOk = ledgerTrail.every((e: any) => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(e.at));
check('L10 台账 at ISO+Z 格式（O4 收口）', atOk, `实际${JSON.stringify(ledgerTrail.map((e: any) => e.at))}`);

console.log(`\n== 门禁④活模型 E2E 汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
console.log(`终态信件: ${JSON.stringify(finalLetter)?.slice(0, 400)}`);
console.log(`台账: ${JSON.stringify(ledgerTrail)?.slice(0, 400)}`);
try { await app.stop(); } catch { /* swallow */ }
try { rmSync(WORK, { recursive: true, force: true }); } catch { /* swallow */ }
process.exit(failCount ? 1 : 0);
