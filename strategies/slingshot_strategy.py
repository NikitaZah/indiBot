import queue

from indicators.slingshot import slingshot
from indicators.stochRSI import stoch_rsi
import get
from indicators.lines import ewm, atr2
from data import client_n as client
from data import pairs_data, all_pairs
from data import Pair
from tqdm import tqdm
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from binance.enums import *
from binance.helpers import round_step_size
from binance.client import Client
from multiprocessing import Process, Queue

deposit = 700
dollars = 10    # percent of deposit
leverage = 20

statistics = pd.DataFrame(columns=['symbol', 'open date', 'close date', 'deal_type', 'addons', 'fixes',
                                             'stop loss', 'result'])


def test_slingshot_strategy():
    global trading_pairs
    stat = []
    filename = './statistics/stat1.pkl'

    testing = 10000
    pairs = dict()

    total_win = 0
    total_lose = 0
    total_res = 0


    test_pairs = ['ETHUSDT', 'TLMUSDT', 'BTCUSDT']
    # all_pairs = test_pairs

    for symbol in tqdm(all_pairs, desc='getting pairs data'):
        pair_data_file1 = './pair_data/' + symbol + '1h.pkl'
        pair_data_file4 = './pair_data/' + symbol + '4h.pkl'
        candles1 = pd.read_pickle(pair_data_file1)
        candles4 = pd.read_pickle(pair_data_file4)
        # end_time1 = candles1['open_time'].iloc[0]
        # end_time4 = candles4['open_time'].iloc[0]
        # candles1 = get.candles(client, symbol, '1h', end_time1, limit=testing).append(candles1).reset_index(drop=True)
        # candles4 = get.candles(client, symbol, '4h', end_time4, limit=(testing // 4 + 1)).append(candles4).reset_index(drop=True)
        # candles1.to_pickle(pair_data_file1)
        # candles4.to_pickle(pair_data_file4)
        pairs[symbol] = [candles1, candles4]
        if candles1['open_time'].size < 20000:
            print(f'pair {symbol} only has {candles1["open_time"].size} candles')

    for symbol in tqdm(all_pairs, desc='checking symbols'):
        if symbol == 'BTCUSDT':
            continue

        in_trade = {}
        trading_pairs.clear()
        candles1 = pairs[symbol][0]
        candles4 = pairs[symbol][1]
        candles1_btc = pairs['BTCUSDT'][0]
        candles4_btc = pairs['BTCUSDT'][1]

        length = candles1['open_time'].size
        start = -1
        for end in range(1000, length):
            start += 1
            klines1 = candles1.iloc[start:end].reset_index(drop=True)
            start_time = klines1.loc[0, 'open_time']
            close_time = klines1.loc[end-start-1, 'close_time']
            klines4 = candles4.loc[candles4['open_time'] < close_time]
            klines1_btc = candles1_btc.loc[(candles1_btc['open_time'] >= start_time) & (candles1_btc['close_time'] <= close_time)].reset_index(drop=True)
            klines4_btc = candles4_btc.loc[(candles4_btc['open_time'] < close_time)]

            price = (klines1.loc[end - start - 1, 'open'])
            c_time = datetime.fromtimestamp(int(klines1.loc[end - start - 1, 'open_time']) / 1000)
            if in_trade:
                fixed = check_position(in_trade['symbol'], in_trade['origQty'], in_trade['ok'], klines1)
                check = check_stop_loss(in_trade, klines1)
                if check:
                    in_trade = fix_profit(in_trade, in_trade['origQty'], in_trade['stop_loss'], c_time)
                elif fixed > 0:
                    in_trade = fix_profit(in_trade, fixed, price, c_time)
                else:
                    if price > 1.16 * in_trade['last_fix_price'] and in_trade['ok'] == 1:
                        in_trade = fix_profit(in_trade, in_trade['origQty']/6, price, c_time)
                    if price < 0.84 * in_trade['last_fix_price'] and in_trade['ok'] == -1:
                        in_trade = fix_profit(in_trade, in_trade['origQty']/6, price, c_time)

                if in_trade['qty'] <= float(pairs_data[symbol]['MARKET_LOT_SIZE']):
                    stat.append([in_trade['symbol'], in_trade['start_date'], in_trade['last_fix'], in_trade['ok'],
                                 in_trade['addon_times'], in_trade['fixed_times'], check, in_trade['result']])
                    print(stat[-1])
                    if in_trade['result'] > 0:
                        total_win += 1
                    else:
                        total_lose += 1
                    total_res += in_trade['result']
                    in_trade = {}

            # # date filter
            # if c_time.month == 9:
            #     continue
            # if c_time.day > 20 and c_time.month != 12:
            #     continue
            # if c_time.day < 3 and c_time.month != 1:
            #     continue

            # volume filter
            if not get.appropriate(symbol, klines1, '1h', volatile=0):
                continue

            pair = apply_status(symbol, klines1, klines4)

            main_trend = get_main_trend('BTCUSDT', klines1_btc, klines4_btc)

            # btc correlation filter
            if not correlation(pair, main_trend):
                continue

            if not signal(pair):
                continue

            if in_trade:
                if in_trade['fixed_times'] == 0:
                    continue
                if in_trade['last_fix'] < in_trade['last_add']:
                    continue
                if 1.04*in_trade['last_add_price'] > price and in_trade['ok'] == 1:
                    continue
                if 0.96*in_trade['last_add_price'] < price and in_trade['ok'] == -1:
                    continue

                # res = check_addon_condition(in_trade['ok'], klines1)
                # if not res:
                #     continue

            placed = test_place_order(pair['symbol'], price, main_trend, klines1.loc[end-start-1, 'open_time'])
            if in_trade:
                in_trade['stop_loss'] = (in_trade['last_add_price'] * in_trade['qty'] + price * placed['qty']) / \
                                        (in_trade['qty'] + placed['qty'])
                in_trade['qty'] += placed['qty']
                in_trade['origQty'] = in_trade['qty']
                in_trade['addon_times'] += 1
                in_trade['last_add'] = c_time
                in_trade['last_add_price'] = price
                in_trade['result'] -= in_trade['ok']*placed['qty'] * price
            else:
                in_trade['symbol'] = symbol
                in_trade['start_date'] = placed['time']
                in_trade['qty'] = placed['qty']
                in_trade['origQty'] = placed['qty']
                in_trade['addon_times'] = 1
                in_trade['ok'] = main_trend
                in_trade['last_fix'] = pd.NA
                in_trade['last_fix_price'] = price
                in_trade['last_add'] = c_time
                in_trade['last_add_price'] = price
                in_trade['fixed_times'] = 0
                in_trade['stop_loss'] = price - in_trade['ok']*0.08*price
                in_trade['result'] = -in_trade['ok'] * placed['qty'] * price
           # print(f'res = {in_trade["result"]}\nqty={in_trade["qty"]}\norig_qty={in_trade["origQty"]}\n')

        if in_trade:
            stat.append([in_trade['symbol'], in_trade['start_date'], in_trade['last_fix'], in_trade['ok'],
                         in_trade['addon_times'], in_trade['fixed_times'], False, in_trade['result']])
            print(stat[-1])

    print(f'testing finished.\nTotal deals: {total_win+total_lose}\nTotal win: {total_win}\nTotal lose: {total_lose}\n'
          f'Total result: {total_res}\n')
    statistics = pd.DataFrame(stat, columns=['symbol', 'open date', 'close date', 'deal_type', 'addons', 'fixes',
                                             'stop loss', 'result'])
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


