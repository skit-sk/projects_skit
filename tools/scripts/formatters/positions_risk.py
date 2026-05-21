"""Risk Summary formatter — Rich Table → plain text for Telegram."""

from rich.table import Table
from rich.console import Console
from io import StringIO

WIDTH = 100


def _roe_emoji(val: float) -> str:
    """7-цветная шкала для ROE% и ROR%."""
    if val >= 100:      return "🔮"
    if val >= 30:       return "💚"
    if val >= 5:        return "🟢"
    if val >= -5:       return "⚪"
    if val >= -30:      return "⚠️"
    if val >= -100:     return "🔶"
    return "🛑"


def _risk_flags(exp_pct: float, liq_delta_pct: float, roe: float) -> list[str]:
    """Сформировать список risk flags."""
    flags = []
    if exp_pct < 20:
        flags.append("✅ EXP% < 20%")
    if exp_pct > 50:
        flags.append("⚠️ EXP% > 50% — повышенная экспозиция")
    if liq_delta_pct < 5:
        flags.append("🚨 LiqΔ% < 5% — близко к ликвидации")
    if roe < -100:
        flags.append("🛑 ROE% < -100% — критический убыток")
    return flags


def format_risk_summary(
    positions: list[dict],
    balance: float,
    fill_counts: dict[str, int] | None = None,
    order_counts: dict[str, int] | None = None,
) -> str:
    """Rich Table → plain text для Telegram."""
    if fill_counts is None:
        fill_counts = {}
    if order_counts is None:
        order_counts = {}

    table = Table(
        title=f"📊 Risk Summary (Balance: {balance:.2f} USDT)",
        width=WIDTH,
        show_header=True,
        header_style="bold",
    )

    table.add_column("Ticker", style="bold", no_wrap=True)
    table.add_column("Cnt", justify="right")
    table.add_column("Side", no_wrap=True)
    table.add_column("Margin", justify="right")
    table.add_column("Bal%", justify="right")
    table.add_column("Mgn%", justify="right")
    table.add_column("Exp%", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("ROE%", justify="right")
    table.add_column("Lev", justify="right")
    table.add_column("LiqΔ%", justify="right")

    total_margin = 0.0
    total_pl = 0.0
    total_value = 0.0
    all_flags: list[str] = []

    for pos in positions:
        margin = float(pos.get("margin_size", 0))
        pl = float(pos.get("unrealized_pl", 0))
        leverage = float(pos.get("leverage", 0))
        value = margin * leverage

        total_margin += margin
        total_pl += pl
        total_value += value

        bal_pct = (margin / balance * 100) if balance else 0
        mgn_pct = 0  # будет пересчитано в total
        exp_pct = (value / balance * 100) if balance else 0
        roe = (pl / margin * 100) if margin else 0
        ror = (pl / balance * 100) if balance else 0

        # LiqDelta% = (openPriceAvg - liqPrice) / openPriceAvg * 100
        open_price = float(pos.get("open_price_avg", 0))
        liq_price = float(pos.get("liquidationPrice", 0))
        liq_delta = abs((open_price - liq_price) / open_price * 100) if open_price and liq_price else 0

        side = pos.get("hold_side", "").lower()
        side_str = "🟢 LONG" if side == "long" else "🔴 SHORT"

        cnt = fill_counts.get(pos.get("symbol", ""), 0)
        oc = order_counts.get(pos.get("symbol", ""), 0)
        cnt_str = str(cnt)
        if oc > 0:
            cnt_str += f"📋{oc}"

        roe_emoji = _roe_emoji(roe)
        ror_emoji = _roe_emoji(ror)

        table.add_row(
            pos.get("symbol", "?"),
            cnt_str,
            side_str,
            f"{margin:.6f}",
            f"{bal_pct:.2f}",
            "",  # Mgn% — в total
            f"{exp_pct:.2f}",
            f"{pl:+.6f}",
            f"{roe_emoji}{roe:+.1f}",
            f"{int(leverage)}x",
            f"{liq_delta:.1f}",
        )

        flags = _risk_flags(exp_pct, liq_delta, roe)
        all_flags.extend(flags)

    # Total row
    total_bal_pct = (total_margin / balance * 100) if balance else 0
    total_exp_pct = (total_value / balance * 100) if balance else 0
    total_roe = (total_pl / total_margin * 100) if total_margin else 0
    total_ror = (total_pl / balance * 100) if balance else 0

    table.add_section()
    table.add_row(
        "TOTAL",
        str(len(positions)),
        "",
        f"{total_margin:.6f}",
        f"{total_bal_pct:.2f}",
        "100",
        f"{total_exp_pct:.2f}",
        f"{total_pl:+.6f}",
        f"{_roe_emoji(total_roe)}{total_roe:+.1f}",
        "",
        "",
    )

    console = Console(file=StringIO(), force_terminal=False, width=WIDTH)
    console.print(table)
    result = console.file.getvalue()

    # Legend
    result += (
        "\nLegend:\n"
        "  MARGIN = часть баланса под позицией\n"
        "  BAL%  = margin / balance × 100\n"
        "  MGN%  = margin / totalMargin × 100\n"
        "  EXP%  = (margin × leverage) / balance × 100\n"
        "  ROE%  = P&L / margin × 100 — доходность маржи\n"
        "  LIQΔ% = (price − liqPrice) / price × 100\n"
    )

    # Risk Flags
    unique_flags = list(dict.fromkeys(all_flags))
    if unique_flags:
        result += "\nRisk Flags:\n"
        for f in unique_flags:
            result += f"  {f}\n"

    return result


def format_order_book(symbol: str, asks: list, bids: list, bucket_size: float = 0) -> str:
    """Order Book → Rich Table → plain text."""
    max_rows = max(len(asks), len(bids))

    title = f"📊 Order Book {symbol}"
    if bucket_size and bucket_size > 0:
        title += f" (aggr: {bucket_size} USDT)"
    table = Table(title=title, width=WIDTH)
    table.add_column("Bid Price", style="green", justify="right")
    table.add_column("Bid Vol", style="green", justify="right")
    table.add_column("│")
    table.add_column("Ask Price", style="red", justify="right")
    table.add_column("Ask Vol", style="red", justify="right")

    for i in range(max_rows):
        b = bids[i] if i < len(bids) else ["", ""]
        a = asks[i] if i < len(asks) else ["", ""]
        table.add_row(
            str(b[0]) if b[0] else "",
            str(b[1]) if b[1] else "",
            "│",
            str(a[0]) if a[0] else "",
            str(a[1]) if a[1] else "",
        )

    # Spread — extract first price from label if range
    if asks and bids and asks[0] and bids[0]:
        def _first_price(val):
            if isinstance(val, str) and "–" in val:
                return float(val.split("–")[0])
            return float(val)
        try:
            best_ask = _first_price(asks[0][0])
            best_bid = _first_price(bids[0][0])
            spread = best_ask - best_bid
            spread_pct = spread / best_bid * 100
            table.add_section()
            table.add_row("", "", f"Spread: {spread:.2f} ({spread_pct:.3f}%)", "", "")
        except (ValueError, IndexError):
            pass

    console = Console(file=StringIO(), force_terminal=False, width=WIDTH)
    console.print(table)
    return console.file.getvalue()
