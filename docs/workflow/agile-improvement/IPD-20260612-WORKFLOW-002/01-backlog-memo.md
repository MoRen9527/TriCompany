# IPD-20260612-WORKFLOW-002 Backlog Memo

## Background

- Intake has been issued as `IPD-20260612-WORKFLOW-002-INTAKE-V001`.
- `IPD-20260611-PLATFORM-001` has completed the full `ceo-demand -> delivery` proving-ground replay and now serves as the evidence baseline for long-term contract candidates.
- `IPD-20260610-PLATFORM-001` is the current full-scope `project-delivery` case for Gate A / Gate B / Gate C consumption and replay.
- This workflow case exists to optimize the IPD mechanism itself and then feed each fix back into the proving-ground replay.
- The end goal is full-stage IPD optimization, not a permanent stop at `Discovery / Intelligence`.

## Current Decision

- Use this case to harden the repeating loop: `workflow sprint -> source-side self-test -> slice validation -> PLATFORM-001 live replay -> continue / freeze / rollback`.
- Use `IPD-20260610-PLATFORM-001` as the current full-scope replay / product-mainline target instead of opening temporary delivery cases; keep `IPD-20260611-PLATFORM-001` as the completed proving-ground baseline.
- Optimize all IPD stages through capability gates; the current sprint only stabilizes Gate A and writes the full-stage map for later gates.

## Priority Backlog

### P0

1. Freeze the Gate A replay contract: `ceo-demand -> task-dispatch -> discovery -> intelligence -> package/signoff`.
2. Define the rollback matrix for `ceo-demand`, `task-dispatch`, and `discovery`, and state when later-stage local replay is allowed.
3. Create a source-side validation matrix for every change before it is replayed or consumed on `IPD-20260610-PLATFORM-001`.
4. Harden the Discovery competitor carry-forward contract: competitor slots seeded by CEO are not an exclusive ceiling, but every seeded competitor must appear in later Discovery references unless explicitly waived with reason.

### P1

1. Prepare the `sprint-planning` package with sprint goal, task order, owners, and verification checkpoints for Gate A.
2. Write the full-stage capability map for Gate B (`designing -> coding -> verify-integration`) and Gate C (`redteam -> qa -> deployment -> assurance -> delivery`).
3. Keep operating record, workflow source, and training guidance aligned with the proving-ground loop.
4. Route process-code modifications for Discovery rigor to CTO by default; CEOChiefOfStaff defines contract and acceptance, but does not keep patching runtime behavior in place of CTO.

### P2

1. Expand regression coverage and operator ergonomics for later-phase submit, signoff, freeze, and rollback behavior.
2. Prepare the handoff contract for turning a validated phase gate into the next replay slice on the fixed proving-ground case.

## In Scope For This Case

- Hardening the IPD optimization mechanism itself.
- Gate-based replay design for all IPD stages.
- Source runtime, CLI, docs, tests, and live case consistency for the process-improvement line.
- Repeated feedback flow from `IPD-20260610-PLATFORM-001` replay / product-mainline consumption back into workflow sprints, while preserving `IPD-20260611-PLATFORM-001` as the completed evidence baseline.

## Out Of Scope For This Case

- Building the platform product itself inside this workflow case.
- Claiming that `designing -> delivery` has already passed live validation.
- Formal host switch, TriMC production hosting, or production-grade launch completion.

## Entry Criteria For Sprint Planning

- Gate A priorities are fixed.
- `IPD-20260610-PLATFORM-001` keeps its current Discovery baseline / replay surface ready for controlled validation.
- Rollback anchors and self-test requirements are explicit.
- Discovery competitor carry-forward rule is explicit: seeded competitors can be expanded, but cannot silently disappear from downstream references.
- The next package can translate the backlog into sprint goal, tasks, sequence, and verification checkpoints.

## Risks

- If Gate A / B / C validation drifts away from `IPD-20260610-PLATFORM-001`, replay evidence will fragment again.
- If the team keeps talking only about `Discovery / Intelligence`, the full-stage optimization goal will drift.
- If source-side self-test is skipped, live replay failures will mix implementation defects with case-state noise.
- If Discovery automation treats `competitorReference` as optional decoration instead of a carry-forward contract, seeded competitors like LiteLLM / sub2api can disappear even when later references are expanded correctly.
- If CEOChiefOfStaff keeps patching workflow behavior directly, CTO ownership over process-code rigor will stay blurred.
