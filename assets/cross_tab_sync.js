/**
 * Cross-Tab Synchronization for xDaimon FastScan
 * Использует BroadcastChannel API для мгновенной синхронизации между вкладками
 */

(function () {
    'use strict';

    // BroadcastChannel для синхронизации между вкладками
    const channel = new BroadcastChannel('fastscan_sync');

    // Слушаем сообщения от других вкладок
    channel.onmessage = function (event) {
        const { type, data } = event.data;

        if (type === 'SLIDER_UPDATE') {
            // Обновляем localStorage для триггера Dash callback
            localStorage.setItem('shared-slider-value', JSON.stringify({
                value: data.value,
                timestamp: Date.now()
            }));
        }

        if (type === 'FILE_CHANGE') {
            localStorage.setItem('shared-file-selection', JSON.stringify({
                filename: data.filename,
                timestamp: Date.now()
            }));
        }

        if (type === 'PLAYBACK_STATE') {
            localStorage.setItem('shared-playback-state', JSON.stringify({
                ...data,
                timestamp: Date.now()
            }));
        }
    };

    // Функция для обновления статуса pop-out окна
    function updatePopoutStatus(view, isOpen) {
        try {
            const key = 'shared-popout-status';
            const currentStr = localStorage.getItem(key);
            let status = {};
            if (currentStr) {
                try {
                    status = JSON.parse(currentStr);
                } catch (e) {
                    status = {};
                }
            }

            status[view] = isOpen;
            status['timestamp'] = Date.now();

            localStorage.setItem(key, JSON.stringify(status));
        } catch (e) {
            console.error('Error updating popout status:', e);
        }
    }

    // Функция для открытия Orderbook pop-out окна (стандартная вкладка)
    window.openOrderbookPopout = function () {
        window.open('/?view=orderbook', '_blank');
    };

    // Функция для открытия BTC pop-out окна (стандартная вкладка)
    window.openBtcPopout = function () {
        window.open('/?view=btc', '_blank');
    };

    // ... (broadcast functions remain same) ...

    // Добавляем обработчики кликов для кнопок pop-out
    document.addEventListener('DOMContentLoaded', function () {
        // ... (click listeners remain same) ...
    });

    // Определяем текущий view mode
    const urlParams = new URLSearchParams(window.location.search);
    const viewMode = urlParams.get('view') || 'main';

    console.log('FastScan cross-tab sync initialized, view mode:', viewMode);

    // Логика для pop-out окон
    if (viewMode !== 'main') {
        // 1. Сообщаем, что окно открыто
        updatePopoutStatus(viewMode, true);

        // 2. Сообщаем, что окно закрыто при выгрузке
        window.addEventListener('beforeunload', function () {
            updatePopoutStatus(viewMode, false);
        });

        // Слушаем изменения в localStorage
        window.addEventListener('storage', function (e) {
            // ...
        });
    } else {
        // Логика для main окна
        // При загрузке main окна можно сбросить статусы, если мы уверены, что это единственная сессия
        // Но лучше не трогать, чтобы не сбросить активные pop-out
    }
})();
