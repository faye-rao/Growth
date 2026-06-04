# MoEngage 两段录屏特性拆解（前端 / 后端 / 数据）

> 来源：`Screen Recording 2026-06-02 at 14.23.47.mov`（6′33″，功能导览）、`Screen Recording 2026-06-02 at 14.39.05.mov`（4′03″，Web Experience 实操）。
> 账号：`BotimNewMoeTest`（dashboard-02 / sdk-02 集群，India 节点）。两段均为**无声**录屏，本文基于逐帧画面还原。
> 配套：《Botim增长平台_概念入门与产品需求》《需求清单》。本文目的——把视频看到的能力映射到「前端交互 / 后端逻辑 / 数据」三层，并对齐自研 scope。

---

## 一、两段视频分别讲了什么

| 视频 | 主题 | 一句话 |
|---|---|---|
| **视频1（14.23.47）** | MoEngage 平台**功能地图导览** | 把左侧菜单逐个点开：Analyze（行为/留存）、Segment（含 RFM/Warehouse/Predictive）、Engage（Flows）、Inform、Reports、Data（Computed Traits）。多为"长什么样"，部分是付费未开通的占位介绍页。 |
| **视频2（14.39.05）** | **Web Experience（千人千面 / API 下发）端到端实操** | 用 `Personalize > Web Experience` 走完「① 选人 → ② 配内容 Payload → ③ 排期+目标」三步向导，并暴露了 **服务端 fetch API** 的完整调用方式。这段是真正的"特性深挖"，与自研最相关。 |

---

## 二、视频1：MoEngage 能力清单（功能地图）

按左侧导航逐项记录，并标注「我方是否要做」（依据需求文档 scope）。

### 2.1 Analyze（分析）
- **Behavior（行为分析）**：选事件 → 出 Behavior chart + Behavior table，"Start with selecting events"。即多事件行为趋势/对比。
- **Retention（留存分析）**：
  - `First Event`（首次事件）+ `Return Event`（回访事件），各支持 OR 多事件。
  - **Retention type**：`Unbounded`（截至当天及以后留存）/ `N-Day`（第 N 天）/ `First Occurrence`。
  - `Split by`（按属性拆分）、`Duration`（如 Last 7 Days）。
- → **我方 scope**：数据看板/分析类**明确不做**（数据组马老板自建 BI）。但留存/行为的"事件口径"是漏斗追踪的基础，需对齐。

### 2.2 Segment（分群）—— 自研 P0/P1 核心
菜单项：`New Segment`、`New User Import`、`New File Segment`、`Search Users`、`All Segments`、`RFM Segments`、`Warehouse Segments`、`Predictive Segments`、`User Imports`、`User Exports`。
- **All Segments**：列表（名称 / Segment Type / Created On / Last Run Time / Actions），支持搜索、按类型过滤、Archived 开关、Synced Segments 标签。
- **RFM Segments**：选 Recency / Frequency / Monetary 三个事件（Frequency 可"沿用 Recency 同一事件"）→ 设 Conversion Goal → Filter Users → RFM Options（Analysis type=RFM，日期区间）。即开箱即用的 RFM 价值分群。
- **Warehouse Segments**（付费/BigQuery 早期访问，未开通）：**Zero-Copy**——直接查数仓建分群，免 ETL 搬数，再下发到 Email/SMS/Push/In-app/WhatsApp。
- **Predictive Segments**（付费）：预测型分群（如"即将流失/将沉睡"）。
- → **我方 scope**：**复刻规则引擎（P0-1）+ NL2SQL（P1-1）+ 分群算法（P1-2）**。RFM 是现成可借鉴的分群范式；Warehouse Segments 的"零拷贝直查数仓"思路正好契合 Botim 有 footprint 全量备份的现状。

### 2.3 Engage（触达编排）—— 自研 P1 核心
- **Flows（旅程编排）**：`Create flow`；统计页签 All / Active / Run Yesterday / Drafts；过滤器 created date / delivery type / status / More filters；列表列：Flow Name / Entry type / Status / Created / Performance / Goals / Actions；Archived flows 开关。
- → **我方 scope**：**内容与推送编排 + A/B/N（P1-3）**。Flow 的 Entry type（触发型 vs 批量）、Performance/Goals 列是要复刻的字段。

