# План: Скрипт SHAP-анализа важности метрик

## Цель
Создать скрипт для анализа важности метрик в данных бинарных опционов с использованием SHAP.

## Целевая переменная
- **Логика**: сравниваем последние значения `down_ask_1_price` и `up_ask_1_price`
- Если `down_ask_1_price > up_ask_1_price` → `target = 0` (DOWN победил)
- Иначе → `target = 1` (UP победил)

## Колонки для анализа

### Исключаемые колонки (не участвуют в анализе):
- `market_slug`
- `timestamp_ms`
- `timestamp_et`
- `time_till_end`
- `seconds_till_end`

### Фичи для SHAP-анализа (76 колонок):

**Ценовые данные Binance:**
- `oracle_btc_price`
- `binance_btc_price`
- `lag`

**Доходность:**
- `binance_ret1s_x100`
- `binance_ret5s_x100`

**Объём:**
- `binance_volume_1s`
- `binance_volume_5s`
- `binance_volma_30s`
- `binance_volume_spike`

**Волатильность:**
- `binance_atr_5s`
- `binance_atr_30s`
- `binance_rvol_30s`

**VWAP:**
- `binance_vwap_30s`
- `binance_p_vwap_5s`
- `binance_p_vwap_30s`

**Latency direction:**
- `lat_dir_raw_x1000`
- `lat_dir_norm_x1000`

**UP Order Book (bid):**
- `up_bid_1_price`, `up_bid_1_size`
- `up_bid_2_price`, `up_bid_2_size`
- `up_bid_3_price`, `up_bid_3_size`
- `up_bid_4_price`, `up_bid_4_size`
- `up_bid_5_price`, `up_bid_5_size`

**UP Order Book (ask):**
- `up_ask_1_price`, `up_ask_1_size`
- `up_ask_2_price`, `up_ask_2_size`
- `up_ask_3_price`, `up_ask_3_size`
- `up_ask_4_price`, `up_ask_4_size`
- `up_ask_5_price`, `up_ask_5_size`

**DOWN Order Book (bid):**
- `down_bid_1_price`, `down_bid_1_size`
- `down_bid_2_price`, `down_bid_2_size`
- `down_bid_3_price`, `down_bid_3_size`
- `down_bid_4_price`, `down_bid_4_size`
- `down_bid_5_price`, `down_bid_5_size`

**DOWN Order Book (ask):**
- `down_ask_1_price`, `down_ask_1_size`
- `down_ask_2_price`, `down_ask_2_size`
- `down_ask_3_price`, `down_ask_3_size`
- `down_ask_4_price`, `down_ask_4_size`
- `down_ask_5_price`, `down_ask_5_size`

**Polymarket агрегаты UP:**
- `pm_up_bid_depth5`
- `pm_up_ask_depth5`
- `pm_up_total_depth5`
- `pm_up_spread`
- `pm_up_imbalance`
- `pm_up_microprice`
- `pm_up_bid_slope`
- `pm_up_ask_slope`
- `pm_up_bid_eatflow`
- `pm_up_ask_eatflow`

**Polymarket агрегаты DOWN:**
- `pm_down_bid_depth5`
- `pm_down_ask_depth5`
- `pm_down_total_depth5`
- `pm_down_spread`
- `pm_down_imbalance`
- `pm_down_microprice`
- `pm_down_bid_slope`
- `pm_down_ask_slope`
- `pm_down_bid_eatflow`
- `pm_down_ask_eatflow`

## Структура скрипта

### Файл: `src/shap_analysis.py`

```python
1. Импорты (pandas, shap, xgboost, sklearn, matplotlib, argparse, pathlib)

2. EXCLUDE_COLUMNS = ['market_slug', 'timestamp_ms', 'timestamp_et',
                       'time_till_end', 'seconds_till_end']

3. Функция load_and_prepare_data(file_path):
   - Загрузка CSV
   - Получение последней строки для определения target
   - target = 0 если down_ask_1_price > up_ask_1_price, иначе 1
   - Выбор всех колонок кроме EXCLUDE_COLUMNS
   - Обработка NaN (fillna(0) или dropna)
   - Возврат X, y (y - одно значение, реплицируется на все строки)

4. Функция train_model(X, y):
   - Разбиение на train/test (80/20)
   - Обучение XGBClassifier
   - Возврат модели и тестовых данных

5. Функция compute_shap(model, X_test):
   - TreeExplainer для XGBoost
   - Вычисление SHAP values
   - Возврат shap_values

6. Функция save_results(shap_values, X_test, output_dir, slug):
   - Создание папки results/{slug}/ (если нет - создать)
   - shap.plots.bar → сохранение shap_bar.png
   - Сохранение feature_importance.csv с усреднёнными SHAP

7. Функция extract_slug(file_path):
   - Извлечение slug из имени файла (btc-updown-15m-1967869)

8. main():
   - argparse: --file (путь к CSV файлу)
   - Выполнение анализа
   - Вывод пути к результатам
```

## Зависимости
```
shap
xgboost
pandas
scikit-learn
matplotlib
```

## Структура результатов
```
results/
└── btc-updown-15m-1967869/
    ├── shap_bar.png          # График shap.plots.bar (усреднённые SHAP)
    └── feature_importance.csv # Таблица: feature, mean_shap_value
```

## Использование
```bash
python src/shap_analysis.py --file files/btc-updown-15m-1967869.csv
```

## Верификация
1. Запустить скрипт на тестовом файле
2. Проверить создание папки `results/{slug}/`
3. Проверить корректность `shap_bar.png` (график с барами)
4. Проверить `feature_importance.csv` (колонки: feature, mean_shap_value)
