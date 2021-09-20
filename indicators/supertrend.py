import pandas as pd
import numpy as np
from indicators.lines import hl2, atr2


def super_trend(source: pd.DataFrame, periods: int, multiplier: int):
    hl = hl2(source)
    atr = atr2(source, periods)

    upper_band = (hl + multiplier * atr).dropna()
    lower_band = (hl - multiplier * atr).dropna()

    final_bands = pd.DataFrame(columns=['upper', 'lower'])
    final_bands.iloc[:, 0] = [x for x in upper_band - upper_band]
    final_bands.iloc[:, 1] = final_bands.iloc[:, 0]

    for i in range(len(final_bands)):   # final upper band
        if i == 0:
            final_bands.iloc[i, 0] = 0
        else:
            if (upper_band[i] < final_bands.iloc[i - 1, 0]) | (source['close'][i - 1] > final_bands.iloc[i - 1, 0]):
                final_bands.iloc[i, 0] = upper_band[i]
            else:
                final_bands.iloc[i, 0] = final_bands.iloc[i - 1, 0]

    for i in range(len(final_bands)):   # final lower band
        if i == 0:
            final_bands.iloc[i, 1] = 0
        else:
            if (lower_band[i] > final_bands.iloc[i - 1, 1]) | (source['close'][i - 1] < final_bands.iloc[i - 1, 1]):
                final_bands.iloc[i, 1] = lower_band[i]
            else:
                final_bands.iloc[i, 1] = final_bands.iloc[i - 1, 1]

    supertrend = pd.DataFrame(columns=[f'supertrend_{periods}'])
    supertrend.iloc[:, 0] = [x for x in final_bands['upper'] - final_bands['upper']]

    for i in range(len(supertrend)):
        if i == 0:
            supertrend.iloc[i, 0] = 0
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 0] and source['close'][i] < final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 0] and source['close'][i] > final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 1] and source['close'][i] > final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 1] and source['close'][i] < final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]

    supertrend = supertrend.set_index(upper_band.index)
    supertrend = supertrend.dropna()[0:]

    upt = []
    dt = []
    close = source['close'].iloc[len(source['close']) - len(supertrend):]

    for i in range(len(supertrend)):
        if close[i] > supertrend.iloc[i, 0]:
            upt.append(supertrend.iloc[i, 0])
            dt.append(np.nan)
        elif close[i] < supertrend.iloc[i, 0]:
            upt.append(np.nan)
            dt.append(supertrend.iloc[i, 0])
        else:
            upt.append(np.nan)
            dt.append(np.nan)

    st, upt, dt = pd.Series(supertrend.iloc[:, 0]), pd.Series(upt), pd.Series(dt)
    upt.index, dt.index = supertrend.index, supertrend.index

    return st
