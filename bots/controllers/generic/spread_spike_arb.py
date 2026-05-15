import numpy as np
import pandas as pd
from decimal import Decimal
from typing import List, Optional, Tuple

from pydantic import Field

from hummingbot.core.data_type.common import MarketDict
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy_v2.controllers.controller_base import ControllerBase, ControllerConfigBase
from hummingbot.strategy_v2.executors.arbitrage_executor.data_types import ArbitrageExecutorConfig
from hummingbot.strategy_v2.executors.data_types import ConnectorPair
from hummingbot.strategy_v2.models.base import RunnableStatus
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, ExecutorAction, StopExecutorAction


class SpreadSpikeArbConfig(ControllerConfigBase):
    controller_name: str = "spread_spike_arb"
    connector_pair_a: ConnectorPair = ConnectorPair(connector_name="binance", trading_pair="BTC-USDT")
    connector_pair_b: ConnectorPair = ConnectorPair(connector_name="bybit", trading_pair="BTC-USDT")
    min_spread_bps: float = Field(default=50, ge=10, le=500)
    zscore_threshold: float = Field(default=2.0, ge=0.5, le=5.0)
    lookback_periods: int = Field(default=100, ge=20, le=1000)
    interval: str = "1m"
    min_std_bps: float = Field(default=5, ge=1, le=50)
    order_amount: Decimal = Field(default=Decimal("0.01"), ge=Decimal("0.001"), le=Decimal("10000"))
    min_profitability: Decimal = Decimal("0.003")
    delay_between_executors: int = Field(default=10, ge=1, le=300)
    max_executors_imbalance: int = Field(default=1, ge=1, le=10)
    max_loss_per_trade_pct: float = Field(default=0.003, ge=0.001, le=0.05)
    daily_max_loss_pct: float = Field(default=0.02, ge=0.005, le=0.1)
    max_consecutive_losses: int = Field(default=3, ge=1, le=10)
    cooldown_after_loss_seconds: float = Field(default=60, ge=10, le=600)
    max_open_positions: int = Field(default=1, ge=1, le=5)
    executor_timeout_seconds: float = Field(default=300, ge=60, le=3600)

    def update_markets(self, markets: MarketDict) -> MarketDict:
        for cp in [self.connector_pair_a, self.connector_pair_b]:
            markets.add_or_update(cp.connector_name, cp.trading_pair)
        return markets


