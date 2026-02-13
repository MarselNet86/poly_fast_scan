window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.playback = {
    // Состояние воспроизведения
    state: {
        isPlaying: false,
        globalBuffer: [], // Полный буфер данных в памяти JS
        globalBufferStartRow: 0, // Индекс первой строки в буфере
        lastValues: {}, // Последние значения для оптимизации restyle
        fps: 10,
        speed: 1,
        lastFrameTime: 0,
        chunkRequestThreshold: 0.75, // Запрашивать следующий чанк на 75%
        isChunkRequested: false,
        totalRows: 0,
        currentGlobalRow: 0,
        lastSliderUpdate: 0,  // Для throttling slider updates
        // Page Visibility API support
        rafId: null,           // requestAnimationFrame ID
        intervalId: null,      // setInterval ID
        useInterval: false     // true если вкладка неактивна
    },

    // Инициализация при загрузке страницы
    init: function () {
        console.log("Playback Engine Initialized");

        // ===== PAGE VISIBILITY API =====
        // Переключение между RAF (активная вкладка) и setInterval (фон)
        document.addEventListener('visibilitychange', () => {
            const s = this.state;
            if (!s.isPlaying) return;

            if (document.hidden) {
                // Вкладка стала неактивной → переключаемся на setInterval
                console.log("Tab hidden → switching to setInterval");
                this.stopLoop();
                s.useInterval = true;
                this.startLoop();
            } else {
                // Вкладка стала активной → переключаемся на RAF
                console.log("Tab visible → switching to requestAnimationFrame");
                this.stopLoop();
                s.useInterval = false;
                this.startLoop();
            }
        });
    },

    // Callback: Получение нового batch данных от сервера
    receiveBatch: function (batchData, requestInfo) {
        if (!batchData || batchData.length === 0) return;

        console.log(`Received batch: ${batchData.length} frames. Start: ${requestInfo?.start_row}`);

        const s = this.state;

        // Если это первый чанк или новый seek (сброс буфера)
        if (requestInfo && requestInfo.reset) {
            s.globalBuffer = batchData;
            s.globalBufferStartRow = requestInfo.start_row;
            s.isChunkRequested = false;
        } else {
            // Append (последовательная подгрузка)
            // Проверяем, стыкуется ли конец текущего с началом нового
            const currentEndRow = s.globalBufferStartRow + s.globalBuffer.length;
            if (requestInfo && requestInfo.start_row === currentEndRow) {
                s.globalBuffer = s.globalBuffer.concat(batchData);
                s.isChunkRequested = false;
            } else {
                console.warn("Batch mismatch, resetting buffer");
                s.globalBuffer = batchData;
                s.globalBufferStartRow = requestInfo ? requestInfo.start_row : 0;
                s.isChunkRequested = false;
            }
        }
    },

    // Callback: Управление состоянием (Play/Pause/Seek)
    updateState: function (playbackState, sliderMax) {
        if (!playbackState) return;

        const s = this.state;
        const wasPlaying = s.isPlaying;
        const oldSpeed = s.speed;
        s.isPlaying = playbackState.is_playing;
        s.speed = playbackState.speed || 1;
        s.totalRows = sliderMax || 10000;

        // Если нажали Play, запускаем цикл
        if (s.isPlaying && !wasPlaying) {
            // Если буфер пуст или мы далеко от него, запрашиваем чанк
            const startRow = playbackState.play_start_row || 0;
            s.currentGlobalRow = startRow;

            // Проверяем, есть ли данные в буфере для текущей позиции
            if (!this.isRowInBuffer(startRow)) {
                this.requestChunk(startRow, true);
            }

            // Определяем режим: RAF для активной вкладки, setInterval для фоновой
            s.useInterval = document.hidden;
            this.startLoop();
        }

        // Если скорость изменилась во время воспроизведения в режиме setInterval
        if (s.isPlaying && wasPlaying && s.speed !== oldSpeed && s.useInterval) {
            console.log(`Speed changed to ${s.speed}x, restarting setInterval`);
            this.startLoop(); // stopLoop вызывается внутри startLoop
        }

        // Если нажали Pause/Stop, останавливаем цикл
        if (!s.isPlaying && wasPlaying) {
            this.stopLoop();
        }
    },

    // Проверка наличия строки в буфере
    isRowInBuffer: function (rowIdx) {
        const s = this.state;
        return rowIdx >= s.globalBufferStartRow &&
            rowIdx < (s.globalBufferStartRow + s.globalBuffer.length);
    },

    // Запуск цикла воспроизведения (RAF или setInterval)
    startLoop: function () {
        const s = this.state;
        this.stopLoop(); // Убедимся что нет дубликатов

        if (s.useInterval) {
            // setInterval для фоновых вкладок (браузер не замедляет)
            const targetInterval = 1000 / (s.fps * s.speed);
            s.intervalId = setInterval(() => this.loop(), targetInterval);
            console.log(`Started setInterval loop (${targetInterval}ms)`);
        } else {
            // requestAnimationFrame для активных вкладок (плавно)
            s.rafId = requestAnimationFrame((ts) => this.loop(ts));
            console.log("Started requestAnimationFrame loop");
        }
    },

    // Остановка цикла воспроизведения
    stopLoop: function () {
        const s = this.state;
        if (s.rafId) {
            cancelAnimationFrame(s.rafId);
            s.rafId = null;
        }
        if (s.intervalId) {
            clearInterval(s.intervalId);
            s.intervalId = null;
        }
    },

    // Основной цикл воспроизведения
    loop: function (timestamp) {
        const s = this.state;
        if (!s.isPlaying) {
            this.stopLoop();
            return;
        }

        // timestamp может быть undefined если вызвано через setInterval
        const now = timestamp || performance.now();

        // Контроль FPS (только для RAF режима)
        if (s.useInterval) {
            // setInterval уже контролирует частоту, просто рендерим
            this.renderFrame();
        } else {
            // requestAnimationFrame: контролируем FPS вручную
            if (!s.lastFrameTime) s.lastFrameTime = now;
            const elapsed = now - s.lastFrameTime;
            const targetInterval = 1000 / (s.fps * s.speed);

            if (elapsed > targetInterval) {
                s.lastFrameTime = now - (elapsed % targetInterval);
                this.renderFrame();
            }

            // Запланировать следующий кадр (только для RAF)
            s.rafId = requestAnimationFrame((ts) => this.loop(ts));
        }
    },

    // Отрисовка одного кадра
    renderFrame: function () {
        const s = this.state;
        const row = s.currentGlobalRow;

        // Если достигли конца
        if (row >= s.totalRows) {
            s.isPlaying = false;
            // Обновить состояние на сервере (остановка)
            // window.dash_clientside.set_props(...)
            return;
        }

        // Если данных нет в буфере - пауза/загрузка
        if (!this.isRowInBuffer(row)) {
            // Если мы вышли за пределы буфера и еще не запросили - запрашиваем
            if (!s.isChunkRequested) {
                this.requestChunk(row, true);
            }
            return; // Пропускаем кадр, ждем данных
        }

        // Получаем данные кадра
        const localIdx = row - s.globalBufferStartRow;
        const frameData = s.globalBuffer[localIdx];

        if (frameData) {
            this.updateCharts(frameData);
            this.updateSlider(row); // Синхронизация слайдера
        }

        // Double buffering: если прошли 75% текущего буфера - грузим следующий
        // Но нужно считать не от начала глобального буфера, а от последнего подгруженного чанка?
        // Проще: если осталось меньше N кадров до конца буфера
        const framesLeft = s.globalBuffer.length - localIdx;
        const threshold = 150; // За 150 кадров (1.5 сек при x10)

        if (framesLeft < threshold && !s.isChunkRequested) {
            const nextChunkStart = s.globalBufferStartRow + s.globalBuffer.length;
            if (nextChunkStart < s.totalRows) {
                this.requestChunk(nextChunkStart, false);
            }
        }

        s.currentGlobalRow++;
    },

    // Запрос чанка через Dash Store
    requestChunk: function (startRow, reset) {
        console.log(`Requesting chunk: ${startRow}, reset=${reset}`);
        this.state.isChunkRequested = true;

        // Используем dash_clientside.set_props для обновления Store
        // Требует Dash 2.11+
        window.dash_clientside.set_props(
            'playback-chunk-request',
            { data: { start_row: startRow, count: 500, reset: reset } }
        );
    },

    // Обновление графиков через Plotly.restyle
    updateCharts: function (data) {
        // Orderbook Chart (chart-orderbook)
        const obDiv = document.getElementById('chart-orderbook');
        const obGraph = obDiv ? obDiv.getElementsByClassName('js-plotly-plot')[0] : null;

        if (obGraph) {
            // Подготовка массивов для restyle
            // Indices: 0=UP Bids, 1=UP Asks, 2=DOWN Bids, 3=DOWN Asks
            // Markers: 6=UP Ask M, 7=DOWN Ask M
            // См. callbacks.py update_orderbook_on_slider

            const update = {
                'x': [data.up_bids.x, data.up_asks.x, data.down_bids.x, data.down_asks.x],
                'y': [data.up_bids.y, data.up_asks.y, data.down_bids.y, data.down_asks.y],
                'text': [data.up_bids.text, data.up_asks.text, data.down_bids.text, data.down_asks.text],
                'marker.color': [data.up_bids.colors, data.up_asks.colors, data.down_bids.colors, data.down_asks.colors]
            };
            const traces = [0, 1, 2, 3];

            // Markers update
            const mUpdate = {
                'x': [data.up_ask_price_x, data.down_ask_price_x],
                'y': [data.up_ask_price_y, data.down_ask_price_y]
            };
            const mTraces = [6, 7];

            Plotly.restyle(obGraph, update, traces);
            Plotly.restyle(obGraph, mUpdate, mTraces);

            // Заголовок (layout update)
            const title = `Orderbook @ ${data.timestamp}<br><sub>UP: ${data.up_pressure} | DOWN: ${data.down_pressure}</sub>`;
            Plotly.relayout(obGraph, { 'title.text': title });
        }

        // BTC Chart (chart-btc)
        const btcDiv = document.getElementById('chart-btc');
        const btcGraph = btcDiv ? btcDiv.getElementsByClassName('js-plotly-plot')[0] : null;

        if (btcGraph) {
            // Indices: 2=Binance M, 3=Oracle M, 5=Lag M
            const update = {
                'x': [data.binance_price_x, data.oracle_price_x, data.lag_x],
                'y': [data.binance_price_y, data.oracle_price_y, data.lag_y]
            };
            const traces = [2, 3, 5];
            Plotly.restyle(btcGraph, update, traces);
            // REMOVED: Plotly.relayout triggers HTTP request to sync_btc_chart_axes callback
            // Title update not critical during playback
        }
    },

    // Синхронизация слайдера (визуальная)
    updateSlider: function (row) {
        // ОПТИМИЗАЦИЯ: Обновляем слайдер РЕДКО (раз в секунду), не каждый кадр!
        // Даже если callbacks блокируются через is_playing, set_props все равно делает HTTP запрос.
        // Throttling: обновляем слайдер максимум раз в 1000ms
        const now = Date.now();
        const s = this.state;

        if (now - s.lastSliderUpdate < 1000) {
            return;  // Skip update, слишком рано
        }

        s.lastSliderUpdate = now;
        window.dash_clientside.set_props('time-slider', { value: row });
    }
};
