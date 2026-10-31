# Восстановленные функциональные требования к проекту Investing Demo

**Источник:** исходный код проекта (Python/Django), рабочая директория `D:\Vibecode\aidd-topic03-homework`  
**Дата восстановления:** 2026-10-30  
**Примечание:** описано только то, что faktisch реализовано в коде. Предполагаемое или желаемое поведение не выдаётся за реализованное. Требования, которые невозможно достоверно восстановить из кода, помечены соответствующим образом.

---

## 1. Общие требования

### FR-01. Веб-интерфейс приложения доступен через Django-шаблоны

**Ожидаемое поведение:** Приложение предоставляет веб-интерфейс на базе Django-шаблонов с Bootstrap 3: главная страница со списком акций, страница детальной информации об акции, формы создания, редактирования и удаления акций, а также страницы авторизации и регистрации пользователей.

**Сценарий использования:** Пользователь открывает главную страницу приложения и видит список акций.

**Подтверждение из кода:**
- `config/urls.py` — подключение `dashboard.urls` и `user.urls`
- `dashboard/urls.py` — маршруты `index`, `detail`, `create`, `update`, `delete`, `api/`
- `user/urls.py` — маршруты `auth`, `registration`, `logout`
- `dashboard/views.py` — `ShareListView`, `ShareDetailView`, `ShareCreateView`, `ShareUpdateView`, `ShareDeleteView`
- `user/views.py` — `AuthView`, `RegistrationView`, `LogoutView`
- `dashboard/templates/dashboard/*.html`, `user/templates/user/*.html` — шаблоны
- `config/settings.py` — `TEMPLATES` с `APP_DIRS: True`

**Ограничения и бизнес-правила:** Доступ к созданию, редактированию и удалению акций ограничен аутентифицированными пользователями (см. FR-08, FR-09).

---

### FR-02. REST API для работы с акциями

**Ожидаемое поведение:** Приложение предоставляет REST API по адресу `/api/v1/shares/` для получения списка акций, получения детальной информации об акции, создания, обновления и удаления акций. Поддерживается фильтрация по `name` и `ticker`, поиск по `name` и сортировка по `name` и `ticker`.

**Сценарий использования:** Клиент отправляет GET-запрос на `/api/v1/shares/` и получает пагинированный список акций.

**Подтверждение из кода:**
- `dashboard/api/v1/router.py` — `router.register(r"shares", ShareViewSet)`
- `dashboard/api/v1/views.py` — `ShareViewSet` (`ModelViewSet`), `ShareFilter` (`FilterSet` с полями `name`, `ticker`)
- `dashboard/api/v1/serializer.py` — `ShareSerializer` с полями `id`, `figi`, `isin`, `name`, `ticker`, `currency`, `last_price`, `is_trend_high`, `updated_at`
- `dashboard/api/v1/urls.py` + `dashboard/api/urls.py` — подключение API под `/api/v1/`
- `config/settings.py` — `REST_FRAMEWORK` с `LimitOffsetPagination`, `PageSize=100`, `DjangoFilterBackend`

**Ограничения и бизнес-правила:** Пагинация по умолчанию — `LimitOffsetPagination` с размером страницы 100.

---

### FR-03. Подключение PostgreSQL в качестве основной базы данных

**Ожидаемое поведение:** Приложение использует PostgreSQL как основную базу данных. Настройки подключения: база `investing`, пользователь `postgres`, пароль `postgres`, хост `localhost`, порт `5432`.

**Сценарий使用:** При запуске приложения Django подключается к PostgreSQL для хранения и чтения данных об акциях и пользователях.

**Подтверждение из кода:**
- `config/settings.py`, раздел `DATABASES` — `ENGINE: django.db.backends.postgresql`, `NAME: investing`, `USER: postgres`, `PASSWORD: postgres`, `HOST: localhost`, `PORT: 5432`
- `docker-compose.yml` — сервис `db` с образом `postgres`, переменные `POSTGRES_DB: investing`, `POSTGRES_USER: postgres`, `POSTGRES_PASSWORD: postgres`

**Ограничения и бизнес-правила:** SQLite указан в закомментированном виде и не используется. Работоспособность без запущенного PostgreSQL не гарантируется.

---

### FR-04. Celery + Redis для фоновых задач

**Ожидаемое поведение:** Приложение использует Celery с Redis в качестве брокера сообщений для выполнения фоновых задач (обновление цен акций).

