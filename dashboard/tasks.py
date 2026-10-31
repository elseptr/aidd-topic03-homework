from config.celery import app
from dashboard.models import Share
from dashboard.services.market_data import get_last_data
from dashboard.services.price_history_service import record_current_prices
from dashboard.services.watchlist_service import check_and_notify_targets
from dashboard.services.strategy_service import run_strategies
from config.settings import logger


@app.task
def update_last_price():
    shares = Share.objects.all()
    for share in shares:
        try:
            last_price, dt = get_last_data(share)
            try:
                if share.last_price is not None and share.last_price > last_price:
                    is_trend_high = False
                else:
                    is_trend_high = True
            except Exception as e:
                logger.error(e)
                is_trend_high = True
            Share.objects.filter(id=share.id).update(
                last_price=last_price, is_trend_high=is_trend_high
            )
        except Exception as e:
            logger.error(e)
    # after prices updated — record history, check alerts, run strategies
    try:
        record_current_prices()
    except Exception as e:
        logger.error(e)
    try:
        check_and_notify_targets()
    except Exception as e:
        logger.error(e)
    try:
        run_strategies()
    except Exception as e:
        logger.error(e)
