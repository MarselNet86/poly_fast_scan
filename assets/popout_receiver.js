window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.popout = {
    channel: null,

    // Инициализация ресивера в pop-out окне
    init: function () {
        console.log("[Popout Receiver] Initializing...");

        if (this.channel) {
            console.warn("[Popout Receiver] Already initialized, closing old channel");
            this.channel.close();
        }

        this.channel = new BroadcastChannel('dash_playback_sync');
        console.log("[Popout Receiver] BroadcastChannel created");

        let messageCount = 0;

        this.channel.onmessage = (event) => {
            messageCount++;

            if (event.data.type === 'frame') {
                if (messageCount % 10 === 0) {  // Логируем каждый 10-й кадр
                    console.log(`[Popout Receiver] Received frame ${messageCount}, row=${event.data.row}`);
                }
                this.updateCharts(event.data.data);
            } else if (event.data.type === 'state') {
                console.log('[Popout Receiver] Received state change:', event.data.data);
            }
        };

        console.log("[Popout Receiver] Message listener attached, ready to receive frames");
    },

    // Обновление графиков (копия логики из playback_engine для независимости)
    updateCharts: function (data) {
        // Определяем тип view из URL
        const isOrderbook = window.location.search.includes('view=orderbook');
        const isBtc = window.location.search.includes('view=btc');

        if (isOrderbook) {
            const obDiv = document.getElementById('popout-chart');
            const obGraph = obDiv ? obDiv.getElementsByClassName('js-plotly-plot')[0] : null;

            if (!obGraph) {
                console.warn('[Popout Receiver] Orderbook graph not found, skipping update');
                return;
            }

            try {
                const update = {
                    'x': [data.up_bids.x, data.up_asks.x, data.down_bids.x, data.down_asks.x],
                    'y': [data.up_bids.y, data.up_asks.y, data.down_bids.y, data.down_asks.y],
                    'text': [data.up_bids.text, data.up_asks.text, data.down_bids.text, data.down_asks.text],
                    'marker.color': [data.up_bids.colors, data.up_asks.colors, data.down_bids.colors, data.down_asks.colors]
                };
                const traces = [0, 1, 2, 3];

                const mUpdate = {
                    'x': [data.up_ask_price_x, data.down_ask_price_x],
                    'y': [data.up_ask_price_y, data.down_ask_price_y]
                };
                const mTraces = [6, 7];

                Plotly.restyle(obGraph, update, traces);
                Plotly.restyle(obGraph, mUpdate, mTraces);

                const title = `Orderbook @ ${data.timestamp}<br><sub>UP: ${data.up_pressure} | DOWN: ${data.down_pressure}</sub>`;
                Plotly.relayout(obGraph, { 'title.text': title });
            } catch (error) {
                console.error('[Popout Receiver] Error updating orderbook chart:', error);
            }
        }

        if (isBtc) {
            const btcDiv = document.getElementById('popout-chart');
            const btcGraph = btcDiv ? btcDiv.getElementsByClassName('js-plotly-plot')[0] : null;

            if (!btcGraph) {
                console.warn('[Popout Receiver] BTC graph not found, skipping update');
                return;
            }

            try {
                const update = {
                    'x': [data.binance_price_x, data.oracle_price_x, data.lag_x],
                    'y': [data.binance_price_y, data.oracle_price_y, data.lag_y]
                };
                const traces = [2, 3, 5];
                Plotly.restyle(btcGraph, update, traces);

                // Also update title for BTC chart in popout
                Plotly.relayout(btcGraph, { 'title.text': `BTC Price & Lag @ ${data.timestamp}` });
            } catch (error) {
                console.error('[Popout Receiver] Error updating BTC chart:', error);
            }
        }
    }
};
