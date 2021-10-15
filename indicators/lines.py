import pandas as pd


def ewm(source: pd.DataFrame, length: int) -> pd.DataFrame:
    res = source.ewm(span=length, adjust=False).mean()
    return res


def rma(source: pd.DataFrame, length: int) -> pd.DataFrame:
    res = source.ewm(com=length-1, adjust=False).mean()
    return res


def rsi(source: pd.DataFrame, length: int) -> pd.DataFrame:
    delta = source.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    rma_up = rma(up, length)
    rma_down = rma(down, length)
    rs = rma_up/rma_down
    return rs


def sma(source: pd.DataFrame, length: int) -> pd.DataFrame:
    res = source.rolling(length).mean()
    return res


def atr2(source: pd.DataFrame, length: int) -> pd.DataFrame:
    tr1 = pd.DataFrame(source['high']-source['low'])
    tr2 = pd.DataFrame(abs(source['high']-source['close'].shift(1)))
    tr3 = pd.DataFrame(abs(source['low'] - source['close'].shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = rma(tr, length)
    return atr


def hl2(source: pd.DataFrame) -> pd.DataFrame:
    hl_avg = (source['high']+source['low'])/2
    return hl_avg


def hlc3(source: pd.DataFrame) -> pd.DataFrame:
    hlc = (source['high']+source['low']+source['close'])/3
    return hlc
