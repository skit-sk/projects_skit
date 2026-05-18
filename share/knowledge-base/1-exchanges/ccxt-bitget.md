# ccxt Bitget Exchange — полный справочник API

## 1. Базовая конфигурация

| Параметр | Значение |
|----------|----------|
| ID | `bitget` |
| Страна | SG (Singapore) |
| Версия API | v2 |
| Rate limit | 50ms (3000 запросов/5 мин) |
| Сертифицирован | ✅ |
| Pro (WebSocket) | ✅ |
| Hostname | `bitget.com` |
| API URL | `https://api.bitget.com` |

### Требуемые credentials

```python
import ccxt
exchange = ccxt.bitget({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'password': 'YOUR_API_PASSWORD',
})
```

### Broker ID (по умолчанию)

```python
exchange.options['broker']  # 'p4sve'
```

### Sandbox mode

```python
exchange.set_sandbox_mode(True)
# Добавляет заголовок: PAPTRADING: 1
```

## 2. Доступные рынки и функции

### Рынки

| Рынок | Поддержка |
|-------|-----------|
| spot (спот) | ✅ |
| margin (маржинальная) | ✅ cross / isolated |
| swap (фьючерсы бессрочные) | ✅ |
| future (фьючерсы срочные) | ✅ |
| option (опционы) | ❌ |

### Timeframes для OHLCV

`1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w, 1M`

## 3. Полный список Unified API методов

### 3.1 Рыночные данные (public)

| Метод | Параметры | Возврат | URL документации |
|-------|-----------|---------|------------------|
| `fetchTime(params)` | — | `Int` | common |
| `fetchMarkets(params)` | — | `List[Market]` | spot/mix/uta |
| `fetchCurrencies(params)` | — | `Currencies` | spot |
| `fetchTicker(symbol, params)` | uta? | `Ticker` | spot/mix/uta |
| `fetchTickers(symbols?, params)` | uta?, subType?, productType? | `Tickers` | spot/mix/uta |
| `fetchMarkPrice(symbol, params)` | — | `Ticker` | mix |
| `fetchOrderBook(symbol, limit?, params)` | uta? | `OrderBook` | spot/mix/uta |
| `fetchTrades(symbol, since?, limit?, params)` | uta? | `List[Trade]` | spot/mix/uta |
| `fetchOHLCV(symbol, timeframe?, since?, limit?, params)` | uta?, until?, price?(mark/index), paginate? | `List[list]` | spot/mix/uta |
| `fetchTradingFee(symbol, params)` | — | `TradingFeeInterface` | spot |
| `fetchTradingFees(params)` | — | `TradingFees` | spot |
| `fetchMarketLeverageTiers(symbol, params)` | — | `List[LeverageTier]` | mix |

### 3.2 Баланс и счёт (private)

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `fetchBalance(params)` | uta?, productType?, marginMode? | `Balances` | spot/mix/margin/uta |
| `fetchLedger(code?, since?, limit?, params)` | paginate? | `List[LedgerEntry]` | spot |

### 3.3 Ордера (private)

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `createOrder(symbol, type, side, amount, price?, params)` | uta?, triggerPrice?, stopLossPrice?, takeProfitPrice?, timeInForce?, marginMode?, trailingPercent?, reduceOnly?, hedged? | `Order` | spot/mix/margin/uta |
| `createMarketBuyOrderWithCost(symbol, cost, params)` | — | `Order` | spot |
| `createOrders(orders, params)` | uta? | `list` | spot/mix/uta |
| `editOrder(id, symbol, type, side, amount?, price?, params)` | — | `Order` | spot/mix |
| `cancelOrder(id, symbol?, params)` | uta? | `Order` | spot/mix/uta |
| `cancelOrders(ids, symbol?, params)` | uta? | `list` | spot/mix |
| `cancelAllOrders(symbol?, params)` | — | `list` | spot/mix |
| `fetchOrder(id, symbol?, params)` | uta? | `Order` | spot/mix/uta |
| `fetchOpenOrders(symbol?, since?, limit?, params)` | uta?, trigger?, trailing?, paginate?, until?, planType? | `List[Order]` | spot/mix/uta |
| `fetchClosedOrders(symbol?, since?, limit?, params)` | uta?, paginate?, until? | `List[Order]` | spot/mix/uta |
| `fetchCanceledOrders(symbol?, since?, limit?, params)` | — | `List[Order]` | spot/mix |
| `fetchCanceledAndClosedOrders(symbol?, since?, limit?, params)` | uta?, paginate?, until? | `List[Order]` | spot/mix/uta |
| `fetchMyTrades(symbol?, since?, limit?, params)` | uta?, paginate?, until? | `List[Trade]` | spot/mix/uta |

