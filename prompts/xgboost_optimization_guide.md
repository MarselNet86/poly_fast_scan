# XGBoost Optimization Guide для Binary Options Prediction

## 📊 Анализ вашей задачи

### Целевая переменная
```
Target: down_ask_1_price - up_ask_1_price
- Положительное значение = DOWN побеждает
- Отрицательное значение = UP побеждает
```

### Характеристики данных (btc-updown-15m-1967869)
- **Размер выборки**: 12,628 наблюдений
- **Распределение целевой переменной**:
  - Mean: -0.535, Median: -0.610
  - Range: [-0.997, +0.290]
  - UP побеждает: 87.28% случаев
  - DOWN побеждает: 12.71% случаев

**⚠️ Критическая проблема**: Сильный дисбаланс классов (87% vs 13%)

---

## 🎯 Что такое XGBoost?

### Основные концепции

**XGBoost (eXtreme Gradient Boosting)** — алгоритм машинного обучения, основанный на ансамблях решающих деревьев.

#### Как это работает?

1. **Gradient Boosting**: Последовательное построение деревьев
   - Каждое новое дерево исправляет ошибки предыдущих
   - Обучение происходит на градиенте функции потерь

2. **Ансамбль деревьев**:
   ```
   Финальное предсказание = Сумма предсказаний всех деревьев
   prediction = tree1 + tree2 + tree3 + ... + treeN
   ```

3. **Регуляризация**: Предотвращает переобучение
   - L1 (Lasso): Уменьшает веса до нуля
   - L2 (Ridge): Уменьшает веса, но не до нуля

### Почему XGBoost популярен?

✅ **Преимущества**:
- Высокая точность на табличных данных
- Встроенная обработка пропусков
- Регуляризация из коробки
- Параллельные вычисления
- Хорошо работает с категориальными и числовыми данными
- Feature importance "из коробки"

⚠️ **Недостатки**:
- Может переобучиться при неправильных параметрах
- Требует тюнинга гиперпараметров
- Черный ящик (сложно интерпретировать)
- Медленнее на очень больших датасетах

---

## 🤖 Модели XGBoost: Что выбрать?

### Сравнение моделей

| Модель | Задача | Когда использовать | Подходит для вас? |
|--------|--------|-------------------|-------------------|
| **XGBRegressor** | Регрессия | Предсказание непрерывной величины | ✅ **ДА** (текущий выбор) |
| **XGBClassifier** | Классификация | Предсказание категории (UP/DOWN) | ✅ **ДА** (альтернатива) |
| **XGBRanker** | Ранжирование | Сортировка списков (поисковые системы) | ❌ Нет |
| **XGBRFRegressor** | Регрессия (RF) | Random Forest вместо boosting | ⚠️ Обычно хуже XGBRegressor |
| **XGBRFClassifier** | Классификация (RF) | Random Forest вместо boosting | ⚠️ Обычно хуже XGBClassifier |

### 🔍 Детальный анализ для вашей задачи

#### 1️⃣ **XGBRegressor** (текущий подход) — ⭐ Рекомендуется для SHAP-анализа

**Плюсы**:
- ✅ Предсказывает точную разницу цен
- ✅ Лучше для SHAP-анализа (показывает влияние на величину)
- ✅ Сохраняет информацию о "силе" победы

**Минусы**:
- ⚠️ Не оптимизирован для дисбаланса классов
- ⚠️ Может давать предсказания вне диапазона

**Когда использовать**:
- Вам важна **интерпретация** (какие фичи влияют и насколько)
- Нужно понять **величину** разницы, а не только победителя
- Для SHAP-анализа важности фичей

#### 2️⃣ **XGBClassifier** — ⭐ Рекомендуется для продакшена

**Плюсы**:
- ✅ Оптимизирован для дисбаланса классов (scale_pos_weight)
- ✅ Выдает вероятности (0-1)
- ✅ Метрики качества понятнее (accuracy, F1, ROC-AUC)

**Минусы**:
- ⚠️ Теряется информация о величине разницы
- ⚠️ SHAP показывает влияние на log-odds, а не на разницу

**Когда использовать**:
- Цель — **предсказать победителя** (UP или DOWN)
- Важна **точность классификации**
- Нужны **вероятности** для risk management

**Как преобразовать задачу**:
```python
# Вместо регрессии
y = df['down_ask_1_price'] - df['up_ask_1_price']

# Классификация
y = (df['down_ask_1_price'] > df['up_ask_1_price']).astype(int)
# 1 = DOWN победил, 0 = UP победил
```

#### 3️⃣ **XGBRFRegressor / XGBRFClassifier** — ❌ Не рекомендуется

