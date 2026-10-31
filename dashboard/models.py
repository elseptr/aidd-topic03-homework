from django.conf import settings
from django.db import models
from django.utils import timezone


class Share(models.Model):
    """Акция"""

    figi = models.CharField(max_length=255, unique=True)
    isin = models.CharField(max_length=255)
    name = models.CharField(max_length=255, verbose_name="Наименование компании")
    ticker = models.CharField(max_length=10, unique=True, verbose_name="Тикер")
    currency = models.CharField(max_length=20, verbose_name="Валюта")
    uid = models.CharField(max_length=255, unique=True)
    last_price = models.FloatField(blank=True, null=True, verbose_name="Текущая цена")
    is_trend_high = models.BooleanField(
        blank=True, null=True, verbose_name="Растет цена"
    )
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return f"{self.ticker} ({self.name})"


# ---------- 1. Персональный мониторинг (watchlist + target prices + notifications) ----------

class Watchlist(models.Model):
    """Персональный список наблюдения"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlists")
    name = models.CharField(max_length=100, default="Мой список")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Список наблюдения"
        verbose_name_plural = "Списки наблюдения"

    def __str__(self):
        return f"{self.name} ({self.user})"


class WatchlistItem(models.Model):
    """Элемент списка с целевой ценой"""
    DIRECTION_ABOVE = "above"
    DIRECTION_BELOW = "below"
    DIRECTION_CHOICES = [
        (DIRECTION_ABOVE, "Выше или равна"),
        (DIRECTION_BELOW, "Ниже или равна"),
    ]

    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name="items")
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="watchlist_items")
    target_price = models.FloatField(verbose_name="Целевая цена")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default=DIRECTION_ABOVE)
    is_active = models.BooleanField(default=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("watchlist", "share")
        verbose_name = "Элемент watchlist"
        verbose_name_plural = "Элементы watchlist"

    def condition_met(self, current_price: float) -> bool:
        if current_price is None:
            return False
        if self.direction == self.DIRECTION_ABOVE:
            return current_price >= self.target_price
        return current_price <= self.target_price


class PriceAlert(models.Model):
    """Уведомление о достижении целевой цены (без дублей по событию)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="price_alerts")
    share = models.ForeignKey(Share, on_delete=models.CASCADE)
    watchlist_item = models.ForeignKey(WatchlistItem, on_delete=models.SET_NULL, null=True, blank=True)
    target_price = models.FloatField()
    actual_price = models.FloatField()
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Уведомление о цене"
        verbose_name_plural = "Уведомления о цене"
        ordering = ["-created_at"]


# ---------- 2. Виртуальный инвестиционный портфель ----------

class Portfolio(models.Model):
    """Виртуальный портфель пользователя"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolios")
    name = models.CharField(max_length=100, default="Основной портфель")
    cash_balance = models.FloatField(default=1_000_000.0, verbose_name="Свободные средства")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Портфель"
        verbose_name_plural = "Портфели"

    def __str__(self):
        return f"{self.name} ({self.user})"


class PortfolioPosition(models.Model):
    """Позиция в портфеле"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="positions")
    share = models.ForeignKey(Share, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    avg_price = models.FloatField(default=0, verbose_name="Средняя цена покупки")

    class Meta:
        unique_together = ("portfolio", "share")
        verbose_name = "Позиция"
        verbose_name_plural = "Позиции"

    @property
    def current_value(self):
        price = self.share.last_price or 0
        return self.quantity * price

    @property
    def pnl(self):
        price = self.share.last_price or 0
        return self.quantity * (price - self.avg_price)

    @property
    def pnl_pct(self):
        if self.avg_price == 0:
            return 0
        price = self.share.last_price or 0
        return (price - self.avg_price) / self.avg_price * 100


class PortfolioTransaction(models.Model):
    """История операций портфеля"""
    BUY = "buy"
    SELL = "sell"
    SIDE_CHOICES = [(BUY, "Покупка"), (SELL, "Продажа")]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    share = models.ForeignKey(Share, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    quantity = models.FloatField()
    price = models.FloatField()
    total = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Операция портфеля"
        verbose_name_plural = "Операции портфеля"


# ---------- 3. История рыночных цен ----------

class PriceHistory(models.Model):
    """Сохранённая рыночная цена акции"""
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="price_history")
    price = models.FloatField()
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "История цены"
        verbose_name_plural = "История цен"
        indexes = [
            models.Index(fields=["share", "recorded_at"]),
        ]


# ---------- 4. Симулятор инвестиционных стратегий ----------

class Strategy(models.Model):
    """Инвестиционная стратегия"""
    BUY = "buy"
    SELL = "sell"
    ACTION_CHOICES = [(BUY, "Покупка"), (SELL, "Продажа")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="strategies")
    name = models.CharField(max_length=100)
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name="strategies")
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    # условие: цена выше/ниже threshold
    threshold_price = models.FloatField()
    direction = models.CharField(
        max_length=10,
        choices=WatchlistItem.DIRECTION_CHOICES,
        default=WatchlistItem.DIRECTION_ABOVE,
    )
    quantity = models.FloatField(default=1.0, verbose_name="Количество для сделки")
    is_active = models.BooleanField(default=True)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Если указан — сделки исполняются в этом портфеле"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Стратегия"
        verbose_name_plural = "Стратегии"

    def condition_met(self, current_price: float) -> bool:
        if current_price is None:
            return False
        if self.direction == WatchlistItem.DIRECTION_ABOVE:
            return current_price >= self.threshold_price
        return current_price <= self.threshold_price


class StrategyTrade(models.Model):
    """Журнал виртуальных сделок стратегии"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="trades")
    side = models.CharField(max_length=4, choices=Strategy.ACTION_CHOICES)
    quantity = models.FloatField()
    price = models.FloatField()
    total = models.FloatField()
    executed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-executed_at"]
        verbose_name = "Сделка стратегии"
        verbose_name_plural = "Сделки стратегий"
