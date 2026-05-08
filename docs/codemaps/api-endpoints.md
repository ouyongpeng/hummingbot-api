# Hummingbot API - 端点快查表

> 自动生成，基于路由文件扫描。最后更新：2026-05-03

## 概览

| 模块 | 前缀 | 认证 | 端点数 |
|------|------|------|--------|
| Accounts | `/accounts` | Basic Auth | 10 |
| Backtesting | `/backtesting` | Basic Auth | 5 |
| Bot Orchestration | `/bot-orchestration` | Basic Auth | 11 |
| Connectors | `/connectors` | Basic Auth | 4 |
| Controllers | `/controllers` | Basic Auth | 11 |
| Docker | `/docker` | Basic Auth | 10 |
| Executors | `/executors` | Basic Auth | 12 |
| Gateway | `/gateway` | Basic Auth | 21 |
| Gateway CLMM | `/gateway` | Basic Auth | 9 |
| Gateway Swap | `/gateway` | Basic Auth | 5 |
| Market Data | `/market-data` | Basic Auth | 16 |
| Portfolio | `/portfolio` | Basic Auth | 4 |
| Rate Oracle | `/rate-oracle` | Basic Auth | 7 |
| Scripts | `/scripts` | Basic Auth | 8 |
| Trading | `/trading` | Basic Auth | 11 |
| WebSocket | (无前缀) | WS Auth | 2 |
| Archived Bots | `/archived-bots` | Basic Auth | 9 |

**总计：135 个端点**

---

## Accounts `/accounts`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/accounts/` | 列出所有账户名 |
| GET | `/accounts/{account_name}/credentials` | 列出账户的连接器凭证 |
| POST | `/accounts/add-account` | 创建新账户 |
| POST | `/accounts/delete-account` | 删除账户 |
| POST | `/accounts/delete-credential/{account_name}/{connector_name}` | 删除连接器凭证 |
| POST | `/accounts/add-credential/{account_name}/{connector_name}` | 添加/更新连接器凭证 |
| GET | `/accounts/gateway/wallets` | 列出 Gateway 钱包 |
| POST | `/accounts/gateway/add-wallet` | 通过私钥添加钱包到 Gateway |
| POST | `/accounts/gateway/wallet/set-default` | 设置链默认钱包 |
| DELETE | `/accounts/gateway/{chain}/{address}` | 从 Gateway 移除钱包 |

---

## Backtesting `/backtesting`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/backtesting/run` | 同步运行回测 |
| POST | `/backtesting/tasks` | 提交后台回测任务 |
| GET | `/backtesting/tasks` | 列出所有回测任务 |
| GET | `/backtesting/tasks/{task_id}` | 获取回测任务详情 |
| DELETE | `/backtesting/tasks/{task_id}` | 取消/删除回测任务 |

---

## Bot Orchestration `/bot-orchestration`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/bot-orchestration/status` | 获取所有活跃 Bot 状态 |
| GET | `/bot-orchestration/mqtt` | 获取 MQTT 连接状态 |
| GET | `/bot-orchestration/{bot_name}/status` | 获取特定 Bot 状态 |
| GET | `/bot-orchestration/{bot_name}/history` | 获取 Bot 交易历史 |
| POST | `/bot-orchestration/start-bot` | 启动 Bot |
| POST | `/bot-orchestration/stop-bot` | 停止 Bot |
| GET | `/bot-orchestration/bot-runs` | 查询 Bot 运行记录 |
| GET | `/bot-orchestration/bot-runs/{bot_run_id}` | 获取特定 Bot 运行记录 |
| GET | `/bot-orchestration/bot-runs/stats` | 获取 Bot 运行统计 |
| POST | `/bot-orchestration/stop-and-archive-bot/{bot_name}` | 停止并归档 Bot |
| POST | `/bot-orchestration/deploy-v2-controllers` | 部署 V2 控制器策略 |
| POST | `/bot-orchestration/deploy-v2-script` | 部署 V2 脚本策略 |

---

## Connectors `/connectors`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/connectors/` | 列出可用连接器 |
| GET | `/connectors/{connector_name}/config-map` | 获取连接器配置字段 |
| GET | `/connectors/{connector_name}/trading-rules` | 获取交易规则 |
| GET | `/connectors/{connector_name}/order-types` | 获取支持的订单类型 |

---

## Controllers `/controllers`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/controllers/` | 按类型列出控制器 |
| GET | `/controllers/configs/` | 列出所有控制器配置 |
| GET | `/controllers/configs/{config_name}` | 获取控制器配置 |
| POST | `/controllers/configs/{config_name}` | 创建/更新控制器配置 |
| DELETE | `/controllers/configs/{config_name}` | 删除控制器配置 |
| GET | `/controllers/{controller_type}/{controller_name}` | 获取控制器内容 |
| POST | `/controllers/{controller_type}/{controller_name}` | 创建/更新控制器 |
| DELETE | `/controllers/{controller_type}/{controller_name}` | 删除控制器 |
| GET | `/controllers/{controller_type}/{controller_name}/config/template` | 获取配置模板 |
| POST | `/controllers/{controller_type}/{controller_name}/config/validate` | 验证配置 |
| GET | `/controllers/bots/{bot_name}/configs` | 获取 Bot 的控制器配置 |
| POST | `/controllers/bots/{bot_name}/{controller_name}/config` | 更新 Bot 的控制器配置 |

