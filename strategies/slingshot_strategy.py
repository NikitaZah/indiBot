import queue

from indicators.slingshot import slingshot
from indicators.stochRSI import stoch_rsi
import get
from indicators.lines import ewm, atr2
from data import client_d as client
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
from binance.exceptions import BinanceAPIException, BinanceRequestException

dollars = 25   # percent of deposit
leverage = 20
main_trend = 1

statistics = pd.DataFrame(columns=['symbol', 'open date', 'close date', 'deal_type', 'addons', 'fixes',
                                             'stop loss', 'result'])

# def test_slingshot_strategy():
#     stat = []
#     filename = './statistics/stat1.pkl'
#
#     testing = 10000
#     pairs = dict()
#
#     total_win = 0
#     total_lose = 0
#     total_res = 0
#
#
#     test_pairs = ['ETHUSDT', 'TLMUSDT', 'BTCUSDT']
#     # all_pairs = test_pairs
#
#     for symbol in tqdm(all_pairs, desc='getting pairs data'):
#         pair_data_file1 = './pair_data/' + symbol + '1h.pkl'
#         pair_data_file4 = './pair_data/' + symbol + '4h.pkl'
#         candles1 = pd.read_pickle(pair_data_file1)
#         candles4 = pd.read_pickle(pair_data_file4)
#         # end_time1 = candles1['open_time'].iloc[0]
#         # end_time4 = candles4['open_time'].iloc[0]
#         # candles1 = get.candles(client, symbol, '1h', end_time1, limit=testing).append(candles1).reset_index(drop=True)
#         # candles4 = get.candles(client, symbol, '4h', end_time4, limit=(testing // 4 + 1)).append(candles4).reset_index(drop=True)
#         # candles1.to_pickle(pair_data_file1)
#         # candles4.to_pickle(pair_data_file4)
#         pairs[symbol] = [candles1, candles4]
#         if candles1['open_time'].size < 20000:
#             print(f'pair {symbol} only has {candles1["open_time"].size} candles')
#
#     for symbol in tqdm(all_pairs, desc='checking symbols'):
#         if symbol == 'BTCUSDT':
#             continue
#
#         in_trade = {}
#         candles1 = pairs[symbol][0]
#         candles4 = pairs[symbol][1]
#         candles1_btc = pairs['BTCUSDT'][0]
#         candles4_btc = pairs['BTCUSDT'][1]
#
#         length = candles1['open_time'].size
#         start = -1
#         for end in range(1000, length):
#             start += 1
#             klines1 = candles1.iloc[start:end].reset_index(drop=True)
#             start_time = klines1.loc[0, 'open_time']
#             close_time = klines1.loc[end-start-1, 'close_time']
#             klines4 = candles4.loc[candles4['open_time'] < close_time]
#             klines1_btc = candles1_btc.loc[(candles1_btc['open_time'] >= start_time) & (candles1_btc['close_time'] <= close_time)].reset_index(drop=True)
#             klines4_btc = candles4_btc.loc[(candles4_btc['open_time'] < close_time)]
#
#             price = (klines1.loc[end - start - 1, 'open'])
#             c_time = datetime.fromtimestamp(int(klines1.loc[end - start - 1, 'open_time']) / 1000)
#             if in_trade:
#                 fixed = check_position(in_trade['symbol'], in_trade['origQty'], in_trade['ok'], klines1)
#                 check = check_stop_loss(in_trade, klines1)
#                 if check:
#                     in_trade = fix_profit(in_trade, in_trade['origQty'], in_trade['stop_loss'], c_time)
#                 elif fixed > 0:
#                     in_trade = fix_profit(in_trade, fixed, price, c_time)
#                 else:
#                     if price > 1.16 * in_trade['last_fix_price'] and in_trade['ok'] == 1:
#                         in_trade = fix_profit(in_trade, in_trade['origQty']/6, price, c_time)
#                     if price < 0.84 * in_trade['last_fix_price'] and in_trade['ok'] == -1:
#                         in_trade = fix_profit(in_trade, in_trade['origQty']/6, price, c_time)
#
#                 if in_trade['qty'] <= float(pairs_data[symbol]['MARKET_LOT_SIZE']):
#                     stat.append([in_trade['symbol'], in_trade['start_date'], in_trade['last_fix'], in_trade['ok'],
#                                  in_trade['addon_times'], in_trade['fixed_times'], check, in_trade['result']])
#                     print(stat[-1])
#                     if in_trade['result'] > 0:
#                         total_win += 1
#                     else:
#                         total_lose += 1
#                     total_res += in_trade['result']
#                     in_trade = {}
#
#             # # date filter
#             # if c_time.month == 9:
#             #     continue
#             # if c_time.day > 20 and c_time.month != 12:
#             #     continue
#             # if c_time.day < 3 and c_time.month != 1:
#             #     continue
#
#             # volume filter
#             if not get.appropriate(symbol, klines1, '1h', volatile=0):
#                 continue
#
#             pair = apply_status(symbol, klines1, klines4)
#
#             main_trend = get_main_trend('BTCUSDT', klines1_btc, klines4_btc)
#
#             # btc correlation filter
#             if not correlation(pair, main_trend):
#                 continue
#
#             if not signal(pair):
#                 continue
#
#             if in_trade:
#                 if in_trade['fixed_times'] == 0:
#                     continue
#                 if in_trade['last_fix'] < in_trade['last_add']:
#                     continue
#                 if 1.04*in_trade['last_add_price'] > price and in_trade['ok'] == 1:
#                     continue
#                 if 0.96*in_trade['last_add_price'] < price and in_trade['ok'] == -1:
#                     continue
#
#                 # res = check_addon_condition(in_trade['ok'], klines1)
#                 # if not res:
#                 #     continue
#
#             placed = test_place_order(pair['symbol'], price, main_trend, klines1.loc[end-start-1, 'open_time'])
#             if in_trade:
#                 in_trade['stop_loss'] = (in_trade['last_add_price'] * in_trade['qty'] + price * placed['qty']) / \
#                                         (in_trade['qty'] + placed['qty'])
#                 in_trade['qty'] += placed['qty']
#                 in_trade['origQty'] = in_trade['qty']
#                 in_trade['addon_times'] += 1
#                 in_trade['last_add'] = c_time
#                 in_trade['last_add_price'] = price
#                 in_trade['result'] -= in_trade['ok']*placed['qty'] * price
#             else:
#                 in_trade['symbol'] = symbol
#                 in_trade['start_date'] = placed['time']
#                 in_trade['qty'] = placed['qty']
#                 in_trade['origQty'] = placed['qty']
#                 in_trade['addon_times'] = 1
#                 in_trade['ok'] = main_trend
#                 in_trade['last_fix'] = pd.NA
#                 in_trade['last_fix_price'] = price
#                 in_trade['last_add'] = c_time
#                 in_trade['last_add_price'] = price
#                 in_trade['fixed_times'] = 0
#                 in_trade['stop_loss'] = price - in_trade['ok']*0.08*price
#                 in_trade['result'] = -in_trade['ok'] * placed['qty'] * price
#            # print(f'res = {in_trade["result"]}\nqty={in_trade["qty"]}\norig_qty={in_trade["origQty"]}\n')
#
#         if in_trade:
#             stat.append([in_trade['symbol'], in_trade['start_date'], in_trade['last_fix'], in_trade['ok'],
#                          in_trade['addon_times'], in_trade['fixed_times'], False, in_trade['result']])
#             print(stat[-1])
#
#     print(f'testing finished.\nTotal deals: {total_win+total_lose}\nTotal win: {total_win}\nTotal lose: {total_lose}\n'
#           f'Total result: {total_res}\n')
#     statistics = pd.DataFrame(stat, columns=['symbol', 'open date', 'close date', 'deal_type', 'addons', 'fixes',
#                                              'stop loss', 'result'])
#     print(f'\n{statistics}')
#     try:
#         statistics.to_pickle(filename)
#     except FileNotFoundError:
#         print(f'Cannot find directory {filename} to save the database. Trying to create...')
#         folder = '/statistics'
#         curr_path = os.getcwd()
#         full_dir_name = curr_path + folder
#         try:
#             os.mkdir(full_dir_name)
#             statistics.to_pickle(filename)
#             print('Directory created successfully')
#         except OSError as err:
#             print(f'Creation of the directory failed because of {err}\n')
#
#     print(f'full statistics will be available at {filename}')


