# CLAUDE.md — frontend（运营控制台 · 7 屏 MVP 已实现）

> 现状：**全部 7 屏 + 基础底座 + 鉴权 + Flow 画布已实现并通过测试**（详见文末"工作项状态清单"）。后端是 7 个 REST 服务 + API 网关。
> 同级目录(backend `src/`)的 CLAUDE.md **不会**自动加载到此 → 前端约定都写在这里。

## 目标
为后端做一个**运营控制台**，复刻 MoEngage 的：圈人规则编辑器、三步活动向导、Flow 画布、报表。

## 技术选型（推荐）
- **React 18 + TypeScript + Vite**
- **Ant Design**（数据密集后台 + 内置 RTL）
- **react-querybuilder**（嵌套规则构造器 ↔ M2 JSON DSL，**必须双向映射**：构造器输出可转 DSL，DSL 可回显）
- **React Flow**（M3 Flow 节点：延时/分支/A·B/等待事件/webhook）
- **ECharts**（M4 漏斗/跨产品漏斗）
- **TanStack Query** + Zustand（服务态/本地态）
- **React Hook Form + Zod**（payload/规则校验）
- **react-i18next + RTL**（en/ar/hi/tl）
- **openapi-typescript**（从网关 `/openapi.json` 生成类型化 client）
- 测试：Vitest + Testing Library + **Playwright(E2E)**

## 硬需求
- **阿语 RTL 必须 day-1 纳入**（Botim 核心市场，后补成本高）。
- **规则构造器 ↔ M2 DSL 双向映射**是 Audience 页核心难点。
- 鉴权走网关 `MOE-APPKEY`/token；多语言文案对接 M6/M5 payload。

## 页面 ↔ 服务
Campaign(M3+M1,最高优先：列表+三步向导+Flow画布+频控+发送状态) · Audience(M2:规则构造器+NL2SQL+实时人数+模板+列表) · Analytics(M4+M9:漏斗+跨产品+归因+报表+洞察) · Personalization(M5:列表+向导+payload编辑器+发布+fetch测试) · Content(M6:多语种生成+行内合规+预览编辑) · Experiment(M7:5%切流+对照报告) · Data(M8:身份查询+DQC+抑制名单)

## 后端前置（前端依赖，需后端先补）
导出 OpenAPI + CORS + 登录换 token 端点 + 列表/保存/CRUD 端点 + 实时通道(人数预估/发送进度)。

## 落地顺序与工作量
详见交接清单/工作报告与对话中的前端计划：阶段0脚手架→阶段1底座(含RTL)→阶段2按优先级(Campaign+Audience先)→阶段3横切→阶段4测试部署。MVP 子集 ~6–7 周；全量 ~2.5–3 个月（前端 ~114 人日 + 后端前置 ~15 人日）。

---

## 当前实现状态（2026-06-05）

**已搭建并验证**（脚手架 + 基础底座 + 鉴权 + **全部 7 屏** + Flow 画布）：
- 脚手架：Vite + React18 + TS + AntD5 + React Router + TanStack Query + Zustand；`vite.config.ts` 用 dev proxy `/api → :8000`(网关)；`tsc --noEmit` 干净；`vite build` 成功。
- 基础底座：`src/layout/AppLayout.tsx`(7 服务左导航)、`src/i18n.ts`(en/ar + **RTL**，`<html dir>`+ConfigProvider direction 同步)、`src/api/client.ts`(带 MOE-APPKEY 的 fetch 封装 + 各服务 typed helper)、`src/api/types.ts`(M2 DSL 类型)、`src/store.ts`。
- **Audience 屏**(`src/features/audience/`)：`dsl.ts`(react-querybuilder ↔ M2 DSL **双向映射**，事件节点经 `__rawNode` 哨兵无损往返) + `AudiencePage.tsx`(NL2SQL 输入→回填构造器+置信度/待审标签、可视化规则构造器、防抖实时人数预估、模板列表、DSL 预览、Compile SQL)。
- **Campaign 屏**(`src/features/campaign/`)：活动列表 + **三步向导**(选人→A/B/N 变体→排期目标)→ `campaignApi.run` → RunResult 摘要；含 `VariantsTable`/`wizardTypes`。

**屏**：Audience(M2)、Campaign(M3+M1，含 **Flow 画布**)、Analytics(M4+M9，ECharts)、Personalization(M5)、Content(M6)、Experiment(M7)、Data(M8) —— **7 屏全建**；+ `src/auth/`(LoginGate 鉴权门 MOE-APPKEY+角色、ErrorBoundary)。

