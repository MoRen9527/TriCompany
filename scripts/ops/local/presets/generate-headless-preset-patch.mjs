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
    else if (a === '--with-bridge-tool') args.bridgeToolPath = argv[++i];
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
  const yaml = req(ypath); // require 形取（fsd-l130-srcpm §二：DEFAULT_FULL_SCHEMA 经
  // ESM 互操作 import 形=undefined——CJS require 全量 named exports 在·3dada21 修笔
  // 无效根因避让形）
  if (
    typeof yaml.load !== 'function' || typeof yaml.dump !== 'function' ||
    typeof yaml.Type !== 'function' || typeof yaml.DEFAULT_SCHEMA?.extend !== 'function'
  ) {
    throw new Error(`js-yaml load/dump/Type/DEFAULT_SCHEMA.extend 不可解析（anchor=${anchor}）`);
  }
  return yaml;
}

// !!js 裸串 Type 组装（案 2 实装·fsd-l130-srcpm §二实装参考正身+dump 面实勘勘正）：
// tag 参=裸串形（非 !<> 包裹）。
// · load 面 resolve:()=>true（发布物可信面 read-only·与 dsh loader 同信任域）→
//   标量值=原文串原样（str 保留原文串）；
// · dump 面 js-yaml 4 dumper 机制实勘（lib/dumper.js L776-780：writeNode 隐式探测
//   未命中→explicit 探测 instanceOf/predicate 形→命中即发射 state.tag=type.tag）——
//   裸 resolve 形零 predicate=dump 零重发射（白盒契约④必红）——故 resolve 侧
//   Set 侧信道录表达式串（每 generate() 调用域内精确），predicate 精确匹配之，
//   represent 原样回写 → 产物 `!!js <表达式>` 原样重发射（白盒契约④⑤）。
// · 已知边界（fail-visible 注记）：同一字面量既作表达式又作普通串时普通串同形
//   误标——现实面零（表达式串唯 dsh loader 条件域）·如实注记不改面。
//
// 零注释自检=注释行判·block scalar 状态机精形（2026-11-18 二次勘正）：
// YAML 注释行=首非空白字符 '#' 且【不在 block scalar 内容域】。
// 现役 persona 投影=`prefix: |` 块内 markdown '#' 头（`## 当前角色定位` 族）
// =字符串值合法内容（干跑实锚 2026-11-18）——朴素 trimStart 形仍误伤（内容行
// 缩进被抹后首字符 '#'）——故走状态机：遇块指示器行（`: |`/`: >-` 族）记录其
// 缩进，后续缩进更深（或空白）行=内容域跳过；缩进回落即出域。
// 残差如实注记：普通标量恰以 |/> 收尾且含 ': ' 形=误开域（js-yaml dump 对此类
// 串强制引号·零现实面；append 文本面=块形）——失败向=内容域多跳过注释检查，
// 非误报向。
function hasCommentLine(text) {
  let blockIndent = null;
  for (const line of text.split('\n')) {
    if (!line.trim()) continue; // 空白行中性（YAML 块内空白不断域）
    const indent = line.length - line.trimStart().length;
    if (blockIndent !== null) {
      if (indent > blockIndent) continue; // 块 scalar 内容域
      blockIndent = null; // 缩进回落=出域
    }
    const trimmed = line.trimStart();
    if (trimmed.startsWith('#')) return true; // 块外 '#' 行=注释行
    if (/:\s/.test(line) && /[|>][0-9+\-]*\s*$/.test(line)) {
      blockIndent = indent; // 块指示器开域（key: | / key: >- / |2 族）
    }
  }
  return false;
}
function buildJsTypeAndSchema(yaml) {
  const jsStrings = new Set();
  const JS_TYPE = new yaml.Type('tag:yaml.org,2002:js', {
    kind: 'scalar',
    resolve: (data) => { jsStrings.add(data); return true; },
    represent: (s) => s,
    predicate: (obj) => typeof obj === 'string' && jsStrings.has(obj),
  });
  return { schema: yaml.DEFAULT_SCHEMA.extend([JS_TYPE]), jsStrings };
}

