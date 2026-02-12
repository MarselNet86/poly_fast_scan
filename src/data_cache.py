"""
Minimal server-side cache - only DataFrames, no trace caching
Упрощенная версия без LRU кеша для clientside playback
"""

import pandas as pd
from typing import Dict
from .data_loader import get_orderbook_data, calculate_anomaly_threshold, calculate_pressure
from .config import BAR_SCALE_COEFF


class SimpleDataFrameCache:
    """Cache loaded DataFrames only"""

    def __init__(self):
        self.df_cache: Dict[str, pd.DataFrame] = {}

    def get_df(self, filename: str) -> pd.DataFrame:
        """Get or load DataFrame"""
        if filename not in self.df_cache:
            from .data_loader import load_data
            self.df_cache[filename] = load_data(filename)
        return self.df_cache[filename]

    def compute_trace_data(self, filename: str, row_idx: int) -> Dict:
        """Compute trace data on-the-fly, no caching"""
        df = self.get_df(filename)
        return extract_trace_data(df, row_idx)


def extract_trace_data(df: pd.DataFrame, row_idx: int) -> Dict:
    """
    Extract trace data from DataFrame row
    Moved from buffer.py _extract_trace_data
    """
    row = df.iloc[row_idx]
    ob_data = get_orderbook_data(row)

    all_sizes = (
        ob_data['up']['bid_sizes'] + ob_data['up']['ask_sizes'] +
        ob_data['down']['bid_sizes'] + ob_data['down']['ask_sizes']
    )
    anomaly_threshold = calculate_anomaly_threshold(all_sizes)

    up_pressure, up_bid_total, up_ask_total = calculate_pressure(
        ob_data['up']['bid_sizes'], ob_data['up']['ask_sizes']
    )
    down_pressure, down_bid_total, down_ask_total = calculate_pressure(
        ob_data['down']['bid_sizes'], ob_data['down']['ask_sizes']
    )

    def get_colors(sizes, base_color, anomaly_color):
        colors = []
        for s in sizes:
            if pd.notna(s) and s > anomaly_threshold:
                colors.append(anomaly_color)
            else:
                colors.append(base_color)
        return colors

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
        'up_pressure': up_pressure,
        'up_bid_total': up_bid_total,
        'up_ask_total': up_ask_total,
        'down_pressure': down_pressure,
        'down_bid_total': down_bid_total,
        'down_ask_total': down_ask_total,
        'up_ask_price_x': [row_idx] if pd.notna(row.get('up_ask_1_price')) else [],
        'up_ask_price_y': [float(row.get('up_ask_1_price'))] if pd.notna(row.get('up_ask_1_price')) else [],
        'down_ask_price_x': [row_idx] if pd.notna(row.get('down_ask_1_price')) else [],
        'down_ask_price_y': [float(row.get('down_ask_1_price'))] if pd.notna(row.get('down_ask_1_price')) else [],
        'binance_price_x': [row_idx] if pd.notna(row.get('binance_btc_price')) else [],
        'binance_price_y': [float(row.get('binance_btc_price'))] if pd.notna(row.get('binance_btc_price')) else [],
        'oracle_price_x': [row_idx] if pd.notna(row.get('oracle_btc_price')) else [],
        'oracle_price_y': [float(row.get('oracle_btc_price'))] if pd.notna(row.get('oracle_btc_price')) else [],
        'lag_x': [row_idx] if pd.notna(row.get('lag')) else [],
        'lag_y': [float(row.get('lag'))] if pd.notna(row.get('lag')) else []
    }
    return trace_data


# Global instance
_cache = None


def get_data_cache():
    """Get global cache instance"""
    global _cache
    if _cache is None:
        _cache = SimpleDataFrameCache()
    return _cache
