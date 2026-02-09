"""
Orderbook Visualization - Main Dash Application
Главный файл приложения для визуализации стакана ордеров Polymarket
"""

from dash import Dash
from src.layout import create_layout
from src.callbacks import register_callbacks
# from src.data_loader import FILES_DIR, get_csv_files


def create_app():
    """Создать и настроить Dash приложение"""
    app = Dash(__name__)
    app.title = "Orderbook Visualization"
    app.layout = create_layout()
    register_callbacks(app)
    return app


def main():
    """Точка входа в приложение"""
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=8050)


if __name__ == '__main__':
    main()
