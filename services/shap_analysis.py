"""
SHAP-анализ важности метрик для бинарных опционов.

Использование:
    python src/shap_analysis.py --file files/btc-updown-15m-1967869.csv

Целевая переменная: разница (down_ask_1_price - up_ask_1_price)
- Положительное значение означает тренд к DOWN
- Отрицательное значение означает тренд к UP
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import shap
import xgboost as xgb
from sklearn.model_selection import train_test_split

EXCLUDE_COLUMNS = [
    'market_slug',
    'timestamp_ms',
    'timestamp_et',
    'time_till_end',
    'seconds_till_end',
    # Microprice - очевидная корреляция с ценами
    'pm_up_microprice',
    'pm_down_microprice',
    # Up bid данные - напрямую связаны с up_ask ценами
    'up_bid_1_price', 'up_bid_1_size',
    'up_bid_2_price', 'up_bid_2_size',
    'up_bid_3_price', 'up_bid_3_size',
    'up_bid_4_price', 'up_bid_4_size',
    'up_bid_5_price', 'up_bid_5_size',
    'up_ask_1_price', 'up_ask_1_size',
    'up_ask_2_price', 'up_ask_2_size', 
    'up_ask_3_price', 'up_ask_3_size',
    'up_ask_4_price', 'up_ask_4_size',
    'up_ask_5_price', 'up_ask_5_size',
    'down_bid_1_price', 'down_bid_1_size',
    'down_bid_2_price', 'down_bid_2_size',
    'down_bid_3_price', 'down_bid_3_size',
    'down_bid_4_price', 'down_bid_4_size',
    'down_bid_5_price', 'down_bid_5_size',
    'down_ask_1_price', 'down_ask_1_size',
    'down_ask_2_price', 'down_ask_2_size',
    'down_ask_3_price', 'down_ask_3_size',
    'down_ask_4_price', 'down_ask_4_size',
    'down_ask_5_price', 'down_ask_5_size',
]

TARGET_COLUMNS = ['down_ask_1_price', 'up_ask_1_price']


def extract_slug(file_path: str) -> str:
    """Извлекает slug из имени файла."""
    return Path(file_path).stem


def load_and_prepare_data(file_path: str) -> tuple[pd.DataFrame, pd.Series]:
    """
    Загружает данные и подготавливает фичи и целевую переменную.

    Target: разница (down_ask_1_price - up_ask_1_price)
    - Положительное значение = DOWN побеждает
    - Отрицательное значение = UP побеждает
    """
    df = pd.read_csv(file_path)

    df['target'] = df['down_ask_1_price'] - df['up_ask_1_price']

    exclude_cols = EXCLUDE_COLUMNS + TARGET_COLUMNS + ['target']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_columns].copy()

    X = X.fillna(0)
    y = df['target'].fillna(0)

    valid_mask = y.notna() & (y != 0)
    X = X[valid_mask]
    y = y[valid_mask]

    return X, y


def train_model(X: pd.DataFrame, y: pd.Series) -> tuple[xgb.XGBRegressor, pd.DataFrame, pd.Series]:
    """Обучает XGBoost регрессор и возвращает тестовые данные."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.05,
        random_state=42,

    )

    model.fit(X_train, y_train)

    return model, X_test, y_test 


def compute_shap(model: xgb.XGBRegressor, X_test: pd.DataFrame) -> shap.Explanation:
    """Вычисляет SHAP values с использованием TreeExplainer."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)
    return shap_values


def save_results(
    shap_values: shap.Explanation,
    X_test: pd.DataFrame,
    output_dir: Path,
    slug: str,
) -> None:
    """Сохраняет результаты SHAP-анализа."""
    results_dir = output_dir / slug
    results_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 10))
    shap.plots.bar(shap_values, show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(results_dir / 'shap_bar.png', dpi=150, bbox_inches='tight')
    plt.close()

    mean_shap = pd.DataFrame({
        'feature': X_test.columns,
        'mean_shap_value': abs(shap_values.values).mean(axis=0),
    })
    mean_shap = mean_shap.sort_values('mean_shap_value', ascending=False)
    mean_shap.to_csv(results_dir / 'feature_importance.csv', index=False)

    print(f"Результаты сохранены в: {results_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='SHAP-анализ важности метрик для бинарных опционов'
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Путь к CSV файлу с данными игры',
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Ошибка: файл не найден: {file_path}")
        return

    slug = extract_slug(args.file)
    print(f"Анализ игры: {slug}")

    print("Загрузка данных...")
    X, y = load_and_prepare_data(args.file)
    print(f"Загружено {len(X)} строк, {len(X.columns)} фичей")
    print(f"Target (down-up): mean={y.mean():.4f}, std={y.std():.4f}")

    print("Обучение модели...")
    model, X_test, y_test = train_model(X, y)

    print("Вычисление SHAP values...")
    shap_values = compute_shap(model, X_test)

    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'results'
    save_results(shap_values, X_test, output_dir, slug)

    print("\nТоп-10 важных фичей:")
    mean_shap = pd.DataFrame({
        'feature': X_test.columns,
        'mean_shap_value': abs(shap_values.values).mean(axis=0),
    }).sort_values('mean_shap_value', ascending=False)

    for i, row in mean_shap.head(10).iterrows():
        print(f"  {row['feature']}: {row['mean_shap_value']:.4f}")


if __name__ == '__main__':
    main()
