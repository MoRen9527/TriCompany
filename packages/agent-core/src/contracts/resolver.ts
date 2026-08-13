// Contract Resolver v3.0 — 收敛权威解析入口（r13-contract-convergence / r13-1）
//
// 双域共用：TriLC / TriMC 的合同解析与校验统一走本模块（thin adapter 边界见
// docs/engineering/agent-contract-v3-spec.md §四）。只接受 v3.0 合同；
// 1.0/2.0 形状输入明确失败并指向迁移指引。
//
// 解析错误格式：`[ContractV3] <agentIdOrPath>: <message>`。

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { parse as parseYaml } from 'yaml';
import {
  AgentContractV3Schema,
  CONTRACT_V3_VERSION,
  type AgentContractV3,
} from './agent-contract.js';

export class ContractV3Error extends Error {
  constructor(
    message: string,
    public context: string
  ) {
    super(`[ContractV3] ${context}: ${message}`);
    this.name = 'ContractV3Error';
  }
}

function describeUnsupportedVersion(raw: unknown): string | undefined {
  if (typeof raw !== 'object' || raw === null) return undefined;
  const contract = (raw as { contract?: { version?: unknown } }).contract;
  const version = typeof contract === 'object' && contract !== null
    ? contract.version
    : undefined;
  return typeof version === 'string' ? version : undefined;
}

function mapIssues(
  issues: { path: (string | number)[]; message: string }[],
  context: string
): string[] {
  return issues.map((i) => `${i.path.join('.') || '(root)'}: ${i.message}（agent: ${context}）`);
}

/**
 * Load and validate a single .contract.yaml file into AgentContractV3.
 * Throws ContractV3Error on any parse/validation failure.
 */
export function loadContractV3(contractPath: string): AgentContractV3 {
  const fullPath = resolve(contractPath);

  let raw: unknown;
  try {
    const content = readFileSync(fullPath, 'utf-8');
    raw = parseYaml(content);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    throw new ContractV3Error(`failed to read or parse YAML: ${message}`, fullPath);
  }

  const unsupported = describeUnsupportedVersion(raw);
  if (unsupported !== undefined && unsupported !== CONTRACT_V3_VERSION) {
    throw new ContractV3Error(
      `unsupported contract version "${unsupported}", expected "${CONTRACT_V3_VERSION}" — ` +
      '迁移指引见 TriCompany/docs/engineering/agent-contract-v3-spec.md §三',
      fullPath,
    );
  }

  const result = AgentContractV3Schema.safeParse(raw);
  if (!result.success) {
    throw new ContractV3Error(
      `schema validation failed: ${result.error.issues.map((i) => `${i.path.join('.') || '(root)'}: ${i.message}`).join('; ')}`,
      fullPath,
    );
  }
  return result.data;
}

/**
 * Resolve all *.contract.yaml from a directory (non-recursive).
 * Failed parses are collected into errors — does not throw on individual failures.
 */
export function resolveContractsV3(
  dirPath: string
): { contracts: AgentContractV3[]; errors: { path: string; message: string }[] } {
  const contracts: AgentContractV3[] = [];
  const errors: { path: string; message: string }[] = [];
  const fullDir = resolve(dirPath);

  let entries: string[];
  try {
    entries = existsSync(fullDir) ? readdirSync(fullDir) : [];
  } catch {
    return { contracts, errors: [{ path: dirPath, message: 'directory not readable' }] };
  }

  for (const entry of entries) {
    if (!entry.endsWith('.contract.yaml')) continue;
    const fullPath = join(fullDir, entry);
    try {
      contracts.push(loadContractV3(fullPath));
    } catch (err: unknown) {
      errors.push({
        path: entry,
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }

  return { contracts, errors };
}
