"""Price history storage and analysis."""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Max, Min, Avg
from dashboard.models import Share, PriceHistory
from config.settings import logger


def record_current_prices():
    """Save current last_price of all shares into history."""
    count = 0
    now = timezone.now()
    for share in Share.objects.exclude(last_price__isnull=True):
        PriceHistory.objects.create(share=share, price=share.last_price, recorded_at=now)
        count += 1
    logger.info(f"Recorded {count} price points")
    return count


def get_history(share: Share, days: int = 30):
    since = timezone.now() - timedelta(days=days)
    return list(
        PriceHistory.objects.filter(share=share, recorded_at__gte=since)
        .order_by("recorded_at")
        .values_list("recorded_at", "price")
    )


def analyze_period(share: Share, days: int = 30):
    since = timezone.now() - timedelta(days=days)
    qs = PriceHistory.objects.filter(share=share, recorded_at__gte=since)
    if not qs.exists():
        return None
    agg = qs.aggregate(mn=Min("price"), mx=Max("price"), avg=Avg("price"))
    first = qs.order_by("recorded_at").first()
    last = qs.order_by("-recorded_at").first()
    abs_change = last.price - first.price
    pct_change = (abs_change / first.price * 100) if first.price else 0
    return {
        "min": agg["mn"],
        "max": agg["mx"],
        "avg": agg["avg"],
        "first": first.price,
        "last": last.price,
        "abs_change": abs_change,
        "pct_change": pct_change,
        "points": qs.count(),
    }
