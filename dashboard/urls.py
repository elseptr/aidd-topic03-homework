from django.urls import include, path

from dashboard.views import (
    ShareCreateView,
    ShareDeleteView,
    ShareDetailView,
    ShareListView,
    ShareUpdateView,
    WatchlistListView,
    WatchlistCreateView,
    WatchlistDetailView,
    WatchlistDeleteView,
    WatchlistAddShareView,
    WatchlistRemoveShareView,
    PriceAlertListView,
    PriceAlertCreateView,
    PriceAlertDeleteView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    PortfolioListView,
    PortfolioCreateView,
    PortfolioDetailView,
    PortfolioDeleteView,
    PortfolioBuyView,
    PortfolioSellView,
)

app_name = "dashboard"

urlpatterns = [
    path("", ShareListView.as_view(), name="index"),
    path("<int:pk>", ShareDetailView.as_view(), name="detail"),
    path("create", ShareCreateView.as_view(), name="create"),
    path("update/<int:pk>", ShareUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", ShareDeleteView.as_view(), name="delete"),
    # Watchlists
    path("watchlists/", WatchlistListView.as_view(), name="watchlist_list"),
    path("watchlists/create/", WatchlistCreateView.as_view(), name="watchlist_create"),
    path(
        "watchlists/<int:pk>/",
        WatchlistDetailView.as_view(),
        name="watchlist_detail",
    ),
    path(
        "watchlists/<int:pk>/delete/",
        WatchlistDeleteView.as_view(),
        name="watchlist_delete",
    ),
    path(
        "watchlists/<int:pk>/add-share/",
        WatchlistAddShareView.as_view(),
        name="watchlist_add_share",
    ),
    path(
        "watchlists/<int:pk>/remove-share/<int:item_id>/",
        WatchlistRemoveShareView.as_view(),
        name="watchlist_remove_share",
    ),
    # Price Alerts
    path(
        "alerts/",
        PriceAlertListView.as_view(),
        name="price_alert_list",
    ),
    path(
        "alerts/create/",
        PriceAlertCreateView.as_view(),
        name="price_alert_create",
    ),
    path(
        "alerts/<int:pk>/delete/",
        PriceAlertDeleteView.as_view(),
        name="price_alert_delete",
    ),
    # Notifications
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification_list",
    ),
    path(
        "notifications/<int:pk>/read/",
        NotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    path(
        "notifications/read-all/",
        NotificationMarkAllReadView.as_view(),
        name="notification_mark_all_read",
    ),
    # Portfolios
    path(
        "portfolios/",
        PortfolioListView.as_view(),
        name="portfolio_list",
    ),
    path(
        "portfolios/create/",
        PortfolioCreateView.as_view(),
        name="portfolio_create",
    ),
    path(
        "portfolios/<int:pk>/",
        PortfolioDetailView.as_view(),
        name="portfolio_detail",
    ),
    path(
        "portfolios/<int:pk>/delete/",
        PortfolioDeleteView.as_view(),
        name="portfolio_delete",
    ),
    path(
        "portfolios/<int:pk>/buy/",
        PortfolioBuyView.as_view(),
        name="portfolio_buy",
    ),
    path(
        "portfolios/<int:pk>/sell/",
        PortfolioSellView.as_view(),
        name="portfolio_sell",
    ),
    path("api/", include("dashboard.api.urls")),
]
