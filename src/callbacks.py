"""
Callbacks Module
Callback функции для интерактивности Dash приложения
"""

import time
from dash import html, callback, Output, Input, State, ctx, no_update, Patch
from .data_loader import load_data, get_file_info, compute_cumulative_times
from .charts import create_orderbook_chart, create_btc_chart, create_orderbook_popout_figure, create_btc_popout_figure
from .data_cache import get_data_cache


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

def register_callbacks(app):
    """
    Зарегистрировать все callback функции
    """

    # ========================================
    # Callback 1: Инициализация при смене файла
    # ========================================
    @callback(
        [
            Output('cumulative-times', 'data'),
            Output('time-slider', 'max'),
            Output('time-slider', 'marks'),
            Output('time-slider', 'value'),
            Output('file-info', 'children'),
            Output('chart-orderbook', 'figure'),
            Output('chart-btc', 'figure')
        ],
        Input('file-selector', 'value')
    )
    def init_on_file_change(filename):
        """Инициализировать все компоненты при смене файла"""
        if not filename:
            empty_fig = {'data': [], 'layout': {'paper_bgcolor': '#1e1e1e', 'plot_bgcolor': '#2d2d2d'}}
            return [], 0, {}, 0, "No file loaded", empty_fig, empty_fig

        cache = get_data_cache()
        df = cache.get_df(filename)
        info = get_file_info(df, filename)
        cumulative_times = compute_cumulative_times(df)

        max_val = len(df) - 1
        # Создаем только 5 меток для лучшей читаемости
        step = max(1, max_val // 4)
        marks = {
            i: {'label': str(i), 'style': {'color': 'white'}}
            for i in range(0, max_val + 1, step)
        }

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

        # Создаем начальные графики (два независимых)
        ob_fig = create_orderbook_chart(df, 0)
        btc_fig = create_btc_chart(df, 0)

        return cumulative_times, max_val, marks, 0, file_info, ob_fig, btc_fig

    # ========================================
    # Callback 2: Обработка Play/Pause кнопки
    # ========================================
    @callback(
        [
            Output('playback-state', 'data'),
            Output('play-pause-btn', 'children'),
            Output('play-pause-btn', 'style'),
            Output('_playback-trigger-dummy', 'children')  # ИЗМЕНЕНО: триггер для clientside
        ],
        [
            Input('play-pause-btn', 'n_clicks'),
            Input('speed-selector', 'value')
        ],
        [
            State('playback-state', 'data'),
            State('time-slider', 'value'),
            State('time-slider', 'max')
        ],
        prevent_initial_call=True
    )
    def handle_playback_controls(n_clicks, speed, state, slider_value, max_rows):
        """Обработать Play/Pause - триггерит clientside playback вместо interval"""
        triggered_id = ctx.triggered_id

        if triggered_id == 'play-pause-btn':
            new_is_playing = not state['is_playing']
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
            return new_state, '⏸ Pause', PAUSE_BTN_STYLE, ''
        else:
            new_state = {
                'is_playing': False,
                'play_start_time': None,
                'play_start_row': slider_value,
                'speed': speed
            }
            return new_state, '▶ Play', PLAY_BTN_STYLE, ''

    # ========================================
    # Callback 3: DISABLED - Server-side interval updates replaced by clientside playback
    # ========================================
    # DISABLED: playback engine обновляет графики через requestAnimationFrame, не нужен server-side interval
    # @callback(
    #     [
    #         Output('time-slider', 'value', allow_duplicate=True),
    #         Output('playback-status', 'children'),
    #         Output('playback-state', 'data', allow_duplicate=True),
    #         Output('playback-interval', 'disabled', allow_duplicate=True),
    #         Output('play-pause-btn', 'children', allow_duplicate=True),
    #         Output('play-pause-btn', 'style', allow_duplicate=True),
    #         Output('buffer-status', 'children', allow_duplicate=True)
    #     ],
    #     Input('playback-interval', 'n_intervals'),
    #     [
    #         State('playback-state', 'data'),
    #         State('cumulative-times', 'data'),
    #         State('time-slider', 'max'),
    #         State('file-selector', 'value'),
    #         State('buffer-size-slider', 'value')
    #     ],
    #     prevent_initial_call=True
    # )
    # def update_on_interval(n_intervals, state, cumulative_times, max_rows, filename, buffer_size):
    #     """Обновить позицию слайдера на основе прошедшего времени"""
    #     if not state['is_playing'] or not cumulative_times:
    #         return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    #
    #     current_time_ms = int(time.time() * 1000)
    #     elapsed_wall_time = current_time_ms - state['play_start_time']
    #     elapsed_data_time = elapsed_wall_time * state['speed']
    #
    #     start_row = state['play_start_row']
    #     if start_row < len(cumulative_times):
    #         start_offset = cumulative_times[start_row]
    #     else:
    #         start_offset = 0
    #
    #     target_time = start_offset + elapsed_data_time
    #     target_row = bisect.bisect_right(cumulative_times, target_time)
    #     target_row = max(0, min(target_row - 1, max_rows))
    #
    #     # Адаптивная буферизация
    #     buffer_status = no_update
    #     speed = state['speed']
    #
    #     if speed >= 4:
    #         prebuffer_interval = 2
    #     elif speed >= 2:
    #         prebuffer_interval = 3
    #     else:
    #         prebuffer_interval = 5
    #
    #     if n_intervals % prebuffer_interval == 0 and filename:
    #         adaptive_buffer_size = int(buffer_size * (1 + (speed - 1) * 0.3))
    #         adaptive_buffer_size = min(adaptive_buffer_size, buffer_size * 2)
    #
    #         prebuffer_traces(filename, target_row, adaptive_buffer_size)
    #         ahead, total = get_buffer_stats(filename, target_row)
    #         buffer_status = f"Buffer: {ahead} ahead | {total} cached | x{speed}"
    #
    #     if target_row >= max_rows:
    #         new_state = {
    #             'is_playing': False,
    #             'play_start_time': None,
    #             'play_start_row': max_rows,
    #             'speed': state['speed']
    #         }
    #         status = f"Playback complete. Row {max_rows}/{max_rows}"
    #         return max_rows, status, new_state, True, '▶ Play', PLAY_BTN_STYLE, "Playback complete"
    #
    #     total_duration = cumulative_times[-1] if cumulative_times else 0
    #     current_data_time = cumulative_times[target_row] if target_row < len(cumulative_times) else total_duration
    #
    #     elapsed_sec = current_data_time / 1000
    #     total_sec = total_duration / 1000
    #     status = f"x{state['speed']} | {elapsed_sec:.1f}s / {total_sec:.1f}s | Row {target_row}/{max_rows}"
    #
    #     return target_row, status, no_update, no_update, no_update, no_update, buffer_status

    # ========================================
    # Callback 4a: Обновление Orderbook графика через Patch
    # ========================================
    #
    # Trace indices in orderbook chart (create_orderbook_popout_figure):
    #   0: UP Bids (bar)
    #   1: UP Asks (bar)
    #   2: DOWN Bids (bar)
    #   3: DOWN Asks (bar)
    #   4: UP Ask Price line
    #   5: DOWN Ask Price line
    #   6: Current UP Ask marker
    #   7: Current DOWN Ask marker
    #
    @callback(
        Output('chart-orderbook', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),  # ДОБАВЛЕНО: проверка playback
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_orderbook_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить Orderbook только при РУЧНОМ движении слайдера"""

        # ДОБАВЛЕНО: Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        cache = get_data_cache()
        trace_data = cache.compute_trace_data(filename, slider_value)

        patched_fig = Patch()

        # Active-Track: авто-скролл ask prices
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis3']['range'] = [x_min, x_max]  # Ask prices chart (row 2)

        # UP Bids (trace 0)
        patched_fig['data'][0]['y'] = trace_data['up_bids']['y']
        patched_fig['data'][0]['x'] = trace_data['up_bids']['x']
        patched_fig['data'][0]['text'] = trace_data['up_bids']['text']
        patched_fig['data'][0]['marker']['color'] = trace_data['up_bids']['colors']

        # UP Asks (trace 1)
        patched_fig['data'][1]['y'] = trace_data['up_asks']['y']
        patched_fig['data'][1]['x'] = trace_data['up_asks']['x']
        patched_fig['data'][1]['text'] = trace_data['up_asks']['text']
        patched_fig['data'][1]['marker']['color'] = trace_data['up_asks']['colors']

        # DOWN Bids (trace 2)
        patched_fig['data'][2]['y'] = trace_data['down_bids']['y']
        patched_fig['data'][2]['x'] = trace_data['down_bids']['x']
        patched_fig['data'][2]['text'] = trace_data['down_bids']['text']
        patched_fig['data'][2]['marker']['color'] = trace_data['down_bids']['colors']

        # DOWN Asks (trace 3)
        patched_fig['data'][3]['y'] = trace_data['down_asks']['y']
        patched_fig['data'][3]['x'] = trace_data['down_asks']['x']
        patched_fig['data'][3]['text'] = trace_data['down_asks']['text']
        patched_fig['data'][3]['marker']['color'] = trace_data['down_asks']['colors']

        # Current UP Ask marker (trace 6)
        patched_fig['data'][6]['x'] = trace_data['up_ask_price_x']
        patched_fig['data'][6]['y'] = trace_data['up_ask_price_y']

        # Current DOWN Ask marker (trace 7)
        patched_fig['data'][7]['x'] = trace_data['down_ask_price_x']
        patched_fig['data'][7]['y'] = trace_data['down_ask_price_y']

        # Заголовок
        title_text = (
            f"Orderbook @ {trace_data['timestamp']}<br>" +
            f"<sub>UP: {trace_data['up_pressure']} pressure " +
            f"(Bids: ${trace_data['up_bid_total']:,.0f} vs Asks: ${trace_data['up_ask_total']:,.0f}) | " +
            f"DOWN: {trace_data['down_pressure']} pressure " +
            f"(Bids: ${trace_data['down_bid_total']:,.0f} vs Asks: ${trace_data['down_ask_total']:,.0f})</sub>"
        )
        patched_fig['layout']['title']['text'] = title_text

        return patched_fig

    # ========================================
    # Callback 4b: Обновление BTC графика через Patch
    # ========================================
    #
    # Trace indices in btc chart (create_btc_popout_figure):
    #   0: Binance BTC line
    #   1: Oracle BTC line
    #   2: Current Binance marker
    #   3: Current Oracle marker
    #   4: Lag line
    #   5: Current Lag marker
    #
    @callback(
        Output('chart-btc', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),  # ДОБАВЛЕНО: проверка playback
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_btc_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить BTC только при РУЧНОМ движении слайдера"""

        # ДОБАВЛЕНО: Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        cache = get_data_cache()
        trace_data = cache.compute_trace_data(filename, slider_value)

        patched_fig = Patch()

        # Active-Track: авто-скролл btc price + lag
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]   # BTC price (row 1)
            patched_fig['layout']['xaxis2']['range'] = [x_min, x_max]  # Lag (row 2)

        # Current Binance marker (trace 2)
        patched_fig['data'][2]['x'] = trace_data['binance_price_x']
        patched_fig['data'][2]['y'] = trace_data['binance_price_y']

        # Current Oracle marker (trace 3)
        patched_fig['data'][3]['x'] = trace_data['oracle_price_x']
        patched_fig['data'][3]['y'] = trace_data['oracle_price_y']

        # Current Lag marker (trace 5)
        patched_fig['data'][5]['x'] = trace_data['lag_x']
        patched_fig['data'][5]['y'] = trace_data['lag_y']

        # Заголовок BTC
        patched_fig['layout']['title']['text'] = f"BTC Price & Lag @ {trace_data['timestamp']}"

        return patched_fig

    # ========================================
    # Callback 5: Динамическое управление FPS
    # ========================================
    @callback(
        Output('playback-interval', 'interval'),
        Input('fps-selector', 'value')
    )
    def update_fps(interval_ms):
        """Изменить частоту обновления UI"""
        return interval_ms

    # ========================================
    # Callback 6a: Синхронизация осей Orderbook chart
    # ========================================
    # В orderbook chart (2-row, 2-col): xaxis3 = Ask prices (row 2, col 1)
    # Нет других timeseries осей для синхронизации внутри этого чарта.

    # ========================================
    # Callback 6b: Синхронизация осей BTC chart
    # ========================================
    # В btc chart (2-row, 1-col): xaxis = BTC price (row 1), xaxis2 = Lag (row 2)
    @callback(
        Output('chart-btc', 'figure', allow_duplicate=True),
        Input('chart-btc', 'relayoutData'),
        [
            State('active-track-checklist', 'value'),
            State('playback-state', 'data')
        ],
        prevent_initial_call=True
    )
    def sync_btc_chart_axes(relayout_data, active_track, playback_state):
        """Синхронизация осей xaxis (btc) и xaxis2 (lag) при зуме"""
        # Skip during playback - JS handles updates
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if active_track and 'enabled' in active_track:
            return no_update
        if not relayout_data:
            return no_update

        patched_fig = Patch()

        # Зум на BTC price (xaxis) -> обновить lag
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            patched_fig['layout']['xaxis2']['range'] = [
                relayout_data['xaxis.range[0]'],
                relayout_data['xaxis.range[1]']
            ]
            return patched_fig

        # Зум на Lag (xaxis2) -> обновить btc price
        if 'xaxis2.range[0]' in relayout_data and 'xaxis2.range[1]' in relayout_data:
            patched_fig['layout']['xaxis']['range'] = [
                relayout_data['xaxis2.range[0]'],
                relayout_data['xaxis2.range[1]']
            ]
            return patched_fig

        # Сброс зума на BTC price
        if 'xaxis.autorange' in relayout_data:
            patched_fig['layout']['xaxis2']['autorange'] = True
            return patched_fig

        # Сброс зума на Lag
        if 'xaxis2.autorange' in relayout_data:
            patched_fig['layout']['xaxis']['autorange'] = True
            return patched_fig

        return no_update

    # ========================================
    # Callback 7: Обновление info текста zoom slider
    # ========================================
    @callback(
        Output('active-track-zoom-info', 'children'),
        Input('active-track-zoom-slider', 'value')
    )
    def update_zoom_info(zoom_level):
        """Обновить информационный текст о размере окна"""
        total_window = zoom_level * 2
        return f"Window: ±{zoom_level} rows ({total_window} total)"

    # ========================================
    # Pop-Out Window Callbacks
    # ========================================

    # Callback 8: Pop-out buttons — open new tab via clientside callback
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                window.open(window.location.origin + '/?view=orderbook', '_blank');
            }
            return '';
        }
        """,
        Output('_popout-ob-dummy', 'children'),
        Input('popout-orderbook-btn', 'n_clicks'),
        prevent_initial_call=True
    )

    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                window.open(window.location.origin + '/?view=btc', '_blank');
            }
            return '';
        }
        """,
        Output('_popout-btc-dummy', 'children'),
        Input('popout-btc-btn', 'n_clicks'),
        prevent_initial_call=True
    )

    # Callback 9: Синхронизация slider в localStorage для pop-out окон
    @callback(
        Output('shared-slider-value', 'data'),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data')
        ],
        prevent_initial_call=True
    )
    def sync_slider_to_storage(slider_value, filename, playback_state):
        """Записать позицию слайдера в localStorage для pop-out окон"""
        # Skip during playback - JS handles slider sync via BroadcastChannel
        if playback_state and playback_state.get('is_playing'):
            return no_update

        return {
            'value': slider_value,
            'filename': filename,
            'timestamp': int(time.time() * 1000)
        }

    # Callback 10: Синхронизация файла в localStorage
    @callback(
        Output('shared-file-selection', 'data'),
        Input('file-selector', 'value'),
        prevent_initial_call=True
    )
    def sync_file_to_storage(filename):
        """Записать выбранный файл в localStorage для pop-out окон"""
        if not filename:
            return no_update
        return {
            'filename': filename,
            'timestamp': int(time.time() * 1000)
        }

    # Callback 14: Router - Render layout based on URL
    @callback(
        Output('content-container', 'children'),
        Input('url', 'search')
    )
    def display_page(search):
        from .layout import create_main_layout, create_orderbook_popout, create_btc_popout
        
        # Parse query params manually or use simple string check
        if search and 'view=orderbook' in search:
            return create_orderbook_popout()
        elif search and 'view=btc' in search:
            return create_btc_popout()
        else:
            return create_main_layout()

    # Callback 12: Update Pop-out Chart content
    @callback(
        [
            Output('popout-chart', 'figure'),
            Output('popout-last-value', 'data')
        ],
        Input('popout-sync-interval', 'n_intervals'),
        [
            State('shared-slider-value', 'data'),
            State('shared-file-selection', 'data'),
            State('popout-last-value', 'data'),
            State('url', 'search')
        ]
    )
    def update_popout_chart(n, slider_data, file_data, last_value_data, search):
        """Обновить график в pop-out окне"""
        if not slider_data:
            return no_update, no_update

        # Fallback logic: sometimes filename is in slider_data if initializing
        filename = None
        if file_data and file_data.get('filename'):
            filename = file_data.get('filename')
        elif slider_data.get('filename'):
             filename = slider_data.get('filename')
        
        slider_value = slider_data.get('value', 0)
        
        # Optimization: Don't update if value hasn't changed
        last_val = last_value_data.get('value', -1) if last_value_data else -1
        # Also check if filename changed, if so force update
        last_file = last_value_data.get('filename') if last_value_data else None

        if slider_value == last_val and filename == last_file and n > 0:
            return no_update, no_update
            
        if not filename:
             return no_update, no_update

        # Determine view mode from URL
        view_mode = 'main'
        if search and 'view=orderbook' in search:
            view_mode = 'orderbook'
        elif search and 'view=btc' in search:
            view_mode = 'btc'
            
        if view_mode == 'main':
             return no_update, no_update

        # Load data
        try:
             df = load_data(filename)
        except Exception as e:
             print(f"Error loading data for pop-out: {e}")
             return no_update, no_update

        fig = no_update
        if view_mode == 'orderbook':
             fig = create_orderbook_popout_figure(df, slider_value)
        elif view_mode == 'btc':
             fig = create_btc_popout_figure(df, slider_value)
            
        # Store current state
        new_state = {'value': slider_value, 'filename': filename}
        
        return fig, new_state

    # Callback 13: Toggle main page charts based on pop-out status
    @callback(
        [
            Output('chart-orderbook-container', 'style'),
            Output('placeholder-orderbook', 'style'),
            Output('chart-btc-container', 'style'),
            Output('placeholder-btc', 'style')
        ],
        Input('shared-popout-status', 'data'),
        prevent_initial_call=False
    )
    def toggle_charts_visibility(popout_status):
        """
        Скрыть графики на главной странице, если они открыты в pop-out окне.
        Показать вместо них placeholder.
        """
        if not popout_status:
            return {}, {'display': 'none'}, {}, {'display': 'none'}

        # Стили плейсхолдера
        visible_placeholder_style = {
            'display': 'block',
            'backgroundColor': '#2d2d2d',
            'border': '2px dashed #555',
            'borderRadius': '8px',
            'padding': '40px',
            'textAlign': 'center',
            'color': '#888',
            'fontSize': '18px',
            'margin': '10px 0'
        }
        hidden_placeholder_style = {'display': 'none'}
        
        hidden_chart_style = {'display': 'none'}
        visible_chart_style = {'display': 'block'}

        # Orderbook Visibility
        if popout_status.get('orderbook'):
            ob_chart_style = hidden_chart_style
            ob_placeholder_style = visible_placeholder_style
        else:
            ob_chart_style = visible_chart_style
            ob_placeholder_style = hidden_placeholder_style

        # BTC Visibility
        if popout_status.get('btc'):
            btc_chart_style = hidden_chart_style
            btc_placeholder_style = visible_placeholder_style
        else:
            btc_chart_style = visible_chart_style
            btc_placeholder_style = hidden_placeholder_style

        return ob_chart_style, ob_placeholder_style, btc_chart_style, btc_placeholder_style

    # ========================================
    # Callback 14: Load data chunks for clientside playback
    # ========================================
    @callback(
        Output('playback-chunk-data', 'data'),
        Input('playback-chunk-request', 'data'),
        State('file-selector', 'value'),
        prevent_initial_call=True
    )
    def load_chunk_for_playback(chunk_request, filename):
        """
        Загрузить chunk данных для clientside playback engine
        chunk_request = {start_row: int, count: int, reset: bool}
        """
        if not chunk_request or not filename:
            return no_update

        start_row = chunk_request.get('start_row', 0)
        count = chunk_request.get('count', 200)
        reset = chunk_request.get('reset', False)

        from .data_loader import load_data
        from .data_cache import get_data_cache

        df = load_data(filename)
        cache = get_data_cache()

        # Extract batch of trace data
        batch = []
        max_row = len(df) - 1
        end_row = min(start_row + count, max_row + 1)

        for row_idx in range(start_row, end_row):
            trace_data = cache.compute_trace_data(filename, row_idx)
            batch.append(trace_data)

        return {
            'batch': batch,
            'start_row': start_row,
            'count': len(batch),
            'reset': reset
        }

    # ========================================
    # Callback 15: Clientside - receive chunks and feed to playback engine
    # ========================================
    app.clientside_callback(
        """
        function(chunkData) {
            if (!chunkData || !chunkData.batch) {
                return window.dash_clientside.no_update;
            }

            const engine = window.dash_clientside.playback;
            if (engine && engine.receiveBatch) {
                engine.receiveBatch(chunkData.batch, {
                    start_row: chunkData.start_row,
                    reset: chunkData.reset
                });
            }

            return window.dash_clientside.no_update;
        }
        """,
        Output('_chunk-receiver-dummy', 'children'),
        Input('playback-chunk-data', 'data'),
        prevent_initial_call=True
    )

    # ========================================
    # Callback 16: Clientside - activate playback engine when state changes
    # ========================================
    app.clientside_callback(
        """
        function(playbackState, sliderMax) {
            if (!playbackState) {
                return window.dash_clientside.no_update;
            }

            const engine = window.dash_clientside.playback;
            if (engine && engine.updateState) {
                engine.updateState(playbackState, sliderMax);
            }

            return window.dash_clientside.no_update;
        }
        """,
        Output('_playback-engine-dummy', 'children'),
        Input('playback-state', 'data'),
        State('time-slider', 'max'),
        prevent_initial_call=False
    )
