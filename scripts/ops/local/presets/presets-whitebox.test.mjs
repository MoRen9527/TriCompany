// ── T3-b/T3-c 生成器白盒族（node --test·BOD 144②·FD 主刀）──
// 运行形（sg 面白盒）: ~/node22/bin/node --test scripts/ops/local/presets/presets-whitebox.test.mjs
// （js-yaml 解析域=--anchor 参数化·白盒传沙箱锚——零仓内依赖）
// 部署窗运行形（河源）: node generate-headless-preset-patch.mjs --web-patch <dump> --anchor /srv/fleet/dsh …
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { generate, appendEntryText } from './generate-headless-preset-patch.mjs';
import { scanRegistry, readSessionId } from './generate-session-registry.mjs';

const SANDBOX_ANCHOR = process.env.T3_YAML_ANCHOR ?? '/srv/fleet/.dsh-sandbox2';
const SEATS = ['cos', 'coo', 'cao', 'cpo', 'cto', 'cho', 'cfo', 'cso', 'fsd', 'sde', 'ste', 'pm', 'rdt'];

function seatEntry(seat, extra = {}) {
  return {
    id: `preset-r-duty-${seat}`,
    name: `preset-r-duty-${seat}`,
    config: { description: `${seat} 席 preset（fixture）`, plugins: { family: 'standard' }, ...extra },
  };
}

async function loadYamlFrom(anchor) {
  const req = createRequire(join(anchor, 'package.json'));
  const ypath = req.resolve('js-yaml');
  const mod = await import(pathToFileURL(ypath).href);
  return mod.default && mod.default.load ? mod.default : mod;
}

