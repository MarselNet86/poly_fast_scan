"""
EV Chart Widget
График Expected Value (сумма цен UP + DOWN)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


from typing import Dict, Optional, List


def compute_cumulative_ev(trades: List[dict], row_mapping: Dict[int, int], max_rows: int) -> np.ndarray:
    """
    Вычислить EV (сумма средних цен входа UP + DOWN) по времени

    EV = AvgPriceUp + AvgPriceDown
    AvgPrice = (Quantity1 * Price1 + Quantity2 * Price2) / Total Quantity

    Args:
        trades: Список сделок трейдера
        row_mapping: Маппинг timestamp -> row_idx
        max_rows: Количество строк в DataFrame

    Returns:
        np.ndarray: Массив EV значений для каждого row_idx
    """
    ev_values = np.zeros(max_rows)
    
    # Собрать все сделки с их row_idx
    trade_events = []
    for trade in trades:
        row_idx = row_mapping.get(trade['timestamp'])
        if row_idx is not None and 0 <= row_idx < max_rows:
            trade_events.append({
                'row_idx': row_idx,
                'side': trade['side'],  # 'Up' или 'Down'
                'price': trade['price'], # В центах (0-100)
                'shares': trade['shares']
            })

    # Сортировать по row_idx
    trade_events.sort(key=lambda x: x['row_idx'])

    # Накапливаем средние цены
    sum_cost_up = 0.0
    sum_shares_up = 0.0
    sum_cost_down = 0.0
    sum_shares_down = 0.0
    
    event_idx = 0

    for row_idx in range(max_rows):
        # Применить все сделки на этом row_idx
        while event_idx < len(trade_events) and trade_events[event_idx]['row_idx'] == row_idx:
            event = trade_events[event_idx]
            if event['side'] == 'Up':
                sum_cost_up += event['price'] * event['shares']
                sum_shares_up += event['shares']
            else:
                sum_cost_down += event['price'] * event['shares']
                sum_shares_down += event['shares']
            event_idx += 1

        avg_up = (sum_cost_up / sum_shares_up) if sum_shares_up > 0 else 0.0
        avg_down = (sum_cost_down / sum_shares_down) if sum_shares_down > 0 else 0.0
        
        ev_values[row_idx] = avg_up + avg_down

    return ev_values


def create_ev_figure(df, row_idx, trader_data: Optional[Dict] = None):
    """
    Создать фигуру для EV графика

    Args:
        df: DataFrame с данными
        row_idx: Текущий индекс строки
        trader_data: Optional dict с данными трейдера

    Returns:
        go.Figure: Plotly figure объект
    """
    fig = make_subplots(
        rows=1, cols=1,
        row_heights=[1.0]
    )

    max_rows = len(df)
    ev = np.zeros(max_rows)

    # Вычислить EV на основе трейдов если они есть
    if trader_data and trader_data.get('trades') and trader_data.get('row_mapping'):
        ev = compute_cumulative_ev(
            trader_data['trades'], 
            trader_data['row_mapping'], 
            max_rows
        )
    else:
        # Fallback: старая логика (микропрайс) если нет данных трейдера
        pm_up_microprice = df['pm_up_microprice'].values if 'pm_up_microprice' in df.columns else np.zeros(max_rows)
        pm_down_microprice = df['pm_down_microprice'].values if 'pm_down_microprice' in df.columns else np.zeros(max_rows)
        ev = pm_up_microprice + pm_down_microprice

    # Фильтрация NaN
    ev_mask = ~pd.isna(ev)
    # Игнорировать нулевые значения если это результат отсутствия сделок
    if not (trader_data and trader_data.get('trades')):
        ev_mask = ev_mask & (ev > 0)

    # Перевод в доллары (0.00-1.00) если данные в центах
    ev = ev / 100.0

    # === Trace 0: EV линия (синяя) ===
    if ev_mask.any():
        fig.add_trace(
            go.Scatter(
                x=[i for i, m in enumerate(ev_mask) if m],
                y=[float(v) for v, m in zip(ev, ev_mask) if m],
                mode='lines',
                name='EV (Weighted Avg)',
                line=dict(color='#2196F3', width=2),
                hovertemplate='EV: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], showlegend=False), row=1, col=1)

    # === Маркер текущей позиции ===
    if row_idx < max_rows and ev_mask[row_idx]:
        current_ev = float(ev[row_idx])
        fig.add_trace(
            go.Scatter(
                x=[row_idx],
                y=[current_ev],
                mode='markers',
                name='Current EV',
                marker=dict(size=10, color='#2196F3', line=dict(color='white', width=2)),
                showlegend=False,
                hovertemplate=f'Current EV: {current_ev:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # === Layout ===
    fig.update_layout(
        title='EV (Expected Value) - Trader Entry Sum',
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
        tickformat='.2f',
        automargin=False,
        row=1, col=1
    )

    fig.update_xaxes(
        title_font=dict(color='white', size=12),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        range=[-100, len(df)],
        row=1, col=1
    )

    # Добавляем вертикальную линию текущего времени
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=1, col=1)

    return fig
