# Employee Source Kit CLI 实验手册

版本：V0.1
日期：2026-06-10
状态：配套正式课程稿的动手实验版

## 1. 实验定位

本手册配套：

- `docs/training/LearningToPractice/CLI/employee-source-kit-cli-course.md`

正式课程稿负责讲清楚结果、原理、分层和完整工作流。

本手册负责把这些内容转成一条可重复执行的动手路径，让研发新人不仅“看懂”，还能亲手跑通、亲手制造问题、亲手解释问题。

## 2. 实验目标

完成本手册后，你应该能独立说清并演示：

1. `employee_source_kit` 的 CLI 入口是怎么工作的。
2. `argparse` 如何把命令行输入变成结构化参数。
3. `validate` 和 `generate` 分别负责什么。
4. 为什么 source kit 必须和 support payload、runtime state 分层。
5. 一个 CLI 是怎么和 agent/source kit/binding/workspace 一起构成工作流的。

## 3. 实验前准备

### 3.1 环境准备

在 `TriCompany` 仓库根目录执行以下命令确认环境：

```powershell
Get-Location
python --version
```

建议当前目录为：

```text
D:\OneDrive\Code\ai\TriCompany
```

### 3.2 本次会用到的源码入口

本实验主要围绕以下文件展开：

1. `runtime/cognition/employee_source_kit.py`
2. `runtime/cognition/knowledge_workspace.py`
3. `runtime/cognition/employee_host_publish.py`
4. `runtime/cognition/host_object_generation.py`
5. `runtime/cognition/employee_source_kit_validation.py`

### 3.3 实验纪律

1. 先跑最小无副作用路径。
2. 再在临时目录里做生成实验，不直接污染主仓库。
3. 故障注入只在临时目录里做。
4. 每一步都记录“输入 -> 处理 -> 输出 -> 验证”。

## 4. 实验总览

本手册按“由浅入深”的顺序分成 6 个实验：

1. 认识命令面
2. 跑最小 MVP：`validate`
3. 沿 `main` 追调用链
4. 在临时目录执行 `generate`
5. 人为制造边界错误并用 `validate` 抓出来
6. 把 source kit 放回完整工作流链路

## 5. 实验 1：先认识命令面

### 5.1 目标

先不看细节实现，只观察这个 CLI 对外暴露了什么命令协议。

### 5.2 执行命令

```powershell
python -m runtime.cognition.employee_source_kit --help
python -m runtime.cognition.employee_source_kit generate --help
python -m runtime.cognition.employee_source_kit validate --help
```

### 5.3 你要观察什么

1. 顶层只有哪两个子命令。
2. 哪些参数是 `generate` 独有的。
3. 哪些参数是 `validate` 独有的。
4. 哪些参数是必填，哪些是可选。

### 5.4 练习题

1. 为什么 `validate` 的参数面比 `generate` 更小？
2. 如果你是新同学，只看 `--help`，你能推断出这个 CLI 大致解决什么问题吗？
3. 为什么 `--responsibility`、`--input-source`、`--voice-trait` 适合设计成可重复传入的参数？

## 6. 实验 2：跑最小 MVP 路径

### 6.1 目标

先跑一条没有写入副作用、但完整闭环的路径：`validate rd-trainer`。

### 6.2 执行命令

```powershell
python -m runtime.cognition.employee_source_kit validate --source-root . --employee-id rd-trainer
```

### 6.3 预期输出

```text
validated_employee_source_kit=rd-trainer
```

### 6.4 这一步实际完成了什么

1. Python 进入模块入口。
2. `argparse` 解析 `validate` 子命令。
3. 程序根据 `employee_id` 计算五件套路径。
4. 程序逐个读取文件并做边界校验。
5. 校验通过后输出结果并返回退出码 `0`。

### 6.5 实验记录模板

请用 4 行总结这条最小闭环：

1. 输入：
2. 处理：
3. 输出：
4. 验证：

### 6.6 练习题

1. 为什么这里把 `validate` 作为 MVP，而不是 `generate`？
2. 这一步为什么能体现完整 CLI 闭环，而不只是一次文件读取？
3. 退出码对 shell、task runner 和 CI 有什么价值？

