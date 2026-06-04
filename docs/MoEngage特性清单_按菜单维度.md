# MoEngage 特性清单（按大菜单维度组织：前端 / 后端 / 数据处理）

> 依据两段录屏逐帧还原。账号 `BotimNewMoeTest`（dashboard-02 / sdk-02，印度集群）。
> 数据底座前提：客户已有 **App SDK 端内打点数据**（event + 事件属性 + 用户标识）。
> 证据等级：📹 视频实操/详看 ｜ 🔎 导览页一闪而过 ｜ 🧩 菜单仅露出、未点开（基于 MoEngage 通识推断）。
> 可建性：✅ 端内数据可直接支撑 ｜ ⚠️ 需补数据/映射/实时流 ｜ 🟥 依赖付费/模型/额外工程。

---

## 1. Segment（用户分群）📹 重点

### 1.1 前端
- 列表页：Segments / Synced Segments 双页签；搜索框、Select Segment Type 过滤、Archived Segments 开关；表头 Custom Segment Name / Segment Type / Created On / **Last Run Time**(可排序) / Actions；空状态 "No results found"；右上 `+ Segment`。
- **New Segment 类型选择弹窗**：`Filter Segment` / `RFM Segment`（Auto-segment by Recency/Frequency/Monetary）/ `File Segment`（名单导入）/ `Predictive Segment`。
- 入口菜单：New Segment / New User Import / New File Segment / Search Users / All Segments / RFM Segments / Warehouse Segments / Predictive Segments / User Imports / User Exports。
- **规则编辑器**（与 Personalize 共用，见 §3.1）：All users / Filter users by；行为条件「Has executed 事件 + 频次 + with 属性 + last N days」；嵌套/排除/OR/In-session。
- **RFM 配置页**：Recency/Frequency/Monetary 三事件选择（Frequency 可复用 Recency 事件）+ Conversion Goal + Filter Users + RFM Options（Analysis type=RFM、日期区间）。
- Warehouse Segments 介绍页（🔎 付费未开通）：Zero-Copy 直查数仓、下发 Email/SMS/Push/In-app/WhatsApp。

### 1.2 后端
- 分群求值引擎：按规则在事件数据上算命中人群。
- 分群运行调度：`Last Run Time` 表明**批量跑批**（定时/手动）；Synced Segments=向下游同步；Archived=归档。
- RFM 计算服务：按三事件 + 日期窗算 R/F/M 分箱。
- Warehouse 直查（🧩 付费）：BigQuery 上跑分群、零拷贝。
- Predictive 分群（🧩 付费）：模型打分人群（流失/沉睡）。

### 1.3 数据处理
- 输入：端内 event + 事件属性 + 用户属性。✅
- 用户标识：customer_id / u_em / u_mb 多重 identifier。⚠️(Botim 无 email)
- RFM 衍生：基于事件自动算 R/F/M。✅
- 名单导入/导出：File Segment / User Imports / User Exports。✅
- 预测特征：🟥 需模型与训练数据。

> **自研映射**：P0-1 复刻规则引擎 + P1-1 NL2SQL + P1-2 分群算法。RFM/File Segment 可作模板；Warehouse/Predictive 暂不做。

---

## 2. Engage（触达编排 / Campaigns / Flows）📹 列表 + 🧩 编排细节

### 2.1 前端
- **Flows 列表**：顶部统计 All / Active / Run Yesterday / Drafts(计数)；过滤 Search flows / Select created date / **Select delivery type** / Select status / More filters；Archived flows 开关；右上 `+ Create flow`。
- 列表列：Flow Name / **Entry type**（触发型 vs 批量）/ Status / Created / **Performance** / **Goals** / Actions。
- 🧩 编排画布（视频未进入）：MoEngage 通识为多步骤旅程——延时 / 分支 / A·B / 等待事件 / 渠道节点。
- 与 Reports 联动：New Campaign Report（见 §7）。

### 2.2 后端
- Flow 执行引擎：Entry type 决定**触发型**（实时事件驱动）或**批量**（排期）。⚠️触发型依赖实时流。
- 多渠道下发：Push / SMS / In-app / WhatsApp / Email（🧩 视频未展示发送细节）；**推送 Token 红线走客户端**。
- 状态机：Draft / Active / 归档；Run Yesterday 统计 = 跑批记录。
- Goals/Performance 统计服务：活动级转化与表现回收。
- 频次控制：🟥 视频未见，自研需补（跨活动去重 + 每用户上限）。

