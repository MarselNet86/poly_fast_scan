"""
Volatility Chart Widget
График волатильности (ATR + RVol)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_volatility_figure(df, row_idx):
    """
    Создать фигуру для Volatility графика (ATR + RVol)

    Args:
        df: DataFrame с данными
        row_idx: Текущий индекс строки

    Returns:
        go.Figure: Plotly figure объект с двумя подграфиками
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['ATR (Average True Range, USD)', 'RVol 30s (Realized Volatility, %)'],
        vertical_spacing=0.15,
        row_heights=[0.5, 0.5]
    )

    # === Извлечение данных ===
    atr_5s = df['binance_atr_5s'].values if 'binance_atr_5s' in df.columns else np.array([np.nan] * len(df))
    atr_30s = df['binance_atr_30s'].values if 'binance_atr_30s' in df.columns else np.array([np.nan] * len(df))
    rvol_30s = df['binance_rvol_30s'].values if 'binance_rvol_30s' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    atr5s_mask = ~pd.isna(atr_5s)
    atr30s_mask = ~pd.isna(atr_30s)
    rvol_mask = ~pd.isna(rvol_30s)

    # ===== ВЕРХНИЙ ГРАФИК: ATR =====

    # Trace 0: ATR 5s (быстрый, тонкая линия)
    if atr5s_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(atr5s_mask) if m],
                y=[float(v) for v, m in zip(atr_5s, atr5s_mask) if m],
                mode='lines',
                name='ATR 5s',
                line=dict(color='#00BCD4', width=2),
                hovertemplate='ATR 5s: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # Trace 1: ATR 30s (медленный, толстая линия)
    if atr30s_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(atr30s_mask) if m],
                y=[float(v) for v, m in zip(atr_30s, atr30s_mask) if m],
                mode='lines',
                name='ATR 30s',
                line=dict(color='#FF6B00', width=3),
                hovertemplate='ATR 30s: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # ===== НИЖНИЙ ГРАФИК: RVOL =====

    # Trace 2: RVol 30s (реализованная волатильность)
    if rvol_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(rvol_mask) if m],
                y=[float(v) for v, m in zip(rvol_30s, rvol_mask) if m],
                mode='lines',
                name='RVol 30s',
                line=dict(color='#9C27B0', width=2),
                fill='tozeroy',
                fillcolor='rgba(156, 39, 176, 0.2)',
                hovertemplate='RVol: %{y:.2f}%<extra></extra>'
            ),
            row=2, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=2, col=1)

    # === Layout ===
    fig.update_layout(
        title='Volatility (ATR & RVol)',
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

    # Настройка осей - верхний график
    fig.update_yaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=1, col=1
    )

    fig.update_xaxes(
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=1, col=1
    )

    # Настройка осей - нижний график
    fig.update_yaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=2, col=1
    )

    fig.update_xaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=2, col=1
    )

    return fig
