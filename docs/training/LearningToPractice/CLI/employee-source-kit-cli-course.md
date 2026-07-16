# Employee Source Kit CLI 从入口到工作流正式课程

版本：V0.1
日期：2026-06-10
状态：按 RAndDTrainer 统一讲法整理的正式课程稿
lastSyncedCommit: 0329974e7e3593548294ee3021d06ab887d9ee1a

## 1. 这门课先讲大的结果

这门课不是单独讲一个 Python 文件怎么跑起来，而是讲清楚：

1. 一个 CLI 如何把用户输入转成结构化动作。
2. 一个 CLI 如何调用本地业务函数，而不是把全部逻辑塞进入口里。
3. 一个 CLI 如何和 source kit、binding profile、support payload、live agent 一起组成工作流闭环。
4. 一个可维护的 CLI 为什么必须有命令协议、边界协议、验证协议和测试入口。

学完这门课后，研发新人应该能看懂三件事：

1. `employee_source_kit` 自己是怎么工作的。
2. 它为什么不是孤立脚本，而是 TriCompany 岗位发布链的一环。
3. 今后再看别的 CLI，也能用同一套方法拆解。

如果要配合动手练习，请同时使用：

- `docs/training/LearningToPractice/CLI/employee-source-kit-cli-lab-manual.md`

## 2. 这门课对应的真实效果

当前这套 CLI 已经实现了一个最小但完整的研发工作流切片：

1. 允许用命令生成员工源侧五件套。
2. 允许对现有五件套做边界校验。
3. 让源侧岗位定义和运行态消费数据保持分层。
4. 为后续 `binding profile`、`support payload` 和 `live agent` 发布提供稳定输入。

换句话说，它实现的不是“帮你写几个 markdown 文件”，而是“把岗位源定义变成可验证、可发布、可接入宿主资产链的标准对象”。

## 3. 这套实现背后的理论方法和协议

在进入代码之前，先记住它依赖的几条稳定方法。

### 3.1 命令分发

一个 CLI 不应该把所有逻辑都写在入口里。入口只负责：

1. 定义命令协议。
2. 解析参数。
3. 路由到正确业务函数。
4. 返回退出码。

### 3.2 数据建模

用户输入、生成结果、校验问题、校验汇总都要有清晰的数据结构，而不是全靠字典和临时变量到处传。

这份实现用 `dataclass` 把输入和输出模型稳定下来。

### 3.3 Source 与 Runtime 分层

源侧文件负责声明稳定规则、岗位定义和边界。

运行态空间负责承载实际消费数据、当前宿主路径和运行时私域状态。

这也是为什么 source kit validator 会严格禁止把 support 路径和运行态消费记录写回源侧五件套。

### 3.4 契约校验

这类 CLI 不是只要生成成功就算成功。它还要证明：

1. 文件是否齐全。
2. 内容是否含有必须标记。
3. 内容是否误混入被禁止的运行态信息。

### 3.5 发布链协议

`employee_source_kit` 不是最终发布器，它是发布链的上游输入。

它后面还接着：

1. `employee_host_publish`
2. `host_object_generation`
3. `binding profile`
4. `TriMetaverse/.github` live agent 入口

所以理解它时，必须始终把它放在完整链路里看。

## 4. 先跑一个最小 MVP 全流程

研发新人第一次学，不先跑 `generate`，而先跑一个无副作用、最容易看懂的最小闭环：校验现有的 `rd-trainer` source kit。

在 `TriCompany` 根目录执行：

```powershell
python -m runtime.cognition.employee_source_kit validate --source-root . --employee-id rd-trainer
```

如果通过，你会看到：

```text
validated_employee_source_kit=rd-trainer
```

这条最小路径已经包含一条完整的 CLI 闭环：

1. 操作者输入命令。
2. Python 进入模块主入口。
3. `argparse` 解析 `validate` 子命令和参数。
4. 代码调用 `validate_employee_source_kit(...)`。
5. 程序根据 `employee_id` 计算五件套路径。
6. 程序逐个读取文件并检查边界标记。
7. 如果通过，输出成功标记并返回退出码 `0`。

这就是本课的 MVP。

## 5. MVP 背后的原理

### 5.1 入口为什么这样写

主入口采用：

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

它表达三件事：

1. 只有当文件被直接执行时，才进入 CLI 模式。
2. 真正的入口逻辑统一收敛到 `main()`。
3. `main()` 返回的整数会变成进程退出码，`0` 表示成功，非 `0` 表示失败。

### 5.2 `main()` 在 MVP 里做了什么

`main()` 在 MVP 里只做参数层工作：

