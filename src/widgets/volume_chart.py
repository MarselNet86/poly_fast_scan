"""
Volume & Spikes Chart Widget
График объёмов торгов и коэффициента всплесков
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_volume_figure(df, row_idx):
    """
    Создать отдельную фигуру для Volume & Spikes

    Args:
        df: DataFrame с данными
        row_idx: Текущий индекс строки

    Returns:
        go.Figure: Plotly figure объект с двумя подграфиками
    """
    # Создаем фигуру с двумя подграфиками (вертикально)
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Volume (USDT)', 'Volume Spike Coefficient'],
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4]  # Верхний график больше
    )

    # === Извлечение данных ===
    volume_1s = df['binance_volume_1s'].values if 'binance_volume_1s' in df.columns else np.array([np.nan] * len(df))
    volume_5s = df['binance_volume_5s'].values if 'binance_volume_5s' in df.columns else np.array([np.nan] * len(df))
    volma_30s = df['binance_volma_30s'].values if 'binance_volma_30s' in df.columns else np.array([np.nan] * len(df))
    volume_spike = df['binance_volume_spike'].values if 'binance_volume_spike' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    v1s_mask = ~pd.isna(volume_1s)
    v5s_mask = ~pd.isna(volume_5s)
    volma_mask = ~pd.isna(volma_30s)
    spike_mask = ~pd.isna(volume_spike)

    # ===== ВЕРХНИЙ ГРАФИК: ОБЪЁМЫ =====

    # Фоновые зоны для V1s
    # Зона высокой активности (>500k)
    fig.add_hrect(
        y0=500000, y1=5000000,  # До 5M для визуализации
        fillcolor='rgba(255, 193, 7, 0.1)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    # Зона крупного игрока (>1M)
    fig.add_hrect(
        y0=1000000, y1=5000000,
        fillcolor='rgba(244, 67, 54, 0.15)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    # Пороговые линии
    fig.add_hline(
        y=50000,
        line_dash='dash',
        line_color='rgba(100, 100, 100, 0.5)',
        line_width=1,
        annotation_text='Low Activity ($50k)',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(150, 150, 150, 0.8)',
        row=1, col=1
    )

    fig.add_hline(
        y=500000,
        line_dash='dash',
        line_color='rgba(255, 193, 7, 0.6)',
        line_width=1,
        annotation_text='High Activity ($500k)',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(255, 193, 7, 0.9)',
        row=1, col=1
    )

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

    # Trace 0: Volume 5s (толстые полупрозрачные бары)
    if v5s_mask.any():
        fig.add_trace(
            go.Bar(
                x=[i for i, m in enumerate(v5s_mask) if m],
                y=[float(v) for v, m in zip(volume_5s, v5s_mask) if m],
                name='Volume 5s',
                marker=dict(color='rgba(100, 181, 246, 0.3)'),
                width=1.0,
                hovertemplate='V5s: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        # Пустой trace для сохранения индексов
        fig.add_trace(go.Bar(x=[], y=[], showlegend=False), row=1, col=1)

    # Trace 1: Volume 1s (основные бары с динамическим цветом)
    if v1s_mask.any():
        # Определяем цвет каждого бара в зависимости от значения
        bar_colors = []
        for v in volume_1s:
            if pd.notna(v):
                if v > 1000000:
                    bar_colors.append('rgba(244, 67, 54, 0.8)')  # Красный - крупный игрок
                elif v > 500000:
                    bar_colors.append('rgba(255, 193, 7, 0.8)')  # Оранжевый - высокая активность
                elif v > 50000:
                    bar_colors.append('rgba(33, 150, 243, 0.7)')  # Синий - нормально
                else:
                    bar_colors.append('rgba(100, 100, 100, 0.5)')  # Серый - низкая
            else:
                bar_colors.append('rgba(100, 100, 100, 0.3)')

        fig.add_trace(
            go.Bar(
                x=[i for i, m in enumerate(v1s_mask) if m],
                y=[float(v) for v, m in zip(volume_1s, v1s_mask) if m],
                name='Volume 1s',
                marker=dict(color=[bar_colors[i] for i, m in enumerate(v1s_mask) if m]),
                width=0.8,
                hovertemplate='V1s: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Bar(x=[], y=[], showlegend=False), row=1, col=1)

    # Trace 2: Volume MA 30s (скользящее среднее - линия)
    if volma_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(volma_mask) if m],
                y=[float(v) for v, m in zip(volma_30s, volma_mask) if m],
                mode='lines',
                name='VolMA 30s',
                line=dict(color='#9C27B0', width=3),
                hovertemplate='VolMA: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # Trace 3: Текущая точка Volume 1s (выделенная)
    current_v1s = volume_1s[row_idx] if row_idx < len(volume_1s) else np.nan
    if pd.notna(current_v1s):
        # Определяем цвет точки
        if current_v1s > 1000000:
            point_color = '#F44336'
        elif current_v1s > 500000:
            point_color = '#FFC107'
        elif current_v1s > 50000:
            point_color = '#2196F3'
        else:
            point_color = '#666666'

        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[float(current_v1s)],
                mode='markers',
                name='Current Volume',
                marker=dict(size=12, color=point_color, symbol='circle', line=dict(color='white', width=2)),
                hovertemplate=f'Current V1s: ${float(current_v1s):,.0f}<extra></extra>',
                showlegend=False
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # ===== НИЖНИЙ ГРАФИК: VOLUME SPIKE =====

    # Фоновые зоны для spike
    # Зона сигнала (>3.0)
    fig.add_hrect(
        y0=3.0, y1=10.0,
        fillcolor='rgba(255, 193, 7, 0.15)',
        layer='below',
        line_width=0,
        row=2, col=1
    )

    # Зона экстремального всплеска (>5.0)
    fig.add_hrect(
        y0=5.0, y1=10.0,
        fillcolor='rgba(244, 67, 54, 0.2)',
        layer='below',
        line_width=0,
        row=2, col=1
    )

    # Пороговые линии для spike
    fig.add_hline(y=0.5, line_dash='dash', line_color='rgba(100, 100, 100, 0.5)', line_width=1, row=2, col=1)
    fig.add_hline(y=2.0, line_dash='dash', line_color='rgba(33, 150, 243, 0.6)', line_width=1, row=2, col=1)
    fig.add_hline(y=3.0, line_dash='dash', line_color='rgba(255, 193, 7, 0.7)', line_width=1,
                  annotation_text='Signal (3.0)', annotation_position='right', row=2, col=1)
    fig.add_hline(y=5.0, line_dash='dot', line_color='rgba(244, 67, 54, 0.8)', line_width=1,
                  annotation_text='Extreme (5.0)', annotation_position='right', row=2, col=1)

    # Trace 4: Volume Spike линия
    if spike_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(spike_mask) if m],
                y=[float(s) for s, m in zip(volume_spike, spike_mask) if m],
                mode='lines',
                name='Volume Spike',
                line=dict(color='#00BCD4', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 188, 212, 0.2)',
                hovertemplate='Spike: %{y:.2f}x<extra></extra>'
            ),
            row=2, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=2, col=1)

    # Trace 5: Текущая точка Spike (выделенная с динамическим цветом)
    current_spike = volume_spike[row_idx] if row_idx < len(volume_spike) else np.nan
    if pd.notna(current_spike):
        # Определяем цвет точки в зависимости от значения spike
        if current_spike > 5.0:
            spike_color = '#F44336'  # Красный - экстремальный
        elif current_spike > 3.0:
            spike_color = '#FFC107'  # Оранжевый - сигнал
        elif current_spike > 2.0:
            spike_color = '#2196F3'  # Синий - повышенная активность
        else:
            spike_color = '#00BCD4'  # Голубой - нормально

        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[float(current_spike)],
                mode='markers',
                name='Current Spike',
                marker=dict(size=12, color=spike_color, symbol='diamond', line=dict(color='white', width=2)),
                hovertemplate=f'Current Spike: {float(current_spike):.2f}x<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=2, col=1)

    # === Layout ===
    timestamp = df["timestamp_et"].iloc[row_idx] if "timestamp_et" in df.columns else "N/A"
    fig.update_layout(
        title=f'Volume & Spikes @ {timestamp}',
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
        hovermode='x unified',
        height=600
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


def add_volume_traces(fig, df, row_idx):
    """
    Добавляет графики объёмов в основную фигуру (если нужно встроить в общий layout)

    Args:
        fig: Plotly figure object
        df: DataFrame с данными
        row_idx: Текущий индекс строки
    """
    # Эта функция может использоваться если нужно добавить в общую фигуру
    # Пока оставим как заглушку, так как мы делаем отдельный график
    pass
