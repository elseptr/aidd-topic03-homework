from decimal import Decimal

from tinkoff.invest import Client

from config.settings import TINKOFF_TOKEN, logger

from dashboard.services.demo_market_data import get_last_data_demo


def get_last_data(share, use_demo_fallback=True):
    """Получить последнюю цену акции по FIGI.

    Возвращает список [цена_в_единицах_валюты, время_обновления]
    или пустой список, если данные не получены.

    Если Tinkoff API недоступен и use_demo_fallback=True,
    возвращаются демонстрационные данные.
    """
    try:
        with Client(TINKOFF_TOKEN) as client:
            resp = client.market_data.get_last_prices(figi=[share.figi])
            if not resp.last_prices:
                logger.warning(
                    f"No last prices returned for share figi={share.figi} id={share.id}"
                )
                if use_demo_fallback:
                    return get_last_data_demo(share)
                return []
            last_price = resp.last_prices[0]
            nano = last_price.price.nano or 0
            price = Decimal(str(last_price.price.units)) + Decimal(nano) / Decimal(
                10 ** 9
            )
            logger.info(f"Get last data for share with id {share.id}")
            return [price, last_price.time]
    except Exception as e:
        logger.error(
            f"Tinkoff API error for share id={share.id}: {e}. "
            f"Demo fallback={'enabled' if use_demo_fallback else 'disabled'}."
        )
        if use_demo_fallback:
            return get_last_data_demo(share)
        return []
