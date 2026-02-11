"""
Layout Module
Верстка и компоненты интерфейса Dash приложения
"""

from dash import html, dcc
from .widgets.right_panel import create_right_panel


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


def create_playback_controls():
    """Создать панель управления воспроизведением"""
    return html.Div([
        html.Div([
            html.Button(
                id='play-pause-btn',
                children='▶ Play',
                n_clicks=0,
                style={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 24px',
                    'fontSize': '16px',
                    'cursor': 'pointer',
                    'borderRadius': '4px',
                    'marginRight': '15px',
                    'minWidth': '100px'
                }
            ),
            html.Label("Speed: ", style={'color': 'white', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='speed-selector',
                options=[
                    {'label': 'x1 (Real-time)', 'value': 1},
                    {'label': 'x2', 'value': 2},
                    {'label': 'x4', 'value': 4},
                ],
                value=1,
                clearable=False,
                style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'}
            ),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'marginBottom': '10px'
        }),
        html.Div(id='playback-status', style={
            'color': '#888',
            'textAlign': 'center',
            'fontSize': '12px'
        })
    ], style={'padding': '10px 20px'})


def create_left_panel():
    """Создать левую панель с графиками"""
    return html.Div([
        # Статический Graph компонент - обновляется только figure
        dcc.Graph(id='main-chart', style={'height': '900px'}),
        create_playback_controls()
    ], style={'flex': '3', 'padding': '20px'})


def create_layout():
    """Создать полный layout приложения"""
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
            interval=100,  # 100ms = 10 FPS (optimized for smooth playback)
            n_intervals=0,
            disabled=True
        ),
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