def slingshot_strategy(restore: bool):
    trading_allowed = True
    while True:
        pairs = []
        # get candles fro symbols and create objects
        for pair in tqdm(all_pairs, desc='getting candles'):
            candles1 = get.candles(client, pair, '1h', limit=1000)
            candles4 = get.candles(client, pair, '4h', limit=1000)
            pairs.append(Pair(pair, candles_1h=candles1, candles_4h=candles4))

            # applying main trend
            if pair == 'BTCUSDT':
                main_trend = get_main_trend(pairs[-1])

        if restore:
            pairs = restore_trading_data(pairs)
            restore = False

        if trading_allowed:
            for pair in pairs:
                if pair == 'BTCUSDT':
                    continue

                # checking pair volume and volatility
                if not get.appropriate(pair.symbol, pair.candles_1h, '1h', volatile=0):
                    continue

                pair = apply_status(pair)

                #  skipping pairs not correlated with BTC and 4h timeframe
                if not correlation(pair, main_trend):
                    continue

                # skipping pairs without signal
                if not signal(pair):
                    continue

                pair = place_order(pair, main_trend)

        save_trading_data(pairs)

        update_time = get.refresh_time(pairs[0].candles_1h['close_time'])

        # update statistics at midnight
        if datetime.fromtimestamp(update_time/1000).hour == 0:
            save_statistics()

        while int(client.get_server_time()["serverTime"]) < update_time:
            counter = 0
            for pair in pairs:
                pair.candles_1h = get.candles(client, pair.symbol, '1h', 1000)
                if pair.in_trade:
                    counter += 1
                    pair = check_stop_loss(pair)
                    if not pair.in_trade:
                        print(f'{pair.symbol} position was closed by stop loss or stop loss was canceled directly')
                        continue
                    qty = check_position(pair)
                    if qty > 0:
                        pair = fix_profit(pair, qty)
                        print(f'{pair.symbol}: fixed profit')
                        if not pair.in_trade:
                            print(f'position for {pair.symbol} was completely closed')
                if int(client.get_server_time()["serverTime"]) >= update_time:
                    break
                time.sleep(1)
        print(f'pairs in trade: {counter}')


