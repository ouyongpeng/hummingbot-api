# Hummingbot API - 代码模块索引

> 自动生成于 2026-05-03 | 项目版本 1.0.1 | 技术栈: Python / FastAPI / SQLAlchemy / Docker

## 目录结构总览

```
hummingbot-api/
├── main.py                  # 应用入口，FastAPI 实例与生命周期管理
├── config.py                # Pydantic Settings 配置中心
├── deps.py                  # FastAPI 依赖注入（从 app.state 获取服务实例）
├── routers/                 # API 路由层（17 个路由模块 + 1 个 WebSocket）
├── services/                # 业务服务层（15 个服务模块）
├── models/                  # Pydantic 请求/响应模型（15 个模型文件）
├── database/                # 数据库层（ORM 模型 + 连接管理 + 8 个仓储）
├── utils/                   # 工具函数（7 个模块）
├── bots/                    # 策略控制器与脚本
│   ├── controllers/         #   做市/方向性/通用 控制器实现
│   └── scripts/             #   V2 策略脚本
└── test/                    # 测试目录
```

---

## 1. 应用入口 (`main.py`)

| 职责 | 说明 |
|------|------|
| FastAPI 实例 | 创建 `app = FastAPI(title="Hummingbot API", version="1.0.1")` |
| 生命周期管理 | `lifespan()` 异步上下文管理器，按顺序初始化/关闭所有服务 |
| 认证 | HTTP Basic Auth（`auth_user`），debug 模式可跳过 |
| Monkey Patch | `patched_save_to_yml` 阻止 Hummingbot 库目录写入 |
| CORS | 全量允许（生产环境需收紧） |
| Logfire | 可选的观测集成 |
| 路由挂载 | 17 个 REST 路由 + 1 个 WebSocket 路由，全部挂载 `Depends(auth_user)` |

### 服务初始化顺序

```
1. GatewayHttpClient 单例
2. AsyncDatabaseManager（建表）
3. RateOracle（从 conf_client.yml 加载）
4. UnifiedConnectorService（所有交易连接器的唯一真实来源）
5. MarketDataService → TradingService → AccountsService
6. ExecutorService（依赖 TradingService）
7. BotsOrchestrator / BacktestingService / DockerService / GatewayService / BotArchiver
8. 启动: connector_service → bots_orchestrator → market_data_service → executor_service → accounts_service
9. 存储: 全部放入 app.state
```

---

## 2. 配置中心 (`config.py`)

| 配置类 | 环境前缀 | 核心字段 |
|--------|----------|----------|
| `BrokerSettings` | `BROKER_` | host, port, username, password |
| `DatabaseSettings` | `DATABASE_` | url (PostgreSQL async) |
| `MarketDataSettings` | `MARKET_DATA_` | cleanup_interval, feed_timeout, candles_ready_timeout, ws_* |
| `SecuritySettings` | (无前缀) | username, password, debug_mode, config_password |
| `AWSSettings` | `AWS_` | api_key, secret_key, s3_default_bucket_name |
| `GatewaySettings` | `GATEWAY_` | url |
| `AppSettings` | (无前缀) | controllers_path, logfire_environment, account_update_interval |
| **`Settings`** | (根级) | 组合以上全部 + banned_tokens |

全局单例: `settings = Settings()`

---

## 3. 依赖注入 (`deps.py`)

每个服务一个 `get_*_service` 函数，从 `request.app.state` 提取实例，供 FastAPI `Depends()` 使用。

| 函数 | 返回类型 |
|------|----------|
| `get_bots_orchestrator` | `BotsOrchestrator` |
| `get_accounts_service` | `AccountsService` |
| `get_docker_service` | `DockerService` |
| `get_gateway_service` | `GatewayService` |
| `get_connector_service` | `UnifiedConnectorService` |
| `get_market_data_service` | `MarketDataService` |
| `get_trading_service` | `TradingService` |
| `get_executor_service` | `ExecutorService` |
| `get_bot_archiver` | `BotArchiver` |
| `get_database_manager` | `AsyncDatabaseManager` |
| `get_executor_ws_manager` | `ExecutorWebSocketManager` |
| `get_backtesting_service` | `BacktestingService` |
| `get_websocket_manager` | `WebSocketManager` |

---

## 4. 路由层 (`routers/`)

### 4.1 REST 路由

