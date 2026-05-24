import os
import hashlib
import hmac
import base64
import time
import requests
from typing import Dict, List, Any, Optional

from .models import AssetBalance, MixAccount, Position, Order, Fill, AccountOverview, ApiStatus

BASE_URL = "https://api.bitget.com"

# Module-level server time cache to avoid extra HTTP round-trip (~340ms) per signed request
_time_cache = {"offset": 0, "cached_at": 0}
_TIME_TTL = 30


class BitgetAccountClient:
    def __init__(self, api_key: str = None, secret_key: str = None, passphrase: str = None):
        self.api_key = api_key or os.environ.get('BITGET_API_KEY', '')
        self.secret_key = secret_key or os.environ.get('BITGET_SECRET_KEY', '')
        self.passphrase = passphrase or os.environ.get('BITGET_PASSPHRASE', '')
        self.base_url = BASE_URL
        self.session = requests.Session()

    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.secret_key and self.passphrase)

    def _get_server_time(self) -> int:
        global _time_cache
        now = time.time()
        if now - _time_cache["cached_at"] < _TIME_TTL:
            return int(now * 1000) + _time_cache["offset"]
        try:
            resp = self.session.get(f"{self.base_url}/api/v2/public/time", timeout=5)
            resp.raise_for_status()
            st = int(resp.json()['data']['serverTime'])
            _time_cache = {"offset": st - int(now * 1000), "cached_at": now}
            return st
        except requests.RequestException:
            return int(now * 1000) + _time_cache["offset"]

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
        }

    def _signed_get(self, endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
        if not self.has_credentials:
            return {"code": "99999", "data": [], "msg": "API credentials not configured"}
        query_string = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        timestamp = str(self._get_server_time())
        signature = self._generate_signature(timestamp, "GET", endpoint, query_string)
        headers = self._get_headers(timestamp, signature)
        url = f"{self.base_url}{endpoint}"
        if query_string:
            url += f"?{query_string}"
        try:
            resp = self.session.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"code": "99999", "data": [], "msg": str(e)}

    def check_status(self) -> ApiStatus:
        t0 = time.time()
        try:
            resp = self.session.get(f"{self.base_url}/api/v2/public/time", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            server_time = data['data']['serverTime']
            latency = (time.time() - t0) * 1000
            if not self.has_credentials:
                return ApiStatus(connected=False, server_time=server_time, latency_ms=round(latency, 1), error="No API keys set")
            return ApiStatus(connected=True, server_time=server_time, latency_ms=round(latency, 1))
        except Exception as e:
            return ApiStatus(connected=False, server_time=0, latency_ms=0, error=str(e))

    def test_auth(self) -> ApiStatus:
        status = self.check_status()
        if not status.connected:
            return status
        t0 = time.time()
        result = self._signed_get("/api/v2/spot/account/assets")
        latency = (time.time() - t0) * 1000
        ok = result.get('code') == '00000'
        return ApiStatus(
            connected=ok,
            server_time=result.get('requestTime', 0),
            latency_ms=round(latency, 1),
            error='' if ok else result.get('msg', 'Auth failed')
        )

    def get_spot_assets(self, coin: str = None) -> List[AssetBalance]:
        params = {}
        if coin:
            params['coin'] = coin
        result = self._signed_get("/api/v2/spot/account/assets", params)
        if result.get('code') != '00000':
            return []
        items = []
        for item in result.get('data', []):
            try:
                available = float(item.get('available', 0))
                frozen = float(item.get('frozen', 0))
                locked = float(item.get('locked', 0))
                items.append(AssetBalance(
                    coin=item.get('coin', ''),
                    total=available + frozen + locked,
                    available=available,
                    frozen=frozen,
                    locked=locked,
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_mix_accounts(self) -> List[MixAccount]:
        result = self._signed_get("/api/v2/mix/account/accounts", {"productType": "USDT-FUTURES"})
        if result.get('code') != '00000':
            return []
        items = []
        for item in result.get('data', []):
            try:
                items.append(MixAccount(
                    margin_coin=item.get('marginCoin', ''),
                    equity=float(item.get('equity', 0)),
                    usdt_equity=float(item.get('usdtEquity', 0)),
                    available=float(item.get('available', 0)),
                    locked=float(item.get('locked', 0)),
                    unrealized_pl=float(item.get('unrealizedPL', 0)),
                    unrealized_pl_ratio=float(item.get('unrealizedPnlRation', 0)),
                    margin_mode=item.get('marginMode', ''),
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_positions(self, product_type: str = "USDT-FUTURES", margin_coin: str = None) -> List[Position]:
        params = {"productType": product_type}
        if margin_coin:
            params["marginCoin"] = margin_coin
        result = self._signed_get("/api/v2/mix/position/all-position", params)
        if result.get('code') != '00000':
            return []
        items = []
        for item in result.get('data', []):
            try:
                items.append(Position(
                    symbol=item.get('symbol', ''),
                    margin_size=float(item.get('marginSize', 0)),
                    open_price_avg=float(item.get('openPriceAvg', 0)),
                    unrealized_pl=float(item.get('unrealizedPL', 0)),
                    c_time=int(item.get('cTime', 0)),
                    leverage=float(item.get('leverage', 0)),
                    liquidation_price=float(item.get('liquidationPrice', 0)),
                    available=float(item.get('available', 0)),
                    hold_side=item.get('holdSide', 'long'),
                    achieved_profits=float(item.get('achievedProfits', 0)),
                    total_coin=float(item.get('total', 0)),
                    total_fee=float(item.get('totalFee', 0)),
                    mark_price=float(item.get('markPrice', 0)),
                    stop_loss_price=float(item.get('stopLoss', 0) or 0),
                    take_profit_price=float(item.get('takeProfit', 0) or 0),
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_spot_orders(self, symbol: str = None) -> List[Order]:
        params = {}
        if symbol:
            params['symbol'] = symbol
        result = self._signed_get("/api/v2/spot/trade/unfilled-orders", params)
        if result.get('code') != '00000':
            return []
        items = []
        for item in result.get('data', []):
            try:
                items.append(Order(
                    order_id=item.get('orderId', ''),
                    symbol=item.get('symbol', ''),
                    price=float(item.get('price', 0)),
                    quantity=float(item.get('quantity', 0)),
                    order_type=item.get('orderType', ''),
                    side=item.get('side', ''),
                    status=item.get('status', ''),
                    c_time=int(item.get('cTime', 0)),
                    client_oid=item.get('clientOid', ''),
                    filled_qty=float(item.get('filledQty', 0)),
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_mix_orders(self, symbol: str = None) -> List[Order]:
        params = {"productType": "USDT-FUTURES"}
        if symbol:
            params['symbol'] = symbol
        result = self._signed_get("/api/v2/mix/order/orders-pending", params)
        if result.get('code') != '00000':
            return []
        data = result.get('data', {})
        if isinstance(data, dict):
            items_data = data.get('entrustedList', [])
        elif isinstance(data, list):
            items_data = data
        else:
            items_data = []
        items = []
        for item in items_data:
            try:
                items.append(Order(
                    order_id=item.get('orderId', ''),
                    symbol=item.get('symbol', ''),
                    price=float(item.get('price', 0)),
                    quantity=float(item.get('size', 0)),
                    order_type=item.get('orderType', ''),
                    side=item.get('side', ''),
                    status=item.get('status', ''),
                    c_time=int(item.get('cTime', 0)),
                    client_oid=item.get('clientOid', ''),
                    filled_qty=float(item.get('baseVolume', 0)),
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_spot_fills(self, symbol: str = None, limit: int = 20) -> List[Fill]:
        params = {}
        if symbol:
            params['symbol'] = symbol
        result = self._signed_get("/api/v2/spot/trade/fills", params)
        if result.get('code') != '00000':
            return []
        data = result.get('data', [])
        if isinstance(data, list):
            data = data[:limit]
        items = []
        for item in data:
            try:
                items.append(Fill(
                    order_id=item.get('orderId', ''),
                    symbol=item.get('symbol', ''),
                    price=float(item.get('price', 0)),
                    quantity=float(item.get('quantity', 0)),
                    filled_qty=float(item.get('filledQty', 0)),
                    fee_ccy=item.get('feeCcy', ''),
                    fee_detail=float(item.get('feeDetail', 0)),
                    side=item.get('side', ''),
                    c_time=int(item.get('cTime', 0)),
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_mix_fills(self, symbol: str = None, limit: int = 20) -> List[Fill]:
        params = {"productType": "USDT-FUTURES"}
        if symbol:
            params['symbol'] = symbol
        result = self._signed_get("/api/v2/mix/order/fills", params)
        if result.get('code') != '00000':
            return []
        data = result.get('data', {})
        if isinstance(data, dict):
            items_data = data.get('fillList', [])
        elif isinstance(data, list):
            items_data = data
        else:
            items_data = []
        items = []
        for item in items_data[:limit]:
            try:
                fee_detail = item.get('feeDetail', [])
                if isinstance(fee_detail, list) and fee_detail:
                    fee_coin = fee_detail[0].get('feeCoin', '')
                    fee_amount = float(fee_detail[0].get('totalFee', 0))
                else:
                    fee_coin = ''
                    fee_amount = 0.0
                items.append(Fill(
                    order_id=item.get('orderId', ''),
                    symbol=item.get('symbol', ''),
                    price=float(item.get('price', 0)),
                    quantity=float(item.get('baseVolume', 0)),
                    filled_qty=float(item.get('baseVolume', 0)),
                    fee_ccy=fee_coin,
                    fee_detail=abs(fee_amount),
                    side=item.get('side', ''),
                    c_time=int(item.get('cTime', 0)),
                ))
            except (ValueError, TypeError):
                continue
        return items

    def get_raw(self, endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
        return self._signed_get(endpoint, params)

    def _parse_fill(self, item: dict, market: str) -> Optional[Fill]:
        try:
            fee_detail = item.get('feeDetail', [])
            if isinstance(fee_detail, list) and fee_detail:
                fee_coin = fee_detail[0].get('feeCoin', '')
                fee_amount = abs(float(fee_detail[0].get('totalFee', 0)))
            else:
                fee_coin = item.get('feeCcy', '')
                fee_amount = abs(float(item.get('feeDetail', 0) or 0))
            qty = float(item.get('baseVolume', item.get('filledQty', 0)))
            return Fill(
                order_id=item.get('orderId', ''),
                symbol=item.get('symbol', ''),
                price=float(item.get('price', 0)),
                quantity=qty,
                filled_qty=qty,
                fee_ccy=fee_coin,
                fee_detail=fee_amount,
                side=item.get('side', ''),
                c_time=int(item.get('cTime', 0)),
                market=market,
                profit=float(item.get('profit', 0)),
                quote_volume=float(item.get('quoteVolume', 0)),
                trade_side=item.get('tradeSide', ''),
                trade_scope=item.get('tradeScope', ''),
            )
        except (ValueError, TypeError):
            return None

    def _fetch_fills_paginated(self, endpoint: str, params: dict = None, since: int = None) -> list:
        all_items = []
        cursor = None
        while True:
            req_params = dict(params or {})
            req_params['limit'] = '100'
            if since:
                req_params['startTime'] = str(since)
            if cursor:
                req_params['idLessThan'] = cursor
            result = self._signed_get(endpoint, req_params)
            if result.get('code') != '00000':
                break
            data = result.get('data', {})
            if isinstance(data, dict):
                items = data.get('fillList', [])
            elif isinstance(data, list):
                items = data
            else:
                break
            if not items:
                break
            all_items.extend(items)
            cursor = items[-1].get('tradeId', '')
            if not cursor:
                break
        return all_items

    def fetch_all_fills(self, market: str = 'all', since: int = None) -> dict:
        fills = []
        spot_total = 0
        futures_total = 0
        if market in ('all', 'spot'):
            raw = self._fetch_fills_paginated('/api/v2/spot/trade/fills', since=since)
            spot_total = len(raw)
            for item in raw:
                f = self._parse_fill(item, 'spot')
                if f:
                    fills.append(f)
        if market in ('all', 'futures'):
            raw = self._fetch_fills_paginated('/api/v2/mix/order/fills',
                params={'productType': 'USDT-FUTURES'}, since=since)
            futures_total = len(raw)
            for item in raw:
                f = self._parse_fill(item, 'futures')
                if f:
                    fills.append(f)
        return {'fills': fills, 'spot_total': spot_total, 'futures_total': futures_total, 'grand_total': spot_total + futures_total}

    def get_overview(self) -> AccountOverview:
        overview = AccountOverview()
        overview.spot_assets = self.get_spot_assets()
        for a in overview.spot_assets:
            if a.coin == 'USDT':
                overview.spot_total_usdt += a.total
            else:
                overview.spot_total_usdt += a.total
        overview.mix_accounts = self.get_mix_accounts()
        for m in overview.mix_accounts:
            overview.futures_equity_usdt += m.usdt_equity
            overview.futures_unrealized_pl += m.unrealized_pl
        overview.total_equity_usdt = overview.spot_total_usdt + overview.futures_equity_usdt
        overview.open_positions_count = len(self.get_positions())
        return overview