### 3.4 Позиции (private)

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `fetchPosition(symbol, params)` | — | `Position` | mix |
| `fetchPositions(symbols?, params)` | uta? | `List[Position]` | mix/uta |
| `fetchPositionsHistory(symbols?, since?, limit?, params)` | — | `List[Position]` | mix |
| `closePosition(symbol, side?, params)` | — | `Order` | mix/uta |
| `closeAllPositions(params)` | — | `List[Position]` | mix/uta |
| `fetchMyLiquidations(symbol?, since?, limit?, params)` | — | `List[Liquidation]` | mix |

### 3.5 Фандинг (private)

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `fetchFundingRate(symbol, params)` | uta? | `FundingRate` | mix/uta |
| `fetchFundingRates(symbols?, params)` | uta? | `FundingRates` | mix/uta |
| `fetchFundingRateHistory(symbol?, since?, limit?, params)` | uta?, paginate? | `list` | mix/uta |
| `fetchFundingInterval(symbol, params)` | uta? | `FundingRate` | mix |
| `fetchFundingIntervals(symbols?, params)` | uta? | `FundingRates` | mix |
| `fetchFundingHistory(symbol?, since?, limit?, params)` | — | `List[FundingHistory]` | mix |
| `fetchOpenInterest(symbol, params)` | — | `OpenInterest` | mix/uta |

### 3.6 Кредитное плечо и маржа (private)

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `setLeverage(leverage, symbol?, params)` | — | `dict` | mix |
| `fetchLeverage(symbol, params)` | — | `Leverage` | mix |
| `setMarginMode(marginMode, symbol?, params)` | — | `dict` | mix |
| `fetchMarginMode(symbol, params)` | — | `MarginMode` | mix |
| `setPositionMode(hedged, symbol?, params)` | — | `dict` | mix |
| `addMargin(symbol, amount, params)` | — | `MarginModification` | mix |
| `reduceMargin(symbol, amount, params)` | — | `MarginModification` | mix |
| `borrowCrossMargin(code, amount, params)` | — | `dict` | margin |
| `borrowIsolatedMargin(symbol, code, amount, params)` | — | `dict` | margin |
| `repayCrossMargin(code, amount, params)` | — | `dict` | margin |
| `repayIsolatedMargin(symbol, code, amount, params)` | — | `dict` | margin |
| `fetchCrossBorrowRate(code, params)` | — | `CrossBorrowRate` | margin |
| `fetchIsolatedBorrowRate(symbol, params)` | — | `IsolatedBorrowRate` | margin |
| `fetchBorrowInterest(code?, symbol?, since?, limit?, params)` | — | `List[BorrowInterest]` | margin |

### 3.7 Финансы (депозиты, выводы, переводы)

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `fetchDepositAddress(code, params)` | — | `DepositAddress` | spot |
| `fetchDeposits(code?, since?, limit?, params)` | — | `List[Transaction]` | spot |
| `fetchWithdrawals(code?, since?, limit?, params)` | — | `List[Transaction]` | spot |
| `withdraw(code, amount, address, tag?, params)` | — | `Transaction` | spot |
| `transfer(code, amount, fromAccount, toAccount, params)` | — | `TransferEntry` | spot |
| `fetchTransfers(code?, since?, limit?, params)` | — | `List[TransferEntry]` | spot |
| `fetchDepositWithdrawFees(codes?, params)` | — | `dict` | spot |

### 3.8 Конвертация

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `fetchConvertCurrencies(params)` | — | `Currencies` | spot |
| `fetchConvertQuote(fromCode, toCode, amount?, params)` | — | `Conversion` | spot |
| `createConvertTrade(id, fromCode, toCode, amount?, params)` | — | `Conversion` | spot |
| `fetchConvertTradeHistory(code?, since?, limit?, params)` | — | `List[Conversion]` | spot |

### 3.9 Дополнительные