### 2.4 Inform / Reports
- **Inform**：`All Alerts`（运营/系统告警类通知）。
- **Reports**：`New Campaign Report` / `New Alert Report`，已有 `Campaigns Reports` / `Alerts Reports`。
- → **我方 scope**：报表类基本不做；但 Campaign Report 的指标口径（CTR/CVR/ROI）要在漏斗追踪里覆盖（P1-5）。

### 2.5 Data —— 注意这是"造数据/造标签"层
- **Computed Traits（付费 add-on，未开通）**：无需工程介入，在平台内**用 Count / Aggregation / First-Last Value / SQL Computation 生成新用户属性**（示例：Customer Lifetime Value、Average Order Value、Engagement Score、Preferred Category）。卖点：消除工程依赖、即算即用于分群/个性化。
- → **我方 scope**：对应 Botim 的 **T+1 标签清洗链路**（数据组）。我方不必做平台内 SQL 计算器，但"标签/Computed Trait 能直接用于圈人"这个产品形态值得对齐。

### 2.6 其它导航
`Dashboards`、`Personalize`（→视频2主角）、`Content`（内容/模板库）、`App Marketplace`（集成）、`Test and Debug`、`Settings`。
> 顶栏出现"账户逾期 60 天"红条——测试账号状态，无业务含义。

---

## 三、视频2：Web Experience（千人千面 / API 下发）端到端拆解 ★重点

这段是 `Personalize > Web Experience > Create`，类型 **`Web & App (API)`**。三步向导：**① Target users → ② Content → ③ Schedule and goals**。这正是 Botim 文档里的「**首页千人千面卡片**」对应特性——**MoEngage 只当决策+内容引擎，最后渲染/下发留在客户端**。

### 步骤① Target users（选人）
- 基本信息：`Experience name`（Test-1）、`Experience tags`（all users）、`Experience key`（Test-1，**API 调用时的关键标识**）。
- **Target audience**（可建多个 audience 页签，可"Add Audience"）。
- **Edit Audience 规则编辑器**（弹窗）：
  - `All users` / `Filter users by`（二选一）。
  - 行为规则示例（即"规则引擎"的真实语法）：
    - 「`Has executed` **User Logout** `predominantly with` (Device Height is 5) `in the last 3 days`」
    - OR「`Has executed` **Push ID Register Android** `atleast 1 time in the last 3 days`」
    - OR「`Has executed` **User Logout** `for a minimum of 10% of the times with` (hour of the day is 12:00 AM–01:00 AM **AND** month of the year is January) `in the last 3 days`」
  - 算子能力：频次（atleast N / minimum X% / predominantly）、事件属性条件（Device Height…）、**时间维度条件**（hour of day、month of year）、时间窗（last N days）、`Nested Filter`（嵌套）、`+Filter`、`Exclude Users`（排除）、`In-session attributes`（会话内属性）。
  - `Save for later use`（规则可存为可复用 audience）。
- **Global control group**（全局对照组开关，本例未定义）——A/B 增量验证基础。

### 步骤② Content（配内容 = Payload）
- **Audiences ⇄ Variations 矩阵**：每个 audience 下可建 `Default` + `Variation 1`（+更多）= **A/B/N 测试**；`Users(% of total)` 默认 `Auto`（自动分流），新功能 `Distribute users` 可手动分配比例。
- 每个 variation：`Create Payload` / `Edit Payload`。
- **Define Content Payload（弹窗）**：
  - 维度：`Audience - Text-1` × `Variation - Default`。
  - 内容是 **KV 键值对**：`Variable name` + 类型（`String`…）+ value，`+ KV pair` 可加多对。
  - **关键**：API 类型的 experience **不在 MoEngage 渲染 UI**，只返回一包结构化 KV/JSON，**由客户端自行渲染**。这与 Botim「只借下发、自渲染、不交 Token」边界完全一致。

