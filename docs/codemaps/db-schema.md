# 数据库表结构文档

> 自动生成自 `database/models.py` | PostgreSQL 16 | SQLAlchemy 声明式 Base

## 概览

| 表名 | 模型类 | 说明 | 关键关系 |
|------|--------|------|----------|
| account_states | AccountState | 账户状态快照 | 1:N → token_states |
| token_states | TokenState | 代币持仓状态 | N:1 → account_states |
| orders | Order | 交易订单 | 1:N → trades, 1:N → executor_orders(间接) |
| trades | Trade | 成交记录 | N:1 → orders |
| position_snapshots | PositionSnapshot | 持仓快照（合约） | 独立 |
| funding_payments | FundingPayment | 资金费率支付 | 独立 |
| bot_runs | BotRun | 机器人运行记录 | 独立 |
| gateway_swaps | GatewaySwap | Gateway 链上兑换 | 独立 |
| gateway_clmm_positions | GatewayCLMMPosition | CLMM 集中流动性仓位 | 1:N → gateway_clmm_events |
| gateway_clmm_events | GatewayCLMMEvent | CLMM 仓位事件 | N:1 → gateway_clmm_positions |
| executors | ExecutorRecord | 执行器状态持久化 | 1:N → executor_orders |
| position_holds | PositionHoldRecord | 持仓持有追踪 | 独立 |
| executor_orders | ExecutorOrder | 执行器关联订单 | N:1 → executors |

---

## account_states

账户状态快照，记录某账户在某连接器下的整体状态。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| timestamp | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 快照时间 |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| connector_name | VARCHAR | NOT NULL, IDX | 连接器名 |

**关系**: `token_states` (1:N, cascade delete-orphan)

---

## token_states

代币持仓状态，属于某个账户状态快照。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| account_state_id | INTEGER | FK → account_states.id, NOT NULL | 所属账户状态 |
| token | VARCHAR | NOT NULL, IDX | 代币标识 |
| units | NUMERIC(30,18) | NOT NULL | 持有数量 |
| price | NUMERIC(30,18) | NOT NULL | 当前价格 |
| value | NUMERIC(30,18) | NOT NULL | 当前价值 |
| available_units | NUMERIC(30,18) | NOT NULL | 可用数量 |

**关系**: `account_states` (N:1)

---

## orders

交易订单记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| client_order_id | VARCHAR | NOT NULL, UNIQUE, IDX | 客户端订单ID |
| exchange_order_id | VARCHAR | IDX | 交易所订单ID |
| created_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 创建时间 |
| updated_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), ON UPDATE now() | 更新时间 |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| connector_name | VARCHAR | NOT NULL, IDX | 连接器名 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| trade_type | VARCHAR | NOT NULL | 买卖方向: BUY, SELL |
| order_type | VARCHAR | NOT NULL | 订单类型: LIMIT, MARKET, LIMIT_MAKER |
| amount | NUMERIC(30,18) | NOT NULL | 下单数量 |
| price | NUMERIC(30,18) | | 下单价格（市价单为 NULL） |
| status | VARCHAR | NOT NULL, DEFAULT 'SUBMITTED', IDX | 状态: SUBMITTED, OPEN, FILLED, CANCELLED, FAILED |
| filled_amount | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 已成交数量 |
| average_fill_price | NUMERIC(30,18) | | 平均成交价 |
| fee_paid | NUMERIC(30,18) | DEFAULT 0 | 手续费金额 |
| fee_currency | VARCHAR | | 手续费币种 |
| error_message | TEXT | | 错误信息 |

**关系**: `trades` (1:N, cascade delete-orphan)

---

## trades

成交记录，属于某个订单。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| order_id | INTEGER | FK → orders.id, NOT NULL | 所属订单 |
| trade_id | VARCHAR | NOT NULL, UNIQUE, IDX | 成交ID |
| timestamp | TIMESTAMP(TZ) | NOT NULL, IDX | 成交时间 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| trade_type | VARCHAR | NOT NULL | 买卖方向: BUY, SELL |
| amount | NUMERIC(30,18) | NOT NULL | 成交数量 |
| price | NUMERIC(30,18) | NOT NULL | 成交价格 |
| fee_paid | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 手续费金额 |
| fee_currency | VARCHAR | | 手续费币种 |

**关系**: `orders` (N:1)

---

## position_snapshots

