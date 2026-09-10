// ── LG-026-P3 门禁③ letter-sweeper 黑盒 v2（ST/小柯 2026-09-02）──
// 时间注入法修正版：每场景独立库+独立 sweeper+注入钟归零——消除场景间 offset
// 与真实墙钟（store strftime now）的耦合伪 age。v1 发现「ref 信封急件自升级链」
// 现象单列盲区报告，本版各场景内不依赖升级产物。
import { createLetterStore } from 'file:///D:/Code/ai/TriRLC/src/letter-store/store.ts';
import { createLetterSweeper } from 'file:///D:/Code/ai/TriRLC/src/letter-store/letter-sweeper.ts';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rmSync } from 'node:fs';

let passCount = 0;
let failCount = 0;
const failures: string[] = [];
function check(name: string, cond: boolean, detail = ''): void {
  if (cond) { passCount++; console.log(`  PASS ${name}`); }
  else { failCount++; failures.push(name + (detail ? ` :: ${detail}` : '')); console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`); }
}

const realNow = Date.now();
let offsetMs = 0;
(Date.now as () => number) = () => realNow + offsetMs;
const H = 3_600_000;
const MIN = 60_000;
const jump = (ms: number) => { offsetMs += ms; };

let dbSeq = 0;
function freshSetup() {
  const db = join(tmpdir(), `lg026p3-sw-${++dbSeq}.db`);
  rmSync(db, { force: true });
  const store = createLetterStore(db, { leaderId: '组长' });
  let wakeCount = 0;
  const sweeper = createLetterSweeper({ letterStore: store, wake: () => { wakeCount++; } }, { intervalMs: 999 * H });
  offsetMs = 0; // 注入钟归零：库时间戳（真实墙钟）≈ 注入钟起点
  const send = async (actor: string, to: string, priority: '常规' | '重要' | '急件', ttlSeconds?: number): Promise<string> => {
    const rec = store.insertLetter({ from: actor, to, priority, payload: null, ttlSeconds });
    store.transition(rec.letterId, 'deliver', '组长');
    return rec.letterId;
  };
  return { store, sweeper, send, wakeRef: () => wakeCount, cleanup: () => { sweeper.stop(); store.close(); rmSync(db, { force: true }); } };
}

// ── ① C-suite 重要件 4h → 重推 → 8h 原子升 ──
console.log('== ① 重要件 C-suite 4h 链 ==');
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const id = await send('alice', 'COS', '重要');
  jump(3 * H);
  let s = sweeper.sweep();
  check('①a 3h 不动', s.rescued === 0 && s.escalated === 0 && store.getLetter(id)!.retries === 0);
  jump(H + MIN);
  s = sweeper.sweep();
  check('①b 4h+ rePush rescued=1', s.rescued === 1);
  check('①c retries=1 且状态仍 delivered', store.getLetter(id)!.retries === 1 && store.getLetter(id)!.status === 'delivered');
  jump(4 * H + MIN);
  s = sweeper.sweep();
  check('①d 8h+ 自动升级 escalated=1', s.escalated === 1, `escalated=${s.escalated}`);
  check('①e 原信 escalated 冻结', store.getLetter(id)!.status === 'escalated');
  const ref = store.listLetters({}).find((l) => l.refLetterId === id)!;
  check('①f ref 信封 to=COS priority=急件 pending', ref?.to === 'COS' && ref?.priority === '急件' && ref?.status === 'pending');
  cleanup();
}

// ── ② 执行席 24h 同构（5h 不动）──
console.log('== ② 执行席 24h 同构 ==');
{
  const { store, sweeper, send, wakeRef, cleanup } = freshSetup();
  const id = await send('bob', 'worker-exec', '重要');
  jump(5 * H);
  let s = sweeper.sweep();
  check('②a 5h 不动（执行席 24h 阈值）', s.rescued === 0 && s.escalated === 0 && wakeRef() === 0);
  jump(19 * H + MIN);
  s = sweeper.sweep();
  check('②b 24h+ rePush retries=1', s.rescued === 1 && store.getLetter(id)!.retries === 1);
  jump(24 * H + MIN);
  s = sweeper.sweep();
  check('②c 48h+ 自动升级', s.escalated === 1 && store.getLetter(id)!.status === 'escalated');
  const ref = store.listLetters({}).find((l) => l.refLetterId === id)!;
  check('②d ref 同构 to=COS 急件', ref?.to === 'COS' && ref?.priority === '急件');
  cleanup();
}

// ── ③ 急件 30min 保护窗 ──
console.log('== ③ 急件 30min 保护窗 ==');
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const id = await send('alice', 'urgent-target', '急件');
  jump(29 * MIN);
  let s = sweeper.sweep();
  check('③a 窗内不动（29min）', s.escalated === 0 && store.getLetter(id)!.status === 'delivered', `status=${store.getLetter(id)!.status}`);
  jump(2 * MIN);
  s = sweeper.sweep();
  check('③b 过窗即时升（31min）', s.escalated === 1 && store.getLetter(id)!.status === 'escalated');
  check('③c 零等待语义 retries=0（不走重推）', store.getLetter(id)!.retries === 0);
  cleanup();
}
console.log('   == ③b-pending 急件（独立库） ==');
{
  const { store, sweeper, cleanup } = freshSetup();
  const id = store.insertLetter({ from: 'x', to: 'urgent-pending', priority: '急件', payload: null }).letterId; // 保持 pending
  jump(31 * MIN);
  const s = sweeper.sweep();
  check('③d pending 急件过窗同样升级', s.escalated === 1 && store.getLetter(id)!.status === 'escalated');
  cleanup();
}

// ── ④ ttl 到期链 ──
console.log('== ④ ttl 到期链 rePush→超限升 ==');
{
  const { store, sweeper, wakeRef, cleanup } = freshSetup();
  const id = store.insertLetter({ from: 'x', to: 'ttl-target', priority: '常规', payload: null, ttlSeconds: 60 }).letterId; // 保持 pending
  jump(61_000);
  let s = sweeper.sweep();
  check('④a 到期 rePush retries=1', s.expired === 1 && s.rescued === 1 && store.getLetter(id)!.retries === 1);
  jump(MIN); sweeper.sweep();
  check('④b retries=2', store.getLetter(id)!.retries === 2);
  jump(MIN); sweeper.sweep();
  check('④c retries=3（=maxRetries）', store.getLetter(id)!.retries === 3);
  jump(MIN);
  s = sweeper.sweep();
  check('④d retries>=3 → escalate', s.escalated === 1 && store.getLetter(id)!.status === 'escalated');
  check('④e wake 恰 3 次（rePush 三次）', wakeRef() === 3, `wake=${wakeRef()}`);
  cleanup();
}

// ── ⑤ 已读/已办结不动 ──
console.log('== ⑤ 终态不动 ==');
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const id = await send('alice', 'COS', '重要');
  store.transition(id, 'read', 'COS');
  jump(10 * H);
  const s = sweeper.sweep();
  check('⑤a 已读件不被重推不升级', s.rescued === 0 && s.escalated === 0 && store.getLetter(id)!.status === 'read');
  cleanup();
}

// ── ⑥ 盲区级现象复现实证：ref 急件信封 30min 后被再升级（单列候裁）──
console.log('== ⑥ ref 信封自升级现象复现（盲区单列，非 PASS/FAIL）==');
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const id = await send('alice', 'urgent-target', '急件'); // 原始急件
  jump(31 * MIN);
  sweeper.sweep(); // 原信升 → ref 信封（急件, to=urgent-target? 不——escalateTo=COS）
  const ref1 = store.listLetters({}).find((l) => l.refLetterId === id)!;
  jump(31 * MIN);
  const s2 = sweeper.sweep();
  const ref2 = store.listLetters({}).find((l) => l.refLetterId === ref1?.letterId);
  console.log(`  [现象] ref1 status=${ref1?.status}; 31min 后 sweep 又升 ${s2.escalated} 封; ref2 存在=${!!ref2} (to=${ref2?.to})`);
  console.log('  [定性] 自动升级产物（ref 急件信封）未排除于急件规则——收件方未及时办结即再自升，链式膨胀；单列盲区候 CTO 裁（修法候选：急件规则排除 refLetterId 非空件，终止于人工）');
  cleanup();
}

console.log(`\n== P3 sweeper 黑盒汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
process.exit(failCount ? 1 : 0);
