from django.contrib.auth import get_user_model
from django.utils import timezone

from dashboard.models import Share, Watchlist, WatchlistItem, PriceAlert, Notification

User = get_user_model()


class WatchlistService:
    """Сервис для работы со списками наблюдения."""

    @staticmethod
    def create_watchlist(user, name):
        """Создать новый список наблюдения для пользователя."""
        watchlist, created = Watchlist.objects.get_or_create(user=user, name=name)
        return watchlist, created

    @staticmethod
    def add_share_to_watchlist(user, watchlist_name, share_figi):
        """Добавить акцию в список наблюдения."""
        try:
            watchlist = Watchlist.objects.get(user=user, name=watchlist_name)
        except Watchlist.DoesNotExist:
            return None, "Список наблюдения не найден"

        try:
            share = Share.objects.get(figi=share_figi)
        except Share.DoesNotExist:
            return None, "Акция не найдена"

        item, created = WatchlistItem.objects.get_or_create(
            watchlist=watchlist, share=share
        )
        return item, created

    @staticmethod
    def remove_share_from_watchlist(user, watchlist_name, share_figi):
        """Удалить акцию из списка наблюдения."""
        try:
            watchlist = Watchlist.objects.get(user=user, name=watchlist_name)
        except Watchlist.DoesNotExist:
            return False, "Список наблюдения не найден"

        try:
            share = Share.objects.get(figi=share_figi)
        except Share.DoesNotExist:
            return False, "Акция не найдена"

        deleted, _ = WatchlistItem.objects.filter(
            watchlist=watchlist, share=share
        ).delete()
        return deleted > 0, None

    @staticmethod
    def get_user_watchlists(user):
        """Получить все списки наблюдения пользователя с предметами."""
        return Watchlist.objects.filter(user=user).prefetch_related("items__share")


class PriceAlertService:
    """Сервис для работы с ценовыми уведомлениями."""

    @staticmethod
    def create_alert(user, share_figi, target_price, alert_type="above"):
        """Создать ценовое уведомление."""
        try:
            share = Share.objects.get(figi=share_figi)
        except Share.DoesNotExist:
            return None, "Акция не найдена"

        alert = PriceAlert.objects.create(
            user=user,
            share=share,
            target_price=target_price,
            alert_type=alert_type,
        )
        return alert, None

    @staticmethod
    def check_alerts(share, current_price):
        """Проверить все активные уведомления для акции и создать уведомления при срабатывании."""
        from decimal import Decimal

        current_price = Decimal(str(current_price))
        alerts = PriceAlert.objects.filter(
            share=share, is_active=True
        ).select_related("user")

        triggered = []
        for alert in alerts:
            should_trigger = False
            if alert.alert_type == "above" and current_price >= alert.target_price:
                should_trigger = True
            elif alert.alert_type == "below" and current_price <= alert.target_price:
                should_trigger = True

            if should_trigger:
                # Защита от дублирования: уведомление не должно срабатывать чаще одного раза в час
                if (
                    alert.last_triggered_at
                    and (timezone.now() - alert.last_triggered_at).total_seconds()
                    < 3600
                ):
                    continue

                message = (
                    f"Цена {share.ticker}达到 {current_price} "
                    f"{share.currency} (цель: {alert.target_price})"
                )
                Notification.objects.create(
                    user=alert.user,
                    message=message,
                )

                alert.last_triggered_at = timezone.now()
                alert.save(update_fields=["last_triggered_at"])
                triggered.append(alert)

        return triggered


class NotificationService:
    """Сервис для работы с уведомлениями."""

    @staticmethod
    def get_unread_count(user):
        """Получить количество непрочитанных уведомлений."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def mark_all_read(user):
        """Отметить все уведомления пользователя как прочитанные."""
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