| Метод | Параметры | Возврат | URL |
|-------|-----------|---------|-----|
| `fetchLongShortRatioHistory(symbol?, timeframe?, since?, limit?, params)` | — | `List[LongShortRatio]` | mix |
| `fetchIndexOHLCV(symbol, timeframe?, since?, limit?, params)` | — | `List[list]` | mix |
| `fetchMarkOHLCV(symbol, timeframe?, since?, limit?, params)` | — | `List[list]` | mix |

## 4. Особенности API

### 4.1 UTA (Unified Trading Account)

Многие методы поддерживают `params.uta = True` для переключения на v3 API:

```python
# UTA режим (v3)
ticker = await exchange.fetchTicker('BTC/USDT', {'uta': True})
order = await exchange.createOrder('BTC/USDT', 'limit', 'buy', 0.01, 30000, {'uta': True})
```

Без uta — используется legacy v2 API (spot/mix).

### 4.2 productType

Определяет тип продукта для контрактов:

| productType | Описание |
|-------------|----------|
| `SPOT` | Спот |
| `USDT-FUTURES` | USDT фьючерсы |
| `USDC-FUTURES` | USDC фьючерсы |
| `COIN-FUTURES` | Coin-M фьючерсы |
| `SUSDT-FUTURES` | Симуляция USDT |
| `SUSDC-FUTURES` | Симуляция USDC |
| `SCOIN-FUTURES` | Симуляция Coin-M |
| `MARGIN` | Маржинальная торговля |

Автоматически определяется через `handle_product_type_and_params()`.

### 4.3 Пагинация

Поддерживается через `params.paginate`:

```python
# OHLCV — детерминированная
orders = await exchange.fetchOHLCV('BTC/USDT', '1h', since, limit, {'paginate': True})

# Ордера — курсорная
orders = await exchange.fetchOpenOrders('BTC/USDT', None, None, {'paginate': True})
```

### 4.4 Подпись запросов

```
Метод: HMAC-SHA256
Кодировка: base64
Строка подписи: timestamp + method + requestPath
Заголовки:
  - ACCESS-KEY
  - ACCESS-SIGN
  - ACCESS-TIMESTAMP
  - ACCESS-PASSPHRASE
  - X-CHANNEL-API-CODE (broker)
```

### 4.5 Баланс — 4 формата данных

В зависимости от типа счёта `fetchBalance()` возвращает разные структуры:

| Тип | Эндпоинт | Ключи |
|-----|----------|-------|
| spot | `v2/spot/account/assets` | available, frozen |
| swap | `v2/mix/account/accounts` | marginCoin, accountEquity |
| margin | `v2/margin/cross/isolated/assets` | totalAmount, borrow, interest |
| uta | `v3/account/assets` | equity, balance, available, debt, locked |

### 4.6 Обработка ошибок

Маппинг кодов ошибок Bitget на исключения ccxt:

| Код Bitget | ccxt исключение |
|------------|-----------------|
| `00000` | Успех |
| `40001` | `AuthenticationError` |
| `40002` | `PermissionDenied` |
| `40003` | `BadRequest` |
| `40004` | `InvalidOrder` |
| `40005` | `OrderNotFound` |
| `40006` | `InsufficientFunds` |
| `40007` | `RateLimitExceeded` |
| `40008` | `ExchangeNotAvailable` |
| `40009` | `OnMaintenance` |
| `40010` | `BadSymbol` |
| `40011` | `ArgumentsRequired` |

## 5. Примеры кода

### 5.1 Инициализация (публичный доступ)

```python
import ccxt.async_support as ccxt

exchange = ccxt.bitget()
markets = await exchange.load_markets()
print(markets.keys())
```

### 5.2 Инициализация (приватный доступ)

```python
import ccxt.async_support as ccxt

exchange = ccxt.bitget({
    'apiKey': 'your_api_key',
    'secret': 'your_secret',
    'password': 'your_api_password',
    'options': {
        'defaultType': 'swap',  # или 'spot'
    }
})
```

### 5.3 Fetch OHLCV

```python
# Спот
ohlcv = await exchange.fetchOHLCV('BTC/USDT', '1h', since=1700000000000, limit=100)
# Фьючерсы с mark price
mark_ohlcv = await exchange.fetchOHLCV('BTC/USDT:USDT', '1h', params={'price': 'mark'})
# UTA
uta_ohlcv = await exchange.fetchOHLCV('BTC/USDT', '1h', params={'uta': True})
```

