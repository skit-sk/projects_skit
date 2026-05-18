import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional


class DashboardCharts:
    def __init__(self):
        self.template = 'plotly_dark'

    def equity_drawdown_chart(self, equity_data: Dict[str, Any]) -> str:
        equity_curve = equity_data.get('equity_curve', [])
        drawdown_curve = equity_data.get('drawdown_curve', [])

        if not equity_curve:
            return self._empty_chart('No equity data')

        dates = [e['date'] for e in equity_curve]
        cumulative = [e['cumulative_pnl'] for e in equity_curve]
        drawdown_pcts = [d['drawdown_pct'] for d in drawdown_curve]

        fig = make_subplots(specs=[[{'secondary_y': True}]])

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative,
                mode='lines',
                name='Cumulative PnL (USDT)',
                line=dict(color='#3b82f6', width=2),
                fill='tozeroy',
                fillcolor='rgba(59, 130, 246, 0.1)'
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=drawdown_pcts,
                mode='lines',
                name='Drawdown (%)',
                line=dict(color='#ef4444', width=1, dash='dot'),
                fill='tozeroy',
                fillcolor='rgba(239, 68, 68, 0.1)'
            ),
            secondary_y=True
        )

        fig.update_layout(
            template=self.template,
            height=350,
            margin=dict(l=60, r=60, t=30, b=60),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            hovermode='x unified'
        )
        fig.update_xaxes(title_text='Date', tickangle=-45, nticks=10)
        fig.update_yaxes(title_text='PnL (USDT)', secondary_y=False, tickformat='+.2f')
        fig.update_yaxes(title_text='Drawdown %', secondary_y=True, tickformat='.1f%', side='right')

        return fig.to_html(full_html=False, include_plotlyjs=False)

    def pnl_distribution_bars(self, distribution: List[Dict[str, Any]]) -> str:
        if not distribution:
            return self._empty_chart('No distribution data')

        distribution = sorted(distribution, key=lambda x: x['pnl_usdt'])
        names = [d['name'][:15] for d in distribution]
        pnl_values = [d['pnl_usdt'] for d in distribution]
        colors = ['#22c55e' if p >= 0 else '#ef4444' for p in pnl_values]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=names,
            y=pnl_values,
            marker_color=colors,
            text=[f'{p:+.2f}' for p in pnl_values],
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color='white', size=8)
        ))

        fig.update_layout(
            template=self.template,
            height=280,
            margin=dict(l=40, r=40, t=30, b=80),
            xaxis_title='Trade',
            yaxis_title='PnL (USDT)',
            showlegend=False,
            xaxis=dict(tickangle=-45, tickfont=dict(size=9))
        )

        return fig.to_html(full_html=False, include_plotlyjs=False)

    def pnl_by_symbol_chart(self, by_symbol: Dict[str, Dict[str, float]]) -> str:
        if not by_symbol:
            return self._empty_chart('No symbol data')

        symbols = sorted(by_symbol.keys())
        pnl_values = [by_symbol[s]['pnl_usdt'] for s in symbols]
        colors = ['#22c55e' if p >= 0 else '#ef4444' for p in pnl_values]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=symbols,
            y=pnl_values,
            marker_color=colors,
            text=[f'{p:+.2f}' for p in pnl_values],
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color='white', size=8)
        ))

        fig.update_layout(
            template=self.template,
            height=280,
            margin=dict(l=50, r=50, t=30, b=50),
            xaxis_title='Symbol',
            yaxis_title='Total PnL (USDT)',
            showlegend=False
        )

        return fig.to_html(full_html=False, include_plotlyjs=False)

    def heatmap_chart(self, heatmap_data: Dict[str, Any]) -> str:
        z = heatmap_data.get('z', [])
        x = heatmap_data.get('x', [])
        y = heatmap_data.get('y', [])
        symbol_min = heatmap_data.get('symbol_min', {})
        symbol_max = heatmap_data.get('symbol_max', {})

        if not z or not x or not y:
            return self._empty_chart('No heatmap data')

        z_normalized = []
        for sym_idx, sym in enumerate(y):
            row = []
            min_roe = symbol_min.get(sym, 0)
            max_roe = symbol_max.get(sym, 1)
            range_roe = max_roe - min_roe if max_roe != min_roe else 1
            for val in z[sym_idx]:
                if val == 0:
                    row.append(0.5)
                else:
                    normalized = (val - min_roe) / range_roe
                    row.append(normalized)
            z_normalized.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=z_normalized,
            x=x,
            y=y,
            colorscale=[
                [0.0, 'rgb(220, 38, 38)'],
                [0.25, 'rgb(239, 68, 68)'],
                [0.4, 'rgb(252, 165, 165)'],
                [0.5, 'rgb(156, 163, 175)'],
                [0.6, 'rgb(134, 239, 172)'],
                [0.75, 'rgb(34, 197, 94)'],
                [1.0, 'rgb(22, 163, 74)']
            ],
            zmin=0,
            zmax=1,
            text=[[f'{v:+.1f}%' for v in row] for row in z],
            texttemplate='%{text}',
            textfont=dict(size=9, color='white'),
            hovertemplate='Symbol: %{y}<br>Month: %{x}<br>Avg ROE: %{text}<extra></extra>'
        ))

        fig.update_layout(
            template=self.template,
            height=300,
            margin=dict(l=80, r=30, t=30, b=50),
            xaxis_title='Month',
            yaxis_title='Symbol'
        )

        return fig.to_html(full_html=False, include_plotlyjs=False)

    # ── MA-аналитика: графики ──

    def ma_price_chart(self, dates: List[str], close: List[float],
                       ma_lines: Dict[str, List[Optional[float]]],
                       signals: Optional[List[Dict]] = None) -> str:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates, y=close, mode='lines',
            name='Price', line=dict(color='#94a3b8', width=1.5),
        ))

        colors = {'sma': {'50': '#f59e0b', '100': '#3b82f6', '200': '#ef4444'},
                  'ema': {'50': '#10b981', '100': '#8b5cf6', '200': '#ec4899'},
                  'wma': {'50': '#06b6d4', '100': '#d946ef', '200': '#f97316'}}

        for key, vals in ma_lines.items():
            parts = key.split('_')
            if len(parts) == 2:
                ma_t, ma_p = parts[0], parts[1]
            else:
                continue
            ma_t_clean = ma_t.lower()
            color = colors.get(ma_t_clean, {}).get(ma_p, '#888')
            dash = 'dot' if ma_t_clean == 'ema' else ('dash' if ma_t_clean == 'wma' else 'solid')
            valid = [i for i, v in enumerate(vals) if v is not None]
            if not valid:
                continue
            fig.add_trace(go.Scatter(
                x=[dates[i] for i in valid], y=[vals[i] for i in valid],
                mode='lines', name=f'{ma_t.upper()} {ma_p}',
                line=dict(color=color, width=1.2, dash=dash),
            ))

        if signals:
            buy_x, buy_y = [], []
            sell_x, sell_y = [], []
            for s in signals:
                if s.get('type') == 'entry' and 'index' in s:
                    buy_x.append(dates[s['index']])
                    buy_y.append(close[s['index']] * 0.98)
                elif s.get('type') == 'exit' and 'index' in s:
                    sell_x.append(dates[s['index']])
                    sell_y.append(close[s['index']] * 1.02)
            if buy_x:
                fig.add_trace(go.Scatter(
                    x=buy_x, y=buy_y, mode='markers',
                    name='Buy', marker=dict(color='#22c55e', size=10, symbol='triangle-up'),
                ))
            if sell_x:
                fig.add_trace(go.Scatter(
                    x=sell_x, y=sell_y, mode='markers',
                    name='Sell', marker=dict(color='#ef4444', size=10, symbol='triangle-down'),
                ))

        fig.update_layout(
            template=self.template,
            height=450,
            margin=dict(l=60, r=60, t=30, b=60),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            hovermode='x unified',
            xaxis=dict(rangeslider=dict(visible=True), type='date'),
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def ma_heatmap(self, ma_types: List[str], periods: List[int],
                   values: List[List[float]], value_name: str = 'Sharpe') -> str:
        fig = go.Figure(data=go.Heatmap(
            z=values,
            x=ma_types,
            y=[str(p) for p in periods],
            colorscale='RdBu_r',
            zmid=0,
            text=[[f'{v:.3f}' for v in row] for row in values],
            texttemplate='%{text}',
            textfont=dict(size=9),
            hovertemplate='MA: %{x}<br>Period: %{y}<br>%{text}<extra></extra>',
        ))
        fig.update_layout(
            template=self.template,
            height=500,
            margin=dict(l=80, r=30, t=30, b=80),
            xaxis_title='MA Type',
            yaxis_title='Period',
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def backtest_equity_chart(self, equity_curve: List[float],
                              dates: List[str], label: str = 'Strategy') -> str:
        valid = [(i, v) for i, v in enumerate(equity_curve) if not np.isnan(v)]
        if not valid:
            return self._empty_chart('No equity data')
        idx = [v[0] for v in valid]
        vals = [v[1] for v in valid]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[dates[i] for i in idx] if dates else list(range(len(vals))),
            y=vals, mode='lines', name=label,
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)',
        ))
        fig.update_layout(
            template=self.template,
            height=300,
            margin=dict(l=60, r=60, t=30, b=60),
            title=label,
            hovermode='x unified',
            yaxis_title='Equity',
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def _empty_chart(self, message: str) -> str:
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=14, color='gray')
        )
        fig.update_layout(
            template=self.template,
            height=200,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)
