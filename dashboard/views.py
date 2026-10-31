from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, View, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal

from .forms import (
    ShareModelForm,
    WatchlistForm,
    PriceAlertForm,
    PortfolioForm,
)
from .models import Share, Watchlist, WatchlistItem, PriceAlert, Portfolio
from .services.graph import get_graph
from .services.watchlist_service import (
    WatchlistService,
    PriceAlertService,
    NotificationService,
)
from .services.portfolio_service import PortfolioService


class IsUserAuthenticatedMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect("user:auth")


class ShareListView(ListView):
    """Список акций"""

    model = Share
    template_name = "dashboard/list.html"
    paginate_by = 100
    ordering = ["name"]


class ShareDetailView(View):
    @staticmethod
    def get(request, pk):
        share = get_object_or_404(Share, id=pk)

        return render(
            request,
            "dashboard/detail.html",
            {"plot_div": get_graph(share), "share": share},
        )


class ShareCreateView(IsUserAuthenticatedMixin, CreateView):
    """Добавление инструмента"""

    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareUpdateView(IsUserAuthenticatedMixin, UpdateView):
    """Редактирование инструмента"""

    model = Share
    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление задачи"""

    model = Share
    template_name = "dashboard/delete.html"
    success_url = reverse_lazy("dashboard:index")


# === Watchlists ===


class WatchlistListView(IsUserAuthenticatedMixin, ListView):
    """Список списков наблюдения пользователя"""

    model = Watchlist
    template_name = "dashboard/watchlist_list.html"
    context_object_name = "watchlists"

    def get_queryset(self):
        return WatchlistService.get_user_watchlists(self.request.user)


class WatchlistCreateView(IsUserAuthenticatedMixin, CreateView):
    """Создание списка наблюдения"""

    model = Watchlist
    form_class = WatchlistForm
    template_name = "dashboard/watchlist_form.html"
    success_url = reverse_lazy("dashboard:watchlist_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class WatchlistDetailView(IsUserAuthenticatedMixin, View):
    """Детальная страница списка наблюдения"""

    def get(self, request, pk):
        watchlist = get_object_or_404(Watchlist, id=pk, user=request.user)
        items = watchlist.items.select_related("share").all()
        return render(
            request,
            "dashboard/watchlist_detail.html",
            {"watchlist": watchlist, "items": items},
        )


class WatchlistDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление списка наблюдения"""

    model = Watchlist
    template_name = "dashboard/watchlist_confirm_delete.html"
    success_url = reverse_lazy("dashboard:watchlist_list")

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)


class WatchlistAddShareView(IsUserAuthenticatedMixin, View):
    """Добавить акцию в список наблюдения"""

    def post(self, request, pk):
        watchlist = get_object_or_404(Watchlist, id=pk, user=request.user)
        share_figi = request.POST.get("share_figi")
        if not share_figi:
            messages.error(request, "Не указан FIGI акции")
            return redirect("dashboard:watchlist_detail", pk=pk)

        _, error = WatchlistService.add_share_to_watchlist(
            request.user, watchlist.name, share_figi
        )
        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Акция добавлена в список наблюдения")
        return redirect("dashboard:watchlist_detail", pk=pk)


class WatchlistRemoveShareView(IsUserAuthenticatedMixin, View):
    """Удалить акцию из списка наблюдения"""

    def post(self, request, pk, item_id):
        watchlist = get_object_or_404(Watchlist, id=pk, user=request.user)
        item = get_object_or_404(WatchlistItem, id=item_id, watchlist=watchlist)
        item.delete()
        messages.success(request, "Акция удалена из списка наблюдения")
        return redirect("dashboard:watchlist_detail", pk=pk)


# === Price Alerts ===


class PriceAlertListView(IsUserAuthenticatedMixin, ListView):
    """Список ценовых уведомлений"""

    model = PriceAlert
    template_name = "dashboard/price_alert_list.html"
    context_object_name = "alerts"

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user).select_related(
            "share"
        )


