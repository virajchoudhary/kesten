import math

from .errors import DatasetError


def split_neutral_prices(observations: list[dict]) -> list[float]:
    """Express each raw close in the share units established by the first row."""
    cumulative_split = 1.0
    prices = []
    for observation in observations:
        try:
            cumulative_split *= observation["split_ratio"]
            price = observation["close"] * cumulative_split
        except OverflowError as exc:
            raise DatasetError("Split-neutral price calculation overflowed.") from exc
        if (
            not math.isfinite(cumulative_split)
            or cumulative_split <= 0
            or not math.isfinite(price)
            or price <= 0
        ):
            raise DatasetError("Split-neutral price is outside the finite positive range.")
        prices.append(price)
    return prices
