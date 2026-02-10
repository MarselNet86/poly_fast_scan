"""
Active-Track Widget Component
Чекбокс для включения режима слежения за ценовым маркером
"""

from dash import html, dcc

def create_active_track_widget():
    """Создать виджет Active-Track"""
    return html.Div([
        html.Hr(style={'borderColor': '#444'}),
        html.H3("Chart Behavior", style={'color': 'white'}),
        dcc.Checklist(
            id='active-track-checklist',
            options=[
                {'label': ' Active-Track (Follow Price)', 'value': 'enabled'}
            ],
            value=[],  # По умолчанию выключено
            style={'color': '#aaa', 'fontSize': '14px'}
        ),
        html.P(
            "Auto-scroll price chart to follow current time",
            style={'color': '#666', 'fontSize': '11px', 'marginTop': '5px'}
        )
    ], style={'paddingBottom': '10px'})
