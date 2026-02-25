"""
Crosshair Info Widget
Компонент для отображения значений метрик в точке crosshair
"""

from dash import html, dcc, callback, Output, Input
import pandas as pd


def create_crosshair_info_widget():
    """Создать виджет отображения информации crosshair"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Crosshair Info", style={'color': 'white'}),
        html.Div(
            id='crosshair-info-display',
            style={
                'color': '#aaa',
                'fontSize': '12px',
                'maxHeight': '400px',
                'overflowY': 'auto',
                'paddingRight': '10px'
            }
        ),
        html.Button(
            'Clear Crosshair',
            id='clear-crosshair-btn',
            n_clicks=0,
            style={
                'marginTop': '10px',
                'backgroundColor': '#666',
                'color': 'white',
                'border': 'none',
                'padding': '8px 16px',
                'fontSize': '12px',
                'cursor': 'pointer',
                'borderRadius': '4px',
                'width': '100%'
            }
        )
    ])


# Callback для отображения значений
@callback(
    Output('crosshair-info-display', 'children'),
    Input('crosshair-values', 'data')
)
def display_crosshair_values(values):
    """Отобразить значения метрик в точке crosshair"""
    if not values:
        return html.P(
            "Click on any chart to see values",
            style={'color': '#666', 'fontStyle': 'italic'}
        )

    # Форматировать значения
    items = []

    # Заголовок с позицией и временем
    items.append(html.Div([
        html.Strong(f"Row: {values['row_idx']}", style={'color': '#FFD700', 'fontSize': '14px'}),
        html.Br(),
        html.Span(f"Time: {values.get('timestamp_et', 'N/A')}", style={'color': '#999', 'fontSize': '11px'}),
        html.Br(),
        html.Span(f"Time till end: {values.get('time_till_end', 'N/A')}", style={'color': '#999', 'fontSize': '11px'})
    ], style={'marginBottom': '12px', 'paddingBottom': '8px', 'borderBottom': '1px solid #444'}))

    # Microprice
    if values.get('pm_up_microprice') is not None or values.get('pm_down_microprice') is not None:
        items.append(html.Div([
            html.Strong("Microprice:", style={'color': '#4CAF50'}),
            html.Br(),
            html.Span(
                f"UP: {values['pm_up_microprice']:.4f}"
                if pd.notna(values.get('pm_up_microprice')) else "UP: N/A",
                style={'color': '#00C853'}
            ),
            html.Br(),
            html.Span(
                f"DOWN: {values['pm_down_microprice']:.4f}"
                if pd.notna(values.get('pm_down_microprice')) else "DOWN: N/A",
                style={'color': '#F44336'}
            )
        ], style={'marginBottom': '10px'}))

    # Spread
    if values.get('pm_up_spread') is not None or values.get('pm_down_spread') is not None:
        items.append(html.Div([
            html.Strong("Spread:", style={'color': '#2196F3'}),
            html.Br(),
            html.Span(
                f"UP: {values['pm_up_spread']:.4f}"
                if pd.notna(values.get('pm_up_spread')) else "UP: N/A"
            ),
            html.Br(),
            html.Span(
                f"DOWN: {values['pm_down_spread']:.4f}"
                if pd.notna(values.get('pm_down_spread')) else "DOWN: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Imbalance
    if values.get('pm_up_imbalance') is not None or values.get('pm_down_imbalance') is not None:
        items.append(html.Div([
            html.Strong("Imbalance:", style={'color': '#9C27B0'}),
            html.Br(),
            html.Span(
                f"UP: {values['pm_up_imbalance']:.2f}"
                if pd.notna(values.get('pm_up_imbalance')) else "UP: N/A"
            ),
            html.Br(),
            html.Span(
                f"DOWN: {values['pm_down_imbalance']:.2f}"
                if pd.notna(values.get('pm_down_imbalance')) else "DOWN: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # BTC Price
    if values.get('binance_btc_price') is not None or values.get('oracle_btc_price') is not None:
        items.append(html.Div([
            html.Strong("BTC Price:", style={'color': '#FF9800'}),
            html.Br(),
            html.Span(
                f"Binance: ${values['binance_btc_price']:,.2f}"
                if pd.notna(values.get('binance_btc_price')) else "Binance: N/A"
            ),
            html.Br(),
            html.Span(
                f"Oracle: ${values['oracle_btc_price']:,.2f}"
                if pd.notna(values.get('oracle_btc_price')) else "Oracle: N/A"
            ),
            html.Br(),
            html.Span(
                f"Lag: {values['lag']:.2f}s"
                if pd.notna(values.get('lag')) else "Lag: N/A",
                style={'color': '#FFC107'}
            )
        ], style={'marginBottom': '10px'}))

    # Returns/Momentum
    if values.get('binance_ret1s_x100') is not None or values.get('binance_ret5s_x100') is not None:
        items.append(html.Div([
            html.Strong("Returns:", style={'color': '#00BCD4'}),
            html.Br(),
            html.Span(
                f"1s: {values['binance_ret1s_x100']:.2f}"
                if pd.notna(values.get('binance_ret1s_x100')) else "1s: N/A"
            ),
            html.Br(),
            html.Span(
                f"5s: {values['binance_ret5s_x100']:.2f}"
                if pd.notna(values.get('binance_ret5s_x100')) else "5s: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Volume
    if values.get('binance_volume_1s') is not None or values.get('binance_volume_5s') is not None:
        items.append(html.Div([
            html.Strong("Volume:", style={'color': '#8BC34A'}),
            html.Br(),
            html.Span(
                f"1s: {values['binance_volume_1s']:,.0f}"
                if pd.notna(values.get('binance_volume_1s')) else "1s: N/A"
            ),
            html.Br(),
            html.Span(
                f"5s: {values['binance_volume_5s']:,.0f}"
                if pd.notna(values.get('binance_volume_5s')) else "5s: N/A"
            ),
            html.Br(),
            html.Span(
                f"MA 30s: {values['binance_volma_30s']:,.0f}"
                if pd.notna(values.get('binance_volma_30s')) else "MA 30s: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Volatility
    if values.get('binance_atr_5s') is not None or values.get('binance_atr_30s') is not None:
        items.append(html.Div([
            html.Strong("Volatility:", style={'color': '#E91E63'}),
            html.Br(),
            html.Span(
                f"ATR 5s: ${values['binance_atr_5s']:.2f}"
                if pd.notna(values.get('binance_atr_5s')) else "ATR 5s: N/A"
            ),
            html.Br(),
            html.Span(
                f"ATR 30s: ${values['binance_atr_30s']:.2f}"
                if pd.notna(values.get('binance_atr_30s')) else "ATR 30s: N/A"
            ),
            html.Br(),
            html.Span(
                f"RVol 30s: {values['binance_rvol_30s']:.2f}%"
                if pd.notna(values.get('binance_rvol_30s')) else "RVol 30s: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Volume Spike
    if values.get('binance_volume_spike') is not None:
        items.append(html.Div([
            html.Strong("Volume Spike:", style={'color': '#FF5722'}),
            html.Br(),
            html.Span(
                f"Z-Score: {values['binance_volume_spike']:.2f}"
                if pd.notna(values.get('binance_volume_spike')) else "N/A"
            )
        ], style={'marginBottom': '10px'}))

    # P/VWAP
    if values.get('binance_p_vwap_5s') is not None or values.get('binance_p_vwap_30s') is not None:
        items.append(html.Div([
            html.Strong("P/VWAP:", style={'color': '#607D8B'}),
            html.Br(),
            html.Span(
                f"5s: {values['binance_p_vwap_5s']:.2f}%"
                if pd.notna(values.get('binance_p_vwap_5s')) else "5s: N/A"
            ),
            html.Br(),
            html.Span(
                f"30s: {values['binance_p_vwap_30s']:.2f}%"
                if pd.notna(values.get('binance_p_vwap_30s')) else "30s: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Depth
    if values.get('pm_up_bid_depth5') is not None:
        items.append(html.Div([
            html.Strong("Depth (Top 5):", style={'color': '#3F51B5'}),
            html.Br(),
            html.Span("UP:", style={'textDecoration': 'underline'}),
            html.Br(),
            html.Span(
                f"  Bid: ${values['pm_up_bid_depth5']:,.0f}"
                if pd.notna(values.get('pm_up_bid_depth5')) else "  Bid: N/A",
                style={'color': '#00C853'}
            ),
            html.Br(),
            html.Span(
                f"  Ask: ${values['pm_up_ask_depth5']:,.0f}"
                if pd.notna(values.get('pm_up_ask_depth5')) else "  Ask: N/A",
                style={'color': '#F44336'}
            ),
            html.Br(),
            html.Span("DOWN:", style={'textDecoration': 'underline'}),
            html.Br(),
            html.Span(
                f"  Bid: ${values['pm_down_bid_depth5']:,.0f}"
                if pd.notna(values.get('pm_down_bid_depth5')) else "  Bid: N/A",
                style={'color': '#00C853'}
            ),
            html.Br(),
            html.Span(
                f"  Ask: ${values['pm_down_ask_depth5']:,.0f}"
                if pd.notna(values.get('pm_down_ask_depth5')) else "  Ask: N/A",
                style={'color': '#F44336'}
            )
        ], style={'marginBottom': '10px'}))

    # EatFlow
    if values.get('pm_up_bid_eatflow') is not None:
        items.append(html.Div([
            html.Strong("EatFlow:", style={'color': '#009688'}),
            html.Br(),
            html.Span("UP:", style={'textDecoration': 'underline'}),
            html.Br(),
            html.Span(
                f"  Bid: {values['pm_up_bid_eatflow']:.2f}"
                if pd.notna(values.get('pm_up_bid_eatflow')) else "  Bid: N/A"
            ),
            html.Br(),
            html.Span(
                f"  Ask: {values['pm_up_ask_eatflow']:.2f}"
                if pd.notna(values.get('pm_up_ask_eatflow')) else "  Ask: N/A"
            ),
            html.Br(),
            html.Span("DOWN:", style={'textDecoration': 'underline'}),
            html.Br(),
            html.Span(
                f"  Bid: {values['pm_down_bid_eatflow']:.2f}"
                if pd.notna(values.get('pm_down_bid_eatflow')) else "  Bid: N/A"
            ),
            html.Br(),
            html.Span(
                f"  Ask: {values['pm_down_ask_eatflow']:.2f}"
                if pd.notna(values.get('pm_down_ask_eatflow')) else "  Ask: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Slope
    if values.get('pm_up_bid_slope') is not None:
        items.append(html.Div([
            html.Strong("Slope:", style={'color': '#795548'}),
            html.Br(),
            html.Span("UP:", style={'textDecoration': 'underline'}),
            html.Br(),
            html.Span(
                f"  Bid: {values['pm_up_bid_slope']:.4f}"
                if pd.notna(values.get('pm_up_bid_slope')) else "  Bid: N/A"
            ),
            html.Br(),
            html.Span(
                f"  Ask: {values['pm_up_ask_slope']:.4f}"
                if pd.notna(values.get('pm_up_ask_slope')) else "  Ask: N/A"
            ),
            html.Br(),
            html.Span("DOWN:", style={'textDecoration': 'underline'}),
            html.Br(),
            html.Span(
                f"  Bid: {values['pm_down_bid_slope']:.4f}"
                if pd.notna(values.get('pm_down_bid_slope')) else "  Bid: N/A"
            ),
            html.Br(),
            html.Span(
                f"  Ask: {values['pm_down_ask_slope']:.4f}"
                if pd.notna(values.get('pm_down_ask_slope')) else "  Ask: N/A"
            )
        ], style={'marginBottom': '10px'}))

    # Latency Direction
    if values.get('lat_dir_raw_x1000') is not None or values.get('lat_dir_norm_x1000') is not None:
        items.append(html.Div([
            html.Strong("Latency Direction:", style={'color': '#CDDC39'}),
            html.Br(),
            html.Span(
                f"Raw: {values['lat_dir_raw_x1000']:.0f}"
                if pd.notna(values.get('lat_dir_raw_x1000')) else "Raw: N/A"
            ),
            html.Br(),
            html.Span(
                f"Normalized: {values['lat_dir_norm_x1000']:.0f}"
                if pd.notna(values.get('lat_dir_norm_x1000')) else "Normalized: N/A"
            )
        ], style={'marginBottom': '10px'}))

    return html.Div(items)


# Callback для очистки crosshair
@callback(
    Output('crosshair-x-position', 'data', allow_duplicate=True),
    Input('clear-crosshair-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_crosshair(n_clicks):
    """Очистить crosshair"""
    if n_clicks > 0:
        return None
    return None