合约持仓快照，含交易所数据和本地对账数据。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| connector_name | VARCHAR | NOT NULL, IDX | 连接器名 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| timestamp | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 快照时间 |
| side | VARCHAR | NOT NULL | 方向: LONG, SHORT |
| exchange_size | NUMERIC(30,18) | NOT NULL | 交易所仓位大小 |
| entry_price | NUMERIC(30,18) | | 平均入场价 |
| mark_price | NUMERIC(30,18) | | 标记价格 |
| unrealized_pnl | NUMERIC(30,18) | | 未实现盈亏 |
| percentage_pnl | NUMERIC(10,6) | | 盈亏百分比 |
| leverage | NUMERIC(10,2) | | 杠杆倍数 |
| initial_margin | NUMERIC(30,18) | | 初始保证金 |
| maintenance_margin | NUMERIC(30,18) | | 维持保证金 |
| cumulative_funding_fees | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 累计资金费 |
| fee_currency | VARCHAR | | 费用币种（通常为 USDT） |
| calculated_size | NUMERIC(30,18) | | 本地交易计算的仓位大小 |
| calculated_entry_price | NUMERIC(30,18) | | 本地交易计算的入场价 |
| size_difference | NUMERIC(30,18) | | 对账差异 |
| exchange_position_id | VARCHAR | IDX | 交易所仓位ID |
| is_reconciled | VARCHAR | NOT NULL, DEFAULT 'PENDING' | 对账状态: RECONCILED, MISMATCH, PENDING |

---

## funding_payments

资金费率支付记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| funding_payment_id | VARCHAR | NOT NULL, UNIQUE, IDX | 资金费支付ID |
| timestamp | TIMESTAMP(TZ) | NOT NULL, IDX | 支付时间 |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| connector_name | VARCHAR | NOT NULL, IDX | 连接器名 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| funding_rate | NUMERIC(20,18) | NOT NULL | 资金费率 |
| funding_payment | NUMERIC(30,18) | NOT NULL | 支付金额 |
| fee_currency | VARCHAR | NOT NULL | 支付币种（通常为 USDT） |
| position_size | NUMERIC(30,18) | | 支付时的仓位大小 |
| position_side | VARCHAR | | 仓位方向: LONG, SHORT |
| exchange_funding_id | VARCHAR | IDX | 交易所资金费ID |

---

## bot_runs

机器人运行记录，追踪部署和运行状态。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| bot_name | VARCHAR | NOT NULL, IDX | 机器人名称 |
| instance_name | VARCHAR | NOT NULL, IDX | 实例名称 |
| deployed_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 部署时间 |
| strategy_type | VARCHAR | NOT NULL, IDX | 策略类型: script, controller |
| strategy_name | VARCHAR | NOT NULL, IDX | 策略名称 |
| config_name | VARCHAR | IDX | 配置名称 |
| stopped_at | TIMESTAMP(TZ) | IDX | 停止时间 |
| deployment_status | VARCHAR | NOT NULL, DEFAULT 'DEPLOYED', IDX | 部署状态: DEPLOYED, FAILED, ARCHIVED |
| run_status | VARCHAR | NOT NULL, DEFAULT 'CREATED', IDX | 运行状态: CREATED, RUNNING, STOPPED, ERROR |
| deployment_config | TEXT | | 部署配置（JSON） |
| final_status | TEXT | | 最终状态（JSON） |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| image_version | VARCHAR | IDX | 镜像版本 |
| error_message | TEXT | | 错误信息 |

---

## gateway_swaps

Gateway 链上兑换记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| transaction_hash | VARCHAR | NOT NULL, UNIQUE, IDX | 交易哈希 |
| timestamp | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 交易时间 |
| network | VARCHAR | NOT NULL, IDX | 网络（chain-network 格式，如 solana-mainnet-beta） |
| connector | VARCHAR | NOT NULL, IDX | 连接器（jupiter, 0x 等） |
| wallet_address | VARCHAR | NOT NULL, IDX | 钱包地址 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| base_token | VARCHAR | NOT NULL, IDX | 基础代币 |
| quote_token | VARCHAR | NOT NULL, IDX | 计价代币 |
| side | VARCHAR | NOT NULL | 方向: BUY, SELL |
| input_amount | NUMERIC(30,18) | NOT NULL | 输入金额 |
| output_amount | NUMERIC(30,18) | NOT NULL | 输出金额 |
| price | NUMERIC(30,18) | NOT NULL | 兑换价格 |
| slippage_pct | NUMERIC(10,6) | | 滑点百分比 |
| gas_fee | NUMERIC(30,18) | | Gas 费用 |
| gas_token | VARCHAR | | Gas 代币（SOL, ETH 等） |
| status | VARCHAR | NOT NULL, DEFAULT 'SUBMITTED', IDX | 状态: SUBMITTED, CONFIRMED, FAILED |
| pool_address | VARCHAR | IDX | 流动性池地址 |
| quote_id | VARCHAR | | 报价ID（若来自报价） |
| error_message | TEXT | | 错误信息 |

---

## gateway_clmm_positions

