from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import pandas as pd
import numpy as np
from tqdm import tqdm


def appropriate(pair: str, pair_data: pd.DataFrame, tf: str, volume=80000000, volatile=8):
    if tf == '5m':
        ness = 288
    elif tf == '15m':
        ness = 96
    elif tf == '1h':
        ness = 24
    elif tf == '4h':
        ness = 6
    else:
        print(f'unavailable timeframe: {tf}')
        return None
    length = pair_data.index.size
    if volatility(pair_data, length, ness) > volatile and cash_volume(pair_data['cash_volume'], length, ness) > volume:
        return True
    return False


def volatility(pair_data: pd.DataFrame, length: int, qty: int):
    start = length - qty - 2
    end = length - 2

    highest = pair_data.loc[start:end, 'high'].max(axis=0)
    lowest = pair_data.loc[start:end, 'low'].min(axis=0)
    return (highest - lowest) / pair_data.loc[length-2, 'close']


def cash_volume(volumes: pd.DataFrame, length: int, qty: int):
    start = length - qty - 2
    end = length - 2
    volume = volumes.iloc[start:end].sum(axis=0)
    return volume


def candles(client: Client, symbol: str, interval: str, end_time=None, limit=1000) -> pd.DataFrame:
    klines = []
    while limit > 1000:
        try:
            if not end_time:
                last_klines = client.futures_klines(symbol=symbol, interval=interval, limit=1000)
            else:
                last_klines = client.futures_klines(symbol=symbol, interval=interval, endTime=end_time, limit=1000)

            if len(last_klines) < 1000:
                limit = len(last_klines)
                break

            end_time = int(last_klines[0][0]) - 1
            limit -= 1000
            last_klines.extend(klines)
            klines = last_klines.copy()
        except BinanceAPIException as error:
            print(f'API exception:{error}\nsymbol = {symbol}\nlimit = {limit}')
            return None
        except BinanceRequestException as error:
            print(f'request exception:{error}\nsymbol = {symbol}\nlimit = {limit}')
            return None
        except Exception as unknown_error:
            print(f'unknown error: {unknown_error}')
            return None
    limit = max(limit, 10)
    try:
        if not end_time:
            last_klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        else:
            last_klines = client.futures_klines(symbol=symbol, interval=interval, endTime=end_time, limit=limit)
        last_klines.extend(klines)
        klines = last_klines.copy()
    except BinanceAPIException as error:
        print(f'API exception:{error}\nsymbol = {symbol}\nlimit = {limit}')
        return None
    except BinanceRequestException as error:
        print(f'request exception:{error}\nsymbol = {symbol}\nlimit = {limit}')
        return None
    except Exception as unknown_error:
        print(f'unknown error: {unknown_error}')
        return None

    open_time, close_time, high_price, low_price, open_price, close_price, volume, cash_volume, trades_number =\
        [], [], [], [], [], [], [], [], []
    for candle in klines:
        open_time.append(int(candle[0]))
        close_time.append(int(candle[6]))
        high_price.append(float(candle[2]))
        low_price.append(float(candle[3]))
        open_price.append(float(candle[1]))
        close_price.append(float(candle[4]))
        volume.append(float(candle[5]))
        cash_volume.append(float(candle[7]))
        trades_number.append(int(candle[8]))

    data = {'open_time': open_time, 'close_time': close_time, 'high': high_price, 'low': low_price,
            'open': open_price, 'close': close_price, 'volume': volume, 'cash_volume': cash_volume,
            'trades': trades_number}
    return pd.DataFrame.from_dict(data)


def price(close: pd.DataFrame):
    length = close.size
    return close.iloc[length-1]


def refresh_time(close_time: pd.DataFrame):
    length = close_time.size
    return close_time.iloc[length-1]
