# LG-025 M0d commit② 返工续作交接件（spawn 窗自足开工，2026-09-03）

- sourceOfTruth: 本件（FD 小全常驻窗中止报+CTO 续作令合成留档）；syncMode: static；lastSyncedAt: 2026-09-03
- 性质：commit② 返工令（R1-R5）+续作令配方+中止报三合一——spawn 窗读本件+CTO 两令文即自足开工，无需前会话上下文

## 一、返工令规格（R1-R5，CTO 2026-09-03T12:4xZ）

- **R1 值形态**：sourceFiles 值改仓库前缀形态 `TriCompany/source-agents/<id>/<suffix>.agent.md`（§B 契约正身，与 liveEntries[].source 同形态；全域 78 键值=13 席×6 键）
- **R2 CSO/DE 合并投影**：colleagues/social 两键照 contract.paths 显式声明改指合并式 `colleagues-social.agent.md`（sourceFiles=contract.paths 的 manifest 投影，禁止自创文件名）
- **R3 frontmatter 映射**：agent_frontmatter 改指实存在的 agent-frontmatter.agent.md
- **R4 pre-pass 基座**：解析对齐 TriCompany 仓根（与 R1 值形态一致）
- **R5 存在性检查**：sourceFiles 所指文件 resolve 不到即 error（source_files_not_found:<key>）

## 二、已验证资产（前窗实证）

1. **重投影脚本逻辑**：逐席读 contract.yaml paths 六键原文（文本解析 `^paths:\n((?:  [a-z_]+: .+\n)+)`）→ 值=TriCompany/source-agents/ 前缀形态 → 更新 manifest 13 条 role-agent。13/13 验证过（CSO/DE colleagues/social 同指 colleagues-social.agent.md 实证）。脚本被前窗清理，依本节描述重建（核心 15 行）。
2. **manifest 工作区现态**：R1 前缀形态重投影版**未提交在位**（git status M）——保留续用或重放皆可。
3. **R4/R5 preflight 代码全文**（前窗已写，checkout 回退，重落即可）：
   - 常量 SOURCE_FILES_REQUIRED_KEYS = ("soul","agent_body","agent_frontmatter","memory","colleagues","social")
   - `_source_files_preflight(entry, source_root)`：kind!=role-agent 豁免；sourceFiles 非 dict → source_files_missing:sourceFiles；六键逐键——值空 → source_files_missing:<key>；值不带 TriCompany/source-agents/ 前缀 → source_files_not_found:<key>；(source_root/剥前缀值).is_file()=False → source_files_not_found:<key>
   - 插入点：run_agent_publish `for entry in entries:` 循环头（source_publish_check.py :1357 附近），error 走 AgentPublishItem(action="error") 前置拦截
4. **fixture 翻法**（32 处已翻后回退，重翻）：validation 文件全局 Replace——①`"kind": "role-agent",` → 加 sourceFiles 六键前缀值字面（ceo 路径）；②`target_file = self.support.root / ".github"` → `self.source.root.parent / ".github"`；③`self.support.write("TriMetaverse/.github/agents/` → `self.source.write_live("TriMetaverse/.github/agents/`（TreeFixture 需带 subdir 嵌套+write_live 方法，见下）。
5. **TreeFixture 改法**：__init__ 加 subdir 参数（root=<td>/<subdir>）；CLI 族 setUp `self.source = TreeFixture(subdir="TriCompany")`；write_live(relative, content)=root.parent 剥 TriMetaverse/ 前缀写。
6. **_write_agent_source 种六件基座**：helper 写 ceo.agent.md 后循环种六件 kit 文件（soul.agent.md/agent-body.agent.md/agent-frontmatter.agent.md/memory.agent.md/colleagues.agent.md/social.agent.md，内容非空）——R5 存在性解析的实存基座。**注意 RootFixture 双实例**：write_live 必须经 source fixture（source.root.parent），勿经 support（两临时根不同=上轮 14 fail 根因）。

## 三、上轮 14 fail 根因（勿重蹈）

fixture 种件（write_live 经 support fixture → support.root.parent=tmp 根A）与 R5 存在性解析（source_root.parent=tmp 根B）**基座错位**——R4/R5 与 fixture 翻必须**同批同基座（TriCompany 仓根替身）落，勿分批试**（CTO 续作令原文）。

## 四、新窗实施序（CTO 续作令）

1. manifest R1 版重放或续用（工作区在位）
2. pre-pass（R4/R5 版，source_root 参数）
3. HostObjectSetDefinition 同步 source_files 定义字段（dataclass 加 `source_files: Mapping[str,str] | None = None`+组装段 definition.source_files or 规则生成六键含 R2 合并投影——前窗已写，checkout 回退重落）
4. fixture 翻 18+三件套永久断言（值前缀断言/contract 投影对表 sourceFiles==contract.paths 投影逐键/存在性 error 断言——COS 第二方法固化）
5. 全量 unittest 绿（373+新增）+employee_host_publish --dry-run rc=0+真值面对表（COS 复核法可复跑）

## 五、约束

- commit② 重做独立 commit（ae349e8 冻结在史不 revert 不扩散）
- manifest R1 工作区版在位不动（续用）
- 真源/渲染物零手编辑；有阻即回 CTO
- 批 1 滚收已毕：66065c9（SOUL_NAMED_GATE 5 席）——与本返工无文件冲突，可同窗先后

## 六、窗中止报（前窗实况）

前窗（FD 小全常驻）完成 R1-R3 验证+R4/R5 落码+fixture 32 处翻+种六件后，全量 14 fail（基座错位族），窗口枯竭未能逐族收敛——git checkout 三文件回退+删临时件，377 门 OK 恢复。窗末自报义务已履行（COS 在案候 CEO /compact 或重启裁）。