def get_main_trend(pair: Pair):
    pair = apply_status(pair)
    length = pair.trend_4h.size
    if pair.trend_4h.iloc[length-1] < 0:
        return -1
    else:
        return 1


def apply_status(pair: Pair):
    pair.trend_1h = slingshot(pair.candles_1h['close'])
    pair.trend_4h = slingshot(pair.candles_4h['close'])
    return pair


def correlation(pair: Pair, trend: int):
    try:
        length = pair.trend_1h.size
        length2 = pair.trend_4h.size
        if pair.trend_1h.iloc[length-1] * pair.trend_4h.iloc[length2-1] > 0:
            if pair.trend_1h.iloc[length-1] * trend > 0:
                return True
        return False
    except Exception as err:
        print(f'exception in correlation: {err}')
        return False


def signal(pair: Pair):
    trend = 1 if pair.trend_1h[pair.trend_1h.size-1] >= 0 else -1
    length = pair.candles_1h['close'].size
    ema_slow = ewm(pair.candles_1h['close'], 62)
    k_line, d_line = stoch_rsi(pair.candles_1h, 14)    # убрать iloc при реальных торгах

    if trend == 1:
        if d_line[d_line.size-1] < k_line[k_line.size-1] <= 20:
            if pair.candles_1h['close'][length-2] < ema_slow[ema_slow.size-2]:
                return True
    else:
        if d_line[d_line.size-1] > k_line[k_line.size-1] >= 80:
            if pair.candles_1h['close'][length-2] > ema_slow[ema_slow.size-2]:
                return True
    return False


