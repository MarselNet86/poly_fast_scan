"""
Latency Direction Chart Widget
График индикатора запаздывания оракула
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_latency_direction_figure(df, row_idx):
    """
    Создать фигуру для Latency Direction графика (осциллятор)

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
    lat_dir_raw = df['lat_dir_raw_x1000'].values if 'lat_dir_raw_x1000' in df.columns else np.array([np.nan] * len(df))
    lat_dir_norm = df['lat_dir_norm_x1000'].values if 'lat_dir_norm_x1000' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    raw_mask = ~pd.isna(lat_dir_raw)
    norm_mask = ~pd.isna(lat_dir_norm)

    # === Фоновые зоны (выше/ниже нуля) ===

    # Бычья зона (выше 0)
    fig.add_hrect(
        y0=0, y1=5.0,  # Максимум для отображения
        fillcolor='rgba(0, 200, 83, 0.1)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    # Медвежья зона (ниже 0)
    fig.add_hrect(
        y0=-5.0, y1=0,  # Минимум для отображения
        fillcolor='rgba(244, 67, 54, 0.1)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    # === Нулевая линия (обязательная) ===
    fig.add_hline(
        y=0,
        line_dash='solid',
        line_color='rgba(255, 255, 255, 0.4)',
        line_width=2,
        row=1, col=1
    )

    # === Пороговые линии (значимые уровни) ===
    # Уровни ±0.5
    fig.add_hline(
        y=0.5,
        line_dash='dash',
        line_color='rgba(0, 200, 83, 0.5)',
        line_width=1,
        annotation_text='Бычий +0.5',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(0, 200, 83, 0.8)',
        row=1, col=1
    )

    fig.add_hline(
        y=-0.5,
        line_dash='dash',
        line_color='rgba(244, 67, 54, 0.5)',
        line_width=1,
        annotation_text='Медвежий -0.5',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(244, 67, 54, 0.8)',
        row=1, col=1
    )

    # Уровни ±1.0
    fig.add_hline(
        y=1.0,
        line_dash='dash',
        line_color='rgba(0, 200, 83, 0.7)',
        line_width=1,
        annotation_text='Сильный бычий +1.0',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(0, 200, 83, 1.0)',
        row=1, col=1
    )

    fig.add_hline(
        y=-1.0,
        line_dash='dash',
        line_color='rgba(244, 67, 54, 0.7)',
        line_width=1,
        annotation_text='Сильный медвежий -1.0',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(244, 67, 54, 1.0)',
        row=1, col=1
    )

    # === Trace 0: lat_dir_norm_x1000 (медленный тренд, толстая линия) ===
    if norm_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(norm_mask) if m],
                y=[float(v) for v, m in zip(lat_dir_norm, norm_mask) if m],
                mode='lines',
                name='LatDir Norm (тренд)',
                line=dict(color='#9C27B0', width=3),  # Фиолетовая толстая
                hovertemplate='Norm: %{y:.3f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: lat_dir_raw_x1000 (быстрый сигнал, тонкая линия) ===
    if raw_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(raw_mask) if m],
                y=[float(v) for v, m in zip(lat_dir_raw, raw_mask) if m],
                mode='lines',
                name='LatDir Raw (сигнал)',
                line=dict(color='#00BCD4', width=2),  # Голубая
                hovertemplate='Raw: %{y:.3f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Layout ===
    fig.update_layout(
        title='Latency Direction (запаздывание оракула)',
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
        title_text='×1000',
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.4)',
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
