"""Watchlist & price alert service."""
from django.utils import timezone
from dashboard.models import WatchlistItem, PriceAlert, Share
from config.settings import logger


def check_and_notify_targets():
    """Check all active watchlist items and create alerts without duplicates."""
    items = WatchlistItem.objects.filter(is_active=True).select_related("share", "watchlist", "watchlist__user")
    created = 0
    for item in items:
        price = item.share.last_price
        if price is None:
            continue
        if not item.condition_met(price):
            continue
        # avoid duplicate: if already notified after last price update for this target
        if item.last_notified_at and item.share.updated_at and item.last_notified_at >= item.share.updated_at:
            continue
        # also check recent alert for same share+target
        recent = PriceAlert.objects.filter(
            user=item.watchlist.user,
            share=item.share,
            target_price=item.target_price,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1),
        ).exists()
        if recent:
            continue
        msg = (
            f"{item.share.ticker}: цена {price} достигла целевой "
            f"{item.target_price} ({item.get_direction_display()})"
        )
        PriceAlert.objects.create(
            user=item.watchlist.user,
            share=item.share,
            watchlist_item=item,
            target_price=item.target_price,
            actual_price=price,
            message=msg,
        )
        item.last_notified_at = timezone.now()
        item.save(update_fields=["last_notified_at"])
        created += 1
        logger.info(f"Alert created: {msg}")
    return created