def place_order(pair: Pair, order_kind: int):
    price = pair.candles_1h['close'].iloc[pair.candles_1h['close'].size-1]
    qty = round_step_size(define_qty(), pair.market_lot_size)
    if not pair.in_trade:
        sl_price = 0.92 * price if order_kind == 1 else 1.08 * price
    else:
        sl_price = (pair.trade_data['last_add_price'] * pair.trade_data['qty'] + price * qty)/\
                   (pair.trade_data['qty'] + qty)
    sl_price = round_step_size(sl_price, pair.price_filter)
    side = Client.SIDE_BUY if order_kind == 1 else Client.SIDE_SELL
    close_side = Client.SIDE_SELL if order_kind == 1 else Client.SIDE_BUY

    order = None
    lev = client.futures_change_leverage(symbol=pair.symbol, leverage=leverage)
    for i in range(10):
        try:
            order = client.futures_create_order(symbol=pair.symbol, side=side,
                                                type=Client.ORDER_TYPE_MARKET, quantity=qty)
            if not pair.in_trade:
                pair.in_trade = True
                pair.trade_data['start_date'] = datetime.fromtimestamp(int(order['updateTime'])/1000)
                pair.trade_data['qty'] = float(order['executedQty'])
                pair.trade_data['origQty'] = pair.trade_data['qty']
                pair.trade_data['addon_times'] = 1
                pair.trade_data['ok'] = order_kind
                pair.trade_data['last_fix'] = pd.NA
                pair.trade_data['last_fix_price'] = float(order['avgPrice'])
                pair.trade_data['last_add'] = datetime.fromtimestamp(int(order['updateTime'])/1000)
                pair.trade_data['last_add_price'] = float(order['avgPrice'])
                pair.trade_data['fixed_times'] = 0
                pair.trade_data['result'] = -order_kind * pair.trade_data['origQty'] * pair.trade_data['last_add_price']
            else:
                pair.trade_data['qty'] += float(order['executedQty'])
                pair.trade_data['origQty'] = pair.trade_data['qty']
                pair.trade_data['addon_times'] += 1
                pair.trade_data['last_add'] = datetime.fromtimestamp(int(order['updateTime']) / 1000)
                pair.trade_data['last_add_price'] = float(order['avgPrice'])
                pair.trade_data['result'] -= order_kind * pair.trade_data['origQty'] * pair.trade_data['last_add_price']

            break
        except Exception as err:
            print(f'cannot place market order for {pair.symbol}. try number: {i+1} Error: {err}\n')
            time.sleep(1)
    if not order:
        return pair
    for i in range(10):
        try:
            sl_order = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=sl_price,
                                                   closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
            pair.trade_data['stop_loss'] = sl_price
            pair.trade_data['slId'] = sl_order['orderId']
            break
        except Exception as err:
            print(f'{pair.symbol}: ATTENTION! Cannot place take profit!')

    return pair


def define_qty():
    acc_info = (client.futures_account_balance())[1]
    curr_balance = float(acc_info['balance'])
    available = float(acc_info['withdrawAvailable'])
    orig_qty = dollars/100 * curr_balance
    qty = orig_qty
    if available / (orig_qty/leverage) < 10:
        qty /= 2
    if available / (orig_qty/leverage) < 5:
        qty /= 2
    if available / (orig_qty / leverage) < 4:
        qty = 0
    return qty


def check_stop_loss(pair: Pair):
    global statistics
    sl_order = client.futures_get_order(symbol=pair.symbol, orderId=pair.trade_data['slId'])
    if sl_order['status'] == 'FILLED':
        c_time = datetime.fromtimestamp(int(sl_order['updateTime']) / 1000)
        pair.trade_data['result'] += pair.trade_data['ok'] * pair.trade_data['qty'] * sl_order['avgPrice']
        res = pd.DataFrame([[pair.symbol, pair.trade_data['start_date'], c_time, pair.trade_data['ok'],
                             pair.trade_data['add_times'], pair.trade_data['fixed_times'], True,
                             pair.trade_data['result']]], columns=['symbol', 'open date', 'close date', 'deal_type',
                                                                   'addons', 'fixes', 'stop loss', 'result'])
        statistics.append(res, ignore_index=True)
        pair.in_trade=False
        pair.trade_data.clear()
    elif sl_order['status'] == 'CANCELED':
        print(f'stop loss order for {pair.symbol} was canceled directly. Tracking of current position has been stopped')
        pair.in_trade = False
        pair.trade_data.clear()
    return pair


def check_position(pair: Pair):
    length = pair.candles_1h['close'].size
    k_line, d_line = stoch_rsi(pair.candles_1h.iloc[:length - 1], 14)
    current_trend = slingshot(pair.candles_1h['close'])
    trend_length = current_trend.size
    c_time = datetime.fromtimestamp(int(pair.candles_1h['open_time'].iloc[length-1])/1000)
    if current_trend.iloc[trend_length - 1] * pair.trade_data['ok'] < 0:
        if pair.trade_data['ok'] == -1:
            if d_line[d_line.size - 1] < k_line[k_line.size - 1]:
                return pair.trade_data['origQty']
        else:
            if d_line[d_line.size - 1] > k_line[k_line.size - 1]:
                return pair.trade_data['origQty']
    else:
        if pair.trade_data['ok'] == -1:
            if d_line[d_line.size - 1] < k_line[k_line.size - 1] < 20:
                if not pair.trade_data['last_fix']:
                    return pair.trade_data['qty'] / 6
                elif pair.trade_data['last_fix'] < c_time - timedelta(hours=3):
                    return pair.trade_data['qty'] / 6
        else:
            if d_line[d_line.size - 1] > k_line[k_line.size - 1] > 80:
                if not pair.in_trade:
                    return pair.trade_data['qty'] / 6
                elif pair.trade_data['last_fix'] < c_time - timedelta(hours=3):
                    return pair.trade_data['qty'] / 6
    return 0