---

## Docker `/docker`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/docker/running` | 检查 Docker 守护进程状态 |
| GET | `/docker/available-images/` | 列出可用镜像 |
| GET | `/docker/active-containers` | 列出运行中容器 |
| GET | `/docker/exited-containers` | 列出已停止容器 |
| POST | `/docker/clean-exited-containers` | 清理已停止容器 |
| POST | `/docker/remove-container/{container_name}` | 移除并归档容器 |
| POST | `/docker/stop-container/{container_name}` | 停止容器 |
| POST | `/docker/start-container/{container_name}` | 启动容器 |
| POST | `/docker/pull-image/` | 后台拉取镜像 |
| GET | `/docker/pull-status/` | 获取拉取进度 |

---

## Executors `/executors`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/executors/` | 创建执行器 |
| POST | `/executors/search` | 搜索执行器（分页） |
| GET | `/executors/summary` | 获取执行器汇总 |
| GET | `/executors/performance` | 获取绩效报告 |
| GET | `/executors/types/available` | 列出可用执行器类型 |
| GET | `/executors/types/{executor_type}/config` | 获取执行器配置 Schema |
| GET | `/executors/{executor_id}` | 获取执行器详情 |
| GET | `/executors/{executor_id}/logs` | 获取执行器日志 |
| POST | `/executors/{executor_id}/stop` | 停止执行器 |
| GET | `/executors/positions/summary` | 获取持仓汇总 |
| GET | `/executors/positions/{connector_name}/{trading_pair}` | 获取特定持仓 |
| DELETE | `/executors/positions/{connector_name}/{trading_pair}` | 清除持仓记录 |

---

## Gateway `/gateway`

### 容器管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gateway/status` | Gateway 容器状态 |
| POST | `/gateway/start` | 启动 Gateway |
| POST | `/gateway/stop` | 停止 Gateway |
| POST | `/gateway/restart` | 重启 Gateway |
| GET | `/gateway/logs` | Gateway 日志 |

### 连接器配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gateway/connectors` | 列出 DEX 连接器 |
| GET | `/gateway/connectors/{connector_name}` | 获取连接器配置 |
| POST | `/gateway/connectors/{connector_name}` | 更新连接器配置 |

### 链与网络

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gateway/chains` | 列出所有链 |
| GET | `/gateway/networks` | 列出所有网络 |
| GET | `/gateway/networks/{network_id}` | 获取网络配置 |
| POST | `/gateway/networks/{network_id}` | 更新网络配置 |
| GET | `/gateway/networks/{network_id}/tokens` | 获取网络代币 |
| POST | `/gateway/networks/{network_id}/tokens` | 添加自定义代币 |
| DELETE | `/gateway/networks/{network_id}/tokens/{token_address}` | 删除自定义代币 |

### 流动性池

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gateway/pools` | 列出流动性池 |
| POST | `/gateway/pools` | 添加流动性池 |
| DELETE | `/gateway/pools/{address}` | 删除流动性池 |

### 钱包与交易

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/gateway/wallets/create` | 创建新钱包 |
| POST | `/gateway/wallets/show-private-key` | 导出私钥 |
| POST | `/gateway/wallets/send` | 发送代币转账 |

---

## Gateway CLMM `/gateway` (CLMM 流动性)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gateway/clmm/pool-info` | 获取 CLMM 池信息 |
| GET | `/gateway/clmm/pools` | 列出 CLMM 池（支持 Meteora） |
| POST | `/gateway/clmm/open` | 开仓 CLMM 头寸 |
| POST | `/gateway/clmm/add` | 增加流动性 |
| POST | `/gateway/clmm/remove` | 移除部分流动性 |
| POST | `/gateway/clmm/close` | 完全平仓 |
| POST | `/gateway/clmm/collect-fees` | 收取手续费 |
| POST | `/gateway/clmm/positions_owned` | 查询持有的头寸 |
| GET | `/gateway/clmm/positions/{position_address}/events` | 获取头寸事件历史 |
| POST | `/gateway/clmm/positions/search` | 搜索 CLMM 头寸 |

---

## Gateway Swap `/gateway` (DEX 兑换)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/gateway/swap/quote` | 获取兑换报价 |
| POST | `/gateway/swap/execute` | 执行兑换 |
| GET | `/gateway/swaps/{transaction_hash}/status` | 查询兑换状态 |
| POST | `/gateway/swaps/search` | 搜索兑换历史 |
| GET | `/gateway/swaps/summary` | 兑换汇总统计 |

---

## Market Data `/market-data`

