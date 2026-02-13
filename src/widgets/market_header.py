"""
Market Header Widget
Информационная панель статуса рынка с индикацией фаз по времени
"""

from dash import html


def get_phase_color(seconds_till_end):
    """
    Определить цвет фона панели по оставшемуся времени

    Args:
        seconds_till_end: секунды до конца рынка

    Returns:
        dict: стили для фона панели
    """
    if seconds_till_end is None or seconds_till_end < 0:
        return {
            'backgroundColor': '#2c2c2c',
            'color': '#888'
        }

    # 🟢 Зелёный (>600s / 10+ мин) — ранняя фаза
    if seconds_till_end > 600:
        return {
            'backgroundColor': '#1e5128',
            'color': '#a7f3d0',
            'phase': 'Ранняя фаза',
            'phaseIcon': '🟢'
        }

    # 🟡 Жёлтый (300–600s / 5–10 мин) — формирование тренда
    elif seconds_till_end > 300:
        return {
            'backgroundColor': '#6b5b11',
            'color': '#fef3c7',
            'phase': 'Основная фаза входа',
            'phaseIcon': '🟡'
        }

    # 🟠 Оранжевый (120–300s / 2–5 мин) — развязка
    elif seconds_till_end > 120:
        return {
            'backgroundColor': '#7c3d00',
            'color': '#fed7aa',
            'phase': 'Развязка — фиксация',
            'phaseIcon': '🟠'
        }

    # 🔴 Красный (<120s / <2 мин) — финал
    elif seconds_till_end > 30:
        return {
            'backgroundColor': '#7f1d1d',
            'color': '#fecaca',
            'phase': 'Финал — экстренный выход',
            'phaseIcon': '🔴'
        }

    # ⚫ Мигающий красный (<30s) — критическая зона
    else:
        return {
            'backgroundColor': '#991b1b',
            'color': '#fef2f2',
            'phase': 'КРИТИЧЕСКАЯ ЗОНА',
            'phaseIcon': '⚠️',
            'animation': 'pulse 0.8s ease-in-out infinite'
        }


def create_market_header():
    """
    Создать информационную панель состояния рынка

    Returns:
        html.Div: компонент панели с динамическим обновлением
    """
    return html.Div([
        # Основной контейнер панели
        html.Div(
            id='market-header-content',
            children=[
                # Левая часть: иконка фазы + название
                html.Div([
                    html.Span(id='phase-icon', style={'fontSize': '24px', 'marginRight': '10px'}),
                    html.Span(id='phase-name', style={'fontSize': '16px', 'fontWeight': 'bold'})
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # Центр: Текущее время ET
                html.Div([
                    html.Span('Время ET: ', style={'opacity': '0.8', 'marginRight': '8px'}),
                    html.Span(id='current-time-et', children='--:--:--',
                             style={'fontSize': '18px', 'fontWeight': 'bold', 'fontFamily': 'monospace'})
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # Правая часть: обратный отсчёт
                html.Div([
                    html.Span('До закрытия: ', style={'opacity': '0.8', 'marginRight': '8px'}),
                    html.Span(id='countdown-display', children='--:--',
                             style={'fontSize': '20px', 'fontWeight': 'bold', 'fontFamily': 'monospace'}),
                    html.Span(id='countdown-seconds', children='(--- сек)',
                             style={'fontSize': '14px', 'marginLeft': '8px', 'opacity': '0.7'})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ],
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'padding': '16px 30px',
                'backgroundColor': '#2c2c2c',
                'color': '#888',
                'borderBottom': '2px solid #444',
                'transition': 'all 0.3s ease'
            }
        )
    ])
