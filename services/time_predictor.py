"""
Time-Based Predictor: Предсказание по первым 11 минутам.

Использование:
    python services/time_predictor.py --all
    python services/time_predictor.py --file files/btc-updown-15m-1967869.csv
"""

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split

warnings.filterwarnings('ignore')

# ============================================================================
# ТЕРМИНАЛ: Динамический вывод
# ============================================================================

class Terminal:
    """Утилиты для динамического терминала."""

    CLEAR_LINE = '\033[2K'
    MOVE_UP = '\033[1A'
    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def clear_line():
        sys.stdout.write(Terminal.CLEAR_LINE + '\r')
        sys.stdout.flush()

    @staticmethod
    def progress(current: int, total: int, prefix: str = '', width: int = 30):
        """Отображает progress bar с динамическим обновлением."""
        pct = current / total
        filled = int(width * pct)
        bar = '█' * filled + '░' * (width - filled)
        # Очищаем строку и выводим progress
        sys.stdout.write(f'\r\033[K{prefix} [{bar}] {current}/{total} ({pct*100:.0f}%)')
        sys.stdout.flush()
        # Переход на новую строку только в конце
        if current == total:
            sys.stdout.write('\n')
            sys.stdout.flush()

    @staticmethod
    def done(msg: str):
        print(f'{Terminal.GREEN}✓{Terminal.RESET} {msg}')

    @staticmethod
    def info(msg: str):
        print(f'{Terminal.BLUE}ℹ{Terminal.RESET} {msg}')

    @staticmethod
    def warn(msg: str):
        print(f'{Terminal.YELLOW}⚠{Terminal.RESET} {msg}')

    @staticmethod
    def error(msg: str):
        print(f'{Terminal.RED}✗{Terminal.RESET} {msg}')

    @staticmethod
    def header(msg: str):
        print(f'\n{Terminal.BOLD}{msg}{Terminal.RESET}')

    @staticmethod
    def metric(name: str, value: float, good_threshold: float = 0.6):
        color = Terminal.GREEN if value >= good_threshold else Terminal.YELLOW
        print(f'  {name}: {color}{value:.4f}{Terminal.RESET}')


# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

EXCLUDE_COLUMNS = [
    'market_slug', 'timestamp_ms', 'timestamp_et',
    'time_till_end', 'seconds_till_end',
    'down_ask_1_price', 'up_ask_1_price',
    'pm_up_microprice', 'pm_down_microprice',
]

# Колонки orderbook исключаем
ORDERBOOK_PATTERNS = ['_bid_', '_ask_']

MODEL_PARAMS = {
    'n_estimators': 300,
    'max_depth': 4,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.5,
    'reg_lambda': 2.0,
    'min_child_weight': 5,
    'random_state': 42,
    'n_jobs': -1,
    'verbosity': 0,
}


# ============================================================================
# ОБРАБОТКА ДАННЫХ
# ============================================================================

def get_feature_columns(df: pd.DataFrame) -> list:
    """Возвращает список фичей для анализа."""
    cols = []
    for col in df.columns:
        if col in EXCLUDE_COLUMNS:
            continue
        if any(p in col for p in ORDERBOOK_PATTERNS):
            continue
        cols.append(col)
    return cols


def process_game(file_path: Path) -> dict | None:
    """Обрабатывает одну игру и возвращает фичи + target."""
    try:
        df = pd.read_csv(file_path)

        # Разделение по времени
        first_11_min = df[df['seconds_till_end'] > 240]

        if len(first_11_min) < 100:
            return None

        # Фичи
        feature_cols = get_feature_columns(df)
        features = {}

        for col in feature_cols:
            data = first_11_min[col].dropna()
            if len(data) == 0:
                continue
            features[f'{col}_last'] = data.iloc[-1]
            features[f'{col}_mean'] = data.mean()
            features[f'{col}_std'] = data.std() if len(data) > 1 else 0

        # Target: победитель в финале
        last_row = df.iloc[-1]
        down_price = last_row.get('down_ask_1_price', 0)
        up_price = last_row.get('up_ask_1_price', 0)

        if pd.isna(down_price) or pd.isna(up_price):
            # Если нет цены - определяем по последней валидной
            valid_rows = df.dropna(subset=['down_ask_1_price', 'up_ask_1_price'])
            if len(valid_rows) == 0:
                return None
            last_valid = valid_rows.iloc[-1]
            down_price = last_valid['down_ask_1_price']
            up_price = last_valid['up_ask_1_price']

        target = 1 if down_price > up_price else 0

        return {
            'slug': file_path.stem,
            'features': features,
            'target': target,
        }
    except Exception:
        return None


