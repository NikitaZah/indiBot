from indicators.slingshot import slingshot
from indicators.stochRSI import stoch_rsi
import get
from indicators.lines import ewm
from data import client_v as client
from data import pairs_data, all_pairs
from tqdm import tqdm
import pandas as pd
import time
import os
from datetime import datetime
from binance.enums import *
from binance.helpers import round_step_size
from binance.client import Client

deposit = 997
dollars = 250
leverage = 5

trading_pairs = list()
order_pairs = list()

STOP_LOSS = 0.04
TAKE_PROFIT = 0.12


def test_slingshot_strategy():
    global trading_pairs
    stat = []
    filename = './statistics/stat1.pkl'

    testing = 9760
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

    test_pairs = ['ETHUSDT', 'TLMUSDT', 'BTCUSDT']
    # all_pairs = test_pairs

    for symbol in tqdm(all_pairs, desc='getting pairs data'):
        candles1 = get.candles(client, symbol, '1h', limit=testing)
        candles4 = get.candles(client, symbol, '4h', limit=(testing//4 + 1))
        pairs[symbol] = [candles1, candles4]
        if candles1['open_time'].size < testing:
            print(f'pair {symbol} only has {candles1["open_time"].size} candles')

    time_start = time.time()
    for symbol in all_pairs:
        if symbol == 'BTCUSDT':
            continue
        trading_pairs.clear()
        candles1 = pairs[symbol][0]
        candles4 = pairs[symbol][1]
        candles1_btc = pairs['BTCUSDT'][0]
        candles4_btc = pairs['BTCUSDT'][1]

        length = candles1['open_time'].size
        start = 0
        for end in range(1000, length):
            klines1 = candles1.iloc[start:end].reset_index(drop=True)
            open_time = klines1.loc[0, 'open_time']
            close_time = klines1.loc[end-start-1, 'close_time']
            klines4 = candles4.loc[candles4['open_time'] < close_time]
            start += 1

            if not get.appropriate(symbol, klines1, '1h', volatile=0):
                continue

            pair = apply_status(symbol, klines1, klines4)
            if not pair:
                continue

            klines1_btc = candles1_btc.loc[(candles1_btc['open_time'] >= open_time) & (candles1_btc['close_time'] <= close_time)].reset_index(drop=True)
            klines4_btc = candles4_btc.loc[(candles4_btc['open_time'] < close_time)]

            main_trend = get_main_trend('BTCUSDT', klines1_btc, klines4_btc)

            if not correlation(pair, main_trend):
                continue

            tp, sl = signal(pair)
            if not tp:
                continue

            length = klines1['close'].size
            price = get.price(klines1['close'].iloc[:length-1])
            placed = test_place_order(pair['symbol'], price, tp, sl, main_trend, klines1.loc[end-start-2, 'open_time'])

            for pair in tqdm(trading_pairs, desc='checking open positions'):
                if pair['tp']:
                    test_res = test_check_tp(pair['symbol'], pair['price'], pair['tp'], pair['ok'], klines1)
                    if test_res:
                        pair['tp'] = None
                        pair['res'] = test_res

                test_res = test_check_sl(pair['symbol'], pair['price'],  pair['sl'], pair['ok'], klines1)
                if test_res:
                    if not pair['tp']:
                        test_res /= 2
                    close_date = datetime.fromtimestamp((klines1.loc[end-start-2, 'close_time'])/1000)
                    stat.append([pair['symbol'], pair['time'], close_date, pair['ok'], pair['res'], test_res, pair['res']+test_res])
                    print(stat[-1])
                    if test_res + pair['res'] > 0:
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
                    total_res += test_res + pair['res']
                    trading_pairs.remove(pair)
                else:
                    pair['sl'] = update_sl(klines1, main_trend)

    print(f'testing finished.\nTotal deals: {total_win+total_lose}\nTotal win: {total_win}\nTotal lose: {total_lose}\n'
          f'Total result: {total_res}\nMax upstream: {max_up}\nMax downstream: {max_down}')
    statistics = pd.DataFrame(stat, columns=['symbol', 'open date', 'close date', 'deal_type', 'tp result', 'sl result', 'result'])
    print(f'\n{statistics}')
    try:
        statistics.to_pickle(filename)
    except FileNotFoundError:
        print(f'Cannot find directory {filename} to save the database. Trying to create...')
        folder = '/statistics'
        curr_path = os.getcwd()
        full_dir_name = curr_path + folder
        try:
            os.mkdir(full_dir_name)
            statistics.to_pickle(filename)
            print('Directory created successfully')
        except OSError as err:
            print(f'Creation of the directory failed because of {err}\n')

    print(f'full statistics will be available at {filename}')


def slingshot_strategy():
    global trading_pairs
    while True:
        start = time.time()
        volatile_pairs = []
        pairs1 = dict()
        pairs4 = dict()

        # получаем свечи 1ч и 4ч для всех пар, складываем в соответствующие словари для удобства
        for pair in tqdm(all_pairs, desc='selecting pairs'):
            candles1 = get.candles(client, pair, '1h', limit=1000)
            candles4 = get.candles(client, pair, '1h', limit=1000)
            pairs1[pair] = candles1
            pairs4[pair] = candles4
            if get.appropriate(pair, candles4, '4h', volatile=0):
                volatile_pairs.append([pair, candles1, candles4])

        main_trend = get_main_trend('BTCUSDT', pairs1['BTCUSDT'], pairs4['BTCUSDT'])    # опираемся на тренд деда
        print(f'\ncurrent trend: {main_trend}\n')

        # возвращает словарь со свечами и трендами (1ч и 4ч), рассчитанными с использованием слингшота
        trend_pairs = []
        for pair in volatile_pairs:
            res = apply_status(pair[0], pair[1], pair[2])
            if res:
                trend_pairs.append(res)

        #  отбираем пары, которые кореллируют с битком и 4ч тф
        for pair in tqdm(trend_pairs, desc='checking pairs for correlation'):
            if not correlation(pair, main_trend):
                trend_pairs.remove(pair)

        for pair in tqdm(trend_pairs, desc='checking pairs for signal'):
            tp, sl = signal(pair)
            if tp:
                placed = place_order(pair['symbol'], get.price(pair['candles1']['close']), tp, sl, main_trend)

        update_time = get.refresh_time(volatile_pairs[0][1]['close_time'])
        while int(client.get_server_time()["serverTime"]) < update_time:
            for pair in trading_pairs:
                check_orders(pair)
            if (update_time - int(client.get_server_time()["serverTime"]))/1000 > 300:
                time.sleep(300)
            else:
                time.sleep((update_time - int(client.get_server_time()["serverTime"]))/1000 - 1)
        print(f'time: {round(time.time()-start, 1)}sec')


def get_main_trend(pair: str, pair_data1: pd.DataFrame, pair_data4: pd.DataFrame):
    res = apply_status(pair, pair_data1, pair_data4)
    length = res['trend4'].size
    if res['trend4'].iloc[length-1] < 0:
        return -1
    else:
        return 1


def apply_status(pair: str, pair_data1: pd.DataFrame, pair_data4: pd.DataFrame):
    res = dict()
    pair_trend1 = slingshot(pair_data1['close'])
    pair_trend4 = slingshot(pair_data4['close'])
    res['symbol'] = pair
    res['candles1'] = pair_data1
    res['candles4'] = pair_data4
    res['trend1'] = pair_trend1
    res['trend4'] = pair_trend4
    return res


def correlation(pair: dict, trend: int):
    try:
        length = pair['trend1'].size
        length2 = pair['trend4'].size
        if pair['trend1'].iloc[length-1] * pair['trend4'].iloc[length2-1] > 0:
            if pair['trend1'].iloc[length-1] * trend > 0:
                return True
        return False
    except Exception as err:
        print(f'exception in correlation: {err}')
        print(f'{pair["symbol"]}\n{pair["candles1"]}\n{pair["candles4"]}\n{pair["trend1"]}\n{pair["trend4"]}')
        return False


def signal(pair: dict):
    tp, sl = None, None
    ema_fast = ewm(pair['candles1']['close'], 38)
    ema_slow = ewm(pair['candles1']['close'], 62)
    k_line, d_line = stoch_rsi(pair['candles1'], 14)
    if pair['trend1'][pair['trend1'].size-1] > 0:
        if k_line[k_line.size-1] < 20 and d_line[d_line.size-1] < 20:
            length = pair['candles1']['low'].size
            if pair['candles1']['close'][length-2] > ema_fast[ema_fast.size-2] > pair['candles1']['low'][length-2]:
                sl = ema_slow.iloc[ema_slow.size-1] - STOP_LOSS * ema_slow.iloc[ema_slow.size-1]
                tp = pair['candles1'].loc[length-2, 'close'] + TAKE_PROFIT * pair['candles1'].loc[length-2, 'close']
    else:
        if k_line[k_line.size-1] > 20 and d_line[d_line.size-1] > 20:
            length = pair['candles1']['high'].size
            if pair['candles1']['close'][length-2] < ema_fast[ema_fast.size-2] < pair['candles1']['high'][length-2]:
                sl = ema_slow.iloc[ema_slow.size-1] + STOP_LOSS * ema_slow.iloc[ema_slow.size-1]
                tp = pair['candles1'].loc[length-2, 'close'] - TAKE_PROFIT * pair['candles1'].loc[length-2, 'close']
    return tp, sl


def place_order(symbol: str, price: float, tp: float, sl: float, order_kind: int):
    global trading_pairs
    qty = round_step_size(dollars * leverage / price, float(pairs_data[symbol]['MARKET_LOT_SIZE']))
    tp = round_step_size(tp, float(pairs_data[symbol]['PRICE_FILTER']))
    sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))
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
            tp_order = client.futures_create_order(symbol=symbol, side=close_side, stopPrice=tp, quantity=(qty//2),
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
    if sl_order['status'] == 'FILLED':
        if tp_order['status'] == 'FILLED':
            print(f'{pair["symbol"]}: trade closed successfully. +$$$')
        elif tp_order['status'] == 'NEW':
            close = client.futures_cancel_order(symbol=pair['symbol'], orderId=pair['tpId'])
            print(f'{pair["symbol"]}: trade closed by stop loss. Take profit order was closed: {close}')

    elif sl_order['status'] == 'CANCELED':
        close = True
        print(f'{pair["symbol"]}: stop loss order was closed directly')
    if close:
        trading_pairs.remove(pair)
        print(f'{pair["symbol"]} trade eliminated')


def test_place_order(symbol: str, price: float, tp: float, sl: float, order_kind: int, timestamp: str):
    global trading_pairs
    price = round_step_size(price, float(pairs_data[symbol]['PRICE_FILTER']))
    tp = round_step_size(tp, float(pairs_data[symbol]['PRICE_FILTER']))
    sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))
    trade_time = datetime.fromtimestamp(int(timestamp)/1000)
    trading_pairs.append(dict(symbol=symbol, price=price, tp=tp, sl=sl, ok=order_kind, time=trade_time, res=0))
    return True


def test_check_sl(symbol: str, price: float, sl: float, order_kind: int, candles: pd.DataFrame) -> float:
    length = candles['open_time'].size
    result = None
    if order_kind == 1:
        if (candles['low'] < sl)[length-1]:
            result = -(price - sl) / price * 100

    else:
        if (candles['high'] > sl)[length-1]:
            result = -(sl - price) / price * 100
    return result


def test_check_tp(symbol: str, price: float, tp: float, order_kind: int, candles: pd.DataFrame) -> float:
    length = candles['open_time'].size
    result = None
    if order_kind == 1:
        if (candles['high'] > tp)[length-1]:
            result = (tp - price) / price * 100 * 1/2

    else:
        if (candles['low'] < tp)[length-1]:
            result = (price - tp) / price * 100 * 1/2
    return result


def update_sl(candles: pd.DataFrame, order_kind: int):
    ema_slow = ewm(candles['close'], 62)
    sl = ema_slow.iloc[ema_slow.size-1] - ema_slow.iloc[ema_slow.size-1] * STOP_LOSS if order_kind == 1 \
        else ema_slow.iloc[ema_slow.size-1] + ema_slow.iloc[ema_slow.size-1] * STOP_LOSS
    return sl
