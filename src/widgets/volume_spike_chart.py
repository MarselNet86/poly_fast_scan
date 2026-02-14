"""
Volume Spike Chart Widget
График всплесков объёма торгов
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_volume_spike_figure(df, row_idx):
    """
    Создать фигуру для Volume Spike графика

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
    volume_spike = df['binance_volume_spike'].values if 'binance_volume_spike' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    spike_mask = ~pd.isna(volume_spike)

    # === Trace 0: Volume Spike (основная линия) ===
    if spike_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(spike_mask) if m],
                y=[float(v) for v, m in zip(volume_spike, spike_mask) if m],
                mode='lines',
                name='Volume Spike',
                line=dict(color='#FF6B00', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 0, 0.2)',
                hovertemplate='Spike: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Нулевая линия ===
    fig.add_hline(
        y=0,
        line_dash='solid',
        line_color='rgba(255, 255, 255, 0.3)',
        line_width=2,
        row=1, col=1
    )

    # === Layout ===
    fig.update_layout(
        title='Volume Spike',
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
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.3)',
        zerolinewidth=2,
        row=1, col=1
    )

    fig.update_xaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=1, col=1
    )

    return fig
