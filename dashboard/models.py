from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


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


class Watchlist(models.Model):
    """Список наблюдения пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="watchlists"
    )
    name = models.CharField(max_length=255, verbose_name="Название списка")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Список наблюдения"
        verbose_name_plural = "Списки наблюдения"
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class WatchlistItem(models.Model):
    """Элемент списка наблюдения — связь акции со списком"""

    watchlist = models.ForeignKey(
        Watchlist, on_delete=models.CASCADE, related_name="items"
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="watchlist_items"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Элемент списка наблюдения"
        verbose_name_plural = "Элементы списков наблюдения"
        unique_together = ("watchlist", "share")

    def __str__(self):
        return f"{self.share.ticker} in {self.watchlist.name}"


class PriceAlert(models.Model):
    """Ценовое уведомление пользователя"""

    ALERT_TYPE_CHOICES = [
        ("above", "Цена выше целевой"),
        ("below", "Цена ниже целевой"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="price_alerts"
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="price_alerts"
    )
    target_price = models.DecimalField(
        max_digits=20, decimal_places=10, verbose_name="Целевая цена"
    )
    alert_type = models.CharField(
        max_length=10, choices=ALERT_TYPE_CHOICES, default="above"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    last_triggered_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Последнее срабатывание"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ценовое уведомление"
        verbose_name_plural = "Ценовые уведомления"

    def __str__(self):
        return f"{self.share.ticker} {self.get_alert_type_display()} {self.target_price}"


class Notification(models.Model):
    """Уведомление пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField(verbose_name="Сообщение")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email}: {self.message[:50]}"


class Portfolio(models.Model):
    """Виртуальный инвестиционный портфель пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="portfolios"
    )
    name = models.CharField(max_length=255, verbose_name="Название портфеля")
    initial_balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        verbose_name="Начальный баланс",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Портфель"
        verbose_name_plural = "Портфели"
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def total_value(self):
        """Текущая стоимость портфеля (сумма позиций по текущим ценам)."""
        total = self.initial_balance
        for position in self.positions.all():
            total += position.current_value()
        return total

    def total_profit_loss(self):
        """Общая прибыль/убыток портфеля."""
        return self.total_value() - self.initial_balance


class PortfolioPosition(models.Model):
    """Позиция в портфеле — количество акций и средняя цена покупки"""

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="positions"
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="portfolio_positions"
    )
    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=0,
        verbose_name="Количество акций",
    )
    average_price = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=0,
        verbose_name="Средняя цена покупки",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Позиция портфеля"
        verbose_name_plural = "Позиции портфеля"
        unique_together = ("portfolio", "share")

    def __str__(self):
        return f"{self.share.ticker} x{self.quantity} @ {self.average_price}"

    def current_value(self):
        """Текущая стоимость позиции."""
        if self.share.last_price is None:
            return Decimal("0")
        from decimal import Decimal as D

        return D(str(self.share.last_price)) * self.quantity

    def current_profit_loss(self):
        """Прибыль/убыток позиции."""
        if self.share.last_price is None:
            return Decimal("0")
        from decimal import Decimal as D

        current = D(str(self.share.last_price)) * self.quantity
        cost = self.average_price * self.quantity
        return current - cost


class PortfolioTransaction(models.Model):
    """История операций портфеля (покупка/продажа)"""

    TRANSACTION_TYPE_CHOICES = [
        ("buy", "Покупка"),
        ("sell", "Продажа"),
    ]

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="transactions"
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="portfolio_transactions"
    )
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES
    )
    quantity = models.DecimalField(
        max_digits=20, decimal_places=10, verbose_name="Количество"
    )
    price = models.DecimalField(
        max_digits=20, decimal_places=10, verbose_name="Цена за единицу"
    )
    total_amount = models.DecimalField(
        max_digits=20, decimal_places=2, verbose_name="Общая сумма"
    )
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Операция портфеля"
        verbose_name_plural = "Операции портфеля"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.share.ticker} x{self.quantity} @ {self.price}"


class PriceHistory(models.Model):
    """Исторические рыночные цены акций"""

    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="price_history"
    )
    price = models.DecimalField(
        max_digits=20, decimal_places=10, verbose_name="Цена"
    )
    timestamp = models.DateTimeField(verbose_name="Время")

    class Meta:
        verbose_name = "Историческая цена"
        verbose_name_plural = "Исторические цены"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["share", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.share.ticker} @ {self.price} ({self.timestamp})"