### K线与行情

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/market-data/candles` | 获取实时 K 线 |
| POST | `/market-data/historical-candles` | 获取历史 K 线 |
| POST | `/market-data/prices` | 获取当前价格 |
| POST | `/market-data/funding-info` | 获取资金费率信息 |

### 订单簿

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/market-data/order-book` | 获取订单簿快照 |
| POST | `/market-data/order-book/price-for-volume` | 按量查价 |
| POST | `/market-data/order-book/volume-for-price` | 按价查量 |
| POST | `/market-data/order-book/price-for-quote-volume` | 按报价货币量查价 |
| POST | `/market-data/order-book/quote-volume-for-price` | 按价查报价货币量 |
| POST | `/market-data/order-book/vwap-for-volume` | 按量查 VWAP |
| GET | `/market-data/order-book/diagnostics/{connector_name}` | 订单簿诊断 |
| POST | `/market-data/order-book/restart/{connector_name}` | 重启订单簿追踪 |

### 交易对管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/market-data/trading-pair/add` | 初始化交易对订单簿 |
| POST | `/market-data/trading-pair/remove` | 移除交易对追踪 |

### 系统信息

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/market-data/active-feeds` | 获取活跃行情源 |
| GET | `/market-data/settings` | 获取行情配置 |
| GET | `/market-data/available-candle-connectors` | 获取支持 K 线的连接器 |

---

## Portfolio `/portfolio`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/portfolio/state` | 获取组合当前状态 |
| POST | `/portfolio/history` | 获取组合历史（分页+采样） |
| POST | `/portfolio/distribution` | 获取代币分布 |
| GET | `/portfolio/accounts-distribution` | 获取账户分布 |

---

## Rate Oracle `/rate-oracle`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/rate-oracle/sources` | 列出可用价格源 |
| GET | `/rate-oracle/config` | 获取当前配置 |
| PUT | `/rate-oracle/config` | 更新配置 |
| POST | `/rate-oracle/rates` | 批量获取汇率 |
| GET | `/rate-oracle/rate/{trading_pair}` | 获取单一汇率（缓存） |
| GET | `/rate-oracle/rate-async/{trading_pair}` | 获取单一汇率（实时） |
| GET | `/rate-oracle/prices` | 获取所有缓存价格 |

---

## Scripts `/scripts`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/scripts/` | 列出所有脚本 |
| GET | `/scripts/configs/` | 列出所有脚本配置 |
| GET | `/scripts/configs/{config_name}` | 获取脚本配置 |
| POST | `/scripts/configs/{config_name}` | 创建/更新脚本配置 |
| DELETE | `/scripts/configs/{config_name}` | 删除脚本配置 |
| GET | `/scripts/{script_name}` | 获取脚本内容 |
| POST | `/scripts/{script_name}` | 创建/更新脚本 |
| DELETE | `/scripts/{script_name}` | 删除脚本 |
| GET | `/scripts/{script_name}/config/template` | 获取脚本配置模板 |

---

## Trading `/trading`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/trading/orders` | 下单 |
| POST | `/trading/{account_name}/{connector_name}/orders/{client_order_id}/cancel` | 撤单 |
| POST | `/trading/orders/active` | 查询活跃订单 |
| POST | `/trading/orders/search` | 搜索历史订单 |
| POST | `/trading/positions` | 查询持仓 |
| POST | `/trading/trades` | 查询成交记录 |
| POST | `/trading/funding-payments` | 查询资金费率支付记录 |
| POST | `/trading/{account_name}/{connector_name}/position-mode` | 设置持仓模式 |
| GET | `/trading/{account_name}/{connector_name}/position-mode` | 获取持仓模式 |
| POST | `/trading/{account_name}/{connector_name}/leverage` | 设置杠杆 |

---

## WebSocket

| 方法 | 路径 | 说明 |
|------|------|------|
| WS | `/ws/market-data` | 实时行情推送（K 线、订单簿、成交） |
| WS | `/ws/executors` | 实时执行器数据推送 |

**WS 认证方式**：Basic Auth（Authorization 头 / ?token=base64(user:pass) / ?username=&password=）

**WS 订阅协议**：
- `{"action": "subscribe", "type": "...", ...}` -- 订阅
- `{"action": "unsubscribe", "subscription_id": "..."}` -- 取消订阅
- `{"action": "ping"}` -- 心跳

---

## Archived Bots `/archived-bots`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/archived-bots/` | 列出所有归档数据库 |
| GET | `/archived-bots/{db_path:path}/status` | 数据库状态 |
| GET | `/archived-bots/{db_path:path}/summary` | 数据库概要 |
| GET | `/archived-bots/{db_path:path}/performance` | 绩效分析 |
| GET | `/archived-bots/{db_path:path}/trades` | 交易记录 |
| GET | `/archived-bots/{db_path:path}/orders` | 订单记录 |
| GET | `/archived-bots/{db_path:path}/executors` | 执行器数据 |
| GET | `/archived-bots/{db_path:path}/positions` | 持仓数据 |
| GET | `/archived-bots/{db_path:path}/controllers` | 控制器数据 |
