# ANALYSIS.md — Investing Demo (результаты работы AI Coding Agent «Cline»)

## 1. Анализ исходного кода (Задание №1)

### 1.1. Назначение и стек
Демо-приложение мониторинга акций с интеграцией Tinkoff Invest API: список, детали + график, CRUD (auth), REST API, Celery-обновление цен.

Стек: Django 4.x, DRF, django-filter, crispy-forms + bootstrap3, Plotly, Celery, tinkoff.invest (опционально). Исходно PostgreSQL + Redis; после модернизации — SQLite + memory broker.

### 1.2–1.3. Структура и архитектура
config/ (settings, urls, celery), dashboard/ (models Share, views CBV, services/graph+market_data, tasks, api/v1 ViewSet, templates, management/add_shares), user/ (восстановлен).

HTTP → urls → CBV/API; Celery task update_last_price; get_graph → Plotly.

### 1.4–1.6. Зависимости, модель, запросы
Зависимости: Django, DRF, filter, crispy, plotly, celery, (tinkoff).

Модель Share: figi/isin/name/ticker/currency/uid (unique), last_price, is_trend_high, updated_at.

Запросы: ListView/DetailView/Create/Update/Delete + ModelViewSet; ORM update last_price.

## 2. Функциональные требования (Задание №2)

**FR-01** Пагинированный список акций с цветом тренда. (ShareListView, list.html)
**FR-02** Детальная страница + график 180д. (ShareDetailView, get_graph)
**FR-03** CRUD акций для authenticated. (Create/Update/Delete + mixin)
**FR-04** REST /api/v1/shares/ CRUD + filter/search/order/pagination. (ShareViewSet)
**FR-05** Периодическое обновление last_price/is_trend_high. (tasks.update_last_price)
**FR-06** Команда add_shares. 
**FR-07** Admin для Share.

**NC-01** Отсутствовало приложение user при ссылках в urls/templates.
**NC-02** Пустые SECRET_KEY / TINKOFF_TOKEN.
**NC-03** Жёсткая зависимость Postgres + Redis.
**NC-04** graph.py не учитывает nano.
**DF-01** Нет manage.py, requirements, user в архиве.
**DF-02** Пустой SECRET_KEY.
**DF-03** Нет fallback без токена.
**DF-04** Опечатка detetime в tasks.
**UR-01** Детали auth (user app отсутствовал).

## 3. Модернизация (Задание №3)
- Добавлены manage.py, requirements.txt, user app.
- SQLite, memory Celery, demo market_data/graph.
- Исправлены опечатки, None-safe тренд.
- Запуск подтверждён: migrate + add_shares + test client (index/api 200, portfolios/watchlists/strategies 200).

## 4. Новая функциональность (Задание №4)

**NFR-01 Watchlist** — списки, target_price + direction, PriceAlert без дублей (last_notified_at + 1h window).
**NFR-02 Portfolio** — cash, buy/sell, avg_price, value, P&L, история транзакций.
**NFR-03 PriceHistory** — автозапись при update, периоды, abs/%, график.
**NFR-04 Strategy** — условия buy/sell, автосделки, журнал, метрики P&L.

Модели + services + views/urls/templates/admin + интеграция в tasks.

## 5. Отчёт агента Cline

**Промпты:** 4 основных (Зад.1–4) + уточнения по окружению.

**Проблемы Cline:** неполный zip → ImportError; disk I/O sqlite в artifacts → /tmp; pip mirror 502 → pypi.org; template dict access → исправлено.

**Итерации:** ~4 основных + 6–8 корректировок, ~1 час.

**Вывод:** Cline удобен для структурированных отчётов и пошагового ТЗ

## Запуск
```
pip install -r requirements.txt
python manage.py migrate
python manage.py add_shares
# admin / admin123
python manage.py runserver
```