def fix_profit(pair: Pair, fixed):
    global statistics
    # price = pair.candles_1h['close'].iloc[pair.candles_1h['close'].size - 1]
    close_side = Client.SIDE_SELL if pair.trade_data['ok'] == 1 else Client.SIDE_BUY
    fixed = round_step_size(fixed, pair.market_lot_size)
    if fixed == 0:
        fixed = pair.trade_data['origQty']
    if fixed == pair.trade_data['origQty']:
        try:
            close = client.futures_create_order(symbol=pair.symbol, type=Client.FUTURE_ORDER_TYPE_MARKET,
                                                side=close_side, closePosition=True)
        except Exception as err:
            print(f'cant close position for {pair.symbol}\n{err}')
            return pair
        try:
            cancel = client.futures_cancel_order(symbol=pair.symbol, orderId=pair.trade_data['slId'])
        except Exception as err:
            print(f'cant cancel stop loss order dor {pair.symbol}\n{err}')
        c_time = datetime.fromtimestamp(int(close['updateTime']) / 1000)
        price = float(close['avgPrice'])
        pair.trade_data['result'] += pair.trade_data['ok'] * pair.trade_data['qty'] * price
        pair.trade_data['fixed_times'] += 1
        pair.trade_data['last_fix_price'] = price
        pair.trade_data['last_fix'] = c_time
        res = pd.DataFrame([[pair.symbol, pair.trade_data['start_trade'], pair.trade_data['last_fix'],
                            pair.trade_data['ok'], pair.trade_data['add_times'], pair.trade_data['fixed_times'], False,
                            pair.trade_data['result']]], columns=['symbol', 'open date', 'close date', 'deal_type',
                                                                  'addons', 'fixes', 'stop loss', 'result'])
        statistics.append(res, ignore_index=True)
        pair.in_trade = False
        pair.trade_data.clear()
    else:
        try:
            fix = client.futures_create_order(symbol=pair.symbol, side=close_side,
                                              type=Client.ORDER_TYPE_MARKET, quantity=fixed)
        except Exception as err:
            print(f'cant fix position for {pair.symbol}\n{err}')
            return pair
        c_time = datetime.fromtimestamp(int(fix['updateTime']) / 1000)
        price = float(fix['avgPrice'])
        pair.trade_data['qty'] -= fixed
        pair.trade_data['fixed_times'] += 1
        pair.trade_data['last_fix'] = c_time
        pair.trade_data['last_fix_price'] = price
        pair.trade_data['result'] += pair.trade_data['ok'] * fixed * price
        if price > 1.03*pair.trade_data['last_add_price'] and pair.trade_data['ok'] == 1:
            try:
                cancel = client.futures_cancel_order(symbol=pair.symbol, orderId=pair.trade_data['slId'])
            except Exception as err:
                print(f'cant cancel stop loss order dor {pair.symbol}\n{err}')
            sl_price = 0.98*pair.trade_data['last_add_price']
            sl_price = round_step_size(sl_price, pair.price_filter)
            try:
                sl_order = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=sl_price,
                                                       closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
            except Exception as err:
                print(f'cant create stop loss order for {pair.symbol}\n{err}')
                return pair
            pair.trade_data['stop_loss'] = sl_price
            pair.trade_data['slId'] = sl_order['orderId']

        elif price < 0.97*pair.trade_data['last_add_price'] and pair.trade_data['ok'] == -1:
            try:
                cancel = client.futures_cancel_order(symbol=pair.symbol, orderId=pair.trade_data['slId'])
            except Exception as err:
                print(f'cant cancel stop loss order dor {pair.symbol}\n{err}')
            sl_price = 1.02*pair.trade_data['last_add_price']
            sl_price = round_step_size(sl_price, pair.price_filter)
            try:
                sl_order = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=sl_price,
                                                       closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
            except Exception as err:
                print(f'cant create stop loss order for {pair.symbol}\n{err}')
                return pair
            pair.trade_data['stop_loss'] = sl_price
            pair.trade_data['slId'] = sl_order['orderId']

    return pair


