# Fast Research Review: Торговля в последние 4 минуты

## Введение

Этот документ определяет **приоритетные метрики и графики** для алгоритмической торговли в фазе "Развязка" (последние 4 минуты = `seconds_till_end` от 240 до 0) на 15-минутных рынках Polymarket UP/DOWN.

**Почему именно последние 4 минуты?**
- Цены контрактов сходятся к 0 или 1 (определённость исхода растёт)
- Оракул уже активен (в отличие от начала рынка)
- Меньше времени = меньше неопределённости = более предсказуемые движения
- Но: спреды расширяются, ликвидность падает

---

## Критические метрики (Tier 1 - ОБЯЗАТЕЛЬНЫЕ)

### 1. Oracle vs Binance Price + Lag

**Почему это #1:**
> Именно цена **оракула Chainlink** определяет исход рынка (UP/DOWN). Если Binance двинулся, а оракул ещё нет — это **арбитражное окно**.

**Переменные:**
- `binance_btc_price` - текущая цена Binance (опережающий индикатор)
- `oracle_btc_price` - цена оракула (определяет исход)
- `lag` = oracle - binance (разница)

**Торговый сигнал:**
```
Если Binance падает, а Oracle ещё не обновился:
  → lag > 0 (Oracle выше Binance)
  → Окно для покупки DOWN

Если Binance растёт, а Oracle отстаёт:
  → lag < 0 (Oracle ниже Binance)
  → Окно для покупки UP
```

**Реализация в Dash + Plotly:**
```python
# График 1: Двухлинейный график цен
fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])

# Основной график: Binance (оранжевый) + Oracle (синий)
fig.add_trace(go.Scatter(x=time, y=binance_price, name='Binance', line=dict(color='#FF6B00')), row=1, col=1)
fig.add_trace(go.Scatter(x=time, y=oracle_price, name='Oracle', line=dict(color='#2196F3')), row=1, col=1)

# Strike price (горизонтальная линия - первая цена оракула)
fig.add_hline(y=strike_price, line_dash="dash", line_color="white", row=1, col=1)

# Subplot: Lag (зелёный если oracle > binance, красный если binance > oracle)
fig.add_trace(go.Scatter(x=time, y=lag_positive, fill='tozeroy', fillcolor='rgba(76,175,80,0.5)'), row=2, col=1)
fig.add_trace(go.Scatter(x=time, y=lag_negative, fill='tozeroy', fillcolor='rgba(244,67,54,0.5)'), row=2, col=1)
```

---

### 2. Spread (Спред стакана)

**Почему это критично для последних 4 минут:**
> Спред **расширяется к концу** 15-минутного периода. Широкий спред = высокая стоимость входа/выхода.

**Переменные:**
- `pm_up_spread` = up_ask_1_price - up_bid_1_price
- `pm_down_spread` = down_ask_1_price - down_bid_1_price

**Пороги для алгоритма:**
| Spread | Интерпретация | Действие |
|--------|---------------|----------|
| < 0.02 | Ликвидный рынок | Market orders OK |
| 0.02-0.05 | Нормально | Limit orders предпочтительнее |
| 0.05-0.10 | Низкая ликвидность | Только limit orders |
| > 0.10 | **КРИТИЧНО** | **НЕ ВХОДИТЬ** |

**Реализация:**
```python
# Два горизонтальных бара показывающих спред UP и DOWN
fig = go.Figure()

# UP Spread
fig.add_trace(go.Bar(
    y=['UP'], x=[up_spread],
    orientation='h',
    marker_color='green' if up_spread < 0.05 else 'orange' if up_spread < 0.10 else 'red'
))

# DOWN Spread
fig.add_trace(go.Bar(
    y=['DOWN'], x=[down_spread],
    orientation='h',
    marker_color='green' if down_spread < 0.05 else 'orange' if down_spread < 0.10 else 'red'
))

# Пороговые линии
fig.add_vline(x=0.02, line_dash="dash", annotation_text="OK")
fig.add_vline(x=0.05, line_dash="dash", annotation_text="Warning")
fig.add_vline(x=0.10, line_dash="dash", line_color="red", annotation_text="STOP")
```

