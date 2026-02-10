"""
Callbacks Module
Callback функции для интерактивности Dash приложения
"""

import time
import bisect
from dash import html, callback, Output, Input, State, ctx, no_update, Patch
from .data_loader import load_data, get_file_info, compute_cumulative_times
from .charts import create_orderbook_figure
from .buffer import get_trace_cache, set_cache_size


# Стили для кнопки Play/Pause
PLAY_BTN_STYLE = {
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

PAUSE_BTN_STYLE = {
    'backgroundColor': '#f44336',
    'color': 'white',
    'border': 'none',
    'padding': '10px 24px',
    'fontSize': '16px',
    'cursor': 'pointer',
    'borderRadius': '4px',
    'marginRight': '15px',
    'minWidth': '100px'
}

# Кеш для данных (используем TraceDataCache из buffer.py)
def get_cached_data(filename):
    """Получить DataFrame из кеша"""
    cache = get_trace_cache()
    return cache.get_df(filename)


def prebuffer_traces(filename, current_row, buffer_size=50):
    """Предзагрузить trace данные в буфер"""
    cache = get_trace_cache()
    return cache.prebuffer(filename, current_row, buffer_size)


def get_buffer_stats(filename, current_row):
    """Получить статистику буфера"""
    cache = get_trace_cache()
    stats = cache.get_stats(filename, current_row)
    return stats['ahead'], stats['cached_frames']


def register_callbacks(app):
    """
    Зарегистрировать все callback функции
    """

    # Callback 1: Инициализация при смене файла
    @callback(
        [
            Output('cumulative-times', 'data'),
            Output('time-slider', 'max'),
            Output('time-slider', 'marks'),
            Output('time-slider', 'value'),
            Output('file-info', 'children'),
            Output('main-chart', 'figure'),
            Output('buffer-status', 'children')
        ],
        [
            Input('file-selector', 'value'),
            Input('buffer-size-slider', 'value')
        ]
    )
    def init_on_file_change(filename, buffer_size):
        """Инициализировать все компоненты при смене файла"""
        if not filename:
            empty_fig = {'data': [], 'layout': {'paper_bgcolor': '#1e1e1e', 'plot_bgcolor': '#2d2d2d'}}
            return [], 0, {}, 0, "No file loaded", empty_fig, "No file"

        df = get_cached_data(filename)
        info = get_file_info(df, filename)
        cumulative_times = compute_cumulative_times(df)

        max_val = len(df) - 1
        step = max(1, max_val // 10)
        marks = {i: str(i) for i in range(0, max_val + 1, step)}

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

        # Устанавливаем размер кеша
        set_cache_size(buffer_size)

        # Создаем начальный график
        fig = create_orderbook_figure(df, 0)

        # Prebuffer начальных кадров (trace data, не полные figures)
        buffered = prebuffer_traces(filename, 0, buffer_size)
        buffer_status = f"Buffered: {buffered} trace frames"

        return cumulative_times, max_val, marks, 0, file_info, fig, buffer_status

    # Callback 2: Обработка Play/Pause кнопки
    @callback(
        [
            Output('playback-state', 'data'),
            Output('play-pause-btn', 'children'),
            Output('play-pause-btn', 'style'),
            Output('playback-interval', 'disabled'),
            Output('buffer-status', 'children', allow_duplicate=True)
        ],
        [
            Input('play-pause-btn', 'n_clicks'),
            Input('speed-selector', 'value')
        ],
        [
            State('playback-state', 'data'),
            State('time-slider', 'value'),
            State('time-slider', 'max'),
            State('file-selector', 'value'),
            State('buffer-size-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def handle_playback_controls(n_clicks, speed, state, slider_value, max_rows, filename, buffer_size):
        """Обработать нажатие Play/Pause и изменение скорости"""
        triggered_id = ctx.triggered_id
        buffer_status = no_update

        if triggered_id == 'play-pause-btn':
            new_is_playing = not state['is_playing']

            # При нажатии Play - prebuffer
            if new_is_playing and filename:
                buffered = prebuffer_traces(filename, slider_value, buffer_size)
                buffer_status = f"Buffered: {buffered} trace frames ahead"

        elif triggered_id == 'speed-selector':
            new_is_playing = state['is_playing']
        else:
            new_is_playing = state['is_playing']

        current_time_ms = int(time.time() * 1000)

        if new_is_playing:
            if slider_value >= max_rows:
                slider_value = 0

            new_state = {
                'is_playing': True,
                'play_start_time': current_time_ms,
                'play_start_row': slider_value,
                'speed': speed
            }
            return new_state, '⏸ Pause', PAUSE_BTN_STYLE, False, buffer_status
        else:
            new_state = {
                'is_playing': False,
                'play_start_time': None,
                'play_start_row': slider_value,
                'speed': speed
            }
            return new_state, '▶ Play', PLAY_BTN_STYLE, True, buffer_status

    # Callback 3: Обновление по таймеру
    @callback(
        [
            Output('time-slider', 'value', allow_duplicate=True),
            Output('playback-status', 'children'),
            Output('playback-state', 'data', allow_duplicate=True),
            Output('playback-interval', 'disabled', allow_duplicate=True),
            Output('play-pause-btn', 'children', allow_duplicate=True),
            Output('play-pause-btn', 'style', allow_duplicate=True),
            Output('buffer-status', 'children', allow_duplicate=True)
        ],
        Input('playback-interval', 'n_intervals'),
        [
            State('playback-state', 'data'),
            State('cumulative-times', 'data'),
            State('time-slider', 'max'),
            State('file-selector', 'value'),
            State('buffer-size-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_on_interval(n_intervals, state, cumulative_times, max_rows, filename, buffer_size):
        """Обновить позицию слайдера на основе прошедшего времени"""
        if not state['is_playing'] or not cumulative_times:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update

        current_time_ms = int(time.time() * 1000)
        elapsed_wall_time = current_time_ms - state['play_start_time']
        elapsed_data_time = elapsed_wall_time * state['speed']

        start_row = state['play_start_row']
        if start_row < len(cumulative_times):
            start_offset = cumulative_times[start_row]
        else:
            start_offset = 0

        target_time = start_offset + elapsed_data_time
        target_row = bisect.bisect_right(cumulative_times, target_time)
        target_row = max(0, min(target_row - 1, max_rows))

        # Prebuffer каждые 10 тиков (1 секунда при 100ms интервале)
        buffer_status = no_update
        if n_intervals % 10 == 0 and filename:
            prebuffer_traces(filename, target_row, buffer_size)
            ahead, total = get_buffer_stats(filename, target_row)
            buffer_status = f"Buffer: {ahead} ahead | Total: {total}"

        if target_row >= max_rows:
            new_state = {
                'is_playing': False,
                'play_start_time': None,
                'play_start_row': max_rows,
                'speed': state['speed']
            }
            status = f"Playback complete. Row {max_rows}/{max_rows}"
            return max_rows, status, new_state, True, '▶ Play', PLAY_BTN_STYLE, "Playback complete"

        total_duration = cumulative_times[-1] if cumulative_times else 0
        current_data_time = cumulative_times[target_row] if target_row < len(cumulative_times) else total_duration

        elapsed_sec = current_data_time / 1000
        total_sec = total_duration / 1000
        status = f"x{state['speed']} | {elapsed_sec:.1f}s / {total_sec:.1f}s | Row {target_row}/{max_rows}"

        return target_row, status, no_update, no_update, no_update, no_update, buffer_status

    # Callback 4: Обновление графика через Patch (частичное обновление)
    @callback(
        Output('main-chart', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        State('file-selector', 'value'),
        prevent_initial_call=True
    )
    def update_chart_on_slider(slider_value, filename):
        """
        Обновить график при изменении позиции слайдера.
        Использует Patch для частичного обновления (только данные traces),
        что уменьшает размер обновления с ~300KB до ~2KB.
        """
        if not filename:
            return no_update

        # Получаем trace данные из кеша
        cache = get_trace_cache()
        trace_data = cache.compute_trace_data(filename, slider_value)

        # Используем Patch для частичного обновления figure
        patched_fig = Patch()

        # Обновляем UP Bids (trace 0)
        patched_fig['data'][0]['y'] = trace_data['up_bids']['y']
        patched_fig['data'][0]['x'] = trace_data['up_bids']['x']
        patched_fig['data'][0]['text'] = trace_data['up_bids']['text']
        patched_fig['data'][0]['marker']['color'] = trace_data['up_bids']['colors']

        # Обновляем UP Asks (trace 1)
        patched_fig['data'][1]['y'] = trace_data['up_asks']['y']
        patched_fig['data'][1]['x'] = trace_data['up_asks']['x']
        patched_fig['data'][1]['text'] = trace_data['up_asks']['text']
        patched_fig['data'][1]['marker']['color'] = trace_data['up_asks']['colors']

        # Обновляем DOWN Bids (trace 2)
        patched_fig['data'][2]['y'] = trace_data['down_bids']['y']
        patched_fig['data'][2]['x'] = trace_data['down_bids']['x']
        patched_fig['data'][2]['text'] = trace_data['down_bids']['text']
        patched_fig['data'][2]['marker']['color'] = trace_data['down_bids']['colors']

        # Обновляем DOWN Asks (trace 3)
        patched_fig['data'][3]['y'] = trace_data['down_asks']['y']
        patched_fig['data'][3]['x'] = trace_data['down_asks']['x']
        patched_fig['data'][3]['text'] = trace_data['down_asks']['text']
        patched_fig['data'][3]['marker']['color'] = trace_data['down_asks']['colors']

        # Обновляем позицию маркера на ценовом графике (trace 7 - Current Binance)
        patched_fig['data'][7]['x'] = trace_data['binance_price_x']
        patched_fig['data'][7]['y'] = trace_data['binance_price_y']

        # Обновляем позицию маркера Oracle на ценовом графике (trace 8 - Current Oracle)
        patched_fig['data'][8]['x'] = trace_data['oracle_price_x']
        patched_fig['data'][8]['y'] = trace_data['oracle_price_y']

        # Формируем заголовок
        title_text = (
            f"Orderbook @ {trace_data['timestamp']}<br>" +
            f"<sub>UP: {trace_data['up_pressure']} pressure " +
            f"(Bids: ${trace_data['up_bid_total']:,.0f} vs Asks: ${trace_data['up_ask_total']:,.0f}) | " +
            f"DOWN: {trace_data['down_pressure']} pressure " +
            f"(Bids: ${trace_data['down_bid_total']:,.0f} vs Asks: ${trace_data['down_ask_total']:,.0f})</sub>"
        )
        patched_fig['layout']['title']['text'] = title_text

        return patched_fig