**Сценарий使用:** Запуск Celery Beat и Celery Worker для периодического обновления цен.

**Подтверждение из кода:**
- `config/settings.py` — `CELERY_BROKER_URL: redis://127.0.0.1:6379/0`, `CELERY_TIMEZONE: Europe/Moscow`, `CELERY_TASK_TRACK_STARTED: True`, `CELERY_TASK_TIME_LIMIT: 30*60`
- `config/celery.py` — настройка приложения Celery, `beat_schedule` с задачей `dashboard.tasks.update_last_price` каждые 10.0 секунд
- `config/__init__.py` — экспорт `celery_app`
- `docker-compose.yml` — сервис `redis` с образом `redis`, порт `6379:6379`

**Ограничения и бизнес-правила:** Требуется запущенный Redis. На Windows рекомендуется пул `eventlet` (см. `README.md`).

---

### FR-05. Модель данных — сущность «Акция» (Share)

**Ожидаемое поведение:** Приложение хранит информацию об акциях в одной таблице с полями: идентификатор, FIGI, ISIN, название, тикер, валюта, UID, текущая цена, флаг тренда роста, время последнего обновления.

**Сценарий使用:** При импорте или создании акции запись сохраняется в таблицу `dashboard_share`.

**Подтверждение из кода:**
- `dashboard/models.py` — класс `Share` со всеми полями
- `dashboard/migrations/0001_add_share.py` … `0007_add_updated_at.py` — история изменений схемы

**Ограничения и бизнес-правила:**
- `figi` — уникальный, max_length=255
- `ticker` — уникальный, max_length=10
- `uid` — уникальный, max_length=255
- `last_price` — nullable, blank
- `is_trend_high` — nullable boolean, blank
- `updated_at` — `auto_now=True`, nullable

---

### FR-06. Модель данных — пользователь (аутентификация по email)

**Ожидаемое поведение:** Пользователи регистрируются и авторизуются по email и паролю. Используется стандартная модель пользователя Django (`get_user_model()`).

**Сценарий使用:** Новый пользователь регистрируется, указывая email, пароль и подтверждение пароля, затем может войти в систему.

**Подтверждение из кода:**
- `user/models.py` — `User = get_user_model()`
- `user/forms.py` — `RegistrationForm` (email, password1, password2), `AuthForm` (email, password)
- `user/views.py` — `RegistrationView`, `AuthView`, `LogoutView`
- `user/templates/user/registration.html`, `auth.html` — шаблоны форм

**Ограничения и бизнес-правила:** Email используется в качестве имени пользователя (`username`) при вызове `create_user(email, email, password)`.

---

## 2. Требования к управлению акциями (CRUD)

### FR-07. Просмотр списка акций

**Ожидаемое поведение:** Пользователь может просматривать список всех акций с пагинацией (100 на страницу), сортировкой по названию. В списке отображаются тикер, название, ISIN, текущая цена с валютой и индикатор тренда (цвет фона: зелёный — растёт, красный — не растёт).

**Сценарий使用:** Пользователь открывает главную страницу и просматривает таблицу акций.

**Подтверждение из кода:**
- `dashboard/views.py` — `ShareListView` (`ListView`, `model=Share`, `paginate_by=100`, `ordering=["name"]`)
- `dashboard/templates/dashboard/list.html` — отображение тикера, названия, ISIN, цены, цвета фона в зависимости от `is_trend_high`, ссылки на деталь/редактирование/удаление
- `dashboard/templates/dashboard/base.html` — навигация, блок приветствия/авторизации

**Ограничения и бизнес-правила:** Кнопки «Добавить», «Редактировать», «Удалить» отображаются только для аутентифицированных пользователей. Если акций нет, выводится сообщение «Акций еще нет».

---

### FR-08. Просмотр детальной информации об акции с графиком

**Ожидаемое поведение:** Пользователь может открыть страницу детальной информации об акции, где отображаются название, текущая цена, валюта, время последнего обновления и график исторических котировок (Plotly, за последние 180 дней, дневные свечи).

**Сценарий使用:** Пользователь кликает на тикер акции в списке и переходит на страницу детали с графиком.

**Подтверждение из кода:**
- `dashboard/views.py` — `ShareDetailView.get(request, pk)`, вызывает `get_graph(share)`
- `dashboard/services/graph.py` — `get_graph(share)`, запрос свечей через Tinkoff Invest API (`get_all_candles`, `CandleInterval.CANDLE_INTERVAL_DAY`, `now() - timedelta(days=180)`), построение графика через `plotly.offline.plot`
- `dashboard/templates/dashboard/detail.html` — отображение информации и графика (`{% autoescape off %}{{ plot_div }}{% endautoescape %}`)

