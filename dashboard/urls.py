from django.urls import include, path
from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.ShareListView.as_view(), name="index"),
    path("<int:pk>", views.ShareDetailView.as_view(), name="detail"),
    path("create", views.ShareCreateView.as_view(), name="create"),
    path("update/<int:pk>", views.ShareUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", views.ShareDeleteView.as_view(), name="delete"),
    path("api/", include("dashboard.api.urls")),
    # watchlist
    path("watchlists/", views.watchlist_list, name="watchlist_list"),
    path("watchlists/create/", views.watchlist_create, name="watchlist_create"),
    path("watchlists/<int:wl_id>/add/", views.watchlist_item_add, name="watchlist_item_add"),
    path("watchlists/item/<int:item_id>/delete/", views.watchlist_item_delete, name="watchlist_item_delete"),
    path("alerts/read/", views.mark_alerts_read, name="mark_alerts_read"),
    # portfolio
    path("portfolios/", views.portfolio_list, name="portfolio_list"),
    path("portfolios/<int:pk>/", views.portfolio_detail, name="portfolio_detail"),
    path("portfolios/<int:pk>/trade/", views.portfolio_trade, name="portfolio_trade"),
    # price history
    path("history/<int:share_id>/", views.price_history_view, name="price_history"),
    # strategies
    path("strategies/", views.strategy_list, name="strategy_list"),
    path("strategies/create/", views.strategy_create, name="strategy_create"),
    path("strategies/<int:pk>/toggle/", views.strategy_toggle, name="strategy_toggle"),
    path("strategies/<int:pk>/trades/", views.strategy_trades, name="strategy_trades"),
    # demo trigger
    path("run-update/", views.run_update, name="run_update"),
]
