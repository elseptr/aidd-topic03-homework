from django.contrib import admin

from dashboard.models import (
    Share,
    Watchlist,
    WatchlistItem,
    PriceAlert,
    Notification,
    Portfolio,
    PortfolioPosition,
    PortfolioTransaction,
    PriceHistory,
)


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("figi", "isin", "name", "ticker", "currency", "last_price")
    search_fields = ("figi", "isin", "name", "ticker")
    fields = (
        "figi",
        "isin",
        "name",
        "ticker",
        "currency",
        "uid",
        "last_price",
        "is_trend_high",
    )


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("name", "user__email")


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("watchlist", "share", "added_at")
    list_filter = ("watchlist",)
    search_fields = ("share__ticker", "share__name")


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = (
        "share",
        "user",
        "target_price",
        "alert_type",
        "is_active",
        "last_triggered_at",
    )
    list_filter = ("is_active", "alert_type", "user")
    search_fields = ("share__ticker", "user__email")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__email", "message")


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "initial_balance", "created_at")
    list_filter = ("user",)
    search_fields = ("name", "user__email")


@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    list_display = (
        "portfolio",
        "share",
        "quantity",
        "average_price",
        "updated_at",
    )
    list_filter = ("portfolio",)
    search_fields = ("share__ticker", "portfolio__name")


@admin.register(PortfolioTransaction)
class PortfolioTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "portfolio",
        "share",
        "transaction_type",
        "quantity",
        "price",
        "executed_at",
    )
    list_filter = ("transaction_type", "executed_at")
    search_fields = ("share__ticker", "portfolio__name")


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("share", "price", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("share__ticker",)
