from django.core.management.base import BaseCommand

from config.settings import TINKOFF_TOKEN
from dashboard.models import Share


class Command(BaseCommand):
    help = "Add shares to DB from Tinkoff Invest API (or seed demo data if API unavailable)"

    def handle(self, *args, **options):
        if not TINKOFF_TOKEN:
            self.stdout.write(
                self.style.WARNING(
                    "TINKOFF_TOKEN is empty — seeding a few demo shares instead of calling the API"
                )
            )
            self._seed_demo()
            return

        try:
            from t_tech.invest import Client
        except ImportError:
            self.stdout.write(
                self.style.WARNING(
                    "t-tech-investments package is not installed — seeding demo shares"
                )
            )
            self._seed_demo()
            return

        added = 0
        skipped = 0
        errors = 0

        with Client(TINKOFF_TOKEN) as client:
            shares = client.instruments.shares()
            for share in shares.instruments:
                try:
                    _, created = Share.objects.get_or_create(
                        figi=share.figi,
                        defaults={
                            "name": share.name,
                            "isin": share.isin,
                            "ticker": share.ticker,
                            "currency": share.currency,
                            "uid": share.uid,
                        },
                    )
                    if created:
                        added += 1
                    else:
                        skipped += 1
                except Exception as e:
                    self.stderr.write(
                        f"Error creating share {getattr(share, 'ticker', 'unknown')}: {e}"
                    )
                    errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Shares import finished: added={added}, skipped={skipped}, errors={errors}"
            )
        )

    def _seed_demo(self):
        demo = [
            ("BBG000B9XRY4", "US0378331005", "Apple Inc", "AAPL", "usd", "aapl-uid"),
            ("BBG000BVPV84", "US5949181045", "Microsoft Corporation", "MSFT", "usd", "msft-uid"),
            ("BBG000N7TDX9", "US0231351067", "Amazon.com Inc", "AMZN", "usd", "amzn-uid"),
            ("BBG000NL6H01", "US67066G1040", "NVIDIA Corporation", "NVDA", "usd", "nvda-uid"),
            ("BBG000BPH459", "US30303M1027", "Meta Platforms Inc", "META", "usd", "meta-uid"),
        ]
        added = 0
        for figi, isin, name, ticker, currency, uid in demo:
            _, created = Share.objects.get_or_create(
                figi=figi,
                defaults={
                    "isin": isin,
                    "name": name,
                    "ticker": ticker,
                    "currency": currency,
                    "uid": uid,
                    "last_price": 100.0,
                },
            )
            if created:
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Demo shares seeded: added={added}"))
