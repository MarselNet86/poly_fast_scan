"""
Right Panel Widget
Правая панель с настройками и элементами управления
"""

from dash import html, dcc
from ..data_loader import get_csv_files
from .active_track import create_active_track_widget


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
