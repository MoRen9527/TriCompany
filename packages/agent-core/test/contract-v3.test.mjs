// Contract v3.0 unit tests（node:test，测 dist 产物）
// 覆盖验收口径 ② 负路径 + ③ strict 形状一致 + 正例默认值填充。
// 运行：npm test（build 后）
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  loadContractV3,
  resolveContractsV3,
  ContractV3Error,
  CONTRACT_V3_VERSION,
} from '../dist/index.js';

const fixturesDir = join(dirname(fileURLToPath(import.meta.url)), 'fixtures');

test('valid v3 contract parses with defaults filled', () => {
  const c = loadContractV3(join(fixturesDir, 'valid-v3.contract.yaml'));
  assert.equal(c.contract.version, CONTRACT_V3_VERSION);
  assert.equal(c.contract.agent_id, 'sample-agent');
  assert.equal(c.identity.display_name, '样例');
  // defaults
  assert.equal(c.identity.user_invocable, true);
  assert.deepEqual(c.decision_rights.freeze, []);
  assert.deepEqual(c.decision_rights.forbidden, []);
  assert.deepEqual(c.collaborators.supervises, []);
  // union responsibilities preserved
  assert.equal(c.responsibilities[0], '职责一');
  assert.equal(c.responsibilities[1].priority, 'high');
  // runtime_baseline object shape preserved
  assert.equal(c.runtime_baseline.tri_mc_status, 'planned');
});

test('v1 contract rejected with unsupported version guidance', () => {
  assert.throws(
    () => loadContractV3(join(fixturesDir, 'unsupported-v1.contract.yaml')),
    (err) => {
      assert.ok(err instanceof ContractV3Error);
      assert.match(err.message, /unsupported contract version "1\.0"/);
      assert.match(err.message, /agent-contract-v3-spec\.md/);
      return true;
    },
  );
});

test('v2 contract rejected with unsupported version guidance', () => {
  assert.throws(
    () => loadContractV3(join(fixturesDir, 'unsupported-v2.contract.yaml')),
    (err) => {
      assert.ok(err instanceof ContractV3Error);
      assert.match(err.message, /unsupported contract version "2\.0"/);
      return true;
    },
  );
});

test('missing io_contract rejected with path context', () => {
  assert.throws(
    () => loadContractV3(join(fixturesDir, 'missing-io-contract.contract.yaml')),
    (err) => {
      assert.ok(err instanceof ContractV3Error);
      assert.match(err.message, /io_contract/);
      return true;
    },
  );
});

test('unknown top-level field rejected by strict()', () => {
  assert.throws(
    () => loadContractV3(join(fixturesDir, 'unknown-field.contract.yaml')),
    (err) => {
      assert.ok(err instanceof ContractV3Error);
      assert.match(err.message, /legacy_field/);
      return true;
    },
  );
});

test('invalid family enum rejected', () => {
  assert.throws(
    () => loadContractV3(join(fixturesDir, 'bad-family.contract.yaml')),
    (err) => {
      assert.ok(err instanceof ContractV3Error);
      assert.match(err.message, /family/);
      return true;
    },
  );
});

test('resolveContractsV3 collects per-file errors without throwing', () => {
  const { contracts, errors } = resolveContractsV3(fixturesDir);
  assert.equal(contracts.length, 1);
  assert.equal(contracts[0].contract.agent_id, 'sample-agent');
  assert.equal(errors.length, 5);
  const errorPaths = errors.map((e) => e.path).sort();
  assert.deepEqual(errorPaths, [
    'bad-family.contract.yaml',
    'missing-io-contract.contract.yaml',
    'unknown-field.contract.yaml',
    'unsupported-v1.contract.yaml',
    'unsupported-v2.contract.yaml',
  ]);
});

test('missing file raises ContractV3Error with path context', () => {
  assert.throws(
    () => loadContractV3(join(fixturesDir, 'no-such-file.contract.yaml')),
    (err) => {
      assert.ok(err instanceof ContractV3Error);
      assert.match(err.message, /no-such-file/);
      return true;
    },
  );
});
