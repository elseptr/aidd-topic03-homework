from django.core.management.base import BaseCommand
from tinkoff.invest import Client

from config.settings import TINKOFF_TOKEN
from dashboard.models import Share


class Command(BaseCommand):
    help = "Add shares to DB"

    def handle(self, *args, **options):
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
