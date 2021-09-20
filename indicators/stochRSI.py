from indicators.lines import sma, rsi
from indicators.stoch import stoch
import pandas as pd


def stoch_rsi(source: pd.DataFrame, length: int):
    smooth_k, smooth_d = 3, 3
    rsi1 = rsi(source['close'], length)
    k = sma(stoch(pd.DataFrame({'close': rsi1, 'high': rsi1, 'low': rsi1}), length), smooth_k)
    d = sma(k, smooth_d)
    return k, d
