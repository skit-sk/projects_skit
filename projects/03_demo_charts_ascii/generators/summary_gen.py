import json, os, sys
from .base import load_data, enrich_summary, legend, sparkline

def generate(data_path, output_dir):
    m = enrich_summary(load_data(data_path))
    r = m.get('raw', {})
    d = m.get('daily', {})
    s = m.get('summary', {})
    close = r.get('close', [])
    dev = d.get('deviation_pct', [])
    prof_i = d.get('profitable', [])

    sp = sparkline(close)
    sp_dev = sparkline(dev) if dev else ''

    leg = legend(m)

    first_c = s.get('first_close', 0)
    last_c = s.get('last_close', 0)
    chg_pct = s.get('price_change_pct', 0)
    chg_sym = '📈' if chg_pct >= 0 else '📉'
    wp = s.get('win_rate', 0)
    wp_sym = '✅' if wp >= 50 else '⚠️'

    md = f'''═ SUMMARY: {m['symbol']} ═
{leg}
{"─" * 60}
PRICE ACTION:
  Entry: ${s.get('entry_price', first_c):.4f}
  Current: ${last_c:.4f}
  Change: {chg_pct:+.1f}% {chg_sym}
  High: ${s.get('max_close', 0):.4f}  Low: ${s.get('min_close', 0):.4f}

PERFORMANCE:
  ROE: {s.get('current_roe_pct', 'N/A'):+.1f}%
  PnL: ${s.get('current_pnl_usdt', 0):+.2f}
  Win Rate: {wp:.1f}% {wp_sym}  ({s.get('profitable_days', 0)}/{s.get('total_days', 0)} days)

RISK:
  Avg Volatility: {s.get('avg_volatility', 0):.3f}
  Max Drawdown: {s.get('max_drawdown_pct', 0):+.1f}%  (${s.get('max_drawdown_usdt', 0):+.2f})
  Leverage: {m.get('leverage', 1)}x

STREAKS:
  Profit Streak: {s.get('streak_profit', 0)} days
  Loss Streak: {s.get('streak_loss', 0)} days
  Best Day: +{s.get('max_profit_day', {}).get('roe_pct', 0) if isinstance(s.get('max_profit_day'), dict) else 0:.1f}%
  Worst Day: {s.get('max_loss_day', {}).get('roe_pct', 0) if isinstance(s.get('max_loss_day'), dict) else 0:.1f}%

SPARKLINE (close):
  {sp}

SPARKLINE (deviation):
  {sp_dev}
{"─" * 60}'''

    out_file = os.path.join(output_dir, 'summary', f"{m['symbol']}_summary.txt")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as f:
        f.write(md)

    return {'file': out_file, 'content': md, 'symbol': m['symbol'], 'summary': s}

if __name__ == '__main__':
    generate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'outputs')