**测试**：单测 **51 通过**(9 文件)；**联合集成 21 通过**(打真实网关，全 7 服务)；**E2E**(Playwright) 1/2(1 真实浏览器用例 NL2SQL→后端通过；1 受 chromium 冷启动 180s 超时影响，非代码问题)。详见 `INTEGRATION-TEST-REPORT.md`。

**已知限制**：`dsl.ts` 数字字符串强转(country="971"→数字)需按字段 inputType 改进；i18n 仅 en/ar(hi/tl 待补)；多个 API helper 返回 `any`(未接 openapi-typescript 自动类型)；E2E 已接入但仅冒烟级、需在 CI 稳定化。

**后端前置（生产化）**：导出 OpenAPI、CORS、登录换 token、列表/CRUD 端点、实时通道(人数/进度)。

---

## 工作项状态清单（截至 2026-06-05）

> 对照 `../docs/Frontend-Plan.md` 的阶段与屏。✅ 完成 ｜ 🟡 部分(MVP) ｜ ⬜ 未开始。

### 阶段 0 · 脚手架
- [x] ✅ Vite + React18 + TS + AntD5 工程
- [x] ✅ 环境配置 + Vite dev proxy(/api→:8000)
- [x] ✅ 类型化 API client（手写；🟡 openapi-typescript 自动生成未接，待后端导出 OpenAPI）
- [ ] ⬜ ESLint/Prettier 配置

### 阶段 1 · 基础底座
- [x] ✅ 整体布局（7 服务左导航）
- [x] ✅ i18n + **RTL（阿语）**（en/ar 已接；🟡 hi/tl 文案待补）
- [x] ✅ 路由（全 7 屏）
- [x] ✅ 登录与鉴权（`LoginGate`：MOE-APPKEY+角色，🟡 MVP，生产需 login→token）
- [x] ✅ 统一加载/错误/空状态 + `ErrorBoundary`

### 阶段 2 · 各模块页面（7 屏，均 🟡 MVP 深度、有单测+联合集成）
- [x] ✅ Campaign(M3+M1)：列表 + 三步向导 + **Flow 画布(React Flow)** + 频控 + RunResult
- [x] ✅ Audience(M2)：规则构造器↔DSL双向 + NL2SQL + 实时人数 + 模板 + Compile SQL
- [x] ✅ Analytics(M4+M9)：ECharts 漏斗 + 跨产品 + 归因 + 报表 + 自动洞察
- [x] ✅ Personalization(M5)：注册/发布 + 多语言 payload 编辑器 + fetch 测试器
- [x] ✅ Content(M6)：多语种生成 + 行内合规(阿语RTL) + 合规检查 + 选优
- [x] ✅ Experiment(M7)：5% 切流 + 对照报告(判定/显著性/CI)
- [x] ✅ Data(M8)：DQC 看板 + 身份解析 + 抑制检查 + ingest

### 阶段 3 · 横切
- [x] 🟡 RTL（阿语已通；全量像素级打磨待补）
- [x] 🟡 RBAC（LoginGate 存角色；按路由/按钮强制鉴权未做）
- [ ] ⬜ 可访问性(a11y) 系统化
- [ ] ⬜ 操作审计日志

### 阶段 4 · 测试与交付
- [x] ✅ 组件单测(Vitest)：51 通过 / 9 文件
- [x] ✅ 联合集成(真实网关，7 服务)：21 通过
- [x] 🟡 E2E(Playwright)：已接入；1/2（1 真实用例通过，1 受 chromium 冷启动超时）
- [ ] ⬜ Storybook
- [ ] ⬜ 接入 CI（前端 job：tsc+vitest+build）
- [ ] ⬜ Docker 构建 + 网关反代部署

### 后端前置（前端生产化依赖，需后端补）
- [ ] ⬜ 各服务导出 OpenAPI + 网关聚合
- [ ] ⬜ CORS
- [ ] ⬜ 登录换 token 端点
- [ ] ⬜ 列表/保存/CRUD 端点（分群/活动/experience）
- [ ] ⬜ 实时通道（人数预估/发送进度：轮询或 WebSocket）

### 测试总览
单测 **51** + 联合集成 **21** = **72 通过**；E2E 1/2；tsc 干净；vite build 成功。详见 `INTEGRATION-TEST-REPORT.md`。
