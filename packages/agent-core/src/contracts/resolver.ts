// Contract Resolver — YAML contract loading and validation
//
// ⚠ 状态（2026-08-13，CTO 小狄 / O2-B）：本模块 schema 为早期设计残留，与当前两代真实合同均不匹配，
// 实测对 source-agents v2 合同（contract.version 2.0，TriLC 消费）与 docs/registry v1 合同
// （contract.version 1.0，TriMC 消费）解析全部失败（metadata: Required）。
// TriMC 与 TriLC 各自维护自己的 resolver（TriMC src/contracts/resolver.ts、TriLC src/config/contract-resolver.ts），
// 本类当前零生产消费方。O2-A（合同真源统一，M3 前置）完成前请勿使用本模块。
// 统一方向见 TriCompany/docs/engineering/trilc-trimc-runtime-parity.md §6.2。

import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { parse as parseYaml } from 'yaml';
import { AgentContractSchema, type AgentContract } from './agent-contract.js';

export interface ContractResolveResult {
  success: boolean;
  contract?: AgentContract;
  errors?: string[];
  path?: string;
}

/**
 * ⚠ 死形状警示（2026-08-13，CTO 小狄 / O2-B）：所依赖的 AgentContractSchema 与两代真实合同
 * 均不匹配，任何真实 .contract.yaml 都会解析失败（实测 metadata: Required）。O2-A 合同统一前勿用。
 *
 * @deprecated 零生产消费方，schema 与真实合同脱节；合同真源统一（O2-A，M3 前置）后按统一 schema 重建。
 */
export class ContractResolver {
  private contractCache: Map<string, AgentContract> = new Map();
  private basePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;
  }

  /**
   * Resolve a contract from a YAML file path (relative to basePath).
   */
  async resolve(filePath: string): Promise<ContractResolveResult> {
    const fullPath = resolve(this.basePath, filePath);

    // Check cache
    const cached = this.contractCache.get(fullPath);
    if (cached) {
      return { success: true, contract: cached, path: fullPath };
    }

    try {
      const content = await readFile(fullPath, 'utf-8');
      const parsed = parseYaml(content);
      const result = AgentContractSchema.safeParse(parsed);

      if (result.success) {
        this.contractCache.set(fullPath, result.data);
        return { success: true, contract: result.data, path: fullPath };
      }

      return {
        success: false,
        errors: result.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`),
        path: fullPath,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, errors: [message], path: fullPath };
    }
  }

  /**
   * Resolve multiple contracts from a directory (non-recursive, *.yaml / *.yml).
   */
  async resolveDirectory(dirPath: string): Promise<ContractResolveResult[]> {
    const fullPath = resolve(this.basePath, dirPath);
    const { readdir } = await import('node:fs/promises');

    try {
      const entries = await readdir(fullPath, { withFileTypes: true });
      const yamlFiles = entries
        .filter((e) => e.isFile() && (e.name.endsWith('.yaml') || e.name.endsWith('.yml')))
        .map((e) => e.name);

      const results = await Promise.all(
        yamlFiles.map((f) => this.resolve(`${dirPath}/${f}`)),
      );
      return results;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return [{ success: false, errors: [message], path: fullPath }];
    }
  }

  /**
   * Get a cached contract by its metadata name.
   */
  getByName(name: string): AgentContract | undefined {
    for (const contract of this.contractCache.values()) {
      if (contract.metadata.name === name) return contract;
    }
    return undefined;
  }

  /**
   * List all cached contracts.
   */
  list(): AgentContract[] {
    return [...this.contractCache.values()];
  }

  /**
   * Clear the cache.
   */
  clearCache(): void {
    this.contractCache.clear();
  }

  /**
   * Set the base path for contract resolution.
   */
  setBasePath(basePath: string): void {
    this.basePath = basePath;
  }
}
