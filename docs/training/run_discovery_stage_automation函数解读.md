这个函数在 ipd_case_engine.py 里，作用可以先概括成一句话：

它是 IPD case 在 Discovery 阶段的“自动执行入口”。给它一个 case_id，它会先检查这个 case 当前能不能跑 Discovery 自动化，然后自动生成 Discovery 阶段需要的参考来源 catalog 和几份核心文档，做一次覆盖校验，最后把这次自动化结果登记回 stage 状态；如果传了 submit=True，还会顺手把这次产出作为阶段提交结果收口。

**总体介绍**

从职责上看，run_discovery_stage_automation 不是“做市场研究本身”的函数，而是“编排一次 Discovery 自动化流程”的函数。它把几个底层动作串起来：

1. 读取 case，并确认这个 case 没被冻结。
2. 确认 Discovery 阶段当前允许自动执行。
3. 根据 case 槽位生成 Discovery 参考来源。
4. 把这些来源写成 catalog。
5. 基于这些来源生成 Discovery 阶段文档。
6. 校验竞品覆盖是否达标。
7. 汇总产出并更新阶段状态。

所以它更像一个 stage orchestration 函数，而不是某个具体文档的生成器。

**分步骤解释**

第一步，加载 case 并检查冻结状态。

函数一开始调用 _load_case(case_id, workspace_root)，把当前 case 的完整 payload 读出来。接着调用 _assert_case_not_frozen(case_payload, action="discovery automation")。

这里的意思很明确：如果这个 case 已经被冻结，就不允许再做 Discovery 自动化。也就是说，冻结机制是整个流程的硬门禁，这一步是防止在已封存或被阻断的 case 上继续写文件和改状态。

第二步，确认 Discovery 阶段是否可以自动执行。

接下来是：

- _ensure_stage_ready_for_automation(case_payload, "discovery", submit=submit)
- _stage_standard_flow(case_payload, stage)

第一句是在校验“这个 case 的 discovery 阶段现在是否处于可自动化状态”。比如阶段是否存在、是否轮到这个阶段、是否已经提交过、submit 模式下是否有额外约束，通常都在这里统一判断。

第二句是拿到这个阶段的标准交付流配置。你可以把 standard_flow 理解成“这个阶段文档应该写到哪里、catalog 应该写到哪里、summaryDocument 是哪一份、packageDocuments 是哪几份”的路径和结构描述。后面所有写文件动作都依赖它。

第三步，生成执行时间和 Discovery 来源集合。

- generated_at = _timestamp_now()
- sources = _build_discovery_sources(case_payload)

generated_at 很简单，就是给这次自动化打一个统一时间戳，后面写 catalog 和文档时会复用。

sources 是这段逻辑的核心输入。_build_discovery_sources(case_payload) 会根据当前 case 的槽位信息，构造出一批 Discovery 阶段参考来源。按注释语义看，这些来源不是人工抓取的真实外部资料，而是“基于当前 case 槽位和内置种子自动生成”的初始参考源集合。

也就是说，这一步产出的不是最终可信研究结果，而是一个“供后续人工复核和补充的 Discovery 起步包”。

第四步，写入 Discovery reference catalog。

这里先取出 catalog 路径：

- catalog_ref = str(standard_flow.get("catalogPath") or "").strip()

然后调用 _write_stage_reference_catalog(...) 写入一个 catalog 对象。这个对象里包含：

- schemaVersion
- kind: discovery-reference-source-catalog
- caseId
- stageKey: discovery
- captureMode: seeded-auto-generated
- generatedAt
- notes
- sources

这里最值得注意的是两个字段：

1. captureMode = seeded-auto-generated
这明确说明它不是人工调研版，而是“种子自动生成版”。

2. notes
里面直接写明：
- 该 catalog 是根据当前 case 槽位和内置种子自动生成的
- 后续需要人工复核，并补充真实抓取、离线快照或额外官方来源

这说明这个函数的定位非常克制：它负责把 Discovery 起步资料搭出来，但不假装自己已经完成了完整研究。

第五步，生成 Discovery 阶段文档。

