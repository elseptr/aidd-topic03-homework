# ANALYSIS.md — Investing Demo

**Автор анализа:** NVIDIA Nemotron 3.5 Super VL (free)  
**Дата:** 2026-10-30 … 2026-10-31  
**Проект:** Investing Demo (Python / Django)  
**Статус:** анализ завершён; дефекты работоспособности устранены; приложение успешно запускается

---

## 1. Назначение приложения и технологический стек

### 1.1 Назначение

**Investing Demo** — веб-приложение для учёта акций, просмотра рыночных котировок и графиков, с последующим расширением до персональных списков наблюдения, ценовых уведомлений, виртуального инвестиционного портфеля, хранения истории цен и симуляции торговых стратегий.

Рыночные данные рассчитаны на **T-Invest API** (официальный Python SDK). При отсутствии токена или пакета SDK приложение **не падает**: используется демонстрационный источник цен и свечей, чтобы UI, API и фоновые сценарии оставались работоспособными.

### 1.2 Технологический стек (актуальное состояние после исправлений)

| Слой | Технологии |
|------|------------|
| Язык | Python 3.8+ |
| Web-фреймворк | Django 4.2.x (LTS) |
| REST API | Django REST Framework, django-filter |
| UI | Django Templates, Bootstrap 3, django-crispy-forms, crispy-bootstrap3 |
| Фоновые задачи | Celery 5.x, брокер Redis |
| БД по умолчанию | **SQLite** (`db.sqlite3`) — для запуска без Docker |
| БД (опционально) | PostgreSQL при `USE_POSTGRES=1` (docker-compose) |
| Рыночные данные | Official SDK **`t-tech-investments`**, импорт `from t_tech.invest import Client` |
| Графики | Plotly |
| Прочее | tenacity, cachetools; grpcio/protobuf — транзитивно от SDK |

**Установка SDK (актуально на 2025–2026):**

```bash
pip install t-tech-investments \
  --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
```

При ошибках SSL допускается `--trusted-host opensource.tbank.ru`.  
Устаревшие пакеты `tinkoff` / `tinkoff-investments` в рабочем `requirements.txt` **не используются** как обязательные runtime-зависимости.

---

## 2. Структура проекта и назначение компонентов

```
config/                     # Конфигурация Django и Celery
  settings.py               # SECRET_KEY, DB, REST, Celery, TINKOFF_TOKEN из env
  urls.py                   # admin, dashboard, user/
  celery.py                 # beat_schedule
  wsgi.py / asgi.py
dashboard/                  # Домен «акции и инвестиции»
  models.py                 # Share + watchlist/portfolio/history (после расширения)
  views.py                  # CBV: список, деталь, CRUD, watchlists, portfolios, …
  forms.py                  # Share, Watchlist, PriceAlert, Portfolio
  services/
    market_data.py          # last price (API или demo)
    graph.py                # Plotly-график (API или demo)
    demo_market_data.py     # синтетические цены/свечи
    watchlist_service.py    # списки, алерты, уведомления
    portfolio_service.py    # buy/sell, P&L
    price_history_service.py# история + StrategySimulatorService
  tasks.py                  # update_last_price, update_price_history
  api/v1/                   # ShareViewSet, serializer, router
  management/commands/add_shares.py
  templates/dashboard/
  admin.py, tests.py, urls.py
user/                       # Регистрация / вход / выход по email
docker-compose.yml          # postgres + redis (опционально)
manage.py
requirements.txt
```

---

## 3. Архитектура и взаимодействие компонентов

```
Клиент (браузер / API)
    │
    ▼
config.urls ──► dashboard.urls / user.urls
    │
    ▼
Class-Based Views ──► ORM Models ──► SQLite / PostgreSQL
    │                      ▲
    └── services.* ────────┤
              │            │
              ├── t_tech.invest.Client  (если токен и пакет есть)
              └── demo_market_data      (fallback)

Celery Beat ──► Redis ──► Celery Worker ──► tasks.update_last_price
                                      └──► tasks.update_price_history
```

**Потоки:**

1. **Список/деталь акций** — views → `Share` → при детали `get_graph(share)`.  
2. **CRUD акций** — только для аутентифицированных (`IsUserAuthenticatedMixin` → редирект на login).  
3. **API** — `/api/v1/shares/` → `ShareViewSet` (pagination, filter, search, ordering).  
4. **Auth** — email как username, сессии Django.  
5. **Фон** — обновление `last_price` / тренда; проверка price alerts; запись `PriceHistory`.  
6. **Импорт инструментов** — `manage.py add_shares` (API или demo-seed).

---

## 4. Модель данных

### 4.1 Базовая сущность

**Share**

| Поле | Тип / ограничения |
|------|-------------------|
| figi | CharField, unique |
| isin | CharField |
| name | CharField |
| ticker | CharField, unique, max_length=10 |
| currency | CharField |
| uid | CharField, unique |
| last_price | FloatField, null/blank |
| is_trend_high | BooleanField, null/blank |
| updated_at | DateTimeField, auto_now |

