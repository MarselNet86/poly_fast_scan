# Инструменты для анализа метрик

## Задача
Определить:
- Какие метрики **влияют** на результат
- Какие **не влияют** (шум)
- Какие **предсказывают** будущее

---

## 1. КОРРЕЛЯЦИОННЫЙ АНАЛИЗ

### 1.1 Correlation Matrix (Pandas)
**Что делает:** Показывает линейную связь между всеми парами метрик

**Когда использовать:** Первый шаг — быстро увидеть какие метрики связаны друг с другом

```python
import pandas as pd
import seaborn as sns

corr = df[['lag', 'pm_up_imbalance', 'binance_ret1s_x100', 'target']].corr()
sns.heatmap(corr, annot=True, cmap='RdYlGn')
```

**Что покажет:**
- Корреляция > 0.3 — метрика потенциально полезна
- Корреляция ~ 0 — метрика не влияет линейно
- Высокая корреляция между двумя метриками — они дублируют друг друга

---

### 1.2 Lagged Correlation
**Что делает:** Показывает связь метрики X в момент t с target в момент t+n

**Когда использовать:** Найти метрики которые **предсказывают** будущее

```python
# Корреляция lag с будущим направлением цены
for shift in [1, 5, 10, 30]:
    corr = df['lag'].corr(df['target'].shift(-shift))
    print(f"lag vs target(+{shift}): {corr:.3f}")
```

**Что покажет:**
- Если корреляция растёт с увеличением shift — метрика предсказывает долгосрочно
- Если падает — метрика работает только краткосрочно

---

## 2. FEATURE IMPORTANCE (ML)

### 2.1 Random Forest Feature Importance
**Что делает:** Ранжирует метрики по их вкладу в предсказание

**Когда использовать:** Быстро отсеять бесполезные метрики

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
```

**Что покажет:**
- Top 10 метрик — фокусироваться на них
- Bottom 10 — можно убрать (шум)

---

### 2.2 SHAP Values (лучший инструмент)
**Что делает:** Объясняет вклад каждой метрики в каждое предсказание

**Когда использовать:** Глубокое понимание — почему модель решила так

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Summary plot — общая важность
shap.summary_plot(shap_values, X_test)

# Dependence plot — как конкретная метрика влияет
shap.dependence_plot('lag', shap_values, X_test)
```

**Что покажет:**
- Какие метрики важны глобально
- Как именно метрика влияет (линейно, нелинейно, с порогом)
- Взаимодействия между метриками

---

### 2.3 Permutation Importance
**Что делает:** Измеряет падение качества при "сломанной" метрике

**Когда использовать:** Проверить реальную важность (не переобученную)

```python
from sklearn.inspection import permutation_importance

result = permutation_importance(model, X_test, y_test, n_repeats=10)

importance = pd.DataFrame({
    'feature': X_test.columns,
    'importance': result.importances_mean
}).sort_values('importance', ascending=False)
```

**Что покажет:**
- Если importance ~ 0 — метрика не нужна модели
- Если importance < 0 — метрика вредит (шум)

---

## 3. СТАТИСТИЧЕСКИЕ ТЕСТЫ

### 3.1 Mutual Information
**Что делает:** Измеряет любую (не только линейную) зависимость

**Когда использовать:** Найти нелинейные связи которые корреляция пропускает

```python
from sklearn.feature_selection import mutual_info_classif

mi = mutual_info_classif(X, y)
importance = pd.DataFrame({
    'feature': X.columns,
    'mutual_info': mi
}).sort_values('mutual_info', ascending=False)
```

**Что покажет:**
- Высокий MI + низкая корреляция = нелинейная связь (интересно!)
- Низкий MI = метрика не несёт информации о target

---

### 3.2 Granger Causality Test
**Что делает:** Проверяет, предсказывает ли X будущее Y

**Когда использовать:** Формально доказать что метрика предсказывает

```python
from statsmodels.tsa.stattools import grangercausalitytests

# Тест: предсказывает ли lag будущий ret1s?
result = grangercausalitytests(df[['binance_ret1s_x100', 'lag']].dropna(), maxlag=10)
```

**Что покажет:**
- p-value < 0.05 — метрика статистически значимо предсказывает target
- Оптимальный лаг предсказания

---

### 3.3 T-Test / Mann-Whitney U
**Что делает:** Сравнивает метрику между двумя группами (например UP выиграл vs DOWN выиграл)

**Когда использовать:** Проверить отличается ли метрика для разных исходов

```python
from scipy.stats import mannwhitneyu

up_wins = df[df['outcome'] == 'UP']['lag']
down_wins = df[df['outcome'] == 'DOWN']['lag']

stat, p_value = mannwhitneyu(up_wins, down_wins)
print(f"p-value: {p_value:.4f}")
```

