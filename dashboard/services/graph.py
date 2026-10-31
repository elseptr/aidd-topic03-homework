from datetime import timedelta

from decimal import Decimal

from plotly.graph_objs import Scatter
from plotly.offline import plot
from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

from config.settings import TINKOFF_TOKEN, logger

from dashboard.services.demo_market_data import get_candles_demo


def _price_to_decimal(candle_close):
    """Преобразовать котировку свечи в Decimal."""
    nano = getattr(candle_close, "nano", 0) or 0
    units = getattr(candle_close, "units", None)
    if units is None:
        # Демо-словарь
        return Decimal(str(candle_close["close"]))
    return Decimal(str(units)) + Decimal(nano) / Decimal(10 ** 9)


def _candle_time(candle):
    """Получить время свечи (поддержка и реальных, и демо-данных)."""
    if hasattr(candle, "time"):
        return candle.time
    return candle["time"]


def _candle_close(candle):
    """Получить цену закрытия свечи (поддержка и реальных, и демо-данных)."""
    if hasattr(candle, "close"):
        return _price_to_decimal(candle.close)
    return Decimal(str(candle["close"]))


def get_graph(share, use_demo_fallback=True):
    """Построить график исторических цен акции за последние 180 дней.

    Возвращает HTML-блок с графиком Plotly или пустую строку,
    если данные не получены.
    """
    try:
        with Client(TINKOFF_TOKEN) as client:
            x_data, y_data = [], []
            candles = list(
                client.get_all_candles(
                    figi=share.figi,
                    from_=now() - timedelta(days=180),
                    interval=CandleInterval.CANDLE_INTERVAL_DAY,
                )
            )
            if not candles:
                if use_demo_fallback:
                    return _build_demo_graph(share)
                return ""

            for candle in candles:
                x_data.append(_candle_time(candle).date())
                y_data.append(_candle_close(candle))

    except Exception as e:
        logger.error(
            f"Tinkoff API error for graph share id={share.id}: {e}. "
            f"Demo fallback={'enabled' if use_demo_fallback else 'disabled'}."
        )
        if use_demo_fallback:
            return _build_demo_graph(share)
        return ""

    plot_div = plot(
        [
            Scatter(
                x=x_data,
                y=[float(v) for v in y_data],
                mode="lines",
                name="test",
                opacity=0.8,
                marker_color="red",
            )
        ],
        output_type="div",
        show_link=False,
        link_text="",
    )
    return plot_div


def _build_demo_graph(share):
    """Построить демонстрационный график с синтетическими данными."""
    candles = get_candles_demo(share, days=180, interval="day")
    if not candles:
        return ""

    x_data = []
    y_data = []
    for candle in candles:
        x_data.append(_candle_time(candle).date())
        y_data.append(float(_candle_close(candle)))

    plot_div = plot(
        [
            Scatter(
                x=x_data,
                y=y_data,
                mode="lines",
                name="demo",
                opacity=0.8,
                marker_color="orange",
            )
        ],
        output_type="div",
        show_link=False,
        link_text="",
    )
    return plot_div
