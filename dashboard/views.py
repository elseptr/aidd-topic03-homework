from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, View, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .forms import ShareModelForm, WatchlistForm, WatchlistItemForm, PortfolioForm, TradeForm, StrategyForm
from .models import (
    Share, Watchlist, WatchlistItem, PriceAlert,
    Portfolio, PortfolioPosition, PortfolioTransaction,
    PriceHistory, Strategy, StrategyTrade,
)
from .services.graph import get_graph
from .services.portfolio_service import buy, sell, portfolio_summary, PortfolioError
from .services.price_history_service import get_history, analyze_period, record_current_prices
from .services.watchlist_service import check_and_notify_targets
from .services.strategy_service import run_strategies, strategy_performance
from .tasks import update_last_price


class IsUserAuthenticatedMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect("dashboard:index")


class ShareListView(ListView):
    model = Share
    template_name = "dashboard/list.html"
    paginate_by = 100
    ordering = ["name"]


class ShareDetailView(View):
    def get(self, request, pk):
        share = get_object_or_404(Share, id=pk)
        days = int(request.GET.get("days", 180))
        analysis = analyze_period(share, days=min(days, 365))
        return render(
            request,
            "dashboard/detail.html",
            {
                "plot_div": get_graph(share, days=days),
                "share": share,
                "analysis": analysis,
                "days": days,
            },
        )


class ShareCreateView(IsUserAuthenticatedMixin, CreateView):
    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareUpdateView(IsUserAuthenticatedMixin, UpdateView):
    model = Share
    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareDeleteView(IsUserAuthenticatedMixin, DeleteView):
    model = Share
    template_name = "dashboard/delete.html"
    success_url = reverse_lazy("dashboard:index")


# ---------- Watchlist ----------

@login_required
def watchlist_list(request):
    lists = Watchlist.objects.filter(user=request.user).prefetch_related("items__share")
    alerts = PriceAlert.objects.filter(user=request.user, is_read=False)[:20]
    return render(request, "dashboard/watchlist_list.html", {"watchlists": lists, "alerts": alerts})


@login_required
def watchlist_create(request):
    if request.method == "POST":
        form = WatchlistForm(request.POST)
        if form.is_valid():
            wl = form.save(commit=False)
            wl.user = request.user
            wl.save()
            messages.success(request, "Список создан")
            return redirect("dashboard:watchlist_list")
    else:
        form = WatchlistForm()
    return render(request, "dashboard/watchlist_form.html", {"form": form})


@login_required
def watchlist_item_add(request, wl_id):
    wl = get_object_or_404(Watchlist, id=wl_id, user=request.user)
    if request.method == "POST":
        form = WatchlistItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.watchlist = wl
            item.save()
            messages.success(request, "Акция добавлена в список")
            return redirect("dashboard:watchlist_list")
    else:
        form = WatchlistItemForm()
    return render(request, "dashboard/watchlist_item_form.html", {"form": form, "watchlist": wl})


@login_required
def watchlist_item_delete(request, item_id):
    item = get_object_or_404(WatchlistItem, id=item_id, watchlist__user=request.user)
    item.delete()
    messages.success(request, "Удалено")
    return redirect("dashboard:watchlist_list")


@login_required
def mark_alerts_read(request):
    PriceAlert.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("dashboard:watchlist_list")


# ---------- Portfolio ----------

@login_required
def portfolio_list(request):
    portfolios = Portfolio.objects.filter(user=request.user)
    if not portfolios.exists():
        Portfolio.objects.create(user=request.user, name="Основной портфель")
        portfolios = Portfolio.objects.filter(user=request.user)
    data = [(p, portfolio_summary(p)) for p in portfolios]
    return render(request, "dashboard/portfolio_list.html", {"portfolios": data})


@login_required
def portfolio_detail(request, pk):
    portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
    summary = portfolio_summary(portfolio)
    txs = portfolio.transactions.select_related("share")[:50]
    trade_form = TradeForm()
    return render(
        request,
        "dashboard/portfolio_detail.html",
        {"portfolio": portfolio, "summary": summary, "transactions": txs, "trade_form": trade_form},
    )


@login_required
def portfolio_trade(request, pk):
    portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
    if request.method != "POST":
        return redirect("dashboard:portfolio_detail", pk=pk)
    form = TradeForm(request.POST)
    side = request.POST.get("side", "buy")
    if form.is_valid():
        share = form.cleaned_data["share"]
        qty = form.cleaned_data["quantity"]
        price = form.cleaned_data.get("price") or None
        try:
            if side == "buy":
                buy(portfolio, share, qty, price)
                messages.success(request, f"Куплено {qty} {share.ticker}")
            else:
                sell(portfolio, share, qty, price)
                messages.success(request, f"Продано {qty} {share.ticker}")
        except PortfolioError as e:
            messages.error(request, str(e))
    else:
        messages.error(request, "Ошибка формы")
    return redirect("dashboard:portfolio_detail", pk=pk)


# ---------- Price history ----------

@login_required
def price_history_view(request, share_id):
    share = get_object_or_404(Share, id=share_id)
    days = int(request.GET.get("days", 30))
    history = get_history(share, days=days)
    analysis = analyze_period(share, days=days)
    # simple plot from history if available
    plot_div = get_graph(share, days=days)
    return render(
        request,
        "dashboard/price_history.html",
        {"share": share, "history": history, "analysis": analysis, "days": days, "plot_div": plot_div},
    )


# ---------- Strategies ----------

@login_required
def strategy_list(request):
    strategies = Strategy.objects.filter(user=request.user).select_related("share", "portfolio")
    perf = {s.id: strategy_performance(s) for s in strategies}
    return render(request, "dashboard/strategy_list.html", {"strategies": strategies, "perf": perf})


@login_required
def strategy_create(request):
    if request.method == "POST":
        form = StrategyForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.user = request.user
            s.save()
            messages.success(request, "Стратегия создана")
            return redirect("dashboard:strategy_list")
    else:
        form = StrategyForm()
        form.fields["portfolio"].queryset = Portfolio.objects.filter(user=request.user)
    return render(request, "dashboard/strategy_form.html", {"form": form})


@login_required
def strategy_toggle(request, pk):
    s = get_object_or_404(Strategy, id=pk, user=request.user)
    s.is_active = not s.is_active
    s.save(update_fields=["is_active"])
    return redirect("dashboard:strategy_list")


@login_required
def strategy_trades(request, pk):
    s = get_object_or_404(Strategy, id=pk, user=request.user)
    trades = s.trades.all()[:100]
    perf = strategy_performance(s)
    return render(request, "dashboard/strategy_trades.html", {"strategy": s, "trades": trades, "perf": perf})


# ---------- Manual trigger for demo ----------

@login_required
def run_update(request):
    """Manually trigger price update + history + alerts + strategies (demo)."""
    update_last_price()
    messages.success(request, "Цены обновлены, история записана, алерты и стратегии проверены")
    return redirect("dashboard:index")
