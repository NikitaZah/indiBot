from indicators.lines import ewm


def slingshot(data: list):
    ema_slow = ewm(data, 62)
    ema_fast = ewm(data, 38)

    trend = []
    len_diff = len(ema_fast)-len(ema_slow)

    for i in range(len(ema_slow)):
        if ema_fast[i+len_diff] >= ema_slow[i]:
            trend.append(1)     # UpTrend
        else:
            trend.append(-1)    # DownTrend
    return trend
