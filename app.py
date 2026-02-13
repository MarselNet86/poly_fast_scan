"""
xDaimon FastScan - Main Dash Application
Главный файл приложения для визуализации стакана ордеров Polymarket
"""

from dash import Dash
from src.layout import create_main_layout
from src.callbacks import register_callbacks


def create_app():
    """Создать и настроить Dash приложение"""
    app = Dash(__name__)
    app.title = "xDaimon FastScan"

    # Главный layout
    app.layout = create_main_layout

    # Регистрируем callbacks
    register_callbacks(app)

    return app


def main():
    """Точка входа в приложение"""
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=8050)


if __name__ == '__main__':
    main()
