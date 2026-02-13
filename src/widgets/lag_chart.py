import pandas as pd
import numpy as np
import plotly.graph_objects as go

def add_lag_traces(fig, df, row_idx):
    """
    Добавляет график Lag (разница Binance - Oracle) в фигуру.
    """
    lag_values = df['lag'].values if 'lag' in df.columns else np.array([np.nan] * len(df))
    lag_mask = ~pd.isna(lag_values)

    # Линия lag
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
        row=4, col=1
    )

    # Нулевая линия
    fig.add_hline(
        y=0, line_dash="solid", line_color="rgba(255,255,255,0.3)",
        line_width=1,
        row=4, col=1
    )

    # Текущая точка lag
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
        row=4, col=1
    )

    # Вертикальная линия текущей позиции
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=4, col=1)

    # Настройка осей
    fig.update_xaxes(
        row=4, col=1,
        gridcolor='#444',
        matches='x4'  # Связать с xaxis4 (btc price chart) для синхронного зума
    )
    fig.update_yaxes(row=4, col=1, gridcolor='#444')
