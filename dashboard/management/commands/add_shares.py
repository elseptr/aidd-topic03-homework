from django.core.management.base import BaseCommand
from dashboard.models import Share


DEMO_SHARES = [
    {"figi": "BBG000B9XRY4", "isin": "US0378331005", "name": "Apple Inc", "ticker": "AAPL", "currency": "usd", "uid": "a9eb4238-eba9-488c-b102-b6140fd08e38", "last_price": 175.50},
    {"figi": "BBG000BVPV84", "isin": "US5949181045", "name": "Microsoft", "ticker": "MSFT", "currency": "usd", "uid": "b1eb4238-eba9-488c-b102-b6140fd08e01", "last_price": 380.20},
    {"figi": "BBG000N9MNX3", "isin": "US02079K3059", "name": "Alphabet", "ticker": "GOOGL", "currency": "usd", "uid": "c2eb4238-eba9-488c-b102-b6140fd08e02", "last_price": 140.10},
    {"figi": "BBG000BPH459", "isin": "US0231351067", "name": "Amazon", "ticker": "AMZN", "currency": "usd", "uid": "d3eb4238-eba9-488c-b102-b6140fd08e03", "last_price": 178.30},
    {"figi": "BBG000B9XVV8", "isin": "US67066G1040", "name": "NVIDIA", "ticker": "NVDA", "currency": "usd", "uid": "e4eb4238-eba9-488c-b102-b6140fd08e04", "last_price": 875.00},
    {"figi": "BBG004730N88", "isin": "RU0009029540", "name": "Сбербанк", "ticker": "SBER", "currency": "rub", "uid": "f5eb4238-eba9-488c-b102-b6140fd08e05", "last_price": 280.50},
    {"figi": "BBG004731032", "isin": "RU0007661625", "name": "Газпром", "ticker": "GAZP", "currency": "rub", "uid": "g6eb4238-eba9-488c-b102-b6140fd08e06", "last_price": 155.20},
]


class Command(BaseCommand):
    help = "Add demo shares to DB (no Tinkoff token required)"

    def handle(self, *args, **options):
        for data in DEMO_SHARES:
            obj, created = Share.objects.get_or_create(
                figi=data["figi"],
                defaults={
                    "isin": data["isin"],
                    "name": data["name"],
                    "ticker": data["ticker"],
                    "currency": data["currency"],
                    "uid": data["uid"],
                    "last_price": data["last_price"],
                    "is_trend_high": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added {obj.ticker}"))
            else:
                self.stdout.write(f"Exists {obj.ticker}")
