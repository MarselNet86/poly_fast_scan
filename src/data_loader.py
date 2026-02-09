"""
Data Loader Module
Загрузка и обработка CSV данных стакана ордеров
"""

import os
import pandas as pd
import numpy as np

# Путь к директории с файлами
FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'files')


def get_csv_files():
    """Получить список CSV файлов в директории"""
    files = [f for f in os.listdir(FILES_DIR) if f.endswith('.csv')]
    return sorted(files)


def load_data(filename):
    """Загрузить данные из CSV файла"""
    filepath = os.path.join(FILES_DIR, filename)
    df = pd.read_csv(filepath)
    return df


def get_orderbook_data(row):
    """
    Извлечь данные стакана ордеров из строки DataFrame

    Returns:
        dict: Словарь с данными UP и DOWN стаканов
    """
    data = {
        'up': {
            'bid_prices': [row.get(f'up_bid_{i}_price', np.nan) for i in range(1, 6)],
            'bid_sizes': [row.get(f'up_bid_{i}_size', np.nan) for i in range(1, 6)],
            'ask_prices': [row.get(f'up_ask_{i}_price', np.nan) for i in range(1, 6)],
            'ask_sizes': [row.get(f'up_ask_{i}_size', np.nan) for i in range(1, 6)],
        },
        'down': {
            'bid_prices': [row.get(f'down_bid_{i}_price', np.nan) for i in range(1, 6)],
            'bid_sizes': [row.get(f'down_bid_{i}_size', np.nan) for i in range(1, 6)],
            'ask_prices': [row.get(f'down_ask_{i}_price', np.nan) for i in range(1, 6)],
            'ask_sizes': [row.get(f'down_ask_{i}_size', np.nan) for i in range(1, 6)],
        },
        'timestamp': row.get('timestamp_et', row.get('timestamp_ms', 'N/A'))
    }
    return data


def calculate_anomaly_threshold(sizes):
    """
    Вычислить порог аномалии (>2x среднего размера)

    Args:
        sizes: Список размеров ордеров

    Returns:
        float: Пороговое значение для определения аномалии
    """
    valid_sizes = [s for s in sizes if pd.notna(s) and s > 0]
    if valid_sizes:
        return np.mean(valid_sizes) * 2
    return float('inf')


def calculate_pressure(bid_sizes, ask_sizes):
    """
    Вычислить давление покупателей/продавцов

    Args:
        bid_sizes: Размеры бидов
        ask_sizes: Размеры асков

    Returns:
        tuple: (тип давления, сумма бидов, сумма асков)
    """
    bid_total = sum([s for s in bid_sizes if pd.notna(s)])
    ask_total = sum([s for s in ask_sizes if pd.notna(s)])
    pressure = "BUYERS" if bid_total > ask_total else "SELLERS"
    return pressure, bid_total, ask_total


def get_file_info(df, filename):
    """
    Получить информацию о файле

    Args:
        df: DataFrame с данными
        filename: Имя файла

    Returns:
        dict: Словарь с информацией о файле
    """
    info = {
        'filename': filename,
        'rows': len(df),
        'columns': len(df.columns),
        'time_start': df['timestamp_et'].iloc[0] if 'timestamp_et' in df.columns else 'N/A',
        'time_end': df['timestamp_et'].iloc[-1] if 'timestamp_et' in df.columns else 'N/A',
    }
    return info
