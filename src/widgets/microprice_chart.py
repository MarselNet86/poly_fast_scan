"""
Microprice Chart Widget
График микроцены (pm_up_microprice, pm_down_microprice)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional


def build_timestamp_to_row_mapping(df: pd.DataFrame, trades: List[dict]) -> Dict[int, int]:
    """
    Create mapping from trade timestamps to CSV row indices

    Uses nearest-neighbor matching with 5-second tolerance

    Args:
        df: DataFrame with timestamp_ms column
        trades: List of trade dicts with 'timestamp' key (in seconds)

    Returns:
        Dict mapping trade timestamp -> row_idx
    """
    if 'timestamp_ms' not in df.columns:
        return {}

    timestamps_ms = df['timestamp_ms'].values
    mapping = {}

    for trade in trades:
        trade_ts_ms = trade['timestamp'] * 1000  # Convert to milliseconds

        # Find nearest row using numpy (handles duplicate timestamps)
        abs_diff = np.abs(timestamps_ms - trade_ts_ms)
        idx = np.argmin(abs_diff)

        # Check tolerance (±5 seconds = ±5000 ms)
        if abs_diff[idx] <= 5000:
            mapping[trade['timestamp']] = int(idx)

    return mapping


def create_microprice_figure(df, row_idx, trader_data: Optional[Dict] = None):
    """
    Создать фигуру для Microprice графика (2 линии)

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
    pm_up_microprice = df['pm_up_microprice'].values if 'pm_up_microprice' in df.columns else np.array([np.nan] * len(df))
    pm_down_microprice = df['pm_down_microprice'].values if 'pm_down_microprice' in df.columns else np.array([np.nan] * len(df))

    # Фильтрация NaN
    up_mask = ~pd.isna(pm_up_microprice)
    down_mask = ~pd.isna(pm_down_microprice)

    # === Trace 0: UP Microprice (зеленая линия) ===
    if up_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(up_mask) if m],
                y=[float(v) for v, m in zip(pm_up_microprice, up_mask) if m],
                mode='lines',
                name='UP Microprice',
                line=dict(color='#00C853', width=2),
                hovertemplate='UP Microprice: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 1: DOWN Microprice (красная линия) ===
    if down_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(down_mask) if m],
                y=[float(v) for v, m in zip(pm_down_microprice, down_mask) if m],
                mode='lines',
                name='DOWN Microprice',
                line=dict(color='#F44336', width=2),
                hovertemplate='DOWN Microprice: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Trace 2 & 3: Trader BUY/SELL Points ===
    if trader_data and trader_data.get('trades'):
        trades = trader_data['trades']
        row_mapping = trader_data.get('row_mapping', {})

        # Separate BUY and SELL trades
        buy_trades = [t for t in trades if t['type'] == 'Buy']
        sell_trades = [t for t in trades if t['type'] == 'Sell']

        # Track used X coordinates to avoid overlapping
        used_x_coords = {}

        # Trace 2: BUY markers
        if buy_trades:
            buy_x = []
            buy_y = []
            buy_text = []

            for trade in buy_trades:
                row_idx_mapped = row_mapping.get(trade['timestamp'])
                if row_idx_mapped is not None and row_idx_mapped < len(df):
                    # Get microprice value at this row
                    microprice_col = 'pm_up_microprice' if trade['side'] == 'Up' else 'pm_down_microprice'
                    if microprice_col in df.columns:
                        microprice_val = df.iloc[row_idx_mapped][microprice_col]
                        if pd.notna(microprice_val):
                            # Apply offset if this X coordinate is already used
                            x_coord = row_idx_mapped
                            if x_coord in used_x_coords:
                                used_x_coords[x_coord] += 0.3
                                x_coord = row_idx_mapped + used_x_coords[row_idx_mapped]
                            else:
                                used_x_coords[x_coord] = 0.0

                            buy_x.append(x_coord)
                            buy_y.append(float(microprice_val))
                            buy_text.append(
                                f"BUY {trade['side']}<br>"
                                f"Price: {trade['price']:.2f}¢<br>"
                                f"Shares: {trade['shares']:.2f}<br>"
                                f"Cost: ${trade['cost']:.2f}"
                            )

            fig.add_trace(
                go.Scatter(
                    x=buy_x,
                    y=buy_y,
                    mode='markers',
                    name='Trader BUY',
                    marker=dict(
                        symbol='x',
                        size=12,
                        color='#FFD700',  # Gold
                        line=dict(width=2)
                    ),
                    text=buy_text,
                    hovertemplate='%{text}<extra></extra>'
                ),
                row=1, col=1
            )

        # Trace 3: SELL markers
        if sell_trades:
            sell_x = []
            sell_y = []
            sell_text = []

            for trade in sell_trades:
                row_idx_mapped = row_mapping.get(trade['timestamp'])
                if row_idx_mapped is not None and row_idx_mapped < len(df):
                    microprice_col = 'pm_up_microprice' if trade['side'] == 'Up' else 'pm_down_microprice'
                    if microprice_col in df.columns:
                        microprice_val = df.iloc[row_idx_mapped][microprice_col]
                        if pd.notna(microprice_val):
                            # Apply offset if this X coordinate is already used
                            x_coord = row_idx_mapped
                            if x_coord in used_x_coords:
                                used_x_coords[x_coord] += 0.3
                                x_coord = row_idx_mapped + used_x_coords[row_idx_mapped]
                            else:
                                used_x_coords[x_coord] = 0.0

                            sell_x.append(x_coord)
                            sell_y.append(float(microprice_val))
                            sell_text.append(
                                f"SELL {trade['side']}<br>"
                                f"Price: {trade['price']:.2f}¢<br>"
                                f"Shares: {trade['shares']:.2f}<br>"
                                f"Cost: ${trade['cost']:.2f}"
                            )

            fig.add_trace(
                go.Scatter(
                    x=sell_x,
                    y=sell_y,
                    mode='markers',
                    name='Trader SELL',
                    marker=dict(
                        symbol='circle',
                        size=10,
                        color='#FF4444',  # Red
                        line=dict(width=2, color='white')
                    ),
                    text=sell_text,
                    hovertemplate='%{text}<extra></extra>'
                ),
                row=1, col=1
            )

    # === Layout ===
    fig.update_layout(
        title='Microprice (Микроцена)',
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
        row=1, col=1
    )

    fig.update_xaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        row=1, col=1
    )

    # Добавляем вертикальную линию текущего времени
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=1, col=1)

    return fig
