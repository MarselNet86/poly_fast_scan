# План поиска паттернов для торгового алгоритма Polymarket

## Цели

**Две стратегии:**
1. **Фаворит в финале** — ставка на лидера в последние 4 минуты (seconds_till_end < 240)
2. **Арбитраж** — ловить моменты когда ask_sum < 1.0

**Таймфрейм:** Мгновенный (1-10 тиков) — высокочастотные решения

**Срок MVP:** 2-3 недели

---

## Проблема

**Текущая ситуация:**
- 15 графиков × 223 файла = потенциально тысячи визуализаций для анализа
- 2.9 млн записей, 82 колонки данных
- Ручной анализ нереалистичен

**Два крайних подхода:**
- A) Ручной просмотр 15000 графиков — неэффективно
- B) Чистый ML без понимания данных — black box

**Решение: Гибридный подход** — умная визуализация + ML валидация

---

## Этап 1: Подготовка данных (1-2 дня)

### 1.1 Объединение данных
```python
# src/ml/data_preparation.py
import pandas as pd
import glob

def load_all_data(files_dir: str) -> pd.DataFrame:
    all_files = glob.glob(f"{files_dir}/btc-updown-15m-*.csv")
    dfs = [pd.read_csv(f) for f in all_files]
    df = pd.concat(dfs, ignore_index=True)
    return df.sort_values('timestamp_ms')
```

### 1.2 Создание target переменных

| Вариант | Описание | Тип задачи |
|---------|----------|------------|
| **A: Direction** | Цена UP идёт вверх/вниз через N тиков | Binary classification |
| **B: Return** | Величина изменения цены | Regression |
| **C: Arbitrage** | Появится ли ask_sum < 1.0 | Binary classification |
| **D: Action** | BUY_UP / BUY_DOWN / HOLD | Multi-class |

**Рекомендация:** Начать с варианта A (Direction), затем перейти к D (Action)

```python
def create_targets(df: pd.DataFrame, horizon: int = 10):
    # Direction (A)
    df['target_direction'] = (df['up_ask_1_price'].shift(-horizon) > df['up_ask_1_price']).astype(int)

    # Arbitrage (C)
    future_sum = df['up_ask_1_price'].shift(-horizon) + df['down_ask_1_price'].shift(-horizon)
    df['target_arbitrage'] = (future_sum < 1.0).astype(int)

    return df
```

---

## Этап 2: Умная визуализация (2-3 дня)

### 2.1 Автоматический поиск "интересных" событий

Вместо просмотра всех графиков — фокус на экстремумах:

```python
def find_interesting_events(df: pd.DataFrame) -> dict:
    return {
        'arbitrage': df[df['up_ask_1_price'] + df['down_ask_1_price'] < 0.99].index,
        'high_lag': df[abs(df['lag']) > df['lag'].std() * 2].index,
        'volume_spike': df[df['binance_volume_spike'] > 2.0].index,
        'high_imbalance': df[abs(df['pm_up_imbalance']) > 0.25].index,
        'spread_anomaly': df[df['pm_up_spread'] > df['pm_up_spread'].quantile(0.95)].index
    }
```

### 2.2 Workflow визуального анализа

1. **Автоматически** найти все "интересные" моменты
2. **Сгруппировать** по типу события
3. **Просмотреть** 20-50 примеров каждого типа (вместо 15000)
4. **Записать** гипотезы о паттернах
5. **Валидировать** на полных данных

### 2.3 Добавить в дашборд

- Кнопка "Jump to Next Event" для быстрой навигации
- Фильтр по типу события
- Сохранение заметок к интересным моментам

---

## Этап 3: Паттерны для поиска

### СТРАТЕГИЯ A: Фаворит в финале (последние 4 минуты)

#### Паттерн A1: Clear Favorite
```
Условие: seconds_till_end < 240 И microprice > 0.7 (или < 0.3)
Гипотеза: Явный фаворит продолжает укрепляться к финишу
Метрика: pm_up_microprice > 0.7 → UP выигрывает
Действие: Ставить на фаворита (UP или DOWN)
```

