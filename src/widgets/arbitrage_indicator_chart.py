"""
Arbitrage Indicator Chart Widget
График индикатора арбитража
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_arbitrage_indicator_figure(df, row_idx):
    """
    Создать фигуру для Arbitrage Indicator графика (2 линии)

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
    up_ask_1_price = df['up_ask_1_price'].values if 'up_ask_1_price' in df.columns else np.array([np.nan] * len(df))
    down_ask_1_price = df['down_ask_1_price'].values if 'down_ask_1_price' in df.columns else np.array([np.nan] * len(df))
    up_bid_1_price = df['up_bid_1_price'].values if 'up_bid_1_price' in df.columns else np.array([np.nan] * len(df))
    down_bid_1_price = df['down_bid_1_price'].values if 'down_bid_1_price' in df.columns else np.array([np.nan] * len(df))

    # Вычисление сумм
    ask_sum = up_ask_1_price + down_ask_1_price
    bid_sum = up_bid_1_price + down_bid_1_price

    # Фильтрация NaN
    ask_mask = ~pd.isna(ask_sum)
    bid_mask = ~pd.isna(bid_sum)

    # === Горизонтальная линия на 1.0 ===
    fig.add_hline(
        y=1.0,
        line_dash='dash',
        line_color='rgba(255, 255, 255, 0.6)',
        line_width=2,
        annotation_text='Арбитражный порог: 1.0',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='white',
        row=1, col=1
    )

    # === Trace 0: Ask Sum (красная линия) ===
    if ask_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(ask_mask) if m],
                y=[float(v) for v, m in zip(ask_sum, ask_mask) if m],
                mode='lines',
                name='Ask Sum',
                line=dict(color='#F44336', width=2),
                hovertemplate='Ask Sum: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: Bid Sum (зеленая линия) ===
    if bid_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(bid_mask) if m],
                y=[float(v) for v, m in zip(bid_sum, bid_mask) if m],
                mode='lines',
                name='Bid Sum',
                line=dict(color='#00C853', width=2),
                hovertemplate='Bid Sum: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Layout ===
    fig.update_layout(
        title='Arbitrage Indicator (Арбитраж)',
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
