# CLAUDE.md — cohort_engine (M2 Cohort Segmentation)

圈人引擎：复刻 MoEngage 第①步圈人 + 叠加 AI。被 audience 服务、M5(命中)、M3(分流)、M7(切流) 复用。

## 结构与契约
- `models.py` — 规则 AST（`Segment`/`Group`/`AttributeCondition`/`EventCondition`/`Frequency`）。**JSON DSL 是对外契约**，前端规则构造器须与之 1:1 双向映射。
- `parser.py` — `parse_segment(dict)`，含校验（`RuleParseError`）。这是"兼容语法层"入口。
- **三套执行引擎**（同一 DSL，按场景选）：
  - `evaluator.py` — 解释执行（内存逐用户，灵活，适合实时/小集）。
  - `sql_compiler.py` — 编译到 SQL（下推 OLAP，适合批量；ANSI-ish/ClickHouse 风格）。
  - `bitmap_engine.py` — RoaringBitmap 倒排（250 万级交并差秒级 + O(1) 人数预估）。需 `pyroaring`。
- `engine.py` — `CohortEngine` facade（evaluate / estimate_size / compile_sql）。
- `nl2sql.py` — **确定性模板/槽位**翻译（**非 LLM**）：`translate()` 返回 `{dsl, confidence, requires_review}`，含兜底转人工。
- `templates.py` — 5 个高频 Cohort 模板。
- `api.py` — FastAPI（/segments/evaluate|size|compile、/nl2sql、/templates）。
- `sample_data.py` — 确定性样例数据（`NOW=2026-06-02`），测试与 demo 共用。

## 频次语义（务必一致）
窗口内事件数为分母；`where` 过滤后为 matching。at_least/at_most/exactly 比 matching；min_percent = matching/total*100 ≥X(total>0)；predominantly = matching/total>0.5。

## 已实现 vs 未实现（勿过度假设）
- ✅ A1–A4 规则 + 时间窗/频次/排除、三引擎、NL2SQL(模板)、模板库、SQL 编译、人数预估。
- ⬜ C 系列 AI（Lookalike/倾向分群/AI 建议/算法优化）、近实时分群(A8)、Cohort 持久化/版本(D1/D3)、真 LLM NL2SQL。详见 `docs/Growth-实现对比报告.md` §2。

## 改动须知
- 改 DSL/算子要**同时改三处**（evaluator + sql_compiler + 测试），并保持 evaluator 与 SQL 语义一致（历史 bug 多源于二者不一致）。
- 改完 `pytest tests/test_evaluator.py tests/test_parser.py tests/test_sql_compiler.py tests/test_nl2sql.py tests/test_bitmap_engine.py`。
