from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Instrument:
    id: str
    symbol: str
    name: str
    exchange: str
    currency: str = "USD"
    timezone: str = "America/New_York"

    def to_dict(self):
        return asdict(self)


INSTRUMENTS = tuple(
    Instrument(f"{exchange.lower()}-{symbol.lower()}", symbol, name, exchange)
    for symbol, name, exchange in (
        ("AAPL", "Apple Inc.", "XNAS"),
        ("MSFT", "Microsoft Corporation", "XNAS"),
        ("NVDA", "NVIDIA Corporation", "XNAS"),
        ("AMZN", "Amazon.com Inc.", "XNAS"),
        ("GOOGL", "Alphabet Inc.", "XNAS"),
        ("META", "Meta Platforms Inc.", "XNAS"),
        ("TSLA", "Tesla Inc.", "XNAS"),
        ("AVGO", "Broadcom Inc.", "XNAS"),
        ("JPM", "JPMorgan Chase & Co.", "XNYS"),
        ("V", "Visa Inc.", "XNYS"),
        ("MA", "Mastercard Incorporated", "XNYS"),
        ("WMT", "Walmart Inc.", "XNAS"),
        ("XOM", "Exxon Mobil Corporation", "XNYS"),
        ("JNJ", "Johnson & Johnson", "XNYS"),
        ("PG", "Procter & Gamble Company", "XNYS"),
        ("HD", "Home Depot Inc.", "XNYS"),
        ("KO", "Coca-Cola Company", "XNYS"),
        ("DIS", "Walt Disney Company", "XNYS"),
        ("NFLX", "Netflix Inc.", "XNAS"),
        ("COST", "Costco Wholesale Corporation", "XNAS"),
    )
)
BY_ID = {instrument.id: instrument for instrument in INSTRUMENTS}


def find_instruments(query):
    normalized = query.strip().casefold()
    return [
        instrument.to_dict()
        for instrument in INSTRUMENTS
        if not normalized
        or normalized in f"{instrument.symbol} {instrument.name} {instrument.exchange}".casefold()
    ]
