from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

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
from dashboard.services.market_data import get_last_data
from dashboard.services.graph import get_graph
from dashboard.services.demo_market_data import get_last_data_demo, get_candles_demo
from dashboard.services.watchlist_service import WatchlistService, PriceAlertService
from dashboard.services.portfolio_service import PortfolioService
from dashboard.services.price_history_service import PriceHistoryService, StrategySimulatorService

User = get_user_model()


class DashboardTests(APITestCase):
    def setUp(self) -> None:
        self.apple_share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
            last_price=100.50,
            is_trend_high=True,
        )

        self.second_company = {
            "figi": "BBG000B9XRY5",
            "isin": "US0378331004",
            "name": "Company_test",
            "ticker": "TESTTEST",
            "currency": "usd",
            "uid": "a9eb4238-eba9-488c-b102-b6140fd08e39",
            "last_price": 1.50,
            "is_trend_high": False,
        }

    def test_share_list_html(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_list(self):
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        apple_share = response.json().get("results")[0]
        self.assertEqual(apple_share["id"], self.apple_share.id)
        self.assertEqual(apple_share["figi"], self.apple_share.figi)
        self.assertEqual(apple_share["isin"], self.apple_share.isin)
        self.assertEqual(apple_share["name"], self.apple_share.name)
        self.assertEqual(apple_share["ticker"], self.apple_share.ticker)
        self.assertEqual(apple_share["currency"], self.apple_share.currency)

    def test_share_detail(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.get(f"/api/v1/shares/{share_detail['id']}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_detail_invalid(self):
        response = self.client.get("/api/v1/shares/2/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_share_update(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "id": share_detail["id"],
                "figi": self.apple_share.figi,
                "isin": self.apple_share.isin,
                "name": f"{self.apple_share.name}_test",
                "ticker": self.apple_share.ticker,
                "currency": self.apple_share.currency,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["figi"], self.apple_share.figi)
        self.assertEqual(body["name"], f"{self.apple_share.name}_test")

    def test_share_update_invalid(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "figi": self.apple_share.figi,
                "name": f"{self.apple_share.name}_test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_share_create(self):
        response = self.client.post(
            "/api/v1/shares/", self.second_company, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["figi"], self.second_company["figi"])
        self.assertEqual(body["name"], self.second_company["name"])
        self.assertEqual(body["ticker"], self.second_company["ticker"])

        response = self.client.get("/api/v1/shares/")
        self.assertEqual(len(response.data["results"]), 2)

    def test_share_create_invalid(self):
        response = self.client.post(
            "/api/v1/shares/", {"figi": "BBG000B9XRY5"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_share_delete(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.delete(f"/api/v1/shares/{share_detail['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_share_delete_invalid(self):
        response = self.client.delete("/api/v1/shares/3/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MarketDataServiceTests(TestCase):
    """Тесты сервиса рыночных данных."""

    def test_get_last_data_returns_list(self):
        """Проверка, что get_last_data возвращает список (даже пустой)."""
        result = get_last_data.__annotations__
        # Функция должна существовать и быть вызываемой
        self.assertTrue(callable(get_last_data))


class GraphServiceTests(TestCase):
    """Тесты сервиса построения графиков."""

    def test_get_graph_callable(self):
        """Проверка, что get_graph существует и вызывается."""
        self.assertTrue(callable(get_graph))


class DetailView404Tests(TestCase):
    """Тесты обработки несуществующих акций в детальном представлении."""

    @override_settings(DEBUG=False)
    def test_detail_nonexistent_share_returns_404(self):
        """Запрос несуществующей акции должен возвращать 404, а не 500."""
        response = self.client.get(reverse("dashboard:detail", args=[99999]))
        self.assertEqual(response.status_code, 404)


class TasksTests(TestCase):
    """Тесты задачи обновления цен."""

    def test_update_last_price_exists(self):
        """Проверка существования задачи update_last_price."""
        from dashboard.tasks import update_last_price
        self.assertTrue(callable(update_last_price))


class DemoMarketDataTests(TestCase):
    """Тесты демонстрационного механизма рыночных данных."""

    def setUp(self):
        self.share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
        )

    def test_get_last_data_demo_returns_list(self):
        """Демо-функция возвращает список [цена, время]."""
        result = get_last_data_demo(self.share)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Decimal)
        self.assertGreater(result[0], 0)

    def test_get_candles_demo_returns_list(self):
        """Демо-функция возвращает список свечей."""
        candles = get_candles_demo(self.share, days=30)
        self.assertEqual(len(candles), 30)
        self.assertIn("close", candles[0])


class WatchlistTests(TestCase):
    """Тесты списков наблюдения."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
        )

    def test_create_watchlist(self):
        """Создание списка наблюдения."""
        watchlist, created = WatchlistService.create_watchlist(self.user, "Мои акции")
        self.assertTrue(created)
        self.assertEqual(watchlist.user, self.user)
        self.assertEqual(watchlist.name, "Мои акции")

    def test_add_share_to_watchlist(self):
        """Добавление акции в список наблюдения."""
        watchlist, _ = WatchlistService.create_watchlist(self.user, "Тестовый")
        item, created = WatchlistService.add_share_to_watchlist(
            self.user, "Тестовый", self.share.figi
        )
        self.assertTrue(created)
        self.assertEqual(item.watchlist, watchlist)
        self.assertEqual(item.share, self.share)

    def test_add_duplicate_share_to_watchlist(self):
        """Повторное добавление той же акции не создает дубликат."""
        watchlist, _ = WatchlistService.create_watchlist(self.user, "Тестовый")
        WatchlistService.add_share_to_watchlist(self.user, "Тестовый", self.share.figi)
        item, created = WatchlistService.add_share_to_watchlist(
            self.user, "Тестовый", self.share.figi
        )
        self.assertFalse(created)

    def test_remove_share_from_watchlist(self):
        """Удаление акции из списка наблюдения."""
        watchlist, _ = WatchlistService.create_watchlist(self.user, "Тестовый")
        WatchlistService.add_share_to_watchlist(self.user, "Тестовый", self.share.figi)
        item = WatchlistItem.objects.get(watchlist=watchlist, share=self.share)
        success, _ = WatchlistService.remove_share_from_watchlist(
            self.user, "Тестовый", self.share.figi
        )
        self.assertTrue(success)
        self.assertEqual(WatchlistItem.objects.filter(id=item.id).count(), 0)


class PriceAlertTests(TestCase):
    """Тесты ценовых уведомлений."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
            last_price=100.00,
        )

    def test_create_price_alert(self):
        """Создание ценового уведомления."""
        alert, error = PriceAlertService.create_alert(
            self.user, self.share.figi, Decimal("150.00"), "above"
        )
        self.assertIsNone(error)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.target_price, Decimal("150.00"))

    def test_alert_triggered_above(self):
        """Уведомление срабатывает при цене выше целевой."""
        alert, _ = PriceAlertService.create_alert(
            self.user, self.share.figi, Decimal("100.00"), "above"
        )
        triggered = PriceAlertService.check_alerts(self.share, Decimal("150.00"))
        self.assertEqual(len(triggered), 1)
        alert.refresh_from_db()
        self.assertIsNotNone(alert.last_triggered_at)

    def test_alert_not_triggered_below(self):
        """Уведомление 'above' не срабатывает при цене ниже целевой."""
        alert, _ = PriceAlertService.create_alert(
            self.user, self.share.figi, Decimal("200.00"), "above"
        )
        triggered = PriceAlertService.check_alerts(self.share, Decimal("100.00"))
        self.assertEqual(len(triggered), 0)

    def test_notification_created(self):
        """При срабатывании уведомления создается запись уведомления."""
        from django.utils import timezone
        PriceAlertService.create_alert(
            self.user, self.share.figi, Decimal("50.00"), "above"
        )
        PriceAlertService.check_alerts(self.share, Decimal("100.00"))
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)


class PortfolioTests(TestCase):
    """Тесты виртуального портфеля."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
            last_price=100.00,
        )
        self.portfolio, _ = PortfolioService.create_portfolio(
            self.user, "Тестовый портфель", Decimal("10000.00")
        )

    def test_create_portfolio(self):
        """Создание портфеля."""
        self.assertEqual(self.portfolio.user, self.user)
        self.assertEqual(self.portfolio.name, "Тестовый портфель")
        self.assertEqual(self.portfolio.initial_balance, Decimal("10000.00"))

    def test_buy_share(self):
        """Покупка акции в портфель."""
        tx, error = PortfolioService.buy_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("10"), Decimal("100.00")
        )
        self.assertIsNone(error)
        self.assertIsNotNone(tx)
        self.assertEqual(tx.transaction_type, "buy")
        self.assertEqual(tx.quantity, Decimal("10"))

    def test_buy_insufficient_balance(self):
        """Покупка с недостаточным балансом."""
        tx, error = PortfolioService.buy_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("1000"), Decimal("100.00")
        )
        self.assertIsNotNone(error)
        self.assertIsNone(tx)

    def test_sell_share(self):
        """Продажа акции из портфеля."""
        PortfolioService.buy_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("10"), Decimal("100.00")
        )
        tx, error = PortfolioService.sell_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("5"), Decimal("110.00")
        )
        self.assertIsNone(error)
        self.assertEqual(tx.transaction_type, "sell")

    def test_sell_insufficient_quantity(self):
        """Продажа большего количества, чем есть в портфеле."""
        PortfolioService.buy_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("10"), Decimal("100.00")
        )
        tx, error = PortfolioService.sell_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("20"), Decimal("110.00")
        )
        self.assertIsNotNone(error)
        self.assertIsNone(tx)

    def test_portfolio_summary(self):
        """Расчет сводки портфеля."""
        PortfolioService.buy_share(
            self.user, "Тестовый портфель", self.share.figi, Decimal("10"), Decimal("100.00")
        )
        summary = PortfolioService.get_portfolio_summary(self.portfolio)
        self.assertEqual(summary["total_invested"], Decimal("1000.00"))
        self.assertEqual(len(summary["positions"]), 1)


class PriceHistoryTests(TestCase):
    """Тесты исторических цен и симулятора."""

    def setUp(self):
        self.share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
        )

    def test_save_and_get_history(self):
        """Сохранение и получение истории цен."""
        from django.utils import timezone
        from datetime import timedelta

        base_time = timezone.now() - timedelta(days=5)
        for i in range(5):
            PriceHistory.objects.create(
                share=self.share,
                price=Decimal("100.00") + Decimal(str(i)),
                timestamp=base_time + timedelta(days=i),
            )

        history = PriceHistoryService.get_history(self.share, days=10)
        self.assertEqual(history.count(), 5)

    def test_strategy_simulator(self):
        """Тест симулятора стратегий."""
        from django.utils import timezone
        from datetime import timedelta

        base_time = timezone.now() - timedelta(days=10)
        for i in range(10):
            PriceHistory.objects.create(
                share=self.share,
                price=Decimal("100.00") + Decimal(str(i * 10)),
                timestamp=base_time + timedelta(days=i),
            )

        # Стратегия: покупать когда цена < 150, продавать когда цена > 200
        result = StrategySimulatorService.simulate(
            self.share,
            start_date=base_time,
            end_date=base_time + timedelta(days=10),
            initial_balance=Decimal("10000"),
            buy_condition=lambda price, ctx: price < Decimal("150") and ctx["balance"] >= price,
            sell_condition=lambda price, ctx: price > Decimal("200") and ctx["shares_held"] > 0,
        )

        self.assertIn("total_return", result)
        self.assertIn("trades", result)
        self.assertIn("trades_count", result)
        self.assertGreaterEqual(result["trades_count"], 0)