#### ★ 后端集成真相：Test Experience（fetch API）
内容步骤下方的 **Test Experience** 给出服务端拉取 payload 的完整方式（支持 cURL / Node.js / Go / PHP / Python / Ruby / Java 代码片段）：

```
POST https://sdk-02.moengage.com/v1/experiences/fetch
Headers:
  Accept: */*
  Content-Type: application/json
  Authorization: Basic <base64 token>      # 例: NEdJN0MxM0kzT1VXVlgyMUM0WVdMTEtL...
  MOE-APPKEY: 4GI7C13I3OUWVX21C4YWLLKK_DEBUG
Body:
{
  "identifiers": {
    "customer_id": "<与 ID 字段映射的用户唯一标识>",
    "user_identifiers": { "u_em": "User Email", "u_mb": "Mobile Number" }
  },
  "experience_key": ["Test-1"],
  "Custom_attribute": "<属性值，例 utm_medium: email>"
}
```
- 备注原文：**"You will receive the payload in response only when the experience is published."**（只有 experience 发布后，调用才会返回 payload。）
- **解读**（前/后/数据三层职责划分，极其重要）：
  1. **客户端/Botim 后端** 在需要展示位时，带着 `customer_id`（或 email/手机号）+ `experience_key` 调 `/v1/experiences/fetch`。
  2. **MoEngage 后端** 实时判定：该用户命中哪个 audience、分到哪个 variation → 返回对应 **content payload（KV/JSON）**。
  3. **客户端** 拿到 payload **自行渲染**首页卡片/弹窗。
  4. 整个过程 **MoEngage 不接管推送通道、不持有渲染层**——它是"内容决策 API"。这正是自研最该复刻的协议形态。

### 步骤③ Schedule and goals（排期 + 目标）
- **Send experience**：`Active` / `Active continuously`（持续生效）。
- 排期：`Start date / Send time`、`End date / End time`（本例 02 Jun 2026 17:04 → 02 Jun 2027 16:04）。
- **Experience time zone**：默认 **`Asia/Kolkata (UTC+0530)`**。
  > ⚠️ **给 Botim 的提醒**：账号默认印度时区，**不是 UAE**。Botim 增长团队在迪拜（`Asia/Dubai`, UTC+4），排期/归因/报表的时区口径必须显式设为 UAE，否则"每天几点推"会差 1.5 小时。自研平台应内建时区配置并默认 UAE。
- **Conversion goals**：`Goal name` + `Event name`（例 `App/Site Opened`）+ `New attribute`，可加多目标 → 用于归因与效果回收。
- 顶部三步进度条 + `Save as draft`（草稿）+ "Draft updated successfully" 提示。

---

## 四、前端 / 后端 / 数据 三层归纳

### 4.1 前端（运营操作界面 + 终端渲染）
| 层面 | MoEngage 做法 | 自研启示 |
|---|---|---|
| 运营配置 UI | 三步向导（选人→内容→排期），规则编辑器弹窗、A/B Variation 矩阵、payload KV 编辑器、排期日历+时区 | 复刻"向导式"低门槛配置；规则编辑器是 P0-1 重点；时区默认 UAE |
| 终端渲染 | `Web & App (API)` 类型**不渲染**，只返回 KV/JSON，**App 自渲染** | 完全匹配 Botim「自渲染、借下发」；首页千人千面（P2-1）按此协议自建即可，迁移风险低 |
| 对照/实验 | Global control group + Variation 分流（Auto / 手动 Distribute） | A/B/N（P1-3）必备；补 Botim 现状缺的"全局对照组" |

