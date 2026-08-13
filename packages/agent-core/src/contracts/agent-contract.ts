// AgentContract Schema v3.0 — 收敛权威 schema（r13-contract-convergence / r13-1）
//
// 唯一合同真源：TriCompany/source-agents/*.contract.yaml（v3.0）。
// 本 schema = v2 基础（contract+paths+decision_rights+runtime_baseline）
//           + TriMC 编排字段（identity+responsibilities+collaborators+tools+io_contract）。
// 兼容策略：无向后兼容分支——1.0/2.0 形状输入必须解析失败（负路径可测）。
// 规格全文与迁移序列见 docs/engineering/agent-contract-v3-spec.md。
import { z } from 'zod';

export const CONTRACT_V3_VERSION = '3.0' as const;
export const CONTRACT_V3_TYPE = 'agent-contract' as const;

export const IdentitySchema = z.object({
  display_name: z.string().min(1),
  role: z.string().min(1),
  description: z.string().min(1),
  user_invocable: z.boolean().default(true),
});

export const PathsSchema = z.object({
  soul: z.string().min(1),
  agent_body: z.string().min(1),
  agent_frontmatter: z.string().min(1),
  memory: z.string().min(1),
  colleagues: z.string().min(1),
  social: z.string().min(1),
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
      version: z.literal(CONTRACT_V3_VERSION),
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
    io_contract: IOContractSchema,
    instructions: z.string().optional(),
    runtime_baseline: RuntimeBaselineSchema.optional(),
  })
  .strict();

export type AgentContractV3 = z.infer<typeof AgentContractV3Schema>;
export type Identity = z.infer<typeof IdentitySchema>;
export type Paths = z.infer<typeof PathsSchema>;
export type Responsibility = z.infer<typeof ResponsibilitySchema>;
export type DecisionRights = z.infer<typeof DecisionRightsSchema>;
export type Collaborators = z.infer<typeof CollaboratorsSchema>;
export type ToolSpec = z.infer<typeof ToolSpecSchema>;
export type IOEntry = z.infer<typeof IOEntrySchema>;
export type IOContract = z.infer<typeof IOContractSchema>;
