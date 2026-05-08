# Hummingbot API — 跨交易所交易机器人管理平台

> 一站式 REST API，管理 Hummingbot 交易机器人的账户、交易、执行器、Bot 编排和 DEX 操作

## 目录

- [一、这是什么（30 秒速览）](#一这是什么30-秒速览)
- [二、快速开始（10 分钟可运行）](#二快速开始10-分钟可运行)
- [三、核心使用](#三核心使用)
- [四、配置说明](#四配置说明)
- [五、进阶使用](#五进阶使用)
- [六、开发者指南](#六开发者指南)
- [附录 A：常见问题 & 错误排查](#附录-a常见问题--错误排查)
- [附录 B：术语表](#附录-b术语表)

---

## 一、这是什么（30 秒速览）

**Hummingbot API** 是 [Hummingbot](https://hummingbot.org) 生态的后端服务，提供 RESTful API 管理跨多个 CEX/DEX 的交易机器人。它将 Hummingbot 客户端的核心能力（连接器、执行器、策略）封装为 HTTP 接口，支持通过 API、AI 助手（MCP）或 Dashboard 集中控制。

### 核心功能

- **多交易所账户管理** — 统一管理 CEX（Binance、OKX 等）和 DEX（通过 Gateway）的 API 密钥与钱包
- **交易执行与监控** — 下单、撤单、持仓跟踪、资金费率查询，覆盖现货与合约
- **8 种执行器类型** — position / grid / dca / twap / arbitrage / xemm / order / lp，支持复杂策略组合
- **Bot 编排** — 通过 MQTT + Docker 编排多个 Hummingbot 实例的启动/停止/状态监控
- **Gateway DEX 集成** — Swap 报价/执行、CLMM 集中流动性做市、链上交易轮询确认
- **实时推送** — WebSocket 推送行情数据（K 线/订单簿/成交）与执行器状态

### 适合谁

| 适合 | 不适合 |
|------|--------|
| 需要集中管理多个交易机器人的量化团队 | 只想在单一交易所跑简单策略的个人用户 |
| 构建交易 Dashboard 或 AI 交易助手的开发者 | 不需要 API 的 Hummingbot 命令行用户 |
| 需要跨 CEX/DEX 统一交易接口的项目 | 纯现货买卖、无需自动化策略的用户 |

---

## 二、快速开始（10 分钟可运行）

### 前置条件

| 依赖 | 版本要求 | 检查命令 |
|------|---------|---------|
| Docker | 20+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Git | 任意 | `git --version` |

### Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/hummingbot/hummingbot-api.git
cd hummingbot-api

# 2. 交互式配置（生成 .env 文件）
make setup

# 3. 启动所有服务
make deploy
```

启动后可访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| API | http://localhost:8000 | REST API |
| Swagger UI | http://localhost:8000/docs | 交互式 API 文档 |
| EMQX Dashboard | http://localhost:18083 | MQTT 管理面板（admin/public） |

### 源码开发模式

```bash
# 1. 安装 Conda 环境
make install

# 2. 启动基础设施
docker compose up emqx postgres -d

# 3. 激活环境并启动（热重载）
conda activate hummingbot-api
uvicorn main:app --reload
```

### 验证运行

```bash
# 检查 API 状态
curl http://localhost:8000/

# 预期返回
# {"name":"Hummingbot API","version":"1.0.1","status":"running"}

# 查看所有服务
docker ps | grep hummingbot
```

---

## 三、核心使用

所有 REST 端点使用 HTTP Basic Auth 认证（用户名/密码在 `.env` 中配置）。

### 3.1 账户管理

管理交易所 API 密钥和 Gateway 钱包。

```bash
# 列出所有账户
curl -u admin:admin http://localhost:8000/accounts/

# 添加 Binance 凭证
curl -u admin:admin -X POST \
  http://localhost:8000/accounts/add-credential/master_account/binance \
  -H "Content-Type: application/json" \
  -d '{"api_key": "xxx", "secret": "xxx"}'

# 列出 Gateway 钱包
curl -u admin:admin http://localhost:8000/accounts/gateway/wallets
```

### 3.2 交易操作

下单、撤单、查询持仓和成交。

```bash
# 下单（市价买入 0.01 BTC-USDT）
curl -u admin:admin -X POST http://localhost:8000/trading/orders \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "binance",
    "trading_pair": "BTC-USDT",
    "trade_type": "BUY",
    "order_type": "MARKET",
    "amount": "0.01"
  }'

# 查询活跃订单
curl -u admin:admin -X POST http://localhost:8000/trading/orders/active \
  -H "Content-Type: application/json" \
  -d '{"connector_name": "binance"}'

# 查询持仓
curl -u admin:admin -X POST http://localhost:8000/trading/positions \
  -H "Content-Type: application/json" \
  -d '{"connector_name": "binance_perpetual"}'
```

### 3.3 执行器

8 种执行器类型，每种对应不同的交易策略逻辑：

| 执行器类型 | 用途 | 典型场景 |
|-----------|------|---------|
| `position_executor` | 单向持仓管理 | 方向性交易（做多/做空） |
| `grid_executor` | 网格交易 | 震荡行情中高抛低吸 |
| `dca_executor` | 定投/分批建仓 | 逐步建仓降低均价 |
| `twap_executor` | 时间加权执行 | 大额订单拆分减少冲击 |
| `arbitrage_executor` | 跨所套利 | 同币种不同交易所价差 |
| `xemm_executor` | 跨交易所做市 | 挂单所吃单所对冲 |
| `order_executor` | 单笔订单 | 简单下单 |
| `lp_executor` | 流动性提供 | DEX 做市 |

```bash
# 创建执行器
curl -u admin:admin -X POST http://localhost:8000/executors/ \
  -H "Content-Type: application/json" \
  -d '{
    "executor_type": "position_executor",
    "connector_name": "binance",
    "trading_pair": "BTC-USDT",
    "side": "BUY",
    "entry_price": "50000",
    "amount": "0.01",
    "leverage": 1
  }'

# 查看执行器汇总
curl -u admin:admin http://localhost:8000/executors/summary

# 停止执行器
curl -u admin:admin -X POST http://localhost:8000/executors/{executor_id}/stop
```

### 3.4 Bot 编排

通过 MQTT + Docker 管理多个 Hummingbot 实例。

```bash
# 查看所有 Bot 状态
curl -u admin:admin http://localhost:8000/bot-orchestration/status

# 启动 Bot
curl -u admin:admin -X POST http://localhost:8000/bot-orchestration/start-bot \
  -H "Content-Type: application/json" \
  -d '{
    "bot_name": "my-market-maker",
    "image": "hummingbot/hummingbot:latest",
    "strategy": "v2_with_controllers"
  }'

# 停止并归档 Bot
curl -u admin:admin -X POST \
  http://localhost:8000/bot-orchestration/stop-and-archive-bot/my-market-maker
```

### 3.5 Gateway（DEX 操作）

Gateway 是连接 DEX 的中间件，支持 Swap 和 CLMM 做市。

```bash
# 检查 Gateway 状态
curl -u admin:admin http://localhost:8000/gateway/status

# 获取 Swap 报价
curl -u admin:admin -X POST http://localhost:8000/gateway/swap/quote \
  -H "Content-Type: application/json" \
  -d '{
    "network": "ethereum",
    "connector": "uniswap",
    "from_token": "ETH",
    "to_token": "USDT",
    "amount": "1.0"
  }'

# 开仓 CLMM 头寸
curl -u admin:admin -X POST http://localhost:8000/gateway/clmm/open \
  -H "Content-Type: application/json" \
  -d '{
    "network": "solana",
    "connector": "raydium_clmm",
    "pool_address": "xxx",
    "amount_a": "1.0",
    "amount_b": "1000"
  }'
```

### 3.6 行情数据

获取 K 线、订单簿、价格等市场数据。

```bash
# 获取 K 线
curl -u admin:admin -X POST http://localhost:8000/market-data/candles \
  -H "Content-Type: application/json" \
  -d '{"connector": "binance", "trading_pair": "BTC-USDT", "interval": "1m"}'

# 获取订单簿
curl -u admin:admin -X POST http://localhost:8000/market-data/order-book \
  -H "Content-Type: application/json" \
  -d '{"connector": "binance", "trading_pair": "BTC-USDT"}'

# 获取当前价格
curl -u admin:admin -X POST http://localhost:8000/market-data/prices \
  -H "Content-Type: application/json" \
  -d '{"connector": "binance", "trading_pairs": ["BTC-USDT", "ETH-USDT"]}'
```

---

## 四、配置说明

### 环境变量

所有配置通过 `.env` 文件管理，由 `make setup` 交互式生成。

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|:----:|
| `SECURITY_USERNAME` | API 认证用户名 | `admin` | 是 |
| `SECURITY_PASSWORD` | API 认证密码 | `admin` | 是 |
| `SECURITY_DEBUG_MODE` | 调试模式（跳过认证） | `false` | 否 |
| `SECURITY_CONFIG_PASSWORD` | Bot 凭证加密密码 | `a` | 是 |
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://hbot:hummingbot-api@localhost:5432/hummingbot_api` | 是 |
| `BROKER_HOST` | MQTT Broker 地址 | `localhost` | 是 |
| `BROKER_PORT` | MQTT Broker 端口 | `1883` | 否 |
| `BROKER_USERNAME` | MQTT 用户名 | `admin` | 否 |
| `BROKER_PASSWORD` | MQTT 密码 | `password` | 否 |
| `GATEWAY_URL` | Gateway 服务地址 | `http://localhost:15888` | 否 |
| `AWS_API_KEY` | AWS API Key（S3 归档） | 空 | 否 |
| `AWS_SECRET_KEY` | AWS Secret Key | 空 | 否 |
| `AWS_S3_DEFAULT_BUCKET_NAME` | S3 存储桶名 | 空 | 否 |
| `APP_LOGFIRE_ENVIRONMENT` | Logfire 环境标签 | `dev` | 否 |
| `APP_ACCOUNT_UPDATE_INTERVAL` | 账户状态更新间隔（分钟） | `5` | 否 |
| `MARKET_DATA_CLEANUP_INTERVAL` | 行情数据清理间隔（秒） | `300` | 否 |
| `MARKET_DATA_FEED_TIMEOUT` | 空闲行情源超时（秒） | `600` | 否 |
| `MARKET_DATA_CANDLES_READY_TIMEOUT` | K 线就绪等待时间（秒） | `30` | 否 |

### Docker 环境差异

Docker Compose 会自动覆盖以下变量：

| 变量 | 本地开发 | Docker 部署 |
|------|---------|------------|
| `BROKER_HOST` | `localhost` | `emqx` |
| `DATABASE_URL` | `localhost:5432` | `postgres:5432` |
| `GATEWAY_URL` | `http://localhost:15888` | `http://host.docker.internal:15888` |

### 配置文件结构

```
hummingbot-api/
├── .env                          # 环境变量（主配置）
├── credentials/
│   └── master_account/
│       ├── .password_verification # 密码验证文件
│       ├── conf_client.yml       # 客户端配置（RateOracle 等）
│       └── connectors/           # 加密的交易所凭证
├── bots/
│   ├── conf/controllers/         # 控制器配置文件
│   ├── controllers/              # 控制器实现代码
│   ├── scripts/                  # 策略脚本
│   ├── instances/                # Bot 实例数据
│   └── archived/                 # 归档数据
```

---

## 五、进阶使用

### 5.1 WebSocket 实时推送

两个 WebSocket 端点，支持订阅式数据推送：

**行情数据** `/ws/market-data`

```json
// 订阅 K 线
{"action": "subscribe", "type": "candles", "connector": "binance", "trading_pair": "BTC-USDT", "interval": "1m", "update_interval": 2}

// 订阅订单簿
{"action": "subscribe", "type": "order_book", "connector": "binance", "trading_pair": "BTC-USDT", "depth": 20}

// 取消订阅
{"action": "unsubscribe", "subscription_id": "xxx"}

// 心跳
{"action": "ping"}
```

**执行器状态** `/ws/executors`

订阅类型：`executors` / `executor_detail` / `executor_summary` / `performance` / `positions` / `executor_logs` / `bot_status` / `all_bots_status`

认证方式：Basic Auth（`Authorization` 头 / `?token=base64(user:pass)` / `?username=&password=`）

### 5.2 AI 助手集成（MCP）

通过 MCP 协议让 Claude 等 AI 助手控制交易：

```bash
# Claude Code 集成
claude mcp add --transport stdio hummingbot -- \
  docker run --rm -i \
  -e HUMMINGBOT_API_URL=http://host.docker.internal:8000 \
  -v hummingbot_mcp:/root/.hummingbot_mcp \
  hummingbot/hummingbot-mcp:latest
```

集成后可用自然语言操作：
- "Show my portfolio balances"
- "Create a market making strategy for ETH-USDT"
- "Start Gateway in development mode"

### 5.3 回测

```bash
# 同步回测
curl -u admin:admin -X POST http://localhost:8000/backtesting/run \
  -H "Content-Type: application/json" \
  -d '{"strategy": "pmm_simple", "trading_pair": "BTC-USDT", "start_date": "2024-01-01", "end_date": "2024-03-01"}'

# 后台回测任务
curl -u admin:admin -X POST http://localhost:8000/backtesting/tasks \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 5.4 Bot 数据归档

支持本地 tar.gz 和 AWS S3 两种归档方式。停止并归档 Bot 时自动触发：

```bash
curl -u admin:admin -X POST \
  http://localhost:8000/bot-orchestration/stop-and-archive-bot/{bot_name}
```

归档后可通过 `/archived-bots/` 端点查询历史绩效数据。

---

## 六、开发者指南

### 项目目录结构

```
hummingbot-api/
├── main.py                 # FastAPI 入口，lifespan 管理，路由注册
├── config.py               # Pydantic Settings 配置（7 个配置类）
├── deps.py                 # FastAPI 依赖注入（13 个 get_*_service）
├── database/
│   ├── models.py           # SQLAlchemy ORM 模型（13 张表）
│   ├── connection.py       # AsyncDatabaseManager（连接池管理）
│   └── repositories/       # 8 个数据仓储
├── models/                 # Pydantic 请求/响应模型（15 个文件）
├── routers/                # FastAPI 路由（17 个 REST + 1 个 WebSocket）
├── services/               # 业务服务层（15 个服务模块）
│   ├── unified_connector_service.py  # 连接器统一入口
│   ├── executor_service.py           # 执行器生命周期
│   ├── bots_orchestrator.py          # MQTT+Docker Bot 编排
│   ├── market_data_service.py        # 行情数据管理
│   ├── trading_service.py            # 交易操作
│   ├── accounts_service.py           # 账户管理
│   ├── gateway_client.py             # Gateway HTTP 客户端
│   ├── gateway_service.py            # Gateway 容器管理
│   ├── gateway_transaction_poller.py # 链上交易轮询
│   ├── websocket_manager.py          # 行情 WS 推送
│   ├── executor_ws_manager.py        # 执行器 WS 推送
│   ├── docker_service.py             # Docker API 交互
│   ├── backtesting_service.py        # 回测任务管理
│   ├── orders_recorder.py            # 订单事件记录
│   └── funding_recorder.py           # 资金费率记录
├── bots/                   # 策略控制器与脚本
│   ├── controllers/        #   做市/方向性/通用 控制器
│   └── scripts/            #   V2 策略脚本
├── utils/                  # 工具函数（7 个模块）
└── test/                   # 测试目录
```

### 本地开发环境搭建

```bash
# 1. 安装 Conda 环境（含 pre-commit hooks）
make install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写必要配置

# 3. 启动基础设施
docker compose up emqx postgres -d

# 4. 启动开发服务（热重载）
conda activate hummingbot-api
uvicorn main:app --reload
```

### 测试

```bash
# 运行所有测试
conda run -n hummingbot-api pytest

# 运行特定测试文件
conda run -n hummingbot-api pytest test/test_gateway_lp_executor.py
```

### 代码质量

- **格式化**：Black（行宽 130）+ isort
- **Pre-commit**：check-yaml + end-of-file-fixer + black + isort
- **安装 hooks**：`make install` 自动安装，或手动 `pre-commit install`

### 服务初始化顺序

应用启动时按以下顺序初始化服务（`main.py` lifespan）：

1. `GatewayHttpClient` 单例
2. `AsyncDatabaseManager`（自动建表）
3. `RateOracle`（从 conf_client.yml 加载配置）
4. `UnifiedConnectorService`（所有交易连接器的唯一真实来源）
5. `MarketDataService` → `TradingService` → `AccountsService`
6. `ExecutorService`（依赖 TradingService）
7. `BotsOrchestrator` / `BacktestingService` / `DockerService` / `GatewayService` / `BotArchiver`
8. 启动所有服务并初始化交易连接器
9. 存入 `app.state`，供依赖注入使用

### 贡献流程

1. Fork 仓库
2. 创建功能分支（`git checkout -b feat/my-feature`）
3. 提交变更（遵循 Black + isort 格式）
4. 推送分支并创建 Pull Request
5. 通过 CI 检查后合并

---

## 附录 A：常见问题 & 错误排查

### API 无法启动

```bash
# 查看容器日志
docker compose logs hummingbot-api

# 检查端口占用
lsof -i :8000
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker compose logs postgres

# 完全重置数据库
docker compose down -v
make deploy
```

**注意**：PostgreSQL 默认用户是 `hbot` 而非 `postgres`。

### MQTT 连接问题

```bash
# 查看 EMQX 日志
docker logs hummingbot-broker

# 重启 EMQX
docker compose restart emqx

# 访问 EMQX Dashboard
# http://localhost:18083 (admin/public)
```

### Gateway 问题

```bash
# 检查 Gateway 状态
curl -u admin:admin http://localhost:8000/gateway/status

# 查看 Gateway 日志
curl -u admin:admin http://localhost:8000/gateway/logs
```

### Docker 守护进程未运行

```bash
# 检查 Docker 状态
docker info

# macOS: 启动 Docker Desktop
open -a Docker
```

### 完全重置

```bash
# 停止所有服务并删除数据卷
docker compose down -v

# 重新配置
make setup

# 重新部署
make deploy
```

---

## 附录 B：术语表

| 术语 | 解释 |
|------|------|
| **Base Asset（基础资产）** | 交易对中数量固定为单价报价单位的资产。如 BTC-USDT 中 BTC 是基础资产 |
| **Quote Asset（报价资产）** | 交易对中数量变化的资产。如 BTC-USDT 中 USDT 是报价资产 |
| **CEX（中心化交易所）** | 由中央机构运营的交易所，保管用户资产。如 Binance、OKX |
| **DEX（去中心化交易所）** | 基于智能合约的交易所，用户自管资产。如 Uniswap、Raydium |
| **Gateway** | Hummingbot 的 DEX 中间件，提供跨链统一接口（Swap、CLMM、钱包管理） |
| **CLMM（集中流动性做市）** | V3 风格流动性池，允许 LP 将资本集中在自定义价格范围，提升资本效率 |
| **Executor（执行器）** | 策略执行单元，负责具体的订单创建与管理。8 种类型覆盖不同交易场景 |
| **Controller（控制器）** | V2 策略框架中的模块化策略组件，发出 ExecutorActions 控制执行器 |
| **Maker（挂单方）** | 下达限价单为市场提供流动性的一方 |
| **Taker（吃单方）** | 下达市价单立即成交并消耗流动性的一方 |
| **Mid Price（中间价）** | 订单簿中最佳买价和最佳卖价的平均值 |
| **MQTT** | 轻量级消息协议，用于 API 与 Hummingbot 实例之间的实时通信 |
| **MCP（Model Context Protocol）** | 让 AI 助手与 Hummingbot API 交互的协议，支持自然语言控制交易 |