## 7. 实验 3：沿着 `main` 追调用链

### 7.1 目标

把“能跑”升级成“知道为什么这样跑”。

### 7.2 推荐打开的函数

请依次打开并阅读：

1. `if __name__ == "__main__":`
2. `main()`
3. `validate_employee_source_kit(...)`
4. `source_kit_paths(...)`
5. `normalize_workspace_id(...)`

### 7.3 你要写下来的调用链

请手写或口述一条最小调用链：

```text
__main__ -> main -> parse_args -> validate_employee_source_kit -> source_kit_paths -> normalize_workspace_id
```

### 7.4 你要回答的问题

1. `main()` 为什么只做参数层和分发层，不直接实现全部业务？
2. `validate_employee_source_kit(...)` 为什么返回结果对象，而不是只打印文本？
3. `normalize_workspace_id(...)` 在安全性和一致性上分别解决了什么问题？

### 7.5 小练习

请把这几个函数按职责归类：

1. 入口层
2. 参数层
3. 业务层
4. 路径层
5. 校验层

## 8. 实验 4：在临时目录执行 `generate`

### 8.1 目标

亲手生成一套新的 source kit，但不污染当前仓库。

### 8.2 准备临时目录

```powershell
$LabRoot = Join-Path $env:TEMP "employee-source-kit-lab"
Remove-Item $LabRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $LabRoot "TriCompany") -Force | Out-Null
```

### 8.3 执行生成命令

```powershell
python -m runtime.cognition.employee_source_kit generate `
  --source-root (Join-Path $LabRoot "TriCompany") `
  --employee-id customer-success-officer `
  --agent-name CustomerSuccessOfficer `
  --role-title "客户成功负责人" `
  --description "适用场景：客户成功、试点跟进、用户反馈收集、续费风险识别。" `
  --role-scope "你负责把试点客户反馈整理成可复核的产品、交付和运营输入。" `
  --display-name "小成" `
  --responsibility "跟进试点客户反馈并区分产品问题、交付问题和使用教育问题。" `
  --responsibility "把稳定客户事实回写到对应产品、运营或 registry 真源。" `
  --input-source "CEO / 当前操作者的客户反馈。" `
  --input-source "CPO、CTO 和 CEOChiefOfStaff 的交接说明。" `
  --voice-trait "耐心、具体、尊重客户原话。" `
  --voice-trait "先区分事实、判断和待确认问题。"
```

### 8.4 预期输出

你会看到类似：

```text
agent=...
soul=...
memory=...
colleagues=...
social=...
validated_employee_source_kit=customer-success-officer
```

### 8.5 检查生成结果

```powershell
Get-ChildItem -Recurse (Join-Path $LabRoot "TriCompany")
```

### 8.6 你要观察什么

1. 五件套具体落到了哪里。
2. 文件名为什么统一使用规范化后的 `employee_id`。
3. 哪些内容属于稳定源定义。
4. 哪些当前宿主绑定事实没有被写进源文件。

### 8.7 练习题

1. 为什么 `generate` 完成后还要再自动执行一次 `validate`？
2. 为什么 `display_name` 可以是中文，但 `employee_id` 要规范成统一的英文/短横线格式？
3. 如果这里直接把 support payload 路径写进源文件，会破坏什么边界？

## 9. 实验 5：故障注入，让 validator 抓出边界错误

### 9.1 目标

不要只看成功路径，还要亲手制造一个越界错误，理解 validator 的价值。

### 9.2 在临时目录里注入错误

```powershell
$MemoryFile = Join-Path $LabRoot "TriCompany/.github/source-agents/customer-success-officer/customer-success-officer.memory.md"
Add-Content -Path $MemoryFile -Value "`n## 阶段记忆记录`n"
```

### 9.3 再次执行校验

```powershell
python -m runtime.cognition.employee_source_kit validate `
  --source-root (Join-Path $LabRoot "TriCompany") `
  --employee-id customer-success-officer
