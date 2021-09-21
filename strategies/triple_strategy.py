from indicators import lines, stochRSI, supertrend
from tqdm import tqdm
import get
from data import client_n as client, all_pairs, pairs_data
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from termcolor import colored as cl
from binance.enums import *
from binance.helpers import round_step_size
from binance.client import Client
from datetime import datetime
import time

deposit = 150
dollars = 30
leverage = 5
trading_pairs = []


def test_triple_strategy():
    global trading_pairs
    stat = []
    filename = './statistics/stat.pkl'

    testing = 3000
    pairs = dict()

    downstream = 0
    max_down = 0
    downstream_flag = False
    upstream = 0
    max_up = 0
    upstream_flag = False

    total_win = 0
    total_lose = 0
    total_res = 0

    for symbol in tqdm(all_pairs, desc='getting pairs data'):
        candles = get.candles(client, symbol, '15m', limit=testing)
        pairs[symbol] = candles
        if candles['open_time'].size < testing:
            print(f'pair {symbol} only has {candles["open_time"].size} candles')
    start = 0
    time_start = time.time()
    for end in range(350, testing+1):
        if start % 10 == 0:
            print(f'start = {start}\ntime spent: {round(time.time() - time_start, 2)}sec')
        if start % 8 == 0:
            volatile_pairs = []
            for pair in tqdm(all_pairs, desc='selecting pairs'):
                candles = pairs[pair].iloc[start:end].reset_index(drop=True)
                if get.appropriate(pair, candles, '15m', volatile=0):
                    volatile_pairs.append(pair)

        trend_pairs = []

        for pair in tqdm(volatile_pairs, desc='applying status to pairs'):
            candles = pairs[pair].iloc[start:end].reset_index(drop=True)
            res = apply_status(pair, candles)
            if res:
                trend_pairs.append(res)
        for pair in tqdm(trend_pairs, desc='checking trend pairs'):
            tp, sl = signal(pair)
            if not tp:
                continue
            price = get.price(pair['candles']['close'])
            placed = test_place_order(pair['symbol'], price, tp, sl, pair['trend'],
                                      pairs[pair['symbol']].loc[end-1, 'open_time'])

        for pair in tqdm(trading_pairs, desc='checking trading pairs'):
            candles = pairs[pair['symbol']].iloc[start:end].reset_index(drop=True)
            test_res = test_check_orders(pair['symbol'], pair['price'], pair['tp'], pair['sl'], pair['ok'],
                                         candles)
            if test_res:
                stat.append([pair['symbol'], pair['time'], pair['ok'], test_res])
                print(stat[-1])
                if test_res > 0:
                    upstream_flag = True
                    upstream += 1
                    total_win += 1
                    if downstream_flag:
                        downstream_flag = False
                        if downstream > max_down:
                            max_down = downstream
                        downstream = 0
                else:
                    downstream_flag = True
                    downstream += 1
                    total_lose += 1
                    if upstream_flag:
                        upstream_flag = False
                        if upstream > max_up:
                            max_up = upstream
                        upstream = 0
                total_res += test_res
                trading_pairs.remove(pair)
        start += 1

    if trading_pairs:
        print(f'\n{len(trading_pairs)} were open\n')

    print(f'testing finished.\nTotal deals: {total_win+total_lose}\nTotal win: {total_win}\nTotal lose: {total_lose}\n'
          f'Total result: {total_res}\nMax upstream: {max_up}\nMax downstream: {max_down}')
    statistics = pd.DataFrame(stat, columns=['symbol', 'hour', 'deal_type', 'result'])
    print(f'ful statisticks will be available at ...\n{statistics}')
    statistics.to_pickle(filename)


def triple_strategy():
    global trading_pairs
    while True:
        start = time.time()
        volatile_pairs = []
        for pair in tqdm(all_pairs, desc='selecting pairs'):
            candles = get.candles(client, pair, '5m', limit=1000)
            if get.appropriate(pair, candles, '5m', volatile=0):
                volatile_pairs.append([pair, candles])

        trend_pairs = []
        for pair in tqdm(volatile_pairs, desc='applying status to pairs'):
            res = apply_status(pair[0], pair[1])
            if res:
                trend_pairs.append(res)

        print(f'\ntrend pairs: {len(trend_pairs)}')
        for pair in trend_pairs:
            print(pair['symbol'])
            tp, sl = signal(pair)
            if not tp:
                continue
            placed = place_order(pair['symbol'], get.price(pair['candles']['close']), tp, sl, pair['trend'])


        update_time = get.refresh_time(volatile_pairs[0][1]['close_time'])
        while int(client.get_server_time()["serverTime"]) < update_time:
            for pair in trading_pairs:
                check_orders(pair)
        print(f'time: {round(time.time()-start, 1)}')