1. 创建 `ArgumentParser`。
2. 注册 `generate` 和 `validate` 两个子命令。
3. 解析参数到 `args`。
4. 根据 `args.command` 分发业务逻辑。

这说明它不是业务核心，而是命令网关。

### 5.3 `validate` 为什么适合当 MVP

`validate` 适合教学起点，因为它具备四个优点：

1. 命令最短。
2. 无写入副作用。
3. 全流程完整。
4. 能直接看到边界校验的价值。

新人可以先理解“程序如何检查既有对象”，再理解“程序如何生成新对象”。

### 5.4 最小业务函数做了什么

`validate_employee_source_kit(...)` 的核心动作可以压缩成四步：

1. 规范化 `employee_id`。
2. 计算五件套路径。
3. 逐个文件检查存在性、禁止标记和必须标记。
4. 返回 `SourceKitValidationResult`。

这一步体现了 CLI 设计的一个关键原则：

入口负责分发，业务函数负责真实判断。

## 6. 从 MVP 增长到中等实现

当新人理解了 `validate`，就可以逐层补复杂度。

### 6.1 第一层增量：从校验走到生成

接下来再看 `generate` 子命令。它比 `validate` 多做了两件事：

1. 把命令行输入封装成 `EmployeeSourceKitDefinition`。
2. 调用 `generate_employee_source_kit(...)` 先生成，再自动回调一次 `validate_employee_source_kit(...)`。

这说明生成不是裸写文件，而是“生成后立刻自校验”。

### 6.2 第二层增量：从字符串到结构化对象

真实实现没有把参数直接散着传，而是引入了几类稳定对象：

1. `EmployeeSourceKitDefinition`：输入模型。
2. `GeneratedEmployeeSourceKit`：生成结果模型。
3. `SourceKitValidationIssue`：单条校验问题。
4. `SourceKitValidationResult`：校验汇总结果。

这一步的价值是让程序更可测试、更可扩展、更容易读。

### 6.3 第三层增量：从单文件逻辑到模板渲染

生成不是硬编码写五次，而是先由 `_render_source_kit(...)` 组装一个字典，再调用：

1. `_render_agent(...)`
2. `_render_soul(...)`
3. `_render_memory(...)`
4. `_render_colleagues(...)`
5. `_render_social(...)`

这代表生成逻辑已经分层：

1. 上层决定“需要哪几份文件”。
2. 下层负责“每份文件如何渲染”。

### 6.4 第四层增量：从路径拼接到统一规范化

`employee_id` 并不是直接拿来拼路径，而是先通过 `normalize_workspace_id(...)` 规范化。

这一步解决的是：

1. 大小写不统一。
2. 空格和下划线不统一。
3. 路径注入和非法字符问题。

也就是说，这不是文案整理，而是正式的输入规范协议。

### 6.5 第五层增量：从本地生成到边界治理

validator 不只检查文件存在，还检查内容里有没有被禁止的运行态信息，比如：

1. 当前 live 入口位于哪里。
2. support payload 的员工路径。
3. `.tricompany-cognition` 这类 runtime 路径。
4. 阶段记忆记录、工作事项记录、社交事项记录等消费数据标记。

这一步告诉新人：

成熟 CLI 的重点不是“把东西写出来”，而是“确保不会写错层”。

## 7. 再从中等实现走到完整工作流

当你理解 source kit 本体后，就要把它放回完整工作流里。

### 7.1 Source kit 只是上游输入

它的产物位于：

- `TriCompany/.github/source-agents/<employee-id>/`

这些文件的职责是定义源侧岗位契约，不是 live discovery 入口。

### 7.2 下一站是 binding profile

当源侧五件套稳定后，发布链会把宿主绑定事实写入：

- `TriCompany/.github/binding-profiles/<employee-id>.json`

这里记录的是：

1. 当前宿主阶段。
2. live entry 路径。
3. support object 路径。
4. runtime namespace 规则。

### 7.3 再下一站是 support payload

随后 `host_object_generation` 会把 role、employee、org、audit workspace 写到：

- `TriCompany-copilot-host-assets/knowledge/roles/...`
- `TriCompany-copilot-host-assets/knowledge/employees/...`
- `TriCompany-copilot-host-assets/knowledge/org/shared`
- `TriCompany-copilot-host-assets/knowledge/audit`

### 7.4 最终才是 live agent 协作

当前 live 入口位于：

- `TriMetaverse/.github/agents/...`

也就是说，一个 agent 在宿主里能稳定工作，不是因为有一份 `.agent.md` 就够了，而是因为：

1. source 定义稳定。
2. binding 关系清楚。
3. support payload 可消费。
4. runtime namespace 有边界。
5. live discovery 入口唯一。

