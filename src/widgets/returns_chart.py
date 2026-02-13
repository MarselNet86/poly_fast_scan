"""
Returns/Momentum Chart Widget
График моментума и доходности BTC
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go


def add_returns_traces(fig, df, row_idx):
    """
    Добавляет графики доходности (Returns/Momentum) в фигуру.

    Args:
        fig: Plotly figure object
        df: DataFrame с данными
        row_idx: Текущий индекс строки
    """
    # Извлекаем данные доходности
    ret1s = df['binance_ret1s_x100'].values if 'binance_ret1s_x100' in df.columns else np.array([np.nan] * len(df))
    ret5s = df['binance_ret5s_x100'].values if 'binance_ret5s_x100' in df.columns else np.array([np.nan] * len(df))

    # Фильтруем NaN значения
    ret1s_mask = ~pd.isna(ret1s)
    ret5s_mask = ~pd.isna(ret5s)

    # === Фоновые зоны для пороговых значений ===

    # Зона сильного импульса вверх (> +0.10 bp)
    fig.add_hrect(
        y0=0.10, y1=1.0,  # Максимум 1.0 bp для отображения
        fillcolor='rgba(0, 200, 83, 0.15)',
        layer='below',
        line_width=0,
        row=4, col=1
    )

    # Зона сильного импульса вниз (< -0.10 bp)
    fig.add_hrect(
        y0=-1.0, y1=-0.10,  # Минимум -1.0 bp для отображения
        fillcolor='rgba(244, 67, 54, 0.15)',
        layer='below',
        line_width=0,
        row=4, col=1
    )

    # === Пороговые линии ===

    # Нулевая линия (обязательная)
    fig.add_hline(
        y=0,
        line_dash='solid',
        line_color='rgba(255, 255, 255, 0.3)',
        line_width=2,
        row=4, col=1
    )

    # Пороговые зоны ±0.05 (пунктир) - импульс
    fig.add_hline(
        y=0.05,
        line_dash='dash',
        line_color='rgba(0, 200, 83, 0.5)',
        line_width=1,
        annotation_text='Импульс +0.05',
        annotation_position='left',
        annotation_font_size=10,
        annotation_font_color='rgba(0, 200, 83, 0.8)',
        row=4, col=1
    )

    fig.add_hline(
        y=-0.05,
        line_dash='dash',
        line_color='rgba(244, 67, 54, 0.5)',
        line_width=1,
        annotation_text='Импульс -0.05',
        annotation_position='left',
        annotation_font_size=10,
        annotation_font_color='rgba(244, 67, 54, 0.8)',
        row=4, col=1
    )

    # Сильные пороги ±0.10
    fig.add_hline(
        y=0.10,
        line_dash='dot',
        line_color='rgba(0, 255, 100, 0.7)',
        line_width=1,
        annotation_text='Сильный +0.10',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(0, 255, 100, 0.9)',
        row=4, col=1
    )

    fig.add_hline(
        y=-0.10,
        line_dash='dot',
        line_color='rgba(255, 100, 100, 0.7)',
        line_width=1,
        annotation_text='Сильный -0.10',
        annotation_position='right',
        annotation_font_size=10,
        annotation_font_color='rgba(255, 100, 100, 0.9)',
        row=4, col=1
    )

    # === Ret5s - сглаженный тренд (толстая линия) ===
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(ret5s_mask) if m],
            y=[float(v) for v, m in zip(ret5s, ret5s_mask) if m],
            mode='lines',
            name='Ret 5s (тренд)',
            line=dict(color='#9C27B0', width=3),  # Фиолетовая толстая линия
            hovertemplate='Ret5s: %{y:.3f} bp<extra></extra>'
        ),
        row=4, col=1
    )

    # === Ret1s - быстрый сигнал (тонкая линия + точки) ===
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(ret1s_mask) if m],
            y=[float(v) for v, m in zip(ret1s, ret1s_mask) if m],
            mode='lines+markers',
            name='Ret 1s (сигнал)',
            line=dict(color='#00BCD4', width=1),  # Голубая тонкая линия
            marker=dict(size=3, color='#00BCD4'),
            hovertemplate='Ret1s: %{y:.3f} bp<extra></extra>'
        ),
        row=4, col=1
    )

    # === Текущая точка Ret1s (выделенная) ===
    current_ret1s = ret1s[row_idx] if row_idx < len(ret1s) else np.nan
    if pd.notna(current_ret1s):
        # Определяем цвет точки в зависимости от значения
        if current_ret1s > 0.10:
            point_color = '#00FF64'  # Ярко-зеленый (сильный UP)
        elif current_ret1s < -0.10:
            point_color = '#FF6464'  # Ярко-красный (сильный DOWN)
        elif abs(current_ret1s) > 0.05:
            point_color = '#FFB300'  # Оранжевый (импульс)
        else:
            point_color = '#00BCD4'  # Голубой (спокойный)

        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[float(current_ret1s)],
                mode='markers',
                name='Current Ret1s',
                marker=dict(
                    size=12,
                    color=point_color,
                    symbol='circle',
                    line=dict(color='white', width=2)
                ),
                hovertemplate=f'Текущий Ret1s: {float(current_ret1s):.3f} bp<extra></extra>',
                showlegend=False
            ),
            row=4, col=1
        )

    # === Текущая точка Ret5s (выделенная) ===
    current_ret5s = ret5s[row_idx] if row_idx < len(ret5s) else np.nan
    if pd.notna(current_ret5s):
        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[float(current_ret5s)],
                mode='markers',
                name='Current Ret5s',
                marker=dict(
                    size=10,
                    color='#9C27B0',
                    symbol='diamond',
                    line=dict(color='white', width=2)
                ),
                hovertemplate=f'Текущий Ret5s: {float(current_ret5s):.3f} bp<extra></extra>',
                showlegend=False
            ),
            row=4, col=1
        )

    # === Layout для подграфика Returns ===
    fig.update_yaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.3)',
        zerolinewidth=2,
        row=4, col=1
    )

    fig.update_xaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=4, col=1
    )


def create_returns_figure(df, row_idx):
    """
    Создать отдельную фигуру только для Returns/Momentum

    Args:
        df: DataFrame с данными
        row_idx: Текущий индекс строки

    Returns:
        go.Figure: Plotly figure объект
    """
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=1,
        vertical_spacing=0.12,
        row_heights=[1.0]
    )

    # Добавляем графики
    ret1s = df['binance_ret1s_x100'].values if 'binance_ret1s_x100' in df.columns else np.array([np.nan] * len(df))
    ret5s = df['binance_ret5s_x100'].values if 'binance_ret5s_x100' in df.columns else np.array([np.nan] * len(df))

    ret1s_mask = ~pd.isna(ret1s)
    ret5s_mask = ~pd.isna(ret5s)

    # === Фоновые зоны ===
    fig.add_hrect(
        y0=0.10, y1=1.0,
        fillcolor='rgba(0, 200, 83, 0.15)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    fig.add_hrect(
        y0=-1.0, y1=-0.10,
        fillcolor='rgba(244, 67, 54, 0.15)',
        layer='below',
        line_width=0,
        row=1, col=1
    )

    # === Нулевая линия ===
    fig.add_hline(
        y=0,
        line_dash='solid',
        line_color='rgba(255, 255, 255, 0.3)',
        line_width=2,
        row=1, col=1
    )

    # === Пороговые линии ===
    fig.add_hline(y=0.05, line_dash='dash', line_color='rgba(0, 200, 83, 0.5)', line_width=1, row=1, col=1)
    fig.add_hline(y=-0.05, line_dash='dash', line_color='rgba(244, 67, 54, 0.5)', line_width=1, row=1, col=1)
    fig.add_hline(y=0.10, line_dash='dot', line_color='rgba(0, 255, 100, 0.7)', line_width=1, row=1, col=1)
    fig.add_hline(y=-0.10, line_dash='dot', line_color='rgba(255, 100, 100, 0.7)', line_width=1, row=1, col=1)

    # === Trace 0: Ret5s линия ===
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(ret5s_mask) if m],
            y=[float(v) for v, m in zip(ret5s, ret5s_mask) if m],
            mode='lines',
            name='Ret 5s (тренд)',
            line=dict(color='#9C27B0', width=3),
            hovertemplate='Ret5s: %{y:.3f} bp<extra></extra>'
        ),
        row=1, col=1
    )

    # === Trace 1: Ret1s линия ===
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(ret1s_mask) if m],
            y=[float(v) for v, m in zip(ret1s, ret1s_mask) if m],
            mode='lines+markers',
            name='Ret 1s (сигнал)',
            line=dict(color='#00BCD4', width=1),
            marker=dict(size=3, color='#00BCD4'),
            hovertemplate='Ret1s: %{y:.3f} bp<extra></extra>'
        ),
        row=1, col=1
    )

    # === Trace 2: Текущая точка Ret1s ===
    current_ret1s = ret1s[row_idx] if row_idx < len(ret1s) else np.nan
    if pd.notna(current_ret1s):
        # Определяем цвет
        if current_ret1s > 0.10:
            point_color = '#00FF64'
        elif current_ret1s < -0.10:
            point_color = '#FF6464'
        elif abs(current_ret1s) > 0.05:
            point_color = '#FFB300'
        else:
            point_color = '#00BCD4'

        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[float(current_ret1s)],
                mode='markers',
                name='Current Ret1s',
                marker=dict(size=12, color=point_color, symbol='circle', line=dict(color='white', width=2)),
                hovertemplate=f'Текущий Ret1s: {float(current_ret1s):.3f} bp<extra></extra>',
                showlegend=False
            ),
            row=1, col=1
        )
    else:
        # Пустой trace для сохранения индексов
        fig.add_trace(
            go.Scatter(x=[], y=[], mode='markers', showlegend=False),
            row=1, col=1
        )

    # === Trace 3: Текущая точка Ret5s ===
    current_ret5s = ret5s[row_idx] if row_idx < len(ret5s) else np.nan
    if pd.notna(current_ret5s):
        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[float(current_ret5s)],
                mode='markers',
                name='Current Ret5s',
                marker=dict(size=10, color='#9C27B0', symbol='diamond', line=dict(color='white', width=2)),
                hovertemplate=f'Текущий Ret5s: {float(current_ret5s):.3f} bp<extra></extra>',
                showlegend=False
            ),
            row=1, col=1
        )
    else:
        # Пустой trace для сохранения индексов
        fig.add_trace(
            go.Scatter(x=[], y=[], mode='markers', showlegend=False),
            row=1, col=1
        )

    # === Layout ===
    fig.update_layout(
        title='Ret1s & Ret5s',
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
