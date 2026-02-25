"""
Callbacks Module
Callback функции для интерактивности Dash приложения
"""

import time
from dash import html, callback, Output, Input, State, ctx, no_update, Patch
from .data_loader import load_data, compute_cumulative_times
from .charts import create_orderbook_chart, create_arbitrage_indicator_chart, create_spread_chart, create_imbalance_chart, create_microprice_chart, create_slope_chart, create_eatflow_chart, create_depth_chart, create_btc_chart, create_latency_direction_chart, create_returns_chart, create_volume_chart, create_volatility_chart, create_volume_spike_chart, create_p_vwap_chart
from .data_cache import get_data_cache
from .api.polymarket_api import search_market, fetch_trades, parse_trades, TRADER_ADDRESS
from .utils.filename_parser import extract_game_datetime_from_csv, build_market_query
from .widgets.microprice_chart import build_timestamp_to_row_mapping


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
            Output('chart-imbalance', 'figure'),
            Output('chart-microprice', 'figure'),
            Output('chart-slope', 'figure'),
            Output('chart-eatflow', 'figure'),
            Output('chart-depth', 'figure'),
            Output('chart-btc', 'figure'),
            Output('chart-latency-direction', 'figure'),
            Output('chart-returns', 'figure'),
            Output('chart-volume', 'figure'),
            Output('chart-volatility', 'figure'),
            Output('chart-volume-spike', 'figure'),
            Output('chart-p-vwap', 'figure'),
            Output('trader-data', 'data'),
            Output('trader-loading-state', 'data')
        ],
        Input('file-selector', 'value')
    )
    def init_on_file_change(filename):
        """Инициализировать все компоненты при смене файла"""
        if not filename:
            empty_fig = {'data': [], 'layout': {'paper_bgcolor': '#1e1e1e', 'plot_bgcolor': '#2d2d2d'}}
            return [], 0, {}, 0, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, None, {'is_loading': False}

        cache = get_data_cache()
        df = cache.get_df(filename)
        cumulative_times = compute_cumulative_times(df)

        # === TRADER DATA FETCH ===
        trader_data = None
        trader_loading_state = {'is_loading': False}

        try:
            # Step 1: Extract game datetime from CSV
            game_datetime = extract_game_datetime_from_csv(df)

            if game_datetime:
                # Step 2: Build market query
                market_query = build_market_query(game_datetime)
                print(f"Searching for market: {market_query}")

                # Step 3: Search for market
                event, market = search_market(market_query, timeout=10)

                if market:
                    condition_id = market.get('conditionId')
                    print(f"Found market: {market.get('question', 'Unknown')}")
                    print(f"Condition ID: {condition_id}")

                    # Step 4: Fetch trades
                    if condition_id:
                        raw_trades = fetch_trades(condition_id, TRADER_ADDRESS, timeout=15)

                        if raw_trades:
                            # Step 5: Parse trades
                            parsed_trades = parse_trades(raw_trades)
                            print(f"Found {len(parsed_trades)} trades for trader {TRADER_ADDRESS}")

                            # Step 6: Build timestamp mapping
                            row_mapping = build_timestamp_to_row_mapping(df, parsed_trades)

                            # Step 7: Store trader data
                            trader_data = {
                                'trades': parsed_trades,
                                'row_mapping': row_mapping,
                                'market_name': market.get('question') or market.get('title'),
                                'condition_id': condition_id
                            }
                        else:
                            print(f"No trades found for trader {TRADER_ADDRESS}")
                else:
                    print(f"Market not found for query: {market_query}")
            else:
                print("Could not extract game datetime from CSV")

        except Exception as e:
            print(f"Error fetching trader data: {e}")
            trader_data = None

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
        imbalance_fig = create_imbalance_chart(df, 0)
        microprice_fig = create_microprice_chart(df, 0, trader_data=trader_data)
        slope_fig = create_slope_chart(df, 0)
        eatflow_fig = create_eatflow_chart(df, 0)
        depth_fig = create_depth_chart(df, 0)
        btc_fig = create_btc_chart(df, 0)
        latency_direction_fig = create_latency_direction_chart(df, 0)
        returns_fig = create_returns_chart(df, 0)
        volume_fig = create_volume_chart(df, 0)
        volatility_fig = create_volatility_chart(df, 0)
        volume_spike_fig = create_volume_spike_chart(df, 0)
        p_vwap_fig = create_p_vwap_chart(df, 0)

        return cumulative_times, max_val, marks, 0, ob_fig, arbitrage_indicator_fig, spread_fig, imbalance_fig, microprice_fig, slope_fig, eatflow_fig, depth_fig, btc_fig, latency_direction_fig, returns_fig, volume_fig, volatility_fig, volume_spike_fig, p_vwap_fig, trader_data, trader_loading_state

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
    # Callback 4b-new2: Обновление Imbalance графика через Patch
    # ========================================
    @callback(
        Output('chart-imbalance', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_imbalance_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Imbalance при изменении слайдера.
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
        patched_fig['layout']['title']['text'] = "Imbalance (Имбаланс)"

        return patched_fig


    # ========================================
    # Callback 4b-new3: Обновление Microprice графика через Patch
    # ========================================
    @callback(
        Output('chart-microprice', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_microprice_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Microprice при изменении слайдера.
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
        patched_fig['layout']['title']['text'] = "Microprice (Микроцена)"

        return patched_fig


    # ========================================
    # Callback 4b-new4: Обновление Slope графика через Patch
    # ========================================
    @callback(
        Output('chart-slope', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_slope_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график Slope при изменении слайдера.
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
        patched_fig['layout']['title']['text'] = "Slope (Наклон)"

        return patched_fig


    # ========================================
    # Callback 4b-new5: Обновление EatFlow графика через Patch
    # ========================================
    @callback(
        Output('chart-eatflow', 'figure', allow_duplicate=True),
        Input('time-slider', 'value'),
        [
            State('file-selector', 'value'),
            State('playback-state', 'data'),
            State('active-track-checklist', 'value'),
            State('active-track-zoom-slider', 'value')
        ],
        prevent_initial_call=True
    )
    def update_eatflow_on_slider(slider_value, filename, playback_state, active_track, zoom_level):
        """
        Обновить график EatFlow при изменении слайдера.
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
        patched_fig['layout']['title']['text'] = "EatFlow (Скорость поедания)"

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
            return no_update

        # Сброс зума на Lag
        if 'xaxis2.autorange' in relayout_data:
            return no_update

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
            return no_update

        # Сброс зума на RVol
        if 'xaxis2.autorange' in relayout_data:
            return no_update

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

    # ========================================
    # Callback 10: Обработка кликов для crosshair
    # ========================================
    @callback(
        Output('crosshair-x-position', 'data'),
        [
            Input('chart-orderbook', 'clickData'),
            Input('chart-microprice', 'clickData'),
            Input('chart-arbitrage-indicator', 'clickData'),
            Input('chart-spread', 'clickData'),
            Input('chart-imbalance', 'clickData'),
            Input('chart-slope', 'clickData'),
            Input('chart-eatflow', 'clickData'),
            Input('chart-depth', 'clickData'),
            Input('chart-btc', 'clickData'),
            Input('chart-latency-direction', 'clickData'),
            Input('chart-returns', 'clickData'),
            Input('chart-volume', 'clickData'),
            Input('chart-volatility', 'clickData'),
            Input('chart-volume-spike', 'clickData'),
            Input('chart-p-vwap', 'clickData')
        ],
        prevent_initial_call=True
    )
    def update_crosshair_position(*click_data_list):
        """Обработать клик на любом из графиков"""
        if not ctx.triggered:
            return no_update

        click_data = ctx.triggered[0]['value']
        if not click_data or 'points' not in click_data:
            return no_update

        # Извлечь координату X (row_idx)
        x_coord = click_data['points'][0]['x']

        return {
            'x': x_coord,
            'timestamp': time.time()
        }

    # ========================================
    # Callback 11: Извлечение значений в точке crosshair
    # ========================================
    @callback(
        Output('crosshair-values', 'data'),
        Input('crosshair-x-position', 'data'),
        State('file-selector', 'value'),
        prevent_initial_call=True
    )
    def extract_crosshair_values(crosshair_pos, filename):
        """Извлечь значения всех метрик в точке crosshair"""
        if not crosshair_pos or not filename:
            return None

        x_coord = crosshair_pos['x']
        row_idx = int(round(x_coord))

        cache = get_data_cache()
        df = cache.get_df(filename)

        if row_idx < 0 or row_idx >= len(df):
            return None

        row = df.iloc[row_idx]

        # Собрать все метрики из CSV
        return {
            'row_idx': row_idx,
            'timestamp_et': row.get('timestamp_et', 'N/A'),
            'time_till_end': row.get('time_till_end', 'N/A'),
            # Microprice
            'pm_up_microprice': row.get('pm_up_microprice'),
            'pm_down_microprice': row.get('pm_down_microprice'),
            # Spread
            'pm_up_spread': row.get('pm_up_spread'),
            'pm_down_spread': row.get('pm_down_spread'),
            # Imbalance
            'pm_up_imbalance': row.get('pm_up_imbalance'),
            'pm_down_imbalance': row.get('pm_down_imbalance'),
            # BTC
            'binance_btc_price': row.get('binance_btc_price'),
            'oracle_btc_price': row.get('oracle_btc_price'),
            'lag': row.get('lag'),
            # Returns
            'binance_ret1s_x100': row.get('binance_ret1s_x100'),
            'binance_ret5s_x100': row.get('binance_ret5s_x100'),
            # Volume
            'binance_volume_1s': row.get('binance_volume_1s'),
            'binance_volume_5s': row.get('binance_volume_5s'),
            'binance_volma_30s': row.get('binance_volma_30s'),
            # Volatility
            'binance_atr_5s': row.get('binance_atr_5s'),
            'binance_atr_30s': row.get('binance_atr_30s'),
            'binance_rvol_30s': row.get('binance_rvol_30s'),
            # Volume spike
            'binance_volume_spike': row.get('binance_volume_spike'),
            # P/VWAP
            'binance_p_vwap_5s': row.get('binance_p_vwap_5s'),
            'binance_p_vwap_30s': row.get('binance_p_vwap_30s'),
            # Depth
            'pm_up_bid_depth5': row.get('pm_up_bid_depth5'),
            'pm_up_ask_depth5': row.get('pm_up_ask_depth5'),
            'pm_down_bid_depth5': row.get('pm_down_bid_depth5'),
            'pm_down_ask_depth5': row.get('pm_down_ask_depth5'),
            # EatFlow
            'pm_up_bid_eatflow': row.get('pm_up_bid_eatflow'),
            'pm_up_ask_eatflow': row.get('pm_up_ask_eatflow'),
            'pm_down_bid_eatflow': row.get('pm_down_bid_eatflow'),
            'pm_down_ask_eatflow': row.get('pm_down_ask_eatflow'),
            # Slope
            'pm_up_bid_slope': row.get('pm_up_bid_slope'),
            'pm_up_ask_slope': row.get('pm_up_ask_slope'),
            'pm_down_bid_slope': row.get('pm_down_bid_slope'),
            'pm_down_ask_slope': row.get('pm_down_ask_slope'),
            # Latency direction
            'lat_dir_raw_x1000': row.get('lat_dir_raw_x1000'),
            'lat_dir_norm_x1000': row.get('lat_dir_norm_x1000'),
        }

    # ========================================
    # Callback 12: Обновление вертикальных линий на всех графиках
    # ========================================
    @callback(
        [
            Output('chart-orderbook', 'figure', allow_duplicate=True),
            Output('chart-microprice', 'figure', allow_duplicate=True),
            Output('chart-arbitrage-indicator', 'figure', allow_duplicate=True),
            Output('chart-spread', 'figure', allow_duplicate=True),
            Output('chart-imbalance', 'figure', allow_duplicate=True),
            Output('chart-slope', 'figure', allow_duplicate=True),
            Output('chart-eatflow', 'figure', allow_duplicate=True),
            Output('chart-depth', 'figure', allow_duplicate=True),
            Output('chart-btc', 'figure', allow_duplicate=True),
            Output('chart-latency-direction', 'figure', allow_duplicate=True),
            Output('chart-returns', 'figure', allow_duplicate=True),
            Output('chart-volume', 'figure', allow_duplicate=True),
            Output('chart-volatility', 'figure', allow_duplicate=True),
            Output('chart-volume-spike', 'figure', allow_duplicate=True),
            Output('chart-p-vwap', 'figure', allow_duplicate=True)
        ],
        Input('crosshair-x-position', 'data'),
        prevent_initial_call=True
    )
    def update_crosshair_lines(crosshair_pos):
        """Обновить вертикальную линию crosshair на всех графиках"""
        patches = []

        if not crosshair_pos:
            # Убрать все линии
            for _ in range(15):
                patched_fig = Patch()
                patched_fig['layout']['shapes'] = []
                patches.append(patched_fig)
            return patches

        x_coord = crosshair_pos['x']

        # Создать линию для каждого графика
        # Графики с subplots нуждаются в линиях для каждого subplot

        # Список названий графиков для определения структуры
        chart_names = [
            'orderbook',      # 0: 2x2 subplots (4 квадранта + ask prices внизу)
            'microprice',     # 1: 1 subplot
            'arbitrage',      # 2: 1 subplot
            'spread',         # 3: 1 subplot
            'imbalance',      # 4: 1 subplot
            'slope',          # 5: 1 subplot
            'eatflow',        # 6: 1 subplot
            'depth',          # 7: 1 subplot
            'btc',            # 8: 2 subplots (BTC + Lag)
            'latency',        # 9: 1 subplot
            'returns',        # 10: 1 subplot
            'volume',         # 11: 1 subplot
            'volatility',     # 12: 2 subplots (ATR + RVol)
            'volume_spike',   # 13: 1 subplot
            'p_vwap'          # 14: 1 subplot
        ]

        for idx, chart_name in enumerate(chart_names):
            patched_fig = Patch()

            if chart_name == 'orderbook':
                # Orderbook: линия только на ask prices chart (subplot 3)
                patched_fig['layout']['shapes'] = [
                    {
                        'type': 'line',
                        'x0': x_coord,
                        'x1': x_coord,
                        'y0': 0,
                        'y1': 1,
                        'yref': 'paper',
                        'xref': 'x3',  # Ask prices chart
                        'line': {
                            'color': 'rgba(255, 215, 0, 0.8)',
                            'width': 2,
                            'dash': 'solid'
                        }
                    }
                ]
            elif chart_name in ['btc', 'volatility']:
                # 2 subplots: добавить линию на оба
                patched_fig['layout']['shapes'] = [
                    {
                        'type': 'line',
                        'x0': x_coord,
                        'x1': x_coord,
                        'y0': 0,
                        'y1': 1,
                        'yref': 'paper',
                        'xref': 'x',  # Первый subplot
                        'line': {
                            'color': 'rgba(255, 215, 0, 0.8)',
                            'width': 2,
                            'dash': 'solid'
                        }
                    },
                    {
                        'type': 'line',
                        'x0': x_coord,
                        'x1': x_coord,
                        'y0': 0,
                        'y1': 1,
                        'yref': 'paper',
                        'xref': 'x2',  # Второй subplot
                        'line': {
                            'color': 'rgba(255, 215, 0, 0.8)',
                            'width': 2,
                            'dash': 'solid'
                        }
                    }
                ]
            else:
                # Одинарные графики
                patched_fig['layout']['shapes'] = [
                    {
                        'type': 'line',
                        'x0': x_coord,
                        'x1': x_coord,
                        'y0': 0,
                        'y1': 1,
                        'yref': 'paper',
                        'xref': 'x',
                        'line': {
                            'color': 'rgba(255, 215, 0, 0.8)',
                            'width': 2,
                            'dash': 'solid'
                        }
                    }
                ]

            patches.append(patched_fig)

        return patches
