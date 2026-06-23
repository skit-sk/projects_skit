"""Bar chart visualization using Plotly."""

import plotly.graph_objects as go


def create_bar_chart(
    categories: list[str],
    values: list[float],
    title: str = "Bar Chart",
    color: str = "#3b82f6",
) -> str:
    if not categories or not values:
        return ""

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        name=title,
        marker_color=color,
        text=values,
        textposition="outside",
    ))

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color="#e5e7eb"),
        ),
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=50, t=40, b=50),
        xaxis=dict(
            title="",
            showgrid=False,
        ),
        yaxis=dict(
            title="Value",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
        ),
        showlegend=False,
        hovermode="x unified",
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)
