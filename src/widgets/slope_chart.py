"""
Slope Chart Widget
График наклона (pm_up_bid_slope, pm_up_ask_slope, pm_down_bid_slope, pm_down_ask_slope)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_slope_figure(df, row_idx):
    """
    Создать фигуру для Slope графика (4 линии)

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

    # === Извлечение данных ===
    up_bid_slope = df['pm_up_bid_slope'].values if 'pm_up_bid_slope' in df.columns else np.array([np.nan] * len(df))
    up_ask_slope = df['pm_up_ask_slope'].values if 'pm_up_ask_slope' in df.columns else np.array([np.nan] * len(df))
    down_bid_slope = df['pm_down_bid_slope'].values if 'pm_down_bid_slope' in df.columns else np.array([np.nan] * len(df))
    down_ask_slope = df['pm_down_ask_slope'].values if 'pm_down_ask_slope' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    # Для простоты используем маску для каждого ряда
    m1 = ~pd.isna(up_bid_slope)
    m2 = ~pd.isna(up_ask_slope)
    m3 = ~pd.isna(down_bid_slope)
    m4 = ~pd.isna(down_ask_slope)

    # === Trace 0: UP Bid Slope (светло-зеленая) ===
    if m1.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(m1) if m],
                y=[float(v) for v, m in zip(up_bid_slope, m1) if m],
                mode='lines',
                name='UP Bid Slope',
                line=dict(color='#81C784', width=2),
                hovertemplate='UP Bid Slope: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: UP Ask Slope (темно-зеленая) ===
    if m2.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(m2) if m],
                y=[float(v) for v, m in zip(up_ask_slope, m2) if m],
                mode='lines',
                name='UP Ask Slope',
                line=dict(color='#2E7D32', width=2),
                hovertemplate='UP Ask Slope: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 2: DOWN Bid Slope (светло-красная) ===
    if m3.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(m3) if m],
                y=[float(v) for v, m in zip(down_bid_slope, m3) if m],
                mode='lines',
                name='DOWN Bid Slope',
                line=dict(color='#E57373', width=2),
                hovertemplate='DOWN Bid Slope: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 3: DOWN Ask Slope (темно-красная) ===
    if m4.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(m4) if m],
                y=[float(v) for v, m in zip(down_ask_slope, m4) if m],
                mode='lines',
                name='DOWN Ask Slope',
                line=dict(color='#C62828', width=2),
                hovertemplate='DOWN Ask Slope: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Layout ===
    fig.update_layout(
        title='Slope (Наклон)',
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

    # Добавляем вертикальную линию текущего времени
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=1, col=1)

    return fig