class SpreadSpikeArbController(ControllerBase):
    def __init__(self, config: SpreadSpikeArbConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.config = config
        self._daily_pnl: float = 0.0
        self._pnl_history: List[Tuple[float, Decimal]] = []
        self._consecutive_losses: int = 0
        self._cooldown_until: float = 0.0
        self._last_executor_created_timestamp: float = 0.0
        self.processed_data = {
            "spread": Decimal("0"),
            "spread_bps": Decimal("0"),
            "rolling_mean": Decimal("0"),
            "rolling_std": Decimal("0"),
            "z_score": Decimal("0"),
            "signal": 0,
            "daily_pnl": Decimal("0"),
            "consecutive_losses": 0,
            "cooldown_until": 0.0,
            "active_executors_count": 0,
        }

    def get_candles_config(self) -> List[CandlesConfig]:
        max_records = self.config.lookback_periods + 20
        return [
            CandlesConfig(
                connector=self.config.connector_pair_a.connector_name,
                trading_pair=self.config.connector_pair_a.trading_pair,
                interval=self.config.interval,
                max_records=max_records,
            ),
            CandlesConfig(
                connector=self.config.connector_pair_b.connector_name,
                trading_pair=self.config.connector_pair_b.trading_pair,
                interval=self.config.interval,
                max_records=max_records,
            ),
        ]

    async def update_processed_data(self):
        candles_a = self.market_data_provider.get_candles_df(
            connector_name=self.config.connector_pair_a.connector_name,
            trading_pair=self.config.connector_pair_a.trading_pair,
            interval=self.config.interval,
            max_records=self.config.lookback_periods + 20,
        )
        candles_b = self.market_data_provider.get_candles_df(
            connector_name=self.config.connector_pair_b.connector_name,
            trading_pair=self.config.connector_pair_b.trading_pair,
            interval=self.config.interval,
            max_records=self.config.lookback_periods + 20,
        )

        if candles_a.empty or candles_b.empty:
            self.processed_data["signal"] = 0
            return

        merged = pd.merge_asof(
            candles_a.sort_values("timestamp"),
            candles_b.sort_values("timestamp"),
            on="timestamp",
            direction="nearest",
            tolerance=pd.Timedelta(self.config.interval),
        )

        if len(merged) < self.config.lookback_periods:
            self.processed_data["signal"] = 0
            return

        merged = merged.tail(self.config.lookback_periods)

        price_a = merged["close_x"].values
        price_b = merged["close_y"].values
        mid_price = (price_a + price_b) / 2
        spread = (price_a - price_b) / mid_price

        rolling_mean = np.mean(spread)
        rolling_std = np.std(spread)

        if rolling_std < self.config.min_std_bps / 10000:
            self.processed_data.update({
                "signal": 0,
                "rolling_std": Decimal(str(rolling_std)),
            })
            return

        current_spread = spread[-1]
        z_score = (current_spread - rolling_mean) / rolling_std
        spread_bps = abs(current_spread) * 10000

        signal = 0
        if spread_bps >= self.config.min_spread_bps and z_score >= self.config.zscore_threshold:
            signal = 1
        elif spread_bps >= self.config.min_spread_bps and z_score <= -self.config.zscore_threshold:
            signal = -1

        self.processed_data.update({
            "spread": Decimal(str(current_spread)),
            "spread_bps": Decimal(str(spread_bps)),
            "rolling_mean": Decimal(str(rolling_mean)),
            "rolling_std": Decimal(str(rolling_std)),
            "z_score": Decimal(str(z_score)),
            "signal": signal,
        })

    def _update_risk_state(self):
        closed_executors = [e for e in self.executors_info if e.status == RunnableStatus.TERMINATED]
        current_time = self.market_data_provider.time()

        for executor in closed_executors:
            if executor.close_timestamp > self._last_executor_created_timestamp:
                pnl = executor.net_pnl_quote
                self._pnl_history.append((current_time, pnl))
                self._daily_pnl += float(pnl)
                if pnl < 0:
                    self._consecutive_losses += 1
                    self._cooldown_until = current_time + self.config.cooldown_after_loss_seconds
                else:
                    self._consecutive_losses = 0

        cutoff_time = current_time - 86400
        self._pnl_history = [(t, p) for t, p in self._pnl_history if t > cutoff_time]
        self._daily_pnl = sum(float(p) for _, p in self._pnl_history)

    def _check_risk_controls(self) -> bool:
        current_time = self.market_data_provider.time()
        if abs(self._daily_pnl) > float(self.config.daily_max_loss_pct) * float(self.config.total_amount_quote):
            return False
        if self._consecutive_losses >= self.config.max_consecutive_losses:
            return False
        if current_time < self._cooldown_until:
            return False
        return True

    def _check_executor_timeout(self) -> List[ExecutorAction]:
        actions = []
        current_time = self.market_data_provider.time()
        active_executors = [e for e in self.executors_info if e.status == RunnableStatus.RUNNING]
        for executor in active_executors:
            if current_time - executor.timestamp > self.config.executor_timeout_seconds:
                actions.append(StopExecutorAction(
                    controller_id=self.config.id,
                    executor_id=executor.id,
                ))
        return actions

    def determine_executor_actions(self) -> List[ExecutorAction]:
        self._update_risk_state()
        actions = self._check_executor_timeout()

        if not self._check_risk_controls():
            return actions

        signal = self.processed_data.get("signal", 0)
        if signal == 0:
            return actions

        active_count = len([e for e in self.executors_info if e.status == RunnableStatus.RUNNING])
        if active_count >= self.config.max_open_positions:
            return actions

        current_time = self.market_data_provider.time()
        if current_time - self._last_executor_created_timestamp < self.config.delay_between_executors:
            return actions

        if signal == 1:
            buying_market = self.config.connector_pair_b
            selling_market = self.config.connector_pair_a
        elif signal == -1:
            buying_market = self.config.connector_pair_a
            selling_market = self.config.connector_pair_b

        executor_config = ArbitrageExecutorConfig(
            timestamp=current_time,
            buying_market=buying_market,
            selling_market=selling_market,
            order_amount=self.config.order_amount,
            min_profitability=self.config.min_profitability,
        )

        actions.append(CreateExecutorAction(
            executor_config=executor_config,
            controller_id=self.config.id,
        ))
        self._last_executor_created_timestamp = current_time
        return actions

    def to_format_status(self) -> List[str]:
        lines = [
            f"Spread Spike Arb | Signal: {self.processed_data.get('signal', 0)} | "
            f"Spread: {self.processed_data.get('spread_bps', 0):.1f} bps | "
            f"Z-Score: {self.processed_data.get('z_score', 0):.2f}",
            f"Risk: Daily PnL: {self._daily_pnl:.4f} | "
            f"Consecutive Losses: {self._consecutive_losses} | "
            f"Cooldown Until: {self._cooldown_until}",
        ]
        return lines