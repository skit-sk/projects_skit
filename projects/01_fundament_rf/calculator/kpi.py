from typing import List, Dict


def calc_kpi(cards: list) -> dict:
    total_pnl = 0.0
    total_margin = 0.0
    total_days = 0
    count = 0
    best_roe = -float('inf')
    worst_roe = float('inf')
    profitable = 0

    for obj in cards:
        lp = obj.data.get('live_position')
        if not lp or not lp.get('hold_side'):
            continue
        pl = float(lp.get('unrealized_pl', 0))
        margin = float(lp.get('margin_size', 0))
        days = int(lp.get('days_open', 0))
        roe = (pl / margin * 100) if margin else 0
        total_pnl += pl
        total_margin += margin
        total_days += days
        count += 1
        profitable += 1 if pl >= 0 else 0
        if roe > best_roe:
            best_roe = roe
        if roe < worst_roe:
            worst_roe = roe

    return {
        "total_pnl": round(total_pnl, 4),
        "total_margin": round(total_margin, 4),
        "avg_days": round(total_days / count, 1) if count else 0,
        "win_rate": round(profitable / count, 4) if count else 0,
        "best_roe": round(best_roe, 2) if best_roe != -float('inf') else 0,
        "worst_roe": round(worst_roe, 2) if worst_roe != float('inf') else 0,
        "total_positions": count,
    }