#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BITGET POSITION CHECKER
Форматы:
  emoji_entry: 🏗️ [number] 🚏[symbol] 🧾[entry] 📆[date] 🕒[days] 🧱[vol] 📈[%] 🫧[$] 📦[result]
  emoji_upd:   🏗️ [number] 🚏[symbol] 🧾[current] 📆[date] 🕒[days] 🧱[vol] 📈[%] 🫧[$] 📦[result]
"""
import sys
import io
import os
import hashlib
import hmac
import base64
import requests
import datetime
import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from functools import lru_cache
from functools import cached_property

API_KEY = "bg_"
SECRET_KEY = "43"
PASSPHRASE = "sk"
BASE_URL = "https://api.bitget.com"
ENDPOINT = "/api/v2/mix/position/all-position"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

class BitgetAPIClient:
    def __init__(self, api_key: str, secret_key: str, passphrase: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = base_url
        self.session = requests.Session()

    def _get_server_time(self) -> int:
        try:
            response = self.session.get(f"{self.base_url}/api/v2/public/time", timeout=5)
            response.raise_for_status()
            return response.json()['data']['serverTime']
        except requests.RequestException:
            return int(datetime.datetime.now().timestamp() * 1000)

    def _generate_signature(self, timestamp: str, method: str, endpoint: str, query_string: str = "") -> str:
        message = timestamp + method.upper() + endpoint
        if query_string:
            message += "?" + query_string
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    def _get_headers(self, timestamp: str, signature: str) -> Dict[str, str]:
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "User-Agent": "Bitget-Position-Checker/1.0"
        }

    def get_positions(self, product_type: str = "USDT-FUTURES", margin_coin: str = None) -> Dict[str, Any]:
        query_params = [f"productType={product_type}"]
        if margin_coin:
            query_params.append(f"marginCoin={margin_coin}")
        query_string = "&".join(query_params)
        timestamp = str(self._get_server_time())
        signature = self._generate_signature(timestamp, "GET", ENDPOINT, query_string)
        headers = self._get_headers(timestamp, signature)
        url = f"{self.base_url}{ENDPOINT}?{query_string}"
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"code": "99999", "data": [], "msg": str(e)}

@dataclass
class OrderData:
    """Данные ордера с формулами PnL как в fundament_rf"""
    symbol: str
    margin_size: float       # 🧱 volume (Объём)
    unrealized_pl: float    # 🫧 PnL в $ (от API)
    c_time: int
    total_fee: float
    open_price_avg: float  # 🧾 entry_price (Цена покупки)
    available: float
    position_id: str = ""  # 🏗️ number
    hold_side: str = "long"  # 🔼 long / 🔽 short

    @property
    def pl_percent(self) -> float:
        """PnL% = (Текущая - Вход) / Вход × 100"""
        if self.margin_size == 0 or self.open_price_avg == 0:
            return 0.0
        # PnL% = (PnL$ / (Вход × Объём)) × 100
        entry_total = self.open_price_avg * self.margin_size
        if entry_total == 0:
            return 0.0
        return (self.unrealized_pl / entry_total) * 100

    @property
    def is_profitable(self) -> bool:
        return self.unrealized_pl >= 0

    @cached_property
    def open_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.c_time / 1000)

    @cached_property
    def days_open(self) -> int:
        delta = datetime.datetime.now() - self.open_datetime
        return int(delta.total_seconds() // (24 * 3600))

    @cached_property
    def open_date(self) -> str:
        return self.open_datetime.date().isoformat()

    @property
    def current_price(self) -> float:
        """Текущая цена = Вход + (PnL$ / Объём)"""
        if self.margin_size == 0:
            return self.open_price_avg
        return self.open_price_avg + (self.unrealized_pl / self.margin_size)

    @property
    def current_date(self) -> str:
        """Текущая дата"""
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @property
    def days_diff(self) -> int:
        """Разница в днях (для emoji_upd)"""
        return self.days_open

    @property
    def side_emoji(self) -> str:
        return "🔼" if self.hold_side == "long" else "🔽"

    @property
    def emoji_entry_line(self) -> str:
        """emoji_entry: 🏗️[number] 🚏[symbol] 🔼/🔽 🧾[entry] 📆[date] 🕒[days] 🧱[vol] 📈[%] 🫧[$] 📦[result]"""
        ticker = self.symbol.replace("USDT", "")
        result_emoji = "🟢" if self.is_profitable else "🔴"
        trend_emoji = "📈" if self.pl_percent >= 0 else "📉"
        return (
            f"🏗️{self.position_id} "
            f"🚏{ticker} "
            f"{self.side_emoji} "
            f"🧾{self.open_price_avg:.5f} "
            f"📆{self.open_date} "
            f"🕒{self.days_open} "
            f"🧱{self.margin_size:.2f} "
            f"{trend_emoji}{self.pl_percent:+.2f} "
            f"🫧{self.unrealized_pl:+.2f} "
            f"📦{result_emoji}"
        )

    @property
    def emoji_upd_line(self) -> str:
        """emoji_upd: 🏗️[number] 🚏[symbol] 🔼/🔽 🧾[current] 📆[date] 🕒[days] 🧱[vol] 📈[%*leverage] 🪙[$ raw] 📦[result] ⬆️[leverage]"""
        ticker = self.symbol.replace("USDT", "")
        result_emoji = "🟢" if self.is_profitable else "🔴"
        trend_emoji = "📈" if self.pl_percent >= 0 else "📉"
        current_price = self.current_price
        current_date = self.current_date
        days_diff = self.days_diff
        leverage = 10  # Плечо
        
        # PnL% БЕЗ плеча (для формулы)
        if self.open_price_avg > 0:
            pnl_pct_raw = ((current_price - self.open_price_avg) / self.open_price_avg) * 100
        else:
            pnl_pct_raw = 0.0
        
        # 📈 PnL% С плечом (pnl_pct_raw × leverage)
        pnl_pct_leveraged = pnl_pct_raw * leverage
        
        # 🪙 PnL$ БЕЗ плеча (сырой, как просил пользователь)
        pnl_usdt_raw = (current_price * self.margin_size) - (self.open_price_avg * self.margin_size)
        
        return (
            f"🏗️{self.position_id} "
            f"🚏{ticker} "
            f"{self.side_emoji} "
            f"🧾{current_price:.5f} "
            f"📆{current_date} "
            f"🕒{days_diff} "
            f"🧱{self.margin_size:.2f} "
            f"{trend_emoji}{pnl_pct_leveraged:+.1f}% "
            f"🪙{pnl_usdt_raw:+.2f}$ "
            f"📦{result_emoji} ⬆️{leverage}"
        )


class TelegramOrderProcessor:
    def __init__(self, json_response: Dict[str, Any]):
        self.data = json_response.get('data', [])
        self.orders: List[OrderData] = []
        self.stats = {
            'total_pl': 0.0,
            'positive_pl': 0.0,
            'negative_pl': 0.0,
            'positive_count': 0,
            'negative_count': 0,
            'total_count': 0,
            'available_balance': 0.0,
        }
        self._parse_orders()
        if self.orders:
            self.stats['available_balance'] = self.orders[0].available
        self.stats['total_count'] = len(self.orders)

    def _parse_orders(self) -> None:
        if not self.data:
            return
        for idx, item in enumerate(self.data, 1):
            try:
                order = OrderData(
                    symbol=item.get('symbol', ''),
                    margin_size=float(item.get('marginSize', 0)),
                    unrealized_pl=float(item.get('unrealizedPL', 0)),
                    c_time=int(item.get('cTime', 0)),
                    total_fee=float(item.get('totalFee', 0)),
                    open_price_avg=float(item.get('openPriceAvg', 0)),
                    available=float(item.get('available', 0)),
                    position_id=str(idx),
                    hold_side=item.get('holdSide', 'long'),
                )
                self.orders.append(order)
                self.stats['total_pl'] += order.unrealized_pl
                if order.is_profitable:
                    self.stats['positive_pl'] += order.unrealized_pl
                    self.stats['positive_count'] += 1
                else:
                    self.stats['negative_pl'] += order.unrealized_pl
                    self.stats['negative_count'] += 1
            except (ValueError, TypeError) as e:
                continue

    def generate_message(self) -> str:
        if not self.orders:
            return "📭 Нет открытых позиций"
        lines = []
        lines.append(f"📋 Позиций: {self.stats['total_count']}")
        lines.append("")
        lines.append("=== emoji_entry (ввод) ===")
        for order in self.orders:
            lines.append(order.emoji_entry_line)
        lines.append("")
        lines.append("=== emoji_upd (актуально) ===")
        for order in self.orders:
            lines.append(order.emoji_upd_line)
        lines.append("")
        lines.extend(self._generate_aggregate_summary())
        lines.append(f"🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return '\n'.join(lines)

    def _generate_aggregate_summary(self) -> List[str]:
        pl_p = abs(self.stats['positive_pl'])
        pl_n = -abs(self.stats['negative_pl'])
        all_pl = pl_p + pl_n
        return [
            f"🟢 Доход:   {pl_p:+7.2f} [{self.stats['positive_count']}]",
            f"🔴 Убыток:  {pl_n:+7.2f} [{self.stats['negative_count']}]",
            "──────────────────────",
            f"📊 Итого:   {all_pl:+7.2f}",
            f"💰 Баланс:  {self.stats['available_balance']:7.2f}",
            f"📋 Позиций: {self.stats['total_count']}"
        ]

    def save_to_file(self, filename: str = "orders_tg.log") -> Dict[str, int]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        content = self.generate_message()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"🕒 {timestamp}\n{content}\n\n")
        return {
            'characters': len(content),
            'lines': content.count('\n') + 1,
            'orders': len(self.orders),
            'timestamp': timestamp
        }

    def print_statistics(self) -> None:
        print(f"\n📊 СТАТИСТИКА ПОЗИЦИЙ:")
        print(f"   📋 Всего позиций: {self.stats['total_count']}")
        print(f"   🟢 Прибыльных: [{self.stats['positive_count']}] {self.stats['positive_pl']:+.2f} $")
        print(f"   🔴 Убыточных: [{self.stats['negative_count']}] {self.stats['negative_pl']:+.2f} $")
        print(f"   📈 Общий P/L: ${self.stats['total_pl']:+.2f}")
        print(f"   💰 Баланс: ${self.stats['available_balance']:.2f}")


def main():
    print("=" * 80)
    print("🔗 BITGET POSITION CHECKER")
    print("=" * 80)
    client = BitgetAPIClient(API_KEY, SECRET_KEY, PASSPHRASE)
    positions_data = client.get_positions()
    if positions_data.get('code') != '00000':
        print(f"   ❌ Ошибка API: {positions_data.get('msg', 'Unknown error')}")
        return
    processor = TelegramOrderProcessor(positions_data)
    if not processor.orders:
        print("📭 Нет открытых позиций для отображения")
        return
    formatted_message = processor.generate_message()
    print("\n" + "=" * 80)
    print("📋 РЕЗУЛЬТАТ:")
    print("=" * 80)
    print(formatted_message)
    print("=" * 80)
    processor.print_statistics()
    file_stats = processor.save_to_file()
    print(f"\n✅ Файл сохранен: orders_tg.log")
    print(f"📝 Строк: {file_stats['lines']}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Выполнение прервано пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