**Ограничения и бизнес-правила:** График строитс на данных из Tinkoff Invest API. Требуется действительный `TINKOFF_TOKEN`.

---

### FR-09. Создание новой акции (только для аутентифицированных пользователей)

**Ожидаемое поведение:** Аутентифицированный пользователь может создать новую запись об акции через веб-форму, заполнив все поля модели `Share`.

**Сценарий使用:** Пользователь нажимает «Добавить», заполняет форму и сохраняет новую акцию.

**Подтверждение из кода:**
- `dashboard/views.py` — `ShareCreateView` (`CreateView`, `IsUserAuthenticatedMixin`, `form_class=ShareModelForm`, `success_url=reverse_lazy("dashboard:index")`)
- `dashboard/forms.py` — `ShareModelForm` (`ModelForm`, `fields = "__all__"`)
- `dashboard/templates/dashboard/create.html` — форма с полями через `crispy_forms`
- `dashboard/urls.py` — маршрут `create`

**Ограничения и бизнес-правила:** Доступ запрещён для неаутентифицированных пользователей (редирект на главную через `handle_no_permission`).

---

### FR-10. Редактирование существующей акции (только для аутентифицированных пользователей)

**Ожидаемое поведение:** Аутентифицированный пользователь может отредактировать поля существующей акции через веб-форму.

**Сценарий使用:** Пользователь нажимает «Редактировать» у акции в списке, изменяет поля и сохраняет.

**Подтверждение из кода:**
- `dashboard/views.py` — `ShareUpdateView` (`UpdateView`, `IsUserAuthenticatedMixin`, `model=Share`, `form_class=ShareModelForm`)
- `dashboard/templates/dashboard/create.html` — используется тот же шаблон формы
- `dashboard/urls.py` — маршрут `update/<int:pk>`

**Ограничения и бизнес-правила:** Доступ только для аутентифицированных пользователей.

---

### FR-11. Удаление акции (только для аутентифицированных пользователей)

**Ожидаемое поведение:** Аутентифицированный пользователь может удалить акцию после подтверждения на странице удаления.

**Сценарий使用:** Пользователь нажимает «Удалить», подтверждает действие, акция удаляется.

**Подтверждение из кода:**
- `dashboard/views.py` — `ShareDeleteView` (`DeleteView`, `IsUserAuthenticatedMixin`, `model=Share`, `template_name="dashboard/delete.html"`)
- `dashboard/templates/dashboard/delete.html` — форма подтверждения
- `dashboard/urls.py` — маршрут `delete/<int:pk>`

**Ограничения и бизнес-правила:** Доступ только для аутентифицированных пользователей.

---

### FR-12. Импорт акций из Tinkoff Invest API (команда управления)

**Ожидаемое поведение:** Администратор может импортировать список акций из Tinkoff Invest API в базу данных с помощью команды `python manage.py add_shares`. Каждая акция создаётся через `get_or_create` по полям figi, name, isin, ticker, currency, uid.

**Сценарий使用:** Запуск команды управления для первоначального заполнения базы акциями.

**Подтверждение из кода:**
- `dashboard/management/commands/add_shares.py` — класс `Command`, `client.instruments.shares()`, `Share.objects.get_or_create(...)`
- `README.md` — инструкция `python manage.py add_shares`

**Ограничения и бизнес-правила:** Требуется действительный `TINKOFF_TOKEN`. Дубликаты по `figi` и `ticker` не создаются благодаря `get_or_create` и ограничениям `unique=True`.

---

## 3. Требования к обновлению рыночных данных

### FR-13. Периодическое обновление цен акций (Celery-задача)

**Ожидаемое поведение:** Каждые 10 секунд (по настройке `beat_schedule`) Celery-задача `update_last_price` обходит все акции, запрашивает последнюю цену через Tinkoff Invest API, определяет направление тренда (рост/падение) по сравнению с предыдущей ценой и обновляет поля `last_price`, `is_trend_high`, `updated_at`.

**Сценарий使用:** Фоновый процесс автоматически обновляет цены всех акций в базе.

