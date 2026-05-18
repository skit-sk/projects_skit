"""Candlestick chart visualization using Plotly."""

import plotly.graph_objects as go
from typing import List, Dict, Any, Optional


def create_candlestick_chart(
    candles: List[Dict[str, Any]],
    patterns: List[Dict[str, Any]] = None,
    title: str = "Price Action & Pattern Recognition"
) -> str:
    """
    Create an interactive candlestick chart with pattern markers.
    
    Args:
        candles: List of candlestick data
        patterns: List of detected patterns
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
    
    # Create main candlestick chart
    fig = go.Figure()
    
    # Candlestick trace
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
            
            if pattern['type'] == 'bullish':
                pattern_colors.append('#22c55e')
            else:
                pattern_colors.append('#ef4444')
            
            # Short codes for patterns
            pattern_icons.append(pattern['pattern'][:3].upper())
        
        # Add markers for patterns
        fig.add_trace(go.Scatter(
            x=pattern_times,
            y=pattern_prices,
            mode='markers+text',
            marker=dict(
                size=18,
                color=pattern_colors,
                symbol='triangle-up',
                line=dict(width=1, color='white'),
            ),
            text=pattern_icons,
            textposition='top center',
            textfont=dict(size=8, color='white'),
            name='Patterns',
            hovertemplate='%{text}<br>%{x}<br>Price: $%{y:.2f}<extra></extra>',
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color='#e5e7eb'),
        ),
        template='plotly_dark',
        height=400,
        margin=dict(l=50, r=50, t=40, b=50),
        xaxis=dict(
            title='',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            zeroline=False,
        ),
        yaxis=dict(
            title='Price (USD)',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            zeroline=False,
            tickformat='$,.0f',
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
    
    # Remove range slider
    fig.update_layout(
        xaxis_rangeslider_visible=False,
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='https://cdn.plot.ly/plotly-2.35.2.min.js')