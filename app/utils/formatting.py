"""Utility functions for progress bar rendering and message formatting."""

def make_progress_bar(current: float, target: float, length: int = 10, fill_char: str = "█", empty_char: str = "░") -> str:
    """Generate a clean visual progress bar string."""
    if target <= 0:
        return empty_char * length
    ratio = min(max(current / target, 0.0), 1.0)
    filled_len = int(round(ratio * length))
    return (fill_char * filled_len) + (empty_char * (length - filled_len))


def format_number(val: float, decimals: int = 1) -> str:
    """Format float cleanly (e.g. 74.0 -> '74', 74.5 -> '74.5')."""
    if val == int(val):
        return str(int(val))
    return f"{val:.{decimals}f}"


def get_traffic_light(val: float, target_min: float, target_max: float) -> str:
    """Return colored circle based on target thresholds."""
    if val >= target_min and val <= target_max:
        return "🟢"
    elif val > 0:
        return "🟡"
    return "⚪"