Random Forest варианты XGBoost. Используют bagging вместо boosting.

**Почему не подходят**:
- Обычно дают худшее качество чем градиентный бустинг
- Теряется главное преимущество XGBoost — последовательное обучение
- Для Random Forest лучше использовать sklearn.RandomForestRegressor

---

## 🎯 Рекомендации по выбору модели

### ✅ Для вашей задачи: **Двухэтапный подход**

#### Этап 1: Анализ (XGBRegressor)
```python
# Для понимания важности фичей
model = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# SHAP покажет влияние на разницу цен
```

#### Этап 2: Предсказание (XGBClassifier)
```python
# Для реальной торговли
y_binary = (y > 0).astype(int)  # 1=DOWN, 0=UP

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    scale_pos_weight=87.28/12.71,  # Балансировка классов!
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# Получите вероятности для принятия решений
proba = model.predict_proba(X_test)
```

---

## 🔧 Байесовская оптимизация гиперпараметров

### Что это такое?

**Байесовская оптимизация** — умный способ поиска лучших гиперпараметров модели.

#### Как работает традиционный поиск (Grid Search)?

```python
# Перебирает ВСЕ комбинации — очень медленно!
for learning_rate in [0.01, 0.05, 0.1]:
    for max_depth in [3, 5, 7]:
        for n_estimators in [100, 200, 300]:
            # 3 * 3 * 3 = 27 моделей!
            train_model(learning_rate, max_depth, n_estimators)
```

#### Как работает Байесовская оптимизация?

1. **Строит вероятностную модель** (Gaussian Process)
   - Предсказывает, какие параметры дадут лучший результат

2. **Умно выбирает следующую точку**
   - Баланс между исследованием (exploration) и использованием (exploitation)

3. **Обучает меньше моделей**
   - Достигает хорошего результата за 30-50 итераций вместо 100+

### Визуальное объяснение

```
Grid Search:
├─ Точка 1 (случайная)
├─ Точка 2 (случайная)
├─ Точка 3 (случайная)
└─ ... (перебирает все)

Байесовская оптимизация:
├─ Точка 1 (случайная)
├─ Точка 2 (случайная) → обучаем модель предсказания качества
├─ Точка 3 (умная!) → предсказываем где искать
└─ Точка 4 (еще умнее!) → сужаем поиск
```

### Стоит ли использовать в вашей задаче?

#### ✅ **ДА, если**:
- У вас есть время (30+ минут на оптимизацию)
- Данных достаточно (>5000 строк) ✓ У вас 12,628
- Хотите выжать максимум из модели
- Планируете использовать модель в продакшене

#### ❌ **НЕТ, если**:
- Сначала нужна быстрая базовая модель
- Экспериментируете с разными подходами
- Данных мало (<1000 строк)

### 🎯 Рекомендация для вас:

**Используйте поэтапно**:

1. **Сначала**: Ручной тюнинг (1-2 часа)
   - Поймете какие параметры важны
   - Получите baseline модель

2. **Потом**: Байесовская оптимизация (если нужно)
   - Выжмете дополнительные 1-3% качества
   - Найдете неочевидные комбинации параметров

---

## 🔧 Ключевые гиперпараметры XGBoost

### Параметры контроля обучения

| Параметр | Что делает | Рекомендуемый диапазон | Ваше значение |
|----------|-----------|----------------------|--------------|
| `n_estimators` | Количество деревьев | 100-1000 | 100 ⚠️ Маловато |
| `learning_rate` | Скорость обучения | 0.01-0.3 | 0.05 ✅ Хорошо |
| `max_depth` | Глубина деревьев | 3-10 | 6 ✅ Норм |

### Параметры регуляризации

| Параметр | Что делает | Рекомендуемый диапазон | Ваше значение |
|----------|-----------|----------------------|--------------|
| `subsample` | % строк для дерева | 0.6-1.0 | ❌ Не задан (default=1.0) |
| `colsample_bytree` | % фичей для дерева | 0.6-1.0 | ❌ Не задан (default=1.0) |
| `reg_alpha` | L1 регуляризация | 0-10 | ❌ Не задан (default=0) |
| `reg_lambda` | L2 регуляризация | 0-10 | ❌ Не задан (default=1) |
| `min_child_weight` | Мин. сумма весов в листе | 1-10 | ❌ Не задан (default=1) |

### Параметры для дисбаланса (только XGBClassifier)

| Параметр | Что делает | Рекомендация |
|----------|-----------|-------------|
| `scale_pos_weight` | Вес редкого класса | `count(majority) / count(minority)` = 6.87 |

