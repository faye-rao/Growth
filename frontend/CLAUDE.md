# CLAUDE.md — frontend（运营控制台 · 计划中，尚未实现）

> 现状：**前端尚未实现**，本目录目前只有本记忆文件。后端是 7 个 REST 服务 + API 网关。
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