def load_all_games(files_dir: Path, pattern: str = 'btc-updown-*.csv') -> tuple:
    """Загружает и обрабатывает все игры."""
    files = sorted(files_dir.glob(pattern))
    files = [f for f in files if 'test' not in f.name]

    games = []
    Terminal.header(f'Загрузка {len(files)} файлов...')

    for i, f in enumerate(files):
        Terminal.progress(i + 1, len(files), 'Обработка')
        result = process_game(f)
        if result:
            games.append(result)

    Terminal.done(f'Загружено {len(games)} игр')

    # Собираем DataFrame
    if not games:
        return None, None, None

    feature_dicts = [g['features'] for g in games]
    X = pd.DataFrame(feature_dicts).fillna(0)
    y = pd.Series([g['target'] for g in games])
    slugs = [g['slug'] for g in games]

    return X, y, slugs


# ============================================================================
# ОБУЧЕНИЕ И ОЦЕНКА
# ============================================================================

def train_and_evaluate(X: pd.DataFrame, y: pd.Series) -> dict:
    """Обучает модель и возвращает результаты."""

    Terminal.header('Обучение модели...')

    # Статистика
    down_wins = (y == 1).sum()
    up_wins = (y == 0).sum()
    scale_pos_weight = up_wins / down_wins if down_wins > 0 else 1.0

    Terminal.info(f'DOWN: {down_wins}, UP: {up_wins}, scale_pos_weight: {scale_pos_weight:.2f}')

    # Кросс-валидация
    model = xgb.XGBClassifier(**MODEL_PARAMS, scale_pos_weight=scale_pos_weight)

    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    Terminal.info(f'CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}')

    # Финальное обучение
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model.fit(X_train, y_train)

    # Метрики
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    results = {
        'model': model,
        'X_test': X_test,
        'y_test': y_test,
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_proba) if len(set(y_test)) > 1 else 0,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
    }

    Terminal.header('Результаты:')
    Terminal.metric('Accuracy', results['accuracy'])
    Terminal.metric('F1 Score', results['f1'], 0.5)
    Terminal.metric('ROC-AUC', results['roc_auc'], 0.6)

    return results


def compute_feature_importance(model, X: pd.DataFrame, output_dir: Path):
    """Вычисляет SHAP и сохраняет важность фичей."""

    Terminal.header('SHAP анализ...')

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)

    # Feature importance
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': np.abs(shap_values.values).mean(axis=0)
    }).sort_values('importance', ascending=False)

    # Сохраняем
    output_dir.mkdir(parents=True, exist_ok=True)
    importance.to_csv(output_dir / 'feature_importance.csv', index=False)

    # Топ-10
    Terminal.header('Топ-10 фичей:')
    for _, row in importance.head(10).iterrows():
        print(f'  {row["feature"][:40]:40s} {row["importance"]:.6f}')

    Terminal.done(f'Сохранено: {output_dir}/feature_importance.csv')

    return importance


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Time-Based Predictor')
    parser.add_argument('--all', action='store_true', help='Обработать все файлы')
    parser.add_argument('--file', type=str, help='Один файл')
    parser.add_argument('--pattern', type=str, default='btc-updown-*.csv')
    args = parser.parse_args()

    print(f'\n{Terminal.BOLD}═══ Time-Based Predictor ═══{Terminal.RESET}')
    print('Анализ: первые 11 мин → предсказание исхода\n')

    # Загрузка данных
    files_dir = Path(__file__).parent.parent / 'files'
    X, y, slugs = load_all_games(files_dir, args.pattern)

    if X is None or len(X) < 10:
        Terminal.error('Недостаточно данных для обучения')
        return

    Terminal.info(f'Размер данных: {X.shape[0]} игр, {X.shape[1]} фичей')

    # Обучение
    results = train_and_evaluate(X, y)

    # SHAP
    output_dir = Path(__file__).parent / 'results' / 'time_predictor'
    compute_feature_importance(results['model'], results['X_test'], output_dir)

    print(f'\n{Terminal.BOLD}═══ Готово ═══{Terminal.RESET}\n')


if __name__ == '__main__':
    main()
