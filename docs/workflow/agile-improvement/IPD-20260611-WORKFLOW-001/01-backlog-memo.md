# IPD-20260611-WORKFLOW-001 Backlog Memo

## Background

- Intake has been migrated to the agile-improvement execution line and formally issued as `IPD-20260611-WORKFLOW-001-INTAKE-V001`.
- This case only improves the company IPD process itself.
- Real project Discovery, Intelligence, PRD, and delivery validation must be opened in separate `project-delivery` cases.

## Current Decision

- Use this case to harden the process-improvement route from `ceo-demand` to `validation-handoff`.
- Keep the signing chain as `owner -> CEO -> CEOChiefOfStaff` for stage outputs.
- Keep rollback support at least at `ceo-demand` and `task-dispatch`.
- Keep live support-root case data aligned with the source runtime and tests.

## Priority Backlog

### P0

1. Freeze the agile stage contracts for `backlog`, `sprint-planning`, `sprint-execution`, `sprint-review`, `retrospective`, and `validation-handoff`.
2. Ensure stage submission, signoff, release issuance, and rollback all work on the agile-improvement line with live case data.
3. Keep the boundary explicit that this WORKFLOW case does not act as a real delivery case.

### P1

1. Prepare the `sprint-planning` package so the next stage can directly define sprint goal, task order, owners, and verification path.
2. Align training and operator guidance with the new split: process-improvement uses agile-improvement, product work uses project-delivery IPD.
3. Harden the bridge contract for later opening a separate model API relay platform `project-delivery` case.

### P2

1. Expand regression coverage around duplicate-role signoff chains, agile artifact numbering, and live support-root reconciliation.
2. Improve operator ergonomics for stage submission and approval commands on the agile line.

## In Scope For This Case

- Process-improvement workflow hardening.
- Agile stage package generation and signoff flow.
- Runtime, CLI, docs, tests, and live support-root consistency for the workflow line.
- A clean handoff contract into future project-delivery cases.

## Out Of Scope For This Case

- Building the model API relay platform itself.
- Using this case to perform real Discovery, Intelligence, PRD, coding, or delivery validation for a product.
- Formal host switch, TriMC production hosting, or broader authorization-matrix completion.

## Entry Criteria For Sprint Planning

- Backlog priorities are fixed.
- Guardrails and out-of-scope are explicit.
- Required owners and support roles are named.
- The next package must translate the backlog into sprint goal, tasks, sequence, and verification checkpoints.

## Risks

- If process-improvement and project-delivery scopes are mixed again, later stages will drift back into pseudo-delivery work.
- If live support data and source runtime diverge, signoff and rollback behavior will become misleading.
- If the next sprint plan does not include explicit verification checkpoints, later release issuance will be weak.