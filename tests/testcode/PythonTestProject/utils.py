def format_currency(amount: float) -> str:
    return f"${amount:.2f}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def summarize(items):
    return format_currency(sum(items))
