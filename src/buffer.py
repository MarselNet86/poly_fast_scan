"""
Efficient Buffer System for Orderbook Playback
Оптимизированная система буферизации для плавного воспроизведения
"""

from collections import OrderedDict
from typing import Dict, Any, Optional
import sys
import pandas as pd
from .config import BAR_SCALE_COEFF


class LRUCache:
    """
    LRU кеш с ограничением по количеству элементов.
    Легковесный, без внешних зависимостей.
    """

    def __init__(self, maxsize: int = 64):
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()

    def get(self, key) -> Optional[Any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)  # Удаляем oldest
        self.cache[key] = value

    def clear(self) -> None:
        self.cache.clear()

    def __len__(self) -> int:
        return len(self.cache)

    def __contains__(self, key) -> bool:
        return key in self.cache

    def get_memory_usage(self) -> int:
        """Приблизительный размер в байтах"""
        return sum(sys.getsizeof(v) for v in self.cache.values())


class TraceDataCache:
    """
    Кеш для данных traces (не для полных figures).
    Хранит легковесные словари с данными для каждого row.
    """

    def __init__(self, maxsize: int = 128):
        self.cache = LRUCache(maxsize)
        self.df_cache: Dict[str, Any] = {}

    def get_df(self, filename: str):
        """Получить DataFrame из кеша"""
        if filename not in self.df_cache:
            from .data_loader import load_data
            self.df_cache[filename] = load_data(filename)
        return self.df_cache[filename]

    def get_trace_data(self, filename: str, row_idx: int) -> Optional[Dict]:
        """Получить данные traces для строки"""
        key = (filename, row_idx)
        return self.cache.get(key)

    def compute_trace_data(self, filename: str, row_idx: int) -> Dict:
        """
        Вычислить и закешировать данные traces для строки.
        Возвращает легковесный dict вместо полной figure.
        """
        key = (filename, row_idx)

        cached = self.cache.get(key)
        if cached is not None:
            return cached

        df = self.get_df(filename)
        data = self._extract_trace_data(df, row_idx)
        self.cache.put(key, data)
        return data

    def _extract_trace_data(self, df, row_idx: int) -> Dict:
        """
        Извлечь только данные для traces (без layout).
        Это намного легче чем полная figure.
        """
        from .data_loader import get_orderbook_data, calculate_anomaly_threshold, calculate_pressure

        row = df.iloc[row_idx]
        ob_data = get_orderbook_data(row)

        # Вычисляем пороги аномалий
        all_sizes = (
            ob_data['up']['bid_sizes'] + ob_data['up']['ask_sizes'] +
            ob_data['down']['bid_sizes'] + ob_data['down']['ask_sizes']
        )
        anomaly_threshold = calculate_anomaly_threshold(all_sizes)

        # Вычисляем давление
        up_pressure, up_bid_total, up_ask_total = calculate_pressure(
            ob_data['up']['bid_sizes'], ob_data['up']['ask_sizes']
        )
        down_pressure, down_bid_total, down_ask_total = calculate_pressure(
            ob_data['down']['bid_sizes'], ob_data['down']['ask_sizes']
        )

        # Функция для определения цветов
        def get_colors(sizes, base_color, anomaly_color):
            colors = []
            for s in sizes:
                if pd.notna(s) and s > anomaly_threshold:
                    colors.append(anomaly_color)
                else:
                    colors.append(base_color)
            return colors

        # Данные для orderbook bars
        trace_data = {
            'up_bids': {
                'y': [f"{p:.2f}" if pd.notna(p) else "N/A" for p in ob_data['up']['bid_prices']],
                'x': [-abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in ob_data['up']['bid_sizes']],
                'text': [f"${s:,.0f}" if pd.notna(s) else "" for s in ob_data['up']['bid_sizes']],
                'colors': get_colors(ob_data['up']['bid_sizes'], 'rgba(0, 200, 83, 0.7)', 'rgba(0, 255, 100, 1)')
            },
            'up_asks': {
                'y': [f"{p:.2f}" if pd.notna(p) else "N/A" for p in ob_data['up']['ask_prices']],
                'x': [abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in ob_data['up']['ask_sizes']],
                'text': [f"${s:,.0f}" if pd.notna(s) else "" for s in ob_data['up']['ask_sizes']],
                'colors': get_colors(ob_data['up']['ask_sizes'], 'rgba(244, 67, 54, 0.7)', 'rgba(255, 100, 100, 1)')
            },
            'down_bids': {
                'y': [f"{p:.2f}" if pd.notna(p) else "N/A" for p in ob_data['down']['bid_prices']],
                'x': [-abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in ob_data['down']['bid_sizes']],
                'text': [f"${s:,.0f}" if pd.notna(s) else "" for s in ob_data['down']['bid_sizes']],
                'colors': get_colors(ob_data['down']['bid_sizes'], 'rgba(0, 200, 83, 0.7)', 'rgba(0, 255, 100, 1)')
            },
            'down_asks': {
                'y': [f"{p:.2f}" if pd.notna(p) else "N/A" for p in ob_data['down']['ask_prices']],
                'x': [abs(s) * BAR_SCALE_COEFF if pd.notna(s) else 0 for s in ob_data['down']['ask_sizes']],
                'text': [f"${s:,.0f}" if pd.notna(s) else "" for s in ob_data['down']['ask_sizes']],
                'colors': get_colors(ob_data['down']['ask_sizes'], 'rgba(244, 67, 54, 0.7)', 'rgba(255, 100, 100, 1)')
            },
            'timestamp': ob_data['timestamp'],
            'row_idx': row_idx,
            # Метрики давления для заголовка
            'up_pressure': up_pressure,
            'up_bid_total': up_bid_total,
            'up_ask_total': up_ask_total,
            'down_pressure': down_pressure,
            'down_bid_total': down_bid_total,
            'down_ask_total': down_ask_total,
            # Позиция маркеров на price chart
            'binance_price_x': [row_idx] if pd.notna(row.get('binance_btc_price')) else [],
            'binance_price_y': [float(row.get('binance_btc_price'))] if pd.notna(row.get('binance_btc_price')) else [],
            'oracle_price_x': [row_idx] if pd.notna(row.get('oracle_btc_price')) else [],
            'oracle_price_y': [float(row.get('oracle_btc_price'))] if pd.notna(row.get('oracle_btc_price')) else [],
            # Позиция маркера на lag chart
            'lag_x': [row_idx] if pd.notna(row.get('lag')) else [],
            'lag_y': [float(row.get('lag'))] if pd.notna(row.get('lag')) else []
        }
        return trace_data

    def prebuffer(self, filename: str, start_row: int, count: int = 30) -> int:
        """
        Предзагрузить данные для следующих count строк.
        Возвращает количество новых записей.
        """
        df = self.get_df(filename)
        max_row = len(df) - 1
        new_count = 0

        for i in range(count):
            row = start_row + i
            if row > max_row:
                break

            key = (filename, row)
            if key not in self.cache:
                self.compute_trace_data(filename, row)
                new_count += 1

        return new_count

    def get_stats(self, filename: str = None, current_row: int = 0) -> Dict:
        """Статистика кеша"""
        total = len(self.cache)
        ahead = 0
        if filename:
            ahead = sum(1 for k in self.cache.cache if k[0] == filename and k[1] >= current_row)

        return {
            'cached_frames': total,
            'ahead': ahead,
            'memory_kb': self.cache.get_memory_usage() / 1024,
            'maxsize': self.cache.maxsize
        }

    def set_maxsize(self, maxsize: int) -> None:
        """Изменить максимальный размер кеша"""
        self.cache.maxsize = maxsize
        # Очистить лишние элементы если нужно
        while len(self.cache) > maxsize:
            self.cache.cache.popitem(last=False)


# Глобальный экземпляр кеша
_trace_cache: Optional[TraceDataCache] = None


def get_trace_cache(maxsize: int = 128) -> TraceDataCache:
    """Получить глобальный кеш"""
    global _trace_cache
    if _trace_cache is None:
        _trace_cache = TraceDataCache(maxsize)
    return _trace_cache


def set_cache_size(maxsize: int) -> None:
    """Установить размер кеша"""
    cache = get_trace_cache()
    cache.set_maxsize(maxsize)