**Подтверждение из кода:**
- `config/celery.py` — `beat_schedule: "add-every-5-min", task: "dashboard.tasks.update_last_price", schedule: 10.0`
- `dashboard/tasks.py` — функция `update_last_price`, вызов `get_last_data(share)`, сравнение `share.last_price > last_price`, установка `is_trend_high`, `Share.objects.filter(id=share.id).update(...)`
- `dashboard/services/market_data.py` — `get_last_data(share)`, запрос `client.market_data.get_last_prices(figi=[share.figi])`, возврат `[resp.price.units, resp.time]`

**Ограничения и бизнес-правила:** Требуется запущенный Redis, Celery Beat и Celery Worker, действительный `TINKOFF_TOKEN`. При ошибке запроса для конкретной акции ошибка логируется, обработка продолжается для остальных акций.

---

## 4. Требования к аутентификации и autorзации

### FR-14. Регистрация пользователя

**Ожидаемое поведение:** Новый пользователь может зарегистрироваться, указав email, пароль и подтверждение пароля. Пароли должны совпадать. Email не должен быть уже зарегистрирован. После успешной регистрации пользователь автоматически авторизуется и перенаправляется на главную страницу.

**Сценарий使用:** Пользователь заполняет форму регистрации и создаёт аккаунт.

**Подтверждение из кода:**
- `user/views.py` — `RegistrationView.post`, `form.is_valid()`, `form.save()`, `login(request, user)`, `redirect("dashboard:index")`
- `user/forms.py` — `RegistrationForm.clean()` (проверка совпадения паролей, проверка уникальности email), `RegistrationForm.save()` (`User.objects.create_user(email, email, password)`, `authenticate`)
- `user/templates/user/registration.html` — форма регистрации

**Ограничения и бизнес-правила:** Email должен быть уникальным. Пароли должны совпадать. При ошибке отображается первое сообщение из `form.errors["__all__"]`.

---

### FR-15. Авторизация пользователя

**Ожидаемое поведение:** Зарегистрированный пользователь может войти в систему, указав email и пароль. При успешной аутентификации пользователь перенаправляется на главную страницу. При неверных учетных данных отображается сообщение об ошибке.

**Сценарий使用:** Пользователь заполняет форму входа и получает доступ к защищённым функциям.

**Подтверждение из кода:**
- `user/views.py` — `AuthView.post`, `authenticate(request, username=form.data["email"].lower(), password=...)`, `login(request, user)`, `redirect("dashboard:index")`
- `user/forms.py` — `AuthForm` (email, password)
- `user/templates/user/auth.html` — форма входа

**Ограничения и бизнес-правила:** Email приводится к нижнему регистру перед передачей в `authenticate`.

---

### FR-16. Выход из системы

**Ожидаемое поведение:** Аутентифицированный пользователь может выйти из системы. После выхода выполняется перенаправление на главную страницу.

**Сценарий使用:** Пользователь нажимает кнопку «Выход» в заголовке страницы.

**Подтверждение из кода:**
- `user/views.py` — `LogoutView.get`, `logout(request)`, `redirect("dashboard:index")`
- `dashboard/templates/dashboard/base.html` — ссылка «Выход» (`{% url 'user:logout' %}`) для аутентифицированных пользователей

---

### FR-17. Защита CRUD-операций авторизацией

**Ожидаемое поведение:** Создание, редактирование и удаление акций доступны только аутентифицированным пользователям. Неаутентифицированный пользователь при попытке доступа перенаправляется на главную страницу.

**Сценарий使用:** Неаутентифицированный пользователь пытается открыть страницу создания акции и перенаправляется на главную.

**Подтверждение из кода:**
- `dashboard/views.py` — `IsUserAuthenticatedMixin` (`test_func` проверяет `self.request.user.is_authenticated`, `handle_no_permission` возвращает `redirect("dashboard:index")`)
- `ShareCreateView`, `ShareUpdateView`, `ShareDeleteView` наследуются от `IsUserAuthenticatedMixin`

**Ограничения и бизнес-правила:** Просмотр списка и детальной информации доступен без авторизации.

---

## 5. Неоднозначности и противоречия