---

### 3. Imbalance (Дисбаланс стакана)

**Почему это важно:**
> Imbalance — **опережающий индикатор** движения цены. Показывает куда давит рынок ДО того, как цена двинется.

**Формула:**
```python
imbalance = (sum_bid_size - sum_ask_size) / (sum_bid_size + sum_ask_size)
# Диапазон: [-1, +1]
```

**Торговые сигналы:**
| UP Imbalance | DOWN Imbalance | Интерпретация | Действие |
|--------------|----------------|---------------|----------|
| > +0.3 | любой | Рынок ожидает рост BTC | Покупай UP |
| любой | > +0.3 | Рынок ожидает падение BTC | Покупай DOWN |
| < -0.3 | любой | Давление продавцов UP | Избегай UP |
| любой | < -0.3 | Давление продавцов DOWN | Избегай DOWN |

**Реализация:**
```python
# Два осциллятора: UP и DOWN imbalance
fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

# UP Imbalance
fig.add_trace(go.Scatter(
    x=time, y=up_imbalance,
    fill='tozeroy',
    fillcolor='rgba(76,175,80,0.3)' if up_imbalance[-1] > 0 else 'rgba(244,67,54,0.3)'
), row=1, col=1)

# Пороговые линии
fig.add_hline(y=0.3, line_dash="dash", line_color="green", row=1, col=1)
fig.add_hline(y=-0.3, line_dash="dash", line_color="red", row=1, col=1)
fig.add_hline(y=0, line_color="white", row=1, col=1)

# Аналогично для DOWN
```

---

## Важные метрики (Tier 2 - РЕКОМЕНДУЕМЫЕ)

### 4. Eat-Flow (Скорость поедания ликвидности)

**Почему важно в последние минуты:**
> Показывает **реальную активность тейкеров** (кто агрессивно покупает/продаёт), а не просто размещение ордеров.

**Формула:**
```python
eat_flow = (depth_now - depth_5s_ago) / 5.0  # контракты/сек
```

**Сигналы:**
- `Eat-Flow < -50`: Ликвидность активно съедается → агрессивные покупатели
- `Eat-Flow > +50`: Ликвидность добавляется → маркет-мейкеры восполняют

**Ключевые комбинации:**
```
UP Ask Eat-Flow << 0 (аски съедаются) → Кто-то агрессивно ПОКУПАЕТ UP → СИГНАЛ UP
UP Bid Eat-Flow << 0 (биды съедаются) → Кто-то агрессивно ПРОДАЁТ UP → СИГНАЛ DOWN

Eat-Flow негативный + Imbalance растёт → Маркет-мейкер восполняет (ЛОЖНЫЙ СИГНАЛ!)
```

**Реализация:**
```python
# 4 линии: UP Bid, UP Ask, DOWN Bid, DOWN Ask
fig = make_subplots(rows=2, cols=1)

# UP контракт
fig.add_trace(go.Scatter(x=time, y=up_bid_eatflow, name='UP Bid EF'), row=1, col=1)
fig.add_trace(go.Scatter(x=time, y=up_ask_eatflow, name='UP Ask EF'), row=1, col=1)

# Пороги
fig.add_hline(y=-50, line_dash="dash", line_color="red", annotation_text="Aggressive eating")
fig.add_hline(y=50, line_dash="dash", line_color="green", annotation_text="MM adding")
fig.add_hline(y=0, line_color="white")
```

---

### 5. Volume Spike (Всплеск объёма)

**Почему важно:**
> Подтверждает силу движения. Spike > 3 без движения цены = возможная ловушка.

**Формула:**
```python
spike = volume_1s / volma_30s
```

**Комбинации для алгоритма:**
```
Spike > 3.0 + Ret1s > 0.05 → Сильный сигнал UP
Spike > 3.0 + Ret1s < -0.05 → Сильный сигнал DOWN
Spike > 3.0 + |Ret1s| < 0.02 → ЛОВУШКА (накопление без движения)
```

