from django.contrib import admin
from dashboard.models import (
    Share, Watchlist, WatchlistItem, PriceAlert,
    Portfolio, PortfolioPosition, PortfolioTransaction,
    PriceHistory, Strategy, StrategyTrade,
)


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("figi", "isin", "name", "ticker", "currency", "last_price", "is_trend_high")
    search_fields = ("figi", "isin", "name", "ticker")
    fields = (
        "figi", "isin", "name", "ticker", "currency", "uid",
        "last_price", "is_trend_high",
    )


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("watchlist", "share", "target_price", "direction", "is_active")


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "share", "target_price", "actual_price", "is_read", "created_at")


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "cash_balance", "created_at")


@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "share", "quantity", "avg_price")


@admin.register(PortfolioTransaction)
class PortfolioTransactionAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "share", "side", "quantity", "price", "total", "created_at")


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("share", "price", "recorded_at")
    list_filter = ("share",)


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "share", "action", "threshold_price", "is_active")


@admin.register(StrategyTrade)
class StrategyTradeAdmin(admin.ModelAdmin):
    list_display = ("strategy", "side", "quantity", "price", "executed_at")
