import pandas as pd
import plotly.graph_objects as go
from ..config import BAR_SCALE_COEFF

def get_bar_colors(sizes, base_color, anomaly_color, threshold):
    """Определить цвета столбцов с учетом аномалий"""
    colors = []
    for s in sizes:
        if pd.notna(s) and s > threshold:
            colors.append(anomaly_color)
        else:
            colors.append(base_color)
    return colors

def add_orderbook_traces(fig, data, anomaly_threshold, global_max):
    """
    Добавляет графики стакана (UP и DOWN) в фигуру.
    """
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

    # Настройка осей для стаканов
    fig.update_xaxes(
        title_text="<- Bids | Asks ->", 
        row=1, col=1, 
        gridcolor='#444',
        range=[-global_max, global_max],
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.5)',
        zerolinewidth=2
    )
    fig.update_xaxes(
        title_text="<- Bids | Asks ->", 
        row=1, col=2, 
        gridcolor='#444',
        range=[-global_max, global_max],
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.5)',
        zerolinewidth=2
    )
    fig.update_yaxes(title_text="Price Level", row=1, col=1, gridcolor='#444')
    fig.update_yaxes(title_text="Price Level", row=1, col=2, gridcolor='#444')
