# AGENTS.md — Hummingbot API

> AI 协作文档，描述项目结构、技术栈与开发规范。
> 由 `update-agents` 技能生成，更新请运行 `/update-agents`。
> **最后更新**：2026-05-03

---

## 目录

- [1. 开发规范](#1-开发规范)
- [2. 项目概览](#2-项目概览)
- [3. 架构说明](#3-架构说明)
- [4. 代码模块索引](#4-代码模块索引)
- [5. 数据库规范](#5-数据库规范)
- [6. API 设计规范](#6-api-设计规范)
- [7. 文档索引](#7-文档索引)
- [8. 开发命令](#8-开发命令)
- [9. 安全规范](#9-安全规范)
- [10. 快速上手](#10-快速上手)

---

## 1. 开发规范
<!-- maintained-by: update-agents -->

<!-- [TEMPLATE] -->
> DDD + TDD，先文档后代码，80% 覆盖率卡点。新功能/修改须通过单元、集成、接口三类测试，未通过不得合并。
<!-- [/TEMPLATE] -->

<!-- [DYNAMIC:update-agents] -->
_由 `/update-agents` 自动维护，请勿手动编辑_
<!-- [/DYNAMIC:update-agents] -->

<!-- [INDEX] -->
- [完整开发规范](docs/standards/dev-workflow.md)
<!-- [/INDEX] -->

---

## 2. 项目概览

**项目名称**：Hummingbot API
**类型**：后端服务 / API 服务
**语言 / 框架**：Python 3.12 / FastAPI / SQLAlchemy / asyncpg / Docker

### 核心功能

| 功能 | 说明 |
|------|------|
| 统一连接器管理 | 通过 UnifiedConnectorService 管理 CEX/DEX 交易与数据连接器 |
| 执行器引擎 | 8 种执行器类型（position/grid/dca/twap/arbitrage/xemm/order/lp） |
| Gateway DEX 集成 | Swap 报价/执行、CLMM 持仓管理、链上交易轮询确认 |
| Bot 编排 | MQTT + Docker 编排 Hummingbot 实例的启动/停止/状态 |
| 实时推送 | WebSocket 推送行情数据与执行器状态 |
| 数据归档 | Bot 数据归档（本地 tar.gz / S3），SQLite 数据库读取 |

---

## 3. 架构说明

### 技术栈

- **语言**：Python 3.8+
- **框架**：FastAPI（异步 ASGI）
- **ORM**：SQLAlchemy（声明式 Base，异步 AsyncDatabaseManager）
- **数据库**：PostgreSQL 16（asyncpg 驱动）
- **配置管理**：Pydantic Settings（环境变量 + .env 文件）
- **消息代理**：EMQX 5（MQTT 协议，Bot 编排通信）
- **容器化**：Docker / Docker Compose
- **可观测性**：Logfire（FastAPI 自动埋点）
- **代码质量**：Black + isort + pre-commit

### 项目结构

```
hummingbot-api/
├── main.py                 # FastAPI 入口，lifespan 管理，路由注册
├── config.py               # Pydantic Settings 配置（分模块）
├── deps.py                 # FastAPI 依赖注入
├── database/
│   ├── models.py           # SQLAlchemy ORM 模型
│   └── __init__.py         # AsyncDatabaseManager
├── models/                 # Pydantic 请求/响应模型
├── routers/                # FastAPI 路由（按业务域拆分）
│   ├── accounts.py
│   ├── backtesting.py
│   ├── bot_orchestration.py
│   ├── connectors.py
│   ├── controllers.py
│   ├── docker.py
│   ├── executors.py
│   ├── gateway.py
│   ├── gateway_clmm.py
│   ├── gateway_swap.py
│   ├── market_data.py
│   ├── portfolio.py
│   ├── rate_oracle.py
│   ├── scripts.py
│   ├── trading.py
│   └── websocket.py
├── services/               # 业务服务层
│   ├── accounts_service.py
│   ├── backtesting_service.py
│   ├── bots_orchestrator.py
│   ├── docker_service.py
│   ├── executor_service.py
│   ├── executor_ws_manager.py
│   ├── funding_recorder.py
│   ├── gateway_client.py
│   ├── gateway_service.py
│   ├── gateway_transaction_poller.py
│   ├── market_data_service.py
│   ├── orders_recorder.py
│   ├── trading_service.py
│   ├── unified_connector_service.py
│   └── websocket_manager.py
├── bots/                   # Bot 配置与控制器
├── utils/                  # 工具函数
│   ├── bot_archiver.py
│   ├── executor_log_capture.py
│   ├── file_system.py
│   ├── hummingbot_api_config_adapter.py
│   ├── hummingbot_database_reader.py
│   ├── mqtt_manager.py
│   └── security.py
├── test/                   # 测试目录
├── docker-compose.yml      # Docker Compose 编排
├── Dockerfile
├── Makefile
├── environment.yml         # Conda 环境定义
├── pyproject.toml          # 项目元数据与工具配置
└── init-db.sql             # 数据库初始化 SQL
```

### 服务架构

FastAPI 单体应用，lifespan 管理服务生命周期。核心依赖链：

```
请求 → FastAPI Router → Service → Connector / DB → 响应
                              ↓
                    UnifiedConnectorService（连接器统一入口）
                              ↓
              MarketDataService / TradingService / AccountsService
                              ↓
                    ExecutorService → ExecutorWebSocketManager
                              ↓
                    BotsOrchestrator（MQTT 通信）
```

> 核心链路：HTTP 请求 → FastAPI Router（HTTP Basic Auth 鉴权）→ Service 层 → UnifiedConnectorService（CEX/DEX 统一入口）→ Hummingbot SDK 连接器 / PostgreSQL → JSON 响应。WebSocket 连接通过 WebSocketManager/ExecutorWebSocketManager 订阅行情与执行器状态，增量推送避免重复。Bot 编排链路：API → BotsOrchestrator → Docker API（容器生命周期）+ MQTT（消息通信）→ Hummingbot 实例。

### 数据存储

**数据库类型**：PostgreSQL 16
**ORM / 驱动**：SQLAlchemy（声明式）+ asyncpg
**迁移工具**：自定义（`AsyncDatabaseManager.create_tables()`，无 Alembic）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| account_states / token_states | 账户状态快照与代币持仓 | account_name, connector_name, token, units, value |
| orders / trades | 交易订单与成交记录 | client_order_id, trading_pair, trade_type, status |
| executors / executor_orders / position_holds | 执行器状态、关联订单、持仓追踪 | executor_id, executor_type, controller_id, net_pnl_quote |
| gateway_swaps | 链上 DEX 兑换记录 | transaction_hash, network, connector, input/output_amount |
| gateway_clmm_positions / gateway_clmm_events | CLMM 集中流动性仓位与事件 | position_address, pool_address, in_range, event_type |
| bot_runs | Bot 运行记录 | bot_name, strategy_type, deployment_status, run_status |
| position_snapshots / funding_payments | 合约持仓快照与资金费 | side, unrealized_pnl, leverage, funding_rate |

---

## 4. 代码模块索引
<!-- maintained-by: update-module-docs -->

<!-- [TEMPLATE] -->
> 路由/服务/模型/中间件/工具函数索引，供 AI 快速定位代码位置与职责边界。
<!-- [/TEMPLATE] -->

<!-- [DYNAMIC:update-module-docs] -->
Hummingbot API 是 Python/FastAPI 后端，包含 17 个 REST 路由、15 个业务服务、8 种执行器类型、Gateway DEX 集成（Swap/CLMM），通过 UnifiedConnectorService 统一管理 CEX/DEX 连接器，支持 WebSocket 实时推送。

| 模块 | 核心类 | 职责 |
|------|--------|------|
| `main.py` | `FastAPI app` | 入口+生命周期（9 步初始化顺序） |
| `services/unified_connector_service.py` | `UnifiedConnectorService` | 连接器唯一真实来源（交易/数据分离） |
| `services/executor_service.py` | `ExecutorService` | 8 种执行器生命周期（position/grid/dca/twap/arbitrage/xemm/order/lp） |
| `services/bots_orchestrator.py` | `BotsOrchestrator` | MQTT+Docker Bot 编排 |
| `services/gateway_client.py` | `GatewayClient` | DEX Swap/CLMM HTTP 客户端 |

详见 docs/codemaps/module-index.md
<!-- [/DYNAMIC:update-module-docs] -->

<!-- [INDEX] -->
- [模块索引详情](docs/codemaps/module-index.md)
<!-- [/INDEX] -->

---

## 5. 数据库规范
<!-- maintained-by: update-db-docs -->

<!-- [TEMPLATE] -->
> snake_case 命名，必备字段(id/created_at/updated_at/enabled)，软删除用 enabled=0，禁止物理 DELETE，所有 SQL 参数化。
<!-- [/TEMPLATE] -->

<!-- [DYNAMIC:update-db-docs] -->
PostgreSQL 16，13 张表，4 组关系。核心表：account_states/token_states（账户快照）、orders/trades（交易订单）、executors/executor_orders/position_holds（执行器与持仓）、gateway_swaps/gateway_clmm_positions/gateway_clmm_events（链上兑换与 CLMM 做市）、bot_runs（Bot 运行记录）、position_snapshots/funding_payments（合约持仓与资金费）。详见 docs/codemaps/db-schema.md
<!-- [/DYNAMIC:update-db-docs] -->

<!-- [INDEX] -->
- [数据库规范](docs/standards/db-conventions.md)
- [数据库 Schema](docs/codemaps/db-schema.md)
<!-- [/INDEX] -->

---

## 6. API 设计规范
<!-- maintained-by: update-api-docs -->

<!-- [TEMPLATE] -->
> RESTful，统一响应 {code,message,data}，错误码 40001-50099，分页用 page/pageSize，所有接口参数化防注入。
<!-- [/TEMPLATE] -->

<!-- [DYNAMIC:update-api-docs] -->
17 个路由模块，覆盖账户管理、交易下单、执行器控制、Docker 容器管理、Gateway（链上兑换/CLMM 做市/连接器配置）、市场数据、回测、Bot 编排、WebSocket 实时推送等。认证方式：HTTP Basic Auth（WebSocket 除外）。详见 docs/codemaps/api-endpoints.md
<!-- [/DYNAMIC:update-api-docs] -->

<!-- [INDEX] -->
- [API 设计规范](docs/standards/api-conventions.md)
- [API 端点列表](docs/codemaps/api-endpoints.md)
<!-- [/INDEX] -->

---

## 7. 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 代码模块索引 | docs/codemaps/module-index.md | 路由/服务/模型/数据库/工具完整索引 |
| 数据库 Schema | docs/codemaps/db-schema.md | 数据库表结构文档 |
| API 端点列表 | docs/codemaps/api-endpoints.md | API 端点快查表 |
| 开发规范 | docs/standards/dev-workflow.md | 编码/测试/部署规范 |
| 数据库规范 | docs/standards/db-conventions.md | 数据库设计约定 |
| API 设计规范 | docs/standards/api-conventions.md | API 设计约定 |
| 安全规范 | docs/standards/security-checklist.md | 安全审查清单 |
| README | README.md | 项目说明 |
| Docker Compose | docker-compose.yml | 服务编排定义 |
| 数据库初始化 | init-db.sql | PostgreSQL 初始化脚本 |

---

## 8. 开发命令

```bash
# 安装依赖（Conda 环境）
make install

# 开发（热重载）
make run
# 等效: docker compose up emqx postgres -d && conda run --no-capture-output -n hummingbot-api uvicorn main:app --reload

# 构建 Docker 镜像
make build

# 生产部署（Docker Compose）
make deploy

# 停止所有服务
make stop

# 测试
poetry run pytest           # 运行所有测试

# 数据库（如有）
# 无独立迁移命令，由 AsyncDatabaseManager.create_tables() 自动建表
```

**环境变量**（复制 `.env` 并填写）：

```
# 安全
SECURITY_USERNAME=admin
SECURITY_PASSWORD=admin
SECURITY_DEBUG_MODE=false
SECURITY_CONFIG_PASSWORD=a

# 数据库
DATABASE_URL=postgresql+asyncpg://hbot:hummingbot-api@localhost:5432/hummingbot_api

# MQTT Broker
BROKER_HOST=localhost
BROKER_PORT=1883
BROKER_USERNAME=admin
BROKER_PASSWORD=password

# Gateway
GATEWAY_URL=http://localhost:15888

# AWS（Bot 归档）
AWS_API_KEY=
AWS_SECRET_KEY=
AWS_S3_DEFAULT_BUCKET_NAME=

# 应用
APP_LOGFIRE_ENVIRONMENT=dev
APP_ACCOUNT_UPDATE_INTERVAL=5
```

---

## 9. 安全规范
<!-- maintained-by: update-agents -->

<!-- [TEMPLATE] -->
> 提交前检查：无硬编码密钥、参数化 SQL、XSS 防护、限流。发现 CRITICAL/HIGH 问题立即停止并修复。
<!-- [/TEMPLATE] -->

<!-- [DYNAMIC:update-agents] -->
_由 `/update-agents` 自动维护，请勿手动编辑_
<!-- [/DYNAMIC:update-agents] -->

<!-- [INDEX] -->
- [安全规范清单](docs/standards/security-checklist.md)
<!-- [/INDEX] -->

---

## 10. 快速上手

```bash
# 1. 安装 Conda 环境
make install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写必要配置

# 3. 启动基础设施（PostgreSQL + EMQX）
docker compose up emqx postgres -d

# 4. 启动开发服务
make run
```

## 重要实现细节

- **认证/鉴权**：HTTP Basic Auth，所有 REST 路由通过 `Depends(auth_user)` 保护；WebSocket 路由自行处理认证。`BackendAPISecurity` 继承 Hummingbot `Security` 类，支持密码验证文件（`ETHKeyFileSecretManger` 加密存储）和 `debug_mode` 跳过认证。登录时解密 `credentials/{account}/connectors/` 下所有加密 yml 文件
- **Hummingbot 集成**：monkey patch `config_helpers.save_to_yml` 防止 API 模式下写入库目录；通过 `HummingbotAPIConfigAdapter`（非原生 `ClientConfigAdapter`）加载连接器配置
- **Gateway 集成**：`GatewayClient` 封装异步 HTTP 客户端（aiohttp），连接 Hummingbot Gateway 服务（默认 `localhost:15888`）；`GatewayTransactionPoller` 双重轮询机制 — 交易确认 10s 间隔、CLMM 头寸同步 300s 间隔，超时 1h 停止重试
- **MQTT 通信**：`BotsOrchestrator` 双通道编排 — Docker API 管理容器生命周期 + MQTT 消息通信控制 Bot 实例；`MQTTManager` 承担原 `HummingbotPerformanceListener` 的全部功能
- **WebSocket**：双管理器设计 — `WebSocketManager` 处理行情订阅（candles/order_book/trades），增量推送（last_sent_candle_ts/last_sent_ob_uid 去重）；`ExecutorWebSocketManager` 处理执行器实时数据（8 种订阅类型），跨服务聚合（ExecutorService + MarketDataService + BotsOrchestrator）
- **依赖注入**：`deps.py` 提供 13 个 `get_xxx_service` 函数，从 `app.state` 获取服务实例，路由通过 `Depends` 注入，实现松耦合
- **部署**：Docker Compose 三容器编排（API + EMQX 5 + PostgreSQL 16）；Dockerfile 多阶段构建（miniconda3 builder + runtime）；setup.sh 支持 Linux/macOS/WSL2，交互式生成 .env
- **环境差异**：Docker 内 `BROKER_HOST=emqx`、`DATABASE_URL` 指向 postgres 容器、`GATEWAY_URL=http://host.docker.internal:15888`；本地开发直接 localhost
