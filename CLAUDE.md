# CLAUDE.md — Botim Growth Platform（仓库级）

自研用户增长平台（替换 MoEngage）。9 业务模块(M1–M9) + 共享契约 + 7 服务 + API 网关。详见 `ARCHITECTURE.md`、`docs/`。

## 技术栈与约定
- **Python ≥3.10**，`src/` 布局（`pyproject.toml` 设 `pythonpath=["src"]`）。
- **核心模块零三方依赖**（仅 stdlib）；可选 extras：`dev`(pytest/pytest-cov/fastapi/httpx/pyroaring)、`api`(fastapi/uvicorn)、`bitmap`(pyroaring)。
- 测试 **pytest**，遵循 **TDD**（先写测试用例再实现）。
- 每个新模块/大改动后做一次**独立 Code Review**（本项目已据此修复多个真实 bug）。

## 常用命令
```bash
pip install -e ".[dev]"
pytest -q                                   # 应 269 passed
pytest --cov=src --cov-report=term-missing  # 覆盖率 ~90%
python examples/e2e_demo.py                 # 端到端 demo
uvicorn api_gateway:app --reload            # 网关 + 挂载的 7 服务
```
**测试结果在哪看**：CI 在 GitHub **Actions** 标签页（run 的 Summary 页有 pytest 摘要，Artifacts 有 JUnit/coverage XML）。本地见上。

## 提交规范
- 无全局 git 身份 → 用一次性覆盖（**勿改全局 config**）：
  `git -c user.name="faye-rao" -c user.email="faye.rao@estidama.ai" commit ...`
- 语义化信息：`feat(M3): ...` / `fix(...)` / `docs:` / `ci:` / `test(e2e): ...`，结尾加：
  `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`
- 推送：`git push origin HEAD:main`（远端 `faye-rao/Growth`，默认分支 main）。

## 模块 ↔ 服务映射（包名）
| 服务(`src/services/`) | 模块包(`src/`) |
|---|---|
| audience | `cohort_engine` (M2) |
| campaign | `orchestration`(M3) + `messaging`(M1) |
| personalization | `personalization` (M5) |
| content | `copywriting` (M6) |
| analytics | `analytics`(M4) + `behavioral`(M9) |
| experiment | `shadow` (M7) |
| data-platform | `data_foundation` (M8) |

## 架构边界（勿破坏）
- 模块经 **`growth_common`** 契约解耦：`DeliveryRecord`(触达日志 schema)、`MessagingGateway`(协议)、`stable_fraction`/`stable_bucket`(确定性分桶，保证 A/B/控制组跨服务一致)。
- 网关(`api_gateway.py`)只做路由/鉴权(MOE-APPKEY)/限流，**不含业务逻辑**。
- 子目录有各自的 `CLAUDE.md`（`src/cohort_engine/`、`src/services/`、`frontend/`），读到时会惰性加载。

## 不变量
- **无 email** → 主键 customer_id/手机号；时区 **Asia/Dubai**；UAE ~250 万规模（M2 用 RoaringBitmap）。

## 现状（勿误当生产系统）
- **内存态 MVP**：无持久化/真实数据源(footprint/Kafka/OLAP/Redis 均为入参或合成)。
- **AI 多为桩/确定性算法**：NL2SQL=模板、自动洞察=z-score、文案=确定性模板(非真 LLM)。
- **无前端**（仅 REST API/网关）；前端计划见 `frontend/CLAUDE.md`。
- 完整度详见 `docs/Growth-实现对比报告.md`（均值 ~62%）。

## Windows 环境提示
- CRLF 警告正常（无需处理）。
- 控制台读中文/跑含中文输出：命令前加 `PYTHONIOENCODING=utf-8`。
