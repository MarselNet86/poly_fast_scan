"""
Layout Module
Верстка и компоненты интерфейса Dash приложения
Поддержка multi-window режима через view_mode параметр
"""

from dash import html, dcc
from .widgets.right_panel import create_right_panel


# Стили для кнопок pop-out
POPOUT_BTN_STYLE = {
    'backgroundColor': '#333',
    'color': 'white',
    'border': '1px solid #555',
    'padding': '8px 16px',
    'fontSize': '14px',
    'cursor': 'pointer',
    'borderRadius': '4px',
    'transition': 'background-color 0.2s'
}


def create_header(view_mode='main'):
    """Создать шапку приложения"""
    title_section = html.Div([
        html.H1("xDaimon FastScan", style={'margin': '0', 'color': 'white'}),
        html.P("Polymarket UP/DOWN Contract Orderbook Analysis", style={'color': '#888', 'margin': '5px 0 0 0'})
    ])

    # Кнопки pop-out только для main view
    if view_mode == 'main':
        popout_buttons = html.Div([
            html.Button(
                "↗ Orderbook",
                id='popout-orderbook-btn',
                n_clicks=0,
                style=POPOUT_BTN_STYLE
            ),
            html.Button(
                "↗ BTC",
                id='popout-btc-btn',
                n_clicks=0,
                style=POPOUT_BTN_STYLE
            ),
        ], style={'display': 'flex', 'gap': '10px'})
    else:
        # Для pop-out окон показываем название view
        view_names = {'orderbook': 'Orderbook View', 'btc': 'BTC & Lag View'}
        popout_buttons = html.Div([
            html.Span(
                view_names.get(view_mode, ''),
                style={'color': '#9c27b0', 'fontSize': '14px', 'fontWeight': 'bold'}
            )
        ])

    return html.Div([
        title_section,
        popout_buttons
    ], style={
        'padding': '20px',
        'backgroundColor': '#1e1e1e',
        'borderBottom': '1px solid #444',
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center'
    })


def create_left_panel():
    """Создать левую панель с двумя независимыми графиками (main view)"""

    # Стиль для placeholder "Opened in a new tab"
    placeholder_style_hidden = {
        'display': 'none',
        'backgroundColor': '#2d2d2d',
        'border': '2px dashed #555',
        'borderRadius': '8px',
        'padding': '40px',
        'textAlign': 'center',
        'color': '#888',
        'fontSize': '18px',
        'margin': '10px 0'
    }

    return html.Div([
        # Orderbook chart (UP/DOWN orderbook + Ask prices)
        html.Div([
            dcc.Graph(id='chart-orderbook', style={'height': '550px'}),
        ], id='chart-orderbook-container'),
        html.Div(
            "📊 Orderbook — opened in a new tab",
            id='placeholder-orderbook',
            style=placeholder_style_hidden
        ),

        # BTC chart (BTC Price + Lag)
        html.Div([
            dcc.Graph(id='chart-btc', style={'height': '450px'}),
        ], id='chart-btc-container'),
        html.Div(
            "📈 BTC & Lag — opened in a new tab",
            id='placeholder-btc',
            style=placeholder_style_hidden
        ),
    ], style={'flex': '3', 'padding': '20px'})


def create_shared_stores():
    """Создать localStorage stores для синхронизации между вкладками"""
    return [
        # Shared stores (localStorage) для cross-tab sync
        dcc.Store(id='shared-slider-value', storage_type='local'),
        dcc.Store(id='shared-file-selection', storage_type='local'),
        dcc.Store(id='shared-playback-state', storage_type='local'),
        dcc.Store(id='shared-popout-status', storage_type='local', data={}),
    ]


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
        dcc.Interval(
            id='playback-interval',
            interval=100,  # 100ms = 10 FPS
            n_intervals=0,
            disabled=True
        ),
        # Shared stores для cross-tab sync
        *create_shared_stores(),
        # Dummy divs для clientside callback outputs (pop-out buttons)
        html.Div(id='_popout-ob-dummy', style={'display': 'none'}),
        html.Div(id='_popout-btc-dummy', style={'display': 'none'}),
        # Основной layout
        create_header(view_mode='main'),
        html.Div([
            create_left_panel(),
            create_right_panel()
        ], style={'display': 'flex', 'minHeight': 'calc(100vh - 100px)'})
    ], style={
        'backgroundColor': '#1e1e1e',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif'
    })


def create_orderbook_popout():
    """Создать layout для pop-out окна Orderbook"""
    return html.Div([
        # Shared stores для чтения состояния
        *create_shared_stores(),
        # Interval для синхронизации
        dcc.Interval(
            id='popout-sync-interval',
            interval=100,  # 100ms sync rate
            n_intervals=0
        ),
        # Store для локального состояния
        dcc.Store(id='popout-last-value', data={'value': 0}),
        # Header
        create_header(view_mode='orderbook'),
        # График
        html.Div([
            dcc.Graph(id='popout-chart', style={'height': 'calc(100vh - 80px)'}),
        ], style={'padding': '10px'})
    ], style={
        'backgroundColor': '#1e1e1e',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif'
    })


def create_btc_popout():
    """Создать layout для pop-out окна BTC"""
    return html.Div([
        # Shared stores для чтения состояния
        *create_shared_stores(),
        # Interval для синхронизации
        dcc.Interval(
            id='popout-sync-interval',
            interval=100,  # 100ms sync rate
            n_intervals=0
        ),
        # Store для локального состояния
        dcc.Store(id='popout-last-value', data={'value': 0}),
        # Header
        create_header(view_mode='btc'),
        # График
        html.Div([
            dcc.Graph(id='popout-chart', style={'height': 'calc(100vh - 80px)'}),
        ], style={'padding': '10px'})
    ], style={
        'backgroundColor': '#1e1e1e',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif'
    })


def create_root_layout():
    """Создать корневой layout с роутингом"""
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='content-container')
    ])
