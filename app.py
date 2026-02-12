"""
xDaimon FastScan - Main Dash Application
Главный файл приложения для визуализации стакана ордеров Polymarket
Поддержка multi-window режима через query параметр ?view=
"""

from flask import request
from dash import Dash
from src.layout import create_root_layout
from src.callbacks import register_callbacks


def create_app():
    """Создать и настроить Dash приложение"""
    app = Dash(
        __name__,
        suppress_callback_exceptions=True  # Нужно для динамических layouts
    )
    app.title = "xDaimon FastScan"

    # Корневой layout с dcc.Location и content-container
    app.layout = create_root_layout

    # Регистрируем callbacks
    register_callbacks(app)

    return app


def main():
    """Точка входа в приложение"""
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=8050)


if __name__ == '__main__':
    main()
