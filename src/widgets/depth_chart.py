"""
Depth Chart Widget
График глубины ликвидности
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_depth_figure(df, row_idx):
    """
    Создать фигуру для Depth графика (4 области)

    Args:
        df: DataFrame с данными
        row_idx: Текущий индекс строки

    Returns:
        go.Figure: Plotly figure объект
    """
    fig = make_subplots(
        rows=1, cols=1,
        row_heights=[1.0]
    )

    # === Извлечение данных depth ===
    pm_up_bid_depth5 = df['pm_up_bid_depth5'].values if 'pm_up_bid_depth5' in df.columns else np.array([np.nan] * len(df))
    pm_up_ask_depth5 = df['pm_up_ask_depth5'].values if 'pm_up_ask_depth5' in df.columns else np.array([np.nan] * len(df))
    pm_down_bid_depth5 = df['pm_down_bid_depth5'].values if 'pm_down_bid_depth5' in df.columns else np.array([np.nan] * len(df))
    pm_down_ask_depth5 = df['pm_down_ask_depth5'].values if 'pm_down_ask_depth5' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    up_bid_mask = ~pd.isna(pm_up_bid_depth5)
    up_ask_mask = ~pd.isna(pm_up_ask_depth5)
    down_bid_mask = ~pd.isna(pm_down_bid_depth5)
    down_ask_mask = ~pd.isna(pm_down_ask_depth5)

    # === Trace 0: UP Bid Depth (зеленый) ===
    if up_bid_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(up_bid_mask) if m],
                y=[float(v) for v, m in zip(pm_up_bid_depth5, up_bid_mask) if m],
                mode='lines',
                name='UP Bid Depth',
                line=dict(color='rgba(0, 200, 83, 0.8)', width=0),
                fill='tozeroy',
                fillcolor='rgba(0, 200, 83, 0.4)',
                hovertemplate='UP Bid Depth: %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: UP Ask Depth (красный) ===
    if up_ask_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(up_ask_mask) if m],
                y=[float(v) for v, m in zip(pm_up_ask_depth5, up_ask_mask) if m],
                mode='lines',
                name='UP Ask Depth',
                line=dict(color='rgba(244, 67, 54, 0.8)', width=0),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.4)',
                hovertemplate='UP Ask Depth: %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 2: DOWN Bid Depth (зеленый) ===
    if down_bid_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(down_bid_mask) if m],
                y=[float(v) for v, m in zip(pm_down_bid_depth5, down_bid_mask) if m],
                mode='lines',
                name='DOWN Bid Depth',
                line=dict(color='rgba(0, 200, 83, 0.6)', width=0),
                fill='tozeroy',
                fillcolor='rgba(0, 200, 83, 0.3)',
                hovertemplate='DOWN Bid Depth: %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 3: DOWN Ask Depth (красный) ===
    if down_ask_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(down_ask_mask) if m],
                y=[float(v) for v, m in zip(pm_down_ask_depth5, down_ask_mask) if m],
                mode='lines',
                name='DOWN Ask Depth',
                line=dict(color='rgba(244, 67, 54, 0.6)', width=0),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.3)',
                hovertemplate='DOWN Ask Depth: %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Layout ===
    fig.update_layout(
        title='Depth (Глубина ликвидности)',
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#2d2d2d',
        font=dict(color='white'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0.5)'
        ),
        margin=dict(l=50, r=20, t=60, b=40),
        hovermode='x unified'
    )

    # Настройка осей
    fig.update_yaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=1, col=1
    )

    fig.update_xaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=1, col=1
    )

    return fig