CLMM（集中流动性做市）仓位记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| position_address | VARCHAR | NOT NULL, UNIQUE, IDX | 仓位 NFT 地址 |
| pool_address | VARCHAR | NOT NULL, IDX | 流动性池地址 |
| network | VARCHAR | NOT NULL, IDX | 网络（chain-network 格式） |
| connector | VARCHAR | NOT NULL, IDX | 连接器（meteora, raydium, uniswap） |
| wallet_address | VARCHAR | NOT NULL, IDX | 钱包地址 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| base_token | VARCHAR | NOT NULL, IDX | 基础代币 |
| quote_token | VARCHAR | NOT NULL, IDX | 计价代币 |
| created_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 创建时间 |
| closed_at | TIMESTAMP(TZ) | IDX | 关闭时间 |
| status | VARCHAR | NOT NULL, DEFAULT 'OPEN', IDX | 状态: OPEN, CLOSED |
| lower_price | NUMERIC(30,18) | NOT NULL | 价格区间下限 |
| upper_price | NUMERIC(30,18) | NOT NULL | 价格区间上限 |
| lower_bin_id | INTEGER | | 下限 bin ID（Meteora 等基于 bin 的 CLMM） |
| upper_bin_id | INTEGER | | 上限 bin ID |
| entry_price | NUMERIC(30,18) | | 开仓时池价 |
| current_price | NUMERIC(30,18) | | 最新价格（关闭时为关闭价） |
| initial_base_token_amount | NUMERIC(30,18) | | 初始基础代币存入量 |
| initial_quote_token_amount | NUMERIC(30,18) | | 初始计价代币存入量 |
| position_rent | NUMERIC(30,18) | | 仓位租金（SOL，关闭时返还） |
| base_token_amount | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 当前基础代币数量 |
| quote_token_amount | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 当前计价代币数量 |
| in_range | VARCHAR | NOT NULL, DEFAULT 'UNKNOWN' | 是否在区间内: IN_RANGE, OUT_OF_RANGE, UNKNOWN |
| percentage | NUMERIC(10,6) | | 价格区间百分比: (upper - lower) / lower |
| base_fee_collected | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 已收取基础代币手续费 |
| quote_fee_collected | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 已收取计价代币手续费 |
| base_fee_pending | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 待收取基础代币手续费 |
| quote_fee_pending | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 待收取计价代币手续费 |
| last_updated | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), ON UPDATE now() | 最后更新时间 |

**关系**: `gateway_clmm_events` (1:N, cascade delete-orphan)

---

## gateway_clmm_events

CLMM 仓位事件记录（开仓、加仓、减仓、收手续费、平仓）。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| position_id | INTEGER | FK → gateway_clmm_positions.id, NOT NULL | 所属仓位 |
| transaction_hash | VARCHAR | NOT NULL, IDX | 交易哈希 |
| timestamp | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 事件时间 |
| event_type | VARCHAR | NOT NULL, IDX | 事件类型: OPEN, ADD_LIQUIDITY, REMOVE_LIQUIDITY, COLLECT_FEES, CLOSE |
| base_token_amount | NUMERIC(30,18) | | 基础代币数量 |
| quote_token_amount | NUMERIC(30,18) | | 计价代币数量 |
| base_fee_collected | NUMERIC(30,18) | | 收取的基础代币手续费 |
| quote_fee_collected | NUMERIC(30,18) | | 收取的计价代币手续费 |
| gas_fee | NUMERIC(30,18) | | Gas 费用 |
| gas_token | VARCHAR | | Gas 代币 |
| status | VARCHAR | NOT NULL, DEFAULT 'SUBMITTED', IDX | 状态: SUBMITTED, CONFIRMED, FAILED |
| error_message | TEXT | | 错误信息 |

**关系**: `gateway_clmm_positions` (N:1)

---

## executors

执行器状态持久化记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| executor_id | VARCHAR | NOT NULL, UNIQUE, IDX | 执行器ID |
| executor_type | VARCHAR | NOT NULL, IDX | 执行器类型 |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| connector_name | VARCHAR | NOT NULL, IDX | 连接器名 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| controller_id | VARCHAR | NOT NULL, DEFAULT 'main', IDX | 控制器ID |
| created_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 创建时间 |
| closed_at | TIMESTAMP(TZ) | IDX | 关闭时间 |
| status | VARCHAR | NOT NULL, DEFAULT 'RUNNING', IDX | 运行状态 |
| close_type | VARCHAR | | 关闭类型 |
| net_pnl_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 净盈亏（计价币） |
| net_pnl_pct | NUMERIC(10,6) | NOT NULL, DEFAULT 0 | 净盈亏百分比 |
| cum_fees_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 累计手续费（计价币） |
| filled_amount_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 已成交金额（计价币） |
| error_log | TEXT | | 错误日志（JSON） |
| config | TEXT | | 执行器配置（JSON） |
| final_state | TEXT | | 最终状态（JSON） |

