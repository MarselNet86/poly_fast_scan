"""
Callbacks Module
Callback функции для интерактивности Dash приложения
"""

import time
from dash import html, callback, Output, Input, State, ctx, no_update, Patch
from .data_loader import load_data, compute_cumulative_times
from .charts import create_orderbook_chart, create_arbitrage_indicator_chart, create_spread_chart, create_depth_chart, create_btc_chart, create_latency_direction_chart, create_returns_chart, create_volume_chart, create_volatility_chart, create_volume_spike_chart, create_p_vwap_chart
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
            Output('chart-orderbook', 'figure'),
            Output('chart-arbitrage-indicator', 'figure'),
            Output('chart-spread', 'figure'),
            Output('chart-depth', 'figure'),
            Output('chart-btc', 'figure'),
            Output('chart-latency-direction', 'figure'),
            Output('chart-returns', 'figure'),
            Output('chart-volume', 'figure'),
            Output('chart-volatility', 'figure'),
            Output('chart-volume-spike', 'figure'),
            Output('chart-p-vwap', 'figure')
        ],
        Input('file-selector', 'value')
    )
    def init_on_file_change(filename):
        """Инициализировать все компоненты при смене файла"""
        if not filename:
            empty_fig = {'data': [], 'layout': {'paper_bgcolor': '#1e1e1e', 'plot_bgcolor': '#2d2d2d'}}
            return [], 0, {}, 0, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

        cache = get_data_cache()
        df = cache.get_df(filename)
        cumulative_times = compute_cumulative_times(df)

        max_val = len(df) - 1
        # Создаем только 5 меток для лучшей читаемости
        step = max(1, max_val // 4)
        marks = {
            i: {'label': str(i), 'style': {'color': 'white'}}
            for i in range(0, max_val + 1, step)
        }

        # Создаем начальные графики (десять независимых)
        ob_fig = create_orderbook_chart(df, 0)
        arbitrage_indicator_fig = create_arbitrage_indicator_chart(df, 0)
        spread_fig = create_spread_chart(df, 0)
        depth_fig = create_depth_chart(df, 0)
        btc_fig = create_btc_chart(df, 0)
        latency_direction_fig = create_latency_direction_chart(df, 0)
        returns_fig = create_returns_chart(df, 0)
        volume_fig = create_volume_chart(df, 0)
        volatility_fig = create_volatility_chart(df, 0)
        volume_spike_fig = create_volume_spike_chart(df, 0)
        p_vwap_fig = create_p_vwap_chart(df, 0)

        return cumulative_times, max_val, marks, 0, ob_fig, arbitrage_indicator_fig, spread_fig, depth_fig, btc_fig, latency_direction_fig, returns_fig, volume_fig, volatility_fig, volume_spike_fig, p_vwap_fig

    # ========================================
    # Callback 2: Обработка Play/Pause кнопки
    # ========================================
    @callback(
        [
            Output('playback-state', 'data'),
            Output('play-pause-btn', 'children'),
            Output('play-pause-btn', 'style')
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
            return new_state, '⏸ Pause', PAUSE_BTN_STYLE
        else:
            new_state = {
                'is_playing': False,
                'play_start_time': None,
                'play_start_row': slider_value,
                'speed': speed
            }
            return new_state, '▶ Play', PLAY_BTN_STYLE

    # ========================================
    # Callback 3: Обновление Orderbook графика через Patch
    # ========================================
    #
    # Trace indices in orderbook chart (create_orderbook_figure):
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
        patched_fig['layout']['title']['text'] = "Orderbook"

        return patched_fig

    # ========================================
    # Callback 4b: Обновление Arbitrage Indicator графика через Patch
    # ========================================
    @callback(
        Output('chart-arbitrage-indicator', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_arbitrage_indicator_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Arbitrage Indicator при изменении слайдера.
        Пропускает обновление во время playback.
        """
        # Пропустить если идёт playback
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: автопрокрутка по X
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Обновить заголовок
        patched_fig['layout']['title']['text'] = "Arbitrage Indicator (Арбитраж)"

        return patched_fig


    # ========================================
    # Callback 4b-new: Обновление Spread графика через Patch
    # ========================================
    @callback(
        Output('chart-spread', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_spread_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Spread при изменении слайдера.
        Пропускает обновление во время playback.
        """
        # Пропустить если идёт playback
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: автопрокрутка по X
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Обновить заголовок
        patched_fig['layout']['title']['text'] = "Spread (Спред)"

        return patched_fig

    # ========================================
    # Callback 4b2: Обновление Depth графика через Patch
    # ========================================
    @callback(
        Output('chart-depth', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_depth_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Depth при изменении слайдера.
        Пропускает обновление во время playback.
        """
        # Пропустить если идёт playback
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: автопрокрутка по X
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Обновить заголовок
        patched_fig['layout']['title']['text'] = "Depth (Глубина ликвидности)"

        return patched_fig

    # ========================================
    # Callback 4c: Обновление BTC графика через Patch
    # ========================================
    #
    # Trace indices in btc chart (create_btc_figure):
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
        patched_fig['layout']['title']['text'] = "BTC Price & Lag"

        return patched_fig

    # ========================================
    # Callback 4c: Обновление Latency Direction графика через Patch
    # ========================================
    @callback(
        Output('chart-latency-direction', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_latency_direction_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Latency Direction при изменении слайдера.
        Пропускает обновление во время playback.
        """
        # Пропустить если идёт playback
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: автопрокрутка по X
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Обновить заголовок
        patched_fig['layout']['title']['text'] = "Latency Direction (запаздывание оракула)"

        return patched_fig

    # ========================================
    # Callback 4d: Обновление Returns графика через Patch
    # ========================================
    #
    # Trace indices in returns chart (create_returns_figure):
    #   0: Ret5s line (сглаженный тренд)
    #   1: Ret1s line (быстрый сигнал)
    #
    @callback(
        Output('chart-returns', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_returns_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить Returns только при РУЧНОМ движении слайдера"""

        # Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: авто-скролл returns
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Заголовок Returns
        patched_fig['layout']['title']['text'] = "Ret1s & Ret5s"

        return patched_fig

    # ========================================
    # Callback 4d: Обновление Volume графика через Patch
    # ========================================
    #
    # Trace indices in volume chart (create_volume_figure):
    #   0: Volume 5s line
    #   1: Volume 1s line
    #   2: VolMA 30s line
    #
    @callback(
        Output('chart-volume', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_volume_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить Volume только при РУЧНОМ движении слайдера"""

        # Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: авто-скролл volume
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Заголовок Volume
        patched_fig['layout']['title']['text'] = "Volume (USDT)"

        return patched_fig

    # ========================================
    # Callback 4e: Обновление Volatility графика через Patch
    # ========================================
    #
    # Trace indices in volatility chart (create_volatility_figure):
    #   0: ATR 5s line (subplot 1)
    #   1: ATR 30s line (subplot 1)
    #   2: RVol 30s line (subplot 2)
    #
    @callback(
        Output('chart-volatility', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_volatility_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить Volatility только при РУЧНОМ движении слайдера"""

        # Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: авто-скролл volatility (оба подграфика)
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]
            patched_fig['layout']['xaxis2']['range'] = [x_min, x_max]

        # Заголовок Volatility
        patched_fig['layout']['title']['text'] = "Volatility (ATR & RVol)"

        return patched_fig

    # ========================================
    # Callback 4f: Обновление Volume Spike графика через Patch
    # ========================================
    #
    # Trace indices in volume spike chart (create_volume_spike_figure):
    #   0: Volume Spike line
    #
    @callback(
        Output('chart-volume-spike', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_volume_spike_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить Volume Spike только при РУЧНОМ движении слайдера"""

        # Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: авто-скролл volume spike
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Заголовок Volume Spike
        patched_fig['layout']['title']['text'] = "Volume Spike"

        return patched_fig

    # ========================================
    # Callback 4g: Обновление P/VWAP графика через Patch
    # ========================================
    #
    # Trace indices in p_vwap chart (create_p_vwap_figure):
    #   0: P/VWAP 30s line (тренд)
    #   1: P/VWAP 5s line (сигнал)
    #
    @callback(
        Output('chart-p-vwap', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_p_vwap_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """Обновить P/VWAP только при РУЧНОМ движении слайдера"""

        # Skip if playback is active (JS handles updates)
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if not filename:
            return no_update

        patched_fig = Patch()

        # Active-Track: авто-скролл p/vwap
        if active_track and 'enabled' in active_track:
            half_window = zoom_level if zoom_level else 150
            x_min = max(0, slider_value - half_window)
            x_max = slider_value + half_window
            patched_fig['layout']['xaxis']['range'] = [x_min, x_max]

        # Заголовок P/VWAP
        patched_fig['layout']['title']['text'] = "P/VWAP (% отклонение от VWAP)"

        return patched_fig

    # ========================================
    # Callback 5: Синхронизация осей Orderbook chart
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
    # Callback 6c: Синхронизация осей Volatility chart
    # ========================================
    # В volatility chart (2-row, 1-col): xaxis = ATR (row 1), xaxis2 = RVol (row 2)
    @callback(
        Output('chart-volatility', 'figure', allow_duplicate=True),
        Input('chart-volatility', 'relayoutData'),
        [
            State('active-track-checklist', 'value'),
            State('playback-state', 'data')
        ],
        prevent_initial_call=True
    )
    def sync_volatility_chart_axes(relayout_data, active_track, playback_state):
        """Синхронизация осей xaxis (ATR) и xaxis2 (RVol) при зуме"""
        # Skip during playback - JS handles updates
        if playback_state and playback_state.get('is_playing'):
            return no_update

        if active_track and 'enabled' in active_track:
            return no_update
        if not relayout_data:
            return no_update

        patched_fig = Patch()

        # Зум на ATR (xaxis) -> обновить RVol
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            patched_fig['layout']['xaxis2']['range'] = [
                relayout_data['xaxis.range[0]'],
                relayout_data['xaxis.range[1]']
            ]
            return patched_fig

        # Зум на RVol (xaxis2) -> обновить ATR
        if 'xaxis2.range[0]' in relayout_data and 'xaxis2.range[1]' in relayout_data:
            patched_fig['layout']['xaxis']['range'] = [
                relayout_data['xaxis2.range[0]'],
                relayout_data['xaxis2.range[1]']
            ]
            return patched_fig

        # Сброс зума на ATR
        if 'xaxis.autorange' in relayout_data:
            patched_fig['layout']['xaxis2']['autorange'] = True
            return patched_fig

        # Сброс зума на RVol
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
    # Callback 8: Load data chunks for clientside playback
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

    # ========================================
    # Callback 8: Clientside - Initialize Playback Engine on main page
    # ========================================
    app.clientside_callback(
        """
        function(_) {
            console.log('[Main Page] Initializing playback engine...');

            // Проверяем что playback engine загружен
            if (window.dash_clientside.playback && window.dash_clientside.playback.init) {
                window.dash_clientside.playback.init();
                console.log('[Main Page] Playback engine initialized');
            } else {
                console.warn('[Main Page] Playback engine not found, retrying in 100ms');
                setTimeout(() => {
                    if (window.dash_clientside.playback && window.dash_clientside.playback.init) {
                        window.dash_clientside.playback.init();
                        console.log('[Main Page] Playback engine initialized (retry)');
                    }
                }, 100);
            }

            return '';
        }
        """,
        Output('_playback-init-dummy', 'children'),
        Input('_playback-init-dummy', 'id'),
        prevent_initial_call=False
    )

    # ========================================
    # Callback 9: Update Market Timer
    # ========================================
    @callback(
        [
            Output('countdown-display', 'children'),
            Output('countdown-seconds', 'children')
        ],
        [
            Input('file-selector', 'value'),
            Input('time-slider', 'value')
        ]
    )
    def update_market_timer(filename, row_idx):
        """Обновить таймер времени до закрытия рынка"""
        if not filename or row_idx is None:
            return '--:--', '(--- сек)'

        try:
            # Получить данные для текущей строки
            cache = get_data_cache()
            trace_data = cache.compute_trace_data(filename, row_idx)

            # Извлечь временные данные
            seconds_till_end = trace_data.get('seconds_till_end', None)
            time_till_end = trace_data.get('time_till_end', '--:--')

            # Форматировать отображение секунд
            seconds_display = f"({seconds_till_end} сек)" if seconds_till_end is not None else "(--- сек)"

            return str(time_till_end), seconds_display

        except Exception as e:
            print(f"Error updating market timer: {e}")
            return '--:--', '(--- сек)'