def apply_status(pair: str, pair_data: pd.DataFrame):
    ema200 = lines.ewm(pair_data['close'], 200)
    k_line, d_line = stochRSI.stoch_rsi(pair_data, 14)

    length = pair_data['open_time'].size
    if pair_data.iloc[length-1, 5] > ema200[ema200.size-1] and d_line[d_line.size-1] < k_line[k_line.size-1] < 30:
        pair_trend = 1
    elif pair_data.iloc[length-1, 5] < ema200[ema200.size-1] and d_line[d_line.size-1] > k_line[k_line.size-1] > 70:
        pair_trend = -1
    else:
        return None
    res = dict()
    res['symbol'] = pair
    res['trend'] = pair_trend
    res['candles'] = pair_data
    return res


def signal(pair: dict):
    tp, sl = None, None
    trend1 = supertrend.super_trend(pair['candles'], 12, 3)
    trend2 = supertrend.super_trend(pair['candles'], 11, 2)
    trend3 = supertrend.super_trend(pair['candles'], 10, 1)

    length = trend1.size
    points = [trend1.iloc[length-2], trend2.iloc[length-2], trend3.iloc[length-2]]
    points.sort()

    last_close = pair['candles'].loc[length-2, 'close']
    current_price = pair['candles'].loc[length-1, 'open']
    if pair['trend'] == 1:
        if last_close > points[1]:
            if last_close > points[2]:
                sl = points[1]
            else:
                sl = points[0]
            tp = current_price + 1.5 * (last_close - sl)
    else:
        if last_close < points[1]:
            if last_close < points[0]:
                sl = points[1]
            else:
                sl = points[2]
            tp = current_price - 1.5 * (sl - last_close)

    return tp, sl


def place_order(symbol: str, price: float, tp: float, sl: float, order_kind: int):
    global trading_pairs
    qty = round_step_size(dollars * leverage / price, float(pairs_data[symbol]['MARKET_LOT_SIZE']))
    side = Client.SIDE_BUY if order_kind == 1 else Client.SIDE_SELL
    close_side = Client.SIDE_SELL if order_kind == 1 else Client.SIDE_BUY

    order = None
    for i in range(30):
        try:
            order = client.futures_create_order(symbol=symbol, side=side,
                                                type=Client.ORDER_TYPE_MARKET, quantity=qty)
            break
        except Exception as err:
            print(f'cannot place market order. try number: {i+1} Error: {err}\n')
            time.sleep(1)
    if not order:
        return False
    while True:
        try:
            sl_order = client.futures_create_order(symbol=symbol, side=close_side, stopPrice=sl,
                                                   closePosition=True,
                                                   type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
            break
        except Exception as err:
            print(f'{symbol}: ATTENTION! Cannot place stop loss!')
    while True:
        try:
            tp_order = client.futures_create_order(symbol=symbol, side=close_side, stopPrice=tp,
                                                   closePosition=True,
                                                   type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET)
            break
        except Exception as err:
            print(f'{symbol}: ATTENTION! Cannot place take profit!')
    trading_pairs.append(dict(symbol=symbol, orderId=order['orderId'], tpId=tp_order['orderId'],
                              slId=sl_order['orderId']))
    return True


def check_orders(pair: dict):
    tp_order = client.futures_get_order(symbol=pair['symbol'], orderId=pair['tpId'])
    sl_order = client.futures_get_order(symbol=pair['symbol'], orderId=pair['slId'])

    close = False
    if tp_order['status'] == 'FILLED':
        close = client.futures_cancel_order(symbol=pair['symbol'], orderId=pair['slId'])
        print(f'{pair["symbol"]}: take profit')
    elif sl_order['status'] == 'FILLED':
        close = client.futures_cancel_order(symbol=pair['symbol'], orderId=pair['tpId'])
        print(f'{pair["symbol"]}: take profit')
    elif tp_order['status'] == 'CANCELED' or sl_order['status'] == 'CANCELED':
        close = True
        print(f'{pair["symbol"]}: the order was closed directly. Eliminated')
    if close:
        trading_pairs.remove(pair)


def test_place_order(symbol: str, price: float, tp: float, sl: float, order_kind: int, timestamp: str):
    global trading_pairs
    price = round_step_size(price, float(pairs_data[symbol]['PRICE_FILTER']))
    tp = round_step_size(tp, float(pairs_data[symbol]['PRICE_FILTER']))
    sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))
    hour = datetime.fromtimestamp(int(timestamp)/1000).hour
    trading_pairs.append(dict(symbol=symbol, price=price, tp=tp, sl=sl, ok=order_kind, time=hour))
    return True


def test_check_orders(symbol: str, price: float, tp: float, sl: float, order_kind: int, candles: pd.DataFrame):
    length = candles['open_time'].size
    result = None
    if order_kind == 1:
        if candles.loc[length-1, 'low'] < sl:
            result = -(price - sl) / price * 100
        elif candles.loc[length-1, 'high'] > tp:
            result = (tp - price) / price * 100
    else:
        if candles.loc[length-1, 'high'] > sl:
            result = -(sl - price) / price * 100
        elif candles.loc[length-1, 'low'] < tp:
            result = (price - tp) / price * 100
    return result