def slingshot_strategy(restore: bool, trading_allowed: bool):
    pairs = []

    # get candles for symbols and create objects if pairs empty:
    for pair in tqdm(all_pairs, desc='getting candles'):
        candles_1h, candles_4h = pd.DataFrame(), pd.DataFrame()
        while candles_4h.empty:
            candles_4h = get.candles(client, pair, '4h', limit=1000)
            if candles_4h.empty:
                time.sleep(3)
        while candles_1h.empty:
            candles_1h = get.candles(client, pair, '1h', limit=1000)
            if candles_1h.empty:
                time.sleep(3)

        obj_pair = Pair(pair)
        obj_pair.put_candles('1h', candles_1h)
        obj_pair.put_candles('4h', candles_4h)
        pairs.append(obj_pair)

    if restore:
        pairs = restore_trading_data(pairs)

    while True:
        now = datetime.now()
        print(f'new cycle started at {now}')
        if trading_allowed:
            for pair in pairs:
                if pair.symbol == 'BTCUSDT':
                    # main_trend = get_main_trend(pair)
                    continue

                # checking pair volume and volatility
                if not get.appropriate(pair.symbol, pair.candles_1h, '1h', volatile=0):
                    continue

                trend_1h, trend_4h = get_trends(pair)
                pair.put_trend('1h', trend_1h)
                pair.put_trend('4h', trend_4h)

                #  skipping pairs not correlated with BTC and 4h timeframe
                if not correlation(pair, main_trend):
                    continue

                # skipping pairs without signal
                if not signal(pair):
                    continue

                if pair.in_trade:
                    if pair.candles_1h.loc[999, 'close'] < 1.05 * pair.trade_data['last_add_price'] \
                            and pair.trade_data['ok'] == 1:
                        continue
                    elif pair.candles_1h.loc[999, 'close'] > 0.95 * pair.trade_data['last_add_price'] \
                            and pair.trade_data['ok'] == -1:
                        continue

                trade_data = pair.trade_data | place_order(pair, main_trend)
                pair.put_data(trade_data)
                if trade_data:
                    pair.in_trade = True
                    print(f'{pair.symbol}:\ntrade data: {trade_data}')

                    save_trading_data(pairs)
                else:
                    print(f'failed do create order for {pair.symbol}')

        update_time = pairs[0].candles_1h.loc[999, 'close_time']
        first_symbol_updated = None

        # update statistics at midnight
        if datetime.fromtimestamp(update_time/1000).hour == 0:
            save_statistics()

        while True:
            for pair in pairs:
                candles_1h = pd.DataFrame()
                candles_4h = pd.DataFrame()
                if first_symbol_updated == pair.symbol:     # new hour started and we have updated all candles
                    break

                while candles_1h.empty:
                    candles_1h = get.candles(client, pair.symbol, '1h', limit=1000)
                    if candles_1h.empty:
                        time.sleep(3)
                pair.put_candles('1h', candles_1h)

                if candles_1h.loc[999, 'open_time'] > update_time and not first_symbol_updated:
                    first_symbol_updated = pair.symbol

                while candles_4h.empty:
                    candles_4h = get.candles(client, pair.symbol, '4h', limit=1000)
                    if candles_4h.empty:
                        time.sleep(3)
                pair.put_candles('4h', candles_4h)

                if pair.in_trade:
                    trade_data = check_stop_loss(pair)
                    if not trade_data:
                        pair.in_trade = False
                        pair.clear_data()
                        print(f'{pair.symbol} position was closed by stop loss or stop loss was canceled directly')
                        save_trading_data(pairs)
                        continue
                    qty = check_position(pair)
                    if qty > 0:
                        trade_data = fix_profit(pair, qty)
                        if not trade_data:
                            pair.in_trade = False
                            pair.clear_data()
                            print(f'position for {pair.symbol} was completely closed')
                        else:
                            pair.put_data(trade_data)
                            print(f'{pair.symbol}: fixed profit')
                        save_trading_data(pairs)

                time.sleep(1)
            if pairs[0].candles_1h.loc[999, 'open_time'] > update_time:
                break