**Реализация:**
```python
# Bar chart объёма + линия Spike
fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4])

# Объём (бары окрашены по spike)
colors = ['grey' if s < 1 else 'yellow' if s < 2 else 'orange' if s < 3 else 'red' for s in spike]
fig.add_trace(go.Bar(x=time, y=volume_1s, marker_color=colors), row=1, col=1)

# Spike осциллятор
fig.add_trace(go.Scatter(x=time, y=spike, fill='tozeroy'), row=2, col=1)
fig.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="SIGNAL", row=2, col=1)
```

---

### 6. Orderbook Visualization (Стакан)

**Почему важно:**
> Визуальное понимание где "стены" (support/resistance) и куда давит рынок.

**Реализация (уже есть в проекте):**
```python
# Горизонтальные бары: биды слева (зелёные), аски справа (красные)
# Аномально большие ордера (>2x avg) подсвечены ярче

# UP стакан
fig.add_trace(go.Bar(
    y=up_bid_prices, x=[-s for s in up_bid_sizes],
    orientation='h', name='UP Bids',
    marker_color=['lime' if s > threshold else 'green' for s in up_bid_sizes]
))
fig.add_trace(go.Bar(
    y=up_ask_prices, x=up_ask_sizes,
    orientation='h', name='UP Asks',
    marker_color=['pink' if s > threshold else 'red' for s in up_ask_sizes]
))
```

---

## Дополнительные метрики (Tier 3 - ОПЦИОНАЛЬНО)

### 7. Microprice

**Формула:**
```python
microprice = (ask_price * bid_size + bid_price * ask_size) / (bid_size + ask_size)
```

**Сигнал:** Microprice близка к ask → скоро пробой вверх

### 8. Slope (Наклон стакана)

**Формула:**
```python
slope = top2_depth / top5_depth  # [0, 1]
```

**Сигнал:** Slope > 0.6 = "стена" на лучших уровнях

### 9. Arbitrage Edge

**Формула:**
```python
edge = 1.0 - (up_bid_price + down_bid_price)
```

**Сигнал:** Edge > 0.02 (2%+) при достаточной глубине = арбитражная возможность

---

## Приоритетный порядок реализации

### Фаза 1: Критические графики (СДЕЛАТЬ ПЕРВЫМИ)

| # | График | Файл | Сложность | Время |
|---|--------|------|-----------|-------|
| 1 | Oracle vs Binance + Lag | charts.py | Средняя | 2-3 часа |
| 2 | Spread Monitor | charts.py | Низкая | 1 час |
| 3 | Imbalance Oscillator | charts.py | Низкая | 1 час |

### Фаза 2: Важные графики

| # | График | Файл | Сложность | Время |
|---|--------|------|-----------|-------|
| 4 | Eat-Flow | charts.py | Средняя | 2 часа |
| 5 | Volume Spike | charts.py | Низкая | 1 час |
| 6 | Orderbook (уже есть) | charts.py | - | - |

### Фаза 3: Расширенные графики

| # | График | Файл | Сложность | Время |
|---|--------|------|-----------|-------|
| 7 | Microprice | charts.py | Низкая | 1 час |
| 8 | Slope | charts.py | Низкая | 1 час |
| 9 | Arbitrage Edge | charts.py | Низкая | 1 час |

---

