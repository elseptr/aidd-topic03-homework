from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from dashboard.models import (
    Portfolio,
    PortfolioPosition,
    PortfolioTransaction,
    Share,
)

User = get_user_model()


class PortfolioService:
    """Сервис для работы с виртуальным портфелем."""

    @staticmethod
    def create_portfolio(user, name, initial_balance=Decimal("0")):
        """Создать виртуальный портфель."""
        portfolio, created = Portfolio.objects.get_or_create(
            user=user,
            name=name,
            defaults={"initial_balance": initial_balance},
        )
        return portfolio, created

    @staticmethod
    def get_user_portfolios(user):
        """Получить все портфели пользователя."""
        return Portfolio.objects.filter(user=user).prefetch_related(
            "positions__share", "transactions__share"
        )

    @staticmethod
    @transaction.atomic
    def buy_share(user, portfolio_name, share_figi, quantity, price):
        """Купить акции в портфель."""
        try:
            portfolio = Portfolio.objects.get(user=user, name=portfolio_name)
        except Portfolio.DoesNotExist:
            return None, "Портфель не найден"

        try:
            share = Share.objects.get(figi=share_figi)
        except Share.DoesNotExist:
            return None, "Акция не найдена"

        quantity = Decimal(str(quantity))
        price = Decimal(str(price))
        total_amount = quantity * price

        # Проверяем баланс
        if portfolio.initial_balance < total_amount:
            return None, "Недостаточно средств на балансе портфеля"

        # Создаем транзакцию покупки
        transaction_obj = PortfolioTransaction.objects.create(
            portfolio=portfolio,
            share=share,
            transaction_type="buy",
            quantity=quantity,
            price=price,
            total_amount=total_amount,
        )

        # Обновляем или создаем позицию
        position, created = PortfolioPosition.objects.get_or_create(
            portfolio=portfolio,
            share=share,
            defaults={"quantity": quantity, "average_price": price},
        )

        if not created:
            # Пересчитываем среднюю цену (взвешенное среднее)
            total_quantity = position.quantity + quantity
            total_cost = (
                position.average_price * position.quantity + price * quantity
            )
            position.quantity = total_quantity
            position.average_price = total_cost / total_quantity
            position.save(update_fields=["quantity", "average_price", "updated_at"])

        # Уменьшаем баланс портфеля
        portfolio.initial_balance -= total_amount
        portfolio.save(update_fields=["initial_balance", "updated_at"])

        return transaction_obj, None

    @staticmethod
    @transaction.atomic
    def sell_share(user, portfolio_name, share_figi, quantity, price):
        """Продать акции из портфеля."""
        try:
            portfolio = Portfolio.objects.get(user=user, name=portfolio_name)
        except Portfolio.DoesNotExist:
            return None, "Портфель не найден"

        try:
            share = Share.objects.get(figi=share_figi)
        except Share.DoesNotExist:
            return None, "Акция не найдена"

        quantity = Decimal(str(quantity))
        price = Decimal(str(price))
        total_amount = quantity * price

        try:
            position = PortfolioPosition.objects.get(
                portfolio=portfolio, share=share
            )
        except PortfolioPosition.DoesNotExist:
            return None, "Акции нет в портфеле"

        if position.quantity < quantity:
            return None, "Недостаточно акций для продажи"

        # Создаем транзакцию продажи
        transaction_obj = PortfolioTransaction.objects.create(
            portfolio=portfolio,
            share=share,
            transaction_type="sell",
            quantity=quantity,
            price=price,
            total_amount=total_amount,
        )

        # Обновляем позицию
        position.quantity -= quantity
        if position.quantity == 0:
            position.delete()
        else:
            position.save(update_fields=["quantity", "updated_at"])

        # Увеличиваем баланс портфеля
        portfolio.initial_balance += total_amount
        portfolio.save(update_fields=["initial_balance", "updated_at"])

        return transaction_obj, None

    @staticmethod
    def get_portfolio_summary(portfolio):
        """Получить сводку по портфелю (стоимость, прибыль/убыток)."""
        positions = portfolio.positions.select_related("share").all()
        positions_data = []
        total_invested = Decimal("0")
        total_current_value = Decimal("0")

        for position in positions:
            current_price = (
                Decimal(str(position.share.last_price))
                if position.share.last_price is not None
                else None
            )
            if current_price is not None:
                current_value = current_price * position.quantity
                cost = position.average_price * position.quantity
                profit_loss = current_value - cost
                profit_loss_percent = (
                    (profit_loss / cost * Decimal("100")) if cost > 0 else Decimal("0")
                )
            else:
                current_value = Decimal("0")
                cost = position.average_price * position.quantity
                profit_loss = Decimal("0")
                profit_loss_percent = Decimal("0")

            total_invested += cost
            total_current_value += current_value

            positions_data.append(
                {
                    "share": position.share,
                    "quantity": position.quantity,
                    "average_price": position.average_price,
                    "current_price": current_price,
                    "current_value": current_value,
                    "cost": cost,
                    "profit_loss": profit_loss,
                    "profit_loss_percent": profit_loss_percent,
                }
            )

        total_profit_loss = total_current_value - total_invested
        total_profit_loss_percent = (
            (total_profit_loss / total_invested * Decimal("100"))
            if total_invested > 0
            else Decimal("0")
        )

        return {
            "portfolio": portfolio,
            "positions": positions_data,
            "initial_balance": portfolio.initial_balance,
            "total_invested": total_invested,
            "total_current_value": total_current_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percent": total_profit_loss_percent,
            "total_value": portfolio.initial_balance + total_current_value,
        }
