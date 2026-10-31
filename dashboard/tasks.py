from config.celery import app
from dashboard.models import Share
from dashboard.services.market_data import get_last_data
from dashboard.services.watchlist_service import PriceAlertService
from dashboard.services.price_history_service import PriceHistoryService
from config.settings import logger


@app.task
def update_last_price():
    """Обновить последние цены всех акций и определить тренд."""
    shares = Share.objects.all()

    for share in shares:
        try:
            result = get_last_data(share)
            if not result:
                continue

            last_price, last_time = result

            try:
                if share.last_price is not None and last_price < share.last_price:
                    is_trend_high = False
                else:
                    is_trend_high = True
            except Exception as e:
                logger.error(e)
                is_trend_high = True

            Share.objects.filter(id=share.id).update(
                last_price=last_price, is_trend_high=is_trend_high
            )

            # Проверяем ценовые уведомления после обновления цены
            try:
                PriceAlertService.check_alerts(share, last_price)
            except Exception as e:
                logger.error(
                    f"Error checking alerts for share id={share.id}: {e}"
                )

        except Exception as e:
            logger.error(f"Error updating price for share id={share.id}: {e}")


@app.task
def update_price_history(share_id, days=180):
    """Обновить историю цен для конкретной акции."""
    try:
        share = Share.objects.get(id=share_id)
    except Share.DoesNotExist:
        logger.error(f"Share id={share_id} not found")
        return 0

    try:
        saved = PriceHistoryService.fetch_and_save_history(share, days=days)
        logger.info(
            f"Saved {saved} new price history records for share id={share_id}"
        )
        return saved
    except Exception as e:
        logger.error(
            f"Error updating price history for share id={share_id}: {e}"
        )
        return 0
