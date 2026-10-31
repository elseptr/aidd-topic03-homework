import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "add-every-5-min": {
        "task": "dashboard.tasks.update_last_price",
        "schedule": 10.0,
    },
    "update-price-hourly": {
        "task": "dashboard.tasks.update_price_history",
        "schedule": 3600.0,
        "args": (1, 180),  # share_id=1, days=180 — пример, настраивается
    },
}
