from django import forms
from .models import (
    Share, Watchlist, WatchlistItem, Portfolio, PortfolioTransaction,
    Strategy,
)


class ShareModelForm(forms.ModelForm):
    class Meta:
        model = Share
        fields = "__all__"


class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ["name"]


class WatchlistItemForm(forms.ModelForm):
    class Meta:
        model = WatchlistItem
        fields = ["share", "target_price", "direction", "is_active"]


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ["name", "cash_balance"]


class TradeForm(forms.Form):
    share = forms.ModelChoiceField(queryset=Share.objects.all())
    quantity = forms.FloatField(min_value=0.01)
    price = forms.FloatField(required=False, help_text="Оставьте пустым для рыночной цены")


class StrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        fields = ["name", "share", "action", "threshold_price", "direction", "quantity", "is_active", "portfolio"]