def get_main_trend(pair: Pair):
    trend1, trend4 = get_trends(pair)
    pair.put_trend('4h', trend4)
    length = pair.trend_4h.size
    if pair.trend_4h.iloc[length-1] < 0:
        return -1
    else:
        return 1


def get_trends(pair: Pair):
    return slingshot(pair.candles_1h['close']), slingshot(pair.candles_4h['close'])


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
        if d_line[d_line.size-1] < k_line[k_line.size-1] < 20:
            if pair.candles_1h['close'][length-2] < ema_slow[ema_slow.size-2]:
                return True
    else:
        if d_line[d_line.size-1] > k_line[k_line.size-1] > 80:
            if pair.candles_1h['close'][length-2] > ema_slow[ema_slow.size-2]:
                return True
    return False


def place_order(pair: Pair, order_kind: int):
    trade_data = pair.extract_data()
    price = pair.candles_1h['close'].iloc[pair.candles_1h['close'].size-1]
    qty = round_step_size(define_qty(pair, price), pair.market_lot_size)
    if qty == 0:
        print(f'{pair.symbol} is too expensive!\nprice: {price}, market lot size: {pair.market_lot_size}')
        return trade_data
    side = Client.SIDE_BUY if order_kind == 1 else Client.SIDE_SELL
    close_side = Client.SIDE_SELL if order_kind == 1 else Client.SIDE_BUY

    order = None
    lev = client.futures_change_leverage(symbol=pair.symbol, leverage=leverage)
    for i in range(10):
        try:
            order = client.futures_create_order(symbol=pair.symbol, side=side,
                                                type=Client.ORDER_TYPE_MARKET, quantity=qty)
            print(f'order status of just created order for {pair.symbol}: {order["status"]}')
            break
        except Exception as err:
            print(f'cannot place market order for {pair.symbol}. try number: {i+1} Error: {err}\n')
            time.sleep(1)
    if not order:
        return trade_data

    while order['status'] != 'FILLED':
        try:
            order = client.futures_get_order(symbol=pair.symbol, orderId=order['orderId'])
        except Exception as err:
            print(f'cannot get recently created market order\nerror = {err}')

    price = float(order['avgPrice'])
    qty = float(order['executedQty'])

    if not pair.in_trade:
        sl_price = 0.92 * price if order_kind == 1 else 1.08 * price
    else:
        sl_price = (trade_data['last_add_price'] * trade_data['origQty'] + price * qty) / (trade_data['origQty'] + qty)
        sl_price = sl_price - pair.price_filter if order_kind == 1 else sl_price + pair.price_filter

    sl_price = round_step_size(sl_price, pair.price_filter)

    if not pair.in_trade:
        trade_data['start_date'] = datetime.fromtimestamp(int(order['updateTime']) / 1000)
        trade_data['qty'] = qty
        trade_data['origQty'] = qty
        trade_data['addon_times'] = 1
        trade_data['ok'] = order_kind
        trade_data['last_fix'] = pd.NA
        trade_data['last_fix_price'] = price
        trade_data['last_add'] = datetime.fromtimestamp(int(order['updateTime']) / 1000)
        trade_data['last_add_price'] = price
        trade_data['fixed_times'] = 0
        trade_data['result'] = -order_kind * qty * price
    else:
        trade_data['qty'] += qty
        trade_data['origQty'] = trade_data['qty']
        trade_data['addon_times'] += 1
        trade_data['last_add'] = datetime.fromtimestamp(int(order['updateTime']) / 1000)
        trade_data['last_add_price'] = price
        trade_data['result'] -= order_kind * qty * price

    sl_order = None
    for i in range(10):
        try:
            sl_order = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=sl_price,
                                                   closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
            break
        except BinanceAPIException as err:
            print(f'{pair.symbol} : {err}\ntrying to move stop loss')
            sl_price = sl_price - pair.price_filter if order_kind == 1 else sl_price + pair.price_filter
        except Exception as err:
            print(f'{pair.symbol}: ATTENTION! Cannot place stop loss!\n{err}')

    if not sl_order:
        return trade_data

    if pair.in_trade:   # cancel old stop loss order after new was created
        cancel_order(pair.symbol, trade_data['slId'])


    trade_data['stop_loss'] = sl_price
    trade_data['slId'] = sl_order['orderId']
    return trade_data