**关系**: `executor_orders` (1:N, cascade delete-orphan)

---

## position_holds

持仓持有追踪，独立于执行器生命周期。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| account_name | VARCHAR | NOT NULL, IDX | 账户名 |
| connector_name | VARCHAR | NOT NULL, IDX | 连接器名 |
| trading_pair | VARCHAR | NOT NULL, IDX | 交易对 |
| controller_id | VARCHAR | NOT NULL, DEFAULT 'main', IDX | 控制器ID |
| buy_amount_base | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 买入量（基础币） |
| buy_amount_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 买入量（计价币） |
| sell_amount_base | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 卖出量（基础币） |
| sell_amount_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 卖出量（计价币） |
| realized_pnl_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 已实现盈亏（计价币） |
| cum_fees_quote | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 累计手续费（计价币） |
| executor_ids | TEXT | | 关联执行器ID列表（JSON 数组） |
| status | VARCHAR | NOT NULL, DEFAULT 'ACTIVE', IDX | 状态: ACTIVE, CLEARED |
| created_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), IDX | 创建时间 |
| last_updated | TIMESTAMP(TZ) | NOT NULL, DEFAULT now(), ON UPDATE now() | 最后更新时间 |
| cleared_at | TIMESTAMP(TZ) | | 清仓时间 |

**唯一约束**: `uq_position_hold_key` (account_name, connector_name, trading_pair, controller_id)

---

## executor_orders

执行器关联的订单记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, IDX | 自增主键 |
| executor_id | VARCHAR | FK → executors.executor_id, NOT NULL, IDX | 所属执行器 |
| client_order_id | VARCHAR | NOT NULL, IDX | 客户端订单ID |
| exchange_order_id | VARCHAR | | 交易所订单ID |
| order_type | VARCHAR | NOT NULL | 订单用途: open, close, take_profit, stop_loss |
| trade_type | VARCHAR | NOT NULL | 买卖方向: BUY, SELL |
| amount | NUMERIC(30,18) | NOT NULL | 下单数量 |
| price | NUMERIC(30,18) | | 下单价格 |
| status | VARCHAR | NOT NULL, DEFAULT 'SUBMITTED' | 状态 |
| filled_amount | NUMERIC(30,18) | NOT NULL, DEFAULT 0 | 已成交数量 |
| average_fill_price | NUMERIC(30,18) | | 平均成交价 |
| created_at | TIMESTAMP(TZ) | NOT NULL, DEFAULT now() | 创建时间 |
| updated_at | TIMESTAMP(TZ) | ON UPDATE now() | 更新时间 |

**关系**: `executors` (N:1)

---

## ER 关系图

```
account_states ──1:N──→ token_states
orders ──1:N──→ trades
gateway_clmm_positions ──1:N──→ gateway_clmm_events
executors ──1:N──→ executor_orders

position_snapshots     (独立)
funding_payments       (独立)
bot_runs               (独立)
gateway_swaps          (独立)
position_holds         (独立，唯一约束: account+connector+pair+controller)
```

---

## 枚举值参考

| 字段 | 可选值 |
|------|--------|
| orders.trade_type | BUY, SELL |
| orders.order_type | LIMIT, MARKET, LIMIT_MAKER |
| orders.status | SUBMITTED, OPEN, FILLED, CANCELLED, FAILED |
| trades.trade_type | BUY, SELL |
| position_snapshots.side | LONG, SHORT |
| position_snapshots.is_reconciled | RECONCILED, MISMATCH, PENDING |
| funding_payments.position_side | LONG, SHORT |
| bot_runs.strategy_type | script, controller |
| bot_runs.deployment_status | DEPLOYED, FAILED, ARCHIVED |
| bot_runs.run_status | CREATED, RUNNING, STOPPED, ERROR |
| gateway_swaps.side | BUY, SELL |
| gateway_swaps.status | SUBMITTED, CONFIRMED, FAILED |
| gateway_clmm_positions.status | OPEN, CLOSED |
| gateway_clmm_positions.in_range | IN_RANGE, OUT_OF_RANGE, UNKNOWN |
| gateway_clmm_events.event_type | OPEN, ADD_LIQUIDITY, REMOVE_LIQUIDITY, COLLECT_FEES, CLOSE |
| gateway_clmm_events.status | SUBMITTED, CONFIRMED, FAILED |
| executors.status | RUNNING, ... |
| executor_orders.order_type | open, close, take_profit, stop_loss |
| executor_orders.trade_type | BUY, SELL |
| position_holds.status | ACTIVE, CLEARED |