### 2.3 数据处理
- 触达流水：用户级"已发→已读→转化"日志。✅
- 归因：按 Goal + 归因窗口算活动功劳。✅
- Performance 聚合：CTR/CVR/ROI 口径（与 Reports 一致）。✅

> **自研映射**：P1-3 内容与推送编排(A/B/N) + P0-2 触达执行(Push+In-app) + P1-7 频控去重 + P0-3 守 Token。

---

## 3. Personalize（千人千面 / Web Experience）📹 端到端实操 — 最核心

### 3.1 前端（三步向导）
- **路径**：Personalize > Web Experience > Create，类型 `Web & App (API)`。进度条：① Target users → ② Content → ③ Schedule and goals；Save as draft / Previous / Next。
- **① Target users**：Experience name / tags / **Experience key**（API 标识）；Target audience（多页签 + Add Audience）。
  - **Edit Audience 弹窗**：Audience name；All users / Filter users by；
    - 行为规则：「Has executed **事件** + 频次算子 + with(属性条件) + in last N days」
    - 频次算子：`atleast N times` / `for a minimum of X% of the times` / `predominantly`
    - 属性条件：`Device Height is 5`；时间维度：`hour of the day`、`month of the year`
    - Nested Filter / +Filter / OR；Exclude Users；In-session attributes；Reset Filters；**Save for later use**
  - **Global control group** 开关（对照组）。
- **② Content**：Audience × Variation 矩阵（Default + Variation 1…= A/B/N）；`Users(% of total)`=Auto 或手动 `Distribute users`；每 variation `Create/Edit Payload`。
  - **Define Content Payload 弹窗**：Audience×Variation 维度；**KV 键值对**（Variable name + 类型 String… + value，`+ KV pair`）。API 型**不渲染**，仅回 JSON。
- **③ Schedule and goals**：Send experience = Active / **Active continuously**；Start/End date + Send/End time；**Experience time zone**（默认 Asia/Kolkata ⚠️应改 Asia/Dubai）；**Conversion goals**（Goal name + Event name 如 App/Site Opened + New attribute，多目标）。

### 3.2 后端（★ 真实 API 契约）
```
POST https://sdk-02.moengage.com/v1/experiences/fetch
Headers: Accept:*/*  Content-Type:application/json
         Authorization: Basic <token>   MOE-APPKEY: <appkey>_DEBUG
Body: {
  "identifiers": { "customer_id":"<映射ID>",
                   "user_identifiers": {"u_em":"User Email","u_mb":"Mobile Number"} },
  "experience_key": ["Test-1"],
  "Custom_attribute": "<属性值, 例 utm_medium: email>"
}
```
- 多端代码片段：cURL / Node.js / Go / PHP / Python / Ruby / Java。
- 命中与分流：服务端实时判定 audience 命中 → 分配 variation → 返回 payload。
- **发布态门控**：未发布不返回 payload。
- 不接管渲染与推送通道——纯"内容决策 API"。

### 3.3 数据处理
- 入参标识：customer_id（主）/ email / mobile。⚠️ Botim 无 email。
- 命中所需：端内事件 + 属性 + 时间窗（✅ 已有）；In-session 实时属性（⚠️ 需实时流）。
- 出参：结构化 KV/JSON payload，客户端自渲染。
- 多语言文案放入 payload（🧩 待定义 schema）。

> **自研映射**：P2-1 首页千人千面**自建下发风险最低**——直接定义对等接口 `POST /experiences/fetch{identifiers,experience_key}→{payload}`。

---

## 4. Analyze（分析）📹 Behavior + Retention

### 4.1 前端
- **Behavior**：选事件（多步）→ Apply → Behavior chart + Behavior table；Set alert / Save；"Start with selecting events"。
- **Retention**：First Event + Return Event（各支持 OR 多事件）；**Retention type**= Unbounded / N-Day / First Occurrence（带说明）；Filter Users；Split by；Duration(如 Last 7 Days)；Set alert / Save。
- 通用：Know more / Watch video。