export async function generate({ webPatchPath, anchor, seats, bridgeToolPath }) {
  const yaml = await loadYaml(anchor);
  const { schema: patchSchema } = buildJsTypeAndSchema(yaml);
  const raw = readFileSync(webPatchPath, 'utf-8');
  // !!js tag 面（落实窗步②实勘勘正）：web patch 含 `!!js` 条件表达式（dsh loader
  // 支持形·头部注记「!!js expressions allowed」）——案 2 同形裸 !!js Type 同域解析
  // （发布物可信面 read-only·与 dsh loader 同信任域·load/dump 双面同 schema）。
  const doc = yaml.load(raw, { schema: patchSchema });
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

  // ④.5 T4 桥工具挂载面（notice-168·--with-bridge-tool flag·门禁绿 A/B 承录）：
  //     每席 preset plugins 尾追加 r-duty-send-message 条目（TriRMC scripts/dsh/
  //     插件·name=绝对路径 file 形照 tricompass 先例）——幂等=已含 id 零重复；
  //     无 flag 零变（T3 现役白盒守护面）。
  let bridgeToolInjected = 0;
  if (bridgeToolPath) {
    for (const e of ordered) {
      if (!Array.isArray(e.config.plugins)) e.config.plugins = [];
      if (!e.config.plugins.some((p) => p && p.id === 'r-duty-send-message')) {
        e.config.plugins.push({ id: 'r-duty-send-message', name: bridgeToolPath, config: {} });
        bridgeToolInjected += 1;
      }
    }
  }

  const outDoc = ordered.length ? [{ insert: ordered }] : [];
  const outYaml = yaml.dump(outDoc, { lineWidth: -1, noRefs: true, schema: patchSchema });
  const readout = {
    event: 'generate-headless-preset-patch',
    presets_total: presets.length,
    seats_expected: seats.length,
    seats_emitted: ordered.length,
    extra_seats: extra,
    carrier: 'insert',
    bridge_tool_injected: bridgeToolInjected,
    danger_full_access_scan: 'clean',
    comment_scan: hasCommentLine(outYaml) ? 'hit' : 'clean',
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

// T4 桥工具 append 面补挂（2026-11-18 SDE 施工勘正·runbook ②「14 条目×plugins 各+1」
// 语义对齐）：--append-entry-text=纯文本域拼接——绕过 generate() 的对象域注入域，
// 被续员条目（pm）零桥工具=「每席挂载」基准违面（case2 补席语义反噬）。本函=对象域
// 回环：patchSchema parse→定位续员条目→幂等补挂 r-duty-send-message→同 schema 全量
// re-dump（13 现役条目值面零改·deep-equal 守护面在白盒）。无 bridgeToolPath 或已含
// id=零变（injected=0）。
export async function injectBridgeIntoAppended({ outYaml, seat, bridgeToolPath, anchor }) {
  const yaml = await loadYaml(anchor);
  const { schema: patchSchema } = buildJsTypeAndSchema(yaml);
  const doc = yaml.load(outYaml, { schema: patchSchema });
  const entry = doc[0] && Array.isArray(doc[0].insert)
    ? doc[0].insert.find((e) => e && e.id === `preset-r-duty-${seat}`)
    : null;
  if (!entry) return { outYaml, injected: 0 };
  if (!Array.isArray(entry.config.plugins)) entry.config.plugins = [];
  if (entry.config.plugins.some((p) => p && p.id === 'r-duty-send-message')) {
    return { outYaml, injected: 0 };
  }
  entry.config.plugins.push({ id: 'r-duty-send-message', name: bridgeToolPath, config: {} });
  const dumped = yaml.dump(doc, { lineWidth: -1, noRefs: true, schema: patchSchema });
  return { outYaml: dumped, injected: 1 };
}

export async function main(argv) {
  const args = parseArgs(argv);
  let { outYaml, readout } = await generate({
    webPatchPath: args.webPatch,
    anchor: args.anchor,
    seats: args.seats,
    bridgeToolPath: args.bridgeToolPath,
  });
  if (args.appendEntryText) {
    const appended = appendEntryText(outYaml, readFileSync(args.appendEntryText, 'utf-8'));
    outYaml = appended.outYaml;
    readout = { ...readout, appended_entries: [appended.seat] };
    if (args.bridgeToolPath) {
      const injected = await injectBridgeIntoAppended({
        outYaml,
        seat: appended.seat,
        bridgeToolPath: args.bridgeToolPath,
        anchor: args.anchor,
      });
      outYaml = injected.outYaml;
      readout.bridge_tool_injected = (readout.bridge_tool_injected ?? 0) + injected.injected;
    }
  }
  if (hasCommentLine(outYaml)) {
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