## Архитектура дашборда для последних 4 минут

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: Time Left: MM:SS │ Phase: 🟠 РАЗВЯЗКА │ Spread OK/WARN │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ PRICE CHART: Binance (orange) + Oracle (blue)       │    │
│  │ Strike line (dashed white)                          │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ LAG SUBPLOT: Green (oracle>binance) Red (binance>)  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ UP ORDERBOOK         │  │ DOWN ORDERBOOK       │        │
│  │ ◀══ Bids │ Asks ══▶  │  │ ◀══ Bids │ Asks ══▶ │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ IMBALANCE: UP (top) + DOWN (bottom)                 │    │
│  │ Thresholds: ±0.3 (dashed lines)                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ SPREAD MONITOR: UP vs DOWN (bars with thresholds)   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SIDEBAR: Spread, Imbalance, Eat-Flow values + SIGNALS      │
└─────────────────────────────────────────────────────────────┘
```

---

## Алгоритм торговли: Базовая логика

```python
def should_trade(data, seconds_left):
    """
    Базовый алгоритм для последних 4 минут.
    Возвращает: 'BUY_UP', 'BUY_DOWN', 'EXIT', или None
    """

    # === ФИЛЬТРЫ (не торговать если) ===

    # 1. Слишком мало времени
    if seconds_left < 30:
        return 'EXIT'  # Критическая зона

    # 2. Слишком широкий спред
    if data['up_spread'] > 0.10 or data['down_spread'] > 0.10:
        return None  # Не входить

    # 3. Недостаточно ликвидности
    if data['up_depth'] < 1000 or data['down_depth'] < 1000:
        return None

    # === СИГНАЛЫ ===

    # Lag-based signal (арбитраж оракула)
    lag = data['oracle_price'] - data['binance_price']

    if lag > 5 and data['binance_ret1s'] < -0.05:
        # Binance падает, оракул отстаёт → DOWN
        if data['down_imbalance'] > 0.2:
            return 'BUY_DOWN'

    if lag < -5 and data['binance_ret1s'] > 0.05:
        # Binance растёт, оракул отстаёт → UP
        if data['up_imbalance'] > 0.2:
            return 'BUY_UP'

    # Imbalance-based signal
    if data['up_imbalance'] > 0.4 and data['up_ask_eatflow'] < -30:
        # Сильное давление покупателей UP + аски съедаются
        if data['volume_spike'] > 2.0:
            return 'BUY_UP'

    if data['down_imbalance'] > 0.4 and data['down_ask_eatflow'] < -30:
        # Сильное давление покупателей DOWN + аски съедаются
        if data['volume_spike'] > 2.0:
            return 'BUY_DOWN'

    return None
```

---

## Чек-лист перед входом (последние 4 минуты)

### Обязательные условия:
- [ ] `seconds_left > 60` (не входить в последнюю минуту)
- [ ] `spread < 0.05` (ликвидность достаточная)
- [ ] `|imbalance| > 0.2` в направлении сделки
- [ ] `volume_spike > 1.5` (активность подтверждает)

### Усиливающие факторы:
- [ ] `lag` в нужном направлении (арбитражное окно)
- [ ] `eat_flow < -30` на стороне покупки (аски съедаются)
- [ ] `slope < 0.6` на стороне против (нет стены)

### Стоп-сигналы:
- [ ] `spread > 0.10` → немедленный выход
- [ ] `seconds_left < 30` → немедленный выход
- [ ] `imbalance` развернулся против позиции

---

## Выводы

### Почему именно эти метрики?

1. **Lag (Oracle vs Binance)** — единственный индикатор, напрямую связанный с исходом рынка. Оракул определяет кто выиграл.

2. **Spread** — в последние минуты критически важен, т.к. определяет стоимость входа/выхода. Широкий спред съедает прибыль.

3. **Imbalance** — опережающий индикатор, показывает куда давит рынок ДО движения цены.

4. **Eat-Flow** — показывает реальную активность, а не просто размещение ордеров. Помогает отличить реальный сигнал от ложного.

5. **Volume Spike** — подтверждающий индикатор. Без объёма движение ненадёжно.

### Порядок важности для алгоритма:

```
1. Lag (арбитражное окно)     ████████████████████ 100%
2. Spread (можно ли торговать) ███████████████████  95%
3. Imbalance (куда давит)      ██████████████████   90%
4. Eat-Flow (реальная активность) ███████████████   75%
5. Volume Spike (подтверждение) ██████████████      70%
6. Orderbook (визуализация)    ████████████         60%
```

### Следующие шаги:

1. Добавить вычисление `imbalance`, `spread`, `eat_flow` в `data_loader.py`
2. Создать новые графики в `charts.py`
3. Добавить алерты/сигналы в callbacks
4. Протестировать на исторических данных
