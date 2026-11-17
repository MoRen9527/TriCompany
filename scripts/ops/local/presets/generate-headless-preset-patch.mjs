#!/usr/bin/env node
// ── T3-b headless preset patch 生成器（BOD 144②·CTO 门禁绿·FD 主刀）──
// input = web patch preset 段（转译器 v2 发布物 dump·READ-ONLY 直读——web patch
//         零写照承）→ output = headless cordis.patch.yml（13 席 preset entries）。
// 形面：preset 条目=preset-r-duty-<seat>（id/name/config{description,plugins 族}
// ·T3-a 勘形窗③样例实锚）——条目原样搬运（转译器内容面零改写·仅载体 web→headless）。
// 护栏（fsd-t3-design-20261117.md §四）：
//   · 零注释形（BOD 裁135 修②教训——dsh patch 解析器不支持注释行·产出首行即条目行）
//   · 降权自检（charter 验收门 4③）：序列化条目面 danger-full-access 零容忍
//   · 13 席齐断言（charter 验收门）：缺席席 fail-visible 逐名列·额外席 warn
//   · 零写面：input 只读·--out 显式才落盘（缺省 stdout——部署窗落位归值席定）
// 运行域：node ≥18·js-yaml 经 dsh 安装锚解析（--anchor·缺省 /srv/fleet/dsh——
// 零新增依赖照 fsd-adopt-runner install-anchored 先例）。
// 读数面：JSON 一行→stderr（D-46：状态/计数面零 preset 值面回显）。
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const SEATS_13 = ['cos', 'coo', 'cao', 'cpo', 'cto', 'cho', 'cfo', 'cso', 'fsd', 'sde', 'ste', 'pm', 'rdt'];

function parseArgs(argv) {
  const args = { seats: SEATS_13, out: null, anchor: '/srv/fleet/dsh', webPatch: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--web-patch') args.webPatch = argv[++i];
    else if (a === '--out') args.out = argv[++i];
    else if (a === '--append-entry-text') args.appendEntryText = argv[++i];
    else if (a === '--anchor') args.anchor = argv[++i];
    else if (a === '--seats') args.seats = argv[++i].split(',').map((s) => s.trim()).filter(Boolean);
    else throw new Error(`未知参数 ${a}`);
  }
  if (!args.webPatch) throw new Error('--web-patch 必载（web patch preset 段 dump·READ-ONLY）');
  return args;
}

async function loadYaml(anchor) {
  const req = createRequire(join(anchor, 'package.json'));
  const ypath = req.resolve('js-yaml');
  const mod = await import(pathToFileURL(ypath).href);
  const yaml = mod.default && mod.default.load ? mod.default : mod;
  if (typeof yaml.load !== 'function' || typeof yaml.dump !== 'function') {
    throw new Error(`js-yaml load/dump 不可解析（anchor=${anchor}）`);
  }
  return yaml;
}