## 8. 这套 CLI 的完整实现地图

对研发新人来说，完整实现至少要分五个文件层面来看。

### 8.1 第一层：CLI 入口

- `runtime/cognition/employee_source_kit.py`

负责：

1. 主入口。
2. `argparse`。
3. 子命令分发。
4. 生成和校验。

### 8.2 第二层：路径与工作空间抽象

- `runtime/cognition/knowledge_workspace.py`

负责：

1. 规范化 id。
2. 计算 knowledge workspace 路径。
3. 定义 role、employee、org、audit 四类工作空间。

### 8.3 第三层：发布 wrapper

- `runtime/cognition/employee_host_publish.py`

负责把：

1. support payload 生成。
2. binding profile 写入。

放到同一条命令里统一完成。

### 8.4 第四层：对象集声明与落盘

- `runtime/cognition/host_object_generation.py`

这里定义了：

1. `HostObjectSetDefinition`
2. `GeneratedHostObjectSet`
3. `generate_host_object_set(...)`
4. `write_host_binding_profiles(...)`

这是连接 source 定义、support payload、binding profile 的核心中台。

### 8.5 第五层：验证与回归

对应的验证文件包括：

1. `runtime/cognition/employee_source_kit_validation.py`
2. `runtime/cognition/role_employee_workspace_validation.py`
3. `runtime/cognition/employee_host_publish_validation.py`
4. `runtime/cognition/rd_trainer_host_object_generation_validation.py`

这说明当前实现不是手工自信，而是有回归入口的。

## 9. 生产级考虑应该怎么看

到这里，才进入“生产级考虑”。

### 9.1 入口兼容

文件顶部有 `__package__` 和 `sys.path` 兼容逻辑，这是为了兼容不同启动方式，而不是让导入偶然成功。

### 9.2 退出码

CLI 不是只给人看输出，还要给 shell、task runner、CI 和其他命令调用者看退出码。

### 9.3 幂等与覆盖保护

默认不覆盖现有 source kit，除非显式传 `--overwrite`。

这能防止误写和误覆盖。

### 9.4 输入规范化

所有 `employee_id` 都要先规范化，防止命名漂移和路径越界。

### 9.5 Source 与 Runtime 严格分层

这是最重要的生产级考虑之一。源侧文档、宿主绑定事实、support payload、runtime state 不应该混写。

### 9.6 帮助命令和自解释能力

`--help` 是正式能力的一部分，不是可有可无的附属品。

一个合格 CLI 应该让新同学不用读全部源码，也能先知道命令协议长什么样。

### 9.7 测试不是附加项

当前 CLI 的单测证明了：

1. 生成路径正确。
2. 边界标记正确。
3. 被禁止标记能被识别。
4. support payload 和 binding profile 链路可以回归验证。

### 9.8 明确未做项

成熟设计不只写“做了什么”，也要说清“还没做什么”。

例如这套链路当前并不等于：

1. TriMC 服务器正式版上线。
2. 完整生产级自动化公司。
3. 所有 agent 都已完成正式 live 启用。

## 10. 研发新人学完后要记住的心智模型

### 10.1 第一个模型：CLI 是控制面，不是全部业务

真正的业务逻辑应该落在可复用、可测试的普通函数里。

### 10.2 第二个模型：先有 source truth，再有宿主绑定

不要把 live 宿主现状直接写回源定义。

### 10.3 第三个模型：MVP 不是简陋版，而是最小完整闭环

只要一条命令已经包含“输入 -> 处理 -> 输出 -> 验证”，它就是一个合格 MVP。

### 10.4 第四个模型：复杂度必须解释它解决了什么问题

每增加一个 dataclass、一个 validator、一个 manifest、一个 wrapper，都应该能说明它补上了哪一块缺口。

### 10.5 第五个模型：工作流不是单文件，而是多层协议协作

source kit、binding profile、support payload、runtime namespace、live agent 共同组成工作流，而不是某一个脚本单独完成一切。

## 11. RAndDTrainer 后续讲同类课程的标准套法

后面再讲任何研发技术主题，都可以复用本课的顺序：

1. 先讲最终效果。
2. 再讲理论方法和协议。
3. 先跑最小 MVP 闭环。
4. 再拆 MVP 原理。
5. 再补中等实现和真实复杂度。
6. 再放回完整工作流。
7. 最后讲完整实现和生产级考虑。

如果一门课没有按这个顺序讲，学习者通常会出现两种问题：

1. 一开始就淹没在细节里，不知道自己为什么学。
2. 虽然看过代码，但没有形成稳定心智模型，下一次换主题还得从零开始。

这门 `employee_source_kit` 课程，就是后续所有研发技术课程的一个标准示范。
