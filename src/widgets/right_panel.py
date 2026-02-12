"""
Right Panel Widget
Правая панель с настройками и элементами управления
"""

from dash import html, dcc
from ..data_loader import get_csv_files
from .active_track import create_active_track_widget


def create_playback_controls():
    """Создать панель управления воспроизведением"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Playback", style={'color': 'white'}),
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
                style={'width': '120px', 'display': 'inline-block', 'verticalAlign': 'middle'}
            ),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'marginBottom': '10px'
        }),
        html.Div(id='playback-status', style={
            'color': 'white',
            'fontSize': '12px'
        })
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
        html.H3("Performance", style={'color': 'white'}),

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
            html.Label("Buffer size (frames ahead):", style={'color': 'white', 'fontSize': '12px'}),
            dcc.Slider(
                id='buffer-size-slider',
                min=10,
                max=200,
                step=10,
                value=50,
                marks={
                    10: {'label': '10', 'style': {'color': 'white'}},
                    50: {'label': '50', 'style': {'color': 'white'}},
                    100: {'label': '100', 'style': {'color': 'white'}},
                    150: {'label': '150', 'style': {'color': 'white'}},
                    200: {'label': '200', 'style': {'color': 'white'}}
                },
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.Div(id='buffer-status', style={
                'color': 'white',
                'fontSize': '11px',
                'marginTop': '10px'
            })
        ])
    ])


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


def create_right_panel():
    """Создать правую панель с настройками"""
    return html.Div([
        create_file_selector(),
        create_file_info_panel(),
        create_playback_controls(),
        create_time_slider(),
        create_performance_settings(),
        create_active_track_widget(),
    ], style={
        'flex': '1',
        'padding': '20px',
        'backgroundColor': '#252525',
        'borderLeft': '1px solid #444',
        'minWidth': '280px'
    })