def define_qty(pair: Pair, price: float):
    acc_info = client.futures_account_information()
    maint_margin = float(acc_info['totalMaintMargin'])
    total_margin = float(acc_info['totalMarginBalance'])
    total_balance = float(acc_info['totalWalletBalance'])
    orig_cash = dollars/100 * total_balance
    init_margin = orig_cash / leverage
    cash = orig_cash

    if maint_margin > total_margin - init_margin * 7:
        cash /= 2
    if maint_margin > total_margin - init_margin * 5:
        cash /= 2
    if maint_margin > total_margin - init_margin * 3:
        cash = 0
    qty = cash/price
    return qty


def check_stop_loss(pair: Pair):
    global statistics
    trade_data = pair.extract_data()
    try:
        sl_order = client.futures_get_order(symbol=pair.symbol, orderId=pair.trade_data['slId'])
    except BinanceAPIException as err:
        print(f'{pair.symbol} : {err}')
        return trade_data
    except Exception as err:
        print(f'Error while getting sl order for {pair.symbol}, order id: {trade_data["slId"]}\n{err}')
        return trade_data

    if sl_order['status'] == 'FILLED':
        c_time = datetime.fromtimestamp(int(sl_order['updateTime']) / 1000)
        trade_data['result'] += trade_data['ok'] * trade_data['qty'] * float(sl_order['avgPrice'])
        res = pd.DataFrame([[pair.symbol, trade_data['start_date'], c_time, trade_data['ok'], trade_data['addon_times'],
                             trade_data['fixed_times'], True, trade_data['result']]],
                           columns=['symbol', 'open date', 'close date', 'deal_type', 'addons', 'fixes', 'stop loss',
                                    'result'])
        statistics.append(res, ignore_index=True)
        trade_data.clear()
    elif sl_order['status'] == 'CANCELED':
        print(f'stop loss order for {pair.symbol} was canceled directly. Tracking of current position has been stopped')
        trade_data.clear()
    return trade_data