| 模块 | 前缀 | Tag | 核心端点 | 对应服务 |
|------|------|-----|----------|----------|
| `docker.py` | `/docker` | Docker | running, available-images, active-containers, exited-containers, clean/remove/stop/start-container, pull-image, pull-status | `DockerService`, `BotArchiver` |
| `gateway.py` | `/gateway` | Gateway | status, start, stop, restart, logs, connectors CRUD, chains, pools CRUD, networks CRUD + tokens, wallets CRUD + send | `GatewayService`, `AccountsService` |
| `accounts.py` | `/accounts` | Accounts | list, add/delete account, credentials CRUD, gateway wallets CRUD + set-default | `AccountsService` |
| `connectors.py` | `/connectors` | Connectors | available, config-map, trading-rules, order-types | `AccountsService`, `MarketDataService` |
| `trading.py` | `/trading` | Trading | orders(POST), cancel, positions, active-orders, orders/search, trades, position-mode, leverage, funding-payments | `AccountsService`, `UnifiedConnectorService` |
| `gateway_swap.py` | `/gateway` | Gateway Swaps | swap/quote, swap/execute, swaps/{hash}/status, swaps/search, swaps/summary | `AccountsService`, `AsyncDatabaseManager` |
| `gateway_clmm.py` | `/gateway` | Gateway CLMM | clmm/pool-info, clmm/pools, clmm/open, clmm/add, clmm/remove, clmm/close, clmm/collect-fees, clmm/positions_owned, clmm/positions/events, clmm/positions/search | `AccountsService`, `AsyncDatabaseManager` |
| `bot_orchestration.py` | `/bot-orchestration` | Bot Orchestration | status, mqtt, {bot}/status, {bot}/history, start-bot, stop-bot, bot-runs CRUD + stats, stop-and-archive-bot, deploy-v2-controllers, deploy-v2-script | `BotsOrchestrator`, `DockerService`, `BotArchiver`, `AsyncDatabaseManager` |
| `controllers.py` | `/controllers` | Controllers | list, configs CRUD, {type}/{name} CRUD, config/template, config/validate, bots/{bot}/configs | `FileSystemUtil` |
| `scripts.py` | `/scripts` | Scripts | list, configs CRUD, {name} CRUD, config/template | `FileSystemUtil` |
| `market_data.py` | `/market-data` | Market Data | candles, historical-candles, active-feeds, settings, available-candle-connectors, prices, funding-info, order-book + 查询端点, trading-pair/add/remove, order-book/diagnostics, order-book/restart | `MarketDataService` |
| `rate_oracle.py` | `/rate-oracle` | Rate Oracle | sources, config GET/PUT, rates, rate/{pair}, rate-async/{pair}, prices | `RateOracle`, `FileSystemUtil` |
| `backtesting.py` | `/backtesting` | Backtesting | run, tasks CRUD | `BacktestingService` |
| `archived_bots.py` | `/archived-bots` | Archived Bots | list, {db}/status, {db}/summary, {db}/performance, {db}/trades, {db}/orders, {db}/executors, {db}/positions, {db}/controllers | `HummingbotDatabase`, `FileSystemUtil` |
| `executors.py` | `/executors` | Executors | create, search, summary, performance, {id}/logs, types/available, {id}, {id}/stop, positions/summary, positions/{connector}/{pair}, DELETE positions, types/{type}/config | `ExecutorService`, `MarketDataService` |
| `portfolio.py` | `/portfolio` | Portfolio | state, history, distribution, accounts-distribution | `AccountsService` |

### 4.2 WebSocket 路由

| 模块 | 路径 | 订阅类型 | 说明 |
|------|------|----------|------|
| `websocket.py` | `/ws/market-data` | candles, order_book, trades | 实时行情推送 |
| `websocket.py` | `/ws/executors` | executors, executor_detail, executor_summary, performance, positions, executor_logs, bot_status, all_bots_status | 执行器状态与性能推送 |

认证方式: Basic Auth（header / query token / query params），心跳间隔 30s。

---

## 5. 服务层 (`services/`)

### 5.1 核心交易服务

| 服务 | 文件 | 核心类 | 职责 |
|------|------|--------|------|
| **统一连接器** | `unified_connector_service.py` | `UnifiedConnectorService` | 所有连接器的唯一真实来源；管理交易连接器（需认证/按账户）和数据连接器（共享/无需认证） |
| **行情数据** | `market_data_service.py` | `MarketDataService` | 集中管理 K线、OrderBook、价格、交易规则；自动生命周期管理（清理过期 Feed） |
| **交易** | `trading_service.py` | `TradingService`, `AccountTradingInterface` | 交易操作（buy/sell/cancel）；提供 ExecutorBase 兼容接口 |
| **账户** | `accounts_service.py` | `AccountsService`, `AccountTradingInterface` | 账户/凭证管理、余额查询、Gateway 钱包管理、组合状态快照与历史 |
| **执行器** | `executor_service.py` | `ExecutorService` | 管理执行器生命周期（position/grid/dca/twap/arbitrage/xemm/order/lp 共 8 种类型）；PnL 计算、PositionHold 跟踪 |

