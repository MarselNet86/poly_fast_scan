"""
Ask Prices Chart Widget
График цен up_ask_1_price (зеленая) и down_ask_1_price (красная)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go


def add_ask_prices_traces(fig, df, row_idx):
    """
    Добавляет графики цен Ask (UP и DOWN контрактов) в фигуру.

    Args:
        fig: Plotly figure
        df: DataFrame с данными
        row_idx: Текущий индекс строки
    """
    # 1. UP Ask 1 Price - зеленая линия
    up_ask_prices = df['up_ask_1_price'].values if 'up_ask_1_price' in df.columns else np.array([np.nan] * len(df))
    up_mask = ~pd.isna(up_ask_prices)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(up_mask) if m],
            y=[float(p) for p, m in zip(up_ask_prices, up_mask) if m],
            mode='lines',
            name='UP Ask Price',
            line=dict(color='#00C853', width=2),  # Зеленый
            hovertemplate='UP Ask: $%{y:.4f}<extra></extra>'
        ),
        row=2, col=1
    )

    # 2. DOWN Ask 1 Price - красная линия
    down_ask_prices = df['down_ask_1_price'].values if 'down_ask_1_price' in df.columns else np.array([np.nan] * len(df))
    down_mask = ~pd.isna(down_ask_prices)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(down_mask) if m],
            y=[float(p) for p, m in zip(down_ask_prices, down_mask) if m],
            mode='lines',
            name='DOWN Ask Price',
            line=dict(color='#F44336', width=2),  # Красный
            hovertemplate='DOWN Ask: $%{y:.4f}<extra></extra>'
        ),
        row=2, col=1
    )

    # 3. Текущая точка UP Ask
    current_up = up_ask_prices[row_idx] if row_idx < len(up_ask_prices) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_up) else [],
            y=[float(current_up)] if pd.notna(current_up) else [],
            mode='markers',
            name='Current UP Ask',
            marker=dict(size=10, color='#00C853', symbol='circle',
                       line=dict(color='white', width=2)),
            hovertemplate=f'UP Ask: ${float(current_up or 0):.4f}<extra></extra>',
            showlegend=False
        ),
        row=2, col=1
    )

    # 4. Текущая точка DOWN Ask
    current_down = down_ask_prices[row_idx] if row_idx < len(down_ask_prices) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_down) else [],
            y=[float(current_down)] if pd.notna(current_down) else [],
            mode='markers',
            name='Current DOWN Ask',
            marker=dict(size=10, color='#F44336', symbol='circle',
                       line=dict(color='white', width=2)),
            hovertemplate=f'DOWN Ask: ${float(current_down or 0):.4f}<extra></extra>',
            showlegend=False
        ),
        row=2, col=1
    )

    # Вертикальная линия текущей позиции
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=2, col=1)

    # Настройка осей
    fig.update_xaxes(row=2, col=1, gridcolor='#444')
    fig.update_yaxes(row=2, col=1, gridcolor='#444')
