# Account — CCXT-based реализация (Вариант 2)

## Обзор

Вместо прямых HTTP-запросов с HMAC-SHA256 подписью — использование библиотеки **CCXT**.

### Плюсы
- Меньше кода — CCXT сам подписывает запросы
- Единый интерфейс для разных бирж (не только Bitget)
- CCXT уже есть в зависимостях проекта
- Встроенная rate limiting

### Минусы
- Зависимость от библиотеки (версии, баги)
- Не все эндпоинты доступны через CCXT
- Снепшоты и кастомные данные сложнее

---

## 1. AccountClient (CCXT-based)

```python
import ccxt
from typing import List

class CCXTAccountClient:
    def __init__(self, api_key=None, secret=None, passphrase=None):
        self.config = {'enableRateLimit': True}
        if api_key:
            self.config['apiKey'] = api_key
        if secret:
            self.config['secret'] = secret
        if passphrase:
            self.config['passphrase'] = passphrase
        self._exchange = None

    @property
    def exchange(self):
        if self._exchange is None:
            self._exchange = ccxt.bitget(self.config)
        return self._exchange

    def has_credentials(self) -> bool:
        return bool(
            self.config.get('apiKey')
            and self.config.get('secret')
            and self.config.get('passphrase')
        )

    def fetch_spot_balance(self) -> dict:
        """ccxt: exchange.fetch_balance() — возвращает {'USDT': {'free': ..., 'used': ..., 'total': ...}, ...}"""
        return self.exchange.fetch_balance({'type': 'spot'})

    def fetch_futures_balance(self) -> dict:
        return self.exchange.fetch_balance({'type': 'future'})

    def fetch_positions(self, symbols=None) -> list:
        """ccxt: exchange.fetch_positions(symbols) — список позиций"""
        return self.exchange.fetch_positions(symbols)

    def fetch_open_orders(self, symbol=None) -> list:
        return self.exchange.fetch_open_orders(symbol)

    def fetch_my_trades(self, symbol=None, since=None, limit=20) -> list:
        return self.exchange.fetch_my_trades(symbol, since, limit)
```

### Формат данных CCXT

**balance:**
```python
{
    'USDT': {'free': 100.0, 'used': 50.0, 'total': 150.0},
    'BTC':  {'free': 0.1, 'used': 0.0, 'total': 0.1},
    ...
}
```

**position:**
```python
{
    'symbol': 'BTC/USDT',
    'entryPrice': 42000.0,
    'markPrice': 43000.0,
    'contracts': 0.1,
    'collateral': 420.0,
    'unrealizedPnl': 100.0,
    'percentage': 23.8,
    'leverage': 10,
    'liquidationPrice': 38000.0,
    'side': 'long',
    'timestamp': 1705312800000,
}
```

**order:**
```python
{
    'id': '123456',
    'symbol': 'BTC/USDT',
    'type': 'limit',
    'side': 'buy',
    'price': 42000.0,
    'amount': 0.1,
    'filled': 0.05,
    'status': 'open',
    'timestamp': 1705312800000,
}
```

---

## 2. Модели

Те же dataclasses, что и в базовом варианте (`AssetBalance`, `Position`, `Order`, `Fill`), но с дополнительным конструктором `from_ccxt_*`:

```python
@classmethod
def from_ccxt_balance(cls, ccxt_data: dict) -> List['AssetBalance']:
    items = []
    for coin, data in ccxt_data.items():
        if isinstance(data, dict) and 'total' in data:
            items.append(cls(
                coin=coin,
                total=data.get('total', 0) or 0,
                available=data.get('free', 0) or 0,
                frozen=(data.get('total', 0) or 0) - (data.get('free', 0) or 0),
            ))
    return items

@classmethod
def from_ccxt_position(cls, pos: dict) -> 'Position':
    return cls(
        symbol=pos['symbol'].replace('/', ''),
        margin_size=pos.get('contracts', 0),
        open_price_avg=pos.get('entryPrice', 0),
        unrealized_pl=pos.get('unrealizedPnl', 0),
        c_time=pos.get('timestamp', 0),
        leverage=pos.get('leverage', 10),
        liquidation_price=pos.get('liquidationPrice', 0),
        available=pos.get('collateral', 0),
    )
```

---

## 3. Эндпоинты

Те же, что в базовом варианте:

| Эндпоинт | CCXT метод |
|----------|-----------|
| `/account-api/api/status` | `exchange.fetch_time()` + test auth |
| `/account-api/api/overview` | `fetch_balance()` + `fetch_positions()` |
| `/account-api/api/balance` | `fetch_balance()` дважды (spot, future) |
| `/account-api/api/positions` | `fetch_positions()` |
| `/account-api/api/orders` | `fetch_open_orders()` |
| `/account-api/api/fills` | `fetch_my_trades()` |

---

## 4. Ключи API

Через CCXT прокси (уже работает в `routes/ccxt_api.py`):
- Из `.env` через `os.environ.get('BITGET_API_KEY')`
- Из тела запроса (переопределение)

---

## 5. Отличия от базового (raw API) варианта

| Аспект | Raw API (реализовано) | CCXT (этот план) |
|--------|----------------------|-------------------|
| Подпись | HMAC-SHA256 вручную | Автоматически CCXT |
| Rate limit | Вручную | Встроенный `enableRateLimit` |
| Позиции | `/api/v2/mix/position/all-position` | `fetch_positions()` |
| Спот баланс | `/api/v2/account/assets` | `fetch_balance({'type':'spot'})` |
| Формат данных | Сырой JSON → dataclass | CCXT нормализованный → dataclass |
| Обработка ошибок | `_signed_get` обёртка | try/except вокруг CCXT методов |
| Зависимости | requests | ccxt (уже есть) |
| Универсальность | Только Bitget | Любая биржа CCXT |

---

## 6. Переход

Можно сделать **гибрид**: новый `CCXTAccountClient` реализует общий интерфейс:

```python
class AccountClientInterface(ABC):
    def check_status(self) -> ApiStatus: ...
    def get_overview(self) -> AccountOverview: ...
    def get_spot_assets(self) -> List[AssetBalance]: ...
    def get_positions(self) -> List[Position]: ...
    def get_orders(self) -> List[Order]: ...
    def get_fills(self) -> List[Fill]: ...
```

- `BitgetAccountClient` — реализует через raw API
- `CCXTAccountClient` — реализует через CCXT

Переключение через `ACCOUNT_CLIENT_BACKEND=raw|ccxt` в `.env`.
