"""
Charts Module
Функции создания графиков Plotly для визуализации стакана ордеров
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .data_loader import (
    get_orderbook_data,
    calculate_anomaly_threshold,
    calculate_pressure,
    calculate_orderbook_range,
)
from .config import BAR_SCALE_COEFF
from .widgets.orderbook import add_orderbook_traces
from .widgets.ask_prices_chart import add_ask_prices_traces
from .widgets.btc_chart import add_btc_traces
from .widgets.lag_chart import add_lag_traces
from .widgets.returns_chart import create_returns_figure


def create_orderbook_chart(df, row_idx):
    """
    Создать независимый график Orderbook + Ask Prices для main view.
    Используется та же структура что и pop-out версия.

    Returns:
        go.Figure: Plotly фигура со стаканами и графиком ask prices
    """
    fig = create_orderbook_popout_figure(df, row_idx)
    fig.update_layout(height=700)
    return fig


def create_btc_chart(df, row_idx):
    """
    Создать независимый график BTC Price + Lag для main view.
    Используется та же структура что и pop-out версия.

    Returns:
        go.Figure: Plotly фигура с графиками BTC price и lag
    """
    fig = create_btc_popout_figure(df, row_idx)
    fig.update_layout(height=700)
    return fig


def create_returns_chart(df, row_idx):
    """
    Создать независимый график Returns/Momentum для main view.

    Returns:
        go.Figure: Plotly фигура с графиками доходности (Ret1s, Ret5s)
    """
    fig = create_returns_figure(df, row_idx)
    fig.update_layout(height=700)
    return fig


def create_orderbook_popout_figure(df, row_idx):
    """
    Создать фигуру для pop-out окна Orderbook (стаканы + ask prices)

    Args:
        df: DataFrame с данными
        row_idx: Индекс строки для отображения

    Returns:
        go.Figure: Plotly фигура со стаканами и графиком ask prices
    """
    row = df.iloc[row_idx]
    data = get_orderbook_data(row)

    all_sizes = (
        data['up']['bid_sizes'] + data['up']['ask_sizes'] +
        data['down']['bid_sizes'] + data['down']['ask_sizes']
    )
    anomaly_threshold = calculate_anomaly_threshold(all_sizes)
    range_data = calculate_orderbook_range(df)
    global_max = range_data['max_size']

    # Создаем фигуру с 2 рядами: стаканы и ask prices
    fig = make_subplots(
        rows=2, cols=2,
        horizontal_spacing=0.12,
        vertical_spacing=0.10,
        row_heights=[0.60, 0.40],
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter", "colspan": 2}, None]
        ]
    )

    # Добавляем стаканы (row 1)
    add_orderbook_traces(fig, data, anomaly_threshold, global_max)

    # Добавляем ask prices (row 2)
    _add_ask_prices_for_popout(fig, df, row_idx)

    up_pressure, up_bid_total, up_ask_total = calculate_pressure(
        data['up']['bid_sizes'], data['up']['ask_sizes']
    )
    down_pressure, down_bid_total, down_ask_total = calculate_pressure(
        data['down']['bid_sizes'], data['down']['ask_sizes']
    )

    fig.update_layout(
        title='Orderbook',
        barmode='overlay',
        bargap=0.2,
        bargroupgap=0.1,
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.08, xanchor='center', x=0.5),
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#2d2d2d',
        font=dict(color='white'),
        margin=dict(l=50, r=20, t=60, b=60)
    )

    return fig


def create_btc_popout_figure(df, row_idx):
    """
    Создать фигуру для pop-out окна BTC (btc price + lag)

    Args:
        df: DataFrame с данными
        row_idx: Индекс строки для отображения

    Returns:
        go.Figure: Plotly фигура с графиками BTC price и lag
    """
    # Создаем фигуру с 2 рядами: btc price и lag
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.12,
        row_heights=[0.65, 0.35]
    )

    # Добавляем btc price (row 1)
    _add_btc_for_popout(fig, df, row_idx)

    # Добавляем lag (row 2)
    _add_lag_for_popout(fig, df, row_idx)

    fig.update_layout(
        title='BTC Price & Lag',
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.08, xanchor='center', x=0.5),
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#2d2d2d',
        font=dict(color='white'),
        margin=dict(l=50, r=20, t=60, b=60)
    )

    return fig


def _add_ask_prices_for_popout(fig, df, row_idx):
    """Добавить ask prices график в pop-out (row 2)"""
    # UP Ask Price - зеленая
    up_ask_prices = df['up_ask_1_price'].values if 'up_ask_1_price' in df.columns else np.array([np.nan] * len(df))
    up_mask = ~pd.isna(up_ask_prices)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(up_mask) if m],
            y=[float(p) for p, m in zip(up_ask_prices, up_mask) if m],
            mode='lines', name='UP Ask Price',
            line=dict(color='#00C853', width=2),
            hovertemplate='UP Ask: $%{y:.4f}<extra></extra>'
        ),
        row=2, col=1
    )

    # DOWN Ask Price - красная
    down_ask_prices = df['down_ask_1_price'].values if 'down_ask_1_price' in df.columns else np.array([np.nan] * len(df))
    down_mask = ~pd.isna(down_ask_prices)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(down_mask) if m],
            y=[float(p) for p, m in zip(down_ask_prices, down_mask) if m],
            mode='lines', name='DOWN Ask Price',
            line=dict(color='#F44336', width=2),
            hovertemplate='DOWN Ask: $%{y:.4f}<extra></extra>'
        ),
        row=2, col=1
    )

    # Текущие маркеры
    current_up = up_ask_prices[row_idx] if row_idx < len(up_ask_prices) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_up) else [],
            y=[float(current_up)] if pd.notna(current_up) else [],
            mode='markers', name='Current UP',
            marker=dict(size=10, color='#00C853', line=dict(color='white', width=2)),
            showlegend=False
        ),
        row=2, col=1
    )

    current_down = down_ask_prices[row_idx] if row_idx < len(down_ask_prices) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_down) else [],
            y=[float(current_down)] if pd.notna(current_down) else [],
            mode='markers', name='Current DOWN',
            marker=dict(size=10, color='#F44336', line=dict(color='white', width=2)),
            showlegend=False
        ),
        row=2, col=1
    )

    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=2, col=1)
    fig.update_xaxes(row=2, col=1, gridcolor='#444')
    fig.update_yaxes(row=2, col=1, gridcolor='#444')


def _add_btc_for_popout(fig, df, row_idx):
    """Добавить BTC price график в pop-out (row 1)"""
    x_indices = list(range(len(df)))

    # Binance BTC
    binance_prices = df['binance_btc_price'].values
    fig.add_trace(
        go.Scatter(
            x=x_indices, y=binance_prices,
            mode='lines', name='Binance BTC',
            line=dict(color='#FF6B00', width=2),
            hovertemplate='Binance: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Oracle BTC
    oracle_prices = df['oracle_btc_price'].values if 'oracle_btc_price' in df.columns else np.array([np.nan] * len(df))
    oracle_mask = ~pd.isna(oracle_prices)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(oracle_mask) if m],
            y=[float(p) for p, m in zip(oracle_prices, oracle_mask) if m],
            mode='lines', name='Oracle BTC',
            line=dict(color='#2196F3', width=2),
            hovertemplate='Oracle: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Текущие маркеры
    current_binance = binance_prices[row_idx]
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_binance) else [],
            y=[float(current_binance)] if pd.notna(current_binance) else [],
            mode='markers', name='Current Binance',
            marker=dict(size=12, color='#FF6B00', line=dict(color='white', width=2)),
            showlegend=False
        ),
        row=1, col=1
    )

    current_oracle = oracle_prices[row_idx] if row_idx < len(oracle_prices) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_oracle) else [],
            y=[float(current_oracle)] if pd.notna(current_oracle) else [],
            mode='markers', name='Current Oracle',
            marker=dict(size=12, color='#2196F3', line=dict(color='white', width=2)),
            showlegend=False
        ),
        row=1, col=1
    )

    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=1, col=1)
    fig.update_xaxes(row=1, col=1, gridcolor='#444')
    fig.update_yaxes(row=1, col=1, gridcolor='#444')


def _add_lag_for_popout(fig, df, row_idx):
    """Добавить Lag график в pop-out (row 2)"""
    lag_values = df['lag'].values if 'lag' in df.columns else np.array([np.nan] * len(df))
    lag_mask = ~pd.isna(lag_values)

    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(lag_mask) if m],
            y=[float(lag) for lag, m in zip(lag_values, lag_mask) if m],
            mode='lines', name='Price Lag',
            line=dict(color='#FFC107', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 193, 7, 0.2)',
            hovertemplate='Lag: $%{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )

    fig.add_hline(y=0, line_dash="solid", line_color="rgba(255,255,255,0.3)", line_width=1, row=2, col=1)

    current_lag = lag_values[row_idx] if row_idx < len(lag_values) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_lag) else [],
            y=[float(current_lag)] if pd.notna(current_lag) else [],
            mode='markers', name='Current Lag',
            marker=dict(size=12, color='#FFC107', line=dict(color='white', width=2)),
            showlegend=False
        ),
        row=2, col=1
    )

    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=2, col=1)
    fig.update_xaxes(row=2, col=1, gridcolor='#444')
    fig.update_yaxes(row=2, col=1, gridcolor='#444')
