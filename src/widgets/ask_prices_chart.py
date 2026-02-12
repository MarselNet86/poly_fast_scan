import pandas as pd
import plotly.graph_objects as go

def add_ask_prices_traces(fig, df, row_idx, row_offset=0):
    """
    Добавляет график Ask Prices (UP и DOWN) в фигуру.
    """
    row = 1 + row_offset
    x_indices = list(range(len(df)))

    # 1. UP Ask 1 Price - зеленая линия
    if 'up_ask_1_price' in df.columns:
        up_ask_prices = df['up_ask_1_price'].values
        fig.add_trace(
            go.Scatter(
                x=x_indices, y=up_ask_prices,
                mode='lines', name='UP Ask 1 Price',
                line=dict(color='rgba(0, 200, 83, 0.8)', width=2),
                hovertemplate='UP Ask 1: $%{y:,.2f}<extra></extra>'
            ),
            row=row, col=1
        )

    # 2. DOWN Ask 1 Price - красная линия
    if 'down_ask_1_price' in df.columns:
        down_ask_prices = df['down_ask_1_price'].values
        fig.add_trace(
            go.Scatter(
                x=x_indices, y=down_ask_prices,
                mode='lines', name='DOWN Ask 1 Price',
                line=dict(color='rgba(244, 67, 54, 0.8)', width=2),
                hovertemplate='DOWN Ask 1: $%{y:,.2f}<extra></extra>'
            ),
            row=row, col=1
        )

    # Вертикальная линия текущей позиции
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=row, col=1)

    # Настройка осей
    fig.update_xaxes(
        title_text="Timeline",
        row=row, col=1,
        gridcolor='#444',
        matches='x3'  # Синхронный зум
    )
    fig.update_yaxes(title_text="Ask Price ($)", row=row, col=1, gridcolor='#444')