class PriceAlertCreateView(IsUserAuthenticatedMixin, CreateView):
    """Создание ценового уведомления"""

    model = PriceAlert
    form_class = PriceAlertForm
    template_name = "dashboard/price_alert_form.html"
    success_url = reverse_lazy("dashboard:price_alert_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {"user": self.request.user}
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Фильтруем акции только те, что есть в БД
        form.fields["share"].queryset = Share.objects.all()
        return super().form_valid(form)


class PriceAlertDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление ценового уведомления"""

    model = PriceAlert
    template_name = "dashboard/price_alert_confirm_delete.html"
    success_url = reverse_lazy("dashboard:price_alert_list")

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user)


# === Notifications ===


class NotificationListView(IsUserAuthenticatedMixin, ListView):
    """Список уведомлений пользователя"""

    model = PriceAlert  # Используем PriceAlert как заглушку для шаблона, но в контексте передаем уведомления
    template_name = "dashboard/notification_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        from dashboard.models import Notification

        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(IsUserAuthenticatedMixin, View):
    """Отметить уведомление как прочитанное"""

    def post(self, request, pk):
        from dashboard.models import Notification

        notification = get_object_or_404(
            Notification, id=pk, user=request.user
        )
        notification.is_read = True
        notification.save()
        return redirect("dashboard:notification_list")


class NotificationMarkAllReadView(IsUserAuthenticatedMixin, View):
    """Отметить все уведомления как прочитанные"""

    def post(self, request):
        NotificationService.mark_all_read(request.user)
        messages.success(request, "Все уведомления отмечены как прочитанные")
        return redirect("dashboard:notification_list")


# === Portfolios ===


class PortfolioListView(IsUserAuthenticatedMixin, ListView):
    """Список портфелей пользователя"""

    model = Portfolio
    template_name = "dashboard/portfolio_list.html"
    context_object_name = "portfolios"

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)


class PortfolioCreateView(IsUserAuthenticatedMixin, CreateView):
    """Создание портфеля"""

    model = Portfolio
    form_class = PortfolioForm
    template_name = "dashboard/portfolio_form.html"
    success_url = reverse_lazy("dashboard:portfolio_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PortfolioDetailView(IsUserAuthenticatedMixin, View):
    """Детальная страница портфеля"""

    def get(self, request, pk):
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        summary = PortfolioService.get_portfolio_summary(portfolio)
        return render(
            request,
            "dashboard/portfolio_detail.html",
            {"portfolio": portfolio, "summary": summary},
        )


class PortfolioDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление портфеля"""

    model = Portfolio
    template_name = "dashboard/portfolio_confirm_delete.html"
    success_url = reverse_lazy("dashboard:portfolio_list")

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)


class PortfolioBuyView(IsUserAuthenticatedMixin, View):
    """Покупка акции в портфель"""

    def post(self, request, pk):
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        share_figi = request.POST.get("share_figi")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        if not all([share_figi, quantity, price]):
            messages.error(request, "Заполните все поля")
            return redirect("dashboard:portfolio_detail", pk=pk)

        try:
            quantity = Decimal(quantity)
            price = Decimal(price)
        except Exception:
            messages.error(request, "Некорректные значения количества или цены")
            return redirect("dashboard:portfolio_detail", pk=pk)

        _, error = PortfolioService.buy_share(
            request.user, portfolio.name, share_figi, quantity, price
        )
        if error:
            messages.error(request, error)
        else:
            messages.success(
                request, f"Куплено {quantity} акций по цене {price}"
            )
        return redirect("dashboard:portfolio_detail", pk=pk)


class PortfolioSellView(IsUserAuthenticatedMixin, View):
    """Продажа акции из портфеля"""

    def post(self, request, pk):
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        share_figi = request.POST.get("share_figi")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        if not all([share_figi, quantity, price]):
            messages.error(request, "Заполните все поля")
            return redirect("dashboard:portfolio_detail", pk=pk)

        try:
            quantity = Decimal(quantity)
            price = Decimal(price)
        except Exception:
            messages.error(request, "Некорректные значения количества или цены")
            return redirect("dashboard:portfolio_detail", pk=pk)

        _, error = PortfolioService.sell_share(
            request.user, portfolio.name, share_figi, quantity, price
        )
        if error:
            messages.error(request, error)
        else:
            messages.success(
                request, f"Продано {quantity} акций по цене {price}"
            )
        return redirect("dashboard:portfolio_detail", pk=pk)
