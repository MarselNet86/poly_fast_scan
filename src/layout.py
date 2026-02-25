"""
Layout Module
Верстка и компоненты интерфейса Dash приложения
"""

from dash import html, dcc
from .widgets.right_panel import create_right_panel
from .widgets.loading_overlay import create_loading_overlay


def create_header():
    """Создать шапку приложения"""
    return html.Div([
        html.H1("xDaimon FastScan", style={'margin': '0', 'color': 'white'}),
        html.P("Polymarket UP/DOWN Contract Orderbook Analysis", style={'color': '#888', 'margin': '5px 0 0 0'})
    ], style={
        'padding': '20px',
        'backgroundColor': '#1e1e1e',
        'borderBottom': '1px solid #444'
    })


def create_left_panel():
    """Создать левую панель с пятью независимыми графиками"""
    return html.Div([
        # Orderbook chart (UP/DOWN orderbook + Ask prices)
        dcc.Graph(id='chart-orderbook', style={'height': '700px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Microprice chart
        dcc.Graph(id='chart-microprice', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Arbitrage Indicator chart
        dcc.Graph(id='chart-arbitrage-indicator', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Spread chart
        dcc.Graph(id='chart-spread', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Imbalance chart
        dcc.Graph(id='chart-imbalance', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Slope chart
        dcc.Graph(id='chart-slope', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # EatFlow chart
        dcc.Graph(id='chart-eatflow', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Depth chart
        dcc.Graph(id='chart-depth', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # BTC chart (BTC Price + Lag)
        dcc.Graph(id='chart-btc', style={'height': '700px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Latency Direction chart (oracle lag indicator)
        dcc.Graph(id='chart-latency-direction', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Returns chart (Momentum / Returns)
        dcc.Graph(id='chart-returns', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Volume chart (V1s, V5s, VolMA)
        dcc.Graph(id='chart-volume', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Volatility chart (ATR, RVol)
        dcc.Graph(id='chart-volatility', style={'height': '700px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # Volume Spike chart
        dcc.Graph(id='chart-volume-spike', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),

        # P/VWAP chart (% отклонение от VWAP)
        dcc.Graph(id='chart-p-vwap', style={'height': '450px', 'width': '100%'}, config={'doubleClick': 'reset', 'responsive': True}),
    ], style={'flex': '3', 'padding': '15px'})


def create_main_layout():
    """Создать полный layout главного окна"""
    return html.Div([
        # Скрытые компоненты для playback
        dcc.Store(id='playback-state', data={
            'is_playing': False,
            'play_start_time': None,
            'play_start_row': 0,
            'speed': 1
        }),
        dcc.Store(id='cumulative-times', data=[]),

        # Stores для trader data
        dcc.Store(id='trader-data', data=None),
        dcc.Store(id='trader-loading-state', data={'is_loading': False}),

        # НОВЫЕ STORES для clientside playback
        dcc.Store(id='playback-chunk-request', data=None),  # JS → Server
        dcc.Store(id='playback-chunk-data', data=None),     # Server → JS

        # Store для crosshair
        dcc.Store(id='crosshair-x-position', data=None),
        dcc.Store(id='crosshair-values', data=None),

        # Dummy divs для clientside callbacks
        html.Div(id='_chunk-receiver-dummy', style={'display': 'none'}),
        html.Div(id='_playback-engine-dummy', style={'display': 'none'}),
        html.Div(id='_playback-init-dummy', style={'display': 'none'}),

        # Loading overlay for trader data
        create_loading_overlay(),

        # Основной layout
        create_header(),
        html.Div([
            create_left_panel(),
            create_right_panel()
        ], style={'display': 'flex', 'minHeight': 'calc(100vh - 100px)'})
    ], style={
        'backgroundColor': '#1e1e1e',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif'
    })