def check_position(pair: Pair):
    k_line, d_line = stoch_rsi(pair.candles_1h, 14)
    current_trend = slingshot(pair.candles_1h['close'])
    trend_length = current_trend.size
    length = pair.candles_1h['open_time'].size
    c_time = datetime.fromtimestamp(int(pair.candles_1h.loc[length-1, 'open_time'])/1000)
    if current_trend.iloc[trend_length - 1] * pair.trade_data['ok'] < 0:
        if pair.trade_data['ok'] == -1:
            if d_line[d_line.size - 1] < k_line[k_line.size - 1]:
                print(f'pair {pair.symbol} is trading contrtrend! Trend:\n{current_trend.tail(7)}')
                return pair.trade_data['qty']
        else:
            if d_line[d_line.size - 1] > k_line[k_line.size - 1]:
                return pair.trade_data['qty']
    else:
        if pair.trade_data['ok'] == -1:
            if d_line[d_line.size - 1] < k_line[k_line.size - 1] < 20:
                if pd.isna(pair.trade_data['last_fix']):
                    return pair.trade_data['origQty'] / 6
                elif pair.trade_data['last_fix'] < c_time - timedelta(hours=3):
                    return pair.trade_data['origQty'] / 6
            elif pair.candles_1h.loc[length-1, 'close'] < 0.9 * pair.trade_data['last_fix_price']:
                return pair.trade_data['origQty'] / 6

        else:
            if d_line[d_line.size - 1] > k_line[k_line.size - 1] > 80:
                if pd.isna(pair.trade_data['last_fix']):
                    return pair.trade_data['origQty'] / 6
                elif pair.trade_data['last_fix'] < c_time - timedelta(hours=3):
                    return pair.trade_data['origQty'] / 6
            elif pair.candles_1h.loc[length-1, 'close'] > 1.1 * pair.trade_data['last_fix_price']:
                return pair.trade_data['origQty'] / 6
    return 0


