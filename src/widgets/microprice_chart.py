"""
Microprice Chart Widget
График микроцены (pm_up_microprice, pm_down_microprice)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_microprice_figure(df, row_idx):
    """
    Создать фигуру для Microprice графика (2 линии)

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
    pm_up_microprice = df['pm_up_microprice'].values if 'pm_up_microprice' in df.columns else np.array([np.nan] * len(df))
    pm_down_microprice = df['pm_down_microprice'].values if 'pm_down_microprice' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    up_mask = ~pd.isna(pm_up_microprice)
    down_mask = ~pd.isna(pm_down_microprice)

    # === Trace 0: UP Microprice (зеленая линия) ===
    if up_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(up_mask) if m],
                y=[float(v) for v, m in zip(pm_up_microprice, up_mask) if m],
                mode='lines',
                name='UP Microprice',
                line=dict(color='#00C853', width=2),
                hovertemplate='UP Microprice: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: DOWN Microprice (красная линия) ===
    if down_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(down_mask) if m],
                y=[float(v) for v, m in zip(pm_down_microprice, down_mask) if m],
                mode='lines',
                name='DOWN Microprice',
                line=dict(color='#F44336', width=2),
                hovertemplate='DOWN Microprice: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Layout ===
    fig.update_layout(
        title='Microprice (Микроцена)',
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