### 4.2 Пользователь

Стандартная модель Django (`get_user_model()`). При регистрации: `create_user(email, email, password)` — email используется и как username, и как email.

### 4.3 Расширение (новая функциональность)

| Модель | Связи | Назначение |
|--------|-------|------------|
| Watchlist | FK → User | Список наблюдения |
| WatchlistItem | FK → Watchlist, Share; unique_together | Акция в списке |
| PriceAlert | FK → User, Share; above/below | Целевой уровень |
| Notification | FK → User | Уведомление |
| Portfolio | FK → User | Виртуальный портфель |
| PortfolioPosition | FK → Portfolio, Share | Кол-во, средняя цена |
| PortfolioTransaction | FK → Portfolio, Share | История buy/sell |
| PriceHistory | FK → Share; индекс (share, −timestamp) | Исторические цены |

Миграции: `0001`…`0007` (Share), `0008_new_features` (новые сущности).

---

## 5. Обработка запросов и взаимодействие с БД

| Сценарий | Механизм |
|----------|----------|
| GET `/` | `ShareListView`, paginate_by=100, ordering по name |
| GET `/<pk>` | `ShareDetailView` + `get_object_or_404` + `get_graph` |
| Create/Update/Delete Share | CBV + `IsUserAuthenticatedMixin` + `ShareModelForm` |
| `/api/v1/shares/` | DRF ModelViewSet, LimitOffsetPagination (100), DjangoFilterBackend |
| `/user/login/`, `/user/registration/`, `/user/logout/` | AuthView, RegistrationView, LogoutView |
| Watchlists / Alerts / Portfolios / Notifications | отдельные CBV и URL под `dashboard` |
| Persist | Django ORM; транзакции на уровне сервисов портфеля |

Все чтения/записи доменных данных идут через модели; прямых SQL в views нет.

---

## 6. Восстановленные функциональные требования

Ниже — **фактически реализованное** поведение. Дефекты реализации требованиями не являются (они исправлены — см. §8).

### FR-01. Веб-интерфейс
Приложение предоставляет страницы на Django Templates (список и деталь акций, формы CRUD, auth).  
**Подтверждение:** `config/urls.py`, `dashboard/urls.py`, `user/urls.py`, шаблоны `dashboard/templates`, `user/templates`.

### FR-02. REST API акций
Эндпоинт `/api/v1/shares/` поддерживает list/retrieve/create/update/delete, фильтры `name`/`ticker`, search, ordering, пагинацию.  
**Подтверждение:** `dashboard/api/v1/views.py`, `serializer.py`, `router.py`, `REST_FRAMEWORK` в settings.

### FR-03. Реляционное хранение
Данные хранятся в БД. По умолчанию SQLite; PostgreSQL включается переменной окружения `USE_POSTGRES=1`.  
**Подтверждение:** `config/settings.py` (`DATABASES`), `docker-compose.yml`.

### FR-04. Фоновые задачи
Celery с брокером Redis выполняет периодическое обновление цен (и истории).  
**Подтверждение:** `CELERY_*` в settings, `config/celery.py`, `dashboard/tasks.py`.

### FR-05. Сущность «Акция»
Поля и unique-ограничения Share — как в §4.1.  
**Подтверждение:** `dashboard/models.py`, миграции 0001–0007.

### FR-06. Аутентификация по email
Регистрация и вход по email и паролю; email = username.  
**Подтверждение:** `user/forms.py`, `user/views.py`.

### FR-07. Список акций
Пагинация 100, сортировка по названию, отображение цены и тренда.  
**Подтверждение:** `ShareListView`, `list.html`.

### FR-08. Деталь с графиком
Карточка акции и Plotly-график ~180 дневных точек (реальные свечи или demo).  
**Подтверждение:** `ShareDetailView`, `services/graph.py`, `detail.html`.

### FR-09–FR-11. CRUD акций для авторизованных
Создание, редактирование, удаление доступны только `is_authenticated`; иначе редирект на login.  
**Подтверждение:** `ShareCreateView` / `UpdateView` / `DeleteView`, `IsUserAuthenticatedMixin`.

### FR-12. Импорт акций
`python manage.py add_shares` загружает инструменты из API либо сеет demo-набор без токена.  
**Подтверждение:** `management/commands/add_shares.py`.

### FR-13. Обновление цен
Задача обходит Share, получает last price, обновляет `last_price` и `is_trend_high`, при наличии алертов создаёт Notification с защитой от частых дублей.  
**Подтверждение:** `tasks.update_last_price`, `get_last_data`, `PriceAlertService`.

### FR-14. Регистрация
Проверка совпадения паролей и уникальности email; после успеха — login и redirect на index.  
**Подтверждение:** `RegistrationForm.clean/save`, `RegistrationView`.

