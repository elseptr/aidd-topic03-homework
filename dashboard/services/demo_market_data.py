import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from config.settings import logger


# Demonstraционные базовые цены для известных тикеров (используются только когда Tinkoff API недоступен)
DEMO_BASE_PRICES = {
    "AAPL": Decimal("150.25"),
    "GOOGL": Decimal("2800.50"),
    "MSFT": Decimal("330.75"),
    "AMZN": Decimal("3400.10"),
    "TSLA": Decimal("250.30"),
    "NVDA": Decimal("450.80"),
    "META": Decimal("320.45"),
    "NFLX": Decimal("480.20"),
}

DEMO_CURRENCIES = {
    "AAPL": "USD",
    "GOOGL": "USD",
    "MSFT": "USD",
    "AMZN": "USD",
    "TSLA": "USD",
    "NVDA": "USD",
    "META": "USD",
    "NFLX": "USD",
}


def _demo_price_variation(base_price: Decimal) -> Decimal:
    """Случайное отклонение цены в пределах ±5% от базовой."""
    variation = base_price * Decimal(str(random.uniform(-0.05, 0.05)))
    return base_price + variation


def get_last_data_demo(share):
    """Демонстрационная версия get_last_data.

    Возвращает [цена, время] с синтетическими данными.
    Используется только когда Tinkoff API недоступен.
    """
    base_price = DEMO_BASE_PRICES.get(share.ticker, Decimal("100.00"))
    price = _demo_price_variation(base_price)
    now = timezone.now()
    logger.info(
        f"Demo market data for share id={share.id} ticker={share.ticker}: price={price}"
    )
    return [price, now]


def get_candles_demo(share, days=180, interval="day"):
    """Демонстрационные исторические свечи.

    Генерирует синтдетические данные о ценах за указанный период.
    Используется только когда Tinkoff API недоступен.
    """
    base_price = DEMO_BASE_PRICES.get(share.ticker, Decimal("100.00"))
    candles = []
    now = timezone.now()
    step = timedelta(days=1) if interval == "day" else timedelta(hours=1)

    price = base_price
    for i in range(days, 0, -1):
        candle_time = now - timedelta(days=i)
        variation = Decimal(str(random.uniform(-0.03, 0.03)))
        price = price * (Decimal("1") + variation)
        candles.append(
            {
                "time": candle_time,
                "open": price,
                "close": price * (Decimal("1") + Decimal(str(random.uniform(-0.02, 0.02)))),
                "high": price * (Decimal("1") + Decimal(str(random.uniform(0, 0.02)))),
                "low": price * (Decimal("1") - Decimal(str(random.uniform(0, 0.02)))),
            }
        )

    return candles
