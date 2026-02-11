"""
Active-Track Widget Component
Чекбокс для включения режима слежения за ценовым маркером
с регулировкой масштаба (размер окна обзора)
"""

from dash import html, dcc

def create_active_track_widget():
    """Создать виджет Active-Track с управлением масштабом"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Active-Track", style={'color': 'white'}),

        # Чекбокс включения
        dcc.Checklist(
            id='active-track-checklist',
            options=[
                {'label': ' Enable (Follow Price)', 'value': 'enabled'}
            ],
            value=[],  # По умолчанию выключено
            style={'color': '#aaa', 'fontSize': '14px', 'marginBottom': '10px'}
        ),

        # Слайдер масштаба (размер окна)
        html.Div([
            html.Label(
                "Zoom Level (window size):",
                style={'color': '#aaa', 'fontSize': '12px', 'marginBottom': '5px'}
            ),
            dcc.Slider(
                id='active-track-zoom-slider',
                min=50,
                max=5000,
                step=50,
                value=150,  # По умолчанию 150 (300 строк всего: ±150)
                marks={
                    50: '50',
                    500: '500',
                    1000: '1k',
                    2500: '2.5k',
                    5000: '5k'
                },
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.P(
                id='active-track-zoom-info',
                children="Window: ±150 rows (300 total)",
                style={'color': '#666', 'fontSize': '11px', 'marginTop': '5px'}
            )
        ], style={'marginTop': '10px'}),

        html.P(
            "Auto-scroll charts to follow current position",
            style={'color': '#666', 'fontSize': '11px', 'marginTop': '10px'}
        )
    ], style={'paddingBottom': '10px'})
