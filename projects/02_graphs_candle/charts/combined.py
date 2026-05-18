"""Combined chart visualization using Plotly."""

import plotly.graph_objects as go
from typing import List, Dict, Any


def create_combined_chart(
    candles: List[Dict[str, Any]],
    patterns: List[Dict[str, Any]] = None,
    pnl_points: List[Dict[str, Any]] = None,
    title: str = "Price Action, Patterns & Cumulative P&L"
) -> str:
    """
    Create a combined chart with candlesticks, patterns, and P&L.
    
    Args:
        candles: List of candlestick data
        patterns: List of detected patterns
        pnl_points: List of P&L data points
        title: Chart title
        
    Returns:
        HTML string of the chart
    """
    if not candles:
        return ""
    
    times = [c['time'] for c in candles]
    opens = [c['open'] for c in candles]
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    fig = go.Figure()
    
    # Candlestick chart (main, takes 70% height)
    fig.add_trace(go.Candlestick(
        x=times,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        name='OHLC',
        increasing_line_color='#22c55e',
        decreasing_line_color='#ef4444',
        increasing_fillcolor='#22c55e',
        decreasing_fillcolor='#ef4444',
        xaxis='x',
        yaxis='y',
    ))
    
    # Add pattern markers
    if patterns:
        pattern_times = []
        pattern_prices = []
        pattern_colors = []
        pattern_icons = []
        
        for pattern in patterns:
            pattern_times.append(pattern['time'])
            pattern_prices.append(pattern['priceLevel'])
            pattern_colors.append('#22c55e' if pattern['type'] == 'bullish' else '#ef4444')
            pattern_icons.append(pattern['pattern'][:3].upper())
        
        fig.add_trace(go.Scatter(
            x=pattern_times,
            y=pattern_prices,
            mode='markers+text',
            marker=dict(
                size=16,
                color=pattern_colors,
                symbol='triangle-up',
                line=dict(width=1, color='white'),
            ),
            text=pattern_icons,
            textposition='top center',
            textfont=dict(size=7, color='white'),
            name='Patterns',
            hovertemplate='%{text}<br>%{x}<br>$%{y:.2f}<extra></extra>',
        ))
    
    # P&L chart (bottom, takes 30% height)
    if pnl_points:
        pnl_times = [p['time'] for p in pnl_points]
        pnl_values = [p['pnl'] for p in pnl_points]
        
        fig.add_trace(go.Scatter(
            x=pnl_times,
            y=pnl_values,
            mode='lines',
            name='P&L',
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)',
            xaxis='x',
            yaxis='y2',
        ))
    
    # Layout with two subplots
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color='#e5e7eb'),
        ),
        template='plotly_dark',
        height=500,
        margin=dict(l=50, r=50, t=40, b=50),
        
        # X-axis (shared)
        xaxis=dict(
            title='',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            rangeslider_visible=False,
        ),
        
        # Y-axis (candlesticks - top)
        yaxis=dict(
            title='Price (USD)',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='$,.0f',
            domain=[0.3, 1.0],  # Top 70%
        ),
        
        # Y2-axis (P&L - bottom)
        yaxis2=dict(
            title='P&L (USD)',
            overlaying='y',
            side='right',
            showgrid=False,
            tickformat='$,.0f',
            domain=[0, 0.25],  # Bottom 25%
        ),
        
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
        hovermode='x unified',
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='https://cdn.plot.ly/plotly-2.35.2.min.js')