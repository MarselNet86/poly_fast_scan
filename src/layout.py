"""
Layout Module
Верстка и компоненты интерфейса Dash приложения
"""

from dash import html, dcc
from .data_loader import get_csv_files


def create_header():
    """Создать шапку приложения"""
    return html.Div([
        html.H1("Orderbook Visualization", style={'margin': '0', 'color': 'white'}),
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


def create_time_slider():
    """Создать слайдер для навигации по времени"""
    return html.Div(
        id='slider-container',
        children=[
            html.Label("Navigate through time:", style={'color': 'white', 'marginBottom': '10px'}),
            dcc.Slider(
                id='time-slider',
                min=0,
                max=100,
                step=1,
                value=0,
                marks={},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ],
        style={'padding': '20px'}
    )


def create_file_selector():
    """Создать селектор файлов"""
    files = get_csv_files()
    return html.Div([
        html.H3("Select File", style={'color': 'white', 'marginTop': '0'}),
        dcc.Dropdown(
            id='file-selector',
            options=[{'label': f, 'value': f} for f in files],
            value=files[0] if files else None,
            style={'marginBottom': '20px'}
        )
    ])


def create_file_info_panel():
    """Создать панель информации о файле"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("File Info", style={'color': 'white'}),
        html.Div(id='file-info', style={'color': '#aaa'})
    ])


def create_legend():
    """Создать легенду"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Legend", style={'color': 'white'}),
        html.Div([
            # Orderbook
            html.P("Orderbook:", style={'color': '#888', 'margin': '5px 0', 'fontSize': '12px'}),
            html.Div([
                html.Span("", style={'color': 'rgba(0, 200, 83, 0.7)', 'fontSize': '20px', 'marginRight': '10px'}),
                html.Span("Bids (Buy Orders)", style={'color': 'white'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("", style={'color': 'rgba(244, 67, 54, 0.7)', 'fontSize': '20px', 'marginRight': '10px'}),
                html.Span("Asks (Sell Orders)", style={'color': 'white'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("", style={'color': 'rgba(0, 255, 100, 1)', 'fontSize': '20px', 'marginRight': '10px'}),
                html.Span("Anomaly (>2x avg)", style={'color': 'white'})
            ], style={'marginBottom': '15px'}),
            # Price Chart
            html.P("Price Chart:", style={'color': '#888', 'margin': '5px 0', 'fontSize': '12px'}),
            html.Div([
                html.Span("━", style={'color': '#FF6B00', 'fontSize': '16px', 'marginRight': '10px'}),
                html.Span("Binance BTC", style={'color': 'white'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("━", style={'color': '#2196F3', 'fontSize': '16px', 'marginRight': '10px'}),
                html.Span("Oracle BTC", style={'color': 'white'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("┄", style={'color': '#888', 'fontSize': '16px', 'marginRight': '10px'}),
                html.Span("VWAP 30s", style={'color': 'white'})
            ], style={'marginBottom': '15px'}),
            # Lag
            html.P("Lag Indicator:", style={'color': '#888', 'margin': '5px 0', 'fontSize': '12px'}),
            html.Div([
                html.Span("", style={'color': '#4CAF50', 'fontSize': '20px', 'marginRight': '10px'}),
                html.Span("Oracle > Binance", style={'color': 'white'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("", style={'color': '#F44336', 'fontSize': '20px', 'marginRight': '10px'}),
                html.Span("Binance > Oracle", style={'color': 'white'})
            ], style={'marginBottom': '10px'}),
        ])
    ])


def create_trading_context():
    """Создать панель с торговым контекстом"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Trading Context", style={'color': 'white'}),
        html.Div([
            html.P("Thick bids, thin asks -> Buyer pressure", style={'color': '#4caf50', 'margin': '5px 0'}),
            html.P("Thin bids, thick asks -> Seller pressure", style={'color': '#f44336', 'margin': '5px 0'}),
            html.P("Large order on one level -> Support/Resistance wall", style={'color': '#ff9800', 'margin': '5px 0'}),
            html.P("Contract prices range: 0-1", style={'color': '#888', 'margin': '5px 0'}),
            html.P("1 contract = $1 on win", style={'color': '#888', 'margin': '5px 0'}),
        ], style={'fontSize': '13px'})
    ])


def create_buffer_settings():
    """Создать панель настроек буфера"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Buffer Settings", style={'color': 'white'}),
        html.Div([
            html.Label("Buffer size (frames ahead):", style={'color': '#aaa', 'fontSize': '12px'}),
            dcc.Slider(
                id='buffer-size-slider',
                min=10,
                max=200,
                step=10,
                value=50,
                marks={10: '10', 50: '50', 100: '100', 150: '150', 200: '200'},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.Div(id='buffer-status', style={
                'color': '#888',
                'fontSize': '11px',
                'marginTop': '10px'
            })
        ])
    ])


def create_left_panel():
    """Создать левую панель с графиками"""
    return html.Div([
        # Статический Graph компонент - обновляется только figure
        dcc.Graph(id='main-chart', style={'height': '750px'}),
        create_playback_controls(),
        create_time_slider()
    ], style={'flex': '3', 'padding': '20px'})


def create_right_panel():
    """Создать правую панель с настройками"""
    return html.Div([
        create_file_selector(),
        create_file_info_panel(),
        create_buffer_settings(),
        create_legend(),
        create_trading_context()
    ], style={
        'flex': '1',
        'padding': '20px',
        'backgroundColor': '#252525',
        'borderLeft': '1px solid #444',
        'minWidth': '280px'
    })


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
