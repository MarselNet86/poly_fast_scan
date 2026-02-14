"""
P/VWAP Chart Widget
График отклонения цены от VWAP (осциллятор)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_p_vwap_figure(df, row_idx):
    """
    Создать фигуру для P/VWAP графика (осциллятор отклонения от VWAP)

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
    p_vwap_5s = df['binance_p_vwap_5s'].values if 'binance_p_vwap_5s' in df.columns else np.array([np.nan] * len(df))
    p_vwap_30s = df['binance_p_vwap_30s'].values if 'binance_p_vwap_30s' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    p5s_mask = ~pd.isna(p_vwap_5s)
    p30s_mask = ~pd.isna(p_vwap_30s)

    # === Фоновые зоны (выше/ниже нуля) ===

    # Бычья зона (выше 0)
    fig.add_hrect(
        y0=0, y1=1.0,  # Максимум для отображения
        fillcolor='rgba(0, 200, 83, 0.1)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    # Медвежья зона (ниже 0)
    fig.add_hrect(
        y0=-1.0, y1=0,  # Минимум для отображения
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

    # === Пороговые линии (значимые отклонения ±0.05%) ===
    fig.add_hline(
        y=0.05,
        line_dash='dash',
        line_color='rgba(0, 200, 83, 0.5)',
        line_width=1,
        annotation_text='Бычий +0.05%',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(0, 200, 83, 0.8)',
        row=1, col=1
    )

    fig.add_hline(
        y=-0.05,
        line_dash='dash',
        line_color='rgba(244, 67, 54, 0.5)',
        line_width=1,
        annotation_text='Медвежий -0.05%',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(244, 67, 54, 0.8)',
        row=1, col=1
    )

    # === Trace 0: P/VWAP 30s (медленный тренд, толстая линия) ===
    if p30s_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(p30s_mask) if m],
                y=[float(v) for v, m in zip(p_vwap_30s, p30s_mask) if m],
                mode='lines',
                name='P/VWAP 30s (тренд)',
                line=dict(color='#9C27B0', width=3),  # Фиолетовая толстая
                hovertemplate='P/VWAP 30s: %{y:.3f}%<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: P/VWAP 5s (быстрый сигнал, тонкая линия) ===
    if p5s_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(p5s_mask) if m],
                y=[float(v) for v, m in zip(p_vwap_5s, p5s_mask) if m],
                mode='lines',
                name='P/VWAP 5s (сигнал)',
                line=dict(color='#00BCD4', width=2),  # Голубая
                hovertemplate='P/VWAP 5s: %{y:.3f}%<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Поиск точек пересечения (сигналы разворота) ===
    # Находим индексы, где обе линии валидны
    both_valid = p5s_mask & p30s_mask
    valid_indices = np.where(both_valid)[0]

    if len(valid_indices) > 1:
        crossover_indices = []

        for i in range(1, len(valid_indices)):
            idx_prev = valid_indices[i - 1]
            idx_curr = valid_indices[i]

            # Разность линий (P/VWAP 5s - P/VWAP 30s)
            diff_prev = p_vwap_5s[idx_prev] - p_vwap_30s[idx_prev]
            diff_curr = p_vwap_5s[idx_curr] - p_vwap_30s[idx_curr]

            # Пересечение происходит, когда знак разности меняется
            if not pd.isna(diff_prev) and not pd.isna(diff_curr):
                if (diff_prev >= 0 and diff_curr < 0) or (diff_prev < 0 and diff_curr >= 0):
                    crossover_indices.append(idx_curr)

        # Добавляем вертикальные маркеры в точках пересечения
        for cross_idx in crossover_indices:
            fig.add_vline(
                x=cross_idx,
                line_dash='dot',
                line_color='rgba(255, 193, 7, 0.7)',  # Жёлтый
                line_width=2,
                row=1, col=1
            )

    # === Layout ===
    fig.update_layout(
        title='P/VWAP (% отклонение от VWAP)',
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
        title_text='%',
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
