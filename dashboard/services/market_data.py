"""Market data service. Uses demo mode when TINKOFF_TOKEN is empty."""
from datetime import datetime, timezone
import random
from config.settings import TINKOFF_TOKEN, logger


def get_last_data(share):
    """Return [price, datetime]. Demo mode generates synthetic prices."""
    if not TINKOFF_TOKEN:
        # demo: slight random walk around last_price or base
        base = share.last_price or 100.0
        delta = random.uniform(-0.02, 0.02) * base
        price = round(base + delta, 2)
        logger.info(f"[demo] last price for {share.ticker}: {price}")
        return [price, datetime.now(timezone.utc)]

    try:
        from tinkoff.invest import Client
        with Client(TINKOFF_TOKEN) as client:
            resp = client.market_data.get_last_prices(figi=[share.figi])
            resp = resp.last_prices.pop()
            logger.info(f"Get last data for share with id {share.id}")
            return [resp.price.units + resp.price.nano / 1e9, resp.time]
    except Exception as e:
        logger.error(e)
        base = share.last_price or 100.0
        return [base, datetime.now(timezone.utc)]