### 5.2 基础设施服务

| 服务 | 文件 | 核心类 | 职责 |
|------|------|--------|------|
| **Gateway 客户端** | `gateway_client.py` | `GatewayClient` | 封装 Gateway HTTP API（钱包、余额、Swap、CLMM 操作） |
| **Gateway 服务** | `gateway_service.py` | `GatewayService` | Gateway Docker 容器生命周期管理（start/stop/restart） |
| **Gateway 轮询** | `gateway_transaction_poller.py` | `GatewayTransactionPoller` | 轮询区块链确认 DEX 交易状态；同步 CLMM 持仓状态 |
| **Docker 服务** | `docker_service.py` | `DockerService` | Docker 守护进程交互（容器/镜像管理、创建 Hummingbot 实例） |
| **Bot 编排** | `bots_orchestrator.py` | `BotsOrchestrator` | MQTT + Docker 编排 Hummingbot 实例（启动/停止/状态查询） |
| **回测** | `backtesting_service.py` | `BacktestingService` | 后台回测任务管理（提交/查询/取消） |

### 5.3 事件记录服务

| 服务 | 文件 | 核心类 | 职责 |
|------|------|--------|------|
| **订单记录** | `orders_recorder.py` | `OrdersRecorder` | 监听 Hummingbot 事件，记录订单/成交到数据库 |
| **资金费率记录** | `funding_recorder.py` | `FundingRecorder` | 监听 FundingPaymentCompletedEvent，记录资金费率支付 |

### 5.4 WebSocket 推送服务

| 服务 | 文件 | 核心类 | 职责 |
|------|------|--------|------|
| **行情 WS** | `websocket_manager.py` | `WebSocketManager` | 管理行情数据 WebSocket 订阅（candles/orderbook/trades） |
| **执行器 WS** | `executor_ws_manager.py` | `ExecutorWebSocketManager` | 管理执行器状态/性能/持仓 WebSocket 订阅 |

### 服务依赖关系

```
UnifiedConnectorService ─────────────────────────────────────────┐
  ├── MarketDataService ─────────────────────────────────────────┤
  │     └── TradingService ──────────────────────────────────────┤
  │           ├── AccountsService ───────────────────────────────┤
  │           └── ExecutorService ───────────────────────────────┤
  │                 └── ExecutorWebSocketManager ────────────────┤
  └── GatewayClient ← GatewayService                             │
                                                                  │
BotsOrchestrator (MQTT + Docker) ← DockerService ← BotArchiver  │
BacktestingService (独立)                                        │
GatewayTransactionPoller ← GatewayClient + AsyncDatabaseManager ←┘
```

---

## 6. 模型层 (`models/`)

所有 Pydantic 请求/响应模型，与路由一一对应。

| 模块文件 | 对应路由 | 核心模型 |
|----------|----------|----------|
| `accounts.py` | accounts | `CredentialRequest`, `LeverageRequest`, `PositionModeRequest`, `GatewayWalletCredential`, `SetDefaultWalletRequest` |
| `archived_bots.py` | archived_bots | `ArchivedBotListResponse`, `BotPerformanceResponse`, `BotSummary`, `TradeHistoryResponse`, `OrderHistoryResponse`, `ExecutorsResponse` |
| `backtesting.py` | backtesting | `BacktestingConfig` |
| `bot_orchestration.py` | bot_orchestration | `StartBotAction`, `StopBotAction`, `V2ControllerDeployment`, `V2ScriptDeployment`, `StopAndArchiveRequest/Response` |
| `connectors.py` | connectors | `ConnectorInfo`, `ConnectorConfigMapResponse`, `ConnectorListResponse`, `TradingRule` |
| `controllers.py` | controllers | `ControllerType`, `Controller`, `ControllerConfig`, `ControllerConfigResponse` |
| `docker.py` | docker | `DockerImage` |
| `executors.py` | executors | `CreateExecutorRequest/Response`, `StopExecutorRequest/Response`, `ExecutorFilterRequest`, `PositionHold` |
| `gateway.py` | gateway | `GatewayConfig`, `GatewayStatus`, `CreateWalletRequest`, `AddPoolRequest`, `AddTokenRequest`, `SendTransactionRequest` |
| `gateway_trading.py` | gateway_swap + gateway_clmm | `SwapQuote/Execute Request/Response`, `CLMMOpen/Add/Remove/Close/CollectFees Request/Response`, `CLMMPoolInfoResponse`, `CLMMPoolListResponse` |
| `market_data.py` | market_data | `CandlesConfigRequest`, `PriceRequest`, `FundingInfoRequest/Response`, `OrderBookRequest/Response`, 各种 OrderBookQuery 模型, `AddTradingPairRequest`, `RemoveTradingPairRequest` |
| `pagination.py` | (通用) | `PaginationParams`, `TimeRangePaginationParams`, `PaginatedResponse` |
| `portfolio.py` | portfolio | `PortfolioStateResponse`, `PortfolioHistoryFilters`, `PortfolioDistributionResponse`, `AccountsDistributionResponse` |
| `rate_oracle.py` | rate_oracle | `RateOracleConfig`, `RateRequest`, `RateResponse`, `SingleRateResponse` |
| `scripts.py` | scripts | `Script`, `ScriptConfig`, `ScriptConfigResponse` |
| `trading.py` | trading | `TradeRequest/Response`, `OrderInfo`, `TradeInfo`, `PositionFilterRequest`, `OrderFilterRequest`, `FundingPaymentFilterRequest` |