| # | Описание | Место в коде |
|---|----------|--------------|
| NC-01 | В `beat_schedule` комментарий указывает «add-every-5-min» (каждые 5 минут), но фактический интервал — `10.0` секунд. Неясно, какой интервал intended. | `config/celery.py`, строка 16 |
| NC-02 | `README.md` ссылается на `TINKOFF_TOKEN` в `config/settings.py`, но значение токена — пустая строка (`""`). Неясно, где должен задаваться реальный токен. | `config/settings.py` (стр. 134), `README.md` (стр. 7) |
| NC-03 | `ShareDetailView.get` использует `Share.objects.get(id=pk)` без `get_object_or_404`. При несуществующем `pk` будет вызвано исключение `Share.DoesNotExist` (ошибка 500), а не 404. Это противоречит ожидаемому поведению API (где 404 обрабатывается корректно через DRF). | `dashboard/views.py`, стр. 32 |
| NC-04 | Миграция `0004_add_last_price` содержит очевидные опечатки: `verbose_name="Валюта"` для поля `name` и `verbose_name="Ти"` для поля `ticker`. Они исправлены в последующих миграциях `0005` и `0006`, но в `0004` они присутствуют. | `dashboard/migrations/0004_add_last_price.py`, стр. 32, 37 |
| NC-05 | В `list.html` HTML-структура ячейки цены некорректна: открывающий тег `<td>` с цветом фона находится внутри условий `{% if %}` / `{% else %}`, но закрывающий `</td>` отсутствует в одной из веток (структура выглядит нарушенной). | `dashboard/templates/dashboard/list.html`, стр. 35–40 |
| NC-06 | `RegistrationView.post` обращается к `form.errors["__all__"].data[0].message`. Если ошибки не `__all__` или список пуст, возможен `IndexError` или `KeyError`. | `user/views.py`, стр. 54 |

---

## 6. Выявленные дефекты (отделены от функциональных требований)

Дефекты ниже — это ошибки реализации, которые не являются функциональными требованиями, но влияют на работоспособность или корректность приложения.

| # | Описание дефекта | Место в коде | Влияние |
|---|------------------|--------------|---------|
| DF-01 | `TINKOFF_TOKEN = ""` — пустой токен. Все вызовы к Tinkoff Invest API (`get_last_data`, `get_graph`, `add_shares`) будут падать с ошибкой аутентификации. | `config/settings.py` стр. 134 | Графики, обновление цен и импорт акций не работают без реального токена |
| DF-02 | `SECRET_KEY = ""` — пустой секретный ключ Django. В продакшене это критическая уязвимость; в режиме `DEBUG=True` может привести к ошибкам при работе с сессиями и CSRF. | `config/settings.py` стр. 6 | Проблемы с сессиями, CSRF, безопасностью |
| DF-03 | В `get_last_data` используется `resp.last_prices.pop()` без проверки на пустой список. Если API вернёт пустой список, возникнет `IndexError`. | `dashboard/services/market_data.py` стр. 9 | Ошибка при обновлении цены, если инструмент не найден в API |
| DF-04 | В `tasks.py` `if share.last_price > last_price` при `share.last_price=None` вызовет `TypeError`. Исключение ловится в общем `except` и устанавливает `is_trend_high=True`, что может быть некорректно. | `dashboard/tasks.py` стр. 16 | Некорректное определение тренда при первом обновлении цены |
| DF-05 | `ShareDetailView.get` не обрабатывает `Share.DoesNotExist` — при несуществующем `pk` пользователь получит ошибку 500 вместо 404. | `dashboard/views.py` стр. 32 | Ошибка 500 при некорректном ID акции |
| DF-06 | `RegistrationView.post` обращается к `form.errors["__all__"].data[0].message` без проверки существования ключа и непустоты списка. | `user/views.py` стр. 54 | Potential `KeyError`/`IndexError` при отображении ошибки регистрации |
| DF-07 | `AuthView.post` использует `form.data["email"]` и `form.data["password"]` вместо `form.cleaned_data`. Если форма не валидна, это может привести к `KeyError`. | `user/views.py` стр. 19 | Potential `KeyError` при невалидной форме входа |
| DF-08 | Миграция `0004_add_last_price` содержит некорректные `verbose_name` для `name` и `ticker` (исправлены позднее, но факт наличия ошибки в промежуточной миграции). | `dashboard/migrations/0004_add_last_price.py` | Некорректные метки в админке на момент применения `0004` |
| DF-09 | `CELERY_TASK_ALWAYS_EAGER = False` закомментирован? Нет, он явно задан как `False`. Это нормально, но при отсутствии запущенного Celery Worker задачи не будут выполняться. | `config/settings.py` стр. 143 | Фоновое обновление цен не работает без запущенного worker |

---

## 7. Требования, Impossible для достоверного восстановления