---

## 📋 Оптимизация вашего кода

### ❌ Текущие проблемы

```python
# services/shap_analysis.py
model = xgb.XGBRegressor(
    n_estimators=100,        # ⚠️ Мало деревьев
    max_depth=6,             # ✅ OK
    learning_rate=0.05,      # ✅ OK
    random_state=42,         # ✅ OK
    # ❌ НЕТ регуляризации!
)
```

### ✅ Улучшенная конфигурация

```python
# Базовая конфигурация для SHAP-анализа
model = xgb.XGBRegressor(
    # Основные параметры
    n_estimators=300,           # Больше деревьев = лучше качество
    max_depth=5,                # Немного меньше = меньше переобучение
    learning_rate=0.05,         # OK

    # Регуляризация
    subsample=0.8,              # Берем 80% строк для каждого дерева
    colsample_bytree=0.8,       # Берем 80% фичей для каждого дерева
    reg_alpha=0.1,              # L1 регуляризация
    reg_lambda=1.0,             # L2 регуляризация
    min_child_weight=3,         # Минимум 3 наблюдения в листе

    # Дополнительно
    random_state=42,
    n_jobs=-1,                  # Используем все CPU
    tree_method='hist',         # Быстрый метод для больших данных
)
```

---

## 🗑️ EXCLUDE_COLUMNS: Что исключать?

### Концепция: Data Leakage vs Predictive Power

#### ⚠️ Что ОБЯЗАТЕЛЬНО исключать

**1. Target leakage** — фичи, которые вычислены из целевой переменной:
```python
MUST_EXCLUDE = [
    # Прямые компоненты таргета
    'down_ask_1_price',  # Таргет = down_ask - up_ask
    'up_ask_1_price',

    # Временные метки (не предсказывают, только идентифицируют)
    'market_slug',
    'timestamp_ms',
    'timestamp_et',
]
```

**2. Future information** — данные, которых не будет на момент предсказания:
```python
# Например, если предсказываем за 5 минут до окончания:
'time_till_end',      # Будет известно
'seconds_till_end',   # Будет известно
```

#### 🤔 Что ВОЗМОЖНО исключать (для обнаружения скрытых паттернов)

**Фичи с очевидной корреляцией** — сильно связаны с таргетом, но скрывают другие паттерны:

```python
OPTIONAL_EXCLUDE = [
    # Microprice — взвешенная середина bid/ask
    'pm_up_microprice',      # Почти = up_ask_1_price
    'pm_down_microprice',    # Почти = down_ask_1_price

    # Все up_bid данные — сильно коррелируют с up_ask
    'up_bid_*_price',
    'up_bid_*_size',
    'pm_up_bid_depth5',
    'pm_up_bid_slope',
    'pm_up_bid_eatflow',

    # Все down_bid данные — сильно коррелируют с down_ask
    'down_bid_*_price',
    'down_bid_*_size',
    'pm_down_bid_depth5',
    'pm_down_bid_slope',
    'pm_down_bid_eatflow',
]
```

### 📊 Анализ текущих результатов

Ваши топ фичи (из `feature_importance.csv`):
```
1. binance_vwap_30s      (0.280) — ⭐ Внешняя цена BTC
2. binance_p_vwap_30s    (0.024) — ⭐ Процент отклонения от VWAP
3. pm_down_bid_slope     (0.007) — Наклон стакана DOWN bid
4. pm_up_ask_slope       (0.006) — Наклон стакана UP ask
5. binance_atr_30s       (0.004) — Волатильность BTC
```

**Вывод**: После исключения очевидных фичей (microprice, prices), модель нашла:
- ✅ **Binance метрики** — внешние факторы (VWAP, волатильность)
- ✅ **Производные orderbook метрики** — depth, slope, imbalance

### 🎯 Итоговая рекомендация по EXCLUDE_COLUMNS

#### Сценарий 1: Для SHAP-анализа (поиск паттернов)
```python
EXCLUDE_COLUMNS = [
    # Обязательно
    'market_slug', 'timestamp_ms', 'timestamp_et',
    'down_ask_1_price', 'up_ask_1_price',  # Компоненты таргета

    # Опционально (для поиска скрытых паттернов)
    'pm_up_microprice', 'pm_down_microprice',
    'up_bid_*', 'down_bid_*',   # Все bid цены/размеры
    'up_ask_*', 'down_ask_*',   # Все ask цены/размеры
    'pm_*_depth5',              # Прямые агрегаты orderbook
]

# Останутся только:
# - Binance метрики (цена, объем, волатильность)
# - Производные метрики (spread, imbalance, slope, eatflow)
# - Lag (задержка Oracle-Binance)
```

