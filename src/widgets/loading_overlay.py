"""
Loading Overlay Widget
Full-page overlay with spinner during API calls
"""

from dash import html, dcc, callback, Output, Input


def create_loading_overlay():
    """Create full-page loading overlay component"""
    return html.Div(
        id='trader-loading-overlay',
        children=[
            html.Div(
                style={
                    'textAlign': 'center',
                    'padding': '50px'
                },
                children=[
                    dcc.Loading(
                        type='circle',
                        color='#4CAF50',
                        children=html.Div()
                    ),
                    html.P(
                        'Searching for trader trades...',
                        style={
                            'color': 'white',
                            'marginTop': '20px',
                            'fontSize': '16px'
                        }
                    )
                ]
            )
        ],
        style={
            'display': 'none',  # Hidden by default
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '100vw',
            'height': '100vh',
            'backgroundColor': 'rgba(0, 0, 0, 0.8)',
            'zIndex': 9999,
            'justifyContent': 'center',
            'alignItems': 'center'
        }
    )


@callback(
    Output('trader-loading-overlay', 'style'),
    Input('trader-loading-state', 'data')
)
def toggle_loading_overlay(loading_state):
    """Show/hide overlay based on loading state"""
    base_style = {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'width': '100vw',
        'height': '100vh',
        'backgroundColor': 'rgba(0, 0, 0, 0.8)',
        'zIndex': 9999,
        'justifyContent': 'center',
        'alignItems': 'center'
    }

    if loading_state and loading_state.get('is_loading'):
        base_style['display'] = 'flex'
    else:
        base_style['display'] = 'none'

    return base_style
