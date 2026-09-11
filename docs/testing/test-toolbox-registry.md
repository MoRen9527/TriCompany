<!-- sourceOfTruth: TriCompany/docs/testing/ | syncMode: local-only | lastSyncedAt: 2026-09-11T21:47+0800 -->

# 测试工具箱台账（Test Toolbox Registry）

> 维护纪律（CEO 2026-09-11 21:28 立，STE 席维护）：①测试工具增减/版本变动一律走本台账（增改有痕）；②工具「有弹药无枪」状态（二进制在盘、驱动未装）显式标注防误判；③每季现勘复核一次（下次复核窗：2026-12）。
> 首册底稿=STE 2026-09-11 21:18 现勘盘点（COS 工具盘点问询件，CEO 21:17 指令触发）。

## 一、浏览器二进制层（环境缓存，非登记工具——随构建/通道产物漂移）

| 项 | 现势（2026-09-11 现勘） | 注记 |
|---|---|---|
| ms-playwright 缓存 | chromium×5（最新 **1228**，chrome-win64 布局）/firefox/webkit/headless_shell/ffmpeg | 位=`%LOCALAPPDATA%\ms-playwright\`；版本随 playwright 安装史漂移，驱动以 executablePath 钉死+回退发现兼容 |
| puppeteer 缓存 | chrome + chrome-headless-shell | 位=`~/.cache/puppeteer/`；无驱动包消费方，闲置 |
| mcp-chrome 四构建 | 766f2c5/a55e462/c292570/c2cce98 | Claude MCP 浏览器通道产物，环境缓存非登记工具 |

## 二、驱动库层（登记工具）

| 工具 | 版本 | 部署位 | 调用方式 | 登记 |
|---|---|---|---|---|
| playwright-core | ^1.63.0 | TriModel devDependencies | node:test 内 `chromium.launch({ executablePath })`，钉 `%LOCALAPPDATA%\ms-playwright\chromium-1228\chrome-win64\chrome.exe`；覆写=`TRIMODEL_E2E_CHROMIUM`；回退=缓存目录最新 chromium-\* 发现（文档化于门禁件头注） | 2026-09-11 STE（CTO 裁定采纳；devDep-only 纪律） |
| jsdom | ^29.1.1（+@types/jsdom） | TriModel devDependencies | FSD 在飞批（UI 重设计批次依赖，未落库） | 2026-09-11 FSD 批（候落库转正登记） |

- 「有弹药无枪」历史状态已消解：2026-09-11 前=二进制在盘驱动全缺（六仓零驱动包）；现=playwright-core 首枪入库（jsdom 系 FSD 在飞第二批）。

## 三、既有 E2E 实践指针

| 实践 | 位 | 注记 |
|---|---|---|
| TriCade manual-e2e-runbook | W33 init-collab 树 | CEO 亲测版 2026-08-15，手工 E2E 步骤书 |
| LG-026 gate4-live-e2e | 12of12 log 在档 | live 链路 E2E 先例（信件闸门） |

## 四、现役 E2E 门禁族（LG-035）

| 件 | 覆盖 | env-gate 规则 |
|---|---|---|
| TriModel `test/ui.e2e.gate.test.ts`（E1-E8） | 首启引导态/连接重拉/下拉五名逐字节/卡片条目提交落库/通道词汇零出现（真渲染 DOM 扫描）/眼睛真实点击/错令牌人话指引/全页截图 | chromium 或驱动包缺席→整族显式 SKIP（SKIP 理由含尝试路径与安装指引），禁静默绿；两相位 boot（无/有 ADMIN_TOKEN） |

## 五、复核记录

| 时点 | 复核人 | 结论 |
|---|---|---|
| 2026-09-11 | STE 小柯 | 首册建立（现勘口径） |
