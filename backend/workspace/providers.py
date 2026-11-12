"""Source policies are checked on every request, before any cached data is read."""

from dataclasses import dataclass

from django.conf import settings


class MarketDataUnavailable(Exception):
    pass


@dataclass(frozen=True)
class ProviderPolicy:
    source_id: str
    label: str
    data_mode: str
    price_basis: str
    usage: str
    ttl_seconds: int
    disclaimer: str

    def authorize(self):
        if self.usage == "demonstration":
            return
        if self.usage != "local_personal_research_only":
            raise MarketDataUnavailable("No approved usage policy is configured for this source.")
        if not settings.CADRISYN_MARKET_DATA_ENABLED:
            raise MarketDataUnavailable("Market data is not enabled. Choose the explicitly labelled demo dataset.")
        if not settings.DEBUG or not settings.CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED:
            raise MarketDataUnavailable(
                "This historical adapter requires local personal-research acknowledgement. "
                "No production or redistribution license is configured."
            )


DEMO = ProviderPolicy(
    source_id="cadrisyn-synthetic-v1",
    label="Synthetic demonstration dataset",
    data_mode="demo",
    price_basis="synthetic",
    usage="demonstration",
    ttl_seconds=3600,
    disclaimer="Synthetic prices for interface demonstration. These are not observed market prices or investment results.",
)
YAHOO_DAILY = ProviderPolicy(
    source_id="yahoo-personal-research",
    label="Yahoo Finance via yfinance",
    data_mode="delayed",
    price_basis="split_and_dividend_adjusted",
    usage="local_personal_research_only",
    ttl_seconds=300,
    disclaimer=(
        "Daily historical observations for explicitly acknowledged local personal research. "
        "Delay is not guaranteed. Not a real-time feed or redistribution entitlement."
    ),
)
PROVIDERS = {"demo": DEMO, "market": YAHOO_DAILY}


def market_data_available():
    try:
        YAHOO_DAILY.authorize()
    except MarketDataUnavailable:
        return False
    return True
