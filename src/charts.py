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


def create_orderbook_figure(df, row_idx):
    """
    Создать фигуру стакана ордеров для указанной строки данных

    Args:
        df: DataFrame с данными
        row_idx: Индекс строки для отображения

    Returns:
        go.Figure: Plotly фигура со стаканом ордеров, ценовым графиком и lag
    """
    row = df.iloc[row_idx]
    data = get_orderbook_data(row)

    # Вычисляем пороги аномалий
    all_sizes = (
        data['up']['bid_sizes'] + data['up']['ask_sizes'] +
        data['down']['bid_sizes'] + data['down']['ask_sizes']
    )
    anomaly_threshold = calculate_anomaly_threshold(all_sizes)

    # Вычисляем глобальный максимум ЗА ВЕСЬ ПЕРИОД
    range_data = calculate_orderbook_range(df)
    global_max = range_data['max_size']
    
    # Создаем фигуру с четырьмя рядами: стаканы, ask prices, btc price, lag
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=('UP Contract Orderbook', 'DOWN Contract Orderbook', '', '', '', '', '', ''),
        horizontal_spacing=0.12,
        vertical_spacing=0.06,
        row_heights=[0.40, 0.20, 0.25, 0.15],
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter", "colspan": 2}, None],
            [{"type": "scatter", "colspan": 2}, None],
            [{"type": "scatter", "colspan": 2}, None]
        ]
    )

    # Добавляем виджеты
    add_orderbook_traces(fig, data, anomaly_threshold, global_max)
    add_ask_prices_traces(fig, df, row_idx)
    add_btc_traces(fig, df, row_idx)
    add_lag_traces(fig, df, row_idx)

    # Вычисляем метрики давления
    up_pressure, up_bid_total, up_ask_total = calculate_pressure(
        data['up']['bid_sizes'], data['up']['ask_sizes']
    )
    down_pressure, down_bid_total, down_ask_total = calculate_pressure(
        data['down']['bid_sizes'], data['down']['ask_sizes']
    )

    fig.update_layout(
        title=dict(
            text=f"Orderbook @ {data['timestamp']}<br>" +
                 f"<sub>UP: {up_pressure} pressure (Bids: ${up_bid_total:,.0f} vs Asks: ${up_ask_total:,.0f}) | " +
                 f"DOWN: {down_pressure} pressure (Bids: ${down_bid_total:,.0f} vs Asks: ${down_ask_total:,.0f})</sub>",
            font=dict(size=14)
        ),
        barmode='overlay',
        bargap=0.2,
        bargroupgap=0.1,
        height=1100,
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5),
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#2d2d2d',
        font=dict(color='white')
    )

    return fig