Следующие аспекты не могут быть достоверно восстановлены исключительно из исходного кода, так как они зависят от внешней среды, конфигурации или не документированы в коде:

| # | Аспект | Причина неопределённости |
|---|--------|-------------------------|
| UR-01 | Реальное значение `TINKOFF_TOKEN` | В коде токен — пустая строка; неясно, где и как должен задаваться в production |
| UR-02 | Порядок и частота ручного запуска `add_shares` | В коде есть команда, но не указано, как часто её нужно запускать |
| UR-03 | Состав и количество акций, доступных через Tinkoff Invest API | Зависит от внешнего API и токена, не задан в коде |
| UR-04 | Поведение при недоступности Tinkoff Invest API (реtry, таймауты, fallback) | В коде нет специальной обработки недоступности API, кроме общего `except` |
| UR-05 | Точное время間 между обновлениями в production (10 сек vs 5 мин) | См. NC-01 — расхождение между комментарием и кодом |
| UR-06 | Наличие и настроен ли корректно PostgreSQL и Redis в окружении запуска | Зависит от инфраструктуры, не задано в коде |
| UR-07 | Политика хранения и архивации логов (`app.logs`) | Указан файл логов, но не указано ротирование или срок хранения |
| UR-08 | Ограничения на количество акций, которое может добавить один пользователь | В коде нет takich ограничений |

---

## 8. Соответствие требований к коду (матрица подтверждений)

| Требование | Файл | Класс / Функция | Строки |
|------------|------|-----------------|--------|
| FR-01 | `config/urls.py`, `dashboard/urls.py`, `dashboard/views.py`, `dashboard/templates/` | URL-маршруты, представления, шаблоны | — |
| FR-02 | `dashboard/api/v1/views.py`, `dashboard/api/v1/serializer.py`, `dashboard/api/v1/router.py` | `ShareViewSet`, `ShareSerializer`, `ShareFilter` | — |
| FR-03 | `config/settings.py` | `DATABASES` | 91–104 |
| FR-04 | `config/settings.py`, `config/celery.py`, `docker-compose.yml` | `CELERY_BROKER_URL`, `beat_schedule` | — |
| FR-05 | `dashboard/models.py` | `Share` | 4–17 |
| FR-06 | `user/models.py`, `user/forms.py`, `user/views.py` | `User`, `RegistrationForm`, `AuthForm` | — |
| FR-07 | `dashboard/views.py`, `dashboard/templates/dashboard/list.html` | `ShareListView` | 20–26 |
| FR-08 | `dashboard/views.py`, `dashboard/services/graph.py`, `dashboard/templates/dashboard/detail.html` | `ShareDetailView`, `get_graph` | 29–38 |
| FR-09 | `dashboard/views.py`, `dashboard/forms.py` | `ShareCreateView`, `ShareModelForm` | 41–46 |
| FR-10 | `dashboard/views.py` | `ShareUpdateView` | 49–55 |
| FR-11 | `dashboard/views.py`, `dashboard/templates/dashboard/delete.html` | `ShareDeleteView` | 58–63 |
| FR-12 | `dashboard/management/commands/add_shares.py` | `Command.handle` | 8–22 |
| FR-13 | `dashboard/tasks.py`, `dashboard/services/market_data.py`, `config/celery.py` | `update_last_price`, `get_last_data` | — |
| FR-14 | `user/views.py`, `user/forms.py` | `RegistrationView`, `RegistrationForm` | — |
| FR-15 | `user/views.py`, `user/forms.py` | `AuthView`, `AuthForm` | — |
| FR-16 | `user/views.py` | `LogoutView` | 58–64 |
| FR-17 | `dashboard/views.py` | `IsUserAuthenticatedMixin` | 11–17 |

---

## 9. Заключение

Восстановлено **17 функциональных требований** (FR-01 … FR-17), охватывающих:
- веб-интерфейс и REST API для работы с акциями,
- подключение PostgreSQL и Celery/Redis,
- модель данных `Share` и пользователей,
- CRUD-операции с защитой авторизацией,
- обновление рыночных цен через Tinkoff Invest API,
- регистрацию, авторизацию и выход пользователей.

Выявлено **6 неоднозначностей** (NC-01 … NC-06), **9 дефектов реализации** (DF-01 … DF-09) и **8 требований, которые невозможно достоверно восстановить из кода** (UR-01 … UR-08).

Код не был изменён. Все утверждения подтверждаются конкретными файлами, классами, функциями и строками исходного кода.