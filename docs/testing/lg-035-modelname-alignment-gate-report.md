<!-- sourceOfTruth: TriCompany/docs/testing/ | syncMode: local-only | lastSyncedAt: 2026-09-11T20:26+0800 -->

# LG-035 模型名标准化对表报告 — STE 门禁族五件（STE 小柯）

- 结论：**对表完成，PASS 口径**——全量 135/135 双跑全绿，daemon 兼容判据实测无升级项
- 对象：TriModel 1ab2bfa（五官方名标准化）+ 1fb16a1（TriMMC 卡片 v2）；本席对表件 commit f8e752e
- 时点：2026-09-11 20:07（对表开工）→ 20:26（本报告）

## 一、对表读数

| 件 | 对表前（CTO 预扫描） | 对表后 |
|---|---|---|
| build.chain.gate | 3p1f | **4/4 绿**（失败源=门禁件 typecheck prefix 属性，随对表消解） |
| keys.secure.gate | 6p1f | **7/7 绿**（跃迁夹具转官方名 GLM-5.3+from 断言 deepseek-v4-pro） |
| policy.gate.e2e | 7p8f | **15/15 绿**（全夹具官方名化：GLM-5.3/deepseek-flash 轮换） |
| policy.gate.evaluation | 8p2f | **10/10 绿**（U11 envDefault 官方名+helper 夹具） |
| proxy.gate | 2p5f | **7/7 绿**（三组精确路由重构+TMV 新案+case 负案） |

**全量终读数：135/135 pass / 0 fail 双跑稳定**（1ab2bfa+1fb16a1 聚合面）；tsc 绿；本席五件 lint 0 error（test-dir 13 errors=FSD anthropic-proxy.test 6+存量 relay-sandbox 7，归因清白）。

## 二、对表三方向落实

1. **旧名值→五官方名**：`tmv-*` 全退役——env 钉值/夹具模型/断言期望/跃迁 from-to 全数转 `deepseek-flash`/`deepseek-v4-pro`/`GLM-5.3-Flash`/`GLM-5.3`/`TMV`（大小写精确）。
2. **UPSTREAM_ROUTES prefix→三组官方名精确匹配**：prefix 形态断言退役，转 `matchModels` 精确匹配+`route.label` 断言（deepseek-anthropic/glm-anthropic/tristaciss-anthropic）；剥壳退役=官方名 verbatim 透传断言；新增 **TMV→tristaciss 路由案**（/v1 尾剥除拼接验证）。
3. **catalog 精确大小写负案**：新增 `'glm-5.3'` 小写→no-upstream-route（502 族）断言 ✓。

**502 E2E 前提重构**：policy PUT 现被五名集校验挡下（非官方名 400），未匹配模型 502 的现实路径=env 误配——E2E 改经进程内 env 构造，语义更真。

## 三、daemon 兼容性判据（CTO 令，实测回执）

锚③真链轮询（真 TriRLC key-cache+真 TriModel server）以官方名 **GLM-5.3** 为策略翻转目标实测：daemon 拉新 default_model + `applyKeyCacheToEnvironment` 落 env 全绿——**daemon 客户端消费非 tmv 官方名零兼容问题，无升级项**。

## 四、1fb16a1 新增对表面处置

| 项 | 处置 |
|---|---|
| ① policy type 扩展（fixed/双向优先级/quota） | 本席夹具全 window 缺省 type——向后兼容由 FSD 既有族零改动实证+本席 e2e 15/15 复证 ✓；fixed/优先级新语义断言挂候办（候派工或下批并入） |
| ② trimmc-card 三端点（admin 三态/悬挂 400/五名交集） | **可扩项本批未扩**——KB 族扩展挂候办；admin-token 三态模式与 KB5 同族，扩展成本低 |
| ③ trimmc-card.json 入 gitignore | 知悉 ✓；本席 e2e 不写该文件（无 override 需求） |

**并发窗 policy.json 真根写入甄别**：双方知悉，无 action ✓（本席快照协议未被波及）。

## 五、使用依据

- TriModel：1ab2bfa/1fb16a1 实盘核验、本席对表件 f8e752e、`npm test` 双跑+`npm run check`+eslint 现跑读数（2026-09-11 20:07-20:25）
- 令源：CTO 20:07 对表开工令+20:22 卡片落库通报
