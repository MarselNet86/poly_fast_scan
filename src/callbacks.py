"""
Callbacks Module
Callback функции для интерактивности Dash приложения
"""

from dash import html, dcc, callback, Output, Input
from .data_loader import load_data, get_file_info
from .charts import create_orderbook_figure


def register_callbacks(app):
    """
    Зарегистрировать все callback функции

    Args:
        app: Dash приложение
    """

    @callback(
        [
            Output('chart-container', 'children'),
            Output('slider-container', 'style'),
            Output('time-slider', 'max'),
            Output('time-slider', 'marks'),
            Output('file-info', 'children')
        ],
        [
            Input('file-selector', 'value'),
            Input('time-slider', 'value')
        ]
    )
    def update_chart(filename, slider_value):
        """Обновить график при изменении файла или позиции слайдера"""

        if not filename:
            return (
                html.Div(
                    "No file selected",
                    style={'color': 'white', 'padding': '50px', 'textAlign': 'center'}
                ),
                {'display': 'none'},
                0,
                {},
                "No file loaded"
            )

        try:
            df = load_data(filename)
            info = get_file_info(df, filename)

            # Информация о файле
            file_info = html.Div([
                html.P(f"File: {info['filename']}", style={'margin': '5px 0'}),
                html.P(f"Rows: {info['rows']:,}", style={'margin': '5px 0'}),
                html.P(f"Columns: {info['columns']}", style={'margin': '5px 0'}),
                html.P("Time range:", style={'margin': '5px 0'}),
                html.P(
                    f"   Start: {info['time_start']}",
                    style={'margin': '2px 0 2px 10px', 'fontSize': '12px'}
                ),
                html.P(
                    f"   End: {info['time_end']}",
                    style={'margin': '2px 0 2px 10px', 'fontSize': '12px'}
                ),
            ])

            fig = create_orderbook_figure(df, slider_value)
            chart = dcc.Graph(figure=fig, style={'height': '750px'})

            # Создаем метки для слайдера
            max_val = len(df) - 1
            step = max(1, max_val // 10)
            marks = {i: str(i) for i in range(0, max_val + 1, step)}

            slider_style = {'padding': '20px'}
            return chart, slider_style, max_val, marks, file_info

        except Exception as e:
            error_msg = html.Div([
                html.H3("Error loading file", style={'color': '#f44336'}),
                html.P(str(e), style={'color': '#888'})
            ], style={'padding': '50px', 'textAlign': 'center'})
            return error_msg, {'display': 'none'}, 0, {}, f"Error: {str(e)}"