```

### 9.4 预期现象

你应该看到 `validation_error=... contains consumption marker ...` 之类的错误输出，并得到非 `0` 退出码。

### 9.5 这一步在教学上的意义

它能让新人明白：

1. validator 不是装饰层。
2. source kit 的目标是守住 source/runtime 边界。
3. 合格 CLI 必须同时证明成功路径和失败路径都可解释。

### 9.6 练习题

1. 为什么 `## 阶段记忆记录` 会被认定为越界？
2. 如果把 `TriCompany-copilot-host-assets/knowledge/employees/...` 写进源侧文件，为什么也算错误？
3. 从工程治理上看，“禁止标记”与“必须标记”分别解决了什么问题？

## 10. 实验 6：把 source kit 放回完整工作流

### 10.1 目标

理解 source kit 只是上游输入，而不是完整发布终点。

### 10.2 观察下游 CLI

请执行：

```powershell
python -m runtime.cognition.employee_host_publish --help
python -m runtime.cognition.employee_host_binding_profile_generation --help
python -m runtime.cognition.employee_host_object_generation --help
```

### 10.3 你要画出的工作流

请自己写出下面这条链：

```text
employee_source_kit
  -> source-agents/<employee-id>/*.md
  -> host_object_generation
  -> binding-profiles/<employee-id>.json
  -> support payload under TriCompany-copilot-host-assets
  -> live agent discovery under TriMetaverse/.github/agents
```

### 10.4 你要解释的问题

1. 为什么 source kit 不是最终发布器？
2. binding profile 在这条链里承担什么角色？
3. support payload 为什么不能直接等同于 source truth？
4. live agent 为什么只是一层 discovery 入口，而不是全部真源？

## 11. 生产级复盘清单

完成上面实验后，请用下面的清单复盘这套 CLI 是否具备工程质量。

### 11.1 入口质量

- 是否有清晰的 `main()` 入口？
- 是否有明确退出码？
- 是否支持 `--help` 自解释？

### 11.2 输入质量

- 是否做了 `employee_id` 规范化？
- 是否明确哪些参数必填、哪些参数可选？
- 是否能拒绝非法标识符？

### 11.3 副作用治理

- 默认是否防止覆盖已有文件？
- 是否能显式允许覆盖？
- 是否把实验副作用限制在临时目录内？

### 11.4 边界治理

- source 与 runtime 是否分层？
- 是否禁止把运行态消费数据写回源侧？
- 是否通过 required marker 保证最小契约完整？

### 11.5 验证与回归

- 是否有单元测试？
- 是否有成功路径和失败路径验证？
- 是否有工作流层面的 publish 验证？

## 12. 最终提交物

完成实验后，建议新人至少提交以下 5 项内容：

1. 一段 150-300 字的总结：`employee_source_kit` 到底解决了什么问题。
2. 一条最小调用链：从 `__main__` 到 `validate_employee_source_kit(...)`。
3. 一条完整工作流链：从 source kit 到 live agent discovery。
4. 一条故障注入记录：你制造了什么错误，validator 怎么识别它。
5. 一份生产级复盘：列出 3 个你认为最关键的工程设计点。

## 13. 助教判定标准

如果学习者能做到以下几点，就说明这次实验基本过关：

1. 不只会抄命令，还能解释每一步在系统里做了什么。
2. 不只会说“这是个 CLI”，还能说清它和 agent/workflow 的关系。
3. 不只会说“有校验”，还能解释为什么要校验 source/runtime 边界。
4. 不只会看成功路径，还能主动构造失败路径并解释错误原因。
5. 能把这次拆解方法迁移到别的 CLI、别的模块或别的工作流。

## 14. RAndDTrainer 复用说明

今后再讲任何研发技术课程，只要主题里有：

1. 命令入口
2. 多层调用链
3. 副作用落盘
4. 工作流协作
5. 生产级边界

都可以直接复用本手册的实验组织方式：

1. 先看命令面。
2. 再跑最小 MVP。
3. 再追调用链。
4. 再做临时生成。
5. 再做故障注入。
6. 最后放回完整工作流和生产级复盘。

这样一来，研发新人面对新的 CLI 或新的 workflow，不会再次从零摸索。
