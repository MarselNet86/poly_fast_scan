"""
Layout Module
Верстка и компоненты интерфейса Dash приложения
"""

from dash import html, dcc
from .widgets.right_panel import create_right_panel
from .widgets.market_header import create_market_header


def create_header():
    """Создать шапку приложения с информационной панелью статуса рынка"""
    return html.Div([
        # Название приложения
        html.Div([
            html.H1("xDaimon FastScan", style={'margin': '0', 'color': 'white'}),
            html.P("Polymarket UP/DOWN Contract Orderbook Analysis", style={'color': '#888', 'margin': '5px 0 0 0'})
        ], style={
            'padding': '20px',
            'backgroundColor': '#1e1e1e',
            'borderBottom': '1px solid #444'
        }),
        # Market Header - информационная панель
        create_market_header()
    ])


def create_left_panel():
    """Создать левую панель с тремя независимыми графиками"""
    return html.Div([
        # Orderbook chart (UP/DOWN orderbook + Ask prices)
        dcc.Graph(id='chart-orderbook', style={'height': '550px'}),

        # BTC chart (BTC Price + Lag)
        dcc.Graph(id='chart-btc', style={'height': '450px'}),

        # Returns chart (Momentum / Returns)
        dcc.Graph(id='chart-returns', style={'height': '350px'}),
    ], style={'flex': '3', 'padding': '20px'})


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

        # НОВЫЕ STORES для clientside playback
        dcc.Store(id='playback-chunk-request', data=None),  # JS → Server
        dcc.Store(id='playback-chunk-data', data=None),     # Server → JS

        # Dummy divs для clientside callbacks
        html.Div(id='_chunk-receiver-dummy', style={'display': 'none'}),
        html.Div(id='_playback-engine-dummy', style={'display': 'none'}),
        html.Div(id='_playback-init-dummy', style={'display': 'none'}),
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


