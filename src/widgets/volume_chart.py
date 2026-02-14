"""
Volume Chart Widget
График объёмов торгов (линии)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_volume_figure(df, row_idx):
    """
    Создать фигуру для Volume графика (V1s, V5s, VolMA 30s)

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
    volume_1s = df['binance_volume_1s'].values if 'binance_volume_1s' in df.columns else np.array([np.nan] * len(df))
    volume_5s = df['binance_volume_5s'].values if 'binance_volume_5s' in df.columns else np.array([np.nan] * len(df))
    volma_30s = df['binance_volma_30s'].values if 'binance_volma_30s' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    v1s_mask = ~pd.isna(volume_1s)
    v5s_mask = ~pd.isna(volume_5s)
    volma_mask = ~pd.isna(volma_30s)

    # === Пороговые линии ===

    # Низкая активность ($50k)
    fig.add_hline(
        y=50000,
        line_dash='dash',
        line_color='rgba(100, 100, 100, 0.5)',
        line_width=1,
        annotation_text='Low ($50k)',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(150, 150, 150, 0.8)',
        row=1, col=1
    )

    # Высокая активность ($500k)
    fig.add_hline(
        y=500000,
        line_dash='dash',
        line_color='rgba(255, 193, 7, 0.6)',
        line_width=1,
        annotation_text='High ($500k)',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(255, 193, 7, 0.9)',
        row=1, col=1
    )

    # Крупный игрок ($1M)
    fig.add_hline(
        y=1000000,
        line_dash='dot',
        line_color='rgba(244, 67, 54, 0.7)',
        line_width=1,
        annotation_text='Big Player ($1M)',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(244, 67, 54, 0.9)',
        row=1, col=1
    )

    # === Trace 0: Volume 5s (толстая полупрозрачная линия) ===
    if v5s_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(v5s_mask) if m],
                y=[float(v) for v, m in zip(volume_5s, v5s_mask) if m],
                mode='lines',
                name='Volume 5s',
                line=dict(color='rgba(100, 181, 246, 0.6)', width=3),
                hovertemplate='V5s: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: Volume 1s (основная линия) ===
    if v1s_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(v1s_mask) if m],
                y=[float(v) for v, m in zip(volume_1s, v1s_mask) if m],
                mode='lines',
                name='Volume 1s',
                line=dict(color='#2196F3', width=2),
                hovertemplate='V1s: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 2: Volume MA 30s (скользящее среднее) ===
    if volma_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(volma_mask) if m],
                y=[float(v) for v, m in zip(volma_30s, volma_mask) if m],
                mode='lines',
                name='VolMA 30s',
                line=dict(color='#9C27B0', width=2),
                hovertemplate='VolMA: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Layout ===
    fig.update_layout(
        title='Volume (USDT)',
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