### 4.2 后端（决策与下发逻辑）
| 层面 | MoEngage 做法 | 自研启示 |
|---|---|---|
| 内容下发协议 | `POST /v1/experiences/fetch`，入参 `identifiers + experience_key`，出参 content payload；Basic Auth + `MOE-APPKEY` | **直接照搬这套"按用户实时返回内容"的 API 契约**；鉴权用 appkey+token |
| 命中判定 | 服务端实时算 audience 命中 + variation 分配 | 需一套近实时规则求值引擎（对应"固定规则近实时链路" P1-8） |
| 发布态控制 | 未发布不返回 payload；草稿/Active/排期窗口控制 | 状态机：draft → published → active(时间窗) → ended |
| 触达边界 | API 型只给内容；Push/SMS 才涉及通道 | 守住 **Token 不外给（P0-3）**，最后一公里走 Botim 接口 |
| 频控 | 视频未展示（Botim 现状本就无频控） | 自研要补 **频次控制/跨活动去重（P1-7）** |

### 4.3 数据
| 层面 | MoEngage 做法 | 自研启示 |
|---|---|---|
| 用户标识 | `customer_id` / `u_em`(email) / `u_mb`(mobile) 多重 identifier 映射 | ⚠️ Botim **无 email**；以 `customer_id`/手机号为主键做 ID-Mapping |
| 圈人原料 | 事件（User Logout、Push ID Register…）+ 事件属性 + 时间维度 | 需拿到埋点 schema（P0-5）；规则算子要支持频次/属性/时间窗/嵌套 |
| 衍生标签 | Computed Traits：Count/Aggregation/SQL 造属性（CLV、AOV、Engagement Score…） | 对应数据组 T+1 标签清洗；标签需能直接喂给圈人 |
| 价值分群 | RFM（Recency/Frequency/Monetary）开箱即用 | 可作为自研分群模板之一 |
| 效果数据 | Conversion goals（事件+属性）→ 归因 | 漏斗追踪（P1-5）按 goal-event 模型设计 |
| 数仓直查 | Warehouse Segments（BigQuery Zero-Copy，免搬数） | Botim 有 footprint 全量备份，可走"直查不搬数"路线 |

---

## 五、对自研需求的直接结论

1. **最值钱的一帧 = `/v1/experiences/fetch` 的 API 契约**。它证明了"千人千面/首页卡片"在 MoEngage 也是**内容决策 API + 客户端自渲染**的模式——和 Botim 现状同构，所以 **P2-1 自建下发风险最低**，可优先验证可行性。建议自研直接定义对等接口：`POST /experiences/fetch { identifiers, experience_key } → { payload }`。

2. **规则引擎语法已拿到真实样本**（频次 atleast/minimum%/predominantly、事件属性、hour/month 时间维度、last N days、嵌套、排除、in-session、OR）。这是 **P0-1 复刻规则引擎** 的字段级输入，也是 **NL2SQL（P1-1）** 要能翻译出的目标 DSL。

3. **A/B/N + 全局对照组** 是 MoEngage 内建、Botim 现状缺失的；自研要把"对照组/分流比例/goal 归因"一起做进编排（P1-3 + P1-7）。

4. **时区是隐藏坑**：账号默认 `Asia/Kolkata`，Botim 在迪拜。自研**默认 `Asia/Dubai`**，排期/归因/报表统一 UAE 口径。

5. **scope 复核**：视频1 大量篇幅是 Analyze/Reports/Computed Traits/Warehouse 等——**这些数据/分析能力按文档归数据组或付费 add-on，我方不做**；我方聚焦 **选人(规则引擎)+内容编排(A/B/payload)+下发API+漏斗追踪** 四件事。

---

## 六、待与 Growth/数据组确认（视频引出的新问题）
- `experience_key` 的命名规范与生命周期管理？一个首页位对应几个 experience？
- `/experiences/fetch` 的**实时性 SLA**？首页加载要分钟级/秒级——决定规则求值要不要近实时（呼应 F1 实时占比命门）。
- payload 的 KV schema 由谁定义（前端约定 vs 配置驱动）？多语言文案（印地/他加禄/阿语/英）如何放进 payload？
- `customer_id` 与 footprint 主键、各业务线 ID 的映射关系（无 email 前提下）。
- 全局对照组在 Botim 是否已有等价机制？Shadow 5% 分流能否复用同一分流器？