接着调用 _write_discovery_documents(...)，传入：

- case_payload
- standard_flow
- sources
- written_at=generated_at
- workspace_root

从后面的 details 文案可以反推，这一步至少会刷新这些文档：

- 竞品 landscape
- 共性功能矩阵
- 亮点功能 memo
- functional brief

也就是说，catalog 是“来源登记层”，而这里写出的 document 则是“研究输出层”。函数返回的 document_refs 就是这些文档的路径引用。

第六步，校验 seeded competitor coverage。

这里调用了 _validate_discovery_seeded_competitor_coverage(...)，传入：

- case_payload
- catalog_ref
- summary_ref
- landscape_ref
- workspace_root

这一步很关键，因为它说明系统不仅生成文档，还会检查自动生成的竞品覆盖是否足够合理。

其中：

- summary_ref 来自 standard_flow.summaryDocument.path
- landscape_ref 来自 standard_flow.packageDocuments[0].path

也就是说，校验逻辑会参考 catalog、本阶段 summary 文档，以及竞品 landscape 文档，去判断这次 seeded automation 有没有满足最低覆盖要求。

如果你从工程角度理解，这一步是 Discovery 自动化的质量门槛，避免函数只是“机械写文件”，却产出一堆覆盖不完整的空壳内容。

第七步，汇总本次自动化产物引用。

- generated_refs = [catalog_ref, *document_refs]

这里把 catalog 和文档统一汇总成一个列表，作为本次自动化生成的成果引用。后面 finalize 的时候可以直接登记这些路径。

第八步，生成对外可读的执行说明。

details 被写成两条中文说明：

- 已自动登记 N 个 Discovery 对标来源。
- 已自动刷新 Discovery 的竞品 landscape、共性功能矩阵、亮点功能 memo 与 functional brief。

这两条是给阶段日志、提交记录或 UI 展示用的摘要，不是核心业务逻辑，但很重要，因为它让这次自动化结果对人可读。

第九步，统一收口并返回结果。

最后调用 _finalize_stage_automation(...)，传入：

- case_payload
- stage
- generated_refs
- details
- object_path=summaryDocument.path
- submit
- workspace_root

这一步通常就是“把这次自动化真正记到账上”。它大概率会做这些事中的一部分：

- 更新 stage 元数据
- 写入自动化执行记录
- 记录生成文件引用
- 如果 submit=True，则把这次结果直接作为阶段输出提交

其中 object_path 选的是 summaryDocument.path，说明这份 summary 文档被当成这次 Discovery 自动化最主要的代表性产物。

**你可以把这个函数理解成什么**

如果用更直白的话说，这个函数做的是：

“拿一个 case，自动给它补一套 Discovery 初稿资产，然后把这次自动化动作正式登记下来。”

它不负责最终拍板，也不负责人工深度分析；它负责把 Discovery 阶段从“空白”推进到“有基础资料、有初稿文档、有覆盖校验、有阶段记录”的状态。

**回顾总结**

总体上，run_discovery_stage_automation 是一个很典型的“阶段编排函数”：

- 前半段做门禁检查：读 case、查冻结、查阶段状态。
- 中段做核心产出：生成 sources、写 catalog、写 Discovery 文档。
- 后半段做质量与收口：覆盖校验、汇总引用、登记阶段结果。

它的设计重点不是复杂算法，而是流程完整性。也就是说，这个函数真正重要的地方在于：

1. 它把 Discovery 自动化流程串成了一个稳定入口。
2. 它明确区分“自动生成的种子资料”和“人工复核后的真实资料”。
3. 它在生成之后立刻做覆盖校验，而不是只管写文件不管质量。
4. 它最终把结果归档到阶段状态里，方便后续 Intelligence 等阶段继续接。

如果你愿意，我下一步可以继续给你讲这几个辅助函数在这条链路里的角色差异，比如：
1. _build_discovery_sources 负责生成什么样的 sources
2. _write_discovery_documents 具体会写哪些文档
3. _finalize_stage_automation 和 submit=True 的行为差别是什么