test('T3-b: preset 过滤面——insert 解包形（转译器 v2 发布形实锚·落实窗步①勘正）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-insert-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    // web patch 实形=顶层单条 `- insert:` 内嵌 preset 数组（转译器发布形）
    const webPatch = [
      { id: 'timer', name: '@deepseek-ai/cordis-plugin-timer' },
      { insert: [seatEntry('cos'), seatEntry('cto'), seatEntry('pm')] },
    ];
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump(webPatch, { lineWidth: -1 }), 'utf-8');
    const { outYaml, readout } = await generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos', 'cto'] });
    assert.equal(readout.presets_total, 3, 'insert 解包面三 preset 全收');
    assert.equal(readout.seats_emitted, 3, '清单序前置+额外席殿后（全量携带·warn 名单承载）');
    assert.equal(readout.carrier, 'insert');
    assert.deepEqual(readout.extra_seats, ['pm'], '额外席 warn 名单面');
    const back = yaml.load(outYaml);
    assert.equal(back.length, 1, '载体=insert 单条');
    assert.ok(Array.isArray(back[0].insert), 'insert 数组形');
    assert.deepEqual(back[0].insert.map((e) => e.id), ['preset-r-duty-cos', 'preset-r-duty-cto', 'preset-r-duty-pm'],
      '清单序前置+额外席殿后');
    assert.equal(back[0].insert[0].config.description, 'cos 席 preset（fixture）', '条目原样搬运');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-b: preset 过滤面——顶层直挂形兼容（双形面）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-gen-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    const webPatch = [
      { id: 'timer', name: '@deepseek-ai/cordis-plugin-timer' },
      seatEntry('cos'),
      seatEntry('cto'),
      { id: 'other', name: 'x' },
    ];
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump(webPatch, { lineWidth: -1 }), 'utf-8');
    const { outYaml, readout } = await generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos', 'cto'] });
    assert.equal(readout.presets_total, 2);
    assert.equal(readout.seats_emitted, 2);
    const back = yaml.load(outYaml);
    assert.equal(back.length, 1, 'insert 载体单条');
    assert.deepEqual(back[0].insert.map((e) => e.id), ['preset-r-duty-cos', 'preset-r-duty-cto']);
    assert.ok(!JSON.stringify(back).includes('"timer"'), '非 preset 条目零带');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-b: 13 席齐断言——缺席席 fail-visible 逐名列', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-miss-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump([seatEntry('cos')], { lineWidth: -1 }), 'utf-8');
    await assert.rejects(
      () => generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: SEATS }),
      (err) => err.message.includes('缺席席') && err.message.includes('cto') && err.message.includes('rdt'),
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-b: 降权自检——danger-full-access 零容忍（charter 验收门 4③）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-danger-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump([seatEntry('cos', { permissions: 'danger-full-access' })], { lineWidth: -1 }), 'utf-8');
    await assert.rejects(
      () => generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos'] }),
      /danger-full-access/,
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-b: 零注释形——产出首行即条目行·全件无 #（BOD 裁135 修②教训面）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-comment-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump([seatEntry('cos')], { lineWidth: -1 }), 'utf-8');
    const { outYaml, readout } = await generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos'] });
    const firstLine = outYaml.split('\n')[0];
    assert.ok(firstLine.startsWith('- '), `首行必须为条目行: ${JSON.stringify(firstLine)}`);
    assert.equal(readout.comment_scan, 'clean');
    assert.ok(!outYaml.includes('#'), '全件零注释');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-c: 三键映射面——r-duty-<seat> 目录扫描+session id 读形（T2 listAgents 同源）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3c-reg-'));
  try {
    for (const seat of ['cos', 'cto']) {
      const d = join(dir, `r-duty-${seat}`);
      mkdirSync(d, { recursive: true });
      writeFileSync(join(d, 'session.json'), JSON.stringify({ name: `r-duty-${seat}`, sessionId: 'b38ba22d-9f06-4443-b295-c5825026404a' }));
    }
    const { registry, readout } = scanRegistry({ sessionsRoot: dir, seats: ['cos', 'cto'] });
    assert.equal(readout.seats_emitted, 2);
    assert.equal(readout.uuid_form_hits, 2);
    const cto = registry.find((e) => e.seat === 'cto');
    assert.equal(cto.session_id, 'b38ba22d-9f06-4443-b295-c5825026404a');
    assert.equal(cto.workspace, 'r-duty-cto');
    assert.equal(cto.employee_id, 'cto', '缺省 manifest=短名自映射');
    // id 读形（raw.sessionId ?? raw.id）
    assert.equal(readSessionId({ id: 'alt-id' }), 'alt-id');
    assert.equal(readSessionId({}), '');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-c: 缺席席 fail-visible+坏件跳过如实面', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3c-miss-'));
  try {
    const d = join(dir, 'r-duty-cos');
    mkdirSync(d, { recursive: true });
    writeFileSync(join(d, 'bad.json'), '{not-json');
    writeFileSync(join(d, 'ok.json'), JSON.stringify({ sessionId: '11111111-2222-3333-4444-555555555555' }));
    await assert.rejects(
      async () => scanRegistry({ sessionsRoot: dir, seats: SEATS }),
      (err) => err.message.includes('缺席席') && err.message.includes('cto'),
    );
    // 单席面（cos 在册）：坏件跳过+ok 件命中
    const { registry, readout } = scanRegistry({ sessionsRoot: dir, seats: ['cos'] });
    assert.equal(registry.length, 1);
    assert.ok(readout.warns.some((w) => w.seat === 'cos' && w.note.includes('坏 json')), '坏件跳过 warn 如实');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T3-c: manifest 精化形——employeeId 键位承接', () => {
  const dir = mkdtempSync(join(tmpdir(), 't3c-manifest-'));
  try {
    const d = join(dir, 'r-duty-cos');
    mkdirSync(d, { recursive: true });
    writeFileSync(join(d, 's.json'), JSON.stringify({ sessionId: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee' }));
    const { registry } = scanRegistry({
      sessionsRoot: dir, seats: ['cos'],
      manifest: { cos: 'ceo-chief-of-staff' },
    });
    assert.equal(registry[0].employee_id, 'ceo-chief-of-staff', 'manifest 精化面（TriCompany 正名承接位）');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('smoke: 生成器脚本文件在位（ops-local face 邻位）', () => {
  const here = new URL('.', import.meta.url).pathname;
  assert.ok(existsSync(join(here, 'generate-headless-preset-patch.mjs')));
  assert.ok(existsSync(join(here, 'generate-session-registry.mjs')));
});

// ── T4 桥工具挂载面（notice-168·--with-bridge-tool 延一跳）────────────────

test('T4: --with-bridge-tool 挂载面——每席 plugins 尾追加 r-duty-send-message', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't4-bridge-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    const webPatch = [{ insert: [seatEntry('cos'), seatEntry('cto'), seatEntry('pm')] }];
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump(webPatch, { lineWidth: -1 }), 'utf-8');
    const toolPath = '/srv/fleet/TriRMC/scripts/dsh/r-duty-send-message/index.mjs';
    const { outYaml, readout } = await generate({
      webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos', 'cto'], bridgeToolPath: toolPath,
    });
    assert.equal(readout.bridge_tool_injected, 3, '全量携带面=额外席殿后亦挂（三席各一件）');
    const back = yaml.load(outYaml);
    const inserted = back[0].insert;
    for (const e of inserted) {
      const tail = e.config.plugins[e.config.plugins.length - 1];
      assert.deepEqual(tail, { id: 'r-duty-send-message', name: toolPath, config: {} },
        `${e.id}: 尾件=桥工具条目（路径 file 形照 tricompass 先例）`);
    }
    // 幂等：已含 id 零重复（二次生成域内模拟——手工前置一条再跑）
    const webPatch2 = [{ insert: [
      { ...seatEntry('cos'), config: { description: 'x', plugins: [{ id: 'r-duty-send-message', name: toolPath, config: {} }] } },
      seatEntry('cto'),
    ] }];
    const p2 = join(dir, 'web.patch.2.yml');
    writeFileSync(p2, yaml.dump(webPatch2, { lineWidth: -1 }), 'utf-8');
    const r2 = await generate({ webPatchPath: p2, anchor: SANDBOX_ANCHOR, seats: ['cos', 'cto'], bridgeToolPath: toolPath });
    assert.equal(r2.readout.bridge_tool_injected, 1, '幂等面=已含 id 零重复（仅 ct 注入）');
    const back2 = yaml.load(r2.outYaml);
    assert.equal(back2[0].insert[0].config.plugins.filter((x) => x.id === 'r-duty-send-message').length, 1, 'cos 零重复');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('T4: 无 flag 零变（T3 现役白盒守护面）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't4-noflag-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    const webPatch = [{ insert: [seatEntry('cos'), seatEntry('cto')] }];
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump(webPatch, { lineWidth: -1 }), 'utf-8');
    const { outYaml, readout } = await generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos', 'cto'] });
    assert.equal(readout.bridge_tool_injected, 0, '无 flag=零注入');
    const back = yaml.load(outYaml);
    for (const e of back[0].insert) {
      assert.ok(!JSON.stringify(e.config.plugins).includes('r-duty-send-message'), '无 flag=零桥工具条目');
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

// ── L130 源侧补 pm（notice-160/161·T-b/c 修面+验收白盒）─────────────────

/** 案 2 同形白盒解析面（测试工具域·裸 !!js Type+Schema.extend——实参形=tag 串直书）。 */
async function loadYamlWithJsTag() {
  const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
  const JsTag = new yaml.Type('tag:yaml.org,2002:js', { kind: 'scalar', resolve: () => true, represent: (s) => s });
  const schema = yaml.DEFAULT_SCHEMA.extend(JsTag);
  return (text) => yaml.load(text, { schema });
}

test('L130 T-b: pm 条目产件结构断言——seat 面/plugins 套/persona 投影/!!js 保留', async () => {
  const here = new URL('.', import.meta.url).pathname;
  const entryText = readFileSync(join(here, 'pm-entry-r-duty-pm.yml'), 'utf-8');
  // 首行缩进=4 空格 insert 续员形（append 面合法性）
  assert.ok(entryText.split('\n')[0].startsWith('    - id: preset-r-duty-pm'), '产件首行=续员条目行');
  const load = await loadYamlWithJsTag();
  const e = load(entryText)[0];
  assert.equal(e.id, 'preset-r-duty-pm');
  assert.equal(e.name, '@deepseek-ai/dsh-agent-preset', '挂载插件=现役形');
  assert.equal(e.config.id, 'r-duty-pm');
  assert.equal(e.config.name, 'ProductManager', 'frontmatter name 实锚');
  assert.ok(e.config.description.includes('产品经理（全栈向）'), 'description=frontmatter 实锚');
  assert.equal(e.config.plugins.length, 20, 'plugins standard 套=20 件照 cos 条目形');
  const persona = e.config.plugins.find((p) => p.id === 'persona');
  assert.ok(persona.config.prefix.includes('## 当前角色定位'), 'persona=pm agent-body 投影（首节）');
  assert.ok(persona.config.prefix.includes('树执行前必查 COS 授权'), 'persona 投影含护栏节（树执行门禁）');
  assert.ok(persona.config.prefix.includes('标注与手稿的版本差'), 'persona 投影至尾节');
  assert.ok(!('suffix' in persona.config), 'suffix 零造形（pm body 无该面节·如实投影）');
  assert.equal(e.config.plugins.find((p) => p.id === 'tricompass-context').config.file,
    '.claude/compass/product-manager.session.md', 'compass 尾件=pm 面');
  const jsRows = e.config.plugins.filter((p) => typeof p.disabled === 'string' && p.disabled.includes('process.platform'));
  assert.equal(jsRows.length, 2, '!!js 双行保留（tool-bash/pwsh disabled 照 cos 形）');
  assert.ok(!JSON.stringify(e.config.plugins).includes('danger-full-access'), '降权自检零命中（charter 门 4③）');
});

test('L130 T-b: append-entry-text 续员面——文本原样+!!js 保留+现役条目零损+零重复守卫', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-append-'));
  try {
    const yaml = await loadYamlFrom(SANDBOX_ANCHOR);
    // fixture 现役 2 条目（insert 形）
    const webPatch = [{ insert: [seatEntry('cos'), seatEntry('cto')] }];
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, yaml.dump(webPatch, { lineWidth: -1 }), 'utf-8');
    const { outYaml } = await generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats: ['cos', 'cto'] });
    // append 面：文本块直拼（!!js 行原样·零 parse 域）
    const entryText = '    - id: preset-r-duty-pm\n      name: \'@deepseek-ai/dsh-agent-preset\'\n      config:\n        id: r-duty-pm\n        plugins:\n          - id: tool-bash\n            name: \'@deepseek-ai/dsh-tool-bash\'\n            disabled: !!js process.platform === \'win32\'\n';
    const appended = appendEntryText(outYaml, entryText);
    assert.ok(appended.outYaml.includes('id: preset-r-duty-cos'), '现役条目零损（文本面在）');
    assert.ok(appended.outYaml.includes('id: preset-r-duty-cto'), '现役条目零损');
    assert.ok(appended.outYaml.includes('!!js process.platform'), '!!js 行文本原样（零解析域）');
    assert.equal(appended.seat, 'pm');
    // 拼装件可 parse 回读（案 2 同形 Type）——14 条目形语义等价
    const load = await loadYamlWithJsTag();
    const back = load(appended.outYaml);
    const ids = back[0].insert.map((e) => e.id);
    assert.deepEqual(ids, ['preset-r-duty-cos', 'preset-r-duty-cto', 'preset-r-duty-pm'], '续员面=数组尾员');
    // 零重复守卫
    assert.throws(() => appendEntryText(appended.outYaml, entryText), /已存在/, '同 seat 二次 append=拒');
    // 越形守卫
    assert.throws(() => appendEntryText(outYaml, '  - id: preset-r-duty-x\n'), /4 空格缩进/, '首行缩进校验');
    assert.throws(() => appendEntryText(outYaml, '    - id: preset-r-duty-BAD SEAT\n'), /越形/, 'seat 形校验');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

// ── notice-156 施工要件④：!!js 形族三形 fixture+契约断言（白盒面协作·SDE 案 2 主施工）──
// 三形（web patch 实勘形·BOD 裁样）：①裸单行表达式（tool-bash disabled）②带引号表达式
// （profileContext 守卫·单引号转义形）③折叠块 >- 多行表达式（otel url 形）。
// 契约断言：全 doc parse 零炸→preset 13 块照常提取→!!js 行原样保留（round-trip
// 语义保真=产物回读串值===原表达式串）。
// **红基线承录（2026-11-17T16:0xZ）**：当前生成器（3dada21·DEFAULT_FULL_SCHEMA 形）
// 跑本面=unknown tag 红——候 SDE 案 2（自定义裸 !!js Type）落地转绿。
const RAW_JS_FIXTURE = `
- id: timer
  name: '@deepseek-ai/cordis-plugin-timer'
- id: tool-bash
  name: '@deepseek-ai/dsh-tool-bash'
  disabled: !!js process.platform === 'win32'
- id: tool-pwsh
  name: '@deepseek-ai/dsh-tool-pwsh'
  disabled: !!js '!ctx.get(''profileContext'')'
- id: otel
  name: '@deepseek-ai/dsh-otel'
  config:
    mode: !!js process.env.DSH_TELEMETRY_MODE || 'FEEDBACK_ONLY'
    url: !!js >-
      process.env.DSH_TELEMETRY_OTLP_URL ??
      'https://collector.example/v1/logs'
- insert:
`;

function fixturePreset(seat, withJsRow) {
  const lines = [
    `    - id: preset-r-duty-${seat}`,
    `      name: preset-r-duty-${seat}`,
    `      config:`,
    `        description: "${seat} 席 preset（notice-156 fixture）"`,
    `        plugins:`,
    `          - id: agent-instructions`,
    `            name: '@deepseek-ai/dsh-agent-instructions'`,
    `            config:`,
    `              maxBytes: 65536`,
  ];
  if (withJsRow) {
    lines.push(
      `          - id: tool-bash`,
      `            name: '@deepseek-ai/dsh-tool-bash'`,
      `            disabled: !!js process.platform !== 'win32'`,
    );
  }
  return lines.join('\n') + '\n';
}

test('T3-b: !!js 形族三形 fixture——全 doc parse→preset 13 块+!!js 行原样保留（notice-156 要件④）', async () => {
  const dir = mkdtempSync(join(tmpdir(), 't3b-jsfix-'));
  try {
    const seats = SEATS;
    const fixtureText =
      RAW_JS_FIXTURE +
      seats.map((s, i) => fixturePreset(s, i === 0)).join('');
    const p = join(dir, 'web.patch.yml');
    writeFileSync(p, fixtureText, 'utf-8');

    // 契约①②③：全 doc parse 零炸（三形 !!js 过面）+preset 13 块照常提取
    const { outYaml, readout } = await generate({ webPatchPath: p, anchor: SANDBOX_ANCHOR, seats });
    assert.equal(readout.presets_total, 13, '全 doc parse 后 preset 13 块照常提取');
    assert.equal(readout.seats_emitted, 13);
    assert.equal(readout.danger_full_access_scan, 'clean');

    // 契约④：!!js 行原样保留（preset 内 !!js 行进产物）
    assert.ok(outYaml.includes('!!js process.platform !=='), 'preset 内 !!js 行原样保留面');

    // 契约⑤（round-trip 语义保真）：产物回读→preset 内 tool-bash.disabled 串值
    // ===原表达式串（案 2 形=yaml.Type 自定义裸 !!js——回读面用生成器同源 loader 面
    // ——白盒经生成器产物+同 anchor 解析域回读；回读面=生成器同源 loader 面
    // （案 2 同形 Type·SDE 实装勘正 2026-11-18：原 DEFAULT_FULL_SCHEMA 形读含
    // !!js 产物必炸 unknown tag=契约⑤代码与同源注释背离·3dada21 残面勘正形）
    const back = (await loadYamlWithJsTag())(outYaml);
    const cos = back[0].insert.find((e) => e.id === 'preset-r-duty-cos');
    const toolBash = (cos.config.plugins ?? []).find((t) => t.id === 'tool-bash');
    assert.ok(toolBash, 'preset 内 tool-bash 行在');
    assert.equal(toolBash.disabled, "process.platform !== 'win32'", '!!js round-trip 串值保真');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
