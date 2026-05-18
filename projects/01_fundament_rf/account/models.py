import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AssetBalance:
    coin: str
    total: float
    available: float
    frozen: float
    locked: float = 0.0

    @property
    def in_usdt(self) -> bool:
        return self.coin == 'USDT'


@dataclass
class MixAccount:
    margin_coin: str
    equity: float
    usdt_equity: float
    available: float
    locked: float
    unrealized_pl: float
    unrealized_pl_ratio: float
    margin_mode: str


@dataclass
class Position:
    symbol: str
    margin_size: float
    open_price_avg: float
    unrealized_pl: float
    c_time: int
    leverage: float
    liquidation_price: float
    available: float
    hold_side: str = 'long'
    achieved_profits: float = 0.0
    total_coin: float = 0.0
    total_fee: float = 0.0
    mark_price: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    position_id: str = ''

    @property
    def pl_percent(self) -> float:
        if self.margin_size == 0:
            return 0.0
        return (self.unrealized_pl / self.margin_size) * 100

    @property
    def position_value_usdt(self) -> float:
        return self.total_coin * self.current_price

    @property
    def is_profitable(self) -> bool:
        return self.unrealized_pl >= 0

    @property
    def ticker(self) -> str:
        return self.symbol.replace('USDT', '')

    @property
    def current_price(self) -> float:
        if self.mark_price:
            return self.mark_price
        if self.margin_size == 0:
            return self.open_price_avg
        return self.open_price_avg + (self.unrealized_pl / self.margin_size)

    @property
    def risk_to_liquidation(self) -> float:
        if self.liquidation_price <= 0:
            return 0
        diff_percent = abs((self.current_price - self.liquidation_price) / self.current_price) * 100
        return diff_percent

    @property
    def open_date(self) -> str:
        return datetime.datetime.fromtimestamp(self.c_time / 1000).strftime('%Y-%m-%d')

    @property
    def days_open(self) -> int:
        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.c_time / 1000)
        return max(0, int(delta.total_seconds() // (24 * 3600)))

    @property
    def has_sl(self) -> bool:
        return self.stop_loss_price > 0

    @property
    def has_tp(self) -> bool:
        return self.take_profit_price > 0

    @property
    def sl_distance_pct(self) -> Optional[float]:
        if self.stop_loss_price and self.open_price_avg:
            return ((self.stop_loss_price - self.open_price_avg) / self.open_price_avg) * 100
        return None

    @property
    def tp_distance_pct(self) -> Optional[float]:
        if self.take_profit_price and self.open_price_avg:
            return ((self.take_profit_price - self.open_price_avg) / self.open_price_avg) * 100
        return None


@dataclass
class Order:
    order_id: str
    symbol: str
    price: float
    quantity: float
    order_type: str
    side: str
    status: str
    c_time: int
    client_oid: str = ''
    filled_qty: float = 0.0

    @property
    def ticker(self) -> str:
        return self.symbol.replace('USDT', '')


@dataclass
class Fill:
    order_id: str
    symbol: str
    price: float
    quantity: float
    filled_qty: float
    fee_ccy: str
    fee_detail: float
    side: str
    c_time: int
    market: str = 'futures'
    profit: float = 0.0
    quote_volume: float = 0.0
    trade_side: str = ''
    trade_scope: str = ''

    @property
    def ticker(self) -> str:
        return self.symbol.replace('USDT', '')

    @property
    def total_value(self) -> float:
        return self.price * self.filled_qty


@dataclass
class ApiStatus:
    connected: bool
    server_time: int
    latency_ms: float
    error: str = ''


@dataclass
class AccountOverview:
    total_equity_usdt: float = 0.0
    spot_total_usdt: float = 0.0
    futures_equity_usdt: float = 0.0
    futures_unrealized_pl: float = 0.0
    open_positions_count: int = 0
    open_orders_count: int = 0
    spot_assets: List[AssetBalance] = field(default_factory=list)
    mix_accounts: List[MixAccount] = field(default_factory=list)
    error: str = ''
