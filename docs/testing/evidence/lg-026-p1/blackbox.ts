// ── LG-026-P1 门禁② 黑盒交叉验证脚本（ST/小柯 2026-09-02）──
// 方法学：不经仓内 test/letter-store.test.ts，独立脚本直调 createLetterStore 公开 API。
// 依据：CTO 派工令 2026-09-02T04:45Z；设计依据三件 + 严格冻结版终验裁示。
// 覆盖五面：A seq 全局单调+重启续号 / B 状态机门禁矩阵 5态×4动作+actor 两规则 /
//           C escalate 原子性注入回滚 / D ledger 留痕完整性 / E sinceSeq 边界。
// 留档说明：本件为 evidence 留档副本（原跑于系统 TEMP，读数见 blackbox-result.log）。
import { createLetterStore } from 'file:///D:/Code/ai/TriRLC/src/letter-store/store.ts';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rmSync, mkdirSync } from 'node:fs';

const WORK = join(tmpdir(), 'lg026p1-blackbox');
rmSync(WORK, { recursive: true, force: true });
mkdirSync(WORK, { recursive: true });

const LEADER = '组长甲';
const ALICE = 'alice';
const BOB = 'bob';
const COS = 'COS';
const ACTIONS = ['deliver', 'read', 'escalate', 'done'] as const;

let passCount = 0;
let failCount = 0;
const failures: string[] = [];