### 4.2 后端
- 行为/留存计算引擎：在事件流上算趋势、N 日留存矩阵。
- 告警：Set alert（指标阈值触发）。
- 保存：分析可存为报表复用。

### 4.3 数据处理
- 纯基于端内事件 + 用户分群过滤。✅
- 按属性 Split by 拆维。✅

> **自研映射**：分析/看板**归数据组**，我方不做；但事件口径要对齐漏斗追踪(P1-5)。

---

## 5. Dashboards（看板）🧩 仅菜单露出

### 5.1 前端
- 顶部首项导航。视频**未点开**；MoEngage 通识为自定义指标卡片/图表拖拽看板。

### 5.2 后端 / 5.3 数据处理
- 🧩 聚合查询服务 + 指标缓存（未观察到细节）。

> **自研映射**：**明确不做**（数据组马老板重建 BI）。列此条仅为菜单完整性。

---

## 6. Data（数据 / Computed Traits）🔎 介绍页

### 6.1 前端
- Computed Traits 介绍页（付费未开通）：无工程依赖在平台内造属性；卖点页签 Effortless Attribute Creation / Hyper-Personalized / Granular Targeting / Enrich Customer Profile / Optimize Resources。

### 6.2 后端
- 属性计算引擎：Count / Aggregation / First-Last Value / **SQL Computation**。🟥 付费。
- 产出可直接用于分群/个性化。

### 6.3 数据处理
- 衍生属性示例：Customer Lifetime Value / Average Order Value / Engagement Score / Preferred Category。
- 输入：Engagement / Preference / Transactional 数据。

> **自研映射**：对应 Botim 数据组 **T+1 标签清洗**；"标签可直接喂圈人"的产品形态值得保留，平台内 SQL 计算器可不做。

---

## 7. Reports（报表）🔎 菜单

### 7.1 前端
- 入口：New Campaign Report / New Alert Report；已有 Campaigns Reports / Alerts Reports。

### 7.2 后端 / 7.3 数据处理
- 活动级指标聚合（CTR/CVR/ROI）+ 告警记录。✅ 基于触达/转化日志。

> **自研映射**：报表基本不做，指标口径并入漏斗追踪(P1-5)。

---

## 8. Inform（告警）🔎 菜单
- 前端：All Alerts 列表。后端：系统/运营告警下发。数据：告警事件记录。
- 🧩 与 Engage 区分：Inform 偏运维/事务性通知，Engage 偏营销。Botim scope 内可不做。

---

## 9. 平台通用能力（跨菜单）

| 模块 | 特性 | 层 | 证据 |
|---|---|---|---|
| 顶栏 | 环境(Test)切换 / App 切换 / 通知 / Need help | 前端 | 📹 |
| Create New | 全局统一新建入口 | 前端 | 📹 |
| App Marketplace | 第三方集成市场 | 前后端 | 🧩 |
| Test and Debug | 事件/集成调试 | 前后端 | 🧩 |
| Settings | App 设置（Conversion Goal、控制组、时区等） | 全栈 | 🔎(被引用) |
| 列表通用 | 搜索/多过滤/排序/归档/空状态/Watch video | 前端 | 📹 |
| 鉴权 | Basic token + MOE-APPKEY（_DEBUG 环境后缀） | 后端 | 📹 |

---

## 10. 一页速览：菜单 × 自研优先级 × 数据可建性

| 菜单 | 我方是否做 | 优先级 | 数据可建性主结论 |
|---|---|---|---|
| **Personalize**（千人千面/下发API） | ✅ 做 | P0/P2-1 | ✅ 端内事件足够，风险最低，直接复刻 fetch API |
| **Segment**（规则引擎/RFM） | ✅ 做 | P0-1/P1-1/P1-2 | ✅ 端内事件足够；⚠️ 无 email 改主键 |
| **Engage**（编排/A·B/频控） | ✅ 做 | P0-2/P1-3/P1-7 | ✅ 触达日志足够；🟥 频控需自建 |
| **Analyze**（行为/留存） | 口径对齐，不自建 | P1-5 参考 | ✅ |
| **Data**（Computed Traits） | 归数据组 | — | ⚠️/🟥 标签清洗 |
| **Dashboards / Reports / Inform** | 基本不做 | — | 归数据组/不在 scope |
