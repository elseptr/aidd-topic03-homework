from django import forms

from .models import Share, Watchlist, PriceAlert, Portfolio


class ShareModelForm(forms.ModelForm):
    """Инструмент"""

    class Meta:
        model = Share
        fields = "__all__"


class WatchlistForm(forms.ModelForm):
    """Форма создания/редактирования списка наблюдения"""

    class Meta:
        model = Watchlist
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Название списка наблюдения",
                }
            )
        }


class PriceAlertForm(forms.ModelForm):
    """Форма создания ценового уведомления"""

    class Meta:
        model = PriceAlert
        fields = ("share", "target_price", "alert_type", "is_active")
        widgets = {
            "share": forms.Select(attrs={"class": "form-control"}),
            "target_price": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Целевая цена"}
            ),
            "alert_type": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class PortfolioForm(forms.ModelForm):
    """Форма создания портфеля"""

    class Meta:
        model = Portfolio
        fields = ("name", "initial_balance")
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название портфеля"}
            ),
            "initial_balance": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Начальный баланс",
                    "step": "0.01",
                }
            ),
        }