---

## 7. 数据库层 (`database/`)

### 7.1 连接管理 (`connection.py`)

`AsyncDatabaseManager` — 基于 SQLAlchemy async engine + asyncpg，连接池配置: pool_size=5, max_overflow=10, pool_recycle=1800s。

### 7.2 ORM 模型 (`models.py`)

| 表名 | 模型类 | 核心字段 |
|------|--------|----------|
| `account_states` | `AccountState` | id, timestamp, account_name, connector_name → token_states |
| `token_states` | `TokenState` | token, units, price, value, available_units |
| `orders` | `Order` | client_order_id, account_name, connector_name, trading_pair, trade_type, order_type, amount, price, status, filled_amount, fee_paid |
| `trades` | `Trade` | order_id(FK), trade_id, trading_pair, trade_type, amount, price, fee |
| `position_snapshots` | `PositionSnapshot` | account_name, connector_name, trading_pair, amount, entry_price, unrealized_pnl |
| `funding_payments` | `FundingPayment` | account_name, connector_name, trading_pair, funding_rate, payment_amount |
| `bot_runs` | `BotRun` | bot_name, instance_name, strategy_type, strategy_name, deployment_status, run_status |
| `gateway_swaps` | `GatewaySwap` | transaction_hash, network, connector, trading_pair, side, input_amount, output_amount, status |
| `gateway_clmm_positions` | `GatewayCLMMPosition` | position_address, pool_address, connector, trading_pair, lower_price, upper_price, in_range, status |
| `gateway_clmm_events` | `GatewayCLMMEvent` | position_id(FK), event_type, transaction_hash, gas_fee |

### 7.3 仓储 (`repositories/`)

| 仓储 | 文件 | 操作 |
|------|------|------|
| `AccountRepository` | `account_repository.py` | 账户状态快照的保存与历史查询 |
| `BotRunRepository` | `bot_run_repository.py` | Bot 运行记录的 CRUD + 统计 |
| `ExecutorRepository` | `executor_repository.py` | 执行器记录的保存与查询 |
| `FundingRepository` | `funding_repository.py` | 资金费率支付记录 |
| `OrderRepository` | `order_repository.py` | 订单记录的保存与查询 |
| `TradeRepository` | `trade_repository.py` | 成交记录的保存与查询 |
| `GatewaySwapRepository` | `gateway_swap_repository.py` | DEX Swap 记录的 CRUD + 汇总统计 |
| `GatewayCLMMRepository` | `gateway_clmm_repository.py` | CLMM 持仓/事件的 CRUD + 状态更新 |

---

## 8. 工具函数 (`utils/`)

| 模块 | 核心类/函数 | 职责 |
|------|-------------|------|
| `file_system.py` | `FileSystemUtil`, `fs_util` (全局单例) | 文件/目录/YAML 读写、控制器/脚本配置类动态加载 |
| `security.py` | `BackendAPISecurity` | 密码验证文件管理（ETHKeyFileSecretManger 集成） |
| `bot_archiver.py` | `BotArchiver` | Bot 数据归档（本地 tar.gz 或 S3 上传） |
| `mqtt_manager.py` | `MQTTManager` | MQTT 通信管理（Bot 发现/命令/状态） |
| `hummingbot_database_reader.py` | `HummingbotDatabase` | 读取 Hummingbot SQLite 数据库（性能/订单/成交/持仓/执行器） |
| `hummingbot_api_config_adapter.py` | `HummingbotAPIConfigAdapter` | 将 API 配置适配为 Hummingbot 连接器配置 |
| `executor_log_capture.py` | `ExecutorLogCapture` | 执行器日志环形缓冲区捕获 |