#### Паттерн A2: Momentum Confirmation
```
Условие: seconds_till_end < 240 И binance_ret5s однонаправленный с фаворитом
Гипотеза: BTC движется в сторону фаворита — подтверждение
Действие: Усилить ставку на фаворита
```

#### Паттерн A3: Final Sprint
```
Условие: seconds_till_end < 60 И imbalance резко растёт
Гипотеза: Крупные игроки заходят в последнюю минуту
Действие: Следовать за imbalance
```

#### Паттерн A4: Lag Advantage
```
Условие: seconds_till_end < 120 И |lag| > threshold
Гипотеза: Oracle отстаёт — можно предсказать исход по Binance
Действие: Использовать lag для опережения
```

### СТРАТЕГИЯ B: Арбитраж

#### Паттерн B1: Classic Arbitrage
```
Условие: up_ask_1_price + down_ask_1_price < 1.0
Гипотеза: Гарантированная прибыль (купить оба = получить 1.0)
Действие: Купить UP и DOWN одновременно
Profit: 1.0 - ask_sum
```

#### Паттерн B2: Spread Arbitrage
```
Условие: ask_sum < 1.0 И pm_up_spread + pm_down_spread < 0.02
Гипотеза: Узкий спред = низкий slippage
Действие: Арбитраж с уверенностью
```

#### Паттерн B3: Volume Arbitrage
```
Условие: ask_sum < 1.0 И depth5 достаточная
Гипотеза: Есть ликвидность для исполнения
Действие: Проверить pm_up_ask_depth5 + pm_down_ask_depth5
```

### КОМБИНИРОВАННЫЕ ПАТТЕРНЫ

#### Паттерн C1: Lag Reversal
```
Условие: |lag| > threshold И lag меняет знак
Гипотеза: Цена Polymarket догоняет Binance
Действие: Покупать UP если lag > 0, DOWN если lag < 0
```

#### Паттерн C2: Imbalance Divergence
```
Условие: pm_up_imbalance и pm_down_imbalance расходятся
Гипотеза: Рынок предсказывает движение
Действие: Следовать за стороной с большим imbalance
```

#### Паттерн C3: Volume Confirmation
```
Условие: binance_volume_spike > 2.0 И ret1s однонаправленный
Гипотеза: Большой объём подтверждает движение
Действие: Следовать за направлением ret1s
```

---

## Этап 4: ML валидация (3-5 дней)

### 4.1 Feature Engineering

```python
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    # === БЫСТРЫЕ FEATURES (1-10 тиков latency) ===

    # Лаговые features (только 1-5 тиков для скорости)
    for col in ['lag', 'pm_up_imbalance', 'binance_ret1s_x100']:
        df[f'{col}_lag1'] = df[col].shift(1)
        df[f'{col}_lag3'] = df[col].shift(3)
        df[f'{col}_lag5'] = df[col].shift(5)

    # Rolling statistics (короткие окна)
    df['lag_ma5'] = df['lag'].rolling(5).mean()
    df['lag_std5'] = df['lag'].rolling(5).std()
    df['imbalance_diff'] = df['pm_up_imbalance'] - df['pm_down_imbalance']

    # === АРБИТРАЖНЫЕ FEATURES ===
    df['ask_sum'] = df['up_ask_1_price'] + df['down_ask_1_price']
    df['bid_sum'] = df['up_bid_1_price'] + df['down_bid_1_price']
    df['arb_opportunity'] = (df['ask_sum'] < 1.0).astype(int)
    df['arb_profit'] = 1.0 - df['ask_sum']  # потенциальная прибыль

    # === ФАВОРИТ FEATURES ===
    df['favorite'] = (df['pm_up_microprice'] > 0.5).astype(int)  # 1=UP, 0=DOWN
    df['favorite_strength'] = abs(df['pm_up_microprice'] - 0.5) * 2  # 0-1 сила фаворита
    df['favorite_momentum'] = df['pm_up_microprice'] - df['pm_up_microprice'].shift(5)

    # === ВРЕМЕННЫЕ FEATURES (критично для стратегии фаворита) ===
    df['time_remaining_pct'] = df['seconds_till_end'] / 900
    df['is_final_4min'] = (df['seconds_till_end'] < 240).astype(int)
    df['is_final_2min'] = (df['seconds_till_end'] < 120).astype(int)
    df['is_final_1min'] = (df['seconds_till_end'] < 60).astype(int)

    # === КОМБИНИРОВАННЫЕ СИГНАЛЫ ===
    # Фаворит в финале
    df['favorite_final_signal'] = df['is_final_4min'] * df['favorite_strength']

    # Lag advantage в финале
    df['lag_final_signal'] = df['is_final_2min'] * abs(df['lag'])

    return df
```

