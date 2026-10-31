"""Virtual portfolio operations."""
from django.db import transaction
from dashboard.models import Portfolio, PortfolioPosition, PortfolioTransaction, Share
from config.settings import logger


class PortfolioError(Exception):
    pass


@transaction.atomic
def buy(portfolio: Portfolio, share: Share, quantity: float, price: float = None):
    if quantity <= 0:
        raise PortfolioError("Количество должно быть > 0")
    price = price if price is not None else (share.last_price or 0)
    if price <= 0:
        raise PortfolioError("Нет актуальной цены")
    total = quantity * price
    if portfolio.cash_balance < total:
        raise PortfolioError("Недостаточно средств")
    portfolio.cash_balance -= total
    portfolio.save(update_fields=["cash_balance"])

    pos, created = PortfolioPosition.objects.get_or_create(
        portfolio=portfolio, share=share,
        defaults={"quantity": 0, "avg_price": 0},
    )
    new_qty = pos.quantity + quantity
    if new_qty > 0:
        pos.avg_price = (pos.avg_price * pos.quantity + price * quantity) / new_qty
    pos.quantity = new_qty
    pos.save()

    PortfolioTransaction.objects.create(
        portfolio=portfolio, share=share, side=PortfolioTransaction.BUY,
        quantity=quantity, price=price, total=total,
    )
    logger.info(f"BUY {quantity} {share.ticker} @ {price} for portfolio {portfolio.id}")
    return pos


@transaction.atomic
def sell(portfolio: Portfolio, share: Share, quantity: float, price: float = None):
    if quantity <= 0:
        raise PortfolioError("Количество должно быть > 0")
    price = price if price is not None else (share.last_price or 0)
    if price <= 0:
        raise PortfolioError("Нет актуальной цены")
    try:
        pos = PortfolioPosition.objects.get(portfolio=portfolio, share=share)
    except PortfolioPosition.DoesNotExist:
        raise PortfolioError("Нет позиции по этой акции")
    if pos.quantity < quantity:
        raise PortfolioError("Недостаточно акций в позиции")
    total = quantity * price
    portfolio.cash_balance += total
    portfolio.save(update_fields=["cash_balance"])

    pos.quantity -= quantity
    if pos.quantity == 0:
        pos.avg_price = 0
    pos.save()

    PortfolioTransaction.objects.create(
        portfolio=portfolio, share=share, side=PortfolioTransaction.SELL,
        quantity=quantity, price=price, total=total,
    )
    logger.info(f"SELL {quantity} {share.ticker} @ {price} for portfolio {portfolio.id}")
    return pos


def portfolio_summary(portfolio: Portfolio):
    positions = list(portfolio.positions.select_related("share").all())
    positions_value = sum(p.current_value for p in positions)
    total_pnl = sum(p.pnl for p in positions)
    return {
        "cash": portfolio.cash_balance,
        "positions_value": positions_value,
        "total_value": portfolio.cash_balance + positions_value,
        "total_pnl": total_pnl,
        "positions": positions,
    }
