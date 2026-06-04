# CLAUDE.md — services + API gateway

把 9 模块按功能独立性暴露为 **7 个独立服务**（非单体）+ 一个薄网关。详见仓库根 `ARCHITECTURE.md`。

## 结构
- 每个 `services/<name>.py` 暴露模块级 `app = FastAPI(...)`，**可独立部署/运行**（`uvicorn services.audience:app`）。
- `services/__init__.py` — `SERVICES` 注册表：`name -> (prefix, app)`。
- `services/_world.py` — **demo 用内存数据世界**（与 `examples/e2e_demo` 一致，对 M2 圈人与 M1 可达性都成立）。**生产应替换为 warehouse/OLAP-backed 注入**。
- `../api_gateway.py` — **薄边缘**：仅路由(按前缀挂载服务) + 鉴权(`MOE-APPKEY`→401) + 限流(每-key 令牌桶→429) + `/health`。**严禁放业务逻辑**。生产用反向代理(Envoy/Kong)，仓内 mount 仅为可运行 demo。

## 7 服务 ↔ 模块 ↔ 前缀
data-platform(M8,`/api/data`) · audience(M2,`/api/audience`) · personalization(M5,`/api/personalize`) · campaign(M3+M1,`/api/campaign`) · content(M6,`/api/content`) · analytics(M4+M9,`/api/analytics`) · experiment(M7,`/api/experiment`)

## 约定
- 服务保持**薄**：只 re-wrap 模块公共 API + 把领域异常(如 `RuleParseError`)转 4xx。
- 新增端点要在 `tests/test_services_gateway.py` 加用例（各服务独立 TestClient + 网关鉴权/限流/路由）。
- 加服务：实现 `<name>.py` 的 `app` → 注册进 `SERVICES` → 网关自动挂载。

## 未来（生产化）
依赖注入 warehouse/OLAP-backed 实现替换 `_world`；补登录换 token、CORS、OpenAPI 导出（前端依赖）。