def fix_profit(pair: Pair, qty: float):
    global statistics
    trade_data = pair.extract_data()
    close_side = Client.SIDE_SELL if trade_data['ok'] == 1 else Client.SIDE_BUY
    qty = round_step_size(qty, pair.market_lot_size)
    if qty == 0:
        qty = pair.market_lot_size

    fixed = None
    for i in range(5):
        try:
            fixed = client.futures_create_order(symbol=pair.symbol, type=Client.FUTURE_ORDER_TYPE_MARKET,
                                                side=close_side, quantity=qty)
            break
        except BinanceAPIException as err:
            if int(err.code) == -4164:
                qty = trade_data['qty']
            else:
                time.sleep(3)
        except Exception as err:
            print(f'{pair.symbol} : {err}\nFAILED to fix profit')
            time.sleep(5)
    if not fixed:
        return trade_data

    while fixed['status'] != 'FILLED':
        fixed = client.futures_get_order(symbol=pair.symbol, orderId=fixed['orderId'])

    executed_qty = float(fixed["executedQty"])
    c_time = datetime.fromtimestamp(int(fixed['updateTime']) / 1000)
    price = float(fixed['avgPrice'])

    trade_data['qty'] -= executed_qty
    trade_data['result'] += trade_data['ok'] * executed_qty * price
    trade_data['fixed_times'] += 1
    trade_data['last_fix_price'] = price
    trade_data['last_fix'] = c_time

    if trade_data['qty'] <= 0:
        res = pd.DataFrame([[pair.symbol, trade_data['start_date'], trade_data['last_fix'],
                            trade_data['ok'], trade_data['addon_times'], trade_data['fixed_times'], False,
                            trade_data['result']]], columns=['symbol', 'open date', 'close date', 'deal_type',
                                                             'addons', 'fixes', 'stop loss', 'result'])
        statistics.append(res, ignore_index=True)
        cancel_order(pair.symbol, trade_data['slId'])
        trade_data.clear()
        return trade_data

    else:
        sl_order = None
        sl_price = None
        if price > 1.03*trade_data['last_add_price'] and trade_data['ok'] == 1:
            sl_price = 0.98*pair.trade_data['last_add_price']
            sl_price = round_step_size(sl_price, pair.price_filter)

        elif price < 0.97 * trade_data['last_add_price'] and trade_data['ok'] == -1:
            sl_price = 1.02 * pair.trade_data['last_add_price']
            sl_price = round_step_size(sl_price, pair.price_filter)

        if sl_price:
            for i in range(3):
                try:
                    sl_order = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=sl_price,
                                                           closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
                    break
                except BinanceAPIException as err:
                    print(f'{pair.symbol} : {err}\ntrying to move stop loss')
                    sl_price = sl_price - pair.price_filter if trade_data['ok'] == 1 else sl_price + pair.price_filter
                except Exception as err:
                    print(f'{pair.symbol}: ATTENTION! Cannot update stop loss!\n{err}')
                    return trade_data

            if sl_order:
                cancel_order(pair.symbol, trade_data['slId'])
                trade_data['stop_loss'] = sl_price
                trade_data['slId'] = sl_order['orderId']
            else:
                print(f'{pair.symbol}: failed to move stop loss after fixing profit. SL: {trade_data["stop_loss"]}\n'
                      f'last addon price: {trade_data["last_add_price"]}\nfix price: {price}\ntried move SL to\n'
                      f'{sl_price}')
    return trade_data


def cancel_order(symbol: str, order_id):
    try:
        cancel = client.futures_cancel_order(symbol=symbol, orderId=order_id)
    except Exception as error:
        print(f'failed to cancel order for {symbol}\nerror = {error}')


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
            data = pair.extract_data()
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
        except KeyError:    # symbol is not in trade
            continue

        pair.in_trade = True
        trade_data = (df1.to_dict('records'))[0]
        pair.put_data(trade_data)
        print(f'trade data for {pair.symbol} was restored\n{pair.trade_data}')
    return pairs


# def test_place_order(symbol: str, price: float, order_kind: int, timestamp: str):
#     price = round_step_size(price, float(pairs_data[symbol]['PRICE_FILTER']))
#     trade_time = datetime.fromtimestamp(int(timestamp)/1000)
#
#     qty = dollars*leverage/price
#     qty = round_step_size(qty, float(pairs_data[symbol]['MARKET_LOT_SIZE']))
#
#     return dict(qty=qty, time=trade_time)


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


