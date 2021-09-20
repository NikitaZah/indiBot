import pandas as pd


def stoch(source: pd.DataFrame, length: int):

    lowest = source['low'].rolling(window=length).min()
    highest = source['high'].rolling(window=length).max()

    res = 100*(source['close'] - lowest)/(highest - lowest)
    # res = []
    # for i in range(length, len(close)):
    #     lowest = min(low[i-length:i+1])
    #     highest = max(high[i-length:i+1])
    #     x = 100 * (close[i] - lowest) / (highest - lowest)
    #     res.append(x)
    return res
