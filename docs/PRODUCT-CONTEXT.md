# Product Context — Botim Growth Platform（产品级上下文）

> 本文是工作区产品级 `CLAUDE.md` 的**仓库内镜像**（便于随仓库分发给同事/CI）。
> 工作区原件 `C:\Faye\Growth\CLAUDE.md` 因父目录非 git 仓库不随仓库推送，故镜像于此。
> 代码级约定见仓库根 `CLAUDE.md` 与各子目录 `CLAUDE.md`；架构见 `ARCHITECTURE.md`。

## 项目背景
为 **Botim**（迪拜，UAE 上线，目标用户 ≈ 阿联酋人口 1/4 ≈ **250 万**）自研用户增长平台，**替换竞品 MoEngage**。范围来自访谈 survey（`用增问题survey-updated v3.xlsx`）。

## 范围（survey 结论）
- **我方做**：触达执行(M1)、圈人(M2)、编排(M3)、漏斗追踪(M4)、千人千面(M5)、AI文案(M6)、Shadow验证(M7)、数据底座(M8)、行为分析降配(M9)。
- **不做**：Dashboard/全量 BI（数据组马老板重建 + 产品侧已有 Amplitude）。
- **增量靠 AI**；优先级最高 = 触达(Push+In-App)，其次圈人。

## 关键不变量（贯穿所有模块）
- **无 email** → 用户主键 = `customer_id` / 手机号。
- 时区统一 **Asia/Dubai (UTC+4，无 DST)**。
- "数字要对得上"是替换前提；口径(转化/活跃/留存)需先与 Growth/数据组对齐。

## 文档索引（仓库 docs/）
- 需求：`Growth特性清单-M1-1.md`…`M9-1.md`(中) / `Growth-Feature-List-M*.md`(英) / `Growth特性清单-总览索引.md`
- 技术方案：`Growth技术方案-M1-M3/M4-M6/M7-M9.md`(中) / `Growth-Tech-Solutions-*.md`(英)
- 综合分析：`Botim增长平台_基于Survey的重新分析.md`、`MoEngage特性清单_按菜单维度.md`、`MoEngage视频特性拆解_前端后端数据.md`
- 实现/交接：`Growth-实现对比报告.md`(及英 `Growth-Implementation-Audit.md`)、`Growth-交接清单.md`/`Growth-Handover.md`、`Growth-工作报告.md`/`Growth-Work-Report.md`
- 架构/测试：`../ARCHITECTURE.md`、`TEST-REPORT.md`

## 关键依赖（多为"待确认"，开工前先关闭）
数据组(马老板): OLAP 选型/ID-Mapping/清洗/样本 ｜ Growth(Radhika): Cohort/报表清单/频次/Shadow 场景 ｜ 裴青: schema/样本 ｜ MoEngage 厂商: 触达流水。
