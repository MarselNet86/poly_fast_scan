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
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Navigate Time", style={'color': 'white'}),
        dcc.Slider(
            id='time-slider',
            min=0,
            max=100,
            step=1,
            value=0,
            marks={},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ])


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


def create_performance_settings():
    """Создать панель настроек производительности"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Performance Settings", style={'color': 'white'}),

        # FPS Settings
        html.Div([
            html.Label("UI Update Rate (FPS):", style={'color': '#aaa', 'fontSize': '12px', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='fps-selector',
                options=[
                    {'label': '5 FPS (Low CPU)', 'value': 200},
                    {'label': '10 FPS (Balanced)', 'value': 100},
                    {'label': '15 FPS (Smooth)', 'value': 67},
                    {'label': '20 FPS (High)', 'value': 50},
                    {'label': '30 FPS (Ultra)', 'value': 33},
                ],
                value=100,  # 10 FPS по умолчанию
                clearable=False,
                style={'marginBottom': '15px'}
            ),
        ]),

        # Buffer Settings
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
        dcc.Graph(id='main-chart', style={'height': '900px'}),
        create_playback_controls()
    ], style={'flex': '3', 'padding': '20px'})


from .widgets.active_track import create_active_track_widget

def create_right_panel():
    """Создать правую панель с настройками"""
    return html.Div([
        create_file_selector(),
        create_file_info_panel(),
        create_performance_settings(),
        create_time_slider(),
        create_active_track_widget(),   
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
