# Полное руководство по Dash + Plotly в xDaimon FastScan

## Оглавление
1. [Введение в Dash и Plotly](#введение)
2. [Архитектура приложения](#архитектура)
3. [Система роутинга и Multi-Window режим](#роутинг)
4. [Создание графиков с Plotly](#plotly-графики)
5. [Callback система Dash](#callback-система)
6. [Оптимизация производительности через Patch](#patch-optimization)
7. [Система буферизации и кеширования](#буферизация)
8. [Cross-tab синхронизация](#синхронизация)
9. [Продвинутые техники](#продвинутые-техники)

---

## Введение в Dash и Plotly {#введение}

### Что такое Dash?

**Dash** — это Python-фреймворк от Plotly для создания аналитических веб-приложений. Под капотом Dash использует:
- **Flask** (веб-сервер)
- **React.js** (компоненты UI)
- **Plotly.js** (интерактивные графики)

### Что такое Plotly?

**Plotly** — это библиотека для создания интерактивных графиков. В Python это `plotly.graph_objects` и `plotly.express`.

### Как они работают вместе?

```
Python (Dash) → создает компоненты и callback'и
    ↓
Flask сервер → обрабатывает HTTP запросы
    ↓
React компоненты → отображают UI в браузере
    ↓
Plotly.js → рендерит интерактивные графики
```

---

## Архитектура приложения {#архитектура}

### Структура файлов

```
poly_fast_scan/
├── app.py                    # Точка входа, создание Dash app
├── src/
│   ├── layout.py            # Компоненты UI (html.Div, dcc.Graph)
│   ├── callbacks.py         # Вся интерактивность
│   ├── charts.py            # Создание Plotly figures
│   ├── data_loader.py       # Загрузка CSV данных
│   ├── buffer.py            # LRU кеш для оптимизации
│   └── widgets/             # Модульные компоненты
│       ├── right_panel.py
│       ├── orderbook.py
│       ├── btc_chart.py
│       └── ...
└── assets/
    ├── custom.css           # Стили
    └── cross_tab_sync.js    # JavaScript для синхронизации
```

### Инициализация приложения ([app.py](app.py))

```python
from dash import Dash

app = Dash(
    __name__,
    suppress_callback_exceptions=True  # ⚠️ Важно для динамических layouts
)

app.layout = create_root_layout  # Функция, а не объект!
register_callbacks(app)          # Регистрируем все callback'и
app.run(debug=True, host='127.0.0.1', port=8050)
```

**Ключевые моменты:**
- `suppress_callback_exceptions=True` — обязателен для multi-window режима
- `app.layout` должен быть **функцией** для динамических layouts

---

## Система роутинга и Multi-Window режим {#роутинг}

### Принцип работы роутинга

Приложение поддерживает 3 режима отображения через URL параметры:

```
http://localhost:8050/           → Main view (все графики + панель управления)
http://localhost:8050/?view=orderbook  → Pop-out: только Orderbook
http://localhost:8050/?view=btc         → Pop-out: только BTC & Lag
```

### Реализация роутера ([layout.py:207-212](layout.py#L207-L212))

```python
def create_root_layout():
    """Корневой layout с dcc.Location для роутинга"""
    return html.Div([
        dcc.Location(id='url', refresh=False),  # Отслеживает URL
        html.Div(id='content-container')        # Контейнер для динамического контента
    ])
```

### Callback роутера ([callbacks.py:556-570](callbacks.py#L556-L570))

```python
@callback(
    Output('content-container', 'children'),
    Input('url', 'search')  # Отслеживает query параметры (?view=...)
)
def display_page(search):
    if search and 'view=orderbook' in search:
        return create_orderbook_popout()
    elif search and 'view=btc' in search:
        return create_btc_popout()
    else:
        return create_main_layout()
```

**Как это работает:**
1. `dcc.Location` автоматически триггерит callback при изменении URL
2. Callback читает `search` (query string)
3. Возвращает соответствующий layout

### Открытие pop-out окон (clientside callback)

```python
# callbacks.py:498-510
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.open(window.location.origin + '/?view=orderbook', '_blank');
        }
        return '';
    }
    """,
    Output('_popout-ob-dummy', 'children'),
    Input('popout-orderbook-btn', 'n_clicks'),
    prevent_initial_call=True
)
```

**Clientside callback** — JavaScript выполняется **в браузере**, без обращения к серверу.

---

## Создание графиков с Plotly {#plotly-графики}

### Основные концепции Plotly

#### 1. Figure — это словарь с 2 ключами:

```python
fig = {
    'data': [...],    # Список traces (линии, бары, scatter)
    'layout': {...}   # Настройки осей, заголовка, цветов
}
```

#### 2. Trace — один элемент графика

```python
trace = go.Scatter(
    x=[1, 2, 3],
    y=[10, 20, 15],
    mode='lines',
    name='My Line',
    line=dict(color='blue', width=2)
)
```

### Создание Orderbook графика ([charts.py:50-116](charts.py#L50-L116))

#### Структура: 2 ряда × 2 колонки

```python
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('UP Contract', 'DOWN Contract', '', ''),
    row_heights=[0.60, 0.40],  # Ряд 1: 60%, Ряд 2: 40%
    specs=[
        [{"type": "bar"}, {"type": "bar"}],           # Ряд 1: стаканы
        [{"type": "scatter", "colspan": 2}, None]      # Ряд 2: ask prices (на всю ширину)
    ]
)
```

**Визуально:**
```
┌─────────────┬─────────────┐
│  UP Bars    │  DOWN Bars  │  ← Row 1 (стаканы)
├─────────────┴─────────────┤
│   Ask Prices Timeline     │  ← Row 2 (цены во времени)
└───────────────────────────┘
```

#### Добавление горизонтальных баров (стаканов)

```python
# widgets/orderbook.py:11-28
def add_orderbook_traces(fig, data, anomaly_threshold, global_max):
    # UP Bids (зеленые, влево)
    fig.add_trace(
        go.Bar(
            y=[f"{p:.2f}" for p in data['up']['bid_prices']],  # Цены по Y
            x=[-abs(s) for s in data['up']['bid_sizes']],      # Размеры по X (отрицательные!)
            orientation='h',  # Горизонтальная ориентация
            marker=dict(
                color=['rgba(0,200,83,0.7)' if s < anomaly_threshold
                       else 'rgba(0,255,100,1)' for s in data['up']['bid_sizes']]
            ),
            name='UP Bids'
        ),
        row=1, col=1  # Позиция в subplots
    )
```

**Почему X отрицательный для Bids?**
- Создает эффект "зеркала" — биды идут влево, аски вправо
- Классический вид стакана ордеров

#### Определение аномалий (крупных ордеров)

```python
# data_loader.py:52-65
def calculate_anomaly_threshold(sizes):
    """Ордера >2x среднего считаются аномалиями"""
    valid_sizes = [s for s in sizes if pd.notna(s) and s > 0]
    return np.mean(valid_sizes) * 2 if valid_sizes else float('inf')
```

Аномальные ордера подсвечиваются ярким цветом.

### Создание BTC графика ([charts.py:119-160](charts.py#L119-L160))

#### Структура: 2 ряда × 1 колонка

```python
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('BTC Price', 'Price Lag'),
    row_heights=[0.65, 0.35]
)
```

#### Добавление линий цен

```python
# Binance BTC (оранжевая)
fig.add_trace(
    go.Scatter(
        x=list(range(len(df))),         # Индексы строк
        y=df['binance_btc_price'].values,
        mode='lines',
        name='Binance BTC',
        line=dict(color='#FF6B00', width=2)
    ),
    row=1, col=1
)

# Oracle BTC (синяя)
fig.add_trace(
    go.Scatter(
        x=[i for i, m in enumerate(oracle_mask) if m],  # Только валидные точки
        y=[float(p) for p, m in zip(oracle_prices, oracle_mask) if m],
        mode='lines',
        name='Oracle BTC',
        line=dict(color='#2196F3', width=2)
    ),
    row=1, col=1
)
```

#### Добавление маркеров текущей позиции

```python
# Текущая позиция на графике (большой маркер с обводкой)
fig.add_trace(
    go.Scatter(
        x=[row_idx],
        y=[current_binance],
        mode='markers',
        marker=dict(
            size=12,
            color='#FF6B00',
            line=dict(color='white', width=2)  # Белая обводка
        ),
        showlegend=False
    ),
    row=1, col=1
)
```

#### Добавление вертикальной линии

```python
fig.add_vline(
    x=row_idx,
    line_color='rgba(255,255,255,0.2)',
    line_width=1,
    line_dash='dot',  # Пунктирная
    row=1, col=1
)
```

### Стилизация графиков

```python
fig.update_layout(
    title=dict(
        text="My Chart Title",
        font=dict(size=14)
    ),
    showlegend=True,
    legend=dict(
        orientation='h',    # Горизонтальная легенда
        yanchor='top',
        y=-0.08,            # Под графиком
        xanchor='center',
        x=0.5
    ),
    paper_bgcolor='#1e1e1e',  # Фон всей figure
    plot_bgcolor='#2d2d2d',   # Фон области графика
    font=dict(color='white'),
    margin=dict(t=80, b=60)
)

# Стилизация осей
fig.update_xaxes(
    title_text="Timeline",
    gridcolor='#444',  # Цвет сетки
    row=1, col=1
)

fig.update_yaxes(
    title_text="Price ($)",
    gridcolor='#444',
    row=1, col=1
)
```

---

## Callback система Dash {#callback-система}

### Что такое Callback?

**Callback** — это функция Python, которая:
1. **Принимает Inputs/States** (значения компонентов)
2. **Выполняет логику**
3. **Возвращает Outputs** (обновляет компоненты)

### Анатомия Callback

```python
from dash import callback, Input, Output, State

@callback(
    Output('component-id', 'property'),  # Что обновляем
    Input('trigger-id', 'property'),     # Что триггерит callback
    State('data-id', 'property')         # Что читаем (не триггерит!)
)
def my_callback(trigger_value, data_value):
    # Логика обработки
    return new_value
```

**Важно:**
- `Input` — триггерит callback при изменении
- `State` — читаем значение, но не триггерим
- `Output` — компонент, который будет обновлен

### Пример 1: Инициализация при выборе файла ([callbacks.py:67-127](callbacks.py#L67-L127))

```python
@callback(
    [
        Output('cumulative-times', 'data'),      # Сохраняем таймстампы
        Output('time-slider', 'max'),            # Обновляем max слайдера
        Output('time-slider', 'marks'),          # Обновляем метки
        Output('time-slider', 'value'),          # Сбрасываем позицию
        Output('file-info', 'children'),         # Инфо о файле
        Output('chart-orderbook', 'figure'),     # Новый график
        Output('chart-btc', 'figure'),           # Новый график
        Output('buffer-status', 'children')      # Статус буфера
    ],
    [
        Input('file-selector', 'value'),         # Триггер: выбор файла
        Input('buffer-size-slider', 'value')     # Триггер: размер буфера
    ]
)
def init_on_file_change(filename, buffer_size):
    if not filename:
        empty_fig = {'data': [], 'layout': {...}}
        return [], 0, {}, 0, "No file", empty_fig, empty_fig, "No file"

    # Загружаем данные
    df = get_cached_data(filename)
    cumulative_times = compute_cumulative_times(df)

    # Создаем начальные графики
    ob_fig = create_orderbook_chart(df, 0)
    btc_fig = create_btc_chart(df, 0)

    # Предзагружаем кадры в буфер
    buffered = prebuffer_traces(filename, 0, buffer_size)

    # Возвращаем 8 значений (по порядку Output'ов)
    return cumulative_times, max_val, marks, 0, file_info, ob_fig, btc_fig, buffer_status
```

**Что происходит:**
1. Пользователь выбирает файл из dropdown
2. Триггерится callback
3. Загружаются данные
4. Создаются графики
5. Обновляются 8 компонентов одновременно

### Пример 2: Playback кнопка Play/Pause ([callbacks.py:132-193](callbacks.py#L132-L193))

```python
@callback(
    [
        Output('playback-state', 'data'),        # Состояние (играет/пауза)
        Output('play-pause-btn', 'children'),    # Текст кнопки
        Output('play-pause-btn', 'style'),       # Цвет кнопки
        Output('playback-interval', 'disabled'), # Включить/выключить таймер
        Output('buffer-status', 'children', allow_duplicate=True)
    ],
    [
        Input('play-pause-btn', 'n_clicks'),     # Клик по кнопке
        Input('speed-selector', 'value')         # Изменение скорости
    ],
    [
        State('playback-state', 'data'),         # Текущее состояние
        State('time-slider', 'value'),           # Текущая позиция
        State('time-slider', 'max'),             # Максимум
        State('file-selector', 'value'),         # Файл
        State('buffer-size-slider', 'value')     # Размер буфера
    ],
    prevent_initial_call=True  # ⚠️ Не вызывать при загрузке страницы
)
def handle_playback_controls(n_clicks, speed, state, slider_value, max_rows, filename, buffer_size):
    triggered_id = ctx.triggered_id  # Какой Input триггернул?

    if triggered_id == 'play-pause-btn':
        new_is_playing = not state['is_playing']  # Переключаем

        if new_is_playing:
            # Предзагружаем больше кадров для высоких скоростей
            multiplier = 1.5 if speed >= 4 else 1.2 if speed >= 2 else 1.0
            prebuffer_traces(filename, slider_value, int(buffer_size * multiplier))

    if new_is_playing:
        new_state = {
            'is_playing': True,
            'play_start_time': int(time.time() * 1000),  # Текущее время
            'play_start_row': slider_value,
            'speed': speed
        }
        return new_state, '⏸ Pause', PAUSE_BTN_STYLE, False, buffer_status
    else:
        new_state = {'is_playing': False, ...}
        return new_state, '▶ Play', PLAY_BTN_STYLE, True, buffer_status
```

**Ключевые концепции:**
- `ctx.triggered_id` — определяем, **какой Input** триггернул callback
- `prevent_initial_call=True` — не запускать при загрузке страницы
- `allow_duplicate=True` — разрешить несколько callback'ов на один Output

### Пример 3: Таймер анимации ([callbacks.py:198-273](callbacks.py#L198-L273))

```python
@callback(
    [
        Output('time-slider', 'value', allow_duplicate=True),
        Output('playback-status', 'children'),
        Output('playback-state', 'data', allow_duplicate=True),
        Output('playback-interval', 'disabled', allow_duplicate=True),
        # ...
    ],
    Input('playback-interval', 'n_intervals'),  # ⏰ Таймер (каждые 100ms)
    [
        State('playback-state', 'data'),
        State('cumulative-times', 'data'),
        State('time-slider', 'max'),
        # ...
    ],
    prevent_initial_call=True
)
def update_on_interval(n_intervals, state, cumulative_times, max_rows, ...):
    if not state['is_playing']:
        return no_update, ...  # Ничего не делаем, если на паузе

    # Вычисляем сколько времени прошло в реальности
    current_time_ms = int(time.time() * 1000)
    elapsed_wall_time = current_time_ms - state['play_start_time']

    # Умножаем на скорость воспроизведения
    elapsed_data_time = elapsed_wall_time * state['speed']

    # Находим целевую строку через бинарный поиск
    start_offset = cumulative_times[state['play_start_row']]
    target_time = start_offset + elapsed_data_time
    target_row = bisect.bisect_right(cumulative_times, target_time) - 1

    # Предзагружаем следующие кадры (каждые N итераций)
    if n_intervals % prebuffer_interval == 0:
        prebuffer_traces(filename, target_row, buffer_size)

    # Проверяем конец данных
    if target_row >= max_rows:
        new_state = {'is_playing': False, ...}
        return max_rows, status, new_state, True, '▶ Play', PLAY_BTN_STYLE, "Complete"

    return target_row, status, no_update, ...
```

**Как работает таймер:**
1. `dcc.Interval(interval=100)` — триггерит callback каждые 100ms
2. Вычисляем прошедшее **реальное** время
3. Умножаем на скорость (1x, 2x, 4x)
4. Находим соответствующую строку данных через `bisect`
5. Обновляем слайдер

**Бинарный поиск (`bisect`):**
```python
cumulative_times = [0, 100, 250, 400, 600, 900]  # Кумулятивные мс
target_time = 420  # Ищем строку для 420ms

target_row = bisect.bisect_right(cumulative_times, 420) - 1
# bisect_right(420) = 4 (индекс где вставить 420)
# target_row = 3 (строка с timestamp 400ms)
```

---

## Оптимизация производительности через Patch {#patch-optimization}

### Проблема: полная замена figure

**Плохо:**
```python
@callback(
    Output('chart-orderbook', 'figure'),
    Input('time-slider', 'value')
)
def update_chart(slider_value):
    # ❌ Пересоздаем всю figure заново!
    return create_orderbook_chart(df, slider_value)
```

**Проблемы:**
- Пересоздается весь график (все 8 traces + layout)
- ~10-20ms на каждое обновление
- Сбрасывается состояние зума/пана

### Решение: Patch объект

**Хорошо:**
```python
from dash import Patch

@callback(
    Output('chart-orderbook', 'figure', allow_duplicate=True),
    Input('time-slider', 'value'),
    prevent_initial_call=True
)
def update_chart_patch(slider_value):
    cache = get_trace_cache()
    trace_data = cache.compute_trace_data(filename, slider_value)

    patched_fig = Patch()  # 🔥 Создаем патч

    # Обновляем ТОЛЬКО нужные данные
    patched_fig['data'][0]['y'] = trace_data['up_bids']['y']
    patched_fig['data'][0]['x'] = trace_data['up_bids']['x']
    patched_fig['data'][0]['marker']['color'] = trace_data['up_bids']['colors']

    patched_fig['layout']['title']['text'] = f"Orderbook @ {trace_data['timestamp']}"

    return patched_fig  # ✅ Обновляем только измененные поля
```

**Преимущества:**
- Обновляется только **измененные поля**
- ~1-2ms вместо 10-20ms
- Сохраняется состояние зума
- Плавная анимация

### Полный пример: обновление Orderbook ([callbacks.py:289-358](callbacks.py#L289-L358))

```python
@callback(
    Output('chart-orderbook', 'figure', allow_duplicate=True),
    Input('time-slider', 'value'),
    [State('file-selector', 'value'), ...],
    prevent_initial_call=True
)
def update_orderbook_on_slider(slider_value, filename, active_track, zoom_level):
    # Получаем данные из кеша
    cache = get_trace_cache()
    trace_data = cache.compute_trace_data(filename, slider_value)

    patched_fig = Patch()

    # ============ Active-Track: авто-скролл ============
    if active_track and 'enabled' in active_track:
        half_window = zoom_level if zoom_level else 150
        x_min = max(0, slider_value - half_window)
        x_max = slider_value + half_window
        patched_fig['layout']['xaxis3']['range'] = [x_min, x_max]

    # ============ Обновление UP Bids (trace 0) ============
    patched_fig['data'][0]['y'] = trace_data['up_bids']['y']
    patched_fig['data'][0]['x'] = trace_data['up_bids']['x']
    patched_fig['data'][0]['text'] = trace_data['up_bids']['text']
    patched_fig['data'][0]['marker']['color'] = trace_data['up_bids']['colors']

    # ============ Обновление UP Asks (trace 1) ============
    patched_fig['data'][1]['y'] = trace_data['up_asks']['y']
    patched_fig['data'][1]['x'] = trace_data['up_asks']['x']
    # ... аналогично

    # ============ Обновление маркеров текущей позиции ============
    patched_fig['data'][6]['x'] = trace_data['up_ask_price_x']    # [row_idx]
    patched_fig['data'][6]['y'] = trace_data['up_ask_price_y']    # [current_price]

    # ============ Обновление заголовка ============
    title_text = (
        f"Orderbook @ {trace_data['timestamp']}<br>" +
        f"<sub>UP: {trace_data['up_pressure']} ...</sub>"
    )
    patched_fig['layout']['title']['text'] = title_text

    return patched_fig
```

**Индексы traces:**
```
Orderbook chart:
  data[0] = UP Bids (bar)
  data[1] = UP Asks (bar)
  data[2] = DOWN Bids (bar)
  data[3] = DOWN Asks (bar)
  data[4] = UP Ask Price line
  data[5] = DOWN Ask Price line
  data[6] = Current UP marker
  data[7] = Current DOWN marker
```

**Важно знать индексы!** Они определяются порядком `add_trace()` при создании figure.

---

## Система буферизации и кеширования {#буферизация}

### Зачем нужен кеш?

При воспроизведении на скорости 4x:
- Callback триггерится каждые 100ms
- За секунду обновляется ~10 кадров
- Без кеша: каждый кадр вычисляется заново → тормоза

### LRU Cache ([buffer.py:13-49](buffer.py#L13-L49))

```python
class LRUCache:
    """Least Recently Used Cache - удаляет самые старые элементы"""

    def __init__(self, maxsize: int = 64):
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()  # Сохраняет порядок вставки

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)  # Помечаем как недавно использованный
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)  # Удаляем САМЫЙ СТАРЫЙ
        self.cache[key] = value
```

**Почему OrderedDict?**
- Сохраняет порядок вставки
- `move_to_end()` — перемещает элемент в конец (как "недавно использованный")
- `popitem(last=False)` — удаляет самый старый элемент

### TraceDataCache ([buffer.py:51-216](buffer.py#L51-L216))

```python
class TraceDataCache:
    """Кеш для trace данных (НЕ для полных figures)"""

    def __init__(self, maxsize: int = 128):
        self.cache = LRUCache(maxsize)
        self.df_cache: Dict[str, pd.DataFrame] = {}

    def compute_trace_data(self, filename: str, row_idx: int) -> Dict:
        key = (filename, row_idx)

        # Проверяем кеш
        cached = self.cache.get(key)
        if cached is not None:
            return cached  # ✅ Мгновенный ответ

        # Вычисляем данные
        df = self.get_df(filename)
        data = self._extract_trace_data(df, row_idx)

        # Сохраняем в кеш
        self.cache.put(key, data)
        return data
```

### Что хранится в кеше?

**НЕ хранится полная figure** (тяжелая, ~100KB):
```python
# ❌ Плохо
cache[key] = create_orderbook_chart(df, row_idx)  # Полная Plotly figure
```

**Хранится легковесный dict** (~5-10KB):
```python
# ✅ Хорошо
trace_data = {
    'up_bids': {
        'y': ["0.51", "0.52", ...],
        'x': [-1200, -800, ...],
        'text': ["$1,200", "$800", ...],
        'colors': ['rgba(0,200,83,0.7)', ...]
    },
    'up_asks': {...},
    'timestamp': '2024-01-15 12:34:56',
    'up_pressure': 'BUYERS',
    'up_bid_total': 15000,
    # ...
}
```

### Prebuffering: предзагрузка кадров ([buffer.py:175-194](buffer.py#L175-L194))

```python
def prebuffer(self, filename: str, start_row: int, count: int = 30) -> int:
    """Предзагрузить следующие count кадров"""
    df = self.get_df(filename)
    max_row = len(df) - 1
    new_count = 0

    for i in range(count):
        row = start_row + i
        if row > max_row:
            break

        key = (filename, row)
        if key not in self.cache:  # Только новые
            self.compute_trace_data(filename, row)
            new_count += 1

    return new_count
```

**Когда вызывается prebuffer:**
1. При загрузке файла (начальные кадры)
2. При нажатии Play (агрессивная загрузка)
3. Каждые N итераций таймера (адаптивно)

### Адаптивная буферизация ([callbacks.py:238-254](callbacks.py#L238-L254))

```python
# В callback update_on_interval
speed = state['speed']

# Частота prebuffer зависит от скорости
if speed >= 4:
    prebuffer_interval = 2    # Каждые 2 итерации (200ms)
elif speed >= 2:
    prebuffer_interval = 3    # Каждые 3 итерации (300ms)
else:
    prebuffer_interval = 5    # Каждые 5 итераций (500ms)

if n_intervals % prebuffer_interval == 0:
    # Размер буфера увеличивается для высоких скоростей
    adaptive_buffer_size = int(buffer_size * (1 + (speed - 1) * 0.3))
    adaptive_buffer_size = min(adaptive_buffer_size, buffer_size * 2)

    prebuffer_traces(filename, target_row, adaptive_buffer_size)
    ahead, total = get_buffer_stats(filename, target_row)
```

**Логика:**
- Скорость 4x → загружаем чаще и больше кадров
- Скорость 1x → загружаем реже и меньше кадров

---

## Cross-tab синхронизация {#синхронизация}

### Проблема: несколько окон браузера

Пользователь открывает:
- **Main window** — управление + графики
- **Pop-out 1** — Orderbook в отдельной вкладке
- **Pop-out 2** — BTC в отдельной вкладке

Нужно синхронизировать:
- Позицию слайдера
- Выбранный файл
- Состояние playback

### Решение 1: localStorage (Dash Store)

```python
# layout.py:109-117
def create_shared_stores():
    return [
        dcc.Store(id='shared-slider-value', storage_type='local'),
        dcc.Store(id='shared-file-selection', storage_type='local'),
        dcc.Store(id='shared-playback-state', storage_type='local'),
        dcc.Store(id='shared-popout-status', storage_type='local'),
    ]
```

**`storage_type='local'`** → данные сохраняются в `localStorage` браузера.

#### Запись в localStorage

```python
# callbacks.py:527-539
@callback(
    Output('shared-slider-value', 'data'),
    Input('time-slider', 'value'),
    State('file-selector', 'value')
)
def sync_slider_to_storage(slider_value, filename):
    """Записываем позицию слайдера в localStorage"""
    return {
        'value': slider_value,
        'filename': filename,
        'timestamp': int(time.time() * 1000)
    }
```

**Что происходит:**
1. Пользователь двигает слайдер
2. Callback триггерится
3. Данные записываются в `localStorage`
4. **Все вкладки видят изменения!**

#### Чтение из localStorage в pop-out

```python
# callbacks.py:572-637
@callback(
    [Output('popout-chart', 'figure'), Output('popout-last-value', 'data')],
    Input('popout-sync-interval', 'n_intervals'),  # Опрос каждые 100ms
    [State('shared-slider-value', 'data'), ...]
)
def update_popout_chart(n, slider_data, file_data, last_value_data, search):
    if not slider_data:
        return no_update, no_update

    filename = file_data.get('filename')
    slider_value = slider_data.get('value', 0)

    # Оптимизация: не обновляем если значение не изменилось
    last_val = last_value_data.get('value', -1)
    if slider_value == last_val and n > 0:
        return no_update, no_update

    # Загружаем данные
    df = load_data(filename)

    # Определяем тип pop-out
    if 'view=orderbook' in search:
        fig = create_orderbook_popout_figure(df, slider_value)
    elif 'view=btc' in search:
        fig = create_btc_popout_figure(df, slider_value)

    return fig, {'value': slider_value, 'filename': filename}
```

**Поллинг:**
- `dcc.Interval` триггерит callback каждые 100ms
- Читаем `localStorage`
- Если значение изменилось → обновляем график

### Решение 2: BroadcastChannel API (JavaScript)

**Для мгновенной синхронизации** (без задержки 100ms).

```javascript
// assets/cross_tab_sync.js
const channel = new BroadcastChannel('fastscan_sync');

// Отправка сообщения
channel.postMessage({
    type: 'SLIDER_UPDATE',
    data: { value: 42 }
});

// Прием сообщения
channel.onmessage = function(event) {
    const { type, data } = event.data;

    if (type === 'SLIDER_UPDATE') {
        localStorage.setItem('shared-slider-value', JSON.stringify({
            value: data.value,
            timestamp: Date.now()
        }));
    }
};
```

**BroadcastChannel** — это Web API для общения между вкладками **мгновенно**.

### Управление состоянием pop-out окон

```python
# callbacks.py:639-691
@callback(
    [
        Output('chart-orderbook-container', 'style'),
        Output('placeholder-orderbook', 'style'),
        Output('chart-btc-container', 'style'),
        Output('placeholder-btc', 'style')
    ],
    Input('shared-popout-status', 'data')
)
def toggle_charts_visibility(popout_status):
    """Скрыть графики на главной странице если они открыты в pop-out"""
    if not popout_status:
        return {}, {'display': 'none'}, {}, {'display': 'none'}

    # Orderbook
    if popout_status.get('orderbook'):
        ob_chart_style = {'display': 'none'}         # Скрыть график
        ob_placeholder_style = {'display': 'block'}  # Показать placeholder
    else:
        ob_chart_style = {'display': 'block'}
        ob_placeholder_style = {'display': 'none'}

    # Аналогично для BTC
    # ...

    return ob_chart_style, ob_placeholder_style, btc_chart_style, btc_placeholder_style
```

**Логика:**
1. Pop-out окно записывает статус в `localStorage`
2. Main окно читает статус
3. Скрывает график и показывает placeholder "Opened in new tab"

---

## Продвинутые техники {#продвинутые-техники}

### 1. Active-Track: авто-скролл графика

**Задача:** График автоматически следует за текущей позицией.

```python
# callbacks.py:310-314
if active_track and 'enabled' in active_track:
    half_window = zoom_level if zoom_level else 150
    x_min = max(0, slider_value - half_window)
    x_max = slider_value + half_window
    patched_fig['layout']['xaxis3']['range'] = [x_min, x_max]
```

**Как работает:**
- Пользователь включает чекбокс "Follow Price"
- При каждом обновлении слайдера:
  - Вычисляем окно `[current - zoom, current + zoom]`
  - Устанавливаем `xaxis.range` через Patch

### 2. Синхронизация осей между subplots

**Задача:** При зуме на BTC Price автоматически зумировать Lag.

```python
# callbacks.py:438-479
@callback(
    Output('chart-btc', 'figure', allow_duplicate=True),
    Input('chart-btc', 'relayoutData'),  # Триггер: зум/пан
    State('active-track-checklist', 'value')
)
def sync_btc_chart_axes(relayout_data, active_track):
    if active_track and 'enabled' in active_track:
        return no_update  # Не синхронизируем в active-track режиме

    patched_fig = Patch()

    # Зум на BTC (xaxis) → синхронизируем Lag (xaxis2)
    if 'xaxis.range[0]' in relayout_data:
        patched_fig['layout']['xaxis2']['range'] = [
            relayout_data['xaxis.range[0]'],
            relayout_data['xaxis.range[1]']
        ]
        return patched_fig

    # Зум на Lag (xaxis2) → синхронизируем BTC (xaxis)
    if 'xaxis2.range[0]' in relayout_data:
        patched_fig['layout']['xaxis']['range'] = [
            relayout_data['xaxis2.range[0]'],
            relayout_data['xaxis2.range[1]']
        ]
        return patched_fig

    return no_update
```

**`relayoutData`** — специальный Output от `dcc.Graph`, который триггерится при:
- Зуме (wheel)
- Пане (drag)
- Сбросе зума (double-click)

### 3. Динамическое управление FPS

```python
# callbacks.py:420-426
@callback(
    Output('playback-interval', 'interval'),
    Input('fps-selector', 'value')
)
def update_fps(interval_ms):
    """Изменить частоту обновления UI"""
    return interval_ms
```

**Пользователь может выбрать:**
- 5 FPS → `interval=200` (200ms)
- 10 FPS → `interval=100` (100ms)
- 30 FPS → `interval=33` (33ms)

### 4. Вычисление давления покупателей/продавцов

```python
# data_loader.py:68-82
def calculate_pressure(bid_sizes, ask_sizes):
    bid_total = sum([s for s in bid_sizes if pd.notna(s)])
    ask_total = sum([s for s in ask_sizes if pd.notna(s)])
    pressure = "BUYERS" if bid_total > ask_total else "SELLERS"
    return pressure, bid_total, ask_total
```

**Использование в заголовке:**
```python
title = (
    f"Orderbook @ {timestamp}<br>" +
    f"<sub>UP: {up_pressure} (Bids: ${up_bid_total:,.0f} vs Asks: ${up_ask_total:,.0f})</sub>"
)
```

### 5. Определение аномальных ордеров

```python
# data_loader.py:52-65
def calculate_anomaly_threshold(sizes):
    valid_sizes = [s for s in sizes if pd.notna(s) and s > 0]
    return np.mean(valid_sizes) * 2 if valid_sizes else float('inf')
```

**Подсветка в графике:**
```python
colors = [
    'rgba(0,255,100,1)' if size > threshold else 'rgba(0,200,83,0.7)'
    for size in sizes
]
```

### 6. Обработка missing values (NaN)

```python
# charts.py:241-244
oracle_prices = df['oracle_btc_price'].values
oracle_mask = ~pd.isna(oracle_prices)

x_values = [i for i, m in enumerate(oracle_mask) if m]
y_values = [float(p) for p, m in zip(oracle_prices, oracle_mask) if m]
```

**Почему важно:**
- Plotly не любит `NaN` в данных
- Фильтруем через mask

### 7. Hover templates

```python
fig.add_trace(
    go.Scatter(
        x=x, y=y,
        hovertemplate='Binance: $%{y:,.2f}<extra></extra>'
        #             ^ Форматирование  ^ Убирает trace name
    )
)
```

**Форматы:**
- `%{y:,.2f}` — число с запятыми и 2 знаками (12,345.67)
- `%{y:.4f}` — 4 знака после запятой (0.5123)
- `<extra></extra>` — убирает название trace из hover

---

## Заключение

### Основные паттерны проекта

1. **Модульная архитектура**
   - Layout в `layout.py`
   - Логика в `callbacks.py`
   - Графики в `charts.py` + `widgets/`

2. **Multi-window через роутинг**
   - `dcc.Location` + query параметры
   - Динамические layouts

3. **Оптимизация производительности**
   - Patch вместо полной замены
   - LRU кеш для trace данных
   - Предзагрузка кадров

4. **Синхронизация вкладок**
   - `localStorage` для персистентности
   - BroadcastChannel для мгновенной синхронизации
   - Поллинг через `dcc.Interval`

5. **Плавная анимация**
   - Таймер через `dcc.Interval`
   - Бинарный поиск по времени
   - Адаптивная буферизация

### Полезные ссылки

- [Dash документация](https://dash.plotly.com/)
- [Plotly Python документация](https://plotly.com/python/)
- [Dash Callback Advanced Features](https://dash.plotly.com/advanced-callbacks)
- [Plotly Subplots](https://plotly.com/python/subplots/)

### Типичные ошибки и решения

#### Ошибка: "Callback circular dependency"
```python
# ❌ Плохо
@callback(Output('A', 'value'), Input('B', 'value'))
@callback(Output('B', 'value'), Input('A', 'value'))

# ✅ Хорошо: используйте allow_duplicate=True
@callback(
    Output('A', 'value', allow_duplicate=True),
    Input('B', 'value'),
    prevent_initial_call=True
)
```

#### Ошибка: "A component defined in ... is not present in the layout"
- Причина: `suppress_callback_exceptions=False` + динамические layouts
- Решение: `suppress_callback_exceptions=True` в `Dash(__name__, ...)`

#### Ошибка: "NaN in Plotly data"
```python
# ❌ Плохо
y_values = df['price'].values  # Может содержать NaN

# ✅ Хорошо
mask = ~pd.isna(df['price'])
y_values = [float(p) for p, m in zip(df['price'], mask) if m]
```

---

**Автор:** Анализ проекта xDaimon FastScan
**Дата:** 2026-02-12
**Версия Dash:** 2.14+
**Версия Plotly:** 5.18+
