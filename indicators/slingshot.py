from indicators.lines import ewm
import pandas as pd


def slingshot(data: pd.DataFrame):
    ema_slow = ewm(data, 62)
    ema_fast = ewm(data, 38)
    trend = (ema_fast-ema_slow).dropna()
    return trend
