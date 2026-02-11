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


def get_bar_colors(sizes, base_color, anomaly_color, threshold):
    """
    Определить цвета столбцов с учетом аномалий

    Args:
        sizes: Список размеров
        base_color: Базовый цвет
        anomaly_color: Цвет для аномальных значений
        threshold: Порог аномалии

    Returns:
        list: Список цветов для каждого столбца
    """
    colors = []
    for s in sizes:
        if pd.notna(s) and s > threshold:
            colors.append(anomaly_color)
        else:
            colors.append(base_color)
    return colors


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
    
    # Создаем фигуру с тремя рядами: стаканы, цена, lag
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=('UP Contract Orderbook', 'DOWN Contract Orderbook', '', '', '', ''),
        horizontal_spacing=0.12,
        vertical_spacing=0.08,
        row_heights=[0.45, 0.35, 0.20],
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter", "colspan": 2}, None],
            [{"type": "scatter", "colspan": 2}, None]
        ]
    )

    # UP стакан - биды
    up_bid_colors = get_bar_colors(
        data['up']['bid_sizes'],
        'rgba(0, 200, 83, 0.7)', 'rgba(0, 255, 100, 1)',
        anomaly_threshold
    )
    fig.add_trace(
        go.Bar(
            y=[f"{p:.2f}" if pd.notna(p) else "N/A" for p in data['up']['bid_prices']],
            x=[-abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in data['up']['bid_sizes']],
            orientation='h',
            name='UP Bids',
            marker=dict(color=up_bid_colors, line=dict(color='darkgreen', width=1)),
            text=[f"${s:,.0f}" if pd.notna(s) else "" for s in data['up']['bid_sizes']],
            textposition='auto',
            textfont=dict(size=14, color='white'),
            cliponaxis=False,
            hovertemplate='Price: %{y}<br>Size: %{text}<extra></extra>'
        ),
        row=1, col=1
    )

    # UP стакан - аски
    up_ask_colors = get_bar_colors(
        data['up']['ask_sizes'],
        'rgba(244, 67, 54, 0.7)', 'rgba(255, 100, 100, 1)',
        anomaly_threshold
    )
    fig.add_trace(
        go.Bar(
            y=[f"{p:.2f}" if pd.notna(p) else "N/A" for p in data['up']['ask_prices']],
            x=[abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in data['up']['ask_sizes']],
            orientation='h',
            name='UP Asks',
            marker=dict(color=up_ask_colors, line=dict(color='darkred', width=1)),
            text=[f"${s:,.0f}" if pd.notna(s) else "" for s in data['up']['ask_sizes']],
            textposition='auto',
            textfont=dict(size=14, color='white'),
            cliponaxis=False,
            hovertemplate='Price: %{y}<br>Size: %{text}<extra></extra>'
        ),
        row=1, col=1
    )

    # DOWN стакан - биды
    down_bid_colors = get_bar_colors(
        data['down']['bid_sizes'],
        'rgba(0, 200, 83, 0.7)', 'rgba(0, 255, 100, 1)',
        anomaly_threshold
    )

    fig.add_trace(
        go.Bar(
            y=[f"{p:.2f}" if pd.notna(p) else "N/A" for p in data['down']['bid_prices']],
            x=[-abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in data['down']['bid_sizes']],
            orientation='h',
            name='DOWN Bids',
            marker=dict(color=down_bid_colors, line=dict(color='darkgreen', width=1)),
            text=[f"${s:,.0f}" if pd.notna(s) else "" for s in data['down']['bid_sizes']],
            textposition='auto',
            textfont=dict(size=14, color='white'),
            cliponaxis=False,
            hovertemplate='Price: %{y}<br>Size: %{text}<extra></extra>'
        ),
        row=1, col=2
    )

    # DOWN стакан - аски
    down_ask_colors = get_bar_colors(
        data['down']['ask_sizes'],
        'rgba(244, 67, 54, 0.7)', 'rgba(255, 100, 100, 1)',
        anomaly_threshold
    )
    fig.add_trace(
        go.Bar(
            y=[f"{p:.2f}" if pd.notna(p) else "N/A" for p in data['down']['ask_prices']],
            x=[abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in data['down']['ask_sizes']],
            orientation='h',
            name='DOWN Asks',
            marker=dict(color=down_ask_colors, line=dict(color='darkred', width=1)),
            text=[f"${s:,.0f}" if pd.notna(s) else "" for s in data['down']['ask_sizes']],
            textposition='auto',
            textfont=dict(size=14, color='white'),
            cliponaxis=False,
            hovertemplate='Price: %{y}<br>Size: %{text}<extra></extra>'
        ),
        row=1, col=2
    )

    # === ЦЕНОВОЙ ГРАФИК (row=2) ===
    x_indices = list(range(len(df)))

    # 1. Binance BTC - оранжевая линия
    binance_prices = df['binance_btc_price'].values
    fig.add_trace(
        go.Scatter(
            x=x_indices, y=binance_prices,
            mode='lines', name='Binance BTC',
            line=dict(color='#FF6B00', width=2),
            hovertemplate='Binance: $%{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )

    # 2. VWAP 30s - серая пунктирная линия
    vwap = df['binance_vwap_30s'].values if 'binance_vwap_30s' in df.columns else np.array([np.nan] * len(df))
    vwap_mask = ~pd.isna(vwap)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(vwap_mask) if m],
            y=[float(v) for v, m in zip(vwap, vwap_mask) if m],
            mode='lines', name='VWAP 30s',
            line=dict(color='#888', width=1, dash='dot'),
            hovertemplate='VWAP: $%{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )

    # 3. Oracle BTC - синяя линия
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
        row=2, col=1
    )

    # 4. Strike price - первая не-NaN цена oracle
    first_oracle = next((float(p) for p in oracle_prices if pd.notna(p)), None)
    if first_oracle:
        fig.add_hline(
            y=first_oracle, line_dash="dash", line_color="rgba(255,255,255,0.5)",
            annotation_text=f"Strike: ${first_oracle:,.0f}",
            annotation_position="right",
            annotation_font_color="white",
            row=2, col=1
        )

    # 5. Текущая точка Binance (trace 7)
    current_binance = binance_prices[row_idx]
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_binance) else [],
            y=[float(current_binance)] if pd.notna(current_binance) else [],
            mode='markers', name='Current Binance',
            marker=dict(size=12, color='#FF6B00', symbol='circle',
                       line=dict(color='white', width=2)),
            hovertemplate=f'Binance: ${float(current_binance or 0):,.2f}<extra></extra>',
            showlegend=False,
            visible=True
        ),
        row=2, col=1
    )

    # 6. Текущая точка Oracle (trace 8)
    current_oracle = oracle_prices[row_idx] if row_idx < len(oracle_prices) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_oracle) else [],
            y=[float(current_oracle)] if pd.notna(current_oracle) else [],
            mode='markers', name='Current Oracle',
            marker=dict(size=12, color='#2196F3', symbol='circle',
                       line=dict(color='white', width=2)),
            hovertemplate=f'Oracle: ${float(current_oracle or 0):,.2f}<extra></extra>',
            showlegend=False,
            visible=True
        ),
        row=2, col=1
    )

    # Вертикальная линия текущей позиции на графиках
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=2, col=1)

    # === LAG ГРАФИК (row=3) - разница между Binance и Oracle ===
    lag_values = df['lag'].values if 'lag' in df.columns else np.array([np.nan] * len(df))
    lag_mask = ~pd.isna(lag_values)

    # Линия lag (trace 9)
    fig.add_trace(
        go.Scatter(
            x=[i for i, m in enumerate(lag_mask) if m],
            y=[float(lag) for lag, m in zip(lag_values, lag_mask) if m],
            mode='lines',
            name='Price Lag (Binance - Oracle)',
            line=dict(color='#FFC107', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 193, 7, 0.2)',
            hovertemplate='Lag: $%{y:,.2f}<extra></extra>'
        ),
        row=3, col=1
    )

    # Нулевая линия
    fig.add_hline(
        y=0, line_dash="solid", line_color="rgba(255,255,255,0.3)",
        line_width=1,
        row=3, col=1
    )

    # Текущая точка lag (trace 10)
    current_lag = lag_values[row_idx] if row_idx < len(lag_values) else np.nan
    fig.add_trace(
        go.Scatter(
            x=[row_idx] if pd.notna(current_lag) else [],
            y=[float(current_lag)] if pd.notna(current_lag) else [],
            mode='markers',
            name='Current Lag',
            marker=dict(size=12, color='#FFC107', symbol='circle',
                       line=dict(color='white', width=2)),
            hovertemplate=f'Lag: ${float(current_lag or 0):,.2f}<extra></extra>',
            showlegend=False,
            visible=True
        ),
        row=3, col=1
    )

    # Вертикальная линия текущей позиции на lag графике
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=3, col=1)

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
        bargap=0.2,  # Промежуток между барами (30%)
        bargroupgap=0.1,  # Промежуток между группами баров (10%)
        height=900,  # Увеличена высота для третьего ряда
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5),
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#2d2d2d',
        font=dict(color='white')
    )

    fig.update_xaxes(
        title_text="<- Bids | Asks ->", 
        row=1, col=1, 
        gridcolor='#444',
        range=[-global_max, global_max],  # Единый диапазон
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.5)',
        zerolinewidth=2
    )
    fig.update_xaxes(
        title_text="<- Bids | Asks ->", 
        row=1, col=2, 
        gridcolor='#444',
        range=[-global_max, global_max],  # Единый диапазон
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.5)',
        zerolinewidth=2
    )
    fig.update_yaxes(title_text="Price Level", row=1, col=1, gridcolor='#444')
    fig.update_yaxes(title_text="Price Level", row=1, col=2, gridcolor='#444')

    # Оси для ценового графика (row=2)
    fig.update_xaxes(title_text="Timeline", row=2, col=1, gridcolor='#444')
    fig.update_yaxes(title_text="BTC Price ($)", row=2, col=1, gridcolor='#444')

    # Оси для lag графика (row=3) - связаны с price chart через matches
    fig.update_xaxes(
        title_text="Timeline",
        row=3, col=1,
        gridcolor='#444',
        matches='x3'  # Связать с xaxis3 (price chart) для синхронного зума
    )
    fig.update_yaxes(title_text="Lag ($)", row=3, col=1, gridcolor='#444')

    return fig