**Что покажет:**
- p-value < 0.05 — метрика значимо отличается между группами (полезна)
- p-value > 0.05 — нет разницы (бесполезна для классификации)

---

## 4. ВИЗУАЛИЗАЦИЯ

### 4.1 Pair Plot
**Что делает:** Показывает scatter plots всех пар метрик с раскраской по target

**Когда использовать:** Увидеть кластеры и разделимость классов

```python
import seaborn as sns

sns.pairplot(df[['lag', 'pm_up_imbalance', 'binance_ret1s_x100', 'target']],
             hue='target', diag_kind='kde')
```

**Что покажет:**
- Если классы разделяются — метрика полезна
- Если перемешаны — метрика бесполезна

---

### 4.2 Distribution by Outcome
**Что делает:** Показывает распределение метрики для разных исходов

**Когда использовать:** Понять как метрика ведёт себя в разных ситуациях

```python
import plotly.express as px

fig = px.histogram(df, x='lag', color='outcome',
                   marginal='box', barmode='overlay')
fig.show()
```

**Что покажет:**
- Разные распределения = метрика различает исходы
- Одинаковые = метрика не помогает

---

### 4.3 Time Series Decomposition
**Что делает:** Разделяет метрику на тренд, сезонность, шум

**Когда использовать:** Понять структуру метрики

```python
from statsmodels.tsa.seasonal import seasonal_decompose

result = seasonal_decompose(df['lag'].dropna(), period=100)
result.plot()
```

**Что покажет:**
- Есть ли тренд в метрике
- Есть ли периодичность
- Какая доля шума

---

## 5. ОТБОР ПРИЗНАКОВ (Feature Selection)

### 5.1 Recursive Feature Elimination (RFE)
**Что делает:** Итеративно убирает худшие метрики

**Когда использовать:** Найти минимальный набор важных метрик

```python
from sklearn.feature_selection import RFE
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier()
rfe = RFE(model, n_features_to_select=10)
rfe.fit(X, y)

selected = X.columns[rfe.support_]
print("Выбранные метрики:", list(selected))
```

**Что покажет:**
- Минимальный набор метрик для хорошего предсказания
- Какие метрики избыточны

---

### 5.2 Boruta
**Что делает:** Сравнивает метрики с "теневыми" случайными версиями

**Когда использовать:** Строгий отбор — отсеять всё что не лучше случайности

```python
from boruta import BorutaPy
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_jobs=-1)
boruta = BorutaPy(rf, n_estimators='auto', verbose=2)
boruta.fit(X.values, y.values)

selected = X.columns[boruta.support_]
print("Подтверждённые метрики:", list(selected))
```

**Что покажет:**
- Confirmed — точно важные
- Tentative — возможно важные
- Rejected — шум

---

## 6. КЛАСТЕРИЗАЦИЯ МЕТРИК

### 6.1 Hierarchical Clustering
**Что делает:** Группирует похожие метрики в кластеры

**Когда использовать:** Найти дублирующиеся метрики

```python
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

corr = df[feature_cols].corr()
distance = 1 - abs(corr)
linkage_matrix = linkage(squareform(distance), method='average')

dendrogram(linkage_matrix, labels=feature_cols, leaf_rotation=90)
```

**Что покажет:**
- Кластеры похожих метрик — можно оставить одну из каждого
- Изолированные метрики — уникальная информация

---

## РЕКОМЕНДУЕМЫЙ ПОРЯДОК

| Шаг | Инструмент | Цель |
|-----|------------|------|
| 1 | Correlation Matrix | Быстрый обзор связей |
| 2 | Distribution by Outcome | Визуально понять разницу |
| 3 | Mutual Information | Найти нелинейные связи |
| 4 | Random Forest Importance | Первичный отбор |
| 5 | SHAP Values | Глубокое понимание |
| 6 | Lagged Correlation | Найти предсказательные метрики |
| 7 | Granger Causality | Формально подтвердить |
| 8 | RFE или Boruta | Финальный отбор |

---

## БЫСТРЫЙ СТАРТ

Минимальный набор для начала:

```python
# 1. Корреляция с target
print(df.corr()['target'].sort_values(ascending=False))

# 2. Random Forest importance
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(n_estimators=100)
rf.fit(X, y)
print(pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False).head(15))

# 3. SHAP для топ-модели
import shap
explainer = shap.TreeExplainer(rf)
shap.summary_plot(explainer.shap_values(X), X)
```

Этих трёх шагов достаточно чтобы понять какие метрики важны.

---

## БИБЛИОТЕКИ ДЛЯ УСТАНОВКИ

```bash
pip install pandas numpy scipy scikit-learn shap boruta statsmodels seaborn plotly
```