#### Сценарий 2: Для предсказательной модели (продакшен)
```python
EXCLUDE_COLUMNS = [
    # Только обязательные
    'market_slug', 'timestamp_ms', 'timestamp_et',
    'down_ask_1_price', 'up_ask_1_price',
    'time_till_end', 'seconds_till_end',  # Если предсказываем заранее
]

# Используем все доступные фичи для максимальной точности
```

---

## 🎯 Пошаговый план оптимизации

### Фаза 1: Базовый анализ (сейчас)
✅ Вы здесь — понимаете важность фичей

### Фаза 2: Улучшение модели (следующий шаг)

1. **Обновите параметры XGBRegressor**:
```python
model = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    min_child_weight=3,
    random_state=42,
    n_jobs=-1
)
```

2. **Добавьте метрики качества**:
```python
from sklearn.metrics import mean_absolute_error, r2_score

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MAE: {mae:.4f}")
print(f"R²: {r2:.4f}")
```

3. **Проверьте переобучение**:
```python
# Тренировочная ошибка
y_train_pred = model.predict(X_train)
train_mae = mean_absolute_error(y_train, y_train_pred)

# Если train_mae << test_mae → переобучение!
```

### Фаза 3: Альтернативный подход (опционально)

**Попробуйте XGBClassifier для сравнения**:

```python
# Преобразуйте в бинарную задачу
y_binary = (y > 0).astype(int)  # 1=DOWN, 0=UP

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    scale_pos_weight=6.87,  # 87.28% / 12.71%
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42
)

# Метрики
from sklearn.metrics import classification_report, roc_auc_score

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
```

### Фаза 4: Байесовская оптимизация (если нужно)

```python
from hyperopt import hp, fmin, tpe, Trials, STATUS_OK

def objective(params):
    model = xgb.XGBRegressor(
        n_estimators=int(params['n_estimators']),
        max_depth=int(params['max_depth']),
        learning_rate=params['learning_rate'],
        subsample=params['subsample'],
        colsample_bytree=params['colsample_bytree'],
        reg_alpha=params['reg_alpha'],
        reg_lambda=params['reg_lambda'],
        random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    return {'loss': mae, 'status': STATUS_OK}

space = {
    'n_estimators': hp.quniform('n_estimators', 100, 500, 50),
    'max_depth': hp.quniform('max_depth', 3, 10, 1),
    'learning_rate': hp.loguniform('learning_rate', -3, -0.7),  # 0.05-0.5
    'subsample': hp.uniform('subsample', 0.6, 1.0),
    'colsample_bytree': hp.uniform('colsample_bytree', 0.6, 1.0),
    'reg_alpha': hp.loguniform('reg_alpha', -3, 2),  # 0.05-10
    'reg_lambda': hp.loguniform('reg_lambda', -3, 2),
}

trials = Trials()
best = fmin(
    fn=objective,
    space=space,
    algo=tpe.suggest,  # Байесовская оптимизация
    max_evals=50,
    trials=trials
)
```

---

## 📚 Дополнительные ресурсы

### Документация
- [XGBoost Official Docs](https://xgboost.readthedocs.io/)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [Hyperopt (Bayesian Optimization)](http://hyperopt.github.io/hyperopt/)

### Статьи
- [XGBoost: A Scalable Tree Boosting System (оригинальная статья)](https://arxiv.org/abs/1603.02754)
- [Interpretable ML with SHAP](https://christophm.github.io/interpretable-ml-book/shap.html)

---

## 🎓 Ключевые выводы

1. **XGBRegressor** ✅ — текущий выбор правильный для SHAP-анализа важности фичей
2. **XGBClassifier** ⭐ — рассмотрите для продакшена (лучше работает с дисбалансом)
3. **Байесовская оптимизация** 🔧 — используйте после базовой настройки
4. **EXCLUDE_COLUMNS** 🗑️:
   - Обязательно: временные метки, компоненты таргета
   - Опционально: очевидные корреляции (microprice, bid/ask prices)
   - Оставьте: Binance метрики, производные orderbook метрики
5. **Добавьте регуляризацию** — subsample, colsample_bytree, reg_alpha/lambda

---

## 🚀 Следующие шаги

1. Обновите параметры модели (добавьте регуляризацию)
2. Добавьте метрики качества (MAE, R², classification metrics)
3. Сравните XGBRegressor vs XGBClassifier
4. Если нужно — запустите байесовскую оптимизацию
5. Анализируйте SHAP values для бизнес-инсайтов