def test_place_order(symbol: str, price: float, order_kind: int, timestamp: str):
    price = round_step_size(price, float(pairs_data[symbol]['PRICE_FILTER']))
    trade_time = datetime.fromtimestamp(int(timestamp)/1000)

    qty = dollars*leverage/price
    qty = round_step_size(qty, float(pairs_data[symbol]['MARKET_LOT_SIZE']))

    return dict(qty=qty, time=trade_time)


def save_statistics():
    global statistics
    date = datetime.today()
    filename = './statistics/' + date.strftime('%d.%m.%Y') + 'statistics.pkl'
    try:
        statistics.to_pickle(filename)
        print(f'statistics was successfully saved to {filename}')
    except Exception as err:
        print(f'failed to save statistics:\nerror={err}')


def save_trading_data(pairs):
    filename = 'db.pkl'
    res = []
    ind = []
    for pair in pairs:
        if pair.in_trade:
            data = pair.trade_data
            res.append([data['start_date'], data['qty'], data['origQty'], data['addon_times'], data['ok'],
                        data['last_fix'], data['last_fix_price'], data['last_add'], data['last_add_price'],
                        data['fixed_times'], data['stop_loss'], data['slId'], data['result']])
            ind.append(pair.symbol)
    df = pd.DataFrame(res, index=ind, columns=['start_date', 'qty', 'origQty', 'addon_times', 'ok', 'last_fix',
                                               'last_fix_price', 'last_add', 'last_add_price', 'fixed_times',
                                               'stop_loss', 'slId', 'result'])
    try:
        df.to_pickle(filename)
        print(f'trading data was successfully saved in {filename}\n')
    except Exception as err:
        print(f'failed to save trading data\nerror = {err}')


def restore_trading_data(pairs):
    filename = 'db.pkl'
    try:
        df = pd.read_pickle(filename)
    except Exception as err:
        print(f'failed to read {filename} to restore trading data\nerror = {err}')
        return pairs
    for pair in pairs:
        try:
            df1 = df.loc[[pair.symbol]]
        except KeyError:
            continue

        pair.in_trade = True
        pair.trade_data = (df1.to_dict('records'))[0]
        print(f'trade data for {pair.symbol} was restored')
    return pairs


# def check_addon_condition(order_kind: int, candles: pd.DataFrame):
#     ema_fast = ewm(candles['close'], 38)
#     ema_slow = ewm(candles['close'], 62)
#     fast_length = ema_fast.size
#     slow_length = ema_slow.size
#     distance = (ema_fast-ema_slow).dropna()
#     if order_kind == 1:
#         current_v = 0
#         is_downtrend = True
#         for index, value in ema_slow.iloc[slow_length-4:slow_length].items():
#             if current_v == 0:
#                 current_v = value
#                 continue
#             if value > current_v:
#                 is_downtrend = False
#                 break
#             current_v = value
#
#         if not is_downtrend:
#             return True
#
#         current_v = 0
#         for index, value in ema_fast.iloc[fast_length-4:fast_length].items():
#             if current_v == 0:
#                 current_v = value
#                 continue
#             if value > current_v:
#                 is_downtrend = False
#                 break
#             current_v = value
#
#         if not is_downtrend:
#             return True
#
#         if distance.iloc[distance.size-11] < 2.2 * distance.iloc[distance.size-1]:
#             return True
#
#     else:
#         current_v = 0
#         is_uptrend = True
#         for index, value in ema_slow.iloc[slow_length - 4:slow_length].items():
#             if current_v == 0:
#                 current_v = value
#                 continue
#             if value < current_v:
#                 is_uptrend = False
#                 break
#             current_v = value
#
#         if not is_uptrend:
#             return True
#
#         current_v = 0
#         for index, value in ema_fast.iloc[fast_length - 4:fast_length].items():
#             if current_v == 0:
#                 current_v = value
#                 continue
#             if value < current_v:
#                 is_uptrend = False
#                 break
#             current_v = value
#
#         if not is_uptrend:
#             return True
#
#         if distance.iloc[distance.size - 11] < 2.2 * distance.iloc[distance.size - 1]:
#             return True
#     return False

