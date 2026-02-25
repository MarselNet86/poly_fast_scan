"""
Trader Portfolio Chart Widget
График портфеля трейдера (накопительная стоимость позиций)
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Optional, List


def compute_cumulative_portfolio(trades: List[dict], row_mapping: Dict[int, int], max_rows: int) -> Dict[str, np.ndarray]:
    """
    Вычислить накопительную стоимость позиций по времени

    Args:
        trades: Список сделок трейдера
        row_mapping: Маппинг timestamp -> row_idx
        max_rows: Количество строк в DataFrame

    Returns:
        Dict с массивами portfolio_up, portfolio_down, portfolio_total для каждого row_idx
    """
    portfolio_up = np.zeros(max_rows)
    portfolio_down = np.zeros(max_rows)

    # Собрать все сделки с их row_idx
    trade_events = []
    for trade in trades:
        row_idx = row_mapping.get(trade['timestamp'])
        if row_idx is not None and 0 <= row_idx < max_rows:
            trade_events.append({
                'row_idx': row_idx,
                'side': trade['side'],  # 'Up' или 'Down'
                'type': trade['type'],  # 'Buy' или 'Sell'
                'cost': trade['cost'],  # Стоимость сделки в $
                'shares': trade['shares'],
                'price': trade['price']
            })

    # Сортировать по row_idx
    trade_events.sort(key=lambda x: x['row_idx'])

    # Накапливаем позиции
    current_portfolio_up = 0.0
    current_portfolio_down = 0.0
    event_idx = 0

    for row_idx in range(max_rows):
        # Применить все сделки на этом row_idx
        while event_idx < len(trade_events) and trade_events[event_idx]['row_idx'] == row_idx:
            event = trade_events[event_idx]
            cost = event['cost']

            # BUY увеличивает позицию, SELL уменьшает
            if event['type'] == 'Buy':
                if event['side'] == 'Up':
                    current_portfolio_up += cost
                else:
                    current_portfolio_down += cost
            else:  # Sell
                if event['side'] == 'Up':
                    current_portfolio_up -= cost
                else:
                    current_portfolio_down -= cost

            event_idx += 1

        portfolio_up[row_idx] = current_portfolio_up
        portfolio_down[row_idx] = current_portfolio_down

    return {
        'portfolio_up': portfolio_up,
        'portfolio_down': portfolio_down,
        'portfolio_total': portfolio_up + portfolio_down
    }


def create_portfolio_figure(df, row_idx, trader_data: Optional[Dict] = None):
    """
    Создать фигуру для графика Портфель трейдера (накопительная стоимость позиций)

    Args:
        df: DataFrame с данными
        row_idx: Текущий индекс строки
        trader_data: Dict с данными трейдера (trades, row_mapping)

    Returns:
        go.Figure: Plotly figure объект
    """
    fig = make_subplots(
        rows=1, cols=1,
        row_heights=[1.0]
    )

    max_rows = len(df)

    # Вычислить EV если есть данные трейдера
    if trader_data and trader_data.get('trades') and trader_data.get('row_mapping'):
        trades = trader_data['trades']
        row_mapping = trader_data['row_mapping']

        ev_data = compute_cumulative_portfolio(trades, row_mapping, max_rows)
        portfolio_up = ev_data['portfolio_up']
        portfolio_down = ev_data['portfolio_down']
        portfolio_total = ev_data['portfolio_total']

        x_indices = list(range(max_rows))

        # === Trace 0: Portfolio Up (зеленая линия) ===
        fig.add_trace(
            go.Scatter(
                x=x_indices,
                y=portfolio_up.tolist(),
                mode='lines',
                name='Portfolio Up',
                line=dict(color='#00C853', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 200, 83, 0.2)',
                hovertemplate='Portfolio Up: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # === Trace 1: Portfolio Down (красная линия) ===
        fig.add_trace(
            go.Scatter(
                x=x_indices,
                y=portfolio_down.tolist(),
                mode='lines',
                name='Portfolio Down',
                line=dict(color='#F44336', width=2),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.2)',
                hovertemplate='Portfolio Down: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # === Trace 2: Portfolio Total (белая пунктирная линия) ===
        fig.add_trace(
            go.Scatter(
                x=x_indices,
                y=portfolio_total.tolist(),
                mode='lines',
                name='Portfolio Total',
                line=dict(color='#FFFFFF', width=2, dash='dash'),
                hovertemplate='Portfolio Total: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # === Текущие маркеры ===
        if row_idx < max_rows:
            current_portfolio_up = portfolio_up[row_idx]
            current_portfolio_down = portfolio_down[row_idx]
            current_portfolio_total = portfolio_total[row_idx]

            # Marker для Portfolio Up
            fig.add_trace(
                go.Scatter(
                    x=[row_idx],
                    y=[current_portfolio_up],
                    mode='markers',
                    name='Current Up',
                    marker=dict(size=10, color='#00C853', line=dict(color='white', width=2)),
                    showlegend=False,
                    hovertemplate=f'Portfolio Up: ${current_portfolio_up:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

            # Marker для Portfolio Down
            fig.add_trace(
                go.Scatter(
                    x=[row_idx],
                    y=[current_portfolio_down],
                    mode='markers',
                    name='Current Down',
                    marker=dict(size=10, color='#F44336', line=dict(color='white', width=2)),
                    showlegend=False,
                    hovertemplate=f'Portfolio Down: ${current_portfolio_down:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

            # Marker для Portfolio Total
            fig.add_trace(
                go.Scatter(
                    x=[row_idx],
                    y=[current_portfolio_total],
                    mode='markers',
                    name='Current Total',
                    marker=dict(size=12, color='#FFFFFF', line=dict(color='#333', width=2)),
                    showlegend=False,
                    hovertemplate=f'Portfolio Total: ${current_portfolio_total:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

    else:
        # Нет данных трейдера - пустой график
        fig.add_trace(
            go.Scatter(x=[], y=[], mode='lines', name='Portfolio Up', showlegend=True),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=[], y=[], mode='lines', name='Portfolio Down', showlegend=True),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=[], y=[], mode='lines', name='Portfolio Total', showlegend=True),
            row=1, col=1
        )

    # === Нулевая линия ===
    fig.add_hline(
        y=0,
        line_dash='solid',
        line_color='rgba(255, 255, 255, 0.4)',
        line_width=2,
        row=1, col=1
    )

    # === Layout ===
    fig.update_layout(
        title='Портфель трейдера',
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
        tickformat=',.0f',
        tickprefix='$',
        automargin=False,
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.4)',
        zerolinewidth=2,
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