---

## 9. 策略控制器 (`bots/controllers/`)

### 9.1 做市控制器 (`market_making/`)

| 控制器 | 文件 | 说明 |
|--------|------|------|
| PMM Simple | `pmm_simple.py` | 简单纯做市 |
| PMM Dynamic | `pmm_dynamic.py` | 动态价差做市 |
| DMan Maker V2 | `dman_maker_v2.py` | 多层做市 |

### 9.2 方向性交易控制器 (`directional_trading/`)

| 控制器 | 文件 | 说明 |
|--------|------|------|
| Bollinger V1 | `bollinger_v1.py` | 布林带策略 V1 |
| Bollinger V2 | `bollinger_v2.py` | 布林带策略 V2 |
| Bollingrid | `bollingrid.py` | 布林网格 |
| DMan V3 | `dman_v3.py` | DMan V3 方向性 |
| MACD BB V1 | `macd_bb_v1.py` | MACD + 布林带 |
| Supertrend V1 | `supertrend_v1.py` | Supertrend 趋势 |

### 9.3 通用控制器 (`generic/`)

| 控制器 | 文件 | 说明 |
|--------|------|------|
| PMM | `pmm.py` | 纯做市 |
| PMM V1 | `pmm_v1.py` | 做市 V1 |
| PMM Adjusted | `pmm_adjusted.py` | 调整做市 |
| PMM Mister | `pmm_mister.py` | Mister 做市 |
| Grid Strike | `grid_strike.py` | 网格打击 |
| Multi Grid Strike | `multi_grid_strike.py` | 多网格打击 |
| Quantum Grid Allocator | `quantum_grid_allocator.py` | 量子网格分配 |
| XEMM Multiple Levels | `xemm_multiple_levels.py` | 跨交易所做市多层 |
| Stat Arb | `stat_arb.py` | 统计套利 |
| Arbitrage | `arbitrage_controller.py` | 跨交易所套利 |
| Hedge Asset | `hedge_asset.py` | 对冲 |
| LP Rebalancer | `lp_rebalancer/` | LP 再平衡（包式控制器） |
| Examples | `examples/` | 示例控制器（basic_order, candles_data, full_trading 等 7 个） |

---

## 10. 策略脚本 (`bots/scripts/`)

| 脚本 | 文件 | 说明 |
|------|------|------|
| V2 with Controllers | `v2_with_controllers.py` | V2 策略框架，加载并运行控制器组合 |

---

## 11. 测试 (`test/`)

| 文件 | 说明 |
|------|------|
| `test_gateway_lp_executor.py` | Gateway LP 执行器集成测试 |

---

## 12. 关键架构特征

### 认证与安全
- 全局 HTTP Basic Auth（所有 REST 路由），WebSocket 独立认证
- `secrets.compare_digest` 防时序攻击
- `BackendAPISecurity` 通过 `ETHKeyFileSecretManger` 管理密码验证文件
- Debug 模式可跳过认证

### 分页模式
- 游标分页（cursor-based）为主，避免深翻页性能问题
- `PaginatedResponse` 统一分页响应结构
- 支持 `TimeRangePaginationParams` 按时间范围分页

### 连接器管理
- `UnifiedConnectorService` 是连接器的唯一真实来源
- 交易连接器（需认证）vs 数据连接器（共享/无认证）分离
- `get_best_connector_for_market()` 优先使用交易连接器（有 OrderBook Tracker）

### 执行器类型
支持 8 种执行器: `position_executor`, `grid_executor`, `dca_executor`, `twap_executor`, `arbitrage_executor`, `xemm_executor`, `order_executor`, `lp_executor`

### Gateway 集成
- DEX 操作（Swap / CLMM）通过 `GatewayClient` 调用 Gateway HTTP API
- `GatewayTransactionPoller` 轮询链上确认状态
- CLMM 持仓自动同步（轮询 + 关闭验证）
- Raydium 特殊处理：直接调用 Raydium API 而非 Gateway

### 实时推送
- `/ws/market-data`: candles / order_book / trades 订阅
- `/ws/executors`: 执行器状态 / 性能 / 持仓 / 日志 / Bot 状态 订阅
- 订阅间隔可配置（0.5s ~ 60s），默认 2s

### 数据持久化
- PostgreSQL (asyncpg) 存储账户状态快照、订单、成交、资金费率、Bot 运行、Swap/CLMM 操作
- `OrdersRecorder` / `FundingRecorder` 监听 Hummingbot 事件实时记录
- 归档 Bot 数据支持本地 tar.gz 和 AWS S3
