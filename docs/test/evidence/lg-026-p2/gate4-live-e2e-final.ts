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
// 第三轮（CTO 执行令 08:06Z）：组长模型 env 化——probe 存活名 glm-5.3-flash（FD probe 裁，勿自选）
process.env.TRILC_LEAD_MODEL = 'glm-5.3-flash';
// 真 token：从网关进程提取的部署配置值（受限文件 0600，stdout 不回显；2026-09-02 ST 补跑）
{
  const { readFileSync } = await import('node:fs');
  const envFile = readFileSync('C:/Users/jedih/AppData/Local/Temp/lg026p2-blackbox/gw-token.env', 'utf-8').trim();
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
// 第四轮新增：L1 直推帧断言——收件席 stream 注册（组长 deliver 后 letter_state 帧按 to 席触发）
const subSse = await req('POST', '/internal/v1/tasks/submit', { message: 'gate4-sse' });
const sseAllFrames: any[] = [];
let sseStatus = 'init';
// 连接1：寄信前注册，收寄信触发的 letter_inbox 活推帧（R1 语义）
const sseFrame1Promise = (async (): Promise<any> => {
  const res = await fetch(`http://127.0.0.1:${port}/internal/v1/sessions/${subSse.json.sessionId}/stream?as=${RECIPIENT}`, { headers: { 'x-internal-token': TOKEN } });
  sseStatus = `http=${res.status} body=${!!res.body}`;
  if (!res.ok || !res.body) return null;
  const reader = (res.body as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();
  let buf = '';
  const timer = setTimeout(() => { try { reader.cancel(); } catch { /* */ } }, 60_000);
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) { sseStatus += ' stream-done'; return null; }
      buf += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buf.indexOf('\n\n')) >= 0) {
        const block = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        if (!block.includes('event:')) continue;
        const evLine = block.split('\n').find((l) => l.startsWith('event:'));
        const dataLine = block.split('\n').find((l) => l.startsWith('data:'));
        let data: any = null;
        try { data = JSON.parse(dataLine!.slice(5).trim()); } catch { data = null; }
        const ev = evLine?.slice(6).trim() ?? '';
        sseAllFrames.push({ event: ev, data });
        if (ev === 'letter' && data?.event === 'letter_inbox') {
          clearTimeout(timer);
          return { event: ev, data };
        }
      }
    }
  } finally {
    clearTimeout(timer);
    try { reader.cancel(); } catch { /* */ }
  }
})();
await new Promise((r) => setTimeout(r, 800)); // 等 SSE 注册完成
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

// 第四轮：L1 直推帧断言——拆双段：L11a 连接1 活推帧（R1）；L11b L5 真投后重连收补拉 delivered 帧（R2）
const sseFrame1 = await sseFrame1Promise;
check('L11a 寄信入件帧按收件席注册面活推（letter_inbox·R1）', sseFrame1?.event === 'letter' && sseFrame1?.data?.letterId === letterId && sseFrame1?.data?.status === 'pending', `实际${JSON.stringify(sseFrame1)?.slice(0, 160)}`);
await req('POST', `/internal/v1/sessions/${subSse.json.sessionId}/cancel`, {}).catch(() => { /* 关连接1 */ });

// L11b：组长真投后重连 stream，收 delivered 补拉帧（R2 语义，探针会话流关闭不影响新连接）
const subSse2 = await req('POST', '/internal/v1/tasks/submit', { message: 'gate4-sse-2' });
const sseFrame2 = await (async (): Promise<any> => {
  const res = await fetch(`http://127.0.0.1:${port}/internal/v1/sessions/${subSse2.json.sessionId}/stream?as=${RECIPIENT}`, { headers: { 'x-internal-token': TOKEN } });
  if (!res.ok || !res.body) return null;
  const reader = (res.body as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();
  let buf = '';
  const timer = setTimeout(() => { try { reader.cancel(); } catch { /* */ } }, 10_000);
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) return null;
      buf += decoder.decode(value, { stream: true });
      const idx = buf.indexOf('\n\n');
      if (idx >= 0) {
        const block = buf.slice(0, idx);
        const evLine = block.split('\n').find((l) => l.startsWith('event:'));
        const dataLine = block.split('\n').find((l) => l.startsWith('data:'));
        let data: any = null;
        try { data = JSON.parse(dataLine!.slice(5).trim()); } catch { data = null; }
        return { event: evLine?.slice(6).trim() ?? '', data };
      }
    }
  } finally {
    clearTimeout(timer);
    try { reader.cancel(); } catch { /* */ }
    await req('POST', `/internal/v1/sessions/${subSse2.json.sessionId}/cancel`, {}).catch(() => { /* */ });
  }
})();
check('L11b 组长真投后 delivered 积压按席补拉（letter_inbox·R2）', sseFrame2?.event === 'letter' && sseFrame2?.data?.letterId === letterId && sseFrame2?.data?.status === 'delivered', `实际${JSON.stringify(sseFrame2)?.slice(0, 160)}`);
console.log(`  [sse-diag] conn1=${sseStatus} conn1全帧=${JSON.stringify(sseAllFrames)?.slice(0, 400)}`);

console.log(`\n== 门禁④活模型 E2E 汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
console.log(`终态信件: ${JSON.stringify(finalLetter)?.slice(0, 400)}`);
console.log(`台账: ${JSON.stringify(ledgerTrail)?.slice(0, 400)}`);
try { await app.stop(); } catch { /* swallow */ }
if (!process.env.ST_KEEP) {
  try { rmSync(WORK, { recursive: true, force: true }); } catch { /* swallow */ }
} else {
  console.log(`[live] KEEP 现场: ${WORK}`);
}
process.exit(failCount ? 1 : 0);
