"""P&L chart visualization using Plotly."""

import plotly.graph_objects as go
from typing import List, Dict, Any


def create_pnl_chart(
    points: List[Dict[str, Any]],
    title: str = "Cumulative P&L & Drawdown"
) -> str:
    """
    Create an interactive P&L chart with equity curve and drawdown.
    
    Args:
        points: List of P&L data points
        title: Chart title
        
    Returns:
        HTML string of the chart
    """
    if not points:
        return ""
    
    try:
        times = [p['time'] for p in points]
        pnl_values = [p['pnl'] for p in points]
        drawdown_values = [p['drawdown'] for p in points]
        equity_values = [p['equity'] for p in points]
    except (KeyError, TypeError) as e:
        print(f"Error extracting P&L data: {e}")
        return ""
    
    fig = go.Figure()
    
    # P&L line
    fig.add_trace(go.Scatter(
        x=times,
        y=pnl_values,
        mode='lines',
        name='Cumulative P&L',
        line=dict(
            color='#3b82f6',
            width=2,
        ),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
    ))
    
    # Drawdown area (secondary y-axis)
    fig.add_trace(go.Scatter(
        x=times,
        y=drawdown_values,
        mode='lines',
        name='Drawdown %',
        line=dict(
            color='#f59e0b',
            width=1.5,
            dash='dot',
        ),
        yaxis='y2',
    ))
    
    # Calculate range safely
    max_dd = max(drawdown_values) if drawdown_values else 0
    dd_range = [0, max_dd * 1.2] if max_dd > 0 else [0, 10]
    
    # Update layout with dual y-axis
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color='#e5e7eb'),
        ),
        template='plotly_dark',
        height=350,
        margin=dict(l=50, r=50, t=40, b=50),
        xaxis=dict(
            title='',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
        ),
        yaxis=dict(
            title='P&L (USD)',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='$,.0f',
            title_font=dict(color='#3b82f6'),
            tickfont=dict(color='#3b82f6'),
        ),
        yaxis2=dict(
            title='Drawdown %',
            overlaying='y',
            side='right',
            range=dd_range,
            showgrid=False,
            title_font=dict(color='#f59e0b'),
            tickfont=dict(color='#f59e0b'),
            tickformat='.1f',
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