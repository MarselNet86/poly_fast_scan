import pandas as pd
import numpy as np
import plotly.graph_objects as go

def add_btc_traces(fig, df, row_idx):
    """
    Добавляет графики цены BTC (Binance, Oracle, VWAP, Strike) в фигуру.
    """
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
        row=3, col=1
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
        row=3, col=1
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
        row=3, col=1
    )

    # 4. Strike price - первая не-NaN цена oracle
    first_oracle = next((float(p) for p in oracle_prices if pd.notna(p)), None)
    if first_oracle:
        fig.add_hline(
            y=first_oracle, line_dash="dash", line_color="rgba(255,255,255,0.5)",
            annotation_text=f"Strike: ${first_oracle:,.0f}",
            annotation_position="right",
            annotation_font_color="white",
            row=3, col=1
        )

    # 5. Текущая точка Binance
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
        row=3, col=1
    )

    # 6. Текущая точка Oracle
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
        row=3, col=1
    )

    # Вертикальная линия текущей позиции
    fig.add_vline(x=row_idx, line_color='rgba(255,255,255,0.2)', line_width=1, line_dash='dot', row=3, col=1)

    # Настройка осей
    fig.update_xaxes(
        title_text="Timeline",
        row=3, col=1,
        gridcolor='#444',
        matches='x3'  # Связать с xaxis3 (ask prices chart) для синхронного зума
    )
    fig.update_yaxes(title_text="BTC Price ($)", row=3, col=1, gridcolor='#444')