export async function generate({ webPatchPath, anchor, seats }) {
  const yaml = await loadYaml(anchor);
  const raw = readFileSync(webPatchPath, 'utf-8');
  // !!js tag 面（落实窗步②实勘勘正）：web patch 含 `!!js` 条件表达式（dsh loader
  // 支持形·头部注记「!!js expressions allowed」）——DEFAULT_FULL_SCHEMA 同域解析
  // （发布物可信面 read-only·与 dsh loader 同信任域）。
  const doc = yaml.load(raw, { schema: yaml.DEFAULT_FULL_SCHEMA ?? yaml.DEFAULT_SCHEMA });
  if (!Array.isArray(doc)) throw new Error(`web patch 顶层非数组（got ${typeof doc}）`);

  // ① preset 条目过滤（双形面·落实窗步①实勘勘正）：顶层直挂形+**insert 解包形**
  //    （web patch=顶层单条 `- insert:` 数组内嵌 preset 条目——转译器 v2 发布形实锚
  //    2026-11-17T15:5xZ 落实窗步① dump）。条目原样搬运（内容面零改写·仅载体）。
  const presets = [];
  for (const e of doc) {
    if (!e || typeof e !== 'object') continue;
    if (typeof e.id === 'string' && e.id.startsWith('preset-r-duty-')) presets.push(e);
    if (Array.isArray(e.insert)) {
      for (const item of e.insert) {
        if (item && typeof item.id === 'string' && item.id.startsWith('preset-r-duty-')) presets.push(item);
      }
    }
  }
  const bySeat = new Map();
  for (const e of presets) {
    const seat = e.id.slice('preset-r-duty-'.length);
    bySeat.set(seat, e);
  }

  // ② 13 席齐断言（缺席=fail-visible 逐名列·额外席 warn 名单）
  const missing = seats.filter((s) => !bySeat.has(s));
  if (missing.length) {
    throw new Error(`13 席齐断言失败——缺席席: ${missing.join(', ')}（web patch preset 段 ${presets.length} 条）`);
  }
  const extra = [...bySeat.keys()].filter((s) => !seats.includes(s));

  // ③ 降权自检（charter 验收门 4③·danger-full-access 零容忍）
  const serialized = JSON.stringify(presets);
  if (serialized.includes('danger-full-access')) {
    throw new Error('降权自检失败——preset 条目面含 danger-full-access 值（fail-visible 拒产）');
  }

  // ④ headless patch 组装（零注释形·条目原样·首行即条目行——insert 载体形照
  //    转译器发布形：`- insert:` 顶层单条内嵌 preset 数组·registry README 官方正形）
  const ordered = seats.map((s) => bySeat.get(s)).concat(extra.map((s) => bySeat.get(s)));
  const outDoc = ordered.length ? [{ insert: ordered }] : [];
  const outYaml = yaml.dump(outDoc, { lineWidth: -1, noRefs: true, schema: yaml.DEFAULT_FULL_SCHEMA ?? undefined });
  const readout = {
    event: 'generate-headless-preset-patch',
    presets_total: presets.length,
    seats_expected: seats.length,
    seats_emitted: ordered.length,
    extra_seats: extra,
    carrier: 'insert',
    danger_full_access_scan: 'clean',
    comment_scan: outYaml.includes('#') ? 'hit' : 'clean',
  };
  return { outYaml, readout };
}

/**
 * 增量条目文本续员（L130 T-b·notice-160 源侧补 pm 形·纯文本面零 parse 零 tag 墙）：
 * append 块（web patch insert 数组续员形·4 空格缩进 `- id: preset-r-duty-<seat>`
 * 起）接产物尾部——!!js 行原样保留（零解析域）。校验面：首行缩进+条目 id 形。
 */
export function appendEntryText(outYaml, entryText) {
  const text = entryText.endsWith('\n') ? entryText : entryText + '\n';
  const first = text.split('\n')[0];
  if (!first.startsWith('    - id: preset-r-duty-')) {
    throw new Error(`append-entry-text: 首行须为 4 空格缩进条目行（got ${JSON.stringify(first.slice(0, 40))}）`);
  }
  const seat = first.slice('    - id: preset-r-duty-'.length).trim();
  if (!/^[a-z0-9][a-z0-9-]*$/.test(seat)) {
    throw new Error(`append-entry-text: 条目 seat 越形 ${JSON.stringify(seat)}`);
  }
  if (outYaml.includes(`id: preset-r-duty-${seat}\n`)) {
    throw new Error(`append-entry-text: 条目已存在（preset-r-duty-${seat}）——零重复面`);
  }
  const joined = outYaml.endsWith('\n') ? outYaml + text : outYaml + '\n' + text;
  return { outYaml: joined, seat };
}

export async function main(argv) {
  const args = parseArgs(argv);
  let { outYaml, readout } = await generate({
    webPatchPath: args.webPatch,
    anchor: args.anchor,
    seats: args.seats,
  });
  if (args.appendEntryText) {
    const appended = appendEntryText(outYaml, readFileSync(args.appendEntryText, 'utf-8'));
    outYaml = appended.outYaml;
    readout = { ...readout, appended_entries: [appended.seat] };
  }
  if (outYaml.includes('#')) {
    throw new Error('零注释自检失败——产出含注释行（BOD 裁135 修②教训面）');
  }
  if (args.out && args.out !== '-') {
    writeFileSync(args.out, outYaml, 'utf-8');
    readout.written_to = args.out;
  } else {
    process.stdout.write(outYaml);
    readout.written_to = 'stdout';
  }
  process.stderr.write(JSON.stringify(readout) + '\n');
}

if (process.argv[1] && process.argv[1].endsWith('generate-headless-preset-patch.mjs')) {
  main(process.argv.slice(2)).catch((err) => {
    process.stderr.write(`generate-headless-preset-patch: ${err && err.message ? err.message : err}\n`);
    process.exit(1);
  });
}
