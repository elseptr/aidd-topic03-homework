"""Graph generation. Demo mode uses synthetic history."""
from datetime import timedelta, datetime, timezone
import random

from plotly.graph_objs import Scatter
from plotly.offline import plot

from config.settings import TINKOFF_TOKEN, logger


def get_graph(share, days=180):
    """Return plotly div with price history."""
    if not TINKOFF_TOKEN:
        return _demo_graph(share, days)
    try:
        from tinkoff.invest import CandleInterval, Client
        from tinkoff.invest.utils import now
        with Client(TINKOFF_TOKEN) as client:
            x_data, y_data = [], []
            for candle in client.get_all_candles(
                figi=share.figi,
                from_=now() - timedelta(days=days),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
            ):
                x_data.append(candle.time.date())
                y_data.append(candle.close.units + candle.close.nano / 1e9)
        return plot(
            [Scatter(x=x_data, y=y_data, mode="lines", name=share.ticker, opacity=0.8, marker_color="red")],
            output_type="div",
            show_link=False,
            link_text="",
        )
    except Exception as e:
        logger.warning(f"tinkoff graph failed: {e} — using demo")
        return _demo_graph(share, days)


def _demo_graph(share, days=180):
    """Synthetic price series for demo."""
    base = share.last_price or 100.0
    x_data, y_data = [], []
    price = base * 0.85
    start = datetime.now(timezone.utc) - timedelta(days=days)
    for i in range(days):
        d = start + timedelta(days=i)
        price = price * (1 + random.uniform(-0.015, 0.018))
        x_data.append(d.date())
        y_data.append(round(price, 2))
    # end near current last_price
    if y_data:
        y_data[-1] = base
    return plot(
        [Scatter(x=x_data, y=y_data, mode="lines", name=share.ticker or "demo", opacity=0.8, marker_color="steelblue")],
        output_type="div",
        show_link=False,
        link_text="",
    )