function check(name: string, cond: boolean, detail = ''): void {
  if (cond) {
    passCount++;
    console.log(`  PASS ${name}`);
  } else {
    failCount++;
    failures.push(name + (detail ? ` :: ${detail}` : ''));
    console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`);
  }
}

function throws(fn: () => unknown, re: RegExp): boolean {
  try {
    fn();
    return false;
  } catch (e) {
    return re.test(String((e as Error)?.message ?? e));
  }
}

const msg = (e: unknown): string => String((e as Error)?.message ?? e);

// ── A. seq 全局单调 + 重启续号（关开 factory 重验）──
function sectionA(): void {
  console.log('== A. seq 全局单调 + 重启续号 ==');
  const db = join(WORK, 'a.db');
  const s1 = createLetterStore(db, { leaderId: LEADER });
  const q1 = s1.insertLetter({ from: ALICE, to: BOB, priority: '常规', payload: 1 }).seqNo;
  const q2 = s1.insertLetter({ from: BOB, to: ALICE, priority: '急件', payload: 2 }).seqNo;
  const q3 = s1.insertLetter({ from: ALICE, to: COS, priority: '重要', payload: null }).seqNo;
  check('A1 首信 seq=1', q1 === 1);
  check('A2 严格递增步长1（跨发送人/收件人）', q1 === 1 && q2 === 2 && q3 === 3);
  check('A3 getLastSeq=3', s1.getLastSeq() === 3);
  s1.close();

  const s2 = createLetterStore(db, { leaderId: LEADER });
  check('A4 重启1后 getLastSeq 续=3', s2.getLastSeq() === 3);
  const q4 = s2.insertLetter({ from: COS, to: BOB, priority: '常规', payload: 4 }).seqNo;
  check('A5 重启1后新信 seq=4（MAX 续号）', q4 === 4);
  s2.close();

  const s3 = createLetterStore(db, { leaderId: LEADER });
  const q5 = s3.insertLetter({ from: BOB, to: BOB, priority: '常规', payload: 5 }).seqNo;
  check('A6 重启2后续号 seq=5', q5 === 5);
  const all = s3.listLetters();
  const seqs = all.map((l) => l.seqNo);
  check('A7 无重复 seq', new Set(seqs).size === all.length && all.length === 5);
  check('A8 seq={1..5} 无空洞', seqs.join(',') === '1,2,3,4,5');
  s3.close();
}

// ── B. 状态机门禁矩阵：5态×4动作全遍历（每格独立样本信）+ actor 校验两规则 ──
function sectionB(): void {
  console.log('== B. 状态机门禁矩阵 + actor 校验 ==');
  const db = join(WORK, 'b.db');
  const store = createLetterStore(db, { leaderId: LEADER });

  // 期望矩阵（严格冻结版）：leader=仅组长可投 / recipient=仅收件人可读 / ALLOW=无 actor 白名单 / DENY
  const expect: Record<string, Record<string, string>> = {
    pending: { deliver: 'leader', read: 'DENY', escalate: 'ALLOW', done: 'DENY' },
    delivered: { deliver: 'DENY', read: 'recipient', escalate: 'ALLOW', done: 'DENY' },
    read: { deliver: 'DENY', read: 'DENY', escalate: 'ALLOW', done: 'ALLOW' },
    escalated: { deliver: 'DENY', read: 'DENY', escalate: 'DENY', done: 'DENY' },
    done: { deliver: 'DENY', read: 'DENY', escalate: 'DENY', done: 'DENY' },
  };

  let cell = 0;
  for (const st of Object.keys(expect)) {
    for (const action of ACTIONS) {
      cell++;
      const recipient = `rcpt-${st}-${action}`;
      const id = store.insertLetter({ from: ALICE, to: recipient, priority: '常规', payload: { cell } }).letterId;
      // 预流转样本信至目标态
      if (st === 'delivered' || st === 'read' || st === 'done') store.transition(id, 'deliver', LEADER);
      if (st === 'read' || st === 'done') store.transition(id, 'read', recipient);
      if (st === 'escalated') store.transition(id, 'escalate', LEADER);
      if (st === 'done') store.transition(id, 'done', recipient);

      const exp = expect[st][action];
      const actor = exp === 'recipient' ? recipient : LEADER;
      let allowed = false;
      let errText = '';
      try {
        store.transition(id, action, actor);
        allowed = true;
      } catch (e) {
        errText = msg(e);
      }
      const ok = exp === 'DENY' ? !allowed : allowed;
      check(`B${String(cell).padStart(2, '0')} ${st.padEnd(9)}+${action.padEnd(8)} 期望${exp.padEnd(9)}`, ok, `实际${allowed ? 'ALLOW' : 'DENY'} ${errText}`);
    }
  }

  // actor 规则1：deliver 仅 leader（pending 态，多非法 actor 全拒）
  const a1 = store.insertLetter({ from: ALICE, to: 'act1', priority: '常规', payload: null }).letterId;
  for (const bad of [ALICE, BOB, COS, '']) {
    check(`B-a1 deliver 拒绝非leader(${bad || '空串'})`, throws(() => store.transition(a1, 'deliver', bad), /actor_forbidden/));
  }
  // actor 规则2：read 仅收件人（delivered 态）——组长不得代标
  const a2 = store.insertLetter({ from: ALICE, to: 'act2', priority: '常规', payload: null }).letterId;
  store.transition(a2, 'deliver', LEADER);
  for (const bad of [LEADER, ALICE, COS, '']) {
    check(`B-a2 read 拒绝非收件人(${bad || '空串'})——不得代标`, throws(() => store.transition(a2, 'read', bad), /actor_forbidden/));
  }
  // escalate 无 store 层 actor 白名单（设计如此：终裁升级权 COS 业务面，store 留痕交审计）
  const a3 = store.insertLetter({ from: ALICE, to: 'act3', priority: '常规', payload: null }).letterId;
  check('B-a3 escalate 任意 actor 可升（store 层无白名单，设计如此）', !throws(() => store.transition(a3, 'escalate', 'random-bystander'), /./));
  const a4 = store.insertLetter({ from: ALICE, to: 'act4', priority: '常规', payload: null }).letterId;
  store.transition(a4, 'deliver', LEADER);
  store.transition(a4, 'read', 'act4');
  check('B-a4 done 任意 actor 可办结（已读后，store 层无 actor 校验）', !throws(() => store.transition(a4, 'done', 'random-bystander'), /./));
  store.close();
}

// ── C. escalate 原子性：人为注入失败验证回滚无中间态 ──
function sectionC(): void {
  console.log('== C. escalate 原子性（注入回滚）==');
  const db = join(WORK, 'c.db');
  const store = createLetterStore(db, { leaderId: LEADER });

  function assertNoIntermediate(tag: string, letterId: string, expectStatus: string, seqBefore: number, ledgerBefore: number): void {
    const after = store.getLetter(letterId)!;
    check(`${tag} 原信状态未变(${expectStatus})`, after.status === expectStatus, `实际${after.status}`);
    check(`${tag} seq 无空洞`, store.getLastSeq() === seqBefore, `实际${store.getLastSeq()} 期望${seqBefore}`);
    check(`${tag} ledger 无残留行`, store.listLedger({ letterId }).length === ledgerBefore, `实际${store.listLedger({ letterId }).length}`);
  }

  // C1 非法 priority 注入（store 层校验先于 INSERT）
  {
    const rec = store.insertLetter({ from: ALICE, to: 'c1', priority: '常规', payload: {} });
    const seqBefore = store.getLastSeq();
    const ledBefore = store.listLedger({ letterId: rec.letterId }).length;
    let threw = false;
    try {
      store.escalateLetter(rec.letterId, LEADER, { from: LEADER, to: COS, priority: '紧急' as never, payload: {} });
    } catch (e) {
      threw = /invalid_priority/.test(msg(e));
    }
    check('C1 注入抛 invalid_priority', threw);
    assertNoIntermediate('C1', rec.letterId, 'pending', seqBefore, ledBefore);
    check('C1 无 ref 新信封残留', store.listLetters({ to: COS }).length === 0);
  }
  // C2 重复 letterId 注入（新信封显式带已存在 id）
  {
    const rec = store.insertLetter({ from: ALICE, to: 'c2', priority: '常规', payload: {} });
    store.insertLetter({ from: LEADER, to: 'seed', priority: '常规', payload: {}, letterId: 'LT-dup-c2' });
    const seqBefore = store.getLastSeq();
    const ledBefore = store.listLedger({ letterId: rec.letterId }).length;
    let threw = false;
    try {
      store.escalateLetter(rec.letterId, LEADER, { from: LEADER, to: COS, priority: '急件', payload: {}, letterId: 'LT-dup-c2' });
    } catch (e) {
      threw = /duplicate_id/.test(msg(e));
    }
    check('C2 注入抛 duplicate_id', threw);
    assertNoIntermediate('C2', rec.letterId, 'pending', seqBefore, ledBefore);
  }
  // C3 ghost refLetterId 注入（insertLetter 冻结校验路径：只许引用已 escalated 原信）
  {
    const alive = store.insertLetter({ from: ALICE, to: 'c3-alive', priority: '常规', payload: {} });
    const seqBefore = store.getLastSeq();
    let threwGhost = false;
    try {
      store.insertLetter({ from: LEADER, to: COS, priority: '急件', payload: {}, refLetterId: 'LT-ghost-c3' });
    } catch (e) {
      threwGhost = /not_found/.test(msg(e));
    }
    let threwUnfrozen = false;
    try {
      store.insertLetter({ from: LEADER, to: COS, priority: '急件', payload: {}, refLetterId: alive.letterId });
    } catch (e) {
      threwUnfrozen = /ref_not_frozen/.test(msg(e));
    }
    check('C3 ghost ref 抛 not_found', threwGhost);
    check('C3 未冻结原信 ref 抛 ref_not_frozen', threwUnfrozen);
    check('C3 seq 无空洞', store.getLastSeq() === seqBefore);
    check('C3 无半行写入', store.listLetters({ to: COS }).length === 0);
  }
  // C4 成功路径：冻结+新信封同事务落位
  {
    const rec = store.insertLetter({ from: ALICE, to: 'c4', priority: '常规', payload: {} });
    const seqBefore = store.getLastSeq();
    const { original, envelope: env } = store.escalateLetter(rec.letterId, LEADER, {
      from: LEADER, to: COS, priority: '急件', payload: { why: 'c4' },
    });
    check('C4 原信冻结 escalated + escalatedAt 留痕', original.status === 'escalated' && !!original.escalatedAt);
    check('C4 新信封 pending + refLetterId 关联原信', env.status === 'pending' && env.refLetterId === rec.letterId);
    check('C4 新信封 seq 连续+1', env.seqNo === seqBefore + 1);
    check('C4 原信轨迹 send→escalate', JSON.stringify(store.listLedger({ letterId: rec.letterId }).map((e) => e.action)) === '["send","escalate"]');
  }
  // C5（附加）自引用注入：新信封 letterId=原信 id → dup → 回滚解冻
  {
    const rec = store.insertLetter({ from: ALICE, to: 'c5', priority: '常规', payload: {} });
    const seqBefore = store.getLastSeq();
    let threw = false;
    try {
      store.escalateLetter(rec.letterId, LEADER, { from: LEADER, to: COS, priority: '急件', payload: {}, letterId: rec.letterId });
    } catch (e) {
      threw = /duplicate_id/.test(msg(e));
    }
    check('C5(附) 自引用注入抛 duplicate_id', threw, threw ? '' : '未抛错');
    check('C5(附) 原信回滚解冻至 pending', store.getLetter(rec.letterId)!.status === 'pending');
    check('C5(附) seq 无空洞', store.getLastSeq() === seqBefore);
  }
  store.close();
}

// ── D. ledger 留痕完整性（send + 全流转轨迹）──
function sectionD(): void {
  console.log('== D. ledger 留痕完整性 ==');
  const db = join(WORK, 'd.db');
  const store = createLetterStore(db, { leaderId: LEADER });

  const rec = store.insertLetter({ from: ALICE, to: BOB, priority: '重要', payload: { n: 1 } });
  store.transition(rec.letterId, 'deliver', LEADER);
  store.transition(rec.letterId, 'read', BOB);
  store.transition(rec.letterId, 'done', BOB);
  const trail = store.listLedger({ letterId: rec.letterId });
  check('D1 全流转4行 send→deliver→read→done', JSON.stringify(trail.map((e) => e.action)) === '["send","deliver","read","done"]', `实际${JSON.stringify(trail.map((e) => e.action))}`);
  check('D2 actor 序列 [from, leader, 收件人, 收件人]', JSON.stringify(trail.map((e) => e.actor)) === JSON.stringify([ALICE, LEADER, BOB, BOB]));
  check('D3 id 严格递增', trail.every((e, i) => i === 0 || e.id > trail[i - 1].id));
  check('D4 at 全非空', trail.every((e) => e.at.length > 0));

  const rec2 = store.insertLetter({ from: BOB, to: ALICE, priority: '常规', payload: {} });
  const { original, envelope: env } = store.escalateLetter(rec2.letterId, LEADER, {
    from: LEADER, to: COS, priority: '急件', payload: { why: 1 },
  });
  const oTrail = store.listLedger({ letterId: original.letterId });
  check('D5 原信轨迹 send→escalate 两行', oTrail.length === 2 && oTrail[0].action === 'send' && oTrail[1].action === 'escalate');
  const eTrail = store.listLedger({ letterId: env.letterId });
  check('D6 新信封轨迹 send 起（actor=升级发起人）', eTrail.length === 1 && eTrail[0].action === 'send' && eTrail[0].actor === LEADER);
  const tail = store.listLedger({ letterId: original.letterId, sinceId: oTrail[0].id });
  check('D7 sinceId 增量读只给后继行', tail.length === 1 && tail[0].action === 'escalate');

  store.recordRetry(env.letterId, 'SSE offline');
  check('D8 recordRetry 不加 ledger 行（留痕在 letters.retries/last_error）', store.listLedger({ letterId: env.letterId }).length === 1);
  check('D8b retries=1 lastError 落库', store.getLetter(env.letterId)!.retries === 1);

  const allLedger = store.listLedger();
  check('D9 台账总行数=7（4+2+1）', allLedger.length === 7, `实际${allLedger.length}`);
  store.close();
}

// ── E. sinceSeq 边界（0/负数/超界）──
function sectionE(): void {
  console.log('== E. sinceSeq 边界 ==');
  const db = join(WORK, 'e.db');
  const store = createLetterStore(db, { leaderId: LEADER });
  for (let i = 1; i <= 5; i++) {
    store.insertLetter({ from: ALICE, to: `rcpt${i}`, priority: '常规', payload: i });
  }
  check('E1 sinceSeq=0 → 全量5封（seq>0 含 seq1）', store.listLetters({ sinceSeq: 0 }).length === 5);
  check('E2 sinceSeq=-3 负数 → 全量5封', store.listLetters({ sinceSeq: -3 }).length === 5);
  const mid = store.listLetters({ sinceSeq: 3 });
  check('E3 sinceSeq=3 → 2封且为 seq[4,5]', JSON.stringify(mid.map((l) => l.seqNo)) === '[4,5]');
  check('E4 sinceSeq=5（=max）→ 0封', store.listLetters({ sinceSeq: 5 }).length === 0);
  check('E5 sinceSeq=999 超界 → 0封', store.listLetters({ sinceSeq: 999 }).length === 0);
  check('E6 结果恒按 seq 升序', JSON.stringify(store.listLetters({ sinceSeq: 0 }).map((l) => l.seqNo)) === '[1,2,3,4,5]');
  store.transition(store.listLetters({ sinceSeq: 4 })[0].letterId, 'deliver', LEADER); // seq5 → delivered
  const combo = store.listLetters({ sinceSeq: 0, status: 'pending', to: 'rcpt5' });
  check('E7 sinceSeq+status+to 组合过滤（seq5 已投非 pending → 空）', combo.length === 0);
  check('E8 sinceSeq 缺省（undefined）→ 无过滤全量5封', store.listLetters({}).length === 5);
  store.close();
}

sectionA();
sectionB();
sectionC();
sectionD();
sectionE();

console.log('\n== 黑盒交叉验证汇总 ==');
console.log(`PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) {
  console.log('失败项:');
  for (const f of failures) console.log(` - ${f}`);
}
process.exit(failCount ? 1 : 0);