### FR-15. Вход
Email + password → session; сообщение об ошибке при неверных данных.  
**Подтверждение:** `AuthView`, `AuthForm`.

### FR-16. Выход
Logout и redirect на index.  
**Подтверждение:** `LogoutView`.

### FR-17. Защита изменяющих операций
Неаутентифицированный пользователь не выполняет create/update/delete акций.  
**Подтверждение:** `IsUserAuthenticatedMixin`.

### FR новой функциональности (кратко)

| ID | Поведение |
|----|-----------|
| FR-N1 | Пользователь создаёт watchlists, добавляет/удаляет акции |
| FR-N2 | Пользователь задаёт PriceAlert (above/below); при обновлении цены создаётся Notification; повтор не чаще ~1 раза в час |
| FR-N3 | Виртуальный портфель: buy/sell, средняя цена, стоимость, P&L, история транзакций |
| FR-N4 | PriceHistory сохраняется в БД; выборка по периоду; графики на накопленных/API/demo данных |
| FR-N5 | StrategySimulatorService моделирует сделки по условиям и считает return / max drawdown |

Детали реализации — в коде `dashboard/` (models, services, views, templates).

---

## 7. Неоднозначности (исторические, из исходного кода)

| ID | Суть | Статус после работы |
|----|------|---------------------|
| NC-01 | Комментарий «every-5-min» vs `schedule: 10.0` сек | Зафиксировано; интервал оставлен 10.0 как в коде |
| NC-02 | Пустой токен в исходнике | Токен только из env; без него — demo |
| NC-03 | detail через `.get()` → 500 | **Исправлено:** `get_object_or_404` |

---

## 8. Дефекты, которые были в исходнике, и что сделано

| ID | Проблема | Решение |
|----|----------|---------|
| DF-01 | Пустой `SECRET_KEY` | Дефолтный dev-ключ + `DJANGO_SECRET_KEY` из env |
| DF-02 | Пустой `TINKOFF_TOKEN` | Env; demo fallback при пустом токене/ошибке API |
| DF-03 | `ALLOWED_HOSTS = []` | `localhost,127.0.0.1` из env по умолчанию |
| DF-04 | `last_prices.pop()` / пустой ответ API | Проверка пустого списка; безопасный возврат |
| DF-05 | Сравнение с `last_price is None` | Явная проверка перед сравнением |
| DF-06 | 500 на несуществующий pk | `get_object_or_404` |
| DF-07–08 | Небезопасный разбор form / errors | `cleaned_data`, безопасный `.get()` |
| DF-09 | Цена только `units` без `nano` | `Decimal` с учётом nano |
| — | Устаревший pip-пакет Tinkoff | Переход на `t-tech-investments` / `t_tech.invest` |
| — | Только PostgreSQL → нет запуска без Docker | SQLite по умолчанию |
| — | Eager-import сервисов ломал bootstrap | Импорты по месту использования |
| — | `manage.py` / URL `user` без `/` | Исправлены |

### Подтверждение запуска (обязательный критерий модернизации)

| Команда / запрос | Результат |
|------------------|-----------|
| `python manage.py check` | no issues |
| `python manage.py migrate` | OK |
| `GET /` | 200 |
| `GET /api/v1/shares/` | 200 JSON |
| `GET /user/login/` | 200 |
| Login POST | 302 → `/` |
| Share detail | 200 (в т.ч. demo-график) |

Приложение **работоспособно** без Docker и без брокерского токена; при наличии токена и SDK используются реальные котировки.

---

## 9. Зависимости (рабочий профиль)

Минимальный набор для запуска UI/API:

- Django 4.2.x, djangorestframework, django-filter  
- django-crispy-forms, crispy-bootstrap3  
- plotly  
- celery, redis (нужны только для фона)  
- psycopg2-binary (только если PostgreSQL)  
- **отдельно:** `t-tech-investments` с index-url T-Bank Open Source  

Полный список и комментарии — в `requirements.txt` проекта.

---

## 10. Заключение

Выполнен полный анализ исходного кода Investing Demo: определены назначение, стек, структура, архитектура, модель данных и механизмы обработки запросов. Восстановлены функциональные требования FR-01…FR-17 и требования к новой функциональности с привязкой к коду.

Обнаруженные дефекты, блокировавшие запуск (конфигурация, SDK, bootstrap, обработка API/форм), **устранены**. Критерий успешного запуска подтверждён командами `check` / `migrate` / `runserver` и HTTP 200 на ключевых маршрутах.

Дальнейшая эксплуатация с реальными котировками сводится к установке `t-tech-investments` и заданию `TINKOFF_TOKEN`; без них система остаётся в demo-режиме и сохраняет полный UI/API-функционал.

---

*Документ подготовлен NVIDIA Nemotron 3.5 Super VL (free) по результатам анализа кода, восстановления требований, исправления дефектов и проверки запуска.*
