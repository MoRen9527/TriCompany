// ── T3-b/T3-c 生成器白盒族（node --test·BOD 144②·FD 主刀）──
// 运行形（sg 面白盒）: ~/node22/bin/node --test scripts/ops/local/presets/presets-whitebox.test.mjs
// （js-yaml 解析域=--anchor 参数化·白盒传沙箱锚——零仓内依赖）
// 部署窗运行形（河源）: node generate-headless-preset-patch.mjs --web-patch <dump> --anchor /srv/fleet/dsh …
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { generate } from './generate-headless-preset-patch.mjs';
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
