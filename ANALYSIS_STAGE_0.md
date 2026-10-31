# Анализ проекта Investing Demo (этап 0 —熟�ление)

**Дата:** 2026-10-30  
**Статус:** проект изучен, ожидание задания первого этапа

## 1. Назначение приложения и технологический стек

Приложение **Investing Demo** — веб-сервис на Python/Django для отслеживания акций и их рыночных цен с использованием Tinkoff Invest API.

**Стек:**
- Python, Django 4.1.7
- Django REST Framework 3.14.0, django-filter 22.1
- Celery 5.2.7 + Redis (брокер задач)
- PostgreSQL (docker-compose)
- Tinkoff Invest API (`tinkoff-investments==0.2.0b50`, `tinkoff==0.1.1`)
- Plotly 5.13.1 (графики котировок)
- crispy-forms / crispy-bootstrap3 (Bootstrap 3 формы)
- `psycopg2-binary`, `grpcio`, `protobuf`, `tenacity`, `pydantic` и др.

## 2. Структура проекта и компоненты

| Компонент | Назначение |
|-----------|------------|
| `config/` | Настройки Django, Celery, URL-конфигурация, WSGI/ASGI |
| `dashboard/models.py` | Модель `Share` (акция) |
| `dashboard/views.py` | Классовые представления: список, деталь, создание, редактирование, удаление акций |
| `dashboard/urls.py` | Маршруты веб-интерфейса и подключение API |
| `dashboard/forms.py` | `ShareModelForm` (все поля модели) |
| `dashboard/admin.py` | Регистрация `Share` в админке Django |
| `dashboard/services/market_data.py` | Получение последней цены через Tinkoff Invest API |
| `dashboard/services/graph.py` | Построение графика исторических свечей через Plotly |
| `dashboard/tasks.py` | Celery-задача `update_last_price` (обновление цен акций) |
| `dashboard/api/v1/` | DRF ViewSet, сериализатор, фильтры, роутер для `/api/v1/shares/` |
| `dashboard/tests.py` | API-тесты (APITestCase) для акций |
| `dashboard/management/commands/add_shares.py` | Команда импорта акций из Tinkoff Invest API в БД |
| `user/` | Аутентификация: регистрация, вход, выход (кастомная модель пользователя по email) |
| `docker-compose.yml` | PostgreSQL + Redis |
| `requirements.txt` | Зависимости Python |
| `manage.py` | Точка входа Django |

## 3. Архитектура и взаимодействие компонентов

- **Веб-интерфейс:** `ShareListView` → список акций; `ShareDetailView` → деталь с графиком Plotly; `ShareCreateView`/`ShareUpdateView`/`ShareDeleteView` → CRUD (доступно только_authenticated).
- **API:** `ShareViewSet` (ModelViewSet) на `/api/v1/shares/` с фильтрацией по `name`/`ticker`, поиском и сортировкой.
- **Обновление цен:** Celery Beat запускает `update_last_price` каждые 10 секунд (в коде указано 10.0, комментарий "add-every-5-min"). Задача обходит все `Share`, запрашивает цену через `get_last_data`, определяет тренд (`is_trend_high`) и обновляет запись.
- **Импорт акций:** команда `add_shares` загружает инструменты из Tinkoff Invest API через `client.instruments.shares()` и создаёт `Share` через `get_or_create`.
- **Пользователи:** регистрация/авторизация по email+пароль, сессии Django, защита CRUD-операций через `IsUserAuthenticatedMixin`.

## 4. Модель данных (Share)

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | BigAutoField | PK | Идентификатор |
| figi | CharField(255) | unique | FIGI инструмента |
| isin | CharField(255) | — | ISIN |
| name | CharField(255) | verbose_name="Наименование компании" | Название |
| ticker | CharField(10) | unique | Тикер |
| currency | CharField(20) | verbose_name="Валюта" | Валюта |
| uid | CharField(255) | unique | UID инструмента |
| last_price | FloatField | blank, null | Текущая цена |
| is_trend_high | BooleanField | blank, null | Растет цена |
| updated_at | DateTimeField | auto_now | Время обновления |

Миграции: `0001`…`0007` (создание, уникальность figi/ticker, uid, last_price/is_trend_high, verbose_name, updated_at).

## 5. Выявленные проблемы и ограничения (предварительные)

- `TINKOFF_TOKEN = ""` в настройках — токен не заполнен, внешние вызовы к Tinkoff API не будут работать.
- База данных настроена на PostgreSQL (`localhost:5432`); без запущенного контейнера `docker-compose` приложение не поднимется.
- `SECRET_KEY = ""` — пустой секретный ключ Django.
- В `market_data.py`: `resp.last_prices.pop()` — предположение, что список не пуст; отсутствует обработка пустого ответа.
- В `tasks.py`: `if share.last_price > last_price` — при `last_price=None` возникнет `TypeError`, ловится в общем `except` и выставляется `is_trend_high=True`.
- В `views.py` `ShareDetailView.get` использует `Share.objects.get(id=pk)` без `get_object_or_404` —可能 приведет к 500 при несуществующем pk.
- В `user/views.py` `RegistrationView.post` обращается к `form.errors["__all__"].data[0].message` — возможен IndexError при отсутствии ошибок `__all__`.
- API-тесты используют `status` из `rest_framework`, но импортирован `reverse` из `django.urls` — должен работать.
- Миграция `0004_add_last_price` содержит очевидные ошибки: `verbose_name="Валюта"` для `name`, `verbose_name="Ти"` для `ticker` (исправлено в `0005`/`0006`).

## 6. Команды, использованные на этом этапе

- `working_directory` — переход в `D:\Vibecode\aidd-topic03-homework`
- `glob` — полный список файлов проекта
- `read` — ознакомление со всеми ключевыми файлами проекта (см. список выше)

Следующий шаг — выполнение задания этапа №1 после вашей команды.