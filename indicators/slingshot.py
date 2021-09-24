from indicators.lines import ewm
import pandas as pd


def slingshot(data: pd.DataFrame):
    ema_slow = ewm(data, 62)
    ema_fast = ewm(data, 38)
    # print(f'ema fast:\n{ema_fast}\nema slow:\n{ema_slow}')
    trend = (ema_fast-ema_slow).dropna()
    print(f'trend:\n{trend}')
    return trend
