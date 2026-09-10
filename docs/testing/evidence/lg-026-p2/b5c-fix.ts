import { createLetterStore } from 'file:///D:/Code/ai/TriRLC/src/letter-store/store.ts';
import { DatabaseSync } from 'node:sqlite';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const p = join(tmpdir(), 'b5c-fix.db');
const s = createLetterStore(p, { leaderId: '组长' });
const rec = s.insertLetter({ from: 'a', to: 'b', priority: '常规', payload: 1 });
s.close();
const db = new DatabaseSync(p);
let anyAction = false, badFk = false;
try { db.prepare("INSERT INTO ledger (letter_id, actor, action) VALUES (?, 'a', 'any_custom_action_xyz')").run(rec.letterId); anyAction = true; } catch (e) { console.log('抛:', (e as Error).message.split('\n')[0]); }
try { db.prepare("INSERT INTO ledger (letter_id, actor, action) VALUES ('ghost', 'a', 'x')").run(); } catch (e) { badFk = true; }
console.log(JSON.stringify({ 合法信存在时任意action可写: anyAction, 外键拒ghost信: badFk }));
db.close();
