# M2 Cohort Rule Engine — 测试用例设计

> 对应特性见 `Growth特性清单-M2-1.md`。本 MVP 覆盖 **M2-A1~A6**（规则引擎核心），采用 TDD：先设计用例与断言，再实现。
> 测试框架：pytest。数据：内存样例数据集（`sample_data.build_sample_dataset()`，固定参考时间 `now=2026-06-02`）。

## 覆盖矩阵（特性 → 用例）

| 特性 | 能力 | 测试文件::用例 |
|---|---|---|
| **M2-A1** 规则条件构造（嵌套 AND/OR/NOT） | 多条件无穷嵌套 | `test_evaluator::test_nested_and_or_not`、`test_parser::test_parse_nested_group` |
| **M2-A3** 属性算子 | eq/ne/gt/gte/lt/lte/in/not_in/exists/between | `test_evaluator::test_attribute_operators[*]` |
| **M2-A3** 频次算子 | at_least/at_most/exactly/min_percent/predominantly | `test_evaluator::test_frequency_*` |
| **M2-A2** 时间窗算子 | last N days | `test_evaluator::test_time_window_filters_old_events` |
| 时间维度条件 | hour_of_day / month_of_year（事件时间派生） | `test_evaluator::test_event_time_dimension_where` |
| **M2-A4** 排除人群 | exclude 子树 | `test_evaluator::test_exclude_users` |
| **M2-A1** 事件属性条件（event.where） | 事件属性过滤 + 频次 | `test_evaluator::test_event_where_property` |
| **M2-A5** 批量求值 | 返回命中 customer_id 集合 | `test_engine::test_evaluate_returns_ids` |
| **M2-A6** 人群规模预估 | estimate_size = 命中数 | `test_engine::test_estimate_size` |
| **M2-A7** 兼容语法层（JSON DSL 解析/校验） | 合法解析、非法报错 | `test_parser::test_*` |
| 编译到 SQL（方案B） | DSL→SQL / COUNT SQL | `test_sql_compiler::test_*` |

## 关键语义约定（断言依据）

- **频次 occurrences**：事件名匹配且 `ts` 落在 `[now - within_days, now]` 内的事件；若有 `where`，先按 `where` 过滤得 `matching`，否则 `matching = 全部窗口内事件`。
  - `at_least N`：`len(matching) >= N`
  - `at_most N`：`len(matching) <= N`
  - `exactly N`：`len(matching) == N`
  - `min_percent X`：`total = 窗口内该事件总数`；`total>0` 且 `len(matching)/total*100 >= X`
  - `predominantly`：`total>0` 且 `len(matching)/total > 0.5`
- **NOT 组**：对子节点合并结果取逻辑非（"未执行/不满足"）。
- **exclude**：命中 `match` 但同时命中 `exclude` 的用户被剔除。
- **时间维度 where 字段**：`hour_of_day`(0-23)、`month_of_year`(1-12)、`day_of_week`(0=Mon) 由事件 `ts` 派生，可与事件属性混用。

## 样例数据集（节选）
- 用户 u1：is_kyc=true, wallet_activated=false, balance=5000, country=AE, device_height=5
- 用户 u2：is_kyc=true, wallet_activated=true, balance=200, country=IN
- 用户 u3：is_kyc=false, balance=0, country=PH
- 事件：User Logout / Push ID Register Android / App Opened / Transfer，带 ts 与属性（device_height、hour 等）
- 设计若干"近 3 天"与"很久以前"的事件以验证时间窗。

## 验收标准
- 全部 pytest 用例通过（绿）。
- `examples/demo.py` 跑出 3 个真实业务分群（高价值未激活钱包 / 频繁登出设备异常 / KYC 未转账）的命中名单、规模预估与等价 SQL。
