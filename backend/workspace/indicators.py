from collections import deque


def moving_average(bars, window):
    values = deque()
    total = 0.0
    points = []
    for bar in bars:
        values.append(bar["close"])
        total += bar["close"]
        if len(values) > window:
            total -= values.popleft()
        if len(values) == window:
            points.append({"time": bar["time"], "value": round(total / window, 6)})
    return points


def relative_strength_index(bars, window=14):
    if len(bars) <= window:
        return []
    changes = [current["close"] - previous["close"] for previous, current in zip(bars, bars[1:])]
    gain = sum(max(change, 0) for change in changes[:window]) / window
    loss = sum(max(-change, 0) for change in changes[:window]) / window
    points = []
    for index in range(window, len(bars)):
        if index > window:
            change = changes[index - 1]
            gain = (gain * (window - 1) + max(change, 0)) / window
            loss = (loss * (window - 1) + max(-change, 0)) / window
        value = 50.0 if gain == loss == 0 else 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
        points.append({"time": bars[index]["time"], "value": round(value, 6)})
    return points


def calculate_indicators(bars):
    return {
        "sma20": moving_average(bars, 20),
        "sma50": moving_average(bars, 50),
        "rsi14": relative_strength_index(bars),
    }
