#!/usr/bin/env node
// ── T3-c 会话注册表生成器（BOD 144②·CTO 门禁绿·FD 主刀）──
// input = ~/.dsh/sessions 面扫描（r-duty-<seat> 工作区族·listAgents 现役扫描形
//         复用 8252d9f 谱系）→ output = 三键映射 registry JSON：
//         { seat, session_id, employee_id, workspace }[]（T4 桥消费形）。
// 面形（T2 ④-1 映射表+charter T3 行）：r-duty-<seat> 目录名→seat；session 文件
// 内 id（raw.sessionId ?? raw.id·T2 listAgents 读形同源）；employeeId=短名映射
// （--manifest 精化形·缺省=短名自映射）。
// fail-visible：缺席席逐名列（charter 验收门「13 席齐」）；单文件坏=跳过不炸
// （如实面·warn 计数）；非 uuid 形 id=fail 记录保留原值（如实不造替身）。
// 零写面：sessions 根只读·--out 显式才落盘（缺省 stdout）。
// 读数面：JSON 一行→stderr（D-46 状态/计数面）。
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const SEATS_13 = ['cos', 'coo', 'cao', 'cpo', 'cto', 'cho', 'cfo', 'cmo', 'cso', 'fsd', 'sde', 'ste', 'rdt'];
const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function parseArgs(argv) {
  const args = { sessionsRoot: null, out: null, seats: SEATS_13, manifest: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--sessions-root') args.sessionsRoot = argv[++i];
    else if (a === '--out') args.out = argv[++i];
    else if (a === '--seats') args.seats = argv[++i].split(',').map((s) => s.trim()).filter(Boolean);
    else if (a === '--manifest') args.manifest = JSON.parse(readFileSync(argv[++i], 'utf-8'));
    else throw new Error(`未知参数 ${a}`);
  }
  if (!args.sessionsRoot) throw new Error('--sessions-root 必载（~/.dsh/sessions 面）');
  return args;
}

/** 会话文件 id 读形（T2 listAgents 同源：raw.sessionId ?? raw.id ?? ''）。 */
export function readSessionId(doc) {
  return String(doc.sessionId ?? doc.id ?? '');
}

export function scanRegistry({ sessionsRoot, seats, manifest }) {
  const employee = manifest ?? Object.fromEntries(seats.map((s) => [s, s]));
  const entries = [];
  const missing = [];
  const warns = [];
  for (const seat of seats) {
    const dir = join(sessionsRoot, `r-duty-${seat}`);
    let files = [];
    try {
      files = readdirSync(dir).filter((f) => {
        try { return statSync(join(dir, f)).isFile(); } catch { return false; }
      });
    } catch {
      missing.push(seat);
      continue;
    }
    let hit = null;
    let bad = 0;
    for (const f of files) {
      let doc;
      try {
        doc = JSON.parse(readFileSync(join(dir, f), 'utf-8'));
      } catch {
        bad += 1;
        continue;
      }
      const sid = readSessionId(doc);
      if (sid) { hit = { seat, session_id: sid, employee_id: employee[seat] ?? seat, workspace: `r-duty-${seat}`, source_file: f }; break; }
    }
    if (!hit) { missing.push(seat); continue; }
    if (!UUID_RE.test(hit.session_id)) {
      warns.push({ seat, note: `非 uuid 形 id（如实保留·T0 ④ 形面勘定项）: ${hit.session_id.slice(0, 8)}…` });
    }
    if (bad) warns.push({ seat, note: `坏 json 文件跳过 ${bad} 件` });
    entries.push(hit);
  }
  if (missing.length) {
    throw new Error(`会话注册表 13 席齐断言失败——缺席席（无 r-duty-<seat> 工作区或零 id 读）: ${missing.join(', ')}`);
  }
  return {
    registry: entries,
    readout: {
      event: 'generate-session-registry',
      seats_expected: seats.length,
      seats_emitted: entries.length,
      uuid_form_hits: entries.filter((e) => UUID_RE.test(e.session_id)).length,
      warns,
    },
  };
}

export function main(argv) {
  const args = parseArgs(argv);
  const { registry, readout } = scanRegistry(args);
  const out = JSON.stringify({ registrations: registry }, null, 2) + '\n';
  return { out, readout, outPath: args.out && args.out !== '-' ? args.out : null };
}

// 写面（异步面缺省 stdout——落盘=显式 --out 由调用方 writeFileSync 同步形）
if (process.argv[1] && process.argv[1].endsWith('generate-session-registry.mjs')) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const { out, readout, outPath } = main(process.argv.slice(2));
    if (outPath) {
      const { writeFileSync } = await import('node:fs');
      writeFileSync(outPath, out, 'utf-8');
      readout.written_to = outPath;
    } else {
      process.stdout.write(out);
      readout.written_to = 'stdout';
    }
    process.stderr.write(JSON.stringify(readout) + '\n');
  } catch (err) {
    process.stderr.write(`generate-session-registry: ${err && err.message ? err.message : err}\n`);
    process.exit(1);
  }
}