### 5.4 Order Book

```python
ob = await exchange.fetchOrderBook('BTC/USDT', 50)
print(f"Bids: {ob['bids'][:3]}")
print(f"Asks: {ob['asks'][:3]}")
```

### 5.5 Создание ордера

```python
# Лимитный ордер (спот)
order = await exchange.createOrder('BTC/USDT', 'limit', 'buy', 0.01, 30000)

# Рыночный ордер (фьючерсы)
order = await exchange.createOrder('ETH/USDT:USDT', 'market', 'sell', 1)

# Триггер-ордер (stop-loss)
order = await exchange.createOrder(
    'BTC/USDT:USDT', 'limit', 'buy', 1, 25000,
    {'triggerPrice': 24000}
)

# Трейлинг стоп
order = await exchange.createOrder(
    'BTC/USDT:USDT', 'market', 'sell', 1,
    {'trailingPercent': 5, 'trailingTriggerPrice': 30000}
)
```

### 5.6 Работа с UTA

```python
params = {'uta': True}

# Баланс UTA
balance = await exchange.fetchBalance(params)

# Ордер в UTA
order = await exchange.createOrder('BTC/USDT', 'market', 'buy', 0.01, None, params)

# Открытые ордера UTA
open_orders = await exchange.fetchOpenOrders('BTC/USDT', params=params)
```

### 5.7 Маржинальная торговля

```python
# Кросс-маржинальный ордер
order = await exchange.createOrder(
    'BTC/USDT', 'limit', 'buy', 0.01, 30000,
    {'marginMode': 'cross', 'loanType': 'autoLoan'}
)

# Изолированная маржа
order = await exchange.createOrder(
    'BTC/USDT', 'market', 'buy', 0.01,
    {'marginMode': 'isolated'}
)
```

## 6. WebSocket (ccxt.pro)

### Публичные каналы

| Канал | URL |
|-------|-----|
| Tickers | `wss://ws.bitget.com/v2/ws/public` |
| Candlesticks | `wss://ws.bitget.com/v2/ws/public` |
| Depth (Order Book) | `wss://ws.bitget.com/v2/ws/public` |
| Trades | `wss://ws.bitget.com/v2/ws/public` |
| UTA Public | `wss://ws.bitget.com/v3/ws/public` |

### Приватные каналы

| Канал | URL |
|-------|-----|
| Positions | `wss://ws.bitget.com/v2/ws/private` |
| Orders | `wss://ws.bitget.com/v2/ws/private` |
| Fills | `wss://ws.bitget.com/v2/ws/private` |
| Account | `wss://ws.bitget.com/v2/ws/private` |
| UTA Private | `wss://ws.bitget.com/v3/ws/private` |

### Sandbox WebSocket

```
Публичный: wss://wspap.bitget.com/v2/ws/public
Приватный:  wss://wspap.bitget.com/v2/ws/private
UTA Public: wss://wspap.bitget.com/v3/ws/public
UTA Private: wss://wspap.bitget.com/v3/ws/private
```

## 7. Лимиты rate limit

Эндпоинты имеют веса (weight). По умолчанию 20 единиц на 1 секунду (IP/UID):

| Вес | Примеры | Лимит |
|-----|---------|-------|
| 1 | tickers, candles, orderbook | 20 запросов/с |
| 2 | fills, vip-level | 10 запросов/с |
| 4 | deposit-address, transfer | 5 запросов/с |
| 6.6667 | currencies | 3 запроса/с |
| 20 | account-info, all-account-balance | 1 запрос/с |
| 200 | sub-account-assets | 0.1 запроса/с |

## 8. Ссылки

- [Bitget API Docs (Spot)](https://www.bitget.com/api-doc/spot/intro)
- [Bitget API Docs (Contract)](https://www.bitget.com/api-doc/contract/intro)
- [Bitget API Docs (Margin)](https://www.bitget.com/api-doc/margin/intro)
- [Bitget API Docs (UTA)](https://www.bitget.com/api-doc/uta/intro)
- [ccxt документация](https://docs.ccxt.com)
- [ccxt Bitget exchange page](https://docs.ccxt.com/exchanges/bitget)
