from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from dashboard.models import PriceHistory, Share
from dashboard.services.demo_market_data import get_candles_demo
from config.settings import logger


class PriceHistoryService:
    """Сервис для работы с историческими ценами."""

    @staticmethod
    def save_candles(share, candles):
        """Сохранить исторические свечи в базу данных."""
        saved = 0
        for candle in candles:
            timestamp = (
                candle["time"] if isinstance(candle, dict) else candle.time
            )
            price = (
                Decimal(str(candle["close"]))
                if isinstance(candle, dict)
                else Decimal(str(candle.close.units))
                + Decimal(str(getattr(candle.close, "nano", 0) or 0))
                / Decimal(10 ** 9)
            )

            obj, created = PriceHistory.objects.update_or_create(
                share=share,
                timestamp=timestamp,
                defaults={"price": price},
            )
            if created:
                saved += 1
        return saved

    @staticmethod
    def fetch_and_save_history(share, days=180, use_demo_fallback=True):
        """Загрузить историю цен и сохранить в БД."""
        try:
            from tinkoff.invest import CandleInterval, Client
            from tinkoff.invest.utils import now
            from config.settings import TINKOFF_TOKEN

            candles = []
            with Client(TINKOFF_TOKEN) as client:
                for candle in client.get_all_candles(
                    figi=share.figi,
                    from_=now() - timedelta(days=days),
                    interval=CandleInterval.CANDLE_INTERVAL_DAY,
                ):
                    candles.append(
                        {
                            "time": candle.time,
                            "close": candle.close,
                        }
                    )
        except Exception as e:
            logger.error(
                f"Tinkoff API error for price history share id={share.id}: {e}. "
                f"Demo fallback={'enabled' if use_demo_fallback else 'disabled'}."
            )
            if use_demo_fallback:
                candles = get_candles_demo(share, days=days, interval="day")
            else:
                return 0

        return PriceHistoryService.save_candles(share, candles)

    @staticmethod
    def get_history(share, days=None):
        """Получить историю цен из БД."""
        queryset = PriceHistory.objects.filter(share=share).order_by("timestamp")
        if days:
            cutoff = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=cutoff)
        return queryset


class StrategySimulatorService:
    """Сервис для симуляции инвестиционных стратегий на исторических данных."""

    @staticmethod
    def simulate(
        share,
        start_date,
        end_date,
        initial_balance=Decimal("10000"),
        buy_condition=None,
        sell_condition=None,
    ):
        """Запустить симуляцию стратегии на исторических данных.

        buy_condition: функция(price, context) -> bool
        sell_condition: функция(price, context) -> bool

        Возвращает словарь с результатами симуляции.
        """
        from decimal import Decimal as D

        history = (
            PriceHistory.objects.filter(share=share)
            .filter(timestamp__gte=start_date)
            .filter(timestamp__lte=end_date)
            .order_by("timestamp")
        )

        if not history.exists():
            return {
                "error": "Нет исторических данных для указанного периода",
                "trades": [],
                "metrics": {},
            }

        balance = D(str(initial_balance))
        shares_held = D("0")
        trades = []
        portfolio_values = []

        for record in history:
            price = D(str(record.price))
            context = {
                "balance": balance,
                "shares_held": shares_held,
                "price": price,
                "timestamp": record.timestamp,
            }

            # Проверяем условия продажи сначала
            if shares_held > 0 and sell_condition and sell_condition(price, context):
                sell_amount = shares_held * price
                balance += sell_amount
                trades.append(
                    {
                        "type": "sell",
                        "price": price,
                        "quantity": shares_held,
                        "total": sell_amount,
                        "timestamp": record.timestamp,
                    }
                )
                shares_held = D("0")

            # Проверяем условия покупки
            elif balance >= price and buy_condition and buy_condition(price, context):
                quantity = balance // price
                cost = quantity * price
                balance -= cost
                shares_held += quantity
                trades.append(
                    {
                        "type": "buy",
                        "price": price,
                        "quantity": quantity,
                        "total": cost,
                        "timestamp": record.timestamp,
                    }
                )

            current_value = balance + shares_held * price
            portfolio_values.append(
                {"timestamp": record.timestamp, "value": current_value}
            )

        final_price = D(str(history.last().price))
        final_value = balance + shares_held * final_price
        total_return = final_value - D(str(initial_balance))
        total_return_percent = (
            (total_return / D(str(initial_balance)) * D("100"))
            if initial_balance > 0
            else D("0")
        )

        # Расчет максимальной просадки
        max_drawdown = D("0")
        peak = D("0")
        for pv in portfolio_values:
            if pv["value"] > peak:
                peak = pv["value"]
            drawdown = peak - pv["value"]
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        max_drawdown_percent = (
            (max_drawdown / peak * D("100")) if peak > 0 else D("0")
        )

        return {
            "share": share,
            "initial_balance": D(str(initial_balance)),
            "final_value": final_value,
            "total_return": total_return,
            "total_return_percent": total_return_percent,
            "max_drawdown": max_drawdown,
            "max_drawdown_percent": max_drawdown_percent,
            "trades": trades,
            "trades_count": len(trades),
            "final_balance": balance,
            "final_shares": shares_held,
            "portfolio_values": portfolio_values,
        }
