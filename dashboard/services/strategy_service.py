"""Strategy simulator."""
from django.utils import timezone
from dashboard.models import Strategy, StrategyTrade
from dashboard.services.portfolio_service import buy, sell, PortfolioError
from config.settings import logger


def run_strategies():
    """Evaluate active strategies and execute virtual trades when conditions met."""
    strategies = Strategy.objects.filter(is_active=True).select_related("share", "portfolio", "user")
    executed = 0
    for strat in strategies:
        price = strat.share.last_price
        if price is None or not strat.condition_met(price):
            continue
        # simple anti-spam: one trade per strategy per hour
        recent = StrategyTrade.objects.filter(
            strategy=strat,
            executed_at__gte=timezone.now() - timezone.timedelta(hours=1),
        ).exists()
        if recent:
            continue
        total = strat.quantity * price
        note = f"Auto by strategy '{strat.name}'"
        try:
            if strat.action == Strategy.BUY:
                if strat.portfolio:
                    buy(strat.portfolio, strat.share, strat.quantity, price)
                StrategyTrade.objects.create(
                    strategy=strat, side=Strategy.BUY,
                    quantity=strat.quantity, price=price, total=total, note=note,
                )
            else:
                if strat.portfolio:
                    sell(strat.portfolio, strat.share, strat.quantity, price)
                StrategyTrade.objects.create(
                    strategy=strat, side=Strategy.SELL,
                    quantity=strat.quantity, price=price, total=total, note=note,
                )
            executed += 1
            logger.info(f"Strategy trade: {strat.name} {strat.action} {strat.quantity} @ {price}")
        except PortfolioError as e:
            logger.warning(f"Strategy {strat.id} skipped: {e}")
            StrategyTrade.objects.create(
                strategy=strat, side=strat.action,
                quantity=strat.quantity, price=price, total=total,
                note=f"Failed: {e}",
            )
    return executed


def strategy_performance(strategy: Strategy):
    trades = list(strategy.trades.all())
    buys = [t for t in trades if t.side == Strategy.BUY]
    sells = [t for t in trades if t.side == Strategy.SELL]
    invested = sum(t.total for t in buys)
    returned = sum(t.total for t in sells)
    return {
        "trades_count": len(trades),
        "buys": len(buys),
        "sells": len(sells),
        "invested": invested,
        "returned": returned,
        "pnl": returned - invested,
    }
