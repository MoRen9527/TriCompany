// AgentContract Schema v3.0 — 收敛权威 schema（r13-contract-convergence / r13-1）
//
// 唯一合同真源：TriCompany/source-agents/*.contract.yaml（v3.0）。
// 本 schema = v2 基础（contract+paths+decision_rights+runtime_baseline）
//           + TriMC 编排字段（identity+responsibilities+collaborators+tools+io_contract）。
// 兼容策略：无向后兼容分支——1.0/2.0 形状输入必须解析失败（负路径可测）。
// 规格全文与迁移序列见 docs/engineering/agent-contract-v3-spec.md。
import { z } from 'zod';

export const CONTRACT_V3_VERSION = '3.0' as const;
// LG-025 后续件①（CTO 小令 2026-09-04）：ceo 合同 v3.1 门放行——accept 面 3.0+3.1
// （v3.1=ceo 席 paths/session_body 键扩展，v3.0 形态超集；LG-026 在册漂移信号本体消解）。
export const CONTRACT_V3_SUPPORTED_VERSIONS = ['3.0', '3.1'] as const;
export const CONTRACT_V3_TYPE = 'agent-contract' as const;

export const IdentitySchema = z.object({
  display_name: z.string().min(1),
  role: z.string().min(1),
  description: z.string().min(1),
  user_invocable: z.boolean().default(true),
});

// batch-15 件③（CTO 终裁 2026-10-02）：Registry family=非人格席，无
// soul/memory/colleagues/social 四件套路径映射（设计声明，board 合同头「无四件套」；
// CEO 09-27 审认在役）——四件套 optional 化，简形=agent_body/agent_frontmatter。
// Role 形四件套强约束由主 schema superRefine 按 family 分支维持（防 v1 负路径回归）。
export const PathsSchema = z.object({
  soul: z.string().min(1).optional(),
  agent_body: z.string().min(1),
  agent_frontmatter: z.string().min(1),
  memory: z.string().min(1).optional(),
  colleagues: z.string().min(1).optional(),
  social: z.string().min(1).optional(),
});

export const ResponsibilitySchema = z.union([
  z.string(),
  z.object({
    description: z.string(),
    priority: z.enum(['high', 'medium', 'low']).optional(),
  }),
]);

export const DecisionRightsSchema = z.object({
  approve: z.array(z.string()).default([]),
  freeze: z.array(z.string()).default([]),
  escalate: z.array(z.string()).default([]),
  forbidden: z.array(z.string()).default([]),
});

export const CollaboratorsSchema = z.object({
  reports_to: z.string().min(1),
  peers: z.array(z.string()).default([]),
  supervises: z.array(z.string()).default([]),
});

export const ToolSpecSchema = z.object({
  name: z.string().min(1),
  scope: z.array(z.string()).default([]),
  risk_level: z.enum(['low', 'medium', 'high', 'critical']),
  requires_approval: z.boolean().default(false),
  runtime_equivalent: z.string().default(''),
});

export const IOEntrySchema = z.object({
  type: z.string().min(1),
  description: z.string().min(1),
  source: z.string().optional(),
});

export const IOContractSchema = z.object({
  inputs: z.array(IOEntrySchema).min(1),
  outputs: z.array(IOEntrySchema).min(1),
});

export const RuntimeBaselineSchema = z.record(z.unknown());

export const AgentContractV3Schema = z
  .object({
    contract: z.object({
      version: z.union([z.literal('3.0'), z.literal('3.1')]),
      type: z.literal(CONTRACT_V3_TYPE),
      agent_id: z.string().min(1),
      family: z.enum(['Role', 'Registry']),
    }),
    identity: IdentitySchema,
    paths: PathsSchema,
    responsibilities: z.array(ResponsibilitySchema).min(1),
    decision_rights: DecisionRightsSchema,
    collaborators: CollaboratorsSchema,
    tools: z.array(ToolSpecSchema).default([]),
    // batch-15 件③追裁细则①②（CTO 2026-10-02）：io_contract Registry family 可缺——
    // .nullish() 非 .optional()：yaml 空段（`io_contract:` 段头无内容）解析为 null，
    // 纯 optional 二次翻车；Role 形 Required 强约束由主 schema superRefine 维持。
    io_contract: IOContractSchema.nullish(),
    // batch-15 件③追裁细则③（CTO 2026-10-02）：interfaces 为 board 特有节
    //（非人格治理面，合同 L53 自证），optional 宽松节放行——不选 passthrough：
    // passthrough 放行全部未知键=strict 全废，显式单键放行=最小约束面。
    // 不进 domain shape（resolver 不映射，无消费面零外溢）。
    interfaces: z.record(z.unknown()).optional(),
    instructions: z.string().optional(),
    runtime_baseline: RuntimeBaselineSchema.optional(),
  })
  .strict()
  .superRefine((val, ctx) => {
    // Registry family 分支（batch-15 件③·CTO 终裁 2026-10-02）：Role 形四件套强约束
    // 在此维持——PathsSchema optional 化仅为 Registry 简形放行，Role 合同回归面不松。
    if (val.contract.family === 'Role') {
      for (const k of ['soul', 'memory', 'colleagues', 'social'] as const) {
        const v = val.paths[k];
        if (typeof v !== 'string' || v.length < 1) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ['paths', k],
            message: `paths.${k} is Required for Role-family contracts`,
          });
        }
      }
      // 追裁细则②（batch-15 件③·CTO 2026-10-02）：Role 形 io_contract Required——
      // 键缺失（undefined）与 yaml 空段（null）两种形都打回；inputs/outputs min1
      // 由 IOContractSchema 自身维持，此处只把关非缺非 null。员工席强约束不松动。
      if (val.io_contract === undefined || val.io_contract === null) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['io_contract'],
          message: 'io_contract is Required for Role-family contracts',
        });
      }
    }
  });

export type AgentContractV3 = z.infer<typeof AgentContractV3Schema>;
export type Identity = z.infer<typeof IdentitySchema>;
export type Paths = z.infer<typeof PathsSchema>;
export type Responsibility = z.infer<typeof ResponsibilitySchema>;
export type DecisionRights = z.infer<typeof DecisionRightsSchema>;
export type Collaborators = z.infer<typeof CollaboratorsSchema>;
export type ToolSpec = z.infer<typeof ToolSpecSchema>;
export type IOEntry = z.infer<typeof IOEntrySchema>;
export type IOContract = z.infer<typeof IOContractSchema>;