### 4.2 Модели

| Задача | Модель | Библиотека |
|--------|--------|------------|
| Направление цены | XGBoost, LightGBM | xgboost, lightgbm |
| Режимы рынка | K-Means, DBSCAN | sklearn |
| Аномалии | Isolation Forest | sklearn |
| Feature importance | SHAP | shap |

### 4.3 Валидация

```python
from sklearn.model_selection import TimeSeriesSplit

# ВАЖНО: Временные ряды - нельзя random split!
tscv = TimeSeriesSplit(n_splits=5)

for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    # ... train and evaluate
```

---

## Этап 5: Торговый алгоритм (5-7 дней)

### 5.1 Структура

```python
@dataclass
class Signal:
    direction: Literal['UP', 'DOWN', 'BOTH', 'NONE']
    confidence: float
    signal_type: Literal['momentum', 'arbitrage', 'reversal']
    entry_price: float
    target_price: float
    stop_loss: float

class TradingStrategy:
    def generate_signal(self, current_state: dict) -> Optional[Signal]:
        # 1. Проверить арбитраж (приоритет)
        # 2. ML предсказание направления
        # 3. Проверить уверенность модели
        pass
```

### 5.2 Backtesting

```python
class Backtester:
    def run(self) -> dict:
        # Прогнать стратегию по историческим данным
        pass

    def calculate_metrics(self) -> dict:
        return {
            'total_trades': ...,
            'win_rate': ...,
            'total_pnl': ...,
            'sharpe_ratio': ...,
            'max_drawdown': ...
        }
```

---

## Новые зависимости

```
# Добавить в requirements.txt
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
shap>=0.43.0
optuna>=3.4.0      # Hyperparameter tuning
```

---

## Структура новых файлов

```
src/
└── ml/
    ├── __init__.py
    ├── data_preparation.py   # Загрузка и объединение данных
    ├── features.py           # Feature engineering
    ├── models.py             # ML модели
    ├── eda.py                # Exploratory analysis
    ├── backtest.py           # Бэктестинг
    └── experiments/
        ├── 01_eda.ipynb
        ├── 02_features.ipynb
        ├── 03_models.ipynb
        └── 04_backtest.ipynb
```

---

## Timeline (2-3 недели MVP)

| Дни | Фокус | Результат |
|-----|-------|-----------|
| 1-3 | Data + EDA | Unified dataset + targets + базовая статистика |
| 4-6 | Smart Visualization | Поиск событий + просмотр 50-100 примеров + гипотезы |
| 7-10 | Feature Engineering | Быстрые features (1-10 тиков latency) |
| 11-14 | ML Models | XGBoost/LightGBM + SHAP analysis |
| 15-18 | Backtesting | Тестирование обеих стратегий |
| 19-21 | Integration | Интеграция в дашборд + real-time signals |

### Приоритеты MVP

**Неделя 1: Быстрый старт**
- [ ] Объединить данные
- [ ] Найти все арбитражные события (ask_sum < 1.0)
- [ ] Проанализировать паттерн "фаворит в последние 4 мин"
- [ ] Baseline: простые правила без ML

**Неделя 2: ML валидация**
- [ ] Feature engineering
- [ ] Обучить XGBoost для обеих стратегий
- [ ] Проверить accuracy на test set

**Неделя 3: Backtest + Integration**
- [ ] Backtesting framework
- [ ] Метрики: win rate, profit, drawdown
- [ ] Интеграция сигналов в дашборд

---

## Ключевые метрики успеха

1. **Accuracy направления** > 55% (лучше random)
2. **Win rate** в backtesting > 52%
3. **Sharpe ratio** > 1.0
4. **Max drawdown** < 20%
5. **Количество найденных арбитражей** и их профит