# def check_take_profits(symbol: str):
#     global trading_pairs_data
#     tp_orders = trading_pairs_data[symbol]['tp']
#     for order in tp_orders:
#         status = (client.futures_get_order(symbol=symbol, orderId=order))['status']
#         if status == 'FILLED':
#             print(f'got take profit for {symbol}')
#         elif status == 'CANCELED':
#             print(f'take profit order for {symbol} is canceled')
#         elif status == 'NEW':
#             continue
#         else:
#             print(f'unknown status for take profit order: {status}')
#
#
# def check_stop_loss(symbol: str, candles: pd.DataFrame):
#     global trading_pairs_data
#     sl = trading_pairs_data[symbol]['sl']
#     if sl:
#         status = (client.futures_get_order(symbol=symbol, orderId=sl))['status']
#         if status == 'FILLED':
#             print(f'position for {symbol} was closed by stop loss')
#             return False
#         elif status == 'CANCELED':
#             print(f'stop loss order for {symbol} is canceled')
#             return False
#         elif status == 'NEW':
#             cancel = client.futures_cancel_order(symbol=symbol, orderId=sl)
#             print(f'old stop loss for {symbol} was canceled: {cancel}')
#         else:
#             print(f'unknown status for stop loss order:{status}')
#             return False
#
#     sl_price = update_sl(symbol, candles, trading_pairs_data['order_kind'])
#     close_side = Client.SIDE_SELL if trading_pairs_data['order_kind'] == 1 else Client.SIDE_BUY
#
#     while True:
#         try:
#             sl_order = client.futures_create_order(symbol=symbol, side=close_side, stopPrice=sl_price,
#                                                    closePosition=True,
#                                                    type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
#             print(f'new stop loss was created successfully: {sl_order}')
#             break
#         except Exception as err:
#             print(f'{symbol}: ATTENTION! Cannot place stop loss!Error: {err}')
#     return True


# def update_sl(symbol: str, candles: pd.DataFrame, order_kind: int):
#     ema_fast = ewm(candles['close'], 38)
#     ema_slow = ewm(candles['close'], 62)
#     sl = ema_slow.iloc[ema_slow.size-1] - ema_slow.iloc[ema_slow.size-1] * STOP_LOSS if order_kind == 1 \
#         else ema_slow.iloc[ema_slow.size-1] + ema_slow.iloc[ema_slow.size-1] * STOP_LOSS
#     sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))
#     return sl


# def check_candle(candle: pd.DataFrame, order_kind: int):
#     body, upper_shadow, lower_shadow = candle_parts(candle)
#     if order_kind == 1:
#         if lower_shadow * 2 < body or lower_shadow < upper_shadow * 2:
#             return False
#     else:
#         if upper_shadow * 2 < body or lower_shadow * 2 > upper_shadow:
#             return False
#     return True
#
#
# def candle_parts(candle: pd.DataFrame):
#     body = abs((candle['close'] - candle['open']).iloc[0])
#     upper_shadow = min((candle['high']-candle['close']).iloc[0], (candle['high']-candle['open']).iloc[0])
#     lower_shadow = min((candle['close']-candle['low']).iloc[0], (candle['open']-candle['low']).iloc[0])
#     return body, upper_shadow, lower_shadow


# def test_check_sl(symbol: str, price: float, sl: float, order_kind: int, candles: pd.DataFrame) -> float:
#     length = candles['open_time'].size
#     result = None
#     if order_kind == 1:
#         if candles['low'].iloc[length-1] < sl:
#             result = -(price - sl) / price * 100
#
#     else:
#         if candles['high'].iloc[length-1] > sl:
#             result = -(sl - price) / price * 100
#     return result
#
#
# def test_check_tp(symbol: str, price: float, tp: float, order_kind: int, candles: pd.DataFrame) -> float:
#     length = candles['open_time'].size
#     result = None
#     if order_kind == 1:
#         if candles['high'].iloc[length-1] > tp:
#             result = (tp - price) / price * 100 * 1/2
#
#     else:
#         if candles['low'].iloc[length-1] < tp:
#             result = (price - tp) / price * 100 * 1/2
#     return